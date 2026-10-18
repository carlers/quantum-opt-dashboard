"""Navigate to generic and synthetic scientific configuration tools."""
import os
import runpy
import sys
from pathlib import Path

target = Path(__file__).resolve().parents[2] / "streamlit_configurable" / "app.py"
sys.path.insert(0, str(target.parent))
previous = os.environ.get("QOPT_UNIFIED_DASHBOARD")
try:
    os.environ["QOPT_UNIFIED_DASHBOARD"] = "1"
    runpy.run_path(str(target), run_name="__main__")
finally:
    if previous is None:
        os.environ.pop("QOPT_UNIFIED_DASHBOARD", None)
    else:
        os.environ["QOPT_UNIFIED_DASHBOARD"] = previous
