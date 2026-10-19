"""Pre-registered G0/G1 source N20 candidate-generator sensitivity.

PR #79 protocol predates any experiment; this file never edits source data or
the old notebook. G1 filters original snapped pool by direct *modeled* original
fixed wireless link BEFORE unchanged original farthest-first selection.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.spatial import cKDTree
import shapely
from shapely import concave_hull
from shapely.geometry import MultiPoint, Point, LineString

from scripts.n20_independent_geometry_audit import (
    EXPECTED_DATA_SHA, EXPECTED_FIXED, EXPECTED_FREE,
    EXPECTED_FEASIBLE, EXPECTED_DATA_SHA as ORIGINAL_DATA_SHA,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
ARCHIVE = ROOT / "problems/water_quality/notebooks/experiment9 grid search copy.ipynb"
ORIGINAL_NOTEBOOK_SHA = "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"
FACTOR_NAMES = (
    "a1_river_proximity", "a2_runoff_proximity", "b1_fishpen_density",
    "b2_hypoxic_proximity", "c1_bathymetric_depressions",
    "c2_outlet_proximity", "d1_boatramp_proximity", "d2_road_proximity",
)
WEIGHTS = np.array([.3671, .1224, .2508, .0502, .1278, .0183, .0476, .0159])
N_FREE, K_NEW, POOL_SIZE = 20, 5, 10000
HULL_RATIO, D_MAX_BUFFER = .05, 1.15
L_C, L_W, BETA, DELTA = 7500.0, 1000.0, 1.0, 1.0
EXPECTED_G0_ZERO = [2, 4, 5, 8, 11, 16, 18]
EXPECTED_G0_SHA = "2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a"
EXPECTED_G0_BEST = (0, 1, 3, 6, 7)
EXPECTED_G0_ENERGY = -3.3012934918564643


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def load_source():
    if sha_bytes(DATA.read_bytes()) != EXPECTED_DATA_SHA:
        raise ValueError("Committed source original GeoJSON checksum mismatch")
    if sha_bytes(ARCHIVE.read_bytes()) != ORIGINAL_NOTEBOOK_SHA:
        raise ValueError("Original archived 25-code-cell source changed")
    features = json.loads(DATA.read_text(encoding="utf-8"))["features"]
    if len(features) != 5417:
        raise ValueError("Original expected source has 5417 features")
    xy = np.asarray([f["geometry"]["coordinates"][:2] for f in features], dtype=float)
    fact = np.asarray([
        [np.nan if f["properties"].get(name) is None
         else float(f["properties"][name]) for name in FACTOR_NAMES]
        for f in features
    ], dtype=float)
    fixed = np.flatnonzero([
        bool(f["properties"].get("has_existing_station", False)) for f in features
    ])
    if fixed.tolist() != EXPECTED_FIXED or not np.isfinite(xy).all():
        raise ValueError("Source original fixed identities or coordinates changed")
    valid = ~np.isnan(fact)
    weighted = np.nansum(fact * WEIGHTS, axis=1)
    denom = np.nansum(valid * WEIGHTS, axis=1)
    util = np.clip(weighted / np.where(denom == 0, 1, denom), 0, 1)
    if not np.isfinite(util).all():
        raise ValueError("Source factor-utility calculation invalid")
    return xy, fact, fixed, util


def hex_snapped_pool(coords, fixed, hull):
    """Match source notebook exactly (row-major hex -> KDTree -> np.unique)."""
    xmin, ymin = np.min(coords, axis=0)
    xmax, ymax = np.max(coords, axis=0)
    dx = float(np.sqrt((xmax - xmin) * (ymax - ymin) / POOL_SIZE / (np.sqrt(3) / 2)))
    dy = dx * np.sqrt(3) / 2
    hexa = [
        (xmin + col * dx + (dx / 2 if row % 2 else 0), ymin + row * dy)
        for row in range(int(np.ceil((ymax - ymin) / dy)) + 1)
        for col in range(int(np.ceil((xmax - xmin) / dx)) + 1)
        if ymin + row * dy <= ymax
        and xmin + col * dx + (dx / 2 if row % 2 else 0) <= xmax
    ]
    water = np.asarray([point for point in hexa if hull.contains(Point(point))],
                       dtype=float)
    if water.size == 0:
        raise ValueError("Original water hex pool is empty")
    snapped = cKDTree(coords).query(water, k=1)[1]
    free_pool = np.unique(snapped[~np.isin(snapped, fixed)])
    if len(free_pool) < N_FREE:
        raise ValueError("Original snapped unique pool insufficient")
    return free_pool, len(hexa), len(water)


def dmax_from_original(coords, fixed):
    nearest = cKDTree(coords[fixed]).query(coords[fixed], k=2)[0][:, 1]
    return float(np.max(nearest) * D_MAX_BUFFER)


def legal_link(p, q, hull, dmax):
    """Original source strict GEOS water polygon+line and Euclidean threshold."""
    # Check distance first only as exact short-circuit for impossible links;
    # boundary equality remains as in original notebook.
    if np.linalg.norm(np.asarray(q) - np.asarray(p)) > dmax:
        return False
    return (hull.contains(Point(p)) and hull.contains(Point(q))
            and hull.contains(LineString([p, q])))


def direct_fixed_filter(coords, candidates, fixed, hull, dmax):
    """G1 prefilter: one direct legal source-model fixed-station contact."""
    accepted = []
    fixed_points = coords[fixed]
    for idx in candidates:
        p = coords[idx]
        for q in fixed_points:
            if legal_link(p, q, hull, dmax):
                accepted.append(int(idx))
                break
    return np.asarray(accepted, dtype=int)


def farthest_first(coords, fixed, unique_pool, count=N_FREE):
    """Exactly original source seed (all fixed sites) + iterative FPS rule."""
    if len(unique_pool) < count:
        raise ValueError(f"Only {len(unique_pool)} qualifying sites; need {count}")
    if len(set(map(int, unique_pool))) != len(unique_pool):
        raise ValueError("Unique free snapped pool required")
    if not np.array_equal(unique_pool, np.sort(unique_pool)):
        raise ValueError("Original np.unique sorted source-order convention required")
    min_distance = cKDTree(coords[fixed]).query(coords[unique_pool], k=1)[0]
    selected = []
    for _ in range(count):
        position = int(np.argmax(min_distance))
        chosen_master = int(unique_pool[position])
        selected.append(chosen_master)
        min_distance = np.minimum(
            min_distance, np.linalg.norm(coords[unique_pool] - coords[chosen_master],
                                         axis=1)
        )
        min_distance[position] = -1.0
    return selected


def original_instance(coords, util, fixed, free, hull, dmax):
    """Replicate original scientific source code cell 12, no changed objective."""
    positions = np.vstack([coords[free], coords[fixed]])
    linear = -util[free].copy()
    quad = []
    neighbors = [set() for _ in range(N_FREE)]
    flags = np.zeros(N_FREE, dtype=int)
    for i, j in combinations(range(len(positions)), 2):
        p, q = positions[i], positions[j]
        if not (hull.contains(Point(p)) and hull.contains(Point(q))
                and hull.contains(LineString([p, q]))):
            continue
        diff = q - p
        dist = float(np.linalg.norm(diff))
        if dist == 0:
            continue
        if dist <= dmax:
            if i < N_FREE and j < N_FREE:
                neighbors[i].add(j)
                neighbors[j].add(i)
            elif i < N_FREE:
                flags[i] = 1
            elif j < N_FREE:
                flags[j] = 1
        if dist > 2 * L_C:
            continue
        redundancy = max(0.0, 1.0 - dist / L_C)
        cosine = float(np.clip(diff[0] / dist, -1.0, 1.0))
        wake_forward = np.exp(-dist / L_W) * cosine if cosine > 0.7071 else 0.0
        wake_backward = -np.exp(-dist / L_W) * cosine if -cosine > 0.7071 else 0.0
        coefficient = float(BETA * redundancy + DELTA * (wake_forward + wake_backward))
        if abs(coefficient) <= 1e-12:
            continue
        if i < N_FREE and j < N_FREE:
            quad.append((i, j, coefficient))
        elif i < N_FREE:
            linear[i] += coefficient
        elif j < N_FREE:
            linear[j] += coefficient
    return linear, quad, [sorted(row) for row in neighbors], flags.astype(int).tolist()


def check_reference(reference, free, linear, quad, neighbors, flags, dmax):
    model = reference.get("model_input", {})
    if (reference.get("dataset_sha256") != EXPECTED_DATA_SHA
            or reference.get("archived_notebook_sha256") != ORIGINAL_NOTEBOOK_SHA
            or reference.get("feasible_combinations") != EXPECTED_FEASIBLE
            or model.get("candidate_master_feature_positions") != EXPECTED_FREE
            or free != EXPECTED_FREE
            or model.get("fixed_master_feature_positions") != EXPECTED_FIXED):
        raise AssertionError("Source cold notebook G0 canary identities mismatch")
    blob_sha = sha_bytes(canonical(model))
    if blob_sha != reference.get("model_input_sha256"):
        raise AssertionError("Source original model input digest mismatch")
    if (model.get("free_neighbor_indices") != neighbors
            or model.get("fixed_neighbor_flags") != flags
            or abs(float.fromhex(model["d_max_m_float64_hex"]) - dmax) > 1e-7):
        raise AssertionError("Independently rebuilt original G0 graph/Dmax mismatch")
    ref_l = [float.fromhex(v) for v in model["linear_float64_hex"]]
    ref_q = [(int(i), int(j), float.fromhex(q))
             for i, j, q in model["quadratic_ij_float64_hex"]]
    if len(ref_l) != 20 or len(ref_q) != len(quad):
        raise AssertionError("Source original coefficient shape differs")
    if not np.allclose(linear, ref_l, rtol=0, atol=1e-7):
        raise AssertionError("Source G0 original coefficient parity differs")
    if any((i, j) != (a, b) or abs(q - x) > 1e-7
           for (i, j, q), (a, b, x) in zip(quad, ref_q)):
        raise AssertionError("Source G0 quadratic parity differs")


def enumerate_case(free, coords, util, fixed, hull, dmax):
    linear, quad, neighbors, flags = original_instance(
        coords, util, fixed, free, hull, dmax
    )
    if len(free) != N_FREE:
        raise AssertionError("Incorrect N")
    empty = [i for i in range(N_FREE) if not flags[i] and not neighbors[i]]
    feasible = 0
    dig = hashlib.sha256()
    best = math.inf
    winners = []
    for chosen in combinations(range(N_FREE), K_NEW):
        ids = set(chosen)
        if any(not flags[i] and not ids.intersection(neighbors[i]) for i in ids):
            continue
        feasible += 1
        dig.update((",".join(map(str, chosen)) + "\n").encode("ascii"))
        energy = float(sum(float(linear[i]) for i in chosen) +
                       sum(float(q) for i, j, q in quad if i in ids and j in ids))
        if energy < best - 1e-9:
            best, winners = energy, [chosen]
        elif abs(energy - best) <= 1e-9:
            winners.append(chosen)
    if not winners:
        raise AssertionError("Empty K5 feasible region; must report as unavailable")
    return {
        "candidate_master_feature_positions": list(map(int, free)),
        "linear_float64_hex": [float(v).hex() for v in linear],
        "quadratic_ij_float64_hex": [
            [int(i), int(j), float(q).hex()] for i, j, q in quad
        ],
        "quadratic_term_count": len(quad),
        "free_neighbors": neighbors,
        "fixed_flags": flags,
        "zero_neighbor_local_positions": empty,
        "feasible_K5_count": feasible,
        "feasible_K5_membership_sha256": dig.hexdigest(),
        "optima_local_positions": [list(ids) for ids in winners],
        "optima_master_positions": [
            [int(free[i]) for i in ids] for ids in winners
        ],
        "best_original_source_objective": best,
        "original_source_factor_utility_20": [
            float(util[i]) for i in free
        ],
    }


def distribution(vals):
    arr = np.asarray(vals, dtype=float)
    return {
        "min": float(np.min(arr)), "mean": float(np.mean(arr)),
        "median": float(np.median(arr)), "max": float(np.max(arr)),
    }


def coverage_stats(coords, fixed, chosen):
    monitors = np.concatenate([fixed, np.asarray(chosen, dtype=int)])
    distances = cKDTree(coords[monitors]).query(coords, k=1)[0]
    return distribution(distances)


def include_metrics(case, coords, util, fixed):
    free = case["candidate_master_feature_positions"]
    choice = case["optima_master_positions"][0]
    case["coverage_15_fixed_plus_20_candidate_all_5417_metres"] = coverage_stats(
        coords, fixed, free
    )
    case["coverage_15_fixed_plus_5_installed_all_5417_metres"] = coverage_stats(
        coords, fixed, choice
    )
    case["utility_20_candidate_distribution"] = distribution(util[free])
    case["utility_5_installed_distribution"] = distribution(util[choice])
    case["finite_original_eight_factor_counts"] = {
        "note": "Computed from committed source; site-specific utility is based on available weights"
    }
    case["nearest_original_fixed_distances_20_metres"] = [
        float(x) for x in cKDTree(coords[fixed]).query(coords[free], k=1)[0]
    ]


def analyze(reference: dict) -> dict:
    coords, factors, fixed, util = load_source()
    hull = concave_hull(MultiPoint(coords), ratio=HULL_RATIO, allow_holes=True)
    if hull.is_empty or not hull.is_valid:
        raise ValueError("Original source hull invalid")
    dmax = dmax_from_original(coords, fixed)
    snapped, raw_pool, water_pool = hex_snapped_pool(coords, fixed, hull)
    g0 = farthest_first(coords, fixed, snapped)
    g0case = enumerate_case(g0, coords, util, fixed, hull, dmax)
    linear, quad, neighbors, flags = original_instance(
        coords, util, fixed, g0, hull, dmax
    )
    check_reference(reference, g0, linear, quad, neighbors, flags, dmax)
    if (g0case["zero_neighbor_local_positions"] != EXPECTED_G0_ZERO
            or g0case["feasible_K5_count"] != EXPECTED_FEASIBLE
            or g0case["feasible_K5_membership_sha256"] != EXPECTED_G0_SHA
            or g0case["optima_local_positions"] != [list(EXPECTED_G0_BEST)]
            or abs(g0case["best_original_source_objective"] -
                   EXPECTED_G0_ENERGY) >= 1e-7):
        raise AssertionError("Source G0 exact canary feasible region/optimum differs")
    include_metrics(g0case, coords, util, fixed)

    eligible = direct_fixed_filter(coords, snapped, fixed, hull, dmax)
    if len(eligible) < N_FREE:
        raise RuntimeError(
            f"Preregistered G1 could only find {len(eligible)} eligible sites; "
            "do not tune Dmax to force 20")
    g1 = farthest_first(coords, fixed, eligible)
    g1case = enumerate_case(g1, coords, util, fixed, hull, dmax)
    include_metrics(g1case, coords, util, fixed)
    if not all(g1case["fixed_flags"]) or g1case["zero_neighbor_local_positions"]:
        raise AssertionError("G1 selected site without an independently legal direct fixed link")
    if (g1case["feasible_K5_count"] != 15504
            or g1case["feasible_K5_membership_sha256"] !=
            sha_bytes(b"".join(
                (",".join(map(str, ids)) + "\n").encode("ascii")
                for ids in combinations(range(20), 5)
            ))):
        raise AssertionError("G1 directly anchored site feasible universe mismatch")
    return {
        "schema_version": 1,
        "status": "preregistered_G0_historical_vs_G1_direct_fixed_counterfactual",
        "preregistration": (
            "docs/research_protocols/N20_G1_CANDIDATE_ELIGIBILITY_PREREG_2026_10_19.md"
        ),
        "original_source_data_sha256": EXPECTED_DATA_SHA,
        "archived_original_notebook_sha256": ORIGINAL_NOTEBOOK_SHA,
        "cold_source_n20_model_input_sha256": reference["model_input_sha256"],
        "original_15_fixed_master_ids": list(map(int, fixed)),
        "dmax_original_m_float64_hex": float(dmax).hex(),
        "hex_pool_raw_count": raw_pool,
        "hex_pool_inside_original_hull_count": water_pool,
        "unique_snapped_nonfixed_candidate_count": len(snapped),
        "G1_qualified_direct_fixed_pool_count": len(eligible),
        "G1_qualified_pool_master_position_sha256": sha_bytes(canonical(
            list(map(int, eligible))
        )),
        "G0": g0case, "G1": g1case,
        "observed_hypotheses": {
            "H0_same_20_master_candidates": g0 == g1,
            "H1_G1_fewer_unselectable_local_nodes": (
                len(g1case["zero_neighbor_local_positions"]) <
                len(g0case["zero_neighbor_local_positions"])
            ),
            "H2_G1_more_local_feasible_K5": (
                g1case["feasible_K5_count"] > g0case["feasible_K5_count"]
            ),
            "H3_G1_higher_max_nearest_distance_15_fixed_plus_20_generated": (
                g1case["coverage_15_fixed_plus_20_candidate_all_5417_metres"]["max"] >
                g0case["coverage_15_fixed_plus_20_candidate_all_5417_metres"]["max"]
            ),
            "H4_optimizing_five_master_locations_changed": (
                g0case["optima_master_positions"] != g1case["optima_master_positions"]
            ),
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "shapely": shapely.__version__,
        },
        "warnings": [
            "G1 direct fixed edge only, stricter than source one-hop relay alternatives",
            "Source lake hull, not a verified real shoreline/radio/Fresnel survey",
            "Coverage of 20 GENERATED candidates is not coverage of five INSTALLED sensors",
            "Objective coefficients differ because the candidate universe differs",
            "Published AHP/WorldPop/MIQP provenance remains unresolved; no source rewrite",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    opts = parser.parse_args()
    if opts.output.exists():
        raise FileExistsError("Will not overwrite a previous preregistered run")
    record = json.loads(opts.reference.read_text(encoding="utf-8"))
    result = analyze(record)
    opts.output.parent.mkdir(parents=True, exist_ok=True)
    opts.output.write_bytes(canonical(result))
    print("N20_G1_SOURCE_CANDIDATE_STUDY " + json.dumps({
        "eligible_unique_source_pool": result["G1_qualified_direct_fixed_pool_count"],
        "G0_master_ids": result["G0"]["candidate_master_feature_positions"],
        "G1_master_ids": result["G1"]["candidate_master_feature_positions"],
        "G0_unselectable": result["G0"]["zero_neighbor_local_positions"],
        "G1_unselectable": result["G1"]["zero_neighbor_local_positions"],
        "G0_K5_feasible": result["G0"]["feasible_K5_count"],
        "G1_K5_feasible": result["G1"]["feasible_K5_count"],
        "G0_optimal_master": result["G0"]["optima_master_positions"],
        "G1_optimal_master": result["G1"]["optima_master_positions"],
        "G0_best_energy": result["G0"]["best_original_source_objective"],
        "G1_best_energy": result["G1"]["best_original_source_objective"],
        "G0_candidate_cover_mean_m": result["G0"][
            "coverage_15_fixed_plus_20_candidate_all_5417_metres"
        ]["mean"],
        "G1_candidate_cover_mean_m": result["G1"][
            "coverage_15_fixed_plus_20_candidate_all_5417_metres"
        ]["mean"],
        "G0_candidate_cover_max_m": result["G0"][
            "coverage_15_fixed_plus_20_candidate_all_5417_metres"
        ]["max"],
        "G1_candidate_cover_max_m": result["G1"][
            "coverage_15_fixed_plus_20_candidate_all_5417_metres"
        ]["max"],
        "hypotheses": result["observed_hypotheses"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
