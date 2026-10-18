"""Navigation wrapper for scientific limitations and full repository history."""
import runpy
from pathlib import Path

target = Path(__file__).resolve().parents[1] / "about.py"
runpy.run_path(str(target), run_name="__main__")
