"""Data Quality page: transparent scoring dimensions + full issue list."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from services.workflow_service import workflow_service
from streamlit_app.components.metrics import metric_row
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.status import issue_badge, no_dataset_notice
from streamlit_app.components.theme import apply_theme, hero, section_title

apply_theme("Data Quality", "✅")
state = get_state()
render_sidebar(state)

hero("Data Quality Engine", "A transparent, formula-based quality score — never an arbitrary AI guess.")

if not state.has_dataset():
    no_dataset_notice()
    st.stop()

if state.quality_report is None:
    with st.spinner("Evaluating data quality..."):
        workflow_service.run_full_pipeline(state)

report = state.quality_report

section_title("Overall Score")
col1, col2 = st.columns([1, 2])
with col1:
    st.metric("Overall Data Quality Score", f"{report.overall_score} / 100")
with col2:
    st.caption(
        "Formula: weighted average of Completeness (35%), Validity (25%), "
        "Consistency (20%), and Uniqueness (20%). Every sub-score is computed directly "
        "from detected issues — nothing here is an AI estimate."
    )

metric_row([(d.name, f"{d.score}/100", "") for d in report.dimensions.values()])

with st.expander("📐 How each dimension score was calculated"):
    for d in report.dimensions.values():
        st.markdown(f"**{d.name}** — `{d.explanation}`")

st.markdown("---")
section_title(f"Detected Issues ({len(report.issues)})")
severity_counts = report.issues_by_severity()
metric_row([(sev.title(), str(count), "") for sev, count in severity_counts.items()])

if not report.issues:
    st.success("No data-quality issues were detected by any engine. 🎉")
else:
    rows = []
    for issue in sorted(report.issues, key=lambda i: {"critical": 0, "high": 1, "medium": 2, "low": 3}[i.severity.value]):
        rows.append({
            "Severity": issue.severity.value.upper(),
            "Category": issue.category,
            "Column": issue.column or "(dataset-wide)",
            "Description": issue.description,
            "Detection Method": issue.detection_method,
            "Confidence": f"{issue.confidence:.0%}",
            "Affected Rows": issue.affected_rows,
        })
    df_issues = pd.DataFrame(rows)

    sev_filter = st.multiselect("Filter by severity", options=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                                 default=["CRITICAL", "HIGH", "MEDIUM", "LOW"])
    cat_filter = st.multiselect("Filter by category", options=sorted(df_issues["Category"].unique()),
                                 default=sorted(df_issues["Category"].unique()))
    filtered = df_issues[df_issues["Severity"].isin(sev_filter) & df_issues["Category"].isin(cat_filter)]
    st.dataframe(filtered, use_container_width=True, height=440)

st.page_link("pages/05_Cleaning_Studio.py", label="➡️ Fix these issues in the Cleaning Studio", icon="🧹")
