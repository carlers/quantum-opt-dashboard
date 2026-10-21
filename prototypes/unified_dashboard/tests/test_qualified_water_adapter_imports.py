"""Issue #108: independently exercise the qualified lazy water adapter import.

Only same-name *unqualified* module poisoning is tested here.  It does not
certify hostile qualified-package injection or simultaneous browser sessions.
Original notebook model math/data and scientific compiler are not modified.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "problems/evacuation_centers/bundle_runner.py"
SYNTHETIC = ROOT / "problems/water_quality/examples/fake-water-n5.bundle.json"


def test_isolated_lazy_water_adapter_ignores_bare_name_cache_and_path(tmp_path):
    foreign = tmp_path / "untrusted"
    foreign.mkdir()
    names = ("water_bundle_adapter", "notebook_reference_model", "bundle_runner")
    for name in names:
        (foreign / (name + ".py")).write_text(
            "raise RuntimeError('untrusted bare module was executed')\n",
            encoding="utf-8",
        )
    script = """
import importlib
import pathlib
import sys
from types import ModuleType
root, foreign, fixture, destination = map(pathlib.Path, sys.argv[1:5])
sys.path.insert(0, str(foreign))
for name in ('water_bundle_adapter', 'notebook_reference_model', 'bundle_runner'):
    fake = ModuleType(name)
    fake.__file__ = str(foreign / (name + '.py'))
    sys.modules[name] = fake
water_dir = str(root / 'problems/water_quality')
assert water_dir not in sys.path
runner = importlib.import_module('problems.evacuation_centers.bundle_runner')
# Synthetic-only paths must keep the optional water adapter lazy.
assert 'problems.water_quality.water_bundle_adapter' not in sys.modules
report = runner.execute(fixture, destination)
water = importlib.import_module('problems.water_quality.water_bundle_adapter')
reference = importlib.import_module('problems.water_quality.notebook_reference_model')
assert pathlib.Path(water.__file__).resolve() == (
    root / 'problems/water_quality/water_bundle_adapter.py').resolve()
assert pathlib.Path(reference.__file__).resolve() == (
    root / 'problems/water_quality/notebook_reference_model.py').resolve()
assert runner.execute.__module__ == 'problems.evacuation_centers.bundle_runner'
assert water.make_instance is reference.make_instance
assert water.solve_scip is reference.solve_scip
assert report['kind'] == 'SYNTHETIC-VALIDATED-CONFIGURATION'
assert report['result']['historical_source_scenario'] is False
assert report['result']['dataset_point_count'] == 81
assert water_dir not in sys.path
for name in ('water_bundle_adapter', 'notebook_reference_model', 'bundle_runner'):
    assert pathlib.Path(sys.modules[name].__file__).parent == foreign
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script,
         str(ROOT), str(foreign), str(SYNTHETIC), str(tmp_path / "output")],
        cwd=tmp_path, capture_output=True, text=True, timeout=110,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_standalone_water_bundle_cli_from_foreign_cwd(tmp_path):
    """Actual synthetic projected GeoJSON executes via installed source modules."""
    output = tmp_path / "bundle"
    result = subprocess.run(
        [sys.executable, "-I", str(CLI), "--bundle", str(SYNTHETIC),
         "--output-dir", str(output)],
        cwd=tmp_path, capture_output=True, text=True, timeout=110,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads((output / "run.json").read_text(encoding="utf-8"))
    audit = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert record["kind"] == "SYNTHETIC-VALIDATED-CONFIGURATION"
    assert record["result"]["historical_source_scenario"] is False
    assert record["result"]["dataset_point_count"] == 81
    assert isinstance(audit["files_sha256"], dict)
    assert "run.json" in audit["files_sha256"]


def test_configurable_page_and_runner_use_only_qualified_local_water_modules():
    page = (ROOT / "prototypes/streamlit_configurable/app.py").read_text(
        encoding="utf-8"
    )
    runner = CLI.read_text(encoding="utf-8")
    adapter = (ROOT / "problems/water_quality/water_bundle_adapter.py").read_text(
        encoding="utf-8"
    )
    assert "from problems.water_quality.notebook_reference_model import" in page
    assert "from problems.water_quality.water_bundle_adapter import" in page
    assert "from problems.evacuation_centers.bundle_runner import" in page
    assert 'sys.path.insert(0, str(ROOT / "problems" / "water_quality"))' not in page
    assert 'sys.path.insert(0, str(ROOT / "problems" / "evacuation_centers"))' not in page
    assert 'sys.path.insert(0, str(REPO / "problems" / "water_quality"))' not in runner
    assert "from problems.water_quality.water_bundle_adapter import run_water_bundle" in runner
    assert "from problems.water_quality.notebook_reference_model import" in adapter
