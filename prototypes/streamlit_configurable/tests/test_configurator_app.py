"""Headless Streamlit AppTest for experimental editor + genuine SCIP solving.

The supported Streamlit test tree exposes widget labels, sessions and proto
messages; code blocks/download buttons are checked through generated ZIP
and session evidence, not unsupported .code/.message convenience APIs.
"""
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def _app():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert any("Configurable Optimization Workbench" in title.value
               for title in app.title)
    return app


def _button(app, text):
    matches = [item for item in app.button if item.label == text]
    assert len(matches) == 1, (text, [x.label for x in app.button])
    return matches[0]


def _selector(app, text):
    matches = [item for item in app.selectbox if item.label == text]
    assert len(matches) == 1
    return matches[0]


def _text_area(app, text):
    matches = [item for item in app.text_area if item.label == text]
    assert len(matches) == 1
    return matches[0]


def test_preview_is_solver_free_then_real_scip_run_exports_actual_lp():
    at = _app()
    assert not [x for x in at.button if x.label.startswith("Run this validated")]
    _button(at, "Validate and preview formulation").click().run()
    assert not at.exception
    assert at.session_state["preview_fingerprint"]
    _button(at, "Run this validated synthetic model with SCIP").click().run()
    assert not at.exception
    assert any("Your optimization result" in x.value
               for x in at.subheader)
    with ZipFile(BytesIO(at.session_state["completed_run"]["archive"])) as zipf:
        names = set(zipf.namelist())
        assert {"input-bundle.json", "input-source.json", "run.json",
                "manifest.json", "actual-scip-unserved.lp",
                "actual-scip-travel.lp"} <= names
        assert b"capacity_0" in zipf.read("actual-scip-unserved.lp")


def test_switching_formulation_invalidates_old_result():
    at = _app()
    _button(at, "Validate and preview formulation").click().run()
    _button(at, "Run this validated synthetic model with SCIP").click().run()
    assert not at.exception
    original = at.session_state["completed_run"]["fingerprint"]
    _selector(at, "Mathematical formulation").set_value("maximal_coverage").run()
    assert not at.exception
    assert any("Changed inputs require a new formulation preview" in str(x.proto)
               for x in at.info)
    assert not [x for x in at.subheader if "SCIP result" in x.value]

    _button(at, "Validate and preview formulation").click().run()
    assert at.session_state["preview_fingerprint"] != original
    _button(at, "Run this validated synthetic model with SCIP").click().run()
    assert not at.exception
    assert at.session_state["completed_run"]["report"]["result"][
        "potentially_reachable_persons_NOT_served"] == 7.0


def test_generic_binary_parameters_and_editable_coefficients():
    at = _app()
    _selector(at, "Example problem").set_value("Generic binary quadratic").run()
    assert not at.exception
    _button(at, "Validate and preview formulation").click().run()
    _button(at, "Run this validated synthetic model with SCIP").click().run()
    assert not at.exception
    original = at.session_state["completed_run"]
    assert original["report"]["scip"]["selected_variables"] == ["alpha"]
    original_fp = original["fingerprint"]

    _text_area(at, "Formulation parameters JSON — editable").set_value(
        json.dumps({"rhs_overrides": {"budget": 0}})).run()
    assert not at.exception
    assert any("Changed inputs require a new formulation preview" in str(x.proto)
               for x in at.info)
    _button(at, "Validate and preview formulation").click().run()
    assert at.session_state["preview_fingerprint"] != original_fp
    _button(at, "Run this validated synthetic model with SCIP").click().run()
    assert not at.exception
    assert at.session_state["completed_run"]["report"]["scip"]["objective"] == 0.


def test_bad_json_fails_without_calling_solver_and_hides_results():
    at = _app()
    _text_area(at, "Dataset JSON — editable").set_value(
        '{"classification": "ACTUAL EMERGENCY RECORDS"}').run()
    assert not at.exception
    assert any("Data / model preflight failed" in str(x.proto) for x in at.error)
    assert not [x for x in at.button if x.label.startswith("Run this validated")]
