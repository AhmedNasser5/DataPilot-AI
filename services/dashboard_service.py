"""Dashboard Service — facade over the dashboard planner and chart generator."""
from __future__ import annotations

import pandas as pd

from core.dashboard.dashboard_generator import dashboard_generator
from core.dashboard.dashboard_planner import dashboard_planner
from models.analysis import ChartRecommendation, DomainDetection, KPIDefinition
from models.profile import DatasetProfile


class DashboardService:
    def build_plan(self, profile: DatasetProfile, kpis: list[KPIDefinition], domain: DomainDetection):
        return dashboard_planner.plan(profile, kpis, domain)

    def build_figure(self, df: pd.DataFrame, chart: ChartRecommendation):
        return dashboard_generator.build_figure(df, chart)


dashboard_service = DashboardService()
