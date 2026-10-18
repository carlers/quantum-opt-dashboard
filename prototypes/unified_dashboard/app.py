"""One Streamlit entry point for the integrated scientific MVP.

All existing solver/source/prototype code stays importable and independently
testable; navigation wrappers only route to existing validated experiences.
No original GeoJSON, notebook or scientific model is rewritten here.
"""
import streamlit as st

st.set_page_config(
    page_title="Quantum Optimization Research Workbench",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)
pages = [
    st.Page("pages/water.py", title="Water-quality placement", icon="🌊", default=True),
    st.Page("pages/custom.py", title="Configure another problem", icon="🧮"),
    st.Page("pages/research.py", title="QUBO and classical SA", icon="📈"),
    st.Page("pages/about.py", title="About the research", icon="📋"),
]
st.navigation(pages, position="sidebar").run()
