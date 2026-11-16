"""Validates a proposed/applied transformation before or after execution."""
from __future__ import annotations

import pandas as pd

from models.transformation import Transformation


class TransformationValidator:
    def validate_pre(self, df: pd.DataFrame, t: Transformation) -> list[str]:
        problems = []
        if t.column and t.column not in df.columns:
            problems.append(f"Column '{t.column}' does not exist in the current dataset.")
        if not (0.0 <= t.confidence <= 1.0):
            problems.append(f"Confidence {t.confidence} is out of the expected 0-1 range.")
        return problems

    def validate_post(self, before: pd.DataFrame, after: pd.DataFrame, t: Transformation) -> list[str]:
        problems = []
        if t.action != "remove_exact_duplicate_rows" and len(after) != len(before):
            problems.append(
                f"Row count changed unexpectedly ({len(before)} -> {len(after)}) "
                f"for a transformation not expected to change row count."
            )
        return problems


transformation_validator = TransformationValidator()
