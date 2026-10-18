"""Run a validated standalone page inside the unified Streamlit shell.

Use ScriptRunner-thread-scoped context, not process-global os.environ:
overlapping browser sessions must never affect one another.
"""
import runpy
import sys
import threading
from pathlib import Path

target = Path(__file__).resolve().parents[2] / "streamlit_water_quality" / "app.py"
sys.path.insert(0, str(target.parent))
thread = threading.current_thread()
previous = getattr(thread, "_qopt_unified_page", False)
try:
    setattr(thread, "_qopt_unified_page", True)
    runpy.run_path(str(target), run_name="__main__")
finally:
    if previous:
        setattr(thread, "_qopt_unified_page", True)
    else:
        delattr(thread, "_qopt_unified_page")
