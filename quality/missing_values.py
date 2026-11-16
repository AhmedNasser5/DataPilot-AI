"""
Missing-value detection.

Detects real nulls AND configured missing-value markers hiding inside
text columns (e.g. the string "N/A", "-", "unknown"...). Returns
QualityIssue records; it never mutates the dataframe (that is the
cleaning engine's job).
"""
from __future__ import annotations

import uuid

import pandas as pd

from config.settings import settings
from core.profiling.type_detector import is_text_like_dtype
from models.quality import QualityIssue, Severity


class MissingValueDetector:
    def detect(self, df: pd.DataFrame) -> list[QualityIssue]:
        issues: list[QualityIssue] = []
        n_rows = len(df)
        if n_rows == 0:
            return issues

        markers = set(settings.missing_value_markers)

        for col in df.columns:
            series = df[col]
            null_count = int(series.isna().sum())

            hidden_count = 0
            if is_text_like_dtype(series):
                as_str = series.dropna().astype(str).str.strip().str.lower()
                hidden_count = int(as_str.isin(markers).sum())

            total_missing = null_count + hidden_count
            if total_missing == 0:
                continue

            pct = 100 * total_missing / n_rows
            severity = self._severity_for_pct(pct)

            issues.append(QualityIssue(
                issue_id=f"MISS-{uuid.uuid4().hex[:8]}",
                column=col,
                category="missing",
                description=(
                    f"{total_missing} missing value(s) detected "
                    f"({null_count} native null, {hidden_count} disguised as text markers)."
                ),
                severity=severity,
                affected_rows=total_missing,
                detection_method="null-count + missing-value-marker matching",
                confidence=1.0 if hidden_count == 0 else 0.95,
                details={"null_count": null_count, "hidden_marker_count": hidden_count, "pct": round(pct, 2)},
            ))
        return issues

    @staticmethod
    def _severity_for_pct(pct: float) -> Severity:
        if pct >= 50:
            return Severity.CRITICAL
        if pct >= 20:
            return Severity.HIGH
        if pct >= 5:
            return Severity.MEDIUM
        return Severity.LOW
