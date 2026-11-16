"""
Premium dark analytics theme shared by every Streamlit page.

Design language: dark navy surface, cyan/sky accent, soft glow cards,
an animated node/aurora background layer, and buttons that are legible
at rest (not just on hover). Paired with .streamlit/config.toml, which
locks the *native* widget theme (dataframes, code chips, inputs,
buttons) to the same dark palette so nothing renders as a jarring
black box against a light surface.
"""
from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Palette — dark navy surface + cyan/sky accent (mirrors .streamlit/config.toml)
# ---------------------------------------------------------------------------
BG = "#0B1220"                # app background
BG_ELEVATED = "#0E1729"       # slightly lighter panel background
SURFACE = "#121B2E"           # card surface
SURFACE_BORDER = "rgba(148,163,184,0.14)"

PRIMARY = "#38BDF8"           # sky-400 — primary accent
PRIMARY_SOFT = "#7DD3FC"      # sky-300 — highlights/gradients
PRIMARY_DEEP = "#0369A1"      # sky-700 — depth in gradients
ACCENT = "#2DD4BF"            # teal-400 — secondary accent (Power-BI-style highlight)
ACCENT_VIOLET = "#818CF8"     # indigo-400 — tertiary accent for variety in charts

SUCCESS = "#34D399"
WARNING = "#FBBF24"
DANGER = "#F87171"

TEXT_MAIN = "#E6EDF7"
TEXT_MUTED = "#94A3B8"
TEXT_FAINT = "#64748B"

CHART_COLORWAY = [PRIMARY, ACCENT, ACCENT_VIOLET, PRIMARY_SOFT, "#F472B6", "#FBBF24", "#4ADE80", "#FB923C"]

# Icon-chip tints (dark-surface friendly)
_CHIP_COLORS = [
    ("rgba(56,189,248,0.14)", PRIMARY),
    ("rgba(45,212,191,0.14)", ACCENT),
    ("rgba(129,140,248,0.14)", ACCENT_VIOLET),
    ("rgba(52,211,153,0.14)", SUCCESS),
    ("rgba(251,191,36,0.14)", WARNING),
]

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

