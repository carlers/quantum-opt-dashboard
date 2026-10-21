"""Issue #108: stable configurable page import and repeat routed entrypoint.

No source-math changes, solver invocation, Streamlit Cloud preview or real
simultaneous-browser security attestation are performed in this test.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[3]
ENTRY = ROOT / "prototypes/unified_dashboard/app.py"
ROUTE = ROOT / "prototypes/unified_dashboard/pages/custom.py"
EDITOR = ROOT / "prototypes/streamlit_configurable/app.py"


def test_custom_route_has_no_process_wide_import_search_side_effects():
    source = ROUTE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(ROUTE))
    assert not any(
        isinstance(n, ast.Import) and any(a.name in {"sys", "runpy"}
                                           for a in n.names)
        for n in ast.walk(tree)
    )
    assert not any(
        isinstance(n, ast.Attribute)
        and isinstance(n.value, ast.Name)
        and ((n.value.id == "sys" and n.attr == "path")
             or (n.value.id == "runpy" and n.attr == "run_path"))
        for n in ast.walk(tree)
    )
    assert any(
        isinstance(n, ast.ImportFrom)
        and n.module == "prototypes.streamlit_configurable.app"
        and any(a.name == "main" for a in n.names)
        for n in ast.walk(tree)
    )


def test_custom_water_custom_rerender_preserves_editor_origin_and_no_autosolve():
    app = AppTest.from_file(str(ENTRY), default_timeout=120).run()
    assert not app.exception, app.exception
    assert "mvp_result" not in app.session_state
    for route, title in (
        ("pages/custom.py", "Configurable Optimization Workbench"),
        ("pages/water.py", "Water-quality sensor placement"),
        ("pages/custom.py", "Configurable Optimization Workbench"),
    ):
        app.switch_page(route).run()
        assert not app.exception, app.exception
        assert any(title in x.value for x in app.title)
        assert "mvp_result" not in app.session_state
        assert not app.session_state.get("completed_run")
    module = sys.modules.get("prototypes.streamlit_configurable.app")
    assert module is not None
    assert Path(module.__file__).resolve() == EDITOR.resolve()
    assert callable(module.main)
