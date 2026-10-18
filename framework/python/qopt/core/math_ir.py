"""Solver-neutral bounded mixed-domain mathematical IR, SCIP compiler and checks.

First vertical slice of #42: explicit binary, bounded integer and continuous
variables, linear constraints, quadratic objective terms ONLY between two
binary variables (exact binary product linearization). This is not unrestricted
MIQP, arbitrary expressions, real shelter decisions, or quantum computation.
"""
from __future__ import annotations

import json
import re
from itertools import product
from math import isfinite, prod
from pathlib import Path

import numpy as np
from pyscipopt import Model, quicksum
from scipy.optimize import linprog


IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,31}$")
TOL = 1e-6


def _fields(value, allowed, required, label):
    if type(value) is not dict or set(value) - set(allowed) or set(required) - set(value):
        raise ValueError(f"{label} has invalid, missing, or unexpected fields")
    return value


def _num(v, name):
    if type(v) not in (int, float) or not isfinite(v) or abs(v) > 1e8:
        raise ValueError(f"{name} must be a bounded finite numeric value")
    return float(v)


def _ident(name, label):
    if type(name) is not str or not IDENT.fullmatch(name):
        raise ValueError(f"{label} must be a safe variable/constraint identifier")
    return name


def validate_ir(data: dict, parameters: dict) -> dict:
    d = _fields(data, {"classification", "variables", "objective", "constraints"},
                {"classification", "variables", "objective", "constraints"}, "typed model")
    if d["classification"] != "SYNTHETIC_TYPED_OPTIMIZATION":
        raise ValueError("Only explicitly SYNTHETIC typed problems are permitted")
    variables = d["variables"]
    if type(variables) is not list or not 1 <= len(variables) <= 12:
        raise ValueError("Typed model permits 1..12 variables")
    normalized = []
    for entry in variables:
        v = _fields(entry, {"name", "domain", "lower", "upper"},
                    {"name", "domain", "lower", "upper"}, "variable")
        name = _ident(v["name"], "variable")
        domain = v["domain"]
        if type(domain) is not str or domain not in ("binary", "integer", "continuous"):
            raise ValueError("Unsupported variable domain; choose binary/integer/continuous")
        low, high = _num(v["lower"], name + " lower"), _num(v["upper"], name + " upper")
        if low > high:
            raise ValueError("Variable has lower bound greater than upper bound")
        if domain == "binary" and (low, high) != (0.0, 1.0):
            raise ValueError("Binary variables must have exact [0,1] bounds")
        if domain == "integer" and (
            not low.is_integer() or not high.is_integer() or high - low > 4
        ):
            raise ValueError("Integer bounds must be integral with at most five domain values")
        normalized.append({"name": name, "domain": domain, "lower": low, "upper": high})
    ids = [v["name"] for v in normalized]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate variable identifiers")
    lookup = {v["name"]: v for v in normalized}
    discrete = [v for v in normalized if v["domain"] != "continuous"]
    choices = prod(
        2 if v["domain"] == "binary" else int(v["upper"] - v["lower"] + 1)
        for v in discrete
    )
    if choices > 4096:
        raise ValueError("Independent-discrete-enumeration limit exceeded (4096 assignments)")
    if sum(v["domain"] == "continuous" for v in normalized) > 8:
        raise ValueError("At most eight continuous variables supported")
    obj = _fields(d["objective"], {"sense", "constant", "linear", "quadratic"},
                  {"sense", "linear", "quadratic"}, "objective")
    if obj["sense"] not in ("minimize", "maximize"):
        raise ValueError("Objective sense must be minimize or maximize")
    if type(obj["linear"]) is not dict or set(obj["linear"]) - set(ids):
        raise ValueError("Unknown variable in objective linear terms")
    linear = {key: _num(value, "linear coefficient") for key, value in obj["linear"].items()}
    terms = obj["quadratic"]
    if type(terms) is not list or len(terms) > 66:
        raise ValueError("Quadratic terms must be a bounded list")
    quadratic, seen_pairs = [], set()
    for raw in terms:
        term = _fields(raw, {"first", "second", "coefficient"},
                       {"first", "second", "coefficient"}, "quadratic term")
        a, b = term["first"], term["second"]
        if (a not in lookup or b not in lookup or a == b or
            lookup[a]["domain"] != "binary" or lookup[b]["domain"] != "binary"):
            raise ValueError("Quadratic objective products are supported only for distinct binary variables")
        pair = tuple(sorted((a, b)))
        if pair in seen_pairs:
            raise ValueError("Duplicate quadratic objective pair")
        seen_pairs.add(pair)
        quadratic.append({"first": a, "second": b,
                          "coefficient": _num(term["coefficient"], "quadratic coefficient")})
    rows, names = [], set()
    raw_rows = d["constraints"]
    if type(raw_rows) is not list or len(raw_rows) > 100:
        raise ValueError("Linear constraints must be a list of at most 100 rows")
    for row in raw_rows:
        r = _fields(row, {"id", "sense", "rhs", "linear"},
                    {"id", "sense", "rhs", "linear"}, "linear constraint")
        rid = _ident(r["id"], "constraint")
        if rid in names:
            raise ValueError("Duplicate linear constraint ID")
        names.add(rid)
        if r["sense"] not in ("<=", "==", ">="):
            raise ValueError("Unsupported constraint relation")
        if type(r["linear"]) is not dict or set(r["linear"]) - set(ids):
            raise ValueError("Unknown variable in constraint coefficients")
        rows.append({"id": rid, "sense": r["sense"],
                     "rhs": _num(r["rhs"], "constraint RHS"),
                     "linear": {k: _num(v, "constraint coefficient")
                                for k, v in r["linear"].items()}})
    _fields(parameters, {"rhs_overrides"}, set(), "typed parameters")
    overrides = parameters.get("rhs_overrides", {})
    if type(overrides) is not dict or set(overrides) - names:
        raise ValueError("RHS overrides contain an unknown constraint")
    for row in rows:
        if row["id"] in overrides:
            row["rhs"] = _num(overrides[row["id"]], "overridden RHS")
    return {
        "schema_version": 1,
        "variables": normalized,
        "objective": {
            "sense": obj["sense"], "constant": _num(obj.get("constant", 0), "constant"),
            "linear": linear, "quadratic": quadratic,
        },
        "constraints": rows,
        "reference_discrete_states": choices,
        "support": "bounded binary/integer/continuous MILP; quadratic objective only binary × binary",
    }


