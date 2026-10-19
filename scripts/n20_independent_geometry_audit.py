"""Independent GeoJSON-to-one-hop adjacency certificate for scoped lake N20/K5.

No notebook imports, no SciPy KD-tree, no SCIP, no cached MODEL_INPUT graph as
the source of adjacency. Uses source-pinned feature positions and Shapely's
same explicit concave-hull policy, with stdlib math.hypot for pair lengths.
The same GEOS geometry engine is a documented independence limitation.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path

from shapely import concave_hull
from shapely.geometry import LineString, MultiPoint, Point

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
EXPECTED_DATA_SHA = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
EXPECTED_FREE = [
    5253, 2394, 1894, 1557, 3225, 4623, 47, 5409, 3922, 2408,
    2694, 4136, 2567, 1164, 4973, 4537, 2726, 968, 16, 1762,
]
EXPECTED_FIXED = [
    417, 454, 725, 1055, 1076, 1709, 2771, 3402, 3520, 3529,
    3732, 3886, 4613, 4868, 5038,
]
EXPECTED_FEASIBLE = 1077
HULL_RATIO = 0.05
FIXED_SPACING_BUFFER = 1.15
N_FREE = 20
K_NEW = 5
GEOMETRIC_THRESHOLD_AMBIGUITY_M = 1e-7


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_coordinates(path: Path = SOURCE) -> tuple[list[tuple[float, float]], list[int]]:
    raw = path.read_bytes()
    if sha256_bytes(raw) != EXPECTED_DATA_SHA:
        raise AssertionError("Independent geometry source SHA-256 differs from archived GeoJSON")
    parsed = json.loads(raw)
    features = parsed["features"]
    if len(features) != 5417:
        raise AssertionError("Unexpected original water-quality source feature count")
    coords: list[tuple[float, float]] = []
    fixed: list[int] = []
    for idx, feature in enumerate(features):
        if feature["geometry"]["type"] != "Point":
            raise AssertionError("Archived lake source coordinate geometry is not Point")
        xy = feature["geometry"]["coordinates"]
        if len(xy) < 2:
            raise AssertionError("Missing projected easting/northing")
        p = (float(xy[0]), float(xy[1]))
        if not all(math.isfinite(c) for c in p):
            raise AssertionError("Nonfinite original projected coordinate")
        coords.append(p)
        if bool(feature["properties"].get("has_existing_station", False)):
            fixed.append(idx)
    if fixed != EXPECTED_FIXED:
        raise AssertionError("Actual GeoJSON marked existing station identities have changed")
    if any(i >= len(coords) or i in fixed for i in EXPECTED_FREE):
        raise AssertionError("Known free-site feature positions are not valid free sites")
    return coords, fixed


def original_fixed_spacing(fixed_coordinates: list[tuple[float, float]]) -> float:
    if len(fixed_coordinates) < 2:
        raise ValueError("At least two fixed stations required to infer original Dmax")
    largest_nearest = max(
        min(math.hypot(a[0] - b[0], a[1] - b[1])
            for j, b in enumerate(fixed_coordinates) if i != j)
        for i, a in enumerate(fixed_coordinates)
    )
    return largest_nearest * FIXED_SPACING_BUFFER


def reconstruct(
    site_positions: list[tuple[float, float]],
    hull,
    threshold_m: float,
    n_free: int,
) -> dict:
    """All free/free and free/fixed edges from actual polygon segment predicates.

    Unlike the notebook's combinations(35,2), visit each free site and each
    higher-index peer. This avoids fixed/fixed pairs and does not import any
    notebook adjacency arrays. The polygon and threshold come from GeoJSON.
    """
    if not 0 < n_free < len(site_positions):
        raise ValueError("Nfree must be positive with at least one existing station")
    if not math.isfinite(threshold_m) or threshold_m <= 0:
        raise ValueError("Adjacency threshold must be positive finite metres")
    if any(len(p) != 2 or not all(math.isfinite(v) for v in p)
           for p in site_positions):
        raise ValueError("Invalid projected site position")
    free_neighbors = [set() for _ in range(n_free)]
    fixed_links = [set() for _ in range(n_free)]
    total_pairs = 0
    interior_pairs = 0
    near_distance_min = math.inf
    boundary_near_pairs = []
    within_threshold = 0
    for i in range(n_free):
        p = site_positions[i]
        for j in range(i + 1, len(site_positions)):
            total_pairs += 1
            q = site_positions[j]
            if not (hull.contains(Point(p)) and hull.contains(Point(q))):
                continue
            if not hull.contains(LineString((p, q))):
                continue
            interior_pairs += 1
            distance = math.hypot(q[0] - p[0], q[1] - p[1])
            if distance == 0:
                continue
            margin = abs(distance - threshold_m)
            near_distance_min = min(near_distance_min, margin)
            if margin <= GEOMETRIC_THRESHOLD_AMBIGUITY_M:
                boundary_near_pairs.append([i, j, distance.hex()])
            if distance <= threshold_m:
                within_threshold += 1
                if j < n_free:
                    free_neighbors[i].add(j)
                    free_neighbors[j].add(i)
                else:
                    fixed_links[i].add(j - n_free)
    return {
        "free_neighbor_indices": [sorted(n) for n in free_neighbors],
        "fixed_neighbor_flags": [int(bool(s)) for s in fixed_links],
        "free_fixed_links": [sorted(s) for s in fixed_links],
        "distance_threshold_m_hex": threshold_m.hex(),
        "distance_to_nearest_threshold_m_hex": (
            near_distance_min.hex() if math.isfinite(near_distance_min) else None
        ),
        "near_threshold_pairs_1e_minus_7_m": boundary_near_pairs,
        "considered_pairs": total_pairs,
        "hull_interior_pairs": interior_pairs,
        "distance_eligible_edges": within_threshold,
        "free_free_undirected_edges": sum(len(n) for n in free_neighbors) // 2,
        "free_fixed_raw_edges": sum(len(s) for s in fixed_links),
    }


def feasible_subsets(neighbors: list[list[int]], fixed: list[int],
                     k: int = K_NEW) -> tuple[int, str]:
    n = len(fixed)
    if len(neighbors) != n:
        raise AssertionError("One-hop graph shape mismatch")
    h = hashlib.sha256()
    count = 0
    for ids in combinations(range(n), k):
        chosen = set(ids)
        if all(fixed[i] or any(j in chosen for j in neighbors[i]) for i in ids):
            count += 1
            h.update((",".join(map(str, ids)) + "\n").encode("ascii"))
    return count, h.hexdigest()


def certify_geometry(record: dict, source: Path = SOURCE) -> dict:
    """Compare original GeoJSON-derived geometry with independently emitted N20."""
    features_xy, fixed_ids = source_coordinates(source)
    model = record["model_input"]
    if (model["dataset_sha256"] != EXPECTED_DATA_SHA
            or record["dataset_sha256"] != EXPECTED_DATA_SHA):
        raise AssertionError("Original GeoJSON SHA not pinned in model and result")
    if model["candidate_master_feature_positions"] != EXPECTED_FREE:
        raise AssertionError("Source-derived N20 candidate IDs changed")
    if model["fixed_master_feature_positions"] != fixed_ids:
        raise AssertionError("Reported fixed station identities differ from real GeoJSON flags")
    selected_ids = EXPECTED_FREE + fixed_ids
    actual_xy = [features_xy[i] for i in selected_ids]
    declared_hex = model["site_coords_epsg32651_float64_hex"]
    original_hex = [[p[0].hex(), p[1].hex()] for p in actual_xy]
    if declared_hex != original_hex:
        raise AssertionError("Reported projected site coordinates differ from raw GeoJSON")
    if (float.fromhex(model["hull_ratio_float64_hex"]) != HULL_RATIO
            or float.fromhex(model["fixed_spacing_buffer_float64_hex"])
            != FIXED_SPACING_BUFFER):
        raise AssertionError("Scientific spatial hull or spacing parameter changed")
    calculated_dmax = original_fixed_spacing(
        [features_xy[i] for i in fixed_ids]
    )
    declared_dmax = float.fromhex(model["d_max_m_float64_hex"])
    if not math.isclose(calculated_dmax, declared_dmax, rel_tol=0,
                        abs_tol=GEOMETRIC_THRESHOLD_AMBIGUITY_M):
        raise AssertionError("Original fixed station spacing and Dmax inconsistent")

    water_hull = concave_hull(MultiPoint(features_xy),
                              ratio=HULL_RATIO, allow_holes=True)
    if water_hull.is_empty or not water_hull.is_valid:
        raise AssertionError("Original lake concave hull is invalid")
    independent = reconstruct(actual_xy, water_hull, calculated_dmax, N_FREE)
    if independent["near_threshold_pairs_1e_minus_7_m"]:
        raise AssertionError("Ambiguous distance threshold edge; review float64/GEOS")
    if independent["free_neighbor_indices"] != model["free_neighbor_indices"]:
        raise AssertionError("Free/free one-hop adjacency differs from original GeoJSON geometry")
    if independent["fixed_neighbor_flags"] != model["fixed_neighbor_flags"]:
        raise AssertionError("Free/fixed one-hop flags differ from original GeoJSON geometry")
    verified_count, verified_sha = feasible_subsets(
        independent["free_neighbor_indices"],
        independent["fixed_neighbor_flags"],
    )
    if (verified_count != EXPECTED_FEASIBLE
            or verified_count != record.get("feasible_combinations")):
        raise AssertionError("Original geometry does not reproduce 1077 feasible K5 subsets")
    if verified_sha != record.get("feasible_site_sets_sha256"):
        raise AssertionError("Original geometry feasible-set membership SHA-256 differs")

    graph_evidence = {
        "candidate_master_feature_positions": EXPECTED_FREE,
        "existing_station_master_feature_positions": fixed_ids,
        "free_neighbor_indices_from_geojson": independent["free_neighbor_indices"],
        "fixed_neighbor_flags_from_geojson": independent["fixed_neighbor_flags"],
        "free_fixed_links_local_existing_positions": independent["free_fixed_links"],
        "distance_threshold_m_from_geojson_hex": calculated_dmax.hex(),
        "distance_threshold_reported_hex": declared_dmax.hex(),
        "nearest_distance_threshold_margin_m_hex":
            independent["distance_to_nearest_threshold_m_hex"],
        "tested_pairs": independent["considered_pairs"],
        "interior_pairs": independent["hull_interior_pairs"],
        "distance_eligible_edges": independent["distance_eligible_edges"],
        "free_free_edges": independent["free_free_undirected_edges"],
        "free_fixed_edges": independent["free_fixed_raw_edges"],
        "feasible_combinations": verified_count,
        "feasible_site_sets_sha256": verified_sha,
    }
    graph_bytes = (json.dumps(graph_evidence, sort_keys=True,
                              separators=(",", ":"), allow_nan=False) + "\n").encode()
    return {
        "schema_version": 1,
        "scope": "N20/K5 independent raw-GeoJSON-derived local one-hop spatial audit",
        "source_data_sha256": EXPECTED_DATA_SHA,
        "model_input_sha256": record["model_input_sha256"],
        "spatial_graph_sha256": sha256_bytes(graph_bytes),
        "spatial_graph": graph_evidence,
        "limitation": (
            "Independent calculation from pinned GeoJSON, without notebook's "
            "adjacency arrays; it uses the SAME Shapely/GEOS concave-hull "
            "definition and does NOT independently certify historical manuscript "
            "inputs, full network connectivity, larger N or quantum sampling."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result", type=Path, required=True,
                   help="Fresh-kernel validated N20 result JSON from PR #66")
    p.add_argument("--output", type=Path, required=True)
    opts = p.parse_args()
    record = json.loads(opts.result.read_text(encoding="utf-8"))
    audit = certify_geometry(record)
    if opts.output.exists():
        raise FileExistsError("Refusing to overwrite source geometry evidence")
    opts.output.parent.mkdir(parents=True, exist_ok=True)
    opts.output.write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("N20_GEOJSON_GEOMETRY_CERTIFICATE " + json.dumps({
        "free_free_edges": audit["spatial_graph"]["free_free_edges"],
        "free_fixed_edges": audit["spatial_graph"]["free_fixed_edges"],
        "feasible_combinations": audit["spatial_graph"]["feasible_combinations"],
        "feasible_sha256": audit["spatial_graph"]["feasible_site_sets_sha256"],
        "geometry_sha256": audit["spatial_graph_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
