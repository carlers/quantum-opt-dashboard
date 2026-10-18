"""Scientific contract: displayed typed math = exact compiled SCIP model = independently checked answer."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from hashlib import sha256

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "framework" / "python"))
sys.path.insert(0, str(ROOT / "problems" / "evacuation_centers"))

from qopt.core.math_ir import (
    validate_ir, render_original, objective_value, original_feasibility,
    independent_reference, exact_unconstrained_qubo, run_typed_ir,
)
from qopt.core.experiment_bundle import load_bundle, canonical
from bundle_runner import execute

EXAMPLES = ROOT / "problems/evacuation_centers" / "examples"


def scenario(name):
    b = load_bundle(EXAMPLES / ("synthetic-typed-" + name + ".bundle.json"))
    return b.data, b.parameters


def test_mixed_integer_continuous_original_lp_independent_enumeration_and_renderer(tmp_path):
    data, parameters = scenario("mixed")
    ir = validate_ir(data, parameters)
    expression = render_original(ir)
    assert "maximize E =" in expression
    assert "open ∈ binary [0, 1]" in expression
    assert "staff ∈ integer [0, 2]" in expression
    assert "people ∈ continuous [0, 5]" in expression
    assert "limit_served" in expression
    independent = independent_reference(ir)
    assert independent["status"] == "optimal"
    assert independent["enumerated_discrete_states"] == 6
    assert independent["continuous_assignment_solver"] == "SciPy HiGHS independent LP"
    assert independent["objective"] == pytest.approx(17, abs=1e-6)
    assert independent["assignment"]["open"] == 1
    assert independent["assignment"]["staff"] == 1
    assert independent["assignment"]["people"] == pytest.approx(4)

    result = run_typed_ir(data, parameters, tmp_path)
    assert result["equation_from_same_compiled_ir"] == render_original(result["typed_ir"])
    assert result["scip"]["status"] == "optimal"
    assert result["scip"]["objective"] == pytest.approx(17, abs=1e-6)
    assert original_feasibility(ir, result["scip"]["assignment"])
    assert objective_value(ir, result["scip"]["assignment"]) == pytest.approx(17)
    assert result["independent_reference"]["objective"] == pytest.approx(17)
    assert result["exact_unconstrained_qubo"] is None
    assert result["solver_compatibility"]["direct_QUBO"].startswith("REFUSED")
    lp = (tmp_path / "actual-typed-scip-milp.lp").read_text()
    for term in ("x_open", "x_staff", "x_people", "limit_served", "staff_requires_open"):
        assert term in lp
    assert not (tmp_path / "exact-unconstrained-qubo.json").exists()


def test_changed_constraint_rhs_changes_optimum_without_changing_source(tmp_path):
    data, parameters = scenario("mixed")
    altered = run_typed_ir(data, {"rhs_overrides": {"limit_served": 2}},
                           tmp_path)
    assert altered["scip"]["objective"] == pytest.approx(8)
    assert altered["scip"]["assignment"]["people"] == pytest.approx(2)
    assert "limit_served: +1*people <= 2" in altered["equation_from_same_compiled_ir"]
    assert altered["independent_reference"]["objective"] == pytest.approx(8)


def test_unconstrained_maximization_flips_exact_qubo_with_offset_and_full_truth_table(tmp_path):
    data, parameters = scenario("binary-qubo")
    model = validate_ir(data, parameters)
    qubo = exact_unconstrained_qubo(model)
    assert qubo["source_sense"] == "maximize"
    assert qubo["minimization_negated_from_maximization"]
    assert qubo["offset"] == -2
    assert qubo["diagonal"] == {"a": -3.0, "b": -2.0}
    assert qubo["pairs"] == [{"first": "a", "second": "b", "coefficient": 4.0}]
    output = run_typed_ir(data, parameters, tmp_path)
    assert output["scip"]["objective"] == pytest.approx(5)
    assert output["scip"]["assignment"]["a"] == pytest.approx(1)
    assert output["scip"]["assignment"]["b"] == pytest.approx(0)
    assert output["independent_reference"]["objective"] == pytest.approx(5)
    exported = json.loads((tmp_path / "exact-unconstrained-qubo.json").read_text())
    assert exported == qubo
    assert "prod_a_b" in (tmp_path / "actual-typed-scip-milp.lp").read_text()


def test_constrained_binary_qubo_refused_not_silently_penalized(tmp_path):
    data, parameters = scenario("binary-qubo")
    data["constraints"] = [{"id":"no_a", "sense":"<=", "rhs":0, "linear":{"a":1}}]
    result = run_typed_ir(data, parameters, tmp_path)
    assert result["scip"]["objective"] == pytest.approx(4)
    assert result["exact_unconstrained_qubo"] is None
    assert result["solver_compatibility"]["direct_QUBO"].startswith("REFUSED")
    assert not (tmp_path / "exact-unconstrained-qubo.json").exists()


def test_infeasible_typed_mixed_model_reported_in_both_solvers(tmp_path):
    data, parameters = scenario("mixed")
    data["constraints"].append({
        "id":"impossible_people", "sense":">=", "rhs":8, "linear":{"people":1}
    })
    output = run_typed_ir(data, parameters, tmp_path)
    assert output["scip"]["status"] == "infeasible"
    assert output["independent_reference"]["status"] == "infeasible"
    assert "impossible_people" in (tmp_path / "actual-typed-scip-milp.lp").read_text()


def test_bundle_runner_exports_formulation_lp_qubo_source_hash_and_solution(tmp_path):
    run = execute(EXAMPLES / "synthetic-typed-binary-qubo.bundle.json", tmp_path)
    assert run["result"]["scip"]["status"] == "optimal"
    assert run["result"]["typed_ir"]["schema_version"] == 1
    assert run["bundle_audit"]["problem_id"] == "structured.synthetic"
    assert run["bundle_audit"]["formulation_id"] == "typed_milp"
    m = json.loads((tmp_path / "manifest.json").read_text())
    for name in ("actual-typed-scip-milp.lp", "exact-unconstrained-qubo.json", "run.json"):
        assert m["files_sha256"][name] == sha256((tmp_path / name).read_bytes()).hexdigest()


@pytest.mark.parametrize("alter,fragment", [
    (lambda d: d["variables"][0].update(domain="arbitrary_python"), "Unsupported variable domain"),
    (lambda d: d["variables"][0].update(lower=-1), "Binary variables"),
    (lambda d: d["variables"][1].update(upper=8), "at most five"),
    (lambda d: d["variables"][2].update(lower=float("nan")), "bounded finite"),
    (lambda d: d["variables"].append(dict(d["variables"][0])), "Duplicate variable"),
    (lambda d: d["objective"]["quadratic"].append(
        {"first":"open","second":"people","coefficient":9}), "only for distinct binary"),
    (lambda d: d["objective"]["linear"].update(evil=1), "Unknown variable"),
    (lambda d: d["objective"].update(sense="eval(payload)"), "minimize or maximize"),
    (lambda d: d["constraints"].append(dict(d["constraints"][0])), "Duplicate linear constraint"),
    (lambda d: d["constraints"][0].update(sense="!="), "Unsupported constraint"),
    (lambda d: d["constraints"][0]["linear"].update(unknown=1), "Unknown variable"),
])
def test_unsupported_untrusted_or_mathematically_invalid_inputs_fail_closed(alter, fragment):
    data, params = scenario("mixed")
    alter(data)
    with pytest.raises(ValueError, match=fragment):
        validate_ir(data, params)


def test_integer_bounds_and_continuous_mixing_are_explicit_and_bounded():
    data, params = scenario("mixed")
    data["variables"][1]["upper"] = 100
    with pytest.raises(ValueError, match="at most five"):
        validate_ir(data, params)
    data["variables"][1]["upper"] = 2
    data["variables"][1]["domain"] = "continuous"
    model = validate_ir(data, params)
    assert model["reference_discrete_states"] == 2
    assert model["variables"][1]["domain"] == "continuous"


def test_named_parameter_validation_and_continuous_qubo_boundary():
    data, params = scenario("mixed")
    with pytest.raises(ValueError, match="unknown constraint"):
        validate_ir(data, {"rhs_overrides": {"does_not_exist":3}})
    with pytest.raises(ValueError, match="invalid"):
        validate_ir(data, {"arbitrary_custom_code": "x"})
    assert exact_unconstrained_qubo(validate_ir(data, {})) is None
