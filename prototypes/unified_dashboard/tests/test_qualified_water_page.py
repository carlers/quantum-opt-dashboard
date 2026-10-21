"""Issue #108: original water Streamlit page runs through one qualified module.

No changes to the author notebook, scientific model/SCIP/graph implementation,
import-cache hostile concurrency, or production Cloud deployment are implied.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[3]
ENTRY = ROOT / "prototypes/unified_dashboard/app.py"
ROUTE = ROOT / "prototypes/unified_dashboard/pages/water.py"
STANDALONE = ROOT / "prototypes/streamlit_water_quality/app.py"


def test_water_wrapper_uses_qualified_import_and_no_dynamic_execution():
    tree = ast.parse(ROUTE.read_text(encoding="utf-8"), filename=str(ROUTE))
    assert not any(
        isinstance(n, ast.Import) and any(a.name in {"runpy", "sys"} for a in n.names)
        for n in ast.walk(tree)
    )
    assert not any(
        isinstance(n, ast.Attribute)
        and isinstance(n.value, ast.Name)
        and n.value.id in {"runpy", "sys"}
        and n.attr in {"run_path", "path"}
        for n in ast.walk(tree)
    )
    assert any(
        isinstance(n, ast.ImportFrom)
        and n.module == "prototypes.streamlit_water_quality.app"
        and any(a.name == "render_water_page" for a in n.names)
        for n in ast.walk(tree)
    )
    assert sum(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "require_water_import_origins"
        for n in ast.walk(tree)
    ) == 2
    page = ast.parse(STANDALONE.read_text(encoding="utf-8"))
    assert sum(
        isinstance(n, ast.FunctionDef) and n.name == "render_water_page"
        for n in page.body
    ) == 1
    assert any(
        isinstance(n, ast.If)
        and isinstance(n.test, ast.Compare)
        and isinstance(n.test.left, ast.Name)
        and n.test.left.id == "__name__"
        for n in page.body
    )


def test_standalone_water_page_keeps_original_unsolved_default():
    app = AppTest.from_file(str(STANDALONE), default_timeout=120).run()
    assert not app.exception, app.exception
    assert any("Water-quality sensor placement" in x.value for x in app.title)
    assert any("committed notebook-derived scenario" in str(x.proto)
               for x in app.warning)
    assert "mvp_result" not in app.session_state
    assert next(r for r in app.radio if r.label == "Wireless connectivity").value == (
        "Local clusters · original"
    )
    assert any(b.key == "mvp_run" for b in app.button)


def test_unified_water_reruns_with_stable_page_origin_and_without_autosolve():
    app = AppTest.from_file(str(ENTRY), default_timeout=120).run()
    assert not app.exception, app.exception
    for route in ("pages/custom.py", "pages/water.py", "pages/research.py",
                  "pages/water.py"):
        app.switch_page(route).run()
        assert not app.exception, app.exception
        assert "mvp_result" not in app.session_state
        assert not app.session_state.get("unified_sa_run")
    assert any("Water-quality sensor placement" in x.value for x in app.title)
    module = sys.modules.get("prototypes.streamlit_water_quality.app")
    assert module is not None
    assert Path(module.__file__).resolve() == STANDALONE.resolve()
    assert callable(module.render_water_page)
