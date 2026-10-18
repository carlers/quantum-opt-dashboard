"""Notebook-derived one-hop water-quality model: strict replaceable GeoJSON adapter.

Preserves mathematical semantics of validated notebook reference model without
requiring an existing shelter schema or changing historical input datasets.
All indices refer to ordered GeoJSON feature positions, never a geographic ID.
"""
from __future__ import annotations

from itertools import combinations
from math import comb, isfinite
from pathlib import Path
import sys

import numpy as np

from notebook_reference_model import (
    FACTOR_NAMES, NOTEBOOK_WEIGHTS, PAPER_WEIGHTS, evaluate,
    load_data, make_instance, solve_scip,
)

PINNED_N20_OPTIMUM = -3.3012934918564643


def _typed_positive(value: object, label: str, *, allow_zero: bool) -> float:
    if type(value) not in (int, float) or not isfinite(value) or value < 0 or (not allow_zero and value == 0):
        raise ValueError(f"{label} must be finite {'nonnegative' if allow_zero else 'positive'}")
    return float(value)


def _validate_geojson(bundle) -> None:
    features = bundle.data.get("features")
    if bundle.data.get("type") != "FeatureCollection" or type(features) is not list:
        raise ValueError("Water input must be a GeoJSON FeatureCollection")
    if not 10 <= len(features) <= 20000:
        raise ValueError("Water GeoJSON requires between 10 and 20,000 sites")
    if bundle.source_manifest["classification"] == "SYNTHETIC":
        crs = bundle.data.get("crs")
        if crs != {"type": "name", "properties": {"name": "EPSG:32651"}}:
            raise ValueError("Synthetic projected water sites must declare CRS EPSG:32651")
    # The historical source is pinned by SHA; do not silently change its source
    # CRS or feature order. Its numeric Easting/Northing are notebook-assumed.
    seen: set[int] = set()
    for index, feature in enumerate(features):
        if type(feature) is not dict or type(feature.get("geometry")) is not dict:
            raise ValueError(f"Feature {index} missing geometry")
        coords = feature["geometry"].get("coordinates")
        if (feature["geometry"].get("type") != "Point" or
            type(coords) is not list or len(coords) < 2 or
            any(type(v) not in (int, float) or not isfinite(v) for v in coords[:2])):
            raise ValueError(f"Feature {index} must be a projected finite Point")
        props = feature.get("properties")
        if type(props) is not dict or "id" not in props or type(props["id"]) is not int:
            raise ValueError(f"Feature {index} needs a stable integer property id")
        if props["id"] in seen:
            raise ValueError("Duplicate geographic feature id")
        seen.add(props["id"])
        if type(props.get("has_existing_station", False)) is not bool:
            raise ValueError("Existing-station indicators must be explicit boolean")
        for factor in FACTOR_NAMES:
            value = props.get(factor)
            if value is not None and (type(value) not in (int, float) or not isfinite(value)):
                raise ValueError(f"Criterion {factor} must be finite numeric or null")
    if bundle.source_manifest["classification"] == "SYNTHETIC" and not any(
        f["properties"].get("has_existing_station") for f in features
    ):
        raise ValueError("Synthetic water inputs need explicit fixed stations; never auto-label simulated sites as actual")


def _parameters(parameters: dict) -> dict:
    allowed = {"n_free", "budget", "beta", "delta", "time_limit", "weights"}
    if type(parameters) is not dict or set(parameters) - allowed:
        raise ValueError("Unsupported water-quality configuration parameter")
    if any(key not in parameters for key in ("n_free", "budget")):
        raise ValueError("n_free and budget are required to define a water problem")
    n = parameters["n_free"]
    k = parameters["budget"]
    if type(n) is not int or not 1 <= n <= 50:
        raise ValueError("n_free must be an integer in 1..50 for this pilot")
    if type(k) is not int or not 0 <= k <= n:
        raise ValueError("budget must be an integer between zero and n_free")
    beta = _typed_positive(parameters.get("beta", 1), "beta", allow_zero=True)
    delta = _typed_positive(parameters.get("delta", 1), "delta", allow_zero=True)
    time_limit = _typed_positive(parameters.get("time_limit", 30), "time_limit", allow_zero=False)
    if time_limit > 120:
        raise ValueError("Prototype SCIP time limit must not exceed 120 seconds")
    raw = parameters.get("weights", NOTEBOOK_WEIGHTS.tolist())
    if type(raw) is not list or len(raw) != 8 or any(
        type(x) not in (int, float) or not isfinite(x) or x < 0 for x in raw
    ) or sum(raw) <= 0:
        raise ValueError("Eight finite nonnegative criterion weights with positive sum required")
    return {"n_free": n, "budget": k, "beta": beta, "delta": delta,
            "time_limit": time_limit, "weights": np.asarray(raw, dtype=float)}


