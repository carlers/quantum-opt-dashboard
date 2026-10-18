"""First-time UX acceptance: change real scientific settings without editing JSON.

These tests assert the ordinary widgets change the exact model fingerprint
and SCIP calculation; they are not screenshots or substitutes for real users.
"""
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_every_real_environmental_factor_and_weight_is_visible_without_json():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not at.exception
    assert any(x.label == "Redundancy strength (β)" for x in at.number_input)
    options = next(x for x in at.radio if x.label == "Criterion weights")
    assert "Custom weights · exploratory" in options.options
    assert "mvp_result" not in at.session_state


def test_custom_factor_weight_changes_compiled_model_and_evidence():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    at.radio[0].set_value("Custom weights · exploratory").run()
    assert not at.exception
    river = next(x for x in at.number_input if x.label == "River proximity weight")
    river.set_value(0.0).run()
    assert not at.exception
    at.button(key="mvp_run").click().run()
    assert not at.exception
    result = at.session_state["mvp_result"]
    with ZipFile(BytesIO(result["zip"])) as z:
        model = json.loads(z.read("model.json"))
    assert model["settings"]["eight_factor_weights"][0] == 0
    assert model["settings"]["weights_source"] == "Custom weights · exploratory"
    assert model["settings"]["beta"] == 1.0
    assert result["independent"]["original_feasible"]


def test_beta_delta_edits_fingerprint_invalidate_current_scip_results():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    at.button(key="mvp_run").click().run()
    assert not at.exception
    previous = at.session_state["mvp_result"]["fingerprint"]
    beta = next(x for x in at.number_input if x.label == "Redundancy strength (β)")
    beta.set_value(0.0).run()
    assert not at.exception
    assert "mvp_result" not in at.session_state
    assert any("Inputs changed" in str(x.proto) for x in at.info)
    at.button(key="mvp_run").click().run()
    assert not at.exception
    result = at.session_state["mvp_result"]
    assert result["fingerprint"] != previous
    with ZipFile(BytesIO(result["zip"])) as z:
        model = json.loads(z.read("model.json"))
    assert model["settings"]["beta"] == 0.0
    assert model["settings"]["delta"] == 1.0
