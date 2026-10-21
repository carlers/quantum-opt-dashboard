"""Issue #108: unified research page uses stable import identity, not runpy.

Tests normal Streamlit rendering and does NOT certify hostile cross-session
sys.path changes, concurrent SCIP quotas or historical QUBO equivalence.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[3]
ENTRY = ROOT / "prototypes/unified_dashboard/app.py"
ROUTE = ROOT / "prototypes/unified_dashboard/pages/research.py"
RESEARCH = ROOT / "prototypes/unified_dashboard/research.py"


def test_research_route_uses_qualified_reusable_rendering_without_runpy():
    tree = ast.parse(ROUTE.read_text(encoding="utf-8"), filename=str(ROUTE))
    assert not any(
        isinstance(n, ast.Import) and any(a.name in {"runpy", "sys"}
                                           for a in n.names)
        for n in ast.walk(tree)
    )
    assert not any(
        isinstance(n, ast.Attribute)
        and isinstance(n.value, ast.Name) and n.value.id in {"runpy", "sys"}
        and n.attr in {"run_path", "path"}
        for n in ast.walk(tree)
    )
    assert any(
        isinstance(n, ast.ImportFrom)
        and n.module == "prototypes.unified_dashboard.research"
        and any(a.name == "render_research_page" for a in n.names)
        for n in ast.walk(tree)
    )
    assert sum(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "require_water_import_origins"
        for n in tree.body
    ) == 2
    source = ast.parse(RESEARCH.read_text(encoding="utf-8"))
    assert any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "render_research_page"
        for n in source.body
    )
    assert any(
        isinstance(n, ast.If)
        and isinstance(n.test, ast.Compare)
        and isinstance(n.test.left, ast.Name)
        and n.test.left.id == "__name__"
        for n in source.body
    )


def test_standalone_research_entrypoint_renders_without_sampling():
    research = AppTest.from_file(str(RESEARCH), default_timeout=120).run()
    assert not research.exception, research.exception
    assert any("QUBO and classical annealing" in x.value for x in research.title)
    assert any(x.label == "Original binary variables" for x in research.metric)
    assert any("Run bounded classical simulated annealing" in x.label
               for x in research.button)
    assert not research.session_state.get("unified_sa_run")
    assert any("not a guarantee" in str(x.proto) for x in research.info)


def test_qualified_research_route_preserves_penalty_and_no_cross_page_solver():
    app = AppTest.from_file(str(ENTRY), default_timeout=120).run()
    assert not app.exception, app.exception
    assert not app.session_state.get("mvp_result")
    for route in ("pages/research.py", "pages/custom.py", "pages/research.py"):
        app.switch_page(route).run()
        assert not app.exception, app.exception
        assert not app.session_state.get("mvp_result")
        assert not app.session_state.get("unified_sa_run")
    assert any("QUBO and classical annealing" in x.value for x in app.title)
    selector = next(s for s in app.selectbox if s.label ==
                    "QUBO penalty (equal budget and connectivity penalties)")
    assert selector.value == "notebook-local-row-sum"
    module = sys.modules.get("prototypes.unified_dashboard.research")
    assert module is not None
    assert Path(module.__file__).resolve() == RESEARCH.resolve()
    assert callable(module.render_research_page)
