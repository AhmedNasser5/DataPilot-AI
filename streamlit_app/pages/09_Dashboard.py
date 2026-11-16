"""Dashboard: auto-generated, context-aware KPI cards + chart grid."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from services.workflow_service import workflow_service
from streamlit_app.components.charts import render_chart_grid
from streamlit_app.components.metrics import format_kpi_value, metric_row
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.status import no_dataset_notice
from streamlit_app.components.theme import apply_theme, hero, section_title

apply_theme("Dashboard", "📊")
state = get_state()
render_sidebar(state)

hero("Auto-Generated Dashboard", "A dashboard shaped by YOUR data — no generic, meaningless charts.")

if not state.has_dataset():
    no_dataset_notice()
    st.stop()

if state.dashboard_plan is None:
    with st.spinner("Building your dashboard..."):
        workflow_service.run_full_pipeline(state)

plan = state.dashboard_plan
ds = state.working_dataset

section_title(f"{plan.domain.domain} — Key Metrics")
# Executive KPI row: only scalar / single-row results belong here (3-5 cards).
# Multi-row category breakdowns are analytical detail, not a headline number —
# those are already covered by the ranking/composition charts below.
executive_kpis = [k for k in plan.kpi_cards if not isinstance(k.value, list)][:5]
if executive_kpis:
    cards = []
    for k in executive_kpis:
        headline, subtext = format_kpi_value(k.value)
        cards.append((k.name, headline, subtext))
    for i in range(0, len(cards), 4):
        metric_row(cards[i:i + 4])
else:
    st.info("No calculable KPIs were found for this dataset yet. Check the KPI Explorer for details.")

st.markdown("---")
section_title(f"Recommended Visualizations ({len(plan.charts)})")
if plan.charts:
    render_chart_grid(ds.dataframe, plan.charts, columns_per_row=2)
else:
    st.info("Not enough structure (dates/categories/numeric columns) was detected to recommend charts yet.")

st.markdown("---")
if st.button("🔄 Regenerate dashboard plan"):
    with st.spinner("Rebuilding..."):
        workflow_service.run_dashboard_plan(state)
    st.rerun()