def render_original(ir: dict) -> str:
    """Human-readable equation generated from EXACT resolved validated IR."""
    o = ir["objective"]
    parts = [f"{o['constant']:+g}"]
    parts += [f"{c:+g}*{k}" for k, c in o["linear"].items()]
    parts += [f"{t['coefficient']:+g}*{t['first']}*{t['second']}"
              for t in o["quadratic"]]
    lines = [o["sense"] + " E = " + " ".join(parts), "subject to"]
    for row in ir["constraints"]:
        lhs = " ".join(f"{v:+g}*{name}" for name, v in row["linear"].items()) or "0"
        lines.append(f"  {row['id']}: {lhs} {row['sense']} {row['rhs']:g}")
    for v in ir["variables"]:
        lines.append(f"  {v['name']} ∈ {v['domain']} [{v['lower']:g}, {v['upper']:g}]")
    return "\n".join(lines)


def objective_value(ir: dict, values: dict[str, float]) -> float:
    o = ir["objective"]
    return (o["constant"]
            + sum(c * values[name] for name, c in o["linear"].items())
            + sum(t["coefficient"] * values[t["first"]] * values[t["second"]]
                  for t in o["quadratic"]))


def original_feasibility(ir: dict, values: dict[str, float]) -> bool:
    if set(values) != {v["name"] for v in ir["variables"]}:
        return False
    for v in ir["variables"]:
        x = values[v["name"]]
        if type(x) not in (int, float) or not isfinite(x):
            return False
        if x < v["lower"] - TOL or x > v["upper"] + TOL:
            return False
        if v["domain"] in ("binary", "integer") and abs(x - round(x)) > TOL:
            return False
    for row in ir["constraints"]:
        lhs = sum(c * values[name] for name, c in row["linear"].items())
        if (row["sense"] == "<=" and lhs > row["rhs"] + TOL or
            row["sense"] == ">=" and lhs < row["rhs"] - TOL or
            row["sense"] == "==" and abs(lhs - row["rhs"]) > TOL):
            return False
    return True


