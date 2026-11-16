"""Session-state bootstrap for the Streamlit app. Every page calls get_state()."""
from __future__ import annotations

import streamlit as st

from services.workflow_service import AppState

_STATE_KEY = "datapilot_app_state"


def get_state() -> AppState:
    if _STATE_KEY not in st.session_state:
        st.session_state[_STATE_KEY] = AppState()
    return st.session_state[_STATE_KEY]


def reset_state() -> None:
    st.session_state[_STATE_KEY] = AppState()
