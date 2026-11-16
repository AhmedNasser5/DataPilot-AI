"""Detects columns whose declared type does not match their real content."""
from __future__ import annotations

import uuid

import pandas as pd

from core.profiling.type_detector import is_text_like_dtype
from models.profile import ColumnProfile
from models.quality import QualityIssue, Severity


class TypeIssueDetector:
    def detect(self, df: pd.DataFrame, column_profiles: dict[str, ColumnProfile]) -> list[QualityIssue]:
        issues: list[QualityIssue] = []
        n_rows = len(df)

        for col, profile in column_profiles.items():
            if "numeric_stored_as_text" in profile.flags:
                issues.append(QualityIssue(
                    issue_id=f"TYPE-{uuid.uuid4().hex[:8]}",
                    column=col,
                    category="type",
                    description=f"Column '{col}' contains numeric values stored as text.",
                    severity=Severity.MEDIUM,
                    affected_rows=n_rows - profile.null_count,
                    detection_method="type_detector heuristic (numeric-like text ratio)",
                    confidence=0.85,
                ))
            if "date_stored_as_text" in profile.flags:
                issues.append(QualityIssue(
                    issue_id=f"TYPE-{uuid.uuid4().hex[:8]}",
                    column=col,
                    category="type",
                    description=f"Column '{col}' contains dates stored as text.",
                    severity=Severity.MEDIUM,
                    affected_rows=n_rows - profile.null_count,
                    detection_method="type_detector heuristic (date-like text ratio)",
                    confidence=0.8,
                ))

            if col in df.columns and is_text_like_dtype(df[col]):
                non_null = df[col].dropna()
                if not non_null.empty:
                    kinds = non_null.map(lambda v: type(v).__name__).nunique()
                    if kinds > 1:
                        issues.append(QualityIssue(
                            issue_id=f"TYPE-{uuid.uuid4().hex[:8]}",
                            column=col,
                            category="type",
                            description=f"Column '{col}' contains mixed Python types ({kinds} distinct types).",
                            severity=Severity.MEDIUM,
                            affected_rows=len(non_null),
                            detection_method="python type() inspection across non-null values",
                            confidence=0.9,
                        ))
        return issues
