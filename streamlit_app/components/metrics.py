"""Reusable metric-card grid rendering."""
from __future__ import annotations

import streamlit as st


def human_number(val: float) -> str:
    """Abbreviates large numbers for executive-style KPI cards: 1.2K, 3.4M, 2.1B."""
    try:
        val = float(val)
    except (TypeError, ValueError):
        return str(val)
    sign = "-" if val < 0 else ""
    val = abs(val)
    for threshold, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if val >= threshold:
            return f"{sign}{val / threshold:,.1f}{suffix}"
    if val == int(val):
        return f"{sign}{int(val):,}"
    return f"{sign}{val:,.2f}"


def format_kpi_value(val) -> tuple[str, str]:
    """
    Formats a KPI value for a compact executive card.
    Returns (headline, subtext).

    - Scalars (int/float/str) -> abbreviated number / the raw string as headline.
    - dict (single-row, multi-column SQL result, e.g. "top category") -> the
      first (usually categorical) field as headline, the rest as subtext.
    - list (multi-row series/category breakdown) -> NOT meant for a KPI card at
      all (it belongs in a chart) — summarized instead of dumped raw.
    """
    if isinstance(val, bool):
        return (str(val), "")
    if isinstance(val, (int, float)):
        return (human_number(val), "")
    if isinstance(val, dict):
        values = list(val.values())
        if not values:
            return ("—", "")
        headline = values[0]
        headline_str = human_number(headline) if isinstance(headline, (int, float)) else str(headline)
        subtext = " · ".join(
            human_number(v) if isinstance(v, (int, float)) else str(v) for v in values[1:]
        )
        return (headline_str, subtext)
    if isinstance(val, list):
        return (f"{len(val)} categories", "See the Dashboard charts or KPI Explorer for the full breakdown")
    return (str(val), "")


def metric_card(label: str, value: str, sub: str = "") -> str:
    return (
        f'<div class="dp-metric-card">'
        f'<div class="dp-metric-label">{label}</div>'
        f'<div class="dp-metric-value">{value}</div>'
        f'<div class="dp-metric-sub">{sub}</div>'
        f'</div>'
    )


def metric_row(cards: list[tuple[str, str, str]]) -> None:
    """cards: list of (label, value, sub)"""
    cols = st.columns(len(cards))
    for col, (label, value, sub) in zip(cols, cards):
        with col:
            st.markdown(metric_card(label, value, sub), unsafe_allow_html=True)
