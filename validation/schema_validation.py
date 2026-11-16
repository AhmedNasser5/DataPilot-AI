"""Validates that a dataframe's schema matches expectations (used after cleaning)."""
from __future__ import annotations

import pandas as pd


class SchemaValidator:
    def validate(self, df: pd.DataFrame) -> list[str]:
        problems = []
        if df.empty:
            problems.append("Dataset has zero rows after processing.")
        if len(df.columns) == 0:
            problems.append("Dataset has zero columns.")
        dup_cols = df.columns[df.columns.duplicated()].tolist()
        if dup_cols:
            problems.append(f"Duplicate column names found: {dup_cols}")
        return problems


schema_validator = SchemaValidator()
