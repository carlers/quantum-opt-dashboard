"""Second-path SCIP/independent enumeration of posthoc-motivated W0/W1.

Consumes fixed coefficient hex manifests, does NOT call original study's
energy, feasibility or winner helpers. No real-current assumption.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
from pathlib import Path

from pyscipopt import Model, quicksum

EXPECTED_FEASIBLE_SHA = "2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a"


def check_case(case):
    linear = [float.fromhex(a) for a in case["linear_float64_hex"]]
    quad = [(int(i), int(j), float.fromhex(q))
            for i, j, q in case["quadratic_ij_float64_hex"]]
    graph, fixed = case["neighbors"], case["fixed_flags"]
    if len(linear) != len(graph) or len(fixed) != 20:
        raise AssertionError("Invalid frozen source model shape")
    for i, row in enumerate(graph):
        if sorted(set(row)) != row or any(i not in graph[j] for j in row):
            raise AssertionError("Invalid source symmetrical one-hop graph")
    if any(q < -1e-13 for _, _, q in quad):
        raise AssertionError("Unregistered negative pair penalty")
    feasible = []
    sha = hashlib.sha256()
    for tup in combinations(range(20), 5):
        selected = set(tup)
        if all(fixed[i] == 1 or bool(selected.intersection(graph[i])) for i in tup):
            sha.update((",".join(str(i) for i in tup) + "\n").encode("ascii"))
            e = sum(linear[i] for i in tup) + sum(
                q for i, j, q in quad if i in selected and j in selected
            )
            feasible.append((float(e), tup))
    if len(feasible) != 1077 or sha.hexdigest() != EXPECTED_FEASIBLE_SHA:
        raise AssertionError("Independent source all-feasible-set membership fails")
    best = min(feasible, key=lambda item: (item[0], item[1]))

    scip = Model("independent_wake_delta_scenario")
    scip.hideOutput()
    x = [scip.addVar(name=f"x{i}", vtype="B") for i in range(20)]
    z = []
    for i, j, _ in quad:
        zz = scip.addVar(name=f"q{i}_{j}", vtype="B")
        scip.addCons(zz <= x[i])
        scip.addCons(zz <= x[j])
        scip.addCons(zz >= x[i] + x[j] - 1)
        z.append(zz)
    scip.addCons(quicksum(x) == 5)
    for i in range(20):
        scip.addCons(x[i] <= int(fixed[i]) +
                     quicksum(x[j] for j in graph[i]))
    scip.setObjective(
        quicksum(linear[i] * x[i] for i in range(20)) +
        quicksum(q * z[k] for k, (_, _, q) in enumerate(quad)), "minimize"
    )
    scip.setRealParam("limits/time", 30.)
    scip.optimize()
    status = str(scip.getStatus())
    if status != "optimal":
        raise AssertionError(f"Exact SCIP did not certify scenario: {status}")
    sol = scip.getBestSol()
    chosen = tuple(i for i in range(20) if scip.getSolVal(sol, x[i]) > .5)
    if (chosen != best[1] or abs(float(scip.getObjVal()) - best[0]) > 1e-7
            or abs(best[0] - case["exact_K5"]["best_energy_under_own_objective"]) > 1e-7
            or case["exact_K5"]["winner_local_positions"] != [list(chosen)]):
        raise AssertionError("Independent exhaustive objective / SCIP / study optimum differ")
    return {
        "status": status,
        "independent_source_feasible_set_sha256": sha.hexdigest(),
        "independent_feasible_count": len(feasible),
        "independent_Scip_winner_local_positions": list(chosen),
        "independent_Scip_objective": float(scip.getObjVal()),
        "independent_full_enumeration_best": best[0],
        "pair_terms": len(quad),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--study", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError("Refuse to overwrite certified evidence")
    src = json.loads(args.study.read_text(encoding="utf-8"))
    if not src.get("previously_known_wake_off_same_winner"):
        raise AssertionError("Cannot hide previous W1 posthoc observation")
    certs = {name: check_case(src["cases"][name])
             for name in ("W0_original", "W1_wake_off")}
    if src["cases"]["W0_original"]["coefficient_manifest_sha256"] == src[
        "cases"]["W1_wake_off"]["coefficient_manifest_sha256"
    ]:
        raise AssertionError("No changed wake coefficients in counterfactual")
    out = {
        "schema_version": 1,
        "scope": "independent_enumeration_and_PySCIPOpt_wake_sensitivity_not_physical_model",
        "original_source_dataset_sha256": src["original_source_geojson_sha256"],
        "scenarios": certs,
        "limitation": (
            "Independent SCIP reads same source-derived coefficient manifests, "
            "not independent measurements of currents, radio links or fish health."
        )
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("N20_WAKE_INDEPENDENT_SCIP_CERTIFICATE " + json.dumps(certs, sort_keys=True))


if __name__ == "__main__":
    main()
