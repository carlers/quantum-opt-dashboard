"""Issue #108: negative import-origin and CLI tests for the synthetic runner.

This stage qualifies one leaf import from the bundle runner; the broader
water/Streamlit import DAG and two overlapping browser sessions remain open.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def test_fresh_isolated_runner_ignores_poisoned_synthetic_reference(tmp_path):
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "synthetic_reference.py").write_text(
        "raise RuntimeError('foreign synthetic math loaded')\n", encoding="utf-8"
    )
    script = """
import importlib
from pathlib import Path
import sys
from types import ModuleType
root, foreign = map(Path, sys.argv[1:3])
sys.path.insert(0, str(foreign))
poison = ModuleType('synthetic_reference')
poison.SyntheticProblem = type('Forged', (), {})
sys.modules['synthetic_reference'] = poison
runner = importlib.import_module('problems.evacuation_centers.bundle_runner')
reference = importlib.import_module('problems.evacuation_centers.synthetic_reference')
assert Path(reference.__file__).resolve() == (
    root / 'problems/evacuation_centers/synthetic_reference.py').resolve()
assert Path(runner.__file__).resolve() == (
    root / 'problems/evacuation_centers/bundle_runner.py').resolve()
assert runner.SyntheticProblem is reference.SyntheticProblem
assert runner.independent_enumeration is reference.independent_enumeration
assert sys.modules['synthetic_reference'] is poison
"""
    proc = subprocess.run(
        [sys.executable, "-I", "-c", script, str(ROOT), str(foreign)],
        cwd=tmp_path, capture_output=True, text=True, timeout=35,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_standalone_synthetic_cli_uses_installed_namespace_outside_repo(tmp_path):
    """A real artificial fixture must execute by file path from a foreign CWD."""
    output = tmp_path / "output"
    cli = ROOT / "problems/evacuation_centers/bundle_runner.py"
    fixture = ROOT / "problems/evacuation_centers/examples/evac-capacitated.json"
    proc = subprocess.run(
        [sys.executable, "-I", str(cli), "--bundle", str(fixture),
         "--output-dir", str(output)],
        cwd=tmp_path, capture_output=True, text=True, timeout=90,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert output.is_dir()
    # Do not assume specific artifact filenames or falsely claim author-science proof.
    assert any(p.is_file() for p in output.iterdir())
