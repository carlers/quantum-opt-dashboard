"""Navigate to the source-pinned classical QUBO research experiment.

Use the installed page's stable module identity. Preflight bare water module
origins before importing the research page or its transitive scientific modules;
normal Streamlit widgets are rendered explicitly on every page navigation.
"""
from prototypes.water_import_guard import require_water_import_origins

require_water_import_origins()

from prototypes.unified_dashboard.research import render_research_page

require_water_import_origins()
render_research_page()
