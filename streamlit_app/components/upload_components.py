"""Small UI helpers for the Upload Data page (sheet picker, format badge)."""
from __future__ import annotations

import streamlit as st

from models.dataset import SheetInfo


def render_sheet_picker(sheets: list[SheetInfo]) -> str:
    st.markdown("**This workbook has multiple sheets.** Choose one to analyze:")
    labels = [f"{s.name}  ({s.n_rows:,} rows × {s.n_cols} cols)" for s in sheets]
    idx = st.selectbox("Sheet", options=range(len(sheets)), format_func=lambda i: labels[i])
    return sheets[idx].name


def render_format_badge(detected) -> None:
    st.markdown(
        f"**Detected format:** `{detected.format}` &nbsp;·&nbsp; "
        f"**Confidence:** {detected.confidence:.0%} &nbsp;·&nbsp; "
        f"*{detected.reason}*"
    )
