"""Duplicate detection: exact duplicate rows and duplicate identifier values."""
from __future__ import annotations

import uuid

import pandas as pd

from models.profile import ColumnProfile
from models.quality import QualityIssue, Severity


class DuplicateDetector:
    def detect(self, df: pd.DataFrame, column_profiles: dict[str, ColumnProfile] | None = None) -> list[QualityIssue]:
        issues: list[QualityIssue] = []
        n_rows = len(df)
        if n_rows == 0:
            return issues

        dup_mask = df.duplicated(keep="first")
        dup_count = int(dup_mask.sum())
        if dup_count > 0:
            pct = 100 * dup_count / n_rows
            issues.append(QualityIssue(
                issue_id=f"DUP-{uuid.uuid4().hex[:8]}",
                column=None,
                category="duplicate",
                description=f"{dup_count} exact duplicate row(s) detected ({pct:.1f}% of dataset).",
                severity=Severity.HIGH if pct >= 10 else (Severity.MEDIUM if pct >= 1 else Severity.LOW),
                affected_rows=dup_count,
                detection_method="full-row equality comparison",
                confidence=1.0,
                details={"pct": round(pct, 2)},
            ))

        if column_profiles:
            id_like_cols = [
                name for name, p in column_profiles.items()
                if p.is_possible_id or p.is_possible_primary_key
            ]
            for col in id_like_cols:
                if col not in df.columns:
                    continue
                dup_ids = df[col].dropna()
                dup_id_count = int(dup_ids.duplicated(keep="first").sum())
                if dup_id_count > 0:
                    issues.append(QualityIssue(
                        issue_id=f"DUPID-{uuid.uuid4().hex[:8]}",
                        column=col,
                        category="duplicate",
                        description=(
                            f"Column '{col}' looks like an identifier but contains "
                            f"{dup_id_count} duplicate value(s), which breaks uniqueness assumptions."
                        ),
                        severity=Severity.HIGH,
                        affected_rows=dup_id_count,
                        detection_method="duplicate check on detected ID/primary-key column",
                        confidence=0.85,
                    ))
        return issues
