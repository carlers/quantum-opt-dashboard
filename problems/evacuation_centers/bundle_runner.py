"""Safe allowlisted CLI for replaceable synthetic datasets/formulations.

One versioned bundle -> one validated model -> actual SCIP LP where solved
-> independent result audit + source hashes. Supports tiny general binary
quadratic models and the two distinct synthetic evacuation model variants.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

from pyscipopt import Model, quicksum

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "framework" / "python"))
from qopt.core.experiment_bundle import canonical, load_bundle
from qopt.core.binary_quadratic import run_binary_quadratic
from synthetic_reference import (
    SyntheticProblem, independent_enumeration, maximal_coverage_reference,
    scip_lexicographic, validate_parity,
)


def _synthetic_evacuation(data: dict, parameters: dict) -> SyntheticProblem:
    allowed = {"classification", "units", "zone_ids", "site_ids", "demands",
               "capacities", "eligible", "travel_minutes", "max_open",
               "predeclared_expected", "schema_version"}
    mandatory = allowed - {"predeclared_expected", "schema_version"}
    if type(data) is not dict or set(data) - allowed or mandatory - set(data):
        raise ValueError("Evacuation dataset has missing/unexpected fields")
    if data["classification"] != (
        "SYNTHETIC TEST FIXTURE ONLY - not real population or evacuation guidance"
    ):
        raise ValueError("Unverified real evacuation data cannot use synthetic adapter")
    if data["units"] != {
        "demands": "persons", "capacity": "persons", "travel_times": "minutes",
        "budget": "maximum number of opened shelters",
    }:
        raise ValueError("Dataset units must be explicit and compatible")
    if type(parameters) is not dict or set(parameters) - {"max_open"}:
        raise ValueError("Unsupported evacuation formulation parameters")
    max_open = parameters.get("max_open", data["max_open"])
    return SyntheticProblem(
        demands=tuple(data["demands"]), capacities=tuple(data["capacities"]),
        travel_minutes=tuple(tuple(row) for row in data["travel_minutes"]),
        eligible=tuple(data["eligible"]), zone_ids=tuple(data["zone_ids"]),
        site_ids=tuple(data["site_ids"]), max_open=max_open,
    )


def _scip_covering(problem: SyntheticProblem, lp: Path) -> dict:
    """SCIP MILP covering potential (NO facility capacity), cross-checked."""
    model = Model("SYNTHETIC-covering-potential-not-served")
    model.hideOutput()
    x = [model.addVar(vtype="B", name=f"open_{j}")
         for j in range(problem.n_sites)]
    z = [model.addVar(vtype="B", name=f"covered_{i}")
         for i in range(problem.n_zones)]
    model.addCons(quicksum(x) <= problem.max_open, name="max_open")
    for j in range(problem.n_sites):
        model.addCons(x[j] <= int(problem.eligible[j]), name=f"eligibility_{j}")
    for i in range(problem.n_zones):
        model.addCons(z[i] <= quicksum(
            x[j] for j in range(problem.n_sites)
            if problem.travel_minutes[i][j] is not None and problem.eligible[j]
        ), name=f"reachable_{i}")
    model.setObjective(quicksum(float(problem.demands[i]) * z[i]
                                for i in range(problem.n_zones)), "maximize")
    model.writeProblem(str(lp), trans=False)
    model.optimize()
    if str(model.getStatus()) != "optimal":
        raise AssertionError("Toy SCIP MCLP not proven optimal")
    x_set = [j for j in range(problem.n_sites) if model.getVal(x[j]) > .5]
    returned = float(model.getObjVal())
    independently_reachable = sum(
        float(problem.demands[i]) for i in range(problem.n_zones)
        if any(problem.travel_minutes[i][j] is not None for j in x_set)
    )
    if abs(returned - independently_reachable) > 1e-7:
        raise AssertionError("Maximal-coverage objective audit failed")
    exact = maximal_coverage_reference(problem)
    if abs(returned - exact["max_potential_coverage_persons"]) > 1e-7:
        raise AssertionError("SCIP maximum coverage vs enumerated solution differs")
    return {
        "status": "optimal", "solver": "SCIP binary MCLP",
        "potentially_reachable_persons_NOT_served": returned,
        "selected_site_indices": x_set,
        "capacity_constraints": "NOT_MODELED",
        "independent_reference": exact,
    }


def _run_evacuation(bundle, folder: Path) -> dict:
    allowed = {"maximal_coverage", "capacitated_lexicographic"}
    if bundle.formulation_id not in allowed:
        raise ValueError("Unknown evacuation formulation ID; never silently substitute")
    problem = _synthetic_evacuation(bundle.data, bundle.parameters)
    details = {
        "scenario": {
            "zones": list(problem.zone_ids), "sites": list(problem.site_ids),
            "demands_persons": list(problem.demands),
            "verified_synthetic_capacity_persons": list(problem.capacities),
            "max_open": problem.max_open,
            "eligible": list(problem.eligible),
            "travel_minutes": [list(r) for r in problem.travel_minutes],
        },
        "model_description": (
            "max sum_i demand_i * covered_i, z_i <= sum reachable open_j; "
            "sum_j open_j <= K; NO capacity"
            if bundle.formulation_id == "maximal_coverage"
            else "min sum_i unmet_i, then min sum_ij travel_ij * served_ij; "
                 "demand balance, site capacity, eligibility, max K, reachable arcs"
        ),
    }
    if bundle.formulation_id == "maximal_coverage":
        solver = _scip_covering(problem, folder / "actual-scip-covering.lp")
        return {**details, "result": solver,
                "human_label": "Potential demand coverage ONLY, not persons served"}
    result = validate_parity(
        problem, stage1_lp=folder / "actual-scip-unserved.lp",
        stage2_lp=folder / "actual-scip-travel.lp"
    )
    return {**details, "result": result,
            "human_label": "Capacitated population served/unserved plus assigned travel"}


def execute(manifest_path: Path, output_dir: Path) -> dict:
    bundle = load_bundle(manifest_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if bundle.problem_id == "evacuation.synthetic":
        result = _run_evacuation(bundle, output_dir)
    elif bundle.problem_id == "binary_quadratic.synthetic":
        if bundle.formulation_id != "binary_quadratic":
            raise ValueError("Unsupported binary problem formulation")
        result = run_binary_quadratic(bundle.data, bundle.parameters, output_dir)
    else:
        raise ValueError("Unknown problem adapter; registry lookup is fail-closed")

    audited = {
        "schema_version": 1,
        "kind": "SYNTHETIC-VALIDATED-CONFIGURATION",
        "bundle_audit": bundle.audit(), "result": result,
        "disclaimer": "Only synthetic examples. Not live Streamlit, real shelters, or quantum hardware.",
    }
    (output_dir / "run.json").write_bytes(canonical(audited))
    audited_names = sorted(p.name for p in output_dir.iterdir()
                           if p.is_file() and p.name != "manifest.json")
    hashes = {name: sha256((output_dir / name).read_bytes()).hexdigest()
              for name in audited_names}
    (output_dir / "manifest.json").write_bytes(canonical({
        "schema_version": 1,
        "bundle_fingerprint": bundle.fingerprint,
        "dataset_sha256": bundle.dataset_sha256,
        "files_sha256": hashes,
    }))
    print("QOPT_BUNDLE_RESULT " + json.dumps({
        "problem_id": bundle.problem_id,
        "formulation_id": bundle.formulation_id,
        "fingerprint": bundle.fingerprint,
        "output_files": audited_names,
    }, sort_keys=True))
    return audited


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    options = parser.parse_args()
    execute(options.bundle, options.output_dir)


if __name__ == "__main__":
    main()
