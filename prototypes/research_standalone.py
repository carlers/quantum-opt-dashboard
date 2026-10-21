"""Standalone Streamlit entrypoint for the bounded classical QUBO research page.

Use a distinct filename outside unified_dashboard/pages/ to avoid Streamlit's
automatic legacy multipage URL-path collision for 'research'. The same
qualified renderer serves the unified sidebar; never copy scientific models.
"""
import streamlit as st

st.set_page_config(page_title="QOpt QUBO and Classical Annealing", layout="wide")

from prototypes.water_import_guard import require_water_import_origins

require_water_import_origins()

from prototypes.unified_dashboard.research import render_research_page

require_water_import_origins()
render_research_page()
