"""Settings: read-only view of environment configuration and resource limits."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config.settings import settings
from streamlit_app.components.metrics import metric_row
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state, reset_state
from streamlit_app.components.theme import apply_theme, hero, section_title

apply_theme("Settings", "⚙️")
state = get_state()
render_sidebar(state)

hero("Settings", "Current configuration. Change values via your `.env` file — nothing here is hardcoded.")

section_title("AI / LLM Provider")
metric_row([
    ("Provider", settings.llm_provider, ""),
    ("Model", settings.model_name, ""),
    ("AI Enabled", "Yes ✅" if settings.ai_enabled() else "No ❌", "Set LLM_API_KEY to enable"),
    ("Environment", settings.environment, ""),
])

st.markdown("---")
section_title("Resource Limits")
metric_row([
    ("Max File Size", f"{settings.max_file_size_mb} MB", ""),
    ("Max Preview Rows", f"{settings.max_rows_for_preview:,}", ""),
    ("Max Query Time", f"{settings.max_query_time_seconds}s", ""),
    ("Max Result Rows", f"{settings.max_result_rows:,}", ""),
])
metric_row([
    ("Max Memory Usage", f"{settings.max_memory_usage_mb} MB", ""),
    ("Max Concurrent Jobs", str(settings.max_concurrent_jobs), ""),
    ("Near-constant threshold", f"{settings.near_constant_threshold:.0%}", ""),
    ("High-cardinality ratio", f"{settings.high_cardinality_ratio:.0%}", ""),
])

st.markdown("---")
section_title("Storage Paths")
st.code(
    f"Originals:  {settings.originals_dir}\n"
    f"Versions:   {settings.versions_dir}\n"
    f"Processed:  {settings.processed_dir}\n"
    f"Exports:    {settings.exports_dir}\n"
    f"DuckDB:     {settings.duckdb_path}"
)

st.markdown("---")
section_title("Session")
st.caption("Reset clears the loaded dataset, cleaning plan, and chat history for this browser session only.")
if st.button("🗑️ Reset Session", type="secondary"):
    reset_state()
    st.success("Session reset. Go to Upload Data to start again.")
    st.rerun()
