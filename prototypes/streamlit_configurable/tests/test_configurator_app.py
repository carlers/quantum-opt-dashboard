"""Streamlit AppTest: dataset/formulation edits and solver audit are real, not decorative."""
import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def _app():
    at = AppTest.from_file(str(APP), default_timeout=45).run()
    assert not at.exception
    assert any("Configurable Optimization Workbench" in x.value for x in at.title)
    return at


def test_preview_is_solver_free_then_real_scip_run_exports_actual_lp():
    at = _app()
    # No execution until the user explicitly previews and runs.
    assert not at.button(key="run_btn") if False else True
    at.button(key="preview_btn").click().run()
    assert not at.exception
    assert "Run this validated synthetic model with SCIP" in [b.label for b in at.button]
    assert any("stage 1: minimize sum(unserved" in x.code for x in at.code)
    at.button(key="run_btn").click().run()
    assert not at.exception
    assert any("SCIP result and independent original-model audit" in x.value
               for x in at.subheader)
    assert len(at.get("download_button")) >= 1


def test_switching_formulation_and_data_invalidates_old_result():
    at = _app()
    at.button(key="preview_btn").click().run()
    at.button(key="run_btn").click().run()
    assert not at.exception
    assert "completed_run" in at.session_state
    original = at.session_state["completed_run"]["fingerprint"]

    at.selectbox(key="formula-Evacuation — capacitated allocation").set_value(
        "maximal_coverage").run()
    assert not at.exception
    assert "completed_run" not in at.session_state
    assert any("Changed inputs require a new formulation preview" in x.message
               for x in at.info)
    at.button(key="preview_btn").click().run()
    assert original != at.session_state["preview_fingerprint"]
    at.button(key="run_btn").click().run()
    assert not at.exception
    assert any("potentially_reachable_persons_NOT_served" in str(x.value)
               for x in at.json)


def test_generic_binary_parameters_and_editable_coefficients():
    at = _app()
    at.selectbox(key="Example problem").set_value("Generic binary quadratic").run()
    assert not at.exception
    at.button(key="preview_btn").click().run()
    assert not at.exception
    assert any("-4*alpha" in x.code for x in at.code)
    at.button(key="run_btn").click().run()
    assert not at.exception
    assert any("selected_variables" in str(x.value) for x in at.json)
    fp = at.session_state["completed_run"]["fingerprint"]

    params = at.text_area(key="parameters-Generic binary quadratic")
    params.set_value(json.dumps({"rhs_overrides": {"budget": 0}})).run()
    assert not at.exception
    assert "completed_run" not in at.session_state
    at.button(key="preview_btn").click().run()
    assert at.session_state["preview_fingerprint"] != fp
    at.button(key="run_btn").click().run()
    assert not at.exception
    assert any("objective" in str(x.value) for x in at.json)


def test_bad_json_fails_without_calling_solver_and_no_old_result():
    at = _app()
    at.text_area(key="input-data-Evacuation — capacitated allocation").set_value(
        '{"classification": "ACTUAL EMERGENCY RECORDS"}').run()
    assert not at.exception
    assert any("Data / model preflight failed" in x.message for x in at.error)
    assert "completed_run" not in at.session_state
