"""Generates before/after previews for a proposed transformation without applying it destructively."""
from __future__ import annotations

import pandas as pd

from core.cleaning.transformations import TRANSFORMATION_REGISTRY
from core.quality.outliers import OutlierDetector
from models.transformation import Transformation


class CleaningPreview:
    def preview(self, df: pd.DataFrame, transformation: Transformation, sample_size: int = 5) -> dict:
        col = transformation.column
        before_sample = df[col].head(sample_size).tolist() if col and col in df.columns else []

        try:
            after_df = self._apply(df, transformation)
            after_sample = after_df[col].head(sample_size).tolist() if col and col in after_df.columns else []
            row_delta = len(after_df) - len(df)
            error = None
        except Exception as e:
            after_sample = []
            row_delta = 0
            error = str(e)

        return {
            "transformation_id": transformation.transformation_id,
            "column": col,
            "before_sample": before_sample,
            "after_sample": after_sample,
            "row_count_before": len(df),
            "row_count_after": len(df) + row_delta,
            "reason": transformation.reason,
            "confidence": transformation.confidence,
            "expected_impact": transformation.expected_impact,
            "error": error,
        }

    def _apply(self, df: pd.DataFrame, t: Transformation) -> pd.DataFrame:
        if t.action == "flag_outliers_column" and t.column:
            detector = OutlierDetector()
            series = pd.to_numeric(df[t.column], errors="coerce").dropna()
            _, mask = detector._select_and_run(series)
            from core.cleaning.transformations import flag_outliers_column
            return flag_outliers_column(df, t.column, mask)

        if t.action == "group_median_imputation" and t.column:
            group_col = t.params.get("group_column")
            if not group_col or group_col not in df.columns:
                raise ValueError(f"Grouping column '{group_col}' is missing.")
            return TRANSFORMATION_REGISTRY["group_median_imputation"](df, t.column, group_col)

        fn = TRANSFORMATION_REGISTRY.get(t.action)
        if fn is None:
            raise ValueError(f"Unknown transformation action '{t.action}'")
        if t.column:
            return fn(df, t.column)
        return fn(df)


cleaning_preview = CleaningPreview()