def independent_reference(ir: dict) -> dict:
    """Exhaustive bounded integer/binary choices + independent SciPy HiGHS LP.

    This deliberately builds its own matrices and uses NO SCIP model handles.
    It can certify infeasibility and global optimum for bounded model classes.
    """
    discrete = [v for v in ir["variables"] if v["domain"] != "continuous"]
    continuous = [v for v in ir["variables"] if v["domain"] == "continuous"]
    states = [
        range(int(v["lower"]), int(v["upper"]) + 1)
        for v in discrete
    ]
    sense = ir["objective"]["sense"]
    optimum, winner = None, None
    feasible_states = 0
    for state in product(*states):
        fixed = {v["name"]: int(x) for v, x in zip(discrete, state)}
        if not continuous:
            if not original_feasibility(ir, fixed):
                continue
            feasible_states += 1
            score = objective_value(ir, fixed)
            candidate = fixed
        else:
            continuous_names = [v["name"] for v in continuous]
            o = ir["objective"]
            coeff = np.array([o["linear"].get(k, 0.) for k in continuous_names])
            if sense == "maximize":
                coeff = -coeff
            A_ub, b_ub, A_eq, b_eq = [], [], [], []
            for row in ir["constraints"]:
                rhs = row["rhs"] - sum(
                    c * fixed.get(name, 0) for name, c in row["linear"].items()
                    if name in fixed
                )
                coefficients = [row["linear"].get(name, 0.) for name in continuous_names]
                if row["sense"] == "==":
                    A_eq.append(coefficients); b_eq.append(rhs)
                elif row["sense"] == "<=":
                    A_ub.append(coefficients); b_ub.append(rhs)
                else:
                    A_ub.append([-a for a in coefficients]); b_ub.append(-rhs)
            lp = linprog(
                coeff, method="highs",
                A_ub=A_ub if A_ub else None, b_ub=b_ub if A_ub else None,
                A_eq=A_eq if A_eq else None, b_eq=b_eq if A_eq else None,
                bounds=[(v["lower"], v["upper"]) for v in continuous],
            )
            if lp.status == 2:
                continue
            if not lp.success:
                raise AssertionError(f"Independent continuous LP failed: {lp.message}")
            candidate = {**fixed, **dict(zip(continuous_names, map(float, lp.x)))}
            if not original_feasibility(ir, candidate):
                raise AssertionError("Independent LP violates original model")
            feasible_states += 1
            score = objective_value(ir, candidate)
        if (optimum is None or (sense == "minimize" and score < optimum - TOL)
            or (sense == "maximize" and score > optimum + TOL)):
            optimum, winner = score, candidate
    return {
        "status": "optimal" if optimum is not None else "infeasible",
        "objective": optimum,
        "assignment": winner,
        "enumerated_discrete_states": ir["reference_discrete_states"],
        "feasible_discrete_states": feasible_states,
        "continuous_assignment_solver": "SciPy HiGHS independent LP" if continuous else None,
    }


def solve_scip(ir: dict, lp_path: Path) -> dict:
    model = Model("SYNTHETIC-typed-MILP-exact-pair-products")
    model.hideOutput()
    model.setRealParam("limits/time", 30.)
    variables = {}
    for v in ir["variables"]:
        kind = {"binary": "B", "integer": "I", "continuous": "C"}[v["domain"]]
        variables[v["name"]] = model.addVar(
            name="x_" + v["name"], vtype=kind, lb=v["lower"], ub=v["upper"]
        )
    aux = {}
    for t in ir["objective"]["quadratic"]:
        a, b = t["first"], t["second"]
        p = model.addVar(name=f"prod_{a}_{b}", vtype="B")
        model.addCons(p <= variables[a], name=f"and_a_{a}_{b}")
        model.addCons(p <= variables[b], name=f"and_b_{a}_{b}")
        model.addCons(p >= variables[a] + variables[b] - 1,
                      name=f"and_lower_{a}_{b}")
        aux[(a, b)] = p
    for r in ir["constraints"]:
        expr = quicksum(c * variables[k] for k, c in r["linear"].items())
        if r["sense"] == "<=":
            model.addCons(expr <= r["rhs"], name=r["id"])
        elif r["sense"] == ">=":
            model.addCons(expr >= r["rhs"], name=r["id"])
        else:
            model.addCons(expr == r["rhs"], name=r["id"])
    obj = ir["objective"]
    expression = (obj["constant"]
                  + quicksum(c * variables[k] for k, c in obj["linear"].items())
                  + quicksum(t["coefficient"] * aux[t["first"], t["second"]]
                             for t in obj["quadratic"]))
    model.setObjective(expression, obj["sense"])
    model.writeProblem(str(lp_path), trans=False)
    model.optimize()
    status = str(model.getStatus())
    if status != "optimal":
        return {"status": status, "solver": "SCIP exact MILP pair-product encoding"}
    assignment = {name: float(model.getVal(var)) for name, var in variables.items()}
    if not original_feasibility(ir, assignment):
        raise AssertionError("SCIP solution violates original typed constraints/bounds")
    original = objective_value(ir, assignment)
    if abs(original - float(model.getObjVal())) > TOL:
        raise AssertionError("SCIP LP objective differs from independent original energy")
    return {"status": "optimal", "assignment": assignment,
            "objective": original, "solver": "SCIP exact MILP pair-product encoding"}


