"""Render the original water Streamlit study from its installed qualified page.

The standalone scientific/SCIP/graph modules retain their original source
identities. Only the original presentation block is now a reusable function.
ScriptRunner thread-local context is restored even on Streamlit exceptions;
do not mutate sys.path, runpy namespace, or module aliases between sessions.
"""
import threading

from prototypes.water_import_guard import require_water_import_origins

require_water_import_origins()
thread = threading.current_thread()
previous = getattr(thread, "_qopt_unified_page", False)
try:
    setattr(thread, "_qopt_unified_page", True)
    from prototypes.streamlit_water_quality.app import render_water_page

    require_water_import_origins()
    render_water_page()
finally:
    if previous:
        setattr(thread, "_qopt_unified_page", True)
    else:
        delattr(thread, "_qopt_unified_page")
