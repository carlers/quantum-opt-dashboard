"""A genuinely domain-neutral *small binary quadratic* mathematical adapter.

JSON dataset defines arbitrary binary variable labels, original objective
coefficients, and linear constraints. SCIP solves an exact binary-product MILP;
independent exhaustive enumeration certifies tiny models. Unconstrained
binary quadratic objectives can be exported as exact QUBOs (not sampled).

No Python/LaTeX expression parsing, nonlinear arbitrary code, geographic or
operational claims. This is an intentionally bounded research prototype.
"""
from __future__ import annotations

import re
from itertools import product
from math import isfinite
from pathlib import Path

from pyscipopt import Model, quicksum

_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,31}$")


def _keys(obj: object, allowed: set[str], required: set[str], label: str) -> dict:
    if type(obj) is not dict:
        raise ValueError(f"{label} must be a dictionary")
    if set(obj) - allowed or required - set(obj):
        raise ValueError(f"{label}: unexpected/missing fields")
    return obj


def _scalar(x: object, name: str) -> float:
    if type(x) not in (int, float) or not isfinite(x) or abs(float(x)) > 1e10:
        raise ValueError(f"{name} must be bounded finite numeric")
    return float(x)


def validate_binary_problem(data: dict, parameters: dict) -> dict:
    d = _keys(data, {"classification", "variables", "objective", "constraints"},
              {"classification", "variables", "objective", "constraints"}, "binary dataset")
    if d["classification"] != "SYNTHETIC_BINARY_QUADRATIC":
        raise ValueError("Only entirely synthetic binary problems are supported")
    labels = d["variables"]
    if type(labels) is not list or not 1 <= len(labels) <= 16 or any(
        type(x) is not str or not _ID.fullmatch(x) for x in labels
    ) or len(set(labels)) != len(labels):
        raise ValueError("Expected 1..16 unique safe binary variable identifiers")
    var_ids = set(labels)
    obj = _keys(d["objective"], {"sense", "constant", "linear", "quadratic"},
                {"sense", "linear", "quadratic"}, "objective")
    if obj["sense"] not in ("minimize", "maximize"):
        raise ValueError("Objective must minimize or maximize")
    _scalar(obj.get("constant", 0), "objective constant")
    lin = _keys(obj["linear"], var_ids, set(), "linear objective")
    for k, v in lin.items():
        _scalar(v, f"linear coefficient {k}")
    quads = obj["quadratic"]
    if type(quads) is not list or len(quads) > 120:
        raise ValueError("Invalid quadratic terms list")
    pairs = set()
    for term in quads:
        q = _keys(term, {"first", "second", "coefficient"},
                  {"first", "second", "coefficient"}, "quadratic term")
        first, second = q["first"], q["second"]
        if first not in var_ids or second not in var_ids or first == second:
            raise ValueError("Quadratic terms require two distinct known variables")
        pair = tuple(sorted((first, second)))
        if pair in pairs:
            raise ValueError("Duplicate quadratic term")
        pairs.add(pair)
        _scalar(q["coefficient"], "quadratic coefficient")

    rows = d["constraints"]
    if type(rows) is not list or len(rows) > 100:
        raise ValueError("Invalid constraint list")
    names = set()
    for row in rows:
        r = _keys(row, {"id", "sense", "rhs", "linear"},
                  {"id", "sense", "rhs", "linear"}, "linear constraint")
        if type(r["id"]) is not str or not _ID.fullmatch(r["id"]) or r["id"] in names:
            raise ValueError("Invalid/duplicate constraint identifier")
        names.add(r["id"])
        if r["sense"] not in ("<=", "==", ">="):
            raise ValueError("Unsupported constraint relation")
        _scalar(r["rhs"], "constraint rhs")
        _keys(r["linear"], var_ids, set(), "constraint coefficients")
        for v in r["linear"].values():
            _scalar(v, "constraint coefficient")

    _keys(parameters, {"rhs_overrides"}, set(), "binary parameter overrides")
    overrides = parameters.get("rhs_overrides", {})
    _keys(overrides, names, set(), "constraint RHS overrides")
    resolved = []
    for row in rows:
        changed = dict(row)
        changed["rhs"] = _scalar(overrides.get(row["id"], row["rhs"]), "override rhs")
        resolved.append(changed)
    return {
        "variables": list(labels),
        "objective": obj,
        "constraints": resolved,
        "formulation": "binary quadratic objective and linear constraints",
    }


def original_energy(problem: dict, bits: dict[str, int]) -> float:
    obj = problem["objective"]
    return float(obj.get("constant", 0)) + sum(
        float(a) * bits[k] for k, a in obj["linear"].items()
    ) + sum(
        float(t["coefficient"]) * bits[t["first"]] * bits[t["second"]]
        for t in obj["quadratic"]
    )


def independent_audit(problem: dict, bits: dict[str, int]) -> bool:
    if set(bits) != set(problem["variables"]) or any(
        type(v) is not int or v not in (0, 1) for v in bits.values()
    ):
        return False
    for row in problem["constraints"]:
        lhs = sum(float(c) * bits[var] for var, c in row["linear"].items())
        rhs = float(row["rhs"])
        sense = row["sense"]
        if (sense == "<=" and lhs > rhs + 1e-7 or
            sense == ">=" and lhs < rhs - 1e-7 or
            sense == "==" and abs(lhs - rhs) > 1e-7):
            return False
    return True


