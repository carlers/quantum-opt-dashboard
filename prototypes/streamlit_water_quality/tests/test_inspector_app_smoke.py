"""Headless real Streamlit app smoke checks; no browser or user action needed."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def _button(app: AppTest, text: str):
    matching = [item for item in app.button if item.label == text]
    assert len(matching) == 1, (text, [item.label for item in app.button])
    return matching[0]


def test_dashboard_inspects_math_without_running_solver_then_audits_real_scip():
    # AppTest simulates clicks inside a fresh session without HTTP or Streamlit Cloud.
    app = AppTest.from_file(str(APP), default_timeout=120)
    app.run()
    assert not app.exception
    assert not app.metric  # No optimizer run on initial page load.

    _button(app, "Inspect mathematical formulation").click().run()
    assert not app.exception
    assert app.session_state["show_formulation"] is True
    assert not app.metric  # The inspector does NOT run SCIP.
    # Dataset-derived N20 QUBO and original/SCIP tabs were rendered.

    _button(app, "Run SCIP experiment").click().run()
    assert not app.exception
    assert len(app.metric) >= 3
    assert app.metric[2].value == "optimal"

    # The last SCIP result is stale if K changes; the UI must not display
    # it against newly built equations.
    k_input = [item for item in app.number_input
               if item.label == "New sensors (K)"]
    assert len(k_input) == 1
    k_input[0].set_value(6).run()
    assert not app.exception
    assert not app.metric
    assert any("previous result is hidden" in item.message
               for item in app.warning)
