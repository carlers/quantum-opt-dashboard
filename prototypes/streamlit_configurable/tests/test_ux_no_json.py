"""Zero-JSON first-run acceptance for the default synthetic evacuation model."""
import json
from pathlib import Path

import pytest

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def start():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not at.exception
    return at


def button(at, label):
    found = [b for b in at.button if b.label == label]
    assert len(found) == 1
    found[0].click().run()
    assert not at.exception


def test_first_time_default_synthetic_scenario_has_visible_guided_control_and_summary():
    at = start()
    assert next(s for s in at.selectbox if s.label == "Example problem").value == (
        "Evacuation — capacitated allocation"
    )
    assert any(x.label == "Maximum evacuation centers to open" for x in at.number_input)
    button(at, "Validate and preview formulation")
    button(at, "Run this validated synthetic model with SCIP")
    report = at.session_state["completed_run"]["report"]
    assert report["result"]["capacitated_scip"]["unserved_persons"] == pytest.approx(2.0, abs=1e-6)
    assert any(m.label == "People not served" for m in at.metric)
    assert any("Your optimization result" in s.value for s in at.subheader)


def test_no_json_edited_open_budget_is_in_validated_solver_config_and_result():
    at = start()
    button(at, "Validate and preview formulation")
    button(at, "Run this validated synthetic model with SCIP")
    original = at.session_state["completed_run"]["fingerprint"]

    budget = next(x for x in at.number_input
                  if x.label == "Maximum evacuation centers to open")
    budget.set_value(2).run()
    assert not at.exception
    assert json.loads(at.session_state[
        "parameters-Evacuation — capacitated allocation"
    ])["max_open"] == 2
    assert "completed_run" not in at.session_state
    button(at, "Validate and preview formulation")
    button(at, "Run this validated synthetic model with SCIP")
    r = at.session_state["completed_run"]
    assert r["fingerprint"] != original
    assert r["report"]["result"]["capacitated_scip"]["unserved_persons"] == pytest.approx(0.0, abs=1e-6)
    assert any(m.label == "People served (fictional)" and m.value == "7" for m in at.metric)


def test_no_json_edited_synthetic_demand_changes_real_input_fingerprint():
    at = start()
    before = at.session_state["input-data-Evacuation — capacitated allocation"]
    demand = next(x for x in at.number_input
                  if x.label == "People needing shelter in selected zone (fictional)")
    demand.set_value(5).run()
    assert not at.exception
    updated = json.loads(at.session_state[
        "input-data-Evacuation — capacitated allocation"
    ])
    assert updated["demands"] == [5, 3]
    assert before != json.dumps(updated, indent=2)
    button(at, "Validate and preview formulation")
    button(at, "Run this validated synthetic model with SCIP")
    result = at.session_state["completed_run"]["report"]["result"]["capacitated_scip"]
    assert result["unserved_persons"] == pytest.approx(3.0, abs=1e-6)


def test_structured_editor_is_visible_without_touching_json():
    at = start()
    chooser = next(x for x in at.selectbox if x.label == "Example problem")
    chooser.set_value("Structured math — binary, integer and continuous").run()
    assert not at.exception
    assert any(x.label == "Objective variable" for x in at.selectbox)
    assert any(x.label == "Linear objective coefficient" for x in at.number_input)
