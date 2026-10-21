"""Issue #108: original water modules are installed at startup, not path-patched.

Tests require the actual root requirements editable distributions. No original
scientific source bytes are edited and no hostile concurrent race is certified.
"""
from __future__ import annotations

import ast
from importlib import metadata
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
WATER = ROOT / "prototypes/streamlit_water_quality"


def _isolated(script: str, cwd: Path, *args: str) -> None:
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(ROOT), *args],
        cwd=cwd, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_all_nine_legacy_modules_resolve_to_unchanged_installed_source(tmp_path):
    """Fail if editable install fails or import spec resolves to another package."""
    script = """
from importlib import metadata, util
from pathlib import Path
import sys
from prototypes.water_import_guard import (
    WATER_BARE_MODULE_NAMES, WATER_SOURCE_DIR, require_water_import_origins,
)
root = Path(sys.argv[1])
assert metadata.version('quantum-opt-dashboard-legacy-water-imports') == '0.1.0'
assert WATER_SOURCE_DIR == (root / 'prototypes/streamlit_water_quality').resolve()
before = sys.path[:]
for name in WATER_BARE_MODULE_NAMES:
    assert name not in sys.modules, 'Test must inspect unloaded source modules'
    spec = util.find_spec(name)
    assert spec is not None, name
    assert Path(spec.origin).resolve() == (WATER_SOURCE_DIR / (name + '.py')).resolve()
require_water_import_origins()
assert sys.path == before
assert not any(name in sys.modules for name in WATER_BARE_MODULE_NAMES)
"""
    _isolated(script, tmp_path)


def test_unloaded_foreign_water_module_is_rejected_before_import(tmp_path):
    """A higher-priority foreign path must fail closed without executing it."""
    fake = tmp_path / "foreign"
    fake.mkdir()
    script = """
from pathlib import Path
import sys
from prototypes.water_import_guard import WaterImportOriginError, require_water_import_origins
root = Path(sys.argv[1])
fake = Path(sys.argv[2])
(fa ke)
"""
    script = script.replace("(fa ke)", """(fake / 'model.py').write_text(
    "raise RuntimeError('foreign model executed')\\n", encoding='utf-8')
sys.path.insert(0, str(fake))
before = sys.path[:]
assert 'model' not in sys.modules
try:
    require_water_import_origins()
except WaterImportOriginError as exc:
    assert 'model' in str(exc)
    assert 'resolver' in str(exc)
else:
    raise AssertionError('preflight accepted foreign unloaded model')
assert 'model' not in sys.modules
assert sys.path == before
""")
    _isolated(script, tmp_path, str(fake))


def test_unified_routes_do_not_mutate_global_import_paths():
    for relative in (
        "prototypes/unified_dashboard/pages/water.py",
        "prototypes/unified_dashboard/research.py",
    ):
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"), filename=relative)
        assert not any(
            isinstance(node, ast.Call) and
            isinstance(node.func, ast.Attribute) and
            isinstance(node.func.value, ast.Attribute) and
            isinstance(node.func.value.value, ast.Name) and
            node.func.value.value.id == "sys" and
            node.func.value.attr == "path"
            for node in ast.walk(tree)
        )
        assert not any(
            isinstance(node, ast.Import) and
            any(alias.name == "sys" for alias in node.names)
            for node in ast.walk(tree)
        )


def test_root_contract_installs_original_legacy_modules():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "-e prototypes/streamlit_water_quality" in requirements
    assert metadata.version("quantum-opt-dashboard-legacy-water-imports") == "0.1.0"
    project = (WATER / "pyproject.toml").read_text(encoding="utf-8")
    for name in ("model", "mvp_audit", "qubo", "sa_benchmark",
                 "formulation_audit", "wireless_topology", "runtime_attestation",
                 "scip_lp_structure", "evidence"):
        assert f'"{name}"' in project
