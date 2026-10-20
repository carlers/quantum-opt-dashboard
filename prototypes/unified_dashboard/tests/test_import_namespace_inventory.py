"""Issue #108 inventory contract and deliberately adversarial import-cache probe.

This DOES NOT test two actual Streamlit browser sessions, and does not certify
that the existing unsafe unqualified imports are fixed.
"""
from __future__ import annotations

from importlib import util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
INVENTORY = ROOT / "scripts/import_namespace_inventory.py"


def _tool():
    spec = util.spec_from_file_location("qopt_issue108_import_inventory", INVENTORY)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_frozen_source_audit_reports_existing_route_hazards():
    record = _tool().inventory()
    assert record["kind"] == "READ_ONLY_IMPORT_SURFACE_AUDIT_NOT_ISOLATION_ATTESTATION"
    assert record["python_source_file_count"] >= 30
    assert record["counts"]["sys_path_mutations"] >= 5
    assert record["counts"]["unqualified_local_name_edges"] >= 10
    by_path = {entry["file"]: entry for entry in record["files_with_observed_edges_or_hazards"]}
    for wrapper in ("water.py", "custom.py"):
        page = by_path[f"prototypes/unified_dashboard/pages/{wrapper}"]
        assert any(x["method"] == "insert" for x in page["sys_path_mutations"])
        assert any(x["kind"] == "runpy.run_path" for x in page["dynamic_execution"])
    assert any(x["method"] == "insert" for x in
               by_path["prototypes/unified_dashboard/research.py"]["sys_path_mutations"])
    assert any(x["module"] == "model" for x in
               by_path["prototypes/unified_dashboard/research.py"]["unqualified_local_name_edges"])
    assert any(x["module"] == "bundle_runner" for x in
               by_path["prototypes/streamlit_configurable/app.py"]["unqualified_local_name_edges"])
    assert any(x["module"] == "water_bundle_adapter" for x in
               by_path["problems/evacuation_centers/bundle_runner.py"]["unqualified_local_name_edges"])


def test_ast_inventory_is_deterministic_and_reports_new_sources(tmp_path):
    root = tmp_path / "repo"
    for part in _tool().SCAN_ROOTS:
        (root / part).mkdir(parents=True)
    source = root / "prototypes/unified_dashboard/page.py"
    source.parent.mkdir(parents=True)
    source.write_text("import sys\nfrom model import F\nsys.path.insert(0, '/tmp')\n")
    (root / "problems/model.py").write_text("F = 1\n")
    a = _tool().inventory(root)
    b = _tool().inventory(root)
    assert a == b
    assert a["python_source_file_count"] == 2
    assert a["counts"]["unqualified_local_name_edges"] == 1
    assert a["counts"]["sys_path_mutations"] == 1


def test_preloaded_foreign_unqualified_module_wins_after_path_reordering(tmp_path):
    """Negative control: global sys.modules name alias defeats path precedence.

    This is an isolated Python probe, NOT a real multi-session Streamlit test.
    It records the unsafe behavior the migration must eliminate.
    """
    script = """
import importlib
import pathlib
import sys
import tempfile
with tempfile.TemporaryDirectory() as location:
    base = pathlib.Path(location)
    foreign, canonical = base / 'foreign', base / 'canonical'
    foreign.mkdir()
    canonical.mkdir()
    (foreign / 'model.py').write_text("ORIGIN = 'foreign'\\n")
    (canonical / 'model.py').write_text("ORIGIN = 'canonical'\\n")
    sys.path.insert(0, str(foreign))
    imported = importlib.import_module('model')
    sys.path.insert(0, str(canonical))
    reimported = importlib.import_module('model')
    assert imported is reimported
    assert reimported.ORIGIN == 'foreign'
    assert pathlib.Path(reimported.__file__).parent == foreign
"""
    done = subprocess.run([sys.executable, "-I", "-c", script],
                          capture_output=True, text=True, timeout=10, cwd=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