def _exact_reference(instance, *, cap: int = 200000) -> dict:
    n, k = len(instance.free_indices), instance.budget
    tries = comb(n, k)
    if tries > cap:
        return {"status": "not_enumerated", "reason": "combinatorial budget limit",
                "combinations": tries}
    best = float("inf")
    choices = []
    for group in combinations(range(n), k):
        x = np.zeros(n, dtype=int)
        x[list(group)] = 1
        # independent from model.evaluate (direct original budget/adjacency
        # and coefficient arithmetic) to catch accidental solver fidelity loss
        if any(not (instance.fixed_neighbors[i] or any(x[j] for j in instance.neighbors[i]))
               for i in group):
            continue
        objective = sum(float(instance.linear[i]) for i in group) + sum(
            float(q) for i, j, q in instance.quadratic if x[i] and x[j]
        )
        if objective < best - 1e-8:
            best, choices = objective, [list(group)]
        elif abs(objective - best) <= 1e-8:
            choices.append(list(group))
    if not choices:
        return {"status": "infeasible", "combinations": tries}
    return {"status": "optimal_by_enumeration",
            "combinations": tries, "optimum": float(best),
            "optimal_local_sets": choices}


def run_water_bundle(bundle, output_dir: Path) -> dict:
    if bundle.formulation_id != "notebook_one_hop_milp":
        raise ValueError("Unsupported water-quality formulation; never silently substitute")
    if bundle.source_format != ".geojson":
        raise ValueError("Water-quality reference requires ordered projected GeoJSON")
    _validate_geojson(bundle)
    p = _parameters(bundle.parameters)
    loaded = load_data(bundle.dataset_path)
    instance, simulated = make_instance(
        loaded, p["weights"], p["n_free"], p["budget"],
        beta=p["beta"], delta=p["delta"]
    )
    if simulated:
        raise ValueError("No real existing fixed stations were supplied; the source model would simulate sites")
    solution, metrics = solve_scip(
        instance, time_limit=p["time_limit"],
        export_lp_path=output_dir / "actual-water-scip-milp.lp"
    )
    independent = _exact_reference(instance)
    if independent["status"] == "optimal_by_enumeration":
        if metrics["status"] != "optimal" or abs(
            metrics["energy"] - independent["optimum"]
        ) > 1e-7:
            raise AssertionError("Water SCIP differs from independent original binary subset enumeration")
    settings_match_frozen = (
        bundle.source_manifest["classification"] == "RESEARCH_REFERENCE"
        and p["n_free"] == 20 and p["budget"] == 5
        and p["beta"] == 1.0 and p["delta"] == 1.0
        and np.array_equal(p["weights"], NOTEBOOK_WEIGHTS)
    )
    if settings_match_frozen:
        if len(loaded.coords) != 5417 or len(instance.fixed_indices) != 15:
            raise AssertionError("Immutable N20 water source site provenance changed")
        if (list(instance.free_indices[:8]) !=
            [5253, 2394, 1894, 1557, 3225, 4623, 47, 5409]):
            raise AssertionError("N20 source candidate mapping changed")
        if metrics["status"] != "optimal" or abs(metrics["energy"] - PINNED_N20_OPTIMUM) > 1e-7:
            raise AssertionError("Notebook-derived pinned N20 objective changed")
        if np.flatnonzero(solution).tolist() != [0, 1, 3, 6, 7]:
            raise AssertionError("Pinned N20 selected local sites changed")
    return {
        "formulation": "notebook_derived_binary_quadratic_with_budget_equality_and_local_one_hop",
        "solver": "exact binary pair-product SCIP MILP, NOT direct QUBO or quantum hardware",
        "historical_source_scenario": bool(settings_match_frozen),
        "manuscript_parity": "UNRESOLVED: AHP Table III/IV, D2 semantics and paper objective differ (#16)",
        "one_hop_is_not_global_network_connectivity": True,
        "dataset_point_count": len(loaded.coords),
        "dataset_crs_assumed": "EPSG:32651 projected meters",
        "weight_order": list(FACTOR_NAMES),
        "resolved_weights": p["weights"].tolist(),
        "n_free": len(instance.free_indices),
        "budget_exactly": int(instance.budget),
        "free_master_feature_positions": instance.free_indices.astype(int).tolist(),
        "fixed_master_feature_positions": instance.fixed_indices.astype(int).tolist(),
        "objective_linear_hex": [float(v).hex() for v in instance.linear],
        "objective_quadratic_hex": [
            {"i": int(i), "j": int(j), "q_hex": float(q).hex()}
            for i, j, q in instance.quadratic
        ],
        "one_hop_free_neighbors": [list(group) for group in instance.neighbors],
        "fixed_neighbor_indicators": instance.fixed_neighbors.astype(int).tolist(),
        "selected_local_positions": np.flatnonzero(solution).astype(int).tolist(),
        "selected_master_positions": instance.free_indices[solution.astype(bool)].astype(int).tolist(),
        "original_objective": float(metrics["energy"]),
        "original_feasible": bool(metrics["feasible"]),
        "scip_status": metrics["status"],
        "independent_enumeration": independent,
        "notes": "Historical model is from pinned separate research PR; never reinterpret selected feature positions as external property IDs.",
    }
