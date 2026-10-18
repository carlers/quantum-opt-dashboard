"""Independent tiny reference: potential coverage vs capacitated shelter assignment.

ONLY artificial numbers. Never use these outputs to recommend real shelters.
Research proposal: docs/EVACUATION_RESEARCH_SPEC.md, review issue #32.

Two independently coded baselines:
  1. Exhaustively enumerated classical maximal-coverage POTENTIAL.
  2. Two-stage lexicographic capacitated SCIP MILP, cross-checked against
     enumeration of all site subsets + independent SciPy HiGHS continuous LP.

No geospatial, hazard, official facilities, quantum hardware or QUBO solver.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import version as dependency_version
from itertools import combinations
import json
from math import isfinite
from pathlib import Path
import platform
from typing import Any

import numpy as np
from scipy.optimize import linprog
from pyscipopt import Model, quicksum


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "tiny_synthetic.json"
TOLERANCE = 1e-7


def encode(payload: Any) -> bytes:
    return (json.dumps(payload, sort_keys=True, allow_nan=False,
                       separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


@dataclass(frozen=True)
class SyntheticProblem:
    demands: tuple[float, ...]  # scenario estimated persons
    capacities: tuple[float, ...]  # usable persons, assumed verified in real use
    travel_minutes: tuple[tuple[float | None, ...], ...]  # None means unreachable
    eligible: tuple[bool, ...]  # only true sites may open
    max_open: int
    zone_ids: tuple[str, ...]
    site_ids: tuple[str, ...]
    label: str = "SYNTHETIC ONLY"

    def __post_init__(self) -> None:
        n, m = len(self.demands), len(self.capacities)
        if not self.label.startswith("SYNTHETIC"):
            raise ValueError("Only explicitly synthetic scenarios are admitted")
        if n < 1 or m < 1 or len(self.travel_minutes) != n:
            raise ValueError("Nonempty, rectangular zone×site matrix required")
        if len(self.eligible) != m or len(self.zone_ids) != n or len(self.site_ids) != m:
            raise ValueError("Candidate/zone array dimensions mismatch")
        if len(set(self.zone_ids)) != n or len(set(self.site_ids)) != m:
            raise ValueError("Duplicate source identifiers")
        if not isinstance(self.max_open, int) or isinstance(self.max_open, bool) or not 0 <= self.max_open <= m:
            raise ValueError("Invalid opened-center budget")
        if not all(type(v) is bool for v in self.eligible):
            raise ValueError("Eligibility must be explicit booleans; unknown is invalid")
        for v in (*self.demands, *self.capacities):
            if isinstance(v, bool) or v is None or not isfinite(float(v)) or float(v) < 0:
                raise ValueError("Unknown/negative/nonfinite population or shelter capacity")
        for row in self.travel_minutes:
            if len(row) != m:
                raise ValueError("Non-rectangular zone×site travel matrix")
            for value in row:
                if value is None:
                    continue
                if isinstance(value, bool) or not isfinite(float(value)) or float(value) < 0:
                    raise ValueError("Travel must be nonnegative minutes or null for no arc")

    @property
    def n_zones(self) -> int:
        return len(self.demands)

    @property
    def n_sites(self) -> int:
        return len(self.capacities)

    @property
    def arcs(self) -> tuple[tuple[int, int], ...]:
        return tuple((i, j) for i, row in enumerate(self.travel_minutes)
                     for j, value in enumerate(row) if value is not None)

    @classmethod
    def from_fixture(cls, path: Path = FIXTURE_PATH) -> "SyntheticProblem":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw["classification"] != "SYNTHETIC TEST FIXTURE ONLY - not real population or evacuation guidance":
            raise ValueError("Not an approved artificial fixture")
        if raw["units"] != {
            "demands": "persons", "capacity": "persons",
            "travel_times": "minutes",
            "budget": "maximum number of opened shelters",
        }:
            raise ValueError("Unit definitions changed")
        return cls(
            demands=tuple(raw["demands"]),
            capacities=tuple(raw["capacities"]),
            travel_minutes=tuple(tuple(row) for row in raw["travel_minutes"]),
            eligible=tuple(raw["eligible"]), max_open=raw["max_open"],
            zone_ids=tuple(raw["zone_ids"]), site_ids=tuple(raw["site_ids"]),
        )


def eligible_subsets(problem: SyntheticProblem):
    indices = tuple(j for j in range(problem.n_sites) if problem.eligible[j])
    for count in range(min(len(indices), problem.max_open) + 1):
        yield from combinations(indices, count)


def maximal_coverage_reference(problem: SyntheticProblem) -> dict:
    """Exact enumeration of binary x,z; no shelter capacity is enforced."""
    best_score = float("-inf")
    best_subset: tuple[int, ...] = ()
    for opened in eligible_subsets(problem):
        covered = sum(
            float(problem.demands[i]) for i in range(problem.n_zones)
            if any(problem.travel_minutes[i][j] is not None for j in opened)
        )
        if covered > best_score + TOLERANCE:
            best_score = covered
            best_subset = opened
    return {
        "label": "potentially_reachable_persons_NOT_served_persons",
        "max_potential_coverage_persons": best_score,
        "selected_sites_zero_based": list(best_subset),
        "capacity_constraints": "NOT_MODELED",
    }


def check_assignment(problem: SyntheticProblem, opened: tuple[int, ...],
                     allocations: dict[tuple[int, int], float],
                     unserved: list[float]) -> dict:
    """Independent original feasibility check (never trust only solver status)."""
    if len(unserved) != problem.n_zones:
        raise AssertionError("Wrong number of unserved-zone amounts")
    if len(set(opened)) != len(opened) or len(opened) > problem.max_open:
        raise AssertionError("Invalid open-site count")
    if any(j < 0 or j >= problem.n_sites or not problem.eligible[j] for j in opened):
        raise AssertionError("An ineligible site is open")
    loads = [0.0] * problem.n_sites
    for (i, j), amount in allocations.items():
        if (i, j) not in problem.arcs or j not in opened:
            raise AssertionError("Assignment on unreachable or closed arc")
        if amount < -TOLERANCE or not isfinite(amount):
            raise AssertionError("Invalid assigned people count")
        loads[j] += amount
    for j in range(problem.n_sites):
        if loads[j] > (problem.capacities[j] if j in opened else 0.) + TOLERANCE:
            raise AssertionError("Capacity or open-state violation")
    for i, demand in enumerate(problem.demands):
        if not isfinite(float(unserved[i])) or unserved[i] < -TOLERANCE:
            raise AssertionError("Invalid unmet demand")
        allocated = sum(amount for (ii, _), amount in allocations.items() if ii == i)
        if abs(allocated + unserved[i] - demand) > TOLERANCE:
            raise AssertionError("Demand balance violated")
    served = sum(allocations.values())
    unmet = sum(unserved)
    burden = sum(float(problem.travel_minutes[i][j]) * value
                 for (i, j), value in allocations.items())
    return {
        "selected_sites_zero_based": list(opened),
        "allocations": [
            {"zone_index": i, "site_index": j, "persons": amount}
            for (i, j), amount in sorted(allocations.items()) if amount > TOLERANCE
        ],
        "unserved_by_zone_persons": list(unserved),
        "site_load_persons": loads,
        "served_persons": served,
        "unserved_persons": unmet,
        "total_travel_person_minutes": burden,
        "mean_travel_minutes_per_served_person": burden / served if served > TOLERANCE else None,
        "original_constraints_ok": True,
    }


def scip_lexicographic(problem: SyntheticProblem, *,
                       stage1_lp: Path | None = None,
                       stage2_lp: Path | None = None,
                       require_all_served: bool = False) -> dict:
    """Two-stage SCIP MILP, not a weighted aggregate objective."""
    model = Model("SYNTHETIC-evacuation-capacitated")
    model.hideOutput()
    model.setRealParam("limits/time", 30.0)
    x = [model.addVar(vtype="B", name=f"open_{j}") for j in range(problem.n_sites)]
    unmet = [model.addVar(vtype="C", lb=0.0, ub=float(problem.demands[i]),
                          name=f"unserved_{i}") for i in range(problem.n_zones)]
    y = {(i, j): model.addVar(vtype="C", lb=0., ub=float(problem.demands[i]),
                             name=f"people_{i}_{j}")
         for i, j in problem.arcs}
    model.addCons(quicksum(x) <= problem.max_open, name="max_open")
    for j in range(problem.n_sites):
        model.addCons(x[j] <= int(problem.eligible[j]), name=f"eligible_{j}")
        model.addCons(quicksum(y[i, jj] for i, jj in problem.arcs if jj == j)
                      <= float(problem.capacities[j]) * x[j], name=f"capacity_{j}")
    for i in range(problem.n_zones):
        model.addCons(quicksum(y[ii, j] for ii, j in problem.arcs if ii == i)
                      + unmet[i] == float(problem.demands[i]), name=f"demand_{i}")
        if require_all_served:
            model.addCons(unmet[i] == 0, name=f"require_all_served_{i}")
    model.setObjective(quicksum(unmet), "minimize")
    if stage1_lp is not None:
        model.writeProblem(str(stage1_lp), trans=False)
    model.optimize()
    status = str(model.getStatus())
    if status != "optimal":
        return {"status": status, "kind": "SYNTHETIC", "phase": 1}
    optimum_unmet = float(model.getObjVal())

    model.freeTransform()
    model.addCons(quicksum(unmet) <= optimum_unmet + 1e-9, name="fix_optimal_unserved")
    model.setObjective(quicksum(float(problem.travel_minutes[i][j]) * y[i, j]
                                for i, j in problem.arcs), "minimize")
    if stage2_lp is not None:
        model.writeProblem(str(stage2_lp), trans=False)
    model.optimize()
    second_status = str(model.getStatus())
    if second_status != "optimal":
        return {"status": second_status, "kind": "SYNTHETIC", "phase": 2,
                "phase1_optimal_unserved_persons": optimum_unmet}

    opened = tuple(j for j in range(problem.n_sites) if model.getVal(x[j]) > 0.5)
    allocations = {(i, j): float(model.getVal(y[i, j]))
                   for i, j in problem.arcs if model.getVal(y[i, j]) > TOLERANCE}
    unserved = [float(model.getVal(unmet[i])) for i in range(problem.n_zones)]
    result = check_assignment(problem, opened, allocations, unserved)
    if abs(result["unserved_persons"] - optimum_unmet) > TOLERANCE:
        raise AssertionError("Second-stage solution violated lexicographic priority")
    return {
        **result,
        "kind": "SYNTHETIC",
        "status": "optimal", "phase1_status": "optimal", "phase2_status": "optimal",
        "phase1_optimal_unserved_persons": optimum_unmet,
        "phase2_optimal_travel_person_minutes": float(model.getObjVal()),
        "solver": "SCIP via PySCIPOpt",
    }


def _independent_flow_lp(problem: SyntheticProblem, opened: tuple[int, ...]) -> dict:
    """SciPy-HiGHS continuous assignment LP for *fixed enumerated* x.

    Matrix built from scratch; does not call SCIP or check_assignment().
    """
    edges = [(i, j) for i in range(problem.n_zones) for j in opened
             if problem.travel_minutes[i][j] is not None]
    n_e, n_z = len(edges), problem.n_zones
    width = n_e + n_z
    demand_eq = np.zeros((n_z, width))
    for col, (i, _) in enumerate(edges):
        demand_eq[i, col] = 1.
    for i in range(n_z):
        demand_eq[i, n_e + i] = 1.
    loads = np.zeros((len(opened), width))
    for row, j in enumerate(opened):
        for col, (_, jj) in enumerate(edges):
            if j == jj:
                loads[row, col] = 1.
    site_caps = np.asarray([float(problem.capacities[j]) for j in opened])
    bounds = [(0., float(problem.demands[i])) for i, _ in edges] + [
        (0., float(v)) for v in problem.demands
    ]
    first_obj = np.asarray([0.] * n_e + [1.] * n_z)
    first = linprog(first_obj, A_eq=demand_eq, b_eq=problem.demands,
                    A_ub=loads if len(opened) else None,
                    b_ub=site_caps if len(opened) else None,
                    bounds=bounds, method="highs")
    if not first.success:
        raise AssertionError("Independent fixed-opening LP infeasible despite unmet variables")
    cap_and_priority = np.vstack([loads, first_obj])
    target_and_priority = np.append(site_caps, float(first.fun) + 1e-9)
    second_obj = np.asarray([float(problem.travel_minutes[i][j]) for i, j in edges] +
                            [0.] * n_z)
    second = linprog(second_obj, A_eq=demand_eq, b_eq=problem.demands,
                     A_ub=cap_and_priority, b_ub=target_and_priority,
                     bounds=bounds, method="highs")
    if not second.success:
        raise AssertionError("Independent stage-two LP could not preserve optimum")
    return {
        "unserved": float(first.fun),
        "travel": float(second.fun),
        "allocations": [
            [i, j, float(second.x[col])] for col, (i, j) in enumerate(edges)
            if second.x[col] > TOLERANCE
        ],
    }


def independent_enumeration(problem: SyntheticProblem) -> dict:
    """Enumerate every eligible opening pattern; optimize flows via SciPy.

    For tiny synthetic problems ONLY. No exponential enumeration for real use.
    """
    candidates = []
    for opened in eligible_subsets(problem):
        lp = _independent_flow_lp(problem, opened)
        candidates.append((float(lp["unserved"]), float(lp["travel"]), opened, lp))
    best_u = min(item[0] for item in candidates)
    best_travel = min(item[1] for item in candidates if item[0] <= best_u + TOLERANCE)
    # Deterministic tie-break; matches the first artificial benchmark uniquely.
    winner = next(item for item in sorted(candidates, key=lambda row: row[2])
                  if item[0] <= best_u + TOLERANCE and
                     item[1] <= best_travel + TOLERANCE)
    return {
        "kind": "SYNTHETIC",
        "method": "enumerate eligible opening subsets + scipy.optimize.linprog HiGHS",
        "opening_subsets_checked": len(candidates),
        "min_unserved_persons": best_u,
        "min_travel_person_minutes": best_travel,
        "selected_sites_zero_based": list(winner[2]),
        "continuous_flow_solution": winner[3],
    }


def validate_parity(problem: SyntheticProblem, *, stage1_lp: Path | None = None,
                    stage2_lp: Path | None = None) -> dict:
    covering = maximal_coverage_reference(problem)
    scip = scip_lexicographic(problem, stage1_lp=stage1_lp, stage2_lp=stage2_lp)
    reference = independent_enumeration(problem)
    if scip["status"] != "optimal":
        raise AssertionError("Synthetic SCIP failed independently checkable optimization")
    if abs(scip["unserved_persons"] - reference["min_unserved_persons"]) > 1e-6:
        raise AssertionError("SCIP service objective differs from enumerated HiGHS")
    if abs(scip["total_travel_person_minutes"] -
           reference["min_travel_person_minutes"]) > 1e-6:
        raise AssertionError("SCIP travel objective differs from enumerated HiGHS")
    return {
        "schema_version": 1, "kind": "SYNTHETIC", "actual_shelters_used": False,
        "scenario": {"zone_ids": list(problem.zone_ids),
                     "site_ids": list(problem.site_ids),
                     "demands_persons": list(problem.demands),
                     "capacities_persons": list(problem.capacities),
                     "max_open": problem.max_open,
                     "eligible": list(problem.eligible),
                     "travel_minutes": [list(row) for row in problem.travel_minutes]},
        "mclp_potential_only": covering,
        "capacitated_scip": scip,
        "independent_enumeration_highs": reference,
        "warning": "Synthetic research software validation, NOT real evacuation advice or certified shelter infrastructure",
    }


def run_cli(output_dir: Path, fixture_path: Path = FIXTURE_PATH) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = fixture_path.read_bytes()
    raw_fixture = json.loads(source)
    problem = SyntheticProblem.from_fixture(fixture_path)
    result = validate_parity(problem,
                             stage1_lp=output_dir / "synthetic-stage1-unserved.lp",
                             stage2_lp=output_dir / "synthetic-stage2-travel.lp")
    expected = raw_fixture["predeclared_expected"]
    scip = result["capacitated_scip"]
    mclp = result["mclp_potential_only"]
    if not (
        abs(scip["unserved_persons"] - expected["min_unserved_persons"]) < 1e-6
        and scip["selected_sites_zero_based"] ==
            [expected["selected_site_index_zero_based"]]
        and abs(scip["total_travel_person_minutes"] -
                expected["min_travel_person_minutes"]) < 1e-6
        and abs(mclp["max_potential_coverage_persons"] -
                expected["maximal_covering_potential_persons"]) < 1e-6
    ):
        raise AssertionError("Reference output no longer matches PREDECLARED artificial fixture")

    result["provenance"] = {
        "fixture_sha256": sha256(source).hexdigest(),
        "protocol_issue": 32, "python": platform.python_version(),
        "pyscipopt": dependency_version("pyscipopt"),
        "scipy": dependency_version("scipy"),
        "numpy": np.__version__,
        "source": "tiny_synthetic.json; no real Philippine shelters/population or hazards",
    }
    (output_dir / "summary.json").write_bytes(encode(result))
    (output_dir / "fixture.json").write_bytes(source)
    paths = ("fixture.json", "summary.json", "synthetic-stage1-unserved.lp",
             "synthetic-stage2-travel.lp")
    manifest = {
        "schema_version": 1, "kind": "SYNTHETIC",
        "files_sha256": {
            name: sha256((output_dir / name).read_bytes()).hexdigest() for name in paths
        },
    }
    (output_dir / "manifest.json").write_bytes(encode(manifest))
    print("EVAC_SYNTHETIC_REFERENCE " + json.dumps({
        "capacity_service_result": scip["unserved_persons"],
        "travel_person_minutes": scip["total_travel_person_minutes"],
        "selected_sites_zero_based": scip["selected_sites_zero_based"],
        "potential_coverage_persons_not_served": mclp["max_potential_coverage_persons"],
        "independent_subsets_checked": result["independent_enumeration_highs"]["opening_subsets_checked"],
    }, sort_keys=True))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run_cli(args.output_dir)
