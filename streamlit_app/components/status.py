"""Status, badge, and alert rendering helpers."""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.theme import badge, severity_badge_kind


def issue_badge(severity: str) -> str:
    return badge(severity.upper(), severity_badge_kind(severity))


def ai_disabled_notice():
    st.warning(
        "🤖 AI reasoning features are currently disabled because no `LLM_API_KEY` is configured. "
        "Deterministic features (profiling, quality, cleaning, SQL, KPIs) work fully without AI. "
        "Set `LLM_PROVIDER` and `LLM_API_KEY` in your `.env` to enable natural-language explanations, "
        "the AI Analyst chat, and NL-to-SQL.",
        icon="🤖",
    )


def no_dataset_notice():
    st.warning("No dataset is loaded yet. Please go to **📤 Upload Data** first.", icon="📂")
