"""
Validates a cleaned dataset by re-profiling and re-scoring it, then
comparing against the pre-cleaning state. Never claims the data is
'perfectly clean' — only reports what changed, using evidence-based
language (Detected / Applied / Validated).
"""
from __future__ import annotations

import pandas as pd

from core.profiling.profiler import DatasetProfiler
from core.quality.quality_engine import quality_engine
from models.dataset import Dataset
from models.quality import QualityReport


class CleaningValidator:
    def __init__(self):
        self._profiler = DatasetProfiler()

    def validate(self, original: Dataset, cleaned: Dataset) -> dict:
        original_profile = self._profiler.profile(original)
        cleaned_profile = self._profiler.profile(cleaned)

        original_report = quality_engine.evaluate(original.dataframe, original_profile)
        cleaned_report = quality_engine.evaluate(cleaned.dataframe, cleaned_profile)

        new_issue_categories = self._new_issue_categories(original_report, cleaned_report)

        return {
            "original_profile": original_profile,
            "cleaned_profile": cleaned_profile,
            "original_quality": original_report,
            "cleaned_quality": cleaned_report,
            "row_count_before": original_profile.row_count,
            "row_count_after": cleaned_profile.row_count,
            "column_count_before": original_profile.column_count,
            "column_count_after": cleaned_profile.column_count,
            "quality_score_before": original_report.overall_score,
            "quality_score_after": cleaned_report.overall_score,
            "quality_delta": round(cleaned_report.overall_score - original_report.overall_score, 1),
            "possible_new_issues": new_issue_categories,
        }

    @staticmethod
    def _new_issue_categories(before: QualityReport, after: QualityReport) -> list[str]:
        before_keys = {(i.category, i.column) for i in before.issues}
        after_keys = {(i.category, i.column) for i in after.issues}
        new_keys = after_keys - before_keys
        return [f"{cat} in column '{col}'" if col else cat for cat, col in new_keys]


cleaning_validator = CleaningValidator()
