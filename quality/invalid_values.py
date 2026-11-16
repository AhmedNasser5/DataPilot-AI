"""Detects malformed dates and other clearly-invalid values."""
from __future__ import annotations

import uuid

import pandas as pd
from dateutil import parser as dateutil_parser

from core.profiling.type_detector import is_text_like_dtype
from models.profile import ColumnProfile
from models.quality import QualityIssue, Severity


class InvalidValueDetector:
    def detect(self, df: pd.DataFrame, column_profiles: dict[str, ColumnProfile]) -> list[QualityIssue]:
        issues: list[QualityIssue] = []

        for col, profile in column_profiles.items():
            if profile.detected_type != "datetime" or col not in df.columns:
                continue
            series = df[col].dropna()
            if series.empty or not is_text_like_dtype(series):
                continue

            malformed = 0
            checked = 0
            for v in series.astype(str).head(500):
                checked += 1
                try:
                    dateutil_parser.parse(v, fuzzy=False)
                except (ValueError, OverflowError, TypeError):
                    malformed += 1
            if malformed > 0:
                pct_of_checked = malformed / checked
                est_total = int(round(pct_of_checked * len(series)))
                issues.append(QualityIssue(
                    issue_id=f"INV-{uuid.uuid4().hex[:8]}",
                    column=col,
                    category="validity",
                    description=f"Column '{col}' contains an estimated {est_total} malformed date value(s).",
                    severity=Severity.MEDIUM if pct_of_checked < 0.2 else Severity.HIGH,
                    affected_rows=est_total,
                    detection_method="dateutil parse attempt on sample of up to 500 values",
                    confidence=0.8,
                ))
        return issues
