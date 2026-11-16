"""
Analytics Service.

Facade for domain detection, KPI recommendation/calculation,
statistical analysis, SQL execution, and the AI analyst. This is the
single entry point the Streamlit pages use for "analysis" features.
"""
from __future__ import annotations

import pandas as pd

from ai.analyst_agent import analyst_agent
from ai.domain_reasoner import domain_reasoner
from ai.insight_generator import insight_generator
from ai.sql_generator import sql_generator
from core.analytics.anomaly_detection import anomaly_detection_engine
from core.analytics.correlation import correlation_engine
from core.analytics.statistics import statistics_engine
from core.analytics.trends import trend_engine
from core.kpi.domain_detector import domain_detector
from core.kpi.kpi_calculator import kpi_calculator
from core.kpi.kpi_recommender import kpi_recommender
from core.sql.query_executor import query_executor
from core.sql.query_explainer import query_explainer
from core.sql.table_manager import table_manager
from models.analysis import DomainDetection, KPIDefinition
from models.dataset import Dataset
from models.profile import DatasetProfile


class AnalyticsService:
    def detect_domain(self, profile: DatasetProfile) -> DomainDetection:
        return domain_detector.detect(profile)

    def explain_domain(self, domain: DomainDetection, column_names: list[str]) -> str:
        return domain_reasoner.explain(domain, column_names)

    def recommend_and_calculate_kpis(self, dataset: Dataset, profile: DatasetProfile,
                                      domain: DomainDetection) -> list[KPIDefinition]:
        table_name = table_manager.table_for(dataset) or table_manager.register(dataset)
        kpis = kpi_recommender.recommend(profile, domain)
        return [kpi_calculator.calculate(table_name, k) for k in kpis]

    def numeric_summary(self, df: pd.DataFrame, column: str) -> dict:
        return statistics_engine.numeric_summary(df[column])

    def categorical_summary(self, df: pd.DataFrame, column: str) -> dict:
        return statistics_engine.categorical_summary(df[column])

    def correlation_matrix(self, df: pd.DataFrame, columns: list[str], method: str = "pearson"):
        return correlation_engine.numeric_correlation_matrix(df, columns, method)

    def top_correlations(self, corr_matrix, top_n: int = 10):
        return correlation_engine.top_correlated_pairs(corr_matrix, top_n=top_n)

    def detect_trend(self, df: pd.DataFrame, date_col: str, value_col: str) -> dict:
        return trend_engine.detect_trend(df, date_col, value_col)

    def analyze_anomalies(self, df: pd.DataFrame, column: str) -> dict:
        return anomaly_detection_engine.analyze_column(df, column)

    def generate_insights(self, domain: DomainDetection, evidence: dict):
        return insight_generator.generate(domain, evidence)

    def run_sql(self, sql: str):
        return query_executor.run(sql)

    def explain_sql(self, sql: str) -> dict:
        return query_explainer.explain(sql)

    def ensure_registered(self, dataset: Dataset) -> str:
        return table_manager.table_for(dataset) or table_manager.register(dataset)

    def ask_ai_analyst(self, dataset: Dataset, question: str):
        return analyst_agent.ask(dataset, question)


analytics_service = AnalyticsService()
