"""Transformation History: full audit trail + original-vs-cleaned comparison."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from models.transformation import TransformationStatus
from services.export_service import export_service
from streamlit_app.components.metrics import metric_row
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.status import no_dataset_notice
from streamlit_app.components.theme import apply_theme, hero, section_title

apply_theme("Transformation History", "📜")
state = get_state()
render_sidebar(state)

hero("Transformation Audit Trail", "Every applied transformation, fully inspectable and reproducible.")

if not state.has_dataset():
    no_dataset_notice()
    st.stop()

if not state.applied_transformations:
    st.info(
        "No transformations have been **applied** yet for this session. Uploading a file only profiles "
        "and scores it — nothing is changed until you go to **Cleaning Studio**, review the proposed fixes, "
        "mark them Approve/Reject, and click **'Apply Approved Transformation(s)'**. This page will fill in "
        "right after that."
    )
    st.page_link("pages/05_Cleaning_Studio.py", label="➡️ Go to Cleaning Studio", icon="🧹")
    st.stop()

comparison = state.cleaning_comparison
if comparison:
    section_title("Original vs. Cleaned Comparison")
    metric_row([
        ("Rows", f"{comparison['row_count_before']} → {comparison['row_count_after']}", ""),
        ("Columns", f"{comparison['column_count_before']} → {comparison['column_count_after']}", ""),
        ("Quality Score", f"{comparison['quality_score_before']} → {comparison['quality_score_after']}",
         f"Δ {comparison['quality_delta']:+}"),
        ("New Issues Introduced", str(len(comparison["possible_new_issues"])), ""),
    ])
    if comparison["possible_new_issues"]:
        with st.expander("⚠️ Possible new issues introduced by cleaning"):
            for issue in comparison["possible_new_issues"]:
                st.markdown(f"- {issue}")
    else:
        st.success("Validated: cleaning did not introduce any new detectable issue categories.")

st.markdown("---")
section_title(f"Applied Transformations ({len(state.applied_transformations)})")

rows = []
for t in state.applied_transformations:
    rows.append({
        "ID": t.transformation_id,
        "Status": t.status.value,
        "Column": t.column or "(dataset-wide)",
        "Action": t.action_label,
        "Reason": t.reason,
        "Confidence": f"{t.confidence:.0%}",
        "Affected Rows": t.affected_rows,
        "Timestamp": t.timestamp,
        "Error": t.error or "",
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, height=420)

with st.expander("🔎 Inspect a single transformation"):
    tid = st.selectbox("Transformation ID", options=[t.transformation_id for t in state.applied_transformations])
    t = next(x for x in state.applied_transformations if x.transformation_id == tid)
    st.markdown(f"**Detection method:** {t.detection_method}")
    st.markdown(f"**Reversibility:** {t.reversibility}")
    st.markdown("**Reproducible Python logic:**")
    st.code(t.python_logic or "# not applicable", language="python")
    if t.sql_logic:
        st.markdown("**Reproducible SQL logic:**")
        st.code(t.sql_logic, language="sql")

st.markdown("---")
section_title("Export the audit trail")
c1, c2 = st.columns(2)
with c1:
    st.download_button(
        "📄 Download as reproducible Python script",
        data=export_service.export_transformations_python(state.applied_transformations),
        file_name="datapilot_cleaning_script.py", mime="text/x-python",
    )
with c2:
    st.download_button(
        "🗄️ Download as SQL script",
        data=export_service.export_transformations_sql(state.applied_transformations),
        file_name="datapilot_cleaning_script.sql", mime="text/sql",
    )
