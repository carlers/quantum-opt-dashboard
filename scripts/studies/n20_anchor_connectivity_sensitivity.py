"""Preregistered N20/K5 S0/S1/S2 connectivity sensitivity; no model corrections.

See docs/research_protocols/N20_S1_ANCHOR_REACHABILITY_PREREG_2026_10_19.md
Preregisration committed in separate DRAFT PR #74 *before* first CI outcome.
Uses fresh unchanged notebook manifest and independently rebuilt source-GeoJSON
full free/fixed links. Stdlib-only, deterministic exhaustive enumeration.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path

EXPECTED_DATA = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
EXPECTED_ARCHIVE = "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"
EXPECTED_S0_SETS_SHA = "2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a"
EXPECTED_S0_CHOICE = (0, 1, 3, 6, 7)
EXPECTED_S0_ENERGY = -3.3012934918564643
EXPECTED_EMPTY_CANDIDATES = (2, 4, 5, 8, 11, 16, 18)
EXPECTED_FREE_MASTER = (
    5253, 2394, 1894, 1557, 3225, 4623, 47, 5409, 3922, 2408,
    2694, 4136, 2567, 1164, 4973, 4537, 2726, 968, 16, 1762,
)
EXPECTED_FIXED_MASTER = (
    417, 454, 725, 1055, 1076, 1709, 2771, 3402, 3520, 3529,
    3732, 3886, 4613, 4868, 5038,
)
N = 20
K = 5


def canonical(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       allow_nan=False, ensure_ascii=False) + "\n").encode("utf-8")


def sha(obj: object) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def checked_graph(neighbors: list, fixed_flags: list, fixed_links: list) -> None:
    if len(neighbors) != N or len(fixed_flags) != N or len(fixed_links) != N:
        raise ValueError("Source graph dimensions differ from 20 free sites")
    for i in range(N):
        if fixed_flags[i] not in (0, 1) or type(fixed_flags[i]) is not int:
            raise ValueError("Invalid original fixed neighbor flag")
        if not isinstance(neighbors[i], list) or not isinstance(fixed_links[i], list):
            raise ValueError("Original adjacency must be ordered integer lists")
        if (neighbors[i] != sorted(set(neighbors[i]))
                or any(type(j) is not int or j < 0 or j >= N or j == i for j in neighbors[i])):
            raise ValueError("Invalid free neighbor indices")
        if (fixed_links[i] != sorted(set(fixed_links[i]))
                or any(type(j) is not int or j < 0 or j >= 15 for j in fixed_links[i])):
            raise ValueError("Invalid verified free-to-fixed link indices")
        if fixed_flags[i] != int(bool(fixed_links[i])):
            raise ValueError("Fixed flags disagree with reconstructed original GeoJSON links")
        for j in neighbors[i]:
            if i not in neighbors[j]:
                raise ValueError("Asymmetric free/free adjacency")


def selected_components(ids: tuple[int, ...], neighbors: list[list[int]]) -> list[tuple[int, ...]]:
    """Connected components of selected new sites *only*, in stable site order."""
    chosen, unvisited = set(ids), set(ids)
    groups: list[tuple[int, ...]] = []
    while unvisited:
        first = min(unvisited)
        pending = [first]
        group = {first}
        unvisited.remove(first)
        while pending:
            i = pending.pop()
            for j in neighbors[i]:
                if j in chosen and j in unvisited:
                    unvisited.remove(j)
                    group.add(j)
                    pending.append(j)
        groups.append(tuple(sorted(group)))
    return groups


def admissibility(ids: tuple[int, ...], neighbors: list[list[int]],
                  fixed_links: list[list[int]]) -> dict:
    """S0/S1/S2; no inferred fixed/fixed links or real-world communications."""
    selected = set(ids)
    flags = [bool(fixed_links[i]) for i in ids]
    source_one_hop = all(
        flags[k] or any(j in selected for j in neighbors[i])
        for k, i in enumerate(ids)
    )
    groups = selected_components(ids, neighbors)
    anchors = [any(bool(fixed_links[i]) for i in group) for group in groups]
    component_anchored = source_one_hop and all(anchors)

    # Traverse the graph induced by selected new nodes and all original fixed
    # nodes; 20..34 are actual existing stations, never linked to each other.
    reachable: set[int] = {ids[0]}
    queue: deque[int] = deque([ids[0]])
    fixed_to_new = [
        [i for i in ids if fixed_idx in fixed_links[i]]
        for fixed_idx in range(15)
    ]
    while queue:
        current = queue.popleft()
        if current < N:
            options = (
                [j for j in neighbors[current] if j in selected]
                + [N + f for f in fixed_links[current]]
            )
        else:
            options = fixed_to_new[current - N]
        for other in options:
            if other not in reachable:
                reachable.add(other)
                queue.append(other)
    shared_component = (
        component_anchored
        and selected.issubset(reachable)
        and any(i >= N for i in reachable)
    )
    return {
        "S0": source_one_hop,
        "S1": component_anchored,
        "S2": shared_component,
        "new_only_component_count": len(groups),
        "anchored_component_count": sum(anchors),
    }


def raw_energy(ids: tuple[int, ...], linear: list[float],
               quadratic: list[tuple[int, int, float]]) -> float:
    chosen = set(ids)
    # The original notebook uses Python sum, in this exact order; do not
    # switch to math.fsum or round coefficient values to force paper parity.
    return float(sum(float(linear[i]) for i in ids) + sum(
        float(q) for i, j, q in quadratic if i in chosen and j in chosen
    ))


def checked_inputs(record: dict, geometry: dict) -> tuple[list, list, list, list[float], list]:
    """Fail closed on historic IDs, exact record, geometry provenance and graph."""
    if (record.get("schema_version") != 2
            or record.get("status") != "notebook_derived_N20_replay_not_paper_parity"
            or record.get("dataset_sha256") != EXPECTED_DATA
            or record.get("archived_notebook_sha256") != EXPECTED_ARCHIVE
            or record.get("candidate_count") != N
            or record.get("new_station_budget") != K
            or record.get("marked_existing_stations") != 15
            or record.get("enumerated_combinations") != 15504
            or record.get("feasible_combinations") != 1077
            or record.get("feasible_site_sets_sha256") != EXPECTED_S0_SETS_SHA):
        raise ValueError("Original source N20 result identity/feasible-set canary differs")
    if (tuple(record.get("selected_local_positions", [])) != EXPECTED_S0_CHOICE
            or record.get("scip_status") != "optimal"
            or not record.get("local_one_hop_not_global_connectivity")
            or not math.isfinite(record.get("original_energy", math.nan))
            or abs(record["original_energy"] - EXPECTED_S0_ENERGY) >= 1e-7):
        raise ValueError("Original independent SCIP optimum differs")
    model = record.get("model_input")
    if not isinstance(model, dict) or sha(model) != record.get("model_input_sha256"):
        raise ValueError("Original model input digest mismatch")
    if (model.get("dataset_sha256") != EXPECTED_DATA
            or model.get("archived_notebook_sha256") != EXPECTED_ARCHIVE
            or tuple(model.get("candidate_master_feature_positions", [])) != EXPECTED_FREE_MASTER
            or tuple(model.get("fixed_master_feature_positions", [])) != EXPECTED_FIXED_MASTER
            or model.get("budget_exact") != K):
        raise ValueError("Original candidate/fixed station identities differ")
    g = geometry.get("spatial_graph")
    if (not isinstance(g, dict)
            or geometry.get("schema_version") != 1
            or geometry.get("source_data_sha256") != EXPECTED_DATA
            or geometry.get("model_input_sha256") != record["model_input_sha256"]
            or sha(g) != geometry.get("spatial_graph_sha256")
            or tuple(g.get("candidate_master_feature_positions", [])) != EXPECTED_FREE_MASTER
            or tuple(g.get("existing_station_master_feature_positions", [])) != EXPECTED_FIXED_MASTER
            or g.get("feasible_combinations") != 1077
            or g.get("feasible_site_sets_sha256") != EXPECTED_S0_SETS_SHA):
        raise ValueError("Independent original GeoJSON geometry certificate differs")

    neighbors = model.get("free_neighbor_indices")
    fixed_flags = model.get("fixed_neighbor_flags")
    links = g.get("free_fixed_links_local_existing_positions")
    if (neighbors != g.get("free_neighbor_indices_from_geojson")
            or fixed_flags != g.get("fixed_neighbor_flags_from_geojson")):
        raise ValueError("Reported free neighbor graph differs from original source geometry")
    checked_graph(neighbors, fixed_flags, links)
    if g.get("free_fixed_edges") != sum(len(row) for row in links):
        raise ValueError("Actual 20×15 source free/fixed edges disagree with certificate")
    if len(model.get("linear_float64_hex", [])) != N:
        raise ValueError("Source linear coefficient count changed")
    linear = [float.fromhex(s) for s in model["linear_float64_hex"]]
    quadratic = [
        (i, j, float.fromhex(v))
        for i, j, v in model.get("quadratic_ij_float64_hex", [])
    ]
    if (len(quadratic) != 12 or len(set((i, j) for i, j, _ in quadratic)) != 12
            or any(type(i) is not int or type(j) is not int or
                   not (0 <= i < j < N) for i, j, _ in quadratic)
            or not all(math.isfinite(x) for x in linear)
            or not all(math.isfinite(v) for _, _, v in quadratic)):
        raise ValueError("Original source MIQP coefficients invalid")
    return neighbors, fixed_flags, links, linear, quadratic


def analyze(record: dict, geometry: dict) -> dict:
    neighbors, fixed_flags, links, linear, quadratic = checked_inputs(record, geometry)
    zero_neighbors = [
        i for i in range(N) if not fixed_flags[i] and not neighbors[i]
    ]
    if tuple(zero_neighbors) != EXPECTED_EMPTY_CANDIDATES:
        raise ValueError("Seven source zero-neighbor candidate IDs changed")

    states = {
        label: {"count": 0, "digest": hashlib.sha256(), "best": math.inf, "best_sets": []}
        for label in ("S0", "S1", "S2")
    }
    first_removed_s1, first_removed_s2 = [], []
    original_components = Counter()
    origin_winner = None
    scanned = 0
    for ids in combinations(range(N), K):
        scanned += 1
        test = admissibility(ids, neighbors, links)
        if ids == EXPECTED_S0_CHOICE:
            origin_winner = test
        if test["S0"]:
            original_components[test["new_only_component_count"]] += 1
            if not test["S1"] and len(first_removed_s1) < 3:
                first_removed_s1.append(list(ids))
            if test["S1"] and not test["S2"] and len(first_removed_s2) < 3:
                first_removed_s2.append(list(ids))
        for key, st in states.items():
            if not test[key]:
                continue
            st["count"] += 1
            st["digest"].update((",".join(map(str, ids)) + "\n").encode("ascii"))
            energy = raw_energy(ids, linear, quadratic)
            if energy < st["best"] - 1e-9:
                st["best"], st["best_sets"] = energy, [list(ids)]
            elif abs(energy - st["best"]) <= 1e-9:
                st["best_sets"].append(list(ids))
    if scanned != 15504:
        raise ValueError("Preregistered complete K5 scan did not finish")
    if (states["S0"]["count"] != 1077
            or states["S0"]["digest"].hexdigest() != EXPECTED_S0_SETS_SHA
            or states["S0"]["best_sets"] != [list(EXPECTED_S0_CHOICE)]
            or abs(states["S0"]["best"] - EXPECTED_S0_ENERGY) >= 1e-7):
        raise ValueError("Source control S0 fails independent exhaustive canary")
    if not (states["S2"]["count"] <= states["S1"]["count"] <= states["S0"]["count"]):
        raise ValueError("Preregistered subset inclusion violated")
    report = {}
    for label, st in states.items():
        is_empty = st["count"] == 0
        report[label] = {
            "status": "no_feasible_k5_sets" if is_empty else "feasible",
            "feasible_k5_sets": st["count"],
            "feasible_set_sha256": st["digest"].hexdigest(),
            "optimal_sets_local_positions": st["best_sets"],
            "optimal_source_objective_energy": None if is_empty else st["best"],
            "source_objective_delta_vs_S0": (
                None if is_empty else st["best"] - states["S0"]["best"]
            ),
        }
    return {
        "schema_version": 1,
        "scope": "preregistered_N20_S0_S1_S2_anchor_graph_not_physical_network",
        "preregistration": "docs/research_protocols/N20_S1_ANCHOR_REACHABILITY_PREREG_2026_10_19.md",
        "source_model_input_sha256": record["model_input_sha256"],
        "source_geojson_sha256": EXPECTED_DATA,
        "independent_geometry_sha256": geometry["spatial_graph_sha256"],
        "source_fixed_count": 15,
        "source_candidate_count": N,
        "never_eligible_candidate_local_ids": zero_neighbors,
        "all_five_site_subsets_examined": scanned,
        "scenario_results": report,
        "S0_new_only_connected_component_histogram": {
            str(k): v for k, v in sorted(original_components.items())
        },
        "original_winner_rule_flags": origin_winner,
        "S0_but_not_S1_first_three_counterexamples": first_removed_s1,
        "S1_but_not_S2_first_three_counterexamples": first_removed_s2,
        "research_warning": (
            "These are mathematical graph constraints derived from original GEOS "
            "geometry, not measured communications or original-paper recreation. "
            "All scenarios use the SAME old objective and candidates."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("--geometry", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    opts = p.parse_args()
    if opts.output.exists():
        raise FileExistsError("Refusing to overwrite preregistered study evidence")
    record = json.loads(opts.result.read_text(encoding="utf-8"))
    geometry = json.loads(opts.geometry.read_text(encoding="utf-8"))
    summary = analyze(record, geometry)
    opts.output.parent.mkdir(parents=True, exist_ok=True)
    opts.output.write_bytes(canonical(summary))
    print("N20_PREREGISTERED_GRAPH_SENSITIVITY " + json.dumps({
        "K5_scanned": summary["all_five_site_subsets_examined"],
        "model_sha": summary["source_model_input_sha256"],
        "independent_geometry_sha": summary["independent_geometry_sha256"],
        "source_zero_neighbor_candidates": summary["never_eligible_candidate_local_ids"],
        "scenarios": {
            s: {"feasible": v["feasible_k5_sets"],
                "selected": v["optimal_sets_local_positions"],
                "energy": v["optimal_source_objective_energy"]}
            for s, v in summary["scenario_results"].items()
        },
    }, sort_keys=True))


if __name__ == "__main__":
    main()
