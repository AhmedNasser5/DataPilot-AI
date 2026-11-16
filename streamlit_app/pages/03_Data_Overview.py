"""Data Overview page: Dataset Intelligence Report + column-level profiling."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from services.workflow_service import workflow_service
from streamlit_app.components.data_tables import show_column_profile_table, show_dataframe
from streamlit_app.components.metrics import metric_row
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.status import no_dataset_notice
from streamlit_app.components.theme import apply_theme, hero, section_title

apply_theme("Data Overview", "📋")
state = get_state()
render_sidebar(state)

hero("Dataset Intelligence Report", "A complete, evidence-based summary of what's actually in your data.")

if not state.has_dataset():
    no_dataset_notice()
    st.stop()

if state.profile is None or state.quality_report is None:
    with st.spinner("Profiling dataset..."):
        workflow_service.run_full_pipeline(state)

profile = state.profile
report = state.quality_report
domain = state.domain
ds = state.working_dataset

section_title("Summary")
metric_row([
    ("Dataset", ds.metadata.original_filename, f"Format: {ds.metadata.file_format}"),
    ("Detected Domain", domain.domain if domain else "—", f"Confidence: {domain.confidence:.0%}" if domain else ""),
    ("Rows", f"{profile.row_count:,}", f"{profile.estimated_memory_mb} MB estimated"),
    ("Columns", f"{profile.column_count}", ""),
])
metric_row([
    ("Overall Data Quality", f"{report.overall_score}/100", ""),
    ("Critical Issues", str(report.issues_by_severity()["critical"]), ""),
    ("Medium+ Issues", str(report.issues_by_severity()["medium"] + report.issues_by_severity()["high"]), ""),
    ("Suggested Cleaning Ops", str(len(state.cleaning_plan) if state.cleaning_plan else 0),
     "Visit Cleaning Studio to generate" if not state.cleaning_plan else ""),
])

if domain and domain.evidence:
    with st.expander("Why this domain?"):
        for e in domain.evidence:
            st.markdown(f"- {e}")

section_title("Column Profiles")
show_column_profile_table(profile)

with st.expander("🔎 Inspect a single column in depth"):
    col_name = st.selectbox("Column", options=list(profile.columns.keys()))
    c = profile.columns[col_name]
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Type & Semantics**")
        st.write(f"Detected type: `{c.detected_type}`")
        st.write(f"Pandas dtype: `{c.pandas_dtype}`")
        for g in c.semantic_types:
            st.write(f"- {g.label}: {g.confidence:.0%} confidence — {g.evidence}")
    with c2:
        st.markdown("**Completeness & Cardinality**")
        st.write(f"Nulls: {c.null_count} ({c.null_percentage}%)")
        st.write(f"Unique: {c.unique_count} ({c.unique_percentage}%)")
        st.write(f"Flags: {', '.join(c.flags) or '—'}")
    with c3:
        st.markdown("**Statistics**")
        if c.mean is not None:
            st.write(f"Mean: {c.mean:.4g} · Median: {c.median:.4g} · Std: {c.std:.4g}")
            st.write(f"Min: {c.minimum:.4g} · Max: {c.maximum:.4g}")
            if c.skewness is not None:
                st.write(f"Skewness: {c.skewness:.3f} · Kurtosis: {c.kurtosis:.3f}")
        st.write(f"Most frequent: {c.most_frequent_values[:3]}")

section_title("Raw Data Preview")
show_dataframe(ds.dataframe, max_preview_rows=500)
