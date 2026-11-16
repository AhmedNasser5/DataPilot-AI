"""Plans the overall dashboard structure: which KPI cards + which charts, in what order."""
from __future__ import annotations

from core.dashboard.chart_recommender import chart_recommender
from models.analysis import ChartRecommendation, DomainDetection, KPIDefinition
from models.profile import DatasetProfile


class DashboardPlan:
    def __init__(self, kpi_cards: list[KPIDefinition], charts: list[ChartRecommendation], domain: DomainDetection):
        self.kpi_cards = kpi_cards
        self.charts = charts
        self.domain = domain


class DashboardPlanner:
    def plan(self, profile: DatasetProfile, kpis: list[KPIDefinition], domain: DomainDetection) -> DashboardPlan:
        # Prioritize calculable KPIs for the top KPI-card row
        calculable = [k for k in kpis if k.calculable][:6]
        charts = chart_recommender.recommend(profile, max_charts=8)
        return DashboardPlan(kpi_cards=calculable, charts=charts, domain=domain)


dashboard_planner = DashboardPlanner()
