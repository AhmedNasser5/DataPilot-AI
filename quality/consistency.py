"""Detects consistency problems: capitalization, whitespace, format drift."""
from __future__ import annotations

import uuid

import pandas as pd

from core.profiling.type_detector import is_text_like_dtype
from models.profile import ColumnProfile
from models.quality import QualityIssue, Severity


class ConsistencyDetector:
    def detect(self, df: pd.DataFrame, column_profiles: dict[str, ColumnProfile]) -> list[QualityIssue]:
        issues: list[QualityIssue] = []

        for col, profile in column_profiles.items():
            if col not in df.columns or profile.detected_type not in ("categorical", "text"):
                continue
            series = df[col].dropna()
            if series.empty or not is_text_like_dtype(series):
                continue
            str_series = series.astype(str)

            # Whitespace inconsistency: leading/trailing spaces
            ws_count = int((str_series != str_series.str.strip()).sum())
            if ws_count > 0:
                issues.append(self._issue(col, "consistency",
                    f"{ws_count} value(s) in '{col}' have leading/trailing whitespace.",
                    Severity.LOW, ws_count, "whitespace comparison", 1.0))

            # Capitalization inconsistency: same value, different case collapses to fewer categories
            lowered_nunique = str_series.str.strip().str.lower().nunique()
            raw_nunique = str_series.str.strip().nunique()
            if raw_nunique > lowered_nunique and lowered_nunique > 0:
                collapse_ratio = (raw_nunique - lowered_nunique) / raw_nunique
                if collapse_ratio > 0.05:
                    issues.append(self._issue(col, "consistency",
                        f"Column '{col}' has inconsistent capitalization: {raw_nunique} raw categories "
                        f"collapse to {lowered_nunique} when case-insensitive.",
                        Severity.MEDIUM, len(str_series), "case-insensitive category collapse", 0.85))

        return issues

    @staticmethod
    def _issue(col, category, desc, sev, rows, method, conf) -> QualityIssue:
        return QualityIssue(
            issue_id=f"CONS-{uuid.uuid4().hex[:8]}",
            column=col, category=category, description=desc, severity=sev,
            affected_rows=rows, detection_method=method, confidence=conf,
        )
