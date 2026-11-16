import pandas as pd

from core.cleaning.cleaning_executor import cleaning_executor
from core.cleaning.cleaning_planner import cleaning_planner
from core.profiling.profiler import DatasetProfiler
from core.quality.quality_engine import quality_engine
from models.dataset import Dataset
from models.transformation import TransformationStatus


def test_original_dataframe_never_mutated():
    df = pd.DataFrame({"x": [1, 1, 2, 3], "y": ["a", "a", "b", "c"]})
    original_copy = df.copy()

    ds = Dataset.new(df, "t.csv", "csv", 10)
    profiler = DatasetProfiler()
    profile = profiler.profile(ds)
    report = quality_engine.evaluate(df, profile)
    plan = cleaning_planner.build_plan(df, profile, report.issues)
    for t in plan:
        t.status = TransformationStatus.APPROVED

    cleaned_df, _ = cleaning_executor.apply(df, plan)

    pd.testing.assert_frame_equal(df, original_copy)
    assert len(cleaned_df) <= len(df)


def test_duplicate_removal_transformation_applies():
    df = pd.DataFrame({"x": [1, 1, 2, 3], "y": ["a", "a", "b", "c"]})
    ds = Dataset.new(df, "t.csv", "csv", 10)
    profiler = DatasetProfiler()
    profile = profiler.profile(ds)
    report = quality_engine.evaluate(df, profile)
    plan = cleaning_planner.build_plan(df, profile, report.issues)

    dup_transform = next(t for t in plan if t.action == "remove_exact_duplicate_rows")
    dup_transform.status = TransformationStatus.APPROVED

    cleaned_df, applied = cleaning_executor.apply(df, plan)
    assert len(cleaned_df) == 3
    applied_dup = next(t for t in applied if t.action == "remove_exact_duplicate_rows")
    assert applied_dup.status == TransformationStatus.APPLIED


def test_rejected_transformation_not_applied():
    df = pd.DataFrame({"x": [1, 1, 2, 3]})
    ds = Dataset.new(df, "t.csv", "csv", 10)
    profiler = DatasetProfiler()
    profile = profiler.profile(ds)
    report = quality_engine.evaluate(df, profile)
    plan = cleaning_planner.build_plan(df, profile, report.issues)
    for t in plan:
        t.status = TransformationStatus.REJECTED

    cleaned_df, applied = cleaning_executor.apply(df, plan)
    pd.testing.assert_frame_equal(cleaned_df, df)
    assert all(t.status == TransformationStatus.REJECTED for t in applied)
