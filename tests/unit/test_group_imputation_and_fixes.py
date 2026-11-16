import numpy as np
import pandas as pd

from core.cleaning.cleaning_planner import cleaning_planner
from core.cleaning.transformations import group_median_imputation
from core.profiling.profiler import DatasetProfiler
from core.quality.quality_engine import quality_engine
from models.dataset import Dataset


def test_group_median_imputation_uses_group_specific_median():
    df = pd.DataFrame({
        "industry": ["Tech", "Tech", "Tech", "Retail", "Retail", "Retail"],
        "amount": [100.0, np.nan, 300.0, 5.0, np.nan, 15.0],
    })
    out = group_median_imputation(df, "amount", "industry")
    # Tech group median of [100, 300] = 200; Retail group median of [5, 15] = 10
    assert out.loc[1, "amount"] == 200.0
    assert out.loc[4, "amount"] == 10.0


def test_group_median_imputation_falls_back_when_group_entirely_null():
    df = pd.DataFrame({
        "industry": ["Tech", "Tech", "Retail", "Retail"],
        "amount": [100.0, 300.0, np.nan, np.nan],
    })
    out = group_median_imputation(df, "amount", "industry")
    overall_median = 200.0  # median of [100, 300]
    assert out.loc[2, "amount"] == overall_median
    assert out.loc[3, "amount"] == overall_median


def test_duplicate_removal_transformation_reports_correct_affected_rows():
    df = pd.DataFrame({"x": [1, 1, 2, 3, 4], "y": ["a", "a", "b", "c", "d"]})
    ds = Dataset.new(df, "t.csv", "csv", 10)
    profiler = DatasetProfiler()
    profile = profiler.profile(ds)
    report = quality_engine.evaluate(df, profile)
    plan = cleaning_planner.build_plan(df, profile, report.issues)

    dup_transform = next(t for t in plan if t.action == "remove_exact_duplicate_rows")
    assert dup_transform.affected_rows == 1  # exactly one duplicate row in this dataset


def test_planner_prefers_group_imputation_when_grouping_column_exists():
    rng = np.random.default_rng(0)
    n = 60
    df = pd.DataFrame({
        "industry": rng.choice(["Tech", "Retail", "Finance"], n),
        "total_laid_off": [float(v) if i % 5 != 0 else np.nan for i, v in enumerate(rng.uniform(5, 5000, n))],
    })
    ds = Dataset.new(df, "layoffs.csv", "csv", 10)
    profiler = DatasetProfiler()
    profile = profiler.profile(ds)
    report = quality_engine.evaluate(df, profile)
    plan = cleaning_planner.build_plan(df, profile, report.issues)

    imputation = next((t for t in plan if t.column == "total_laid_off"), None)
    assert imputation is not None
    assert imputation.action == "group_median_imputation"
    assert imputation.params.get("group_column") == "industry"
