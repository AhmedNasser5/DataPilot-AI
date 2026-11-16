"""Renders ChartRecommendation objects as Plotly figures in a responsive grid."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services.dashboard_service import dashboard_service
from streamlit_app.components.plot_theme import style_figure


def render_chart_grid(df: pd.DataFrame, charts: list, columns_per_row: int = 2) -> None:
    for i in range(0, len(charts), columns_per_row):
        row_charts = charts[i:i + columns_per_row]
        cols = st.columns(len(row_charts))
        for col, chart in zip(cols, row_charts):
            with col:
                with st.container(border=True):
                    fig = dashboard_service.build_figure(df, chart)
                    if fig is not None:
                        style_figure(fig, height=340)
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    st.caption(f"**Why this chart:** {chart.reason}")
                    st.caption(f"**Purpose:** {chart.purpose}")
