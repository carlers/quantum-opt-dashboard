"""Independent source-only 35-node all-stations geometric graph certificate.

Rebuilds all free/free, free/fixed and NEW fixed/fixed modeled edges from
pinned raw GeoJSON. Independently counts all 20-choose-K fully connected
subsets with union-find, and cross-checks the bounded exact-energy attestor.

This does not import unmerged UX PR #78, model RF propagation, authenticate
external solver logs, or establish manuscript/field sensor-network validity.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path

from shapely import concave_hull
from shapely.geometry import LineString, MultiPoint, Point

from scripts import bounded_result_attestation as proof
from scripts import n20_independent_geometry_audit as geo
from scripts import science_claim_gate as gate
from scripts.run_n20_reference_notebook import verify_result
from scripts.scientific_dashboard_adapter import (
    GLOBAL_TOPOLOGY, scenario_signature,
)

SCHEMA = 1
EXPECTED_GLOBAL_FEASIBLE = 860
EXPECTED_GLOBAL_FEASIBLE_SHA256 = (
    "3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40"
)
EXPECTED_FIXED_FIXED_EDGES = 17
EXPECTED_FULL_COMPONENTS = 8
EXPECTED_GLOBAL_WINNER = [0, 1, 3, 6, 7]
MAX_COMBINATIONS = 20_000


def build_full_graph(
    points: list[tuple[float, float]], hull, threshold: float, n_free: int
) -> dict:
    """Construct direct edges independently of the original notebook and UX.

    Uses the source GEOS concave hull predicate; this shared GEOS implementation
    is a documented geometry-independence limitation, not radio validation.
    """
    size = len(points)
    if (type(n_free) is not int or n_free <= 0 or n_free >= size
            or not math.isfinite(threshold) or threshold <= 0):
        raise ValueError("Invalid source projected graph dimensions or Dmax")
    if getattr(hull, "is_empty", True) or not hull.is_valid:
        raise ValueError("Original source waterbody hull is invalid")
    if any(len(p) != 2 or not all(math.isfinite(v) for v in p) for p in points):
        raise ValueError("Invalid projected source coordinate")
    inside = [bool(hull.contains(Point(p))) for p in points]
    edges = []
    for i in range(size):
        if not inside[i]:
            continue
        for j in range(i + 1, size):
            if not inside[j]:
                continue
            a, b = points[i], points[j]
            distance = math.hypot(b[0] - a[0], b[1] - a[1])
            if distance == 0 or distance > threshold:
                continue
            if abs(distance - threshold) <= geo.GEOMETRIC_THRESHOLD_AMBIGUITY_M:
                raise ValueError("Distance-boundary ambiguity requires independent review")
            if hull.contains(LineString((a, b))):
                edges.append([i, j])
    return {"node_count": size, "undirected_edges": edges}


def _neighbors(graph: dict) -> tuple[set[int], ...]:
    size = graph["node_count"]
    if type(size) is not int or not 1 <= size <= 35:
        raise ValueError("Missing full fixed-station or candidate node count")
    edges = graph["undirected_edges"]
    if not isinstance(edges, list):
        raise ValueError("Graph edges must be a list")
    adjacency = [set() for _ in range(size)]
    seen = set()
    for pair in edges:
        if (not isinstance(pair, list) or len(pair) != 2
                or any(type(v) is not int for v in pair)):
            raise ValueError("Malformed modeled graph edge")
        i, j = pair
        if not 0 <= i < j < size or (i, j) in seen:
            raise ValueError("Repeated or invalid direct link")
        seen.add((i, j))
        adjacency[i].add(j)
        adjacency[j].add(i)
    return tuple(adjacency)


def independent_union_find_connected(
    graph: dict, chosen: tuple[int, ...], n_free: int
) -> bool:
    """All original fixed and chosen candidates must form one component."""
    size = graph["node_count"]
    if type(n_free) is not int or not 0 <= n_free < size:
        raise ValueError("Invalid fixed-node boundary")
    if (len(chosen) != len(set(chosen))
            or any(type(i) is not int or i < 0 or i >= n_free for i in chosen)):
        raise ValueError("Invalid or duplicated selected free indices")
    _neighbors(graph)
    active = set(chosen) | set(range(n_free, size))
    parent = {i: i for i in active}

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in graph["undirected_edges"]:
        if i in active and j in active:
            parent[root(i)] = root(j)
    return len({root(i) for i in active}) == 1


def _full_component_count(graph: dict) -> int:
    adjacency = _neighbors(graph)
    missing = set(range(len(adjacency)))
    count = 0
    while missing:
        count += 1
        stack = [missing.pop()]
        while stack:
            for j in adjacency[stack.pop()]:
                if j in missing:
                    missing.remove(j)
                    stack.append(j)
    return count


def _original_fraction_energy(model: dict, subset: tuple[int, ...]) -> Fraction:
    selected = set(subset)
    return (
        sum((Fraction.from_float(float.fromhex(model["linear_float64_hex"][i]))
             for i in subset), Fraction())
        + sum((Fraction.from_float(float.fromhex(q))
               for i, j, q in model["quadratic_ij_float64_hex"]
               if i in selected and j in selected), Fraction())
    )


def full_global_subset_oracle(model: dict, graph: dict) -> dict:
    """Independent exact rational energy ordering and union-find feasible SHA."""
    n = len(model["candidate_master_feature_positions"])
    budget = model["budget_exact"]
    if (n != 20 or graph["node_count"] != n + 15
            or type(budget) is not int or budget != 5
            or math.comb(n, budget) > MAX_COMBINATIONS):
        raise ValueError("Only the frozen 20/15/K5 scoped global experiment is supported")
    feasible = 0
    accepted = sha256()
    best_ids = None
    best_exact = None
    for ids in combinations(range(n), budget):
        if not independent_union_find_connected(graph, ids, n):
            continue
        feasible += 1
        accepted.update((",".join(map(str, ids)) + "\n").encode("ascii"))
        val = _original_fraction_energy(model, ids)
        if best_exact is None or val < best_exact:
            best_ids, best_exact = ids, val
    return {
        "all_combinations": math.comb(n, budget),
        "feasible_subsets": feasible,
        "feasible_set_sha256": accepted.hexdigest(),
        "independently_optimal_indices": list(best_ids) if best_ids else None,
        "independent_exact_energy_numerator": (
            str(best_exact.numerator) if best_exact is not None else None
        ),
        "independent_exact_energy_denominator": (
            str(best_exact.denominator) if best_exact is not None else None
        ),
        "best_energy_approximation": float(best_exact) if best_exact is not None else None,
        "independent_graph_oracle": "union_find_full_mandatory_fixed_and_selected",
        "independent_objective_oracle": "fractions_over_binary64_coefficients",
    }


def validate_source_full_global(reference: dict) -> dict:
    """Cold source-only proof; Global is exploratory relative to local notebook."""
    verify_result(reference)
    local_geometry = geo.certify_geometry(reference)
    source_points, fixed_ids = geo.source_coordinates()
    model = reference["model_input"]
    source_indices = geo.EXPECTED_FREE + fixed_ids
    projected = [source_points[i] for i in source_indices]
    if model["site_coords_epsg32651_float64_hex"] != [
        [x.hex(), y.hex()] for x, y in projected
    ]:
        raise AssertionError("Declared source coordinates mismatch pinned raw GeoJSON")
    hull = concave_hull(MultiPoint(source_points), ratio=geo.HULL_RATIO, allow_holes=True)
    dmax = geo.original_fixed_spacing([source_points[i] for i in fixed_ids])
    graph = build_full_graph(projected, hull, dmax, len(geo.EXPECTED_FREE))
    neighbors = _neighbors(graph)
    n = len(geo.EXPECTED_FREE)
    local_source = local_geometry["spatial_graph"]
    rebuilt_local = [sorted(j for j in neighbors[i] if j < n) for i in range(n)]
    rebuilt_fixed = [
        sorted(j - n for j in neighbors[i] if j >= n) for i in range(n)
    ]
    if rebuilt_local != local_source["free_neighbor_indices_from_geojson"]:
        raise AssertionError("Original local free/free graph differs from complete global graph")
    if rebuilt_fixed != local_source["free_fixed_links_local_existing_positions"]:
        raise AssertionError("Original source raw free/fixed edges differ from new full graph")
    kinds = {
        "free_free": sum(j < n for i, j in graph["undirected_edges"]),
        "free_fixed": sum(i < n <= j for i, j in graph["undirected_edges"]),
        "fixed_fixed": sum(n <= i for i, j in graph["undirected_edges"]),
    }
    all_components = _full_component_count(graph)
    oracle = full_global_subset_oracle(model, graph)
    if (
        kinds != {"free_free": 11, "free_fixed": 34, "fixed_fixed": EXPECTED_FIXED_FIXED_EDGES}
        or all_components != EXPECTED_FULL_COMPONENTS
        or oracle["feasible_subsets"] != EXPECTED_GLOBAL_FEASIBLE
        or oracle["feasible_set_sha256"] != EXPECTED_GLOBAL_FEASIBLE_SHA256
        or oracle["independently_optimal_indices"] != EXPECTED_GLOBAL_WINNER
        or not math.isclose(
            oracle["best_energy_approximation"], reference["original_energy"],
            rel_tol=0.0, abs_tol=1e-8,
        )
    ):
        raise AssertionError("Source 35-node full-global modeled graph canaries changed")

    graph_sha = gate.full_manifest_digest(graph)
    scenario = {
        "model_input": model,
        "topology_mode": GLOBAL_TOPOLOGY,
        "graph_sha256": graph_sha,
        "input_origin": "exploratory",
        "solver_backend": "exact_enumeration",
        "controls": {},
    }
    report = {
        "scenario_sha256": scenario_signature(scenario),
        "selected_local_positions": oracle["independently_optimal_indices"],
        "reported_energy": oracle["best_energy_approximation"],
        "reported_solver_status": "optimal_exhaustive",
    }
    independent = proof.attest_bounded_result(scenario, report, graph=graph)
    if (
        independent["feasible_subsets"] != oracle["feasible_subsets"]
        or independent["feasible_sets_sha256"] != oracle["feasible_set_sha256"]
        or independent["independent_optimal_set"] != oracle["independently_optimal_indices"]
        or not independent["reported_selection_is_independently_optimal"]
        or independent["infeasibility_independently_proved"]
    ):
        raise AssertionError("Union-find oracle and bounded independent graph solver disagree")
    return {
        "schema_version": SCHEMA,
        "scope": "source-derived 35-node exploratory geometric full-global mathematical only",
        "source_data_sha256": geo.EXPECTED_DATA_SHA,
        "source_original_model_input_sha256": reference["model_input_sha256"],
        "original_source_local_geometry_sha256": local_geometry["spatial_graph_sha256"],
        "objective_fingerprint_sha256": gate.objective_fingerprint(model),
        "graph_manifest_sha256": graph_sha,
        "graph_manifest_hash_namespace": "science_bounded_exact_edge_payload_not_UX_PR78_fingerprint",
        "full_global_graph": graph,
        "modeled_edge_counts": kinds,
        "all_35_modeled_graph_component_count": all_components,
        "original_source_local_feasible_subsets": reference["feasible_combinations"],
        "global_exact_union_find_oracle": oracle,
        "independent_bounded_backend_check": independent,
        "global_scenario_sha256": scenario_signature(scenario),
        "distinct_from_original_notebook_local_one_hop": True,
        "actual_external_scip_solver_run_authenticated_for_global": False,
        "measured_radio_links_or_fixed_backhaul_validated": False,
        "manuscript_D2_AHP_reconciled": False,
        "physical_waterbody_or_transport_calibrated": False,
        "limitations": (
            "Both graph builders depend on the same source concave-hull/GEOS polygon "
            "proxy, not independent surveyed shoreline; neither fixed/fixed links "
            "nor radio/backhaul availability are field-measured. Global objective "
            "proof is mathematical exact enumeration, not original SCIP or paper parity."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite original scientific evidence")
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    report = validate_source_full_global(reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gate.canonical(report))
    x = report["global_exact_union_find_oracle"]
    print("N20_FULL_GLOBAL_INDEPENDENT_GEOMETRY_PROOF " + json.dumps({
        "graph_sha256": report["graph_manifest_sha256"],
        "source_only_geometry_sha256": report["original_source_local_geometry_sha256"],
        "modeled_edge_counts": report["modeled_edge_counts"],
        "all_35_components": report["all_35_modeled_graph_component_count"],
        "feasible_K5": x["feasible_subsets"],
        "feasible_K5_sha256": x["feasible_set_sha256"],
        "selected": x["independently_optimal_indices"],
        "score": x["best_energy_approximation"],
        "global_source_SCIPlike_certificate_claimed": False,
        "field_radio_or_water_quality_validated": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
