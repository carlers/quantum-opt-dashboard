"""Navigate to bounded QUBO and classical OpenJij experiments."""
import runpy
from pathlib import Path

target = Path(__file__).resolve().parents[1] / "research.py"
runpy.run_path(str(target), run_name="__main__")
