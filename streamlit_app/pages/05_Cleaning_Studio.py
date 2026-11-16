"""Cleaning Studio: generate a cleaning plan, preview each step, approve/reject, apply."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from ai.cleaning_advisor import cleaning_advisor
from config.settings import settings
from models.transformation import CleaningLevel, TransformationStatus
from services.cleaning_service import cleaning_service
from services.workflow_service import workflow_service
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.status import no_dataset_notice
from streamlit_app.components.theme import apply_theme, hero, section_title

apply_theme("Cleaning Studio", "🧹")
state = get_state()
render_sidebar(state)

hero("Cleaning Studio", "Review every proposed transformation with full before/after evidence before it touches your data.")

if not state.has_dataset():
    no_dataset_notice()
    st.stop()

if state.profile is None or state.quality_report is None:
    with st.spinner("Preparing quality report..."):
        workflow_service.run_full_pipeline(state)

if not state.cleaning_plan:
    if st.button("🧠 Generate Cleaning Plan", type="primary"):
        with st.spinner("Analyzing issues and building a cleaning plan..."):
            state.cleaning_plan = cleaning_service.build_plan(state.working_dataset, state.profile, state.quality_report)
        st.rerun()
    st.info("No cleaning plan generated yet. Click the button above to analyze detected issues.")
    st.stop()

LEVEL_LABELS = {
    CleaningLevel.SAFE_AUTOMATIC: "🟢 Level 1 — Safe Automatic",
    CleaningLevel.AI_ASSISTED: "🟡 Level 2 — AI-Assisted Suggested",
    CleaningLevel.ADVANCED_CONTEXTUAL: "🟠 Level 3 — Advanced Contextual",
}

section_title(f"Proposed Transformations ({len(state.cleaning_plan)})")
st.caption("Nothing is applied until you click **Apply Approved Transformations** at the bottom. "
           "The original dataset is never overwritten.")

for level in CleaningLevel:
    level_items = [t for t in state.cleaning_plan if t.level == level]
    if not level_items:
        continue
    st.markdown(f"### {LEVEL_LABELS[level]}")
    for t in level_items:
        with st.container(border=True):
            top = st.columns([3, 1, 1])
            with top[0]:
                st.markdown(f"**{t.action_label}** — column `{t.column or '(dataset-wide)'}`")
                st.caption(t.issue)
            with top[1]:
                st.metric("Confidence", f"{t.confidence:.0%}")
            with top[2]:
                st.metric("Affected rows", t.affected_rows)

            reason_col, ai_col = st.columns([1, 1])
            with reason_col:
                st.markdown(f"**Reason:** {t.reason}")
                st.caption(f"Detection method: {t.detection_method} · Reversibility: {t.reversibility}")
            with ai_col:
                if settings.ai_enabled() and level != CleaningLevel.SAFE_AUTOMATIC:
                    if st.button("🤖 AI explanation", key=f"ai_{t.transformation_id}"):
                        with st.spinner("Asking the AI to explain..."):
                            st.info(cleaning_advisor.explain(t))

            if st.toggle("👁️ Show before/after preview", key=f"prev_{t.transformation_id}"):
                preview = cleaning_service.preview_transformation(state.working_dataset, t)
                pc1, pc2 = st.columns(2)
                with pc1:
                    st.markdown("**Before**")
                    st.code(preview["before_sample"], language="python")
                with pc2:
                    st.markdown("**After**")
                    st.code(preview["after_sample"], language="python")
                st.caption(f"Rows: {preview['row_count_before']} → {preview['row_count_after']} · "
                           f"Expected impact: {preview['expected_impact']}")
                if preview["error"]:
                    st.error(f"Preview error: {preview['error']}")

            decision = st.radio(
                "Decision", options=["Pending", "Approve", "Reject"],
                key=f"decision_{t.transformation_id}", horizontal=True,
                index={"proposed": 0, "approved": 1, "rejected": 2}.get(t.status.value, 0),
            )
            t.status = {
                "Pending": TransformationStatus.PROPOSED,
                "Approve": TransformationStatus.APPROVED,
                "Reject": TransformationStatus.REJECTED,
            }[decision]

st.markdown("---")
approved_count = sum(1 for t in state.cleaning_plan if t.status == TransformationStatus.APPROVED)
c1, c2 = st.columns([1, 3])
with c1:
    apply_clicked = st.button(f"✅ Apply {approved_count} Approved Transformation(s)", type="primary",
                               disabled=approved_count == 0)
with c2:
    st.caption("This creates a NEW dataset version (v2). Your original upload is always preserved.")

if apply_clicked:
    with st.spinner("Applying approved transformations and re-validating..."):
        cleaned_dataset, updated = cleaning_service.apply_approved(state.working_dataset, state.cleaning_plan)
        workflow_service.promote_cleaned_dataset(state, cleaned_dataset, updated)
        state.cleaning_plan = []  # plan consumed; regenerate against new version if desired
    st.success(f"✅ Applied transformations. New dataset version: **{cleaned_dataset.version}**.")
    st.page_link("pages/06_Transformation_History.py", label="➡️ View the Transformation Audit Trail", icon="📜")
