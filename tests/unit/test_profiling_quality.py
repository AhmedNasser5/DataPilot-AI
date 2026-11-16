import numpy as np
import pandas as pd

from core.profiling.profiler import DatasetProfiler
from core.quality.quality_engine import quality_engine
from models.dataset import Dataset


def _make_dataset(df: pd.DataFrame) -> Dataset:
    return Dataset.new(df, "test.csv", "csv", len(df.to_csv().encode()))


def test_profiler_detects_numeric_and_categorical():
    df = pd.DataFrame({
        "amount": [1.0, 2.0, 3.0, 4.0, 5.0],
        "category": ["a", "b", "a", "b", "c"],
    })
    profiler = DatasetProfiler()
    profile = profiler.profile(_make_dataset(df))
    assert profile.columns["amount"].detected_type == "numeric"
    assert profile.columns["category"].detected_type == "categorical"


def test_profiler_detects_constant_column():
    df = pd.DataFrame({"x": [1, 1, 1, 1], "y": [1, 2, 3, 4]})
    profiler = DatasetProfiler()
    profile = profiler.profile(_make_dataset(df))
    assert profile.columns["x"].is_constant is True


def test_profiler_detects_possible_primary_key():
    df = pd.DataFrame({"id": [1, 2, 3, 4], "val": ["a", "b", "c", "d"]})
    profiler = DatasetProfiler()
    profile = profiler.profile(_make_dataset(df))
    assert profile.columns["id"].is_possible_primary_key is True


def test_quality_engine_detects_missing_values():
    df = pd.DataFrame({"x": [1, 2, None, 4], "y": ["a", "b", "c", "d"]})
    profiler = DatasetProfiler()
    ds = _make_dataset(df)
    profile = profiler.profile(ds)
    report = quality_engine.evaluate(df, profile)
    missing_issues = [i for i in report.issues if i.category == "missing"]
    assert len(missing_issues) >= 1
    assert report.overall_score < 100


def test_quality_engine_detects_duplicates():
    df = pd.DataFrame({"x": [1, 1, 2, 3], "y": ["a", "a", "b", "c"]})
    profiler = DatasetProfiler()
    ds = _make_dataset(df)
    profile = profiler.profile(ds)
    report = quality_engine.evaluate(df, profile)
    dup_issues = [i for i in report.issues if i.category == "duplicate" and i.column is None]
    assert len(dup_issues) == 1
    assert dup_issues[0].affected_rows == 1


def test_perfect_dataset_scores_100():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": ["a", "b", "c", "d", "e"]})
    profiler = DatasetProfiler()
    ds = _make_dataset(df)
    profile = profiler.profile(ds)
    report = quality_engine.evaluate(df, profile)
    assert report.overall_score == 100.0
