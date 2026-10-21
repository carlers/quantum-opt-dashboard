"""Issue #108: assert installed qopt.core imports never need process-global path edits.

These tests run a separate Python -I subprocess outside the repository, and
check first-party module file/callable origins. They do NOT defend against
attacker access to the *qualified* qopt namespace or cross-session hot-reloads.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def test_cold_installed_qopt_core_resists_unqualified_module_poison(tmp_path):
    fake = tmp_path / "untrusted"
    fake.mkdir()
    for name in ("experiment_bundle", "binary_quadratic", "math_ir"):
        (fake / (name + ".py")).write_text(
            "raise RuntimeError('foreign bare module imported')\n", encoding="utf-8"
        )
    script = """
import importlib
from pathlib import Path
import sys
from types import ModuleType
root, foreign = map(Path, sys.argv[1:3])
framework_path = (root / 'framework/python').resolve()
assert framework_path not in [Path(x).resolve() for x in sys.path if x]
sys.path.insert(0, str(foreign))
for name in ('experiment_bundle', 'binary_quadratic', 'math_ir'):
    poison = ModuleType(name)
    poison.__file__ = str(foreign / (name + '.py'))
    sys.modules[name] = poison
experiment = importlib.import_module('qopt.core.experiment_bundle')
binary = importlib.import_module('qopt.core.binary_quadratic')
math_ir = importlib.import_module('qopt.core.math_ir')
runner = importlib.import_module('problems.evacuation_centers.bundle_runner')
assert Path(experiment.__file__).resolve() == (
    root / 'framework/python/qopt/core/experiment_bundle.py').resolve()
assert Path(binary.__file__).resolve() == (
    root / 'framework/python/qopt/core/binary_quadratic.py').resolve()
assert Path(math_ir.__file__).resolve() == (
    root / 'framework/python/qopt/core/math_ir.py').resolve()
assert runner.canonical is experiment.canonical
assert runner.load_bundle is experiment.load_bundle
assert runner.run_binary_quadratic is binary.run_binary_quadratic
assert framework_path not in [Path(x).resolve() for x in sys.path if x]
for name in ('experiment_bundle', 'binary_quadratic', 'math_ir'):
    assert Path(sys.modules[name].__file__).parent == foreign
"""
    proc = subprocess.run(
        [sys.executable, "-I", "-c", script, str(ROOT), str(fake)],
        cwd=tmp_path, capture_output=True, text=True, timeout=35,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_framework_core_installed_in_clean_foreign_working_directory(tmp_path):
    """Do not allow pytest's or Streamlit's repo CWD to conceal a missing install."""
    snippet = """
from importlib import import_module, metadata
from pathlib import Path
import sys
root = Path(sys.argv[1])
assert metadata.version('quantum-opt-dashboard-ui-imports') == '0.1.0'
for name, expected in (
    ('qopt', 'framework/python/qopt/__init__.py'),
    ('qopt.core.experiment_bundle', 'framework/python/qopt/core/experiment_bundle.py'),
    ('qopt.core.binary_quadratic', 'framework/python/qopt/core/binary_quadratic.py'),
    ('qopt.core.math_ir', 'framework/python/qopt/core/math_ir.py'),
):
    module = import_module(name)
    assert Path(module.__file__).resolve() == (root / expected).resolve()
assert (root / 'framework/python').resolve() not in [
    Path(x).resolve() for x in sys.path if x
]
"""
    proc = subprocess.run(
        [sys.executable, "-I", "-c", snippet, str(ROOT)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_framework_runtime_modules_no_longer_mutate_global_sys_path():
    app = (ROOT / "prototypes/streamlit_configurable/app.py").read_text(
        encoding="utf-8"
    )
    runner = (ROOT / "problems/evacuation_centers/bundle_runner.py").read_text(
        encoding="utf-8"
    )
    for module in (app, runner):
        assert "sys.path" not in module
        assert "import sys" not in module
        assert "from qopt.core.experiment_bundle import" in module
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'qopt = "framework/python/qopt"' in pyproject
