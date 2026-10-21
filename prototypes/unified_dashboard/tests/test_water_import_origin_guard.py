"""Issue #108: reject poisoned unqualified water modules before sys.path mutates.

No changes to historical notebook/GeoJSON/scientific model; a defensive
pre-import check is NOT full malicious-process or two-session isolation.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def _isolated(script: str, tmp_path: Path):
    proc = subprocess.run(
        [sys.executable, "-I", "-c", script, str(ROOT)],
        cwd=tmp_path, capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_cached_same_name_modules_fail_closed_without_path_mutation(tmp_path):
    """Foreign file origin, forged file origin, and no import spec all reject."""
    script = """
from importlib.machinery import ModuleSpec
from pathlib import Path
import sys
from types import ModuleType
from prototypes.water_import_guard import (
    WATER_BARE_MODULE_NAMES, WATER_SOURCE_DIR, WaterImportOriginError,
    require_water_import_origins,
)
root = Path(sys.argv[1])
assert WATER_SOURCE_DIR == (root / 'prototypes/streamlit_water_quality').resolve()
assert len(WATER_BARE_MODULE_NAMES) >= 9
assert all((WATER_SOURCE_DIR / (name + '.py')).is_file()
           for name in WATER_BARE_MODULE_NAMES)
before = sys.path[:]
for name in WATER_BARE_MODULE_NAMES:
    for shape in ('foreign', 'missing_spec', 'forged_file'):
        fake = ModuleType(name)
        fake.__file__ = str(WATER_SOURCE_DIR / (name + '.py'))
        if shape == 'foreign':
            fake.__file__ = '/tmp/foreign/' + name + '.py'
            fake.__spec__ = ModuleSpec(name, loader=None, origin=fake.__file__)
        elif shape == 'forged_file':
            fake.__spec__ = ModuleSpec(
                name, loader=None, origin='/tmp/foreign/' + name + '.py')
        sys.modules[name] = fake
        try:
            require_water_import_origins()
        except WaterImportOriginError as exc:
            assert 'Water import preflight rejected' in str(exc)
            assert name in str(exc)
        else:
            raise AssertionError('Untrusted water module was not rejected')
        assert sys.modules[name] is fake
        assert sys.path == before
        del sys.modules[name]
# Even a negative import-cache slot is rejected rather than silently ignored.
sys.modules['model'] = None
try:
    require_water_import_origins()
except WaterImportOriginError:
    pass
else:
    raise AssertionError('Negative model cache entry not rejected')
assert sys.modules['model'] is None
del sys.modules['model']
"""
    _isolated(script, tmp_path)


def test_legitimate_canonical_model_module_is_not_rejected(tmp_path):
    """An actual import spec plus correct resolved file origin is accepted."""
    script = """
from importlib import util
from pathlib import Path
import sys
from prototypes.water_import_guard import WATER_SOURCE_DIR, require_water_import_origins
path = WATER_SOURCE_DIR / 'model.py'
spec = util.spec_from_file_location('model', path)
module = util.module_from_spec(spec)
sys.modules['model'] = module
try:
    assert spec.loader is not None
    spec.loader.exec_module(module)
    before = sys.path[:]
    require_water_import_origins()
    assert sys.path == before
    assert Path(module.__file__).resolve() == path.resolve()
finally:
    del sys.modules['model']
"""
    _isolated(script, tmp_path)


def test_water_and_research_routes_reject_poison_before_runtime_script(tmp_path):
    """Fail *before* model import, Streamlit execution or new path insertions."""
    script = """
from importlib.machinery import ModuleSpec
from pathlib import Path
import runpy
import sys
from types import ModuleType
from prototypes.water_import_guard import WaterImportOriginError
root = Path(sys.argv[1])
for name, route in (('model', 'pages/water.py'), ('qubo', 'pages/research.py')):
    fake = ModuleType(name)
    fake.__file__ = '/tmp/foreign/' + name + '.py'
    fake.__spec__ = ModuleSpec(name, loader=None, origin=fake.__file__)
    sys.modules[name] = fake
    before = sys.path[:]
    try:
        runpy.run_path(str(root / 'prototypes/unified_dashboard' / route))
    except WaterImportOriginError as exc:
        assert name in str(exc)
    else:
        raise AssertionError('Route unexpectedly used cached foreign module')
    assert sys.path == before
    assert sys.modules[name] is fake
    del sys.modules[name]
"""
    _isolated(script, tmp_path)


def test_guard_stays_out_of_pinned_scientific_source_tree():
    from prototypes.water_import_guard import WATER_BARE_MODULE_NAMES
    assert {"model", "mvp_audit", "qubo", "sa_benchmark", "formulation_audit",
            "wireless_topology", "runtime_attestation"}.issubset(
                set(WATER_BARE_MODULE_NAMES)
            )
    source = (ROOT / "prototypes/unified_dashboard/pages/water.py").read_text(
        encoding="utf-8"
    )
    research = (ROOT / "prototypes/unified_dashboard/research.py").read_text(
        encoding="utf-8"
    )
    for text in (source, research):
        assert "require_water_import_origins()" in text
    assert "sys.path.insert(" not in source
    assert "sys.path.insert(" not in research
    assert "runpy.run_path" in source  # Remains a separate open import risk
    assert "from model import" in research  # Historical bare names remain
