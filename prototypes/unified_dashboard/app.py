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
# This notice belongs to the shared navigation entrypoint so it appears on
# ALL four routed research pages, not only the About page.
# It is a scientific-scope notice, NOT authentication or access restriction.
st.warning(
    "Research-only computational prototype — NOT a reproduction of the "
    "published manuscript and NOT validated for physical water monitoring, "
    "emergency decisions, or sensor deployment. The source notebook uses a "
    "different AHP weight set and D2 road-proximity factor than the "
    "manuscript's WorldPop population description. Connectivity is modeled, "
    "not measured; OpenJij simulated annealing is classical, not quantum hardware."
)

pages = [
    st.Page("pages/water.py", title="Water-quality placement", icon="🌊", default=True),
    st.Page("pages/verified_results.py", title="Verified source results", icon="📊"),
    st.Page("pages/experiments.py", title="Run experiments (local)", icon="🧪"),
    st.Page("pages/custom.py", title="Configure another problem", icon="🧮"),
    st.Page("pages/research.py", title="QUBO and classical SA", icon="📈"),
    st.Page("pages/about.py", title="About the research", icon="📋"),
]
st.navigation(pages, position="sidebar").run()
