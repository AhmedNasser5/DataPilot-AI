import numpy as np
import pandas as pd

from core.cleaning.cleaning_executor import cleaning_executor
from core.cleaning.cleaning_planner import cleaning_planner
from core.cleaning.cleaning_validator import cleaning_validator
from core.ingestion.loader_registry import loader_registry
from core.kpi.domain_detector import domain_detector
from core.kpi.kpi_calculator import kpi_calculator
from core.kpi.kpi_recommender import kpi_recommender
from core.profiling.profiler import DatasetProfiler
from core.quality.quality_engine import quality_engine
from core.sql.query_executor import query_executor
from core.sql.table_manager import table_manager
from models.transformation import TransformationStatus


def _build_messy_csv() -> bytes:
    rng = np.random.default_rng(42)
    n = 200
    df = pd.DataFrame({
        "Order ID": range(1, n + 1),
        "Category": rng.choice(["Electronics", "  electronics", "Clothing", "CLOTHING"], n),
        "Revenue": [f"${v:.2f}" for v in rng.uniform(10, 1000, n)],
        "Quantity": rng.integers(1, 20, n),
    })
    df = pd.concat([df, df.iloc[:5]])  # inject 5 duplicate rows
    return df.to_csv(index=False).encode("utf-8")


def test_full_pipeline_end_to_end():
    content = _build_messy_csv()
    dataset = loader_registry.load("orders.csv", content)
    assert dataset.metadata.row_count == 205

    profiler = DatasetProfiler()
    profile = profiler.profile(dataset)

    report = quality_engine.evaluate(dataset.dataframe, profile)
    assert report.overall_score < 100  # messy data must not score perfectly

    plan = cleaning_planner.build_plan(dataset.dataframe, profile, report.issues)
    assert len(plan) > 0
    for t in plan:
        t.status = TransformationStatus.APPROVED

    cleaned_df, applied = cleaning_executor.apply(dataset.dataframe, plan)
    assert len(cleaned_df) == 200  # duplicates removed
    assert all(t.status in (TransformationStatus.APPLIED,) for t in applied)

    cleaned_dataset = dataset.derive(cleaned_df, "v2", "Cleaned")
    comparison = cleaning_validator.validate(dataset, cleaned_dataset)
    assert comparison["quality_score_after"] >= comparison["quality_score_before"]

    table_name = table_manager.register(cleaned_dataset)
    result = query_executor.run(f'SELECT COUNT(*) AS n FROM "{table_name}"')
    assert result.error is None
    assert result.rows[0][0] == 200

    cleaned_profile = profiler.profile(cleaned_dataset)
    domain = domain_detector.detect(cleaned_profile)
    kpis = kpi_recommender.recommend(cleaned_profile, domain)
    assert len(kpis) > 0

    revenue_kpi = next((k for k in kpis if k.kpi_id == "total_revenue"), None)
    if revenue_kpi:
        calculated = kpi_calculator.calculate(table_name, revenue_kpi)
        assert calculated.calculable is True
        assert isinstance(calculated.value, float)
        assert calculated.value > 0
