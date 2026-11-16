"""Shared sidebar: branding + live dataset status, shown on every page."""
from __future__ import annotations

import streamlit as st

from config.settings import settings
from services.workflow_service import AppState
from streamlit_app.components.theme import chip


def render_sidebar(state: AppState) -> None:
    with st.sidebar:
        st.markdown("## 🧭 DataPilot AI")
        st.caption("Upload Your Data. Understand It. Clean It. Analyze It.")
        st.markdown("---")

        if state.has_dataset():
            ds = state.working_dataset
            st.markdown("**Active Dataset**")
            st.markdown(chip(ds.metadata.original_filename, "📄"), unsafe_allow_html=True)
            st.markdown(f"🔖 Version: **{ds.version}** — {ds.version_label}")
            st.markdown(f"📐 {ds.metadata.row_count:,} rows × {ds.metadata.column_count} cols")
            if state.quality_report:
                st.markdown(f"⭐ Quality Score: **{state.quality_report.overall_score}/100**")
            if state.domain:
                st.markdown(f"🏷️ Domain: **{state.domain.domain}**")
        else:
            st.info("No dataset loaded yet. Go to **Upload Data** to get started.")

        st.markdown("---")
        ai_status = "🟢 Enabled" if settings.ai_enabled() else "🔴 Disabled (no API key)"
        st.markdown(f"**AI Reasoning Layer:** {ai_status}")
        st.markdown(
            chip(settings.llm_provider, "🔌") + " " + chip(settings.model_name, "🧠"),
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.caption("© DataPilot AI — a real analytics engine, not a demo.")
