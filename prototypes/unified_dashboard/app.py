"""One Streamlit entry point for the integrated scientific MVP.

All existing solver/source/prototype code stays importable and independently
testable; navigation wrappers only route to existing validated experiences.
No original GeoJSON, notebook or scientific model is rewritten here.
"""
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(
    page_title="Quantum Optimization Research Workbench",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)
pages = [
    st.Page(str(ROOT / "pages" / "water.py"), title="Water-quality placement", icon="🌊", default=True),
    st.Page(str(ROOT / "pages" / "custom.py"), title="Configure another problem", icon="🧮"),
    st.Page(str(ROOT / "pages" / "research.py"), title="QUBO and classical SA", icon="📈"),
    st.Page(str(ROOT / "pages" / "about.py"), title="About the research", icon="📋"),
]
st.navigation(pages, position="sidebar").run()
