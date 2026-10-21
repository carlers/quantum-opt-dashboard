"""Publish exact 15-fixed+K-new full-global network evidence from pinned source.

Not historical paper validation. This command is CI-only, outputs reproducible
bounded metadata; does not alter the original GeoJSON, source notebook or UI.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
from pathlib import Path
import platform

import numpy as np

from model import NOTEBOOK_WEIGHTS, load_data, make_instance, evaluate
from mvp_audit import source_sha
from wireless_topology import (
    _canonical, components, fully_connected, exact_global_search,
    graph_from_source,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
S0_EXPECTED_COUNT = 1077
S0_EXPECTED_SHA = "2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a"


def observed_record() -> dict:
    data_hash = source_sha(DATA)
    data = load_data(DATA)
    instance, fallback = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    if fallback or len(instance.fixed_indices) != 15:
        raise AssertionError("Actual original fixed-site identities required")
    graph = graph_from_source(data, instance, dataset_sha256=data_hash)
    s0_count = global_count = 0
    s0_sha = hashlib.sha256()
    global_sha = hashlib.sha256()
    for ids in combinations(range(20), 5):
        bits = np.zeros(20, dtype=int)
        bits[list(ids)] = 1
        if evaluate(instance, bits)["feasible"]:
            s0_count += 1
            s0_sha.update((",".join(map(str, ids)) + "\n").encode("ascii"))
        if fully_connected(graph, ids):
            global_count += 1
            global_sha.update((",".join(map(str, ids)) + "\n").encode("ascii"))
            if not evaluate(instance, bits)["feasible"]:
                raise AssertionError("Fully connected subset violates original one-hop rule")
    if s0_count != S0_EXPECTED_COUNT or s0_sha.hexdigest() != S0_EXPECTED_SHA:
        raise AssertionError("Original source local feasible set changed")
    chosen, result = exact_global_search(instance, graph, timeout_seconds=30)
    if result["status"] == "time_limit_no_certified_optimum":
        raise RuntimeError("Source global exact enumeration timed out; no report accepted")
    if global_count != result.get("feasible_combinations", 0):
        raise AssertionError("Global connected-set counts differ between algorithms")
    if chosen is not None:
        active = tuple(np.flatnonzero(chosen).tolist())
        if not fully_connected(graph, active):
            raise AssertionError("Chosen global solution is not connected")
    fixed_groups = components(graph, ())
    all_possible_groups = components(graph, tuple(range(20)))
    return {
        "schema_version": 1,
        "status": "notebook_derived_exploratory_global_wireless_proxy",
        "owner_requirement": (
            "all 15 original existing AND all 5 selected new stations "
            "mutually reachable through water-only direct modeled links"
        ),
        "source_dataset_sha256": data_hash,
        "source_free_master_feature_positions": [int(x) for x in instance.free_indices],
        "source_fixed_master_feature_positions": [int(x) for x in instance.fixed_indices],
        "original_objective_linear_float64_hex": [float(x).hex() for x in instance.linear],
        "original_objective_quadratic_ij_float64_hex": [
            [int(i), int(j), float(q).hex()] for i, j, q in instance.quadratic
        ],
        "source_dmax_float64_hex": float(instance.d_max).hex(),
        "modeled_geometry_graph": graph.as_record(),
        "all_direct_link_counts": {
            "free_free": sum(j < 20 for i, j in graph.edges),
            "free_fixed": sum(i < 20 and j >= 20 for i, j in graph.edges),
            "fixed_fixed": sum(i >= 20 for i, j in graph.edges),
        },
        "fixed_only_component_count": len(fixed_groups),
        "fixed_only_component_membership": [list(row) for row in fixed_groups],
        "all_35_component_count": len(all_possible_groups),
        "full_source_K5_subsets": 15504,
        "original_local_feasible_count": s0_count,
        "original_local_feasible_sha256": s0_sha.hexdigest(),
        "all_stations_global_feasible_count": global_count,
        "all_stations_global_feasible_sha256": global_sha.hexdigest(),
        "globally_connected_selected_indices": (
            [int(x) for x in np.flatnonzero(chosen)] if chosen is not None else None
        ),
        "search": result,
        "runtime": {"python": platform.python_version()},
        "limitations": [
            "Fixed-fixed links are inferred from source hull and Dmax, not surveyed radio backhaul",
            "Unselected candidates are optional; source sites, budget and objective unchanged",
            "Independent geometry is still same original Shapely/GEOS lake hull proxy",
            "Not the earlier 110-combination S2 study and not source-paper replication",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite full-global research certificate")
    result = observed_record()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(_canonical(result))
    print("N20_ALL_FIXED_FULL_GLOBAL_CI_CERTIFICATE " + json.dumps({
        "fixed_fixed_edges": result["all_direct_link_counts"]["fixed_fixed"],
        "fixed_only_components": result["fixed_only_component_count"],
        "full_all_sites_components": result["all_35_component_count"],
        "local_feasible": result["original_local_feasible_count"],
        "global_feasible": result["all_stations_global_feasible_count"],
        "global_feasible_sha256": result["all_stations_global_feasible_sha256"],
        "global_optimum": result["globally_connected_selected_indices"],
        "global_status": result["search"]["status"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
