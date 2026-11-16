"""
Workflow Service.

Defines the AppState container tracked across the Streamlit session and
provides orchestration helpers that chain multiple services together
for common multi-step flows (e.g. "run full analysis pipeline").
Streamlit pages read/write AppState; they never hold raw engine state
themselves.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from models.analysis import ChartRecommendation, DomainDetection, KPIDefinition
from models.dataset import Dataset
from models.profile import DatasetProfile
from models.quality import QualityReport
from models.transformation import Transformation
from services.analytics_service import analytics_service
from services.cleaning_service import cleaning_service
from services.dashboard_service import dashboard_service


@dataclass
class AppState:
    """Single source of truth for the active session. Stored in st.session_state."""
    original_dataset: Optional[Dataset] = None
    working_dataset: Optional[Dataset] = None          # currently displayed/analyzed version
    dataset_versions: list[Dataset] = field(default_factory=list)

    profile: Optional[DatasetProfile] = None
    quality_report: Optional[QualityReport] = None

    cleaning_plan: list[Transformation] = field(default_factory=list)
    applied_transformations: list[Transformation] = field(default_factory=list)
    cleaning_comparison: Optional[dict] = None

    domain: Optional[DomainDetection] = None
    kpis: list[KPIDefinition] = field(default_factory=list)
    dashboard_plan: Optional[object] = None

    sql_history: list[dict] = field(default_factory=list)
    ai_chat_history: list[dict] = field(default_factory=list)

    def reset(self) -> None:
        self.__init__()

    def has_dataset(self) -> bool:
        return self.working_dataset is not None


class WorkflowService:
    def run_profiling_and_quality(self, state: AppState) -> None:
        profile, report = cleaning_service.evaluate_quality(state.working_dataset)
        state.profile = profile
        state.quality_report = report

    def run_domain_and_kpis(self, state: AppState) -> None:
        state.domain = analytics_service.detect_domain(state.profile)
        state.kpis = analytics_service.recommend_and_calculate_kpis(
            state.working_dataset, state.profile, state.domain
        )

    def run_dashboard_plan(self, state: AppState) -> None:
        state.dashboard_plan = dashboard_service.build_plan(state.profile, state.kpis, state.domain)

    def run_full_pipeline(self, state: AppState) -> None:
        """Runs profiling -> quality -> domain -> KPIs -> dashboard plan in one go."""
        self.run_profiling_and_quality(state)
        self.run_domain_and_kpis(state)
        self.run_dashboard_plan(state)

    def promote_cleaned_dataset(self, state: AppState, cleaned_dataset: Dataset,
                                 updated_transformations: list[Transformation]) -> None:
        state.applied_transformations = updated_transformations
        state.cleaning_comparison = cleaning_service.validate_cleaning(
            state.original_dataset, cleaned_dataset
        )
        state.dataset_versions.append(cleaned_dataset)
        state.working_dataset = cleaned_dataset
        # Re-run downstream analysis on the cleaned version
        self.run_full_pipeline(state)


workflow_service = WorkflowService()
