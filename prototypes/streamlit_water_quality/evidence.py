"""Headless, auditable N=20 SCIP evidence export.

This script executes the existing Streamlit pilot model unchanged. It does
not claim the historical paper inputs match the committed dataset or notebook.
All geographical identifiers are explicitly differentiated from local indices.

Usage:
  python prototypes/streamlit_water_quality/evidence.py --output-dir /tmp/n20-evidence
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path
import platform
import sys
from time import perf_counter

import numpy as np

from model import (
    CURRENT_VECTOR, D_MAX_BUFFER, FACTOR_NAMES, HULL_RATIO, L_C, L_W,
    NOTEBOOK_WEIGHTS, PAPER_WEIGHTS, POOL_SIZE,
    evaluate, load_data, make_instance, solve_scip,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GEOJSON = REPO_ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
NOTEBOOK = REPO_ROOT / "problems/water_quality/notebooks/experiment9 grid search copy.ipynb"
N_FREE = 20
BUDGET = 5
PAPER_REPORTED_SCIP_ENERGY = -3.301319
PAPER_REPORTED_LOCAL_INDICES = (0, 1, 3, 6, 7)

# Manually transcribed from the previous paper, page 4, Table III.
TABLE_III = np.array(
    [[1, 4, 6, 8], [1/4, 1, 3, 5], [1/6, 1/3, 1, 3], [1/8, 1/5, 1/3, 1]],
    dtype=float,
)
LOCAL_SPLITS = ((0.5, 0.5), (2/3, 1/3), (2/3, 1/3), (0.5, 0.5))
SCENARIO_NOTES = {
    "notebook": "Weights hard-coded in Cell 2 of the committed research notebook.",
    "paper-table-iv": "Published Table IV weights applied to the committed dataset; not an original paper rerun.",
    "table-iii-eigen": "Counterfactual principal eigenvector of printed Table III with local splits; not published weights.",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_bytes(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n").encode("utf-8")


def eigenvector_weights() -> np.ndarray:
    vals, vecs = np.linalg.eig(TABLE_III)
    index = int(np.argmax(vals.real))
    main = vecs[:, index].real
    if main.sum() < 0:
        main = -main
    main = main / main.sum()
    return np.asarray([main[i] * f for i, pair in enumerate(LOCAL_SPLITS) for f in pair])


def weights_for(scenario: str) -> np.ndarray:
    if scenario == "notebook":
        return NOTEBOOK_WEIGHTS.copy()
    if scenario == "paper-table-iv":
        return PAPER_WEIGHTS.copy()
    if scenario == "table-iii-eigen":
        return eigenvector_weights()
    raise ValueError(f"Unknown N20 scenario: {scenario}")


def enumerated_optimum(instance) -> dict:
    """Independent finite search over the C(20, 5) feasible-or-not subsets.

    This checks the *assembled* coefficients and constraints without using
    model.evaluate or SCIP. Construction parity is tested independently in
    test_n20_reference.py.
    """
    n = len(instance.free_indices)
    if n != N_FREE or instance.budget != BUDGET:
        raise ValueError("Exhaustive reference is explicitly limited to N=20, K=5")
    best = float("inf")
    winners = []
    feasible_count = 0
    considered = 0
    for subset in combinations(range(n), BUDGET):
        considered += 1
        chosen = set(subset)
        if any(
            not (instance.fixed_neighbors[i] or chosen.intersection(instance.neighbors[i]))
            for i in subset
        ):
            continue
        feasible_count += 1
        score = sum(float(instance.linear[i]) for i in subset)
        score += sum(float(q) for i, j, q in instance.quadratic if i in chosen and j in chosen)
        if score < best - 1e-9:
            best, winners = score, [list(subset)]
        elif abs(score - best) <= 1e-9:
            winners.append(list(subset))
    if not winners:
        raise RuntimeError("No feasible reference subset for N=20, K=5")
    return {
        "combinations_checked": considered,
        "feasible_count": feasible_count,
        "minimum_energy": float(best),
        "optimal_local_index_sets": winners,
    }


def run_scenario(scenario: str, *, time_limit: float = 120.0) -> tuple[dict, dict, list[dict]]:
    if not np.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("time_limit must be a finite positive number")
    weights = weights_for(scenario)
    data = load_data(GEOJSON)
    instance, simulated = make_instance(data, weights, N_FREE, BUDGET)
    reference = enumerated_optimum(instance)

    began = perf_counter()
    selected, solver = solve_scip(instance, time_limit=time_limit)
    elapsed = perf_counter() - began
    if solver["status"] != "optimal" or not solver["feasible"]:
        raise RuntimeError("SCIP did not certify an optimal feasible solution")
    chosen = np.flatnonzero(selected).tolist()
    if chosen not in reference["optimal_local_index_sets"]:
        raise AssertionError("SCIP selection differs from independent exhaustive optimum")
    if abs(float(solver["energy"]) - reference["minimum_energy"]) > 1e-7:
        raise AssertionError("SCIP energy differs from independent enumeration")

    positions = instance.free_indices.tolist()
    fixed = instance.fixed_indices.tolist()
    config = {
        "schema_version": 1,
        "experiment": "water_quality_n20_scip_cold_build",
        "scenario": scenario,
        "scenario_note": SCENARIO_NOTES[scenario],
        "n_free": N_FREE,
        "budget_new_stations": BUDGET,
        "beta": 1.0,
        "delta": 1.0,
        "weights": {name: float(w) for name, w in zip(FACTOR_NAMES, weights)},
        "model_parameters": {
            "L_c_m": L_C, "L_w_m": L_W, "current_vector": list(CURRENT_VECTOR),
            "D_max_buffer": D_MAX_BUFFER, "pool_size": POOL_SIZE, "hull_ratio": HULL_RATIO,
        },
        "sources": {
            "geojson": str(GEOJSON.relative_to(REPO_ROOT)),
            "geojson_sha256": sha256_bytes(GEOJSON.read_bytes()),
            "notebook": str(NOTEBOOK.relative_to(REPO_ROOT)),
            "notebook_sha256": sha256_bytes(NOTEBOOK.read_bytes()),
        },
    }
    config_hash = sha256_bytes(canonical_bytes(config))

    instance_json = {
        "schema_version": 1,
        "config_sha256": config_hash,
        "coordinates_crs": "EPSG:32651",
        "num_geojson_features": len(data.ids),
        "num_marked_existing": int(data.existing.sum()),
        "fixed_was_simulated": bool(simulated),
        "n_fixed_used": len(fixed),
        "D_max_m": float(instance.d_max),
        "free_master_feature_positions": positions,
        "free_geojson_property_ids": data.ids[instance.free_indices].tolist(),
        "fixed_master_feature_positions": fixed,
        "fixed_geojson_property_ids": data.ids[instance.fixed_indices].tolist(),
        "coords_easting_northing_m": instance.coords.tolist(),
        "utility_free_then_fixed": instance.utility.tolist(),
        "linear_coefficients": instance.linear.tolist(),
        "quadratic_terms_local_i_j_value": [[i, j, float(v)] for i, j, v in instance.quadratic],
        "free_neighbors_local_positions": [list(x) for x in instance.neighbors],
        "has_fixed_neighbor": instance.fixed_neighbors.astype(int).tolist(),
    }
    instance_hash = sha256_bytes(canonical_bytes(instance_json))
    linear_energy = float(sum(instance.linear[i] for i in chosen))
    pair_energy = float(sum(q for i, j, q in instance.quadratic if i in chosen and j in chosen))
    checked = evaluate(instance, selected)
    if not (checked["feasible"] and checked["budget_ok"] and checked["connectivity_ok"]):
        raise AssertionError("Independent model feasibility check failed")
    if abs(linear_energy + pair_energy - solver["energy"]) > 1e-9:
        raise AssertionError("Objective component sum does not match solver energy")
    if len(chosen) != BUDGET:
        raise AssertionError("Solver selection violates fixed budget")

    result = {
        "schema_version": 1,
        "scenario": scenario,
        "config_sha256": config_hash,
        "instance_sha256": instance_hash,
        "status": solver["status"],
        "proven_optimal": bool(solver["optimal"]),
        "solver_gap": float(solver["gap"]),
        "solver_time_limit_s": float(time_limit),
        "solver_wall_time_s": float(elapsed),
        "solver_energy": float(solver["energy"]),
        "objective_components": {"linear": linear_energy, "quadratic_free_free": pair_energy},
        "feasibility": {
            "feasible": bool(checked["feasible"]),
            "budget_ok": bool(checked["budget_ok"]),
            "local_connectivity_ok": bool(checked["connectivity_ok"]),
            "selected_count": int(checked["num_selected"]),
        },
        "selected_local_candidate_positions": chosen,
        "selected_geojson_master_feature_positions": [positions[i] for i in chosen],
        "selected_geojson_property_ids": [int(data.ids[positions[i]]) for i in chosen],
        "independent_enumeration": reference,
        "paper_comparison_reference_only": {
            "historical_paper_scip_energy": PAPER_REPORTED_SCIP_ENERGY,
            "historical_paper_selected_local_positions": list(PAPER_REPORTED_LOCAL_INDICES),
            "difference_from_paper_not_a_parity_test": (
                float(solver["energy"]) - PAPER_REPORTED_SCIP_ENERGY
            ),
            "historical_input_equivalence_verified": False,
        },
        "runtime_provenance": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": __import__("scipy").__version__,
            "shapely": __import__("shapely").__version__,
            "pyscipopt": __import__("pyscipopt").__version__,
            "github_source_sha": os.environ.get("GITHUB_HEAD_SHA")
                                 or os.environ.get("GITHUB_SHA"),
        },
    }
    site_rows = [
        {
            "local_candidate_position": pos,
            "master_feature_position": positions[pos],
            "geojson_property_id": int(data.ids[positions[pos]]),
            "selected": int(selected[pos]),
            "easting_m_epsg32651": float(instance.coords[pos, 0]),
            "northing_m_epsg32651": float(instance.coords[pos, 1]),
            "utility": float(instance.utility[pos]),
            "linear_coefficient": float(instance.linear[pos]),
            "has_fixed_neighbor": int(instance.fixed_neighbors[pos]),
            "free_neighbor_count": len(instance.neighbors[pos]),
        }
        for pos in range(N_FREE)
    ]
    return config, {"instance": instance_json, "result": result}, site_rows


def write_bundle(output_dir: Path, scenarios: tuple[str, ...], time_limit: float) -> dict:
    """Write self-contained, reviewable files. Never modify tracked inputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    summary = []
    for scenario in scenarios:
        config, artifacts, rows = run_scenario(scenario, time_limit=time_limit)
        dest = output_dir / scenario
        dest.mkdir(parents=True, exist_ok=True)
        for file_name, payload in (
            ("config.json", config), ("instance.json", artifacts["instance"]),
            ("result.json", artifacts["result"]),
        ):
            target = dest / file_name
            target.write_bytes(canonical_bytes(payload))
            files[str(target.relative_to(output_dir))] = sha256_bytes(target.read_bytes())
        target = dest / "sites.csv"
        with target.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        files[str(target.relative_to(output_dir))] = sha256_bytes(target.read_bytes())
        value = artifacts["result"]
        summary.append({
            "scenario": scenario,
            "energy": value["solver_energy"],
            "proven_optimal": value["proven_optimal"],
            "selected_local_positions": value["selected_local_candidate_positions"],
            "config_sha256": value["config_sha256"],
            "instance_sha256": value["instance_sha256"],
        })
        print("N20_EVIDENCE " + json.dumps(summary[-1], sort_keys=True))
    manifest = {
        "schema_version": 1,
        "purpose": "Research evidence from notebook-derived pilot, not a reproduction of the paper",
        "scenarios": summary,
        "file_sha256": files,
    }
    (output_dir / "manifest.json").write_bytes(canonical_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scenario", choices=(*SCENARIO_NOTES, "all"), default="all")
    parser.add_argument("--time-limit", type=float, default=120.)
    args = parser.parse_args()
    scenarios = tuple(SCENARIO_NOTES) if args.scenario == "all" else (args.scenario,)
    write_bundle(args.output_dir, scenarios, args.time_limit)


if __name__ == "__main__":
    main()
