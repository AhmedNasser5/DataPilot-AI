"""
DataPilot AI — Streamlit entry point.

Kept intentionally thin: all Home-page content lives in
pages/01_Home.py so the sidebar navigation reads cleanly as
Home -> Upload -> Overview -> ... -> Settings. This file only
bootstraps sys.path and forwards to the Home page.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.switch_page("pages/01_Home.py")
