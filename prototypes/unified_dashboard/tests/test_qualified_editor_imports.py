"""Issue #108: verify a first migrated, installed UI import boundary.

This tests the configurable editor's qualified guided-math modules. Water,
evacuation and research bare imports remain out of scope and untrusted.
"""
from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def test_qualified_editor_resists_injected_unqualified_guided_math(tmp_path):
    """A fresh isolated interpreter must ignore poisoned bare-name cache/path."""
    fake = tmp_path / "foreign"
    fake.mkdir()
    (fake / "guided_math.py").write_text(
        "raise RuntimeError('untrusted guided_math module imported')\n",
        encoding="utf-8",
    )
    script = """
import importlib
from pathlib import Path
import sys
from types import ModuleType
root, foreign = map(Path, sys.argv[1:3])
# Explicit path required only for the existing non-installed qopt framework.
sys.path.insert(0, str(root / 'framework' / 'python'))
sys.path.insert(0, str(foreign))
malicious = ModuleType('guided_math')
malicious.apply_guided_edit = lambda *a, **k: (_ for _ in ()).throw(
    RuntimeError('untrusted guided_math cache alias executed'))
malicious.parse_components = malicious.apply_guided_edit
sys.modules['guided_math'] = malicious
qualified = importlib.import_module('prototypes.streamlit_configurable.guided_math')
ui = importlib.import_module('prototypes.streamlit_configurable.guided_math_ui')
assert Path(qualified.__file__).resolve() == (
    root / 'prototypes/streamlit_configurable/guided_math.py').resolve()
assert Path(ui.__file__).resolve() == (
    root / 'prototypes/streamlit_configurable/guided_math_ui.py').resolve()
assert ui.apply_guided_edit is qualified.apply_guided_edit
assert ui.parse_components is qualified.parse_components
assert sys.modules['guided_math'] is malicious
assert 'prototypes.streamlit_configurable.guided_math' in sys.modules
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", script, str(ROOT), str(fake)],
        cwd=tmp_path, timeout=30, text=True, capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_ui_namespace_is_installed_not_implicitly_provided_by_cwd(tmp_path):
    """An isolated non-repo working directory must find the installed package."""
    snippet = """
import importlib
from importlib.metadata import version
from pathlib import Path
root = Path(__import__('sys').argv[1])
m = importlib.import_module('prototypes.streamlit_configurable')
assert Path(m.__file__).resolve() == (
    root / 'prototypes/streamlit_configurable/__init__.py').resolve()
assert version('quantum-opt-dashboard-ui-imports') == '0.1.0'
"""
    outcome = subprocess.run(
        [sys.executable, "-I", "-c", snippet, str(ROOT)],
        cwd=tmp_path, capture_output=True, text=True, timeout=20,
    )
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr


def test_root_uses_explicit_install_contract():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "-r prototypes/unified_dashboard/requirements.txt" in requirements
    assert "-e ." in requirements
    assert version("quantum-opt-dashboard-ui-imports") == "0.1.0"
