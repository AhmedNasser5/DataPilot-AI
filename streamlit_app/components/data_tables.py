"""Styled dataframe rendering helpers."""
from __future__ import annotations

import pandas as pd
import streamlit as st


def show_dataframe(df: pd.DataFrame, height: int = 420, max_preview_rows: int | None = None) -> None:
    data = df.head(max_preview_rows) if max_preview_rows else df
    st.dataframe(data, use_container_width=True, height=height)


def show_column_profile_table(profile) -> None:
    rows = []
    for name, c in profile.columns.items():
        semantic = ", ".join(f"{g.label} ({g.confidence:.0%})" for g in c.semantic_types[:2])
        rows.append({
            "Column": name,
            "Type": c.detected_type,
            "Nulls %": c.null_percentage,
            "Unique": c.unique_count,
            "Semantic": semantic or "—",
            "Flags": ", ".join(c.flags) or "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=420)
