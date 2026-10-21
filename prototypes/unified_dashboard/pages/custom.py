"""Render the installed configurable app in the unified Streamlit shell.

Only ScriptRunner-thread-scoped route context is changed. The package is
installed before runtime; do not mutate process-global sys.path, use runpy, or
copy and re-execute the Python module with a different import identity.
Standalone `streamlit run prototypes/streamlit_configurable/app.py` retains
its own __main__ entrypoint and page-config behavior.
"""
import threading

from prototypes.streamlit_configurable.app import main as render_configurable_workbench

thread = threading.current_thread()
previous = getattr(thread, "_qopt_unified_page", False)
try:
    setattr(thread, "_qopt_unified_page", True)
    render_configurable_workbench()
finally:
    if previous:
        setattr(thread, "_qopt_unified_page", True)
    else:
        delattr(thread, "_qopt_unified_page")
