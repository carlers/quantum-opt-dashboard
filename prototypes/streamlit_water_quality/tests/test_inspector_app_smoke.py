"""Headless smoke for the integrated original water MVP entry point.

Legacy inspector-button interactions were replaced by an immediately visible
read-only formulation preview and separate research QUBO page.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_water_source_and_math_are_visible_before_explicit_solver_action():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception
    assert any("Understand the current model" in h.value for h in app.subheader)
    assert "mvp_result" not in app.session_state
    assert any(b.label == "Find monitoring locations (SCIP)" for b in app.button)
    app.button(key="mvp_run").click().run()
    assert not app.exception
    result = app.session_state["mvp_result"]
    assert result["metrics"]["status"] == "optimal"
    assert result["independent"]["selected_local_positions"] == [0, 1, 3, 6, 7]
    k = next(x for x in app.number_input if x.label == "New sensors to place (K)")
    k.set_value(6).run()
    assert not app.exception
    assert "mvp_result" not in app.session_state
