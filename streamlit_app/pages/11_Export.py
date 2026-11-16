"""Export: download cleaned data and every analysis artifact."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from services.export_service import export_service
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.status import no_dataset_notice
from streamlit_app.components.theme import apply_theme, hero, section_title

apply_theme("Export", "📤")
state = get_state()
render_sidebar(state)

hero("Export Center", "Take your cleaned data and analysis with you.")

if not state.has_dataset():
    no_dataset_notice()
    st.stop()

ds = state.working_dataset

section_title(f"Export dataset — version {ds.version} ({ds.version_label})")
fmt = st.radio("Format", options=["CSV", "XLSX", "JSON", "Parquet"], horizontal=True)
if st.button("⬇️ Prepare download", type="primary"):
    data = export_service.export_dataset(ds.dataframe, fmt)
    mime = {
        "CSV": "text/csv", "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "JSON": "application/json", "Parquet": "application/octet-stream",
    }[fmt]
    ext = {"CSV": "csv", "XLSX": "xlsx", "JSON": "json", "Parquet": "parquet"}[fmt]
    st.download_button(f"Download {fmt}", data=data, file_name=f"datapilot_dataset_{ds.version}.{ext}", mime=mime)

st.markdown("---")
section_title("Export analysis reports")
c1, c2, c3 = st.columns(3)
with c1:
    if state.quality_report:
        st.download_button("📊 Data Quality Report (JSON)",
                            data=export_service.export_quality_report(state.quality_report),
                            file_name="quality_report.json", mime="application/json")
    else:
        st.caption("Run Data Quality page first.")
with c2:
    if state.profile:
        st.download_button("🧬 Dataset Profile (JSON)",
                            data=export_service.export_profile_report(state.profile),
                            file_name="dataset_profile.json", mime="application/json")
    else:
        st.caption("Run Data Overview page first.")
with c3:
    if state.quality_report and state.profile:
        st.download_button("📝 Full Analysis Summary (Markdown)",
                            data=export_service.export_markdown_summary(
                                ds.metadata.original_filename, state.quality_report, state.profile, state.kpis),
                            file_name="analysis_summary.md", mime="text/markdown")
    else:
        st.caption("Complete profiling first.")

st.markdown("---")
section_title("Export cleaning audit trail")
if state.applied_transformations:
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("🐍 Python cleaning script",
                            data=export_service.export_transformations_python(state.applied_transformations),
                            file_name="cleaning_script.py", mime="text/x-python")
    with c2:
        st.download_button("🗄️ SQL cleaning script",
                            data=export_service.export_transformations_sql(state.applied_transformations),
                            file_name="cleaning_script.sql", mime="text/sql")
else:
    st.caption("No transformations have been applied yet — visit the Cleaning Studio.")
