"""Headless Streamlit test of structured formula edits reaching exact SCIP LP.

No arbitrary Python or LaTeX is parsed. We intentionally exercise different
variable domains, RHS changes, mathematical preview, export and QUBO refusal.
"""
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def run_app():
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    assert not at.exception
    return at


def choose(at, name):
    options = [s for s in at.selectbox if s.label == "Example problem"]
    assert len(options) == 1
    options[0].set_value(name).run()
    assert not at.exception


def edit(at, label, value):
    items = [v for v in at.text_area if v.label == label]
    assert len(items) == 1
    items[0].set_value(value).run()


def press(at, label):
    items = [b for b in at.button if b.label == label]
    assert len(items) == 1, [x.label for x in at.button]
    items[0].click().run()
    assert not at.exception


def test_mixed_domain_structured_editor_solves_and_exports_exact_lp():
    at = run_app()
    choose(at, "Structured math — binary, integer and continuous")
    assert len([t for t in at.text_area if t.label.startswith("Variables —")]) == 1
    assert len([t for t in at.text_area if t.label.startswith("Objective —")]) == 1
    assert len([t for t in at.text_area if t.label.startswith("Constraints —")]) == 1
    press(at, "Validate and preview formulation")
    assert "preview_fingerprint" in at.session_state
    assert "completed_run" not in at.session_state
    press(at, "Run this validated synthetic model with SCIP")
    r = at.session_state["completed_run"]
    assert r["report"]["scip"]["status"] == "optimal"
    assert r["report"]["scip"]["objective"] == 17
    assert r["report"]["independent_reference"]["objective"] == 17
    assert r["report"]["exact_unconstrained_qubo"] is None
    assert "REFUSED" in r["report"]["solver_compatibility"]["direct_QUBO"]
    with ZipFile(BytesIO(r["archive"])) as archive:
        names = set(archive.namelist())
        assert {"run.json", "input-source.json", "input-bundle.json",
                "actual-typed-scip-milp.lp", "manifest.json"} <= names
        assert "exact-unconstrained-qubo.json" not in names
        assert b"x_people" in archive.read("actual-typed-scip-milp.lp")
        src = json.loads(archive.read("input-source.json"))
        assert any(v["domain"] == "continuous" for v in src["variables"])
        assert "people ∈ continuous" in r["report"]["equation_from_same_compiled_ir"]


def test_changing_constraint_rhs_invalidates_preview_and_changes_compiled_problem():
    at = run_app()
    choose(at, "Structured math — binary, integer and continuous")
    press(at, "Validate and preview formulation")
    press(at, "Run this validated synthetic model with SCIP")
    original = at.session_state["completed_run"]["fingerprint"]
    edit(at, "Formulation parameters JSON — editable",
         json.dumps({"rhs_overrides": {"limit_served": 2}}))
    assert not at.exception
    assert not [v for v in at.subheader if "SCIP result" in v.value]
    press(at, "Validate and preview formulation")
    assert at.session_state["preview_fingerprint"] != original
    press(at, "Run this validated synthetic model with SCIP")
    result = at.session_state["completed_run"]
    assert result["report"]["scip"]["objective"] == 8
    assert result["report"]["independent_reference"]["objective"] == 8
    assert "limit_served: +1*people <= 2" in result["report"]["equation_from_same_compiled_ir"]


def test_user_edit_quadratic_coefficients_and_constraints_controls_qubo_eligibility():
    at = run_app()
    choose(at, "Structured math — unconstrained binary QUBO")
    press(at, "Validate and preview formulation")
    press(at, "Run this validated synthetic model with SCIP")
    r = at.session_state["completed_run"]
    assert r["report"]["scip"]["objective"] == 5
    assert r["report"]["exact_unconstrained_qubo"]["offset"] == -2
    with ZipFile(BytesIO(r["archive"])) as archive:
        assert "exact-unconstrained-qubo.json" in archive.namelist()
        q = json.loads(archive.read("exact-unconstrained-qubo.json"))
        assert q["minimization_negated_from_maximization"]
    old = r["fingerprint"]

    edit(at, "Constraints — JSON linear rows with named RHS",
         json.dumps([{"id":"force_b","sense":"==","rhs":1,
                      "linear":{"b":1}}]))
    assert not at.exception
    press(at, "Validate and preview formulation")
    assert at.session_state["preview_fingerprint"] != old
    press(at, "Run this validated synthetic model with SCIP")
    r2 = at.session_state["completed_run"]
    assert r2["report"]["exact_unconstrained_qubo"] is None
    assert r2["report"]["scip"]["objective"] == 4
    with ZipFile(BytesIO(r2["archive"])) as archive:
        assert "exact-unconstrained-qubo.json" not in archive.namelist()


def test_unsupported_integer_continuous_quadratic_product_prevents_run():
    at = run_app()
    choose(at, "Structured math — binary, integer and continuous")
    obj = next(v for v in at.text_area if v.label.startswith("Objective —"))
    o = json.loads(obj.value)
    o["quadratic"].append({"first":"open", "second":"people", "coefficient":2})
    edit(at, "Objective — JSON sense, constant, linear and binary-pair terms", json.dumps(o))
    assert not at.exception
    assert any("Data / model preflight failed" in str(m.proto) for m in at.error)
    assert not any("Run this validated synthetic model" in b.label for b in at.button)