def brute_force_reference(problem: dict) -> dict:
    labels = problem["variables"]
    direction = problem["objective"]["sense"]
    winners: list[dict] = []
    optimal: float | None = None
    feasible_count = 0
    for state in product((0, 1), repeat=len(labels)):
        bits = dict(zip(labels, state))
        if not independent_audit(problem, bits):
            continue
        feasible_count += 1
        score = original_energy(problem, bits)
        if optimal is None or (direction == "minimize" and score < optimal - 1e-8) or (
            direction == "maximize" and score > optimal + 1e-8
        ):
            optimal, winners = score, [bits]
        elif abs(score - optimal) <= 1e-8:
            winners.append(bits)
    return {
        "status": "optimal" if optimal is not None else "infeasible",
        "objective": optimal,
        "all_optimal_assignments": winners,
        "num_assignments_checked": 2 ** len(labels),
        "feasible_assignments": feasible_count,
    }


def compile_and_solve_scip(problem: dict, lp_path: Path) -> dict:
    model = Model("SYNTHETIC-custom-binary-quadratic")
    model.hideOutput()
    model.setRealParam("limits/time", 30.)
    variables = {name: model.addVar(vtype="B", name=f"x_{name}")
                 for name in problem["variables"]}
    aux = {}
    for term in problem["objective"]["quadratic"]:
        a, b = term["first"], term["second"]
        pair = model.addVar(vtype="B", name=f"pair_{a}_{b}")
        model.addCons(pair >= variables[a] + variables[b] - 1,
                      name=f"pair_lb_{a}_{b}")
        model.addCons(pair <= variables[a], name=f"pair_ub_a_{a}_{b}")
        model.addCons(pair <= variables[b], name=f"pair_ub_b_{a}_{b}")
        aux[(a,b)] = pair
    for row in problem["constraints"]:
        expr = quicksum(float(c) * variables[k] for k,c in row["linear"].items())
        rhs = float(row["rhs"])
        if row["sense"] == "<=":
            model.addCons(expr <= rhs, name=row["id"])
        elif row["sense"] == ">=":
            model.addCons(expr >= rhs, name=row["id"])
        else:
            model.addCons(expr == rhs, name=row["id"])
    obj = quicksum(float(c) * variables[k] for k,c in
                   problem["objective"]["linear"].items()) + quicksum(
        float(t["coefficient"]) * aux[t["first"], t["second"]]
        for t in problem["objective"]["quadratic"]
    ) + float(problem["objective"].get("constant", 0.))
    model.setObjective(obj, problem["objective"]["sense"])
    model.writeProblem(str(lp_path), trans=False)
    model.optimize()
    status = str(model.getStatus())
    if status != "optimal":
        return {"status": status, "solver": "SCIP MILP exact linearization"}
    solution = {key: round(model.getVal(v)) for key,v in variables.items()}
    if not independent_audit(problem, solution):
        raise AssertionError("SCIP solution fails original binary problem")
    energy = original_energy(problem, solution)
    if abs(energy - float(model.getObjVal())) > 1e-6:
        raise AssertionError("Original objective differs from compiled SCIP MILP")
    return {"status": "optimal", "solver": "SCIP MILP exact linearization",
            "objective": energy, "selected_variables": [k for k,v in solution.items() if v],
            "assignment": solution}


def run_binary_quadratic(data: dict, parameters: dict, output_dir: Path) -> dict:
    original = validate_binary_problem(data, parameters)
    reference = brute_force_reference(original)
    lp = output_dir / "actual-scip-binary-milp.lp"
    compiled = compile_and_solve_scip(original, lp)
    if reference["status"] != compiled["status"]:
        raise AssertionError("SCIP/exhaustive feasibility disagreement")
    if reference["status"] == "optimal" and abs(
        reference["objective"] - compiled["objective"]
    ) > 1e-6:
        raise AssertionError("SCIP/exhaustive objective disagreement")
    result = {
        "formulation_inspector": {
            "variable_domain": "binary",
            "original_objective": original["objective"],
            "original_constraints": original["constraints"],
            "solver_formulation": "SCIP MILP with binary pair products and original linear rows",
        },
        "scip": compiled, "independent_enumeration": reference,
        "scope": "SYNTHETIC small binary quadratic problem; no historical QUBO parity",
    }
    if not original["constraints"]:
        qubo = {
            "definition": "E(x)=offset + sum_i Q_ii x_i + sum_{i<j} Q_ij x_i x_j",
            "offset": float(original["objective"].get("constant", 0.)),
            "diagonal": {k: float(original["objective"]["linear"].get(k,0.))
                         for k in original["variables"]},
            "off_diagonal": [
                {"first": q["first"], "second": q["second"],
                 "coefficient": float(q["coefficient"])}
                for q in original["objective"]["quadratic"]
            ],
            "sense": original["objective"]["sense"],
            "note": "Exact unconstrained binary quadratic objective only. QUBO minimizes; maximize requires negation. No sampler executed.",
        }
        result["exact_unconstrained_qubo"] = qubo
    else:
        result["qubo_status"] = "NOT_COMPILED: linear constraints require an explicit validated encoding and penalties"
    return result