def exact_unconstrained_qubo(ir: dict) -> dict | None:
    """For all-binary, unconstrained models only: exact minimization energy.

    A maximize objective is negated (including the offset). This is NOT
    a constrained-QUBO penalty converter and uses NO quantum hardware.
    """
    if ir["constraints"] or any(v["domain"] != "binary" for v in ir["variables"]):
        return None
    sign = 1 if ir["objective"]["sense"] == "minimize" else -1
    obj = ir["objective"]
    q = {
        "definition": "min E_Q = offset + sum diag_i*x_i + sum pairs_ij*x_i*x_j",
        "source_sense": obj["sense"],
        "minimization_negated_from_maximization": sign == -1,
        "offset": sign * obj["constant"],
        "diagonal": {v["name"]: sign * obj["linear"].get(v["name"], 0.)
                     for v in ir["variables"]},
        "pairs": [{"first": t["first"], "second": t["second"],
                   "coefficient": sign * t["coefficient"]}
                  for t in obj["quadratic"]],
        "scope": "EXACT unrestricted all-binary objective, no constraints, no sampler",
    }
    # Independently exhaustively check every binary assignment, including offset.
    names = [v["name"] for v in ir["variables"]]
    for bits in product((0, 1), repeat=len(names)):
        state = dict(zip(names, bits))
        calc = (q["offset"]
                + sum(value * state[k] for k, value in q["diagonal"].items())
                + sum(t["coefficient"] * state[t["first"]] * state[t["second"]]
                      for t in q["pairs"]))
        if abs(calc - sign * objective_value(ir, state)) > TOL:
            raise AssertionError("Unconstrained QUBO energy does not match original")
    return q


def run_typed_ir(data: dict, parameters: dict, output_dir: Path) -> dict:
    ir = validate_ir(data, parameters)
    source = render_original(ir)
    reference = independent_reference(ir)
    scip = solve_scip(ir, output_dir / "actual-typed-scip-milp.lp")
    if reference["status"] != scip["status"]:
        raise AssertionError("SCIP and independent bounded mixed-domain reference disagree")
    if reference["status"] == "optimal" and abs(reference["objective"] - scip["objective"]) > TOL:
        raise AssertionError("SCIP and independent reference original objectives differ")
    qubo = exact_unconstrained_qubo(ir)
    if qubo is not None:
        (output_dir / "exact-unconstrained-qubo.json").write_text(
            json.dumps(qubo, sort_keys=True, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    return {
        "typed_ir": ir,
        "equation_from_same_compiled_ir": source,
        "scip": scip,
        "independent_reference": reference,
        "solver_compatibility": {
            "SCIP_MILP": "validated for bounded binary/integer/continuous with only binary×binary objective products",
            "direct_QUBO": "EXACT only for unconstrained all-binary objectives" if qubo else
                           "REFUSED: requires binary-only variables, no constraints or verified penalty/slack conversion",
            "OpenJij_SA": "NOT_RUN: QUBO export is not quantum hardware",
            "arbitrary_MIQP": "NOT_SUPPORTED for quadratic terms involving integers or continuous variables",
        },
        "exact_unconstrained_qubo": qubo,
        "scope": "SYNTHETIC bounded typed model; not full general MIQP or operational decision support",
    }
