"""Home page: product overview + quick-start + live dataset snapshot."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from streamlit_app.components.metrics import metric_row
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.theme import apply_theme, empty_state, hero, icon_feature_list, section_title

apply_theme("Home", "🧭")
state = get_state()
render_sidebar(state)

hero(
    "DataPilot AI",
    "Upload Your Data. Understand It. Clean It. Analyze It. "
    "A production-grade, AI-assisted data analytics platform — not a CSV viewer.",
)

if not state.has_dataset():
    col1, col2 = st.columns([2, 1])
    with col1:
        section_title("What DataPilot AI does")
        icon_feature_list([
            ("📥", "<b>Ingests</b> CSV, TSV, Excel (multi-sheet), JSON/NDJSON, and Parquet/Feather files"),
            ("🔍", "<b>Profiles</b> every column: types, nulls, statistics, semantic meaning, confidence-scored"),
            ("✅", "<b>Scores data quality</b> transparently across Completeness, Validity, Consistency, and Uniqueness"),
            ("🧹", "<b>Cleans intelligently</b> across 3 levels — safe automatic, AI-assisted, and advanced contextual — with full before/after preview and audit trail"),
            ("🗄️", "<b>Runs real SQL</b> via DuckDB, safely sandboxed against destructive statements"),
            ("📈", "<b>Discovers and calculates real KPIs</b> — never fabricated, only what your data can actually support"),
            ("📊", "<b>Auto-builds a dashboard</b> with meaningful, context-aware charts"),
            ("🤖", "<b>Answers questions about your data</b> in plain language, backed by actually-executed SQL"),
            ("💾", "<b>Exports</b> your cleaned data and full analysis reports"),
        ])
    with col2:
        section_title("Get started")
        icon_feature_list([
            ("1️⃣", "Go to <b>Upload Data</b>"),
            ("2️⃣", "Review <b>Data Overview</b> and <b>Data Quality</b>"),
            ("3️⃣", "Approve steps in <b>Cleaning Studio</b>"),
            ("4️⃣", "Explore <b>KPI Explorer</b> and <b>Dashboard</b>"),
            ("5️⃣", "Ask the <b>AI Analyst</b> anything"),
        ])
        st.page_link("pages/02_Upload_Data.py", label="➡️ Upload a dataset now", icon="📤")

    st.markdown("---")
    empty_state("No dataset loaded yet — upload a file to see your live analytics workspace here.", "📂")
else:
    ds = state.working_dataset
    section_title(f"Active dataset: {ds.metadata.original_filename}")
    cards = [
        ("Rows", f"{ds.metadata.row_count:,}", "Total records"),
        ("Columns", f"{ds.metadata.column_count}", "Detected fields"),
        ("Version", ds.version, ds.version_label),
        ("Quality Score", f"{state.quality_report.overall_score}/100" if state.quality_report else "—",
         "Visit Data Quality page"),
    ]
    metric_row(cards)

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.page_link("pages/03_Data_Overview.py", label="Data Overview", icon="📋")
    with c2:
        st.page_link("pages/05_Cleaning_Studio.py", label="Cleaning Studio", icon="🧹")
    with c3:
        st.page_link("pages/09_Dashboard.py", label="Dashboard", icon="📊")
    with c4:
        st.page_link("pages/10_AI_Analyst.py", label="AI Analyst", icon="🤖")

st.markdown('<div class="dp-footer-note">Every number on this screen comes from real computation '
            '(pandas / numpy / scipy / DuckDB). The AI layer only reasons and explains — it never '
            'invents a result.</div>', unsafe_allow_html=True)
