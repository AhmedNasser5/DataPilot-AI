"""Upload Data page: handles ingestion end-to-end with format detection & sheet picking."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from core.ingestion.loader_registry import (
    FileTooLargeError, LoaderError, UnsupportedFormatError,
)
from config.settings import settings
from services.dataset_service import dataset_service
from services.workflow_service import workflow_service
from streamlit_app.components.data_tables import show_dataframe
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.theme import apply_theme, hero, section_title
from streamlit_app.components.upload_components import render_format_badge, render_sheet_picker

apply_theme("Upload Data", "📤")
state = get_state()
render_sidebar(state)

hero("Upload Data", "Drop in a file — DataPilot AI detects the format, validates it, and loads it safely.")

section_title("Supported formats")
st.caption(
    "Tabular: CSV, TSV, delimited TXT, XLSX, XLS · Semi-structured: JSON, NDJSON · "
    f"Columnar: Parquet, Feather.  Max file size: **{settings.max_file_size_mb} MB**."
)

uploaded = st.file_uploader(
    "Choose a file",
    type=["csv", "tsv", "txt", "xlsx", "xls", "json", "ndjson", "jsonl", "parquet", "feather"],
)

if uploaded is not None:
    content = uploaded.getvalue()
    detected = dataset_service.detect_format(uploaded.name, content)
    render_format_badge(detected)

    sheet_name = None
    if detected.format in ("xlsx", "xls"):
        try:
            sheets = dataset_service.list_excel_sheets(content)
            if len(sheets) > 1:
                sheet_name = render_sheet_picker(sheets)
            elif sheets:
                sheet_name = sheets[0].name
                st.caption(f"Single sheet detected: **{sheet_name}**")
        except LoaderError as e:
            st.error(str(e))

    if st.button("🚀 Load & Analyze Dataset", type="primary"):
        with st.spinner("Loading, validating, and profiling your dataset..."):
            try:
                dataset = dataset_service.load_dataset(uploaded.name, content, sheet_name=sheet_name)
                state.original_dataset = dataset
                state.working_dataset = dataset
                state.dataset_versions = [dataset]
                workflow_service.run_full_pipeline(state)
                st.success(
                    f"✅ Loaded **{dataset.metadata.original_filename}** — "
                    f"{dataset.metadata.row_count:,} rows × {dataset.metadata.column_count} columns."
                )
                st.balloons()
            except FileTooLargeError as e:
                st.error(f"📦 File too large: {e}")
            except UnsupportedFormatError as e:
                st.error(f"🚫 Unsupported format: {e}")
            except LoaderError as e:
                st.error(f"⚠️ Could not load file: {e}")
            except Exception as e:
                st.error(f"Unexpected error while loading the file: {e}")

if state.has_dataset():
    st.markdown("---")
    section_title("Preview: first rows of the loaded dataset")
    show_dataframe(state.working_dataset.dataframe, max_preview_rows=settings.max_rows_for_preview)
    st.page_link("pages/03_Data_Overview.py", label="➡️ Continue to Data Overview", icon="📋")
