"""
Cleaning Service.

Application-layer facade orchestrating: quality evaluation -> cleaning
plan generation -> preview -> approval -> execution -> re-validation.
The Streamlit UI never talks to core.cleaning.* or core.quality.*
directly; it goes through this service.
"""
from __future__ import annotations

import pandas as pd

from core.cleaning.cleaning_executor import cleaning_executor
from core.cleaning.cleaning_planner import cleaning_planner
from core.cleaning.cleaning_validator import cleaning_validator
from core.cleaning.preview import cleaning_preview
from core.profiling.profiler import DatasetProfiler
from core.quality.quality_engine import quality_engine
from models.dataset import Dataset
from models.transformation import Transformation, TransformationStatus


class CleaningService:
    def __init__(self):
        self._profiler = DatasetProfiler()

    def evaluate_quality(self, dataset: Dataset):
        profile = self._profiler.profile(dataset)
        report = quality_engine.evaluate(dataset.dataframe, profile)
        return profile, report

    def build_plan(self, dataset: Dataset, profile, report) -> list[Transformation]:
        return cleaning_planner.build_plan(dataset.dataframe, profile, report.issues)

    def preview_transformation(self, dataset: Dataset, transformation: Transformation) -> dict:
        return cleaning_preview.preview(dataset.dataframe, transformation)

    def apply_approved(self, dataset: Dataset, transformations: list[Transformation]) -> tuple[Dataset, list[Transformation]]:
        new_df, updated = cleaning_executor.apply(dataset.dataframe, transformations)
        applied_count = sum(1 for t in updated if t.status == TransformationStatus.APPLIED)
        label = f"Cleaned (v2) — {applied_count} transformation(s) applied"
        new_dataset = dataset.derive(new_df, version="v2", version_label=label)
        return new_dataset, updated

    def validate_cleaning(self, original: Dataset, cleaned: Dataset) -> dict:
        return cleaning_validator.validate(original, cleaned)


cleaning_service = CleaningService()
