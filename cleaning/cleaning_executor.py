"""
Cleaning Executor.

Applies only user-APPROVED transformations, in order, to a COPY of the
dataframe. The original dataframe object passed in is never mutated.
Produces a full audit trail entry per transformation.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from core.cleaning.preview import CleaningPreview
from core.cleaning.transformations import TRANSFORMATION_REGISTRY, flag_outliers_column
from core.quality.outliers import OutlierDetector
from models.transformation import Transformation, TransformationStatus


class CleaningExecutor:
    def __init__(self):
        self._outlier_detector = OutlierDetector()

    def apply(self, df: pd.DataFrame, transformations: list[Transformation]) -> tuple[pd.DataFrame, list[Transformation]]:
        """Returns (new_dataframe, updated_transformations_with_status)."""
        working = df.copy()
        applied: list[Transformation] = []

        for t in transformations:
            if t.status != TransformationStatus.APPROVED:
                applied.append(t)
                continue
            try:
                before_rows = len(working)
                working = self._run_single(working, t)
                t.affected_rows = t.affected_rows or (before_rows - len(working)) or t.affected_rows
                t.status = TransformationStatus.APPLIED
                t.timestamp = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                t.status = TransformationStatus.FAILED
                t.error = str(e)
            applied.append(t)

        return working, applied

    def _run_single(self, df: pd.DataFrame, t: Transformation) -> pd.DataFrame:
        if t.action == "flag_outliers_column" and t.column:
            series = pd.to_numeric(df[t.column], errors="coerce").dropna()
            _, mask = self._outlier_detector._select_and_run(series)
            return flag_outliers_column(df, t.column, mask)

        if t.action == "group_median_imputation" and t.column:
            group_col = t.params.get("group_column")
            if not group_col or group_col not in df.columns:
                raise ValueError(f"Grouping column '{group_col}' is missing or was dropped by an earlier step.")
            fn = TRANSFORMATION_REGISTRY["group_median_imputation"]
            return fn(df, t.column, group_col)

        fn = TRANSFORMATION_REGISTRY.get(t.action)
        if fn is None:
            raise ValueError(f"Unknown transformation action '{t.action}'")
        if t.column:
            if t.column not in df.columns:
                raise ValueError(f"Column '{t.column}' no longer exists (may have been dropped by an earlier step).")
            return fn(df, t.column)
        return fn(df)


cleaning_executor = CleaningExecutor()