.stApp {{
    background: radial-gradient(circle at 12% 8%, #0F2038 0%, {BG} 42%) fixed;
}}

section.main .block-container {{
    position: relative;
    z-index: 1;
    padding-top: 1.6rem;
}}

/* ---------------------------------------------------------------------
   Base text colors — one consistent rule set, no fighting with native
   widget backgrounds because the whole app (incl. native widgets) is
   locked to this same dark theme via .streamlit/config.toml.
   --------------------------------------------------------------------- */
h1, h2, h3, h4 {{ color: {TEXT_MAIN} !important; font-weight: 700 !important; }}
p, li, span, label {{ color: {TEXT_MAIN}; }}
[data-testid="stCaptionContainer"] * {{ color: {TEXT_MUTED} !important; }}
code {{ color: {PRIMARY_SOFT} !important; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0D1526 0%, #0A1120 100%);
    border-right: 1px solid {SURFACE_BORDER};
}}
section[data-testid="stSidebar"] * {{ color: {TEXT_MAIN} !important; }}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {{ color: {TEXT_MUTED} !important; }}
section[data-testid="stSidebar"] hr {{ border-color: {SURFACE_BORDER}; }}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {{
    border-radius: 10px; margin: 1px 6px;
}}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {{
    background: rgba(56,189,248,0.10);
}}
section[data-testid="stSidebar"] [aria-current="page"] {{
    background: rgba(56,189,248,0.16) !important;
    border-radius: 10px;
    box-shadow: inset 2px 0 0 {PRIMARY};
}}

/* ---------------------------------------------------------------------
   Hero banner
   --------------------------------------------------------------------- */
.dp-hero {{
    position: relative;
    background:
        radial-gradient(circle at 85% -10%, rgba(45,212,191,0.16) 0%, transparent 55%),
        linear-gradient(120deg, {PRIMARY_DEEP} 0%, #0B4A6F 45%, #0A2E4A 100%);
    padding: 2.3rem 2.5rem;
    border-radius: 20px;
    color: white;
    margin-bottom: 1.7rem;
    box-shadow: 0 20px 45px -15px rgba(56,189,248,0.35), inset 0 1px 0 rgba(255,255,255,0.06);
    border: 1px solid rgba(125,211,252,0.25);
    overflow: hidden;
}}
.dp-hero h1 {{
    color: white !important; margin-bottom: 0.35rem; font-size: 2.1rem;
    background: linear-gradient(90deg, #FFFFFF 0%, {PRIMARY_SOFT} 100%);
    -webkit-background-clip: text; background-clip: text;
}}
.dp-hero p {{ color: #DBEAFE !important; font-size: 1.02rem; margin: 0; max-width: 62ch; }}

/* ---------------------------------------------------------------------
   Cards / surfaces
   --------------------------------------------------------------------- */
.dp-card {{
    background: {SURFACE};
    border-radius: 16px;
    padding: 1.15rem 1.35rem;
    box-shadow: 0 8px 24px -12px rgba(0,0,0,0.5);
    border: 1px solid {SURFACE_BORDER};
    margin-bottom: 0.9rem;
}}

.dp-metric-card {{
    background: linear-gradient(160deg, {SURFACE} 0%, {BG_ELEVATED} 100%);
    border-radius: 16px;
    padding: 1.05rem 1.25rem;
    border: 1px solid {SURFACE_BORDER};
    box-shadow: 0 8px 20px -12px rgba(0,0,0,0.55);
    text-align: left;
    transition: transform 0.18s ease, border-color 0.18s ease;
}}
.dp-metric-card:hover {{ transform: translateY(-2px); border-color: rgba(56,189,248,0.4); }}
.dp-metric-label {{ color: {TEXT_MUTED}; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem; }}
.dp-metric-value {{ color: {TEXT_MAIN}; font-size: 1.7rem; font-weight: 800; }}
.dp-metric-sub {{ color: {TEXT_MUTED}; font-size: 0.78rem; margin-top: 0.2rem; }}

div[data-testid="stMetric"] {{
    background: linear-gradient(160deg, {SURFACE} 0%, {BG_ELEVATED} 100%);
    border-radius: 14px; padding: 0.9rem 1.1rem;
    border: 1px solid {SURFACE_BORDER};
    box-shadow: 0 8px 20px -12px rgba(0,0,0,0.55);
}}

/* Native containers used with st.container(border=True) */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: {SURFACE_BORDER} !important;
    background: {SURFACE};
    border-radius: 16px !important;
}}

/* Dataframes / tables */
[data-testid="stDataFrame"], [data-testid="stTable"] {{
    border-radius: 12px; overflow: hidden;
    border: 1px solid {SURFACE_BORDER};
}}

/* ---------------------------------------------------------------------
   Badges
   --------------------------------------------------------------------- */
.dp-badge {{
    display: inline-block; padding: 0.18rem 0.7rem; border-radius: 999px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.02em;
    border: 1px solid transparent;
}}
.dp-badge-critical {{ background: rgba(248,113,113,0.14); color: {DANGER}; border-color: rgba(248,113,113,0.3); }}
.dp-badge-high {{ background: rgba(251,191,36,0.14); color: {WARNING}; border-color: rgba(251,191,36,0.3); }}
.dp-badge-medium {{ background: rgba(250,204,21,0.12); color: #FDE047; border-color: rgba(250,204,21,0.28); }}
.dp-badge-low {{ background: rgba(52,211,153,0.14); color: {SUCCESS}; border-color: rgba(52,211,153,0.3); }}
.dp-badge-info {{ background: rgba(56,189,248,0.14); color: {PRIMARY_SOFT}; border-color: rgba(56,189,248,0.3); }}

.dp-chip {{
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: {BG_ELEVATED}; border: 1px solid {SURFACE_BORDER};
    color: {TEXT_MAIN}; padding: 0.28rem 0.75rem; border-radius: 999px;
    font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
}}

.dp-section-title {{
    font-size: 1.18rem; font-weight: 700; color: {TEXT_MAIN};
    margin: 1.2rem 0 0.7rem 0; padding-bottom: 0.45rem;
    border-bottom: 2px solid rgba(56,189,248,0.18);
}}

.dp-empty-state {{
    text-align: center; padding: 3.2rem 1.5rem; color: {TEXT_MUTED};
    background: {SURFACE}; border-radius: 18px; border: 1px dashed {SURFACE_BORDER};
    position: relative; z-index: 1;
}}

.dp-footer-note {{ color: {TEXT_FAINT}; font-size: 0.78rem; margin-top: 2rem; text-align: center; }}

/* ---------------------------------------------------------------------
   Buttons — legible at rest, animated on hover (not plain black)
   --------------------------------------------------------------------- */
.stButton>button, .stDownloadButton>button, .stLinkButton>a {{
    border-radius: 10px !important;
    font-weight: 600 !important;
    background: {BG_ELEVATED} !important;
    color: {TEXT_MAIN} !important;
    border: 1px solid {SURFACE_BORDER} !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, background 0.15s ease !important;
}}
.stButton>button:hover, .stDownloadButton>button:hover, .stLinkButton>a:hover {{
    transform: translateY(-1px);
    border-color: {PRIMARY} !important;
    box-shadow: 0 6px 18px -6px rgba(56,189,248,0.45);
    background: rgba(56,189,248,0.10) !important;
}}
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"] {{
    background: linear-gradient(120deg, {PRIMARY} 0%, {ACCENT} 100%) !important;
    color: #04121F !important;
    border: none !important;
    box-shadow: 0 8px 22px -8px rgba(56,189,248,0.55);
}}
.stButton>button[kind="primary"]:hover {{
    filter: brightness(1.08);
    box-shadow: 0 10px 26px -6px rgba(56,189,248,0.7);
}}

/* Inputs, selects, text areas, chat input — consistent dark surface */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
div[data-baseweb="select"] > div, .stChatInput textarea {{
    background: {BG_ELEVATED} !important;
    color: {TEXT_MAIN} !important;
    border-radius: 10px !important;
    border: 1px solid {SURFACE_BORDER} !important;
}}

/* Radio / segmented "Decision" controls */
div[role="radiogroup"] label {{ color: {TEXT_MAIN} !important; }}

/* ---------------------------------------------------------------------
   Professional icon chips
   --------------------------------------------------------------------- */
.dp-icon-row {{ display: flex; align-items: flex-start; gap: 0.8rem; margin-bottom: 0.9rem; }}
.dp-icon-chip {{
    flex: 0 0 auto; width: 2.15rem; height: 2.15rem; border-radius: 11px;
    display: flex; align-items: center; justify-content: center; font-size: 1.05rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.35);
}}
.dp-icon-text {{ padding-top: 0.18rem; color: {TEXT_MAIN}; font-size: 0.96rem; line-height: 1.5; }}
.dp-icon-text b {{ color: {TEXT_MAIN}; }}

/* ---------------------------------------------------------------------
   ANIMATED BACKGROUND — soft drifting aurora glows + a faint moving
   node/dot network, fixed behind all content on every page.
   --------------------------------------------------------------------- */
.dp-bg-decor {{ position: fixed; inset: 0; overflow: hidden; z-index: 0; pointer-events: none; }}

.dp-bg-decor .dp-orb {{
    position: absolute; border-radius: 50%; filter: blur(90px);
    animation-name: dpDrift; animation-timing-function: ease-in-out; animation-iteration-count: infinite;
    opacity: 0.16;
}}
.dp-bg-decor .dp-dotgrid {{
    position: absolute; inset: -10%;
    background-image: radial-gradient(rgba(148,163,184,0.28) 1px, transparent 1px);
    background-size: 26px 26px;
    opacity: 0.12;
    animation: dpPan 60s linear infinite;
}}
.dp-bg-decor svg {{ position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0.32; }}
.dp-bg-decor svg circle {{ animation-name: dpPulse; animation-timing-function: ease-in-out; animation-iteration-count: infinite; }}

@keyframes dpDrift {{
    0%   {{ transform: translate(0px, 0px) scale(1); }}
    50%  {{ transform: translate(40px, -35px) scale(1.12); }}
    100% {{ transform: translate(0px, 0px) scale(1); }}
}}
@keyframes dpPan {{
    0% {{ transform: translate(0, 0); }}
    100% {{ transform: translate(-26px, -26px); }}
}}
@keyframes dpPulse {{
    0%, 100% {{ opacity: 0.25; r: 1.6; }}
    50% {{ opacity: 0.9; r: 2.6; }}
}}
</style>
"""

_ORBS = [
    (PRIMARY, "-6%", "-8%", "34rem", "26s", "0s"),
    (ACCENT, "70%", "5%", "26rem", "22s", "2s"),
    (ACCENT_VIOLET, "20%", "65%", "30rem", "30s", "4s"),
    (PRIMARY_DEEP, "80%", "70%", "28rem", "24s", "1s"),
]

# A fixed, seeded set of node positions so the "network" looks intentional
# rather than random noise, and stays identical across page navigations.
_NODES = [
    (6, 12), (18, 30), (30, 8), (45, 22), (60, 14), (75, 28), (88, 10),
    (10, 55), (25, 68), (40, 50), (55, 72), (70, 58), (85, 66), (95, 45),
    (15, 88), (35, 92), (50, 82), (65, 90), (80, 86), (92, 92),
]
_EDGES = [
    (0, 1), (1, 3), (3, 4), (4, 6), (2, 3), (5, 6),
    (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 13),
    (14, 15), (15, 16), (16, 17), (17, 18), (18, 19),
    (1, 9), (4, 10), (9, 15), (12, 18),
]


def _network_svg() -> str:
    lines = "".join(
        f'<line x1="{_NODES[a][0]}%" y1="{_NODES[a][1]}%" x2="{_NODES[b][0]}%" y2="{_NODES[b][1]}%" '
        f'stroke="{PRIMARY}" stroke-width="0.6" stroke-opacity="0.18" />'
        for a, b in _EDGES
    )
    dots = "".join(
        f'<circle cx="{x}%" cy="{y}%" r="1.8" fill="{PRIMARY_SOFT}" '
        f'style="animation-duration:{4 + (i % 5)}s; animation-delay:{(i % 6) * 0.4}s;" />'
        for i, (x, y) in enumerate(_NODES)
    )
    return f'<svg preserveAspectRatio="none">{lines}{dots}</svg>'


def _background_decor_html() -> str:
    orbs = "".join(
        f'<div class="dp-orb" style="background:{color}; left:{left}; top:{top}; '
        f'width:{size}; height:{size}; animation-duration:{dur}; animation-delay:{delay};"></div>'
        for color, left, top, size, dur, delay in _ORBS
    )
    return f'<div class="dp-bg-decor">{orbs}<div class="dp-dotgrid"></div>{_network_svg()}</div>'


def apply_theme(page_title: str, icon: str = "📊"):
    st.set_page_config(page_title=f"DataPilot AI — {page_title}", page_icon=icon, layout="wide",
                        initial_sidebar_state="expanded")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(_background_decor_html(), unsafe_allow_html=True)


def hero(title: str, subtitle: str):
    st.markdown(f'<div class="dp-hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def section_title(text: str):
    st.markdown(f'<div class="dp-section-title">{text}</div>', unsafe_allow_html=True)


def empty_state(message: str, icon: str = "📂"):
    st.markdown(f'<div class="dp-empty-state"><div style="font-size:2.4rem;">{icon}</div>'
                f'<p style="margin-top:0.6rem;">{message}</p></div>', unsafe_allow_html=True)


def badge(text: str, kind: str = "info") -> str:
    return f'<span class="dp-badge dp-badge-{kind}">{text}</span>'


def chip(text: str, icon: str = "") -> str:
    prefix = f"{icon} " if icon else ""
    return f'<span class="dp-chip">{prefix}{text}</span>'


def severity_badge_kind(severity: str) -> str:
    return {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}.get(severity.lower(), "info")


def icon_feature_list(items: list[tuple[str, str]]) -> None:
    """Render a list of (emoji, html_text) rows as professional icon chips
    instead of bare inline emojis. Cycles through a tasteful tint palette."""
    rows = []
    for i, (emoji, text) in enumerate(items):
        bg, fg = _CHIP_COLORS[i % len(_CHIP_COLORS)]
        rows.append(
            f'<div class="dp-icon-row">'
            f'<div class="dp-icon-chip" style="background:{bg}; color:{fg};">{emoji}</div>'
            f'<div class="dp-icon-text">{text}</div>'
            f'</div>'
        )
    st.markdown("".join(rows), unsafe_allow_html=True)
