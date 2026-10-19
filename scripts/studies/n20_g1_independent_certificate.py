"""Independent falsification of registered G1 site scenario and original G0.

Reads the PREVIOUS generated result; does not select the 20 sites or import
their generation algorithm. Rebuilds every link from original GeoJSON using
a separate math.hypot graph implementation, checks all K=5 bit sets and runs
a separate SCIP optimality certificate on original source-formula coefficients.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist
from shapely import concave_hull
from shapely.geometry import MultiPoint
from pyscipopt import Model, quicksum

from scripts.n20_independent_geometry_audit import (
    EXPECTED_DATA_SHA, EXPECTED_FIXED, EXPECTED_FREE,
    original_fixed_spacing, source_coordinates, reconstruct
)

ORIGINAL_FEASIBLE_SHA = "2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a"


def independent_source_energy(case, selected):
    chosen = set(selected)
    linear = [float.fromhex(x) for x in case["linear_float64_hex"]]
    quadratic = [(i, j, float.fromhex(q)) for i, j, q in
                 case["quadratic_ij_float64_hex"]]
    return sum(linear[i] for i in selected) + sum(
        q for i, j, q in quadratic if i in chosen and j in chosen
    )


def independent_case(source_xy, fixed, hull, dmax, case, label):
    free = case["candidate_master_feature_positions"]
    if (len(free) != 20 or len(set(free)) != 20
            or any(i in fixed or i >= len(source_xy) or i < 0 for i in free)):
        raise AssertionError(f"{label}: invalid raw source candidate master identities")
    actual = [source_xy[i] for i in free + fixed]
    graph = reconstruct(actual, hull, dmax, 20)
    if (graph["free_neighbor_indices"] != case["free_neighbors"]
            or graph["fixed_neighbor_flags"] != case["fixed_flags"]
            or graph["near_threshold_pairs_1e_minus_7_m"]):
        raise AssertionError(f"{label}: independent raw GeoJSON adjacency differs")
    if label == "G1" and not all(graph["fixed_neighbor_flags"]):
        raise AssertionError("G1: a selected new candidate has NO geometrically valid fixed link")
    if label == "G0" and free != EXPECTED_FREE:
        raise AssertionError("G0: historical candidate IDs changed")

    digest = hashlib.sha256()
    best = math.inf
    winners = []
    feasible = 0
    for combo in combinations(range(20), 5):
        selected = set(combo)
        if any(not graph["fixed_neighbor_flags"][i] and
               not any(j in selected for j in graph["free_neighbor_indices"][i])
               for i in combo):
            continue
        feasible += 1
        digest.update((",".join(map(str, combo)) + "\n").encode("ascii"))
        energy = independent_source_energy(case, combo)
        if energy < best - 1e-9:
            best, winners = energy, [list(combo)]
        elif abs(energy - best) <= 1e-9:
            winners.append(list(combo))
    if (feasible != case["feasible_K5_count"]
            or digest.hexdigest() != case["feasible_K5_membership_sha256"]
            or winners != case["optima_local_positions"]
            or abs(best - case["best_original_source_objective"]) > 1e-7):
        raise AssertionError(f"{label}: independent complete graph/set/energy differs")
    if label == "G0" and (feasible != 1077 or digest.hexdigest() != ORIGINAL_FEASIBLE_SHA):
        raise AssertionError("G0 historical complete feasible membership changed")

    scip = Model(f"n20_prereg_candidate_{label}")
    scip.hideOutput()
    x = [scip.addVar(name=f"x{i}", vtype="B") for i in range(20)]
    quadratic = [(int(i), int(j), float.fromhex(q))
                 for i, j, q in case["quadratic_ij_float64_hex"]]
    if any(q < 0 for _, _, q in quadratic):
        raise AssertionError("Source MIQP nonnegative pair penalties were unexpectedly changed")
    zvars = []
    for i, j, q in quadratic:
        z = scip.addVar(vtype="B", name=f"p{i}_{j}")
        scip.addCons(z >= x[i] + x[j] - 1)
        scip.addCons(z <= x[i])
        scip.addCons(z <= x[j])
        zvars.append(z)
    scip.addCons(quicksum(x) == 5)
    for i in range(20):
        scip.addCons(x[i] <= int(graph["fixed_neighbor_flags"][i]) +
                     quicksum(x[j] for j in graph["free_neighbor_indices"][i]))
    linear = [float.fromhex(s) for s in case["linear_float64_hex"]]
    scip.setObjective(
        quicksum(linear[i] * x[i] for i in range(20)) +
        quicksum(q * zvars[k] for k, (_, _, q) in enumerate(quadratic)),
        sense="minimize"
    )
    scip.setRealParam("limits/time", 30.0)
    scip.optimize()
    status = str(scip.getStatus())
    if status != "optimal":
        raise AssertionError(f"{label}: SCIP did not independently certify optimum: {status}")
    sol = scip.getBestSol()
    chosen = [i for i in range(20) if scip.getSolVal(sol, x[i]) > 0.5]
    scip_energy = independent_source_energy(case, chosen)
    if ([chosen] != winners or abs(scip_energy - best) > 1e-7
            or abs(float(scip.getObjVal()) - best) > 1e-7):
        raise AssertionError(f"{label}: SCIP optimum/site mismatch vs full enumeration")

    # Independent cross-library spatial coverage check: scipy.spatial.cdist
    # dense 5417×35 distances vs source study cKDTree query.
    point_xy = np.asarray(source_xy, dtype=float)
    coverage = {}
    for key, indices in (
        ("candidate_20", free),
        ("installed_optimum_5", case["optima_master_positions"][0]),
    ):
        distances = cdist(point_xy, point_xy[fixed + indices]).min(axis=1)
        key_name = ("coverage_15_fixed_plus_20_candidate_all_5417_metres"
                    if key == "candidate_20" else
                    "coverage_15_fixed_plus_5_installed_all_5417_metres")
        stated = case[key_name]
        for field, actual_value in {
            "min": float(np.min(distances)), "mean": float(np.mean(distances)),
            "median": float(np.median(distances)), "max": float(np.max(distances)),
        }.items():
            if abs(actual_value - stated[field]) > 1e-6:
                raise AssertionError(
                    f"{label}: independent {key} {field} coverage disagrees"
                )
        coverage[key] = {field: stated[field] for field in
                         ("min", "mean", "median", "max")}
    return {
        "scenario": label,
        "independently_reconstructed_source_direct_fixed_edges":
            graph["free_fixed_raw_edges"],
        "independently_reconstructed_source_free_free_edges":
            graph["free_free_undirected_edges"],
        "independently_certified_K5_feasible_count": feasible,
        "independently_certified_K5_membership_sha256": digest.hexdigest(),
        "independent_Scip_status": status,
        "independent_Scip_winner_master_feature_positions": [free[i] for i in chosen],
        "independently_certified_source_energy": scip_energy,
        "independent_cdist_coverage_metres": coverage,
    }


def verify(result):
    if (result.get("original_source_data_sha256") != EXPECTED_DATA_SHA
            or result.get("original_15_fixed_master_ids") != EXPECTED_FIXED):
        raise AssertionError("Generator study isn't based on pinned raw source")
    source_xy, fixed = source_coordinates()
    if fixed != EXPECTED_FIXED:
        raise AssertionError("Raw original 15 original fixed stations changed")
    hull = concave_hull(MultiPoint(source_xy), ratio=0.05, allow_holes=True)
    dmax = original_fixed_spacing([source_xy[i] for i in fixed])
    if abs(float.fromhex(result["dmax_original_m_float64_hex"]) - dmax) > 1e-7:
        raise AssertionError("Source threshold changed")
    cert = {
        label: independent_case(source_xy, fixed, hull, dmax, result[label], label)
        for label in ("G0", "G1")
    }
    if not result["G1_qualified_direct_fixed_pool_count"] >= 20:
        raise AssertionError("Missing qualifying pool, no G1 study possible")
    if result["G0"]["candidate_master_feature_positions"] == result["G1"][
        "candidate_master_feature_positions"
    ] and result["observed_hypotheses"]["H0_same_20_master_candidates"] is False:
        raise AssertionError("Generator hypothesis report doesn't match identities")
    return {
        "schema_version": 1,
        "scope": "independent_from_original_G0_G1_pool_generator_full_K5_geometry_Scip_and_coverage",
        "source_data_sha256": EXPECTED_DATA_SHA,
        "source_geojson_feature_count": len(source_xy),
        "source_marked_fixed_count": len(fixed),
        "results": cert,
        "limitations": (
            "Independent graph/objective/SCIP/coverage verification; same original "
            "GeoJSON, Shapely GEOS hull rule, source weights, no field radio/real "
            "monitoring ground truth and no manuscript parity."
        )
    }


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--study", type=Path, required=True)
    args.add_argument("--output", type=Path, required=True)
    opts = args.parse_args()
    if opts.output.exists():
        raise FileExistsError("Refuse to replace independent certificate")
    case = json.loads(opts.study.read_text(encoding="utf-8"))
    cert = verify(case)
    opts.output.parent.mkdir(parents=True, exist_ok=True)
    opts.output.write_text(json.dumps(cert, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("N20_G0_G1_INDEPENDENT_GEOMETRY_SCIP_COVERAGE_CERTIFICATE " +
          json.dumps(cert["results"], sort_keys=True))


if __name__ == "__main__":
    main()
