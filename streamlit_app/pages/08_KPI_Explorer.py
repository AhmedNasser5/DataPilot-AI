"""KPI Explorer: domain detection + KPIs actually calculated from the data via SQL."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from ai.domain_reasoner import domain_reasoner
from config.settings import settings
from services.workflow_service import workflow_service
from streamlit_app.components.metrics import human_number, metric_row
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.status import no_dataset_notice
from streamlit_app.components.theme import apply_theme, hero, section_title

apply_theme("KPI Explorer", "📈")
state = get_state()
render_sidebar(state)

hero("KPI Explorer", "KPIs recommended from your dataset's structure and domain — every value actually calculated via SQL.")

if not state.has_dataset():
    no_dataset_notice()
    st.stop()

if state.domain is None or not state.kpis:
    with st.spinner("Detecting domain and calculating KPIs..."):
        workflow_service.run_full_pipeline(state)

domain = state.domain
section_title("Detected Business Domain")
c1, c2 = st.columns([1, 3])
with c1:
    st.metric("Domain", domain.domain, f"{domain.confidence:.0%} confidence")
with c2:
    if settings.ai_enabled():
        st.markdown(domain_reasoner.explain(domain, list(state.profile.columns.keys())))
    else:
        st.markdown("; ".join(domain.evidence) or "No strong domain-specific evidence found.")

if domain.alternative_domains:
    with st.expander("Other possible domains considered"):
        for d, conf in domain.alternative_domains:
            st.write(f"- {d}: {conf:.0%}")

st.markdown("---")
section_title(f"Calculated KPIs ({len(state.kpis)})")

calculable = [k for k in state.kpis if k.calculable]
not_calculable = [k for k in state.kpis if not k.calculable]

def _format_kpi_value(val) -> str:
    if isinstance(val, (int, float)):
        return human_number(val)
    if isinstance(val, dict):
        # Single-row, multi-column result (e.g. "top category": {"category": "...", "total": ...})
        parts = [human_number(v) if isinstance(v, (int, float)) else str(v) for v in val.values()]
        return " · ".join(parts)
    if isinstance(val, list):
        # Multi-row series result (e.g. a trend broken down by period) — summarize instead of dumping raw rows
        return f"{len(val)} row(s) — see the Dashboard charts for the full breakdown"
    return str(val)


if calculable:
    cards = []
    for k in calculable:
        cards.append((k.name, _format_kpi_value(k.value), k.definition[:60]))
    for i in range(0, len(cards), 4):
        metric_row(cards[i:i + 4])

    with st.expander("🧮 See the exact SQL behind each KPI"):
        for k in calculable:
            st.markdown(f"**{k.name}**")
            st.code(k.sql, language="sql")
            st.caption(f"Definition: {k.definition} · Formula: `{k.formula}` · Method: {k.calculation_method}")
            st.markdown("---")
else:
    st.info("No KPIs could be calculated from the current columns.")

if not_calculable:
    with st.expander(f"⚠️ KPIs that could NOT be calculated ({len(not_calculable)})"):
        for k in not_calculable:
            st.markdown(f"**{k.name}** — {k.reason_not_calculable}")

st.page_link("pages/09_Dashboard.py", label="➡️ See these KPIs on the Dashboard", icon="📊")
