"""
Shared Plotly styling so every chart in the app matches the dark,
BI-tool aesthetic (dark canvas, cyan/teal accents, clean gridlines)
instead of the mismatched default template.
"""
from __future__ import annotations

from streamlit_app.components.theme import (
    ACCENT, ACCENT_VIOLET, CHART_COLORWAY, PRIMARY, PRIMARY_SOFT,
    SURFACE_BORDER, TEXT_MAIN, TEXT_MUTED,
)

GRID_COLOR = "rgba(148,163,184,0.14)"


def style_figure(fig, title: str | None = None, height: int | None = None):
    """Applies the shared dark BI theme to any Plotly figure in-place-ish
    (returns the same figure for chaining)."""
    layout_kwargs = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT_MAIN, size=13),
        colorway=CHART_COLORWAY,
        margin=dict(l=10, r=10, t=48, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_MUTED)),
        hoverlabel=dict(bgcolor="#131C2E", font=dict(color=TEXT_MAIN), bordercolor=SURFACE_BORDER),
    )
    # Only touch the title if the caller explicitly wants to override it —
    # otherwise keep whatever title the chart-generation layer already set.
    if title is not None:
        layout_kwargs["title"] = dict(text=title, font=dict(color=TEXT_MAIN, size=15, family="Inter, sans-serif"))
    fig.update_layout(**layout_kwargs)
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, color=TEXT_MUTED, linecolor=SURFACE_BORDER)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, color=TEXT_MUTED, linecolor=SURFACE_BORDER)
    if height:
        fig.update_layout(height=height)
    return fig
