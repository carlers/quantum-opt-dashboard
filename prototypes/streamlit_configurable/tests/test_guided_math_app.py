"""Actual Streamlit AppTest interactions for guided controls without manual JSON."""
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def start(preset):
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    assert not at.exception
    change(at, "selectbox", "Example problem", preset)
    return at


def change(at, kind, label, value):
    fields = [x for x in getattr(at, kind) if x.label == label]
    assert len(fields) == 1, (label, [x.label for x in getattr(at, kind)])
    fields[0].set_value(value).run()
    assert not at.exception


def press(at, label):
    buttons = [x for x in at.button if x.label == label]
    assert len(buttons) == 1, (label, [x.label for x in at.button])
    buttons[0].click().run()
    assert not at.exception


def test_guided_coefficient_changes_same_scip_objective_and_source_zip():
    preset = "Structured math — binary, integer and continuous"
    at = start(preset)
    press(at, "Validate and preview formulation")
    press(at, "Run this validated synthetic model with SCIP")
    old = at.session_state["completed_run"]
    assert old["report"]["scip"]["objective"] == 17.
    change(at, "selectbox", "Objective variable", "people")
    change(at, "number_input", "Linear objective coefficient", 8.)
    press(at, "Set linear coefficient")
    assert not [x for x in at.subheader if "SCIP result" in x.value]
    raw = json.loads(at.session_state["typed-objective-" + preset])
    assert raw["linear"]["people"] == 8.
    press(at, "Validate and preview formulation")
    assert at.session_state["preview_fingerprint"] != old["fingerprint"]
    press(at, "Run this validated synthetic model with SCIP")
    result = at.session_state["completed_run"]
    assert result["report"]["scip"]["objective"] == 29.
    assert result["report"]["independent_reference"]["objective"] == 29.
    assert "+8*people" in result["report"]["equation_from_same_compiled_ir"]
    with ZipFile(BytesIO(result["archive"])) as z:
        assert json.loads(z.read("input-source.json"))["objective"]["linear"]["people"] == 8.
        assert b"x_people" in z.read("actual-typed-scip-milp.lp")


def test_guided_rhs_change_reaches_original_model_and_scip():
    preset = "Structured math — binary, integer and continuous"
    at = start(preset)
    change(at, "selectbox", "Select constraint row", "limit_served")
    change(at, "number_input", "Constraint right-hand side", 2.)
    press(at, "Apply constraint relation and RHS")
    assert json.loads(at.session_state["typed-constraints-" + preset])[-1]["rhs"] == 2.
    press(at, "Validate and preview formulation")
    press(at, "Run this validated synthetic model with SCIP")
    result = at.session_state["completed_run"]["report"]
    assert result["scip"]["objective"] == 8.
    assert result["independent_reference"]["objective"] == 8.
    assert "limit_served: +1*people <= 2" in result["equation_from_same_compiled_ir"]


def test_guided_add_remove_constraint_gates_qubo():
    preset = "Structured math — unconstrained binary QUBO"
    at = start(preset)
    press(at, "Validate and preview formulation")
    press(at, "Run this validated synthetic model with SCIP")
    assert at.session_state["completed_run"]["report"]["exact_unconstrained_qubo"] is not None
    change(at, "text_input", "New constraint ID", "restrict")
    press(at, "Add constraint")
    assert not [x for x in at.subheader if "SCIP result" in x.value]
    assert json.loads(at.session_state["typed-constraints-" + preset])[0]["id"] == "restrict"
    change(at, "selectbox", "Constraint variable", "b")
    change(at, "number_input", "Constraint variable coefficient", 1.)
    press(at, "Set constraint coefficient")
    press(at, "Validate and preview formulation")
    press(at, "Run this validated synthetic model with SCIP")
    result = at.session_state["completed_run"]["report"]
    assert result["exact_unconstrained_qubo"] is None
    assert result["solver_compatibility"]["direct_QUBO"].startswith("REFUSED")
    with ZipFile(BytesIO(at.session_state["completed_run"]["archive"])) as z:
        assert "exact-unconstrained-qubo.json" not in z.namelist()
    press(at, "Remove selected constraint")
    press(at, "Validate and preview formulation")
    press(at, "Run this validated synthetic model with SCIP")
    assert at.session_state["completed_run"]["report"]["exact_unconstrained_qubo"] is not None


def test_guided_invalid_domain_keeps_original_source_unchanged():
    preset = "Structured math — unconstrained binary QUBO"
    at = start(preset)
    before = json.loads(at.session_state["typed-vars-" + preset])
    change(at, "selectbox", "Variable domain", "continuous")
    press(at, "Apply variable domain and bounds")
    assert json.loads(at.session_state["typed-vars-" + preset]) == before
    assert any("Change rejected; original math unchanged" in str(x.proto) for x in at.error)
    press(at, "Validate and preview formulation")
    press(at, "Run this validated synthetic model with SCIP")
    assert at.session_state["completed_run"]["report"]["scip"]["objective"] == 5.


def test_guided_add_remove_unreferenced_variable():
    preset = "Structured math — unconstrained binary QUBO"
    at = start(preset)
    change(at, "text_input", "New variable ID", "c")
    press(at, "Add variable")
    assert [v["name"] for v in json.loads(at.session_state["typed-vars-" + preset])] == ["a", "b", "c"]
    change(at, "selectbox", "Select variable to edit", "c")
    press(at, "Remove selected variable")
    assert [v["name"] for v in json.loads(at.session_state["typed-vars-" + preset])] == ["a", "b"]
