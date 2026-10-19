"""Independent exact topology tests: all original fixed stations are mandatory."""
from functools import lru_cache
from pathlib import Path
import sys

import numpy as np
import pytest
from shapely.geometry import Polygon

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from model import Instance, NOTEBOOK_WEIGHTS, load_data, make_instance, evaluate
from mvp_audit import NOTEBOOK_N20_K5_LOCAL_INDICES, source_sha
from wireless_topology import (
    WirelessGraph, components, fully_connected, exact_global_search,
    graph_from_source, evaluate_original_energy,
)


def fake_graph(n_free, n_fixed, edges):
    a = [set() for _ in range(n_free + n_fixed)]
    for i, j in edges:
        a[i].add(j)
        a[j].add(i)
    return WirelessGraph(
        tuple(sorted((min(i, j), max(i, j)) for i, j in edges)),
        tuple(tuple(sorted(row)) for row in a), n_free, n_fixed, "synthetic"
    )


def fake_instance(n_free, n_fixed, k, scores):
    return Instance(
        coords=np.zeros((n_free + n_fixed, 2)),
        free_indices=np.arange(n_free),
        fixed_indices=np.arange(n_fixed),
        utility=np.zeros(n_free + n_fixed),
        linear=np.asarray(scores, dtype=float),
        quadratic=(),
        neighbors=tuple(() for _ in range(n_free)),
        fixed_neighbors=np.ones(n_free, dtype=int),
        budget=k, d_max=1000.0,
    )


def test_mutually_connected_new_pair_cannot_repair_disconnected_original_fixed():
    # 0,1 are new; 2,3 existing. New nodes can see each other and only fixed 2.
    graph = fake_graph(2, 2, [(0, 1), (0, 2)])
    assert len(components(graph, (0, 1))) == 2
    assert not fully_connected(graph, (0, 1))
    result, diag = exact_global_search(fake_instance(2, 2, 2, [-2, -3]), graph)
    assert result is None
    assert diag["status"] == "infeasible_certified_full_graph_disconnected"
    assert 3 in [i for comp in diag["all_35_site_graph_components"] for i in comp]


def test_fixed_to_fixed_links_not_invented_but_can_be_explicitly_used():
    graph = fake_graph(2, 2, [(0, 2), (1, 3)])
    assert not fully_connected(graph, (0, 1))
    # Only a modeled actual fixed/fixed edge can join these clusters.
    graph_with_observed_link = fake_graph(2, 2, [(0, 2), (1, 3), (2, 3)])
    assert fully_connected(graph_with_observed_link, (0, 1))


def test_new_station_can_bridge_two_fixed_components_with_multiple_hops():
    graph = fake_graph(2, 2, [(2, 0), (0, 1), (1, 3)])
    assert not fully_connected(graph, ())
    assert not fully_connected(graph, (0,))
    assert fully_connected(graph, (0, 1))
    x, result = exact_global_search(fake_instance(2, 2, 2, [-1, -3]), graph)
    assert x.tolist() == [1, 1]
    assert result["status"] == "optimal_exhaustive"
    assert result["feasible_combinations"] == 1
    assert result["combinations_examined"] == 1
    assert result["energy"] == -4.0


def test_exact_search_optimizes_original_objective_not_only_connectivity():
    graph = fake_graph(3, 2, [(0, 3), (0, 4), (1, 0), (2, 0)])
    inst = fake_instance(3, 2, 2, [-1, -4, -2])
    x, metrics = exact_global_search(inst, graph)
    assert x.tolist() == [1, 1, 0]
    assert metrics["optimal"]
    assert metrics["energy"] == -5.0
    assert metrics["feasible_combinations"] == 2
    assert metrics["combinations_examined"] == 3


def test_infeasible_K_does_not_claim_scip_success():
    graph = fake_graph(2, 2, [(2, 0), (0, 1), (1, 3)])
    solution, out = exact_global_search(fake_instance(2, 2, 1, [-1, -2]), graph)
    assert solution is None and out["status"] == "infeasible_certified"
    assert out["combinations_examined"] == 2
    assert out["feasible_combinations"] == 0


def test_empty_K_is_valid_only_when_all_existing_already_connected():
    graph = fake_graph(2, 2, [(2, 3)])
    x, info = exact_global_search(fake_instance(2, 2, 0, [-3, -2]), graph)
    assert x.tolist() == [0, 0]
    assert info["status"] == "optimal_exhaustive"
    assert info["combinations_examined"] == 1
    assert info["feasible_combinations"] == 1


def test_duplicate_selected_nodes_refused():
    graph = fake_graph(2, 1, [(0, 1)])
    with pytest.raises(ValueError, match="Duplicate"):
        components(graph, (0, 0))


@lru_cache(maxsize=1)
def source():
    data_path = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
    digest = source_sha(data_path)
    data = load_data(data_path)
    instance, simulated = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    assert not simulated
    return data, instance, digest


def test_actual_lake_global_graph_restores_free_edges_and_fixed_contact_flags():
    data, instance, digest = source()
    graph = graph_from_source(data, instance, dataset_sha256=digest)
    n = graph.n_free
    assert n == 20 and graph.n_fixed == 15
    assert graph.fingerprint
    assert set(i for i, j in graph.edges if i < n and j < n) == {
        min(i, j) for i, js in enumerate(instance.neighbors) for j in js if i < j
    }
    for i in range(n):
        assert bool(instance.fixed_neighbors[i]) == any(
            j >= n for j in graph.neighbors[i]
        )
    assert not any(i == j for i, j in graph.edges)
    assert len(set(graph.edges)) == len(graph.edges)
    # Full fixed-fixed edge construction is a new comparison mode only.
    assert all(0 <= i < j < 35 for i, j in graph.edges)


def test_actual_lake_global_search_never_claims_a_fictitious_solution():
    data, instance, digest = source()
    graph = graph_from_source(data, instance, dataset_sha256=digest)
    selected, info = exact_global_search(instance, graph, timeout_seconds=30)
    assert info["status"] in {
        "optimal_exhaustive", "infeasible_certified",
        "infeasible_certified_full_graph_disconnected"
    }, info
    assert info["combinations_total"] == 15504
    if selected is None:
        assert not info["optimal"]
        assert info["feasible_combinations"] == 0
    else:
        chosen = tuple(np.flatnonzero(selected).tolist())
        assert fully_connected(graph, chosen)
        assert len(chosen) == 5 and info["optimal"]
        assert evaluate_original_energy(instance, chosen) == pytest.approx(info["energy"])
    # Original local reference remains a separate, unchanged model:
    baseline = np.zeros(20, dtype=int)
    baseline[list(NOTEBOOK_N20_K5_LOCAL_INDICES)] = 1
    assert evaluate(instance, baseline)["feasible"]


def test_original_geo_hull_is_not_replaced_by_blanket_distance_links(monkeypatch):
    import wireless_topology as module

    class Data:
        coords = np.array([(0, 0), (10, 0), (10, 10), (0, 10)], dtype=float)

    class Demo:
        coords = np.array([(2., 8.), (8., 8.)] + [(2., 2.)] * 33, dtype=float)
        free_indices = np.arange(20)
        fixed_indices = np.arange(15)
        d_max = 10
        neighbors = tuple(() for _ in range(20))
        fixed_neighbors = np.zeros(20, dtype=int)

    # U shape: pair (2,8) -> (8,8) crosses central land gap.
    u = Polygon([(0, 0), (10, 0), (10, 10), (7, 10),
                 (7, 3), (3, 3), (3, 10), (0, 10)])
    monkeypatch.setattr(module, "concave_hull", lambda *a, **kw: u)
    # Other 33 points (2,2) are technically linked to each other; this
    # synthetic case deliberately tests the early free adjacency parity.
    with pytest.raises(ValueError, match="free/free"):
        graph_from_source(Data(), Demo(), dataset_sha256="a" * 64)


def test_independent_union_find_all_15_fixed_5_new_enumeration():
    """Independent second implementation, using edge list not solver BFS."""
    import hashlib
    import itertools
    import json

    data, instance, digest = source()
    graph = graph_from_source(data, instance, dataset_sha256=digest)
    n = graph.n_free
    fixed_nodes = set(range(n, n + graph.n_fixed))
    fixed_fixed = sum(i >= n and j >= n for i, j in graph.edges)
    free_fixed = sum(i < n and j >= n for i, j in graph.edges)
    free_free = sum(j < n for i, j in graph.edges)

    def independently_connected(chosen):
        active = fixed_nodes | set(chosen)
        parent = {i: i for i in active}

        def root(i):
            while parent[i] != i:
                i = parent[i]
            return i

        for i, j in graph.edges:
            if i in active and j in active:
                parent[root(i)] = root(j)
        return len({root(i) for i in active}) == 1

    all_source_candidate_sets = list(itertools.combinations(range(n), 5))
    accepted = [ids for ids in all_source_candidate_sets if independently_connected(ids)]
    sha = hashlib.sha256()
    for ids in accepted:
        sha.update((",".join(map(str, ids)) + "\n").encode("ascii"))
    incumbent = None
    value = float("inf")
    for ids in accepted:
        s = set(ids)
        energy = sum(float(instance.linear[i]) for i in ids)
        energy += sum(float(q) for i, j, q in instance.quadratic
                      if i in s and j in s)
        if energy < value:
            incumbent, value = ids, energy
    result, metrics = exact_global_search(instance, graph, timeout_seconds=30)
    if not accepted:
        assert result is None
        assert metrics["status"].startswith("infeasible_certified")
        assert not metrics["optimal"]
    else:
        assert metrics["optimal"], metrics
        assert metrics["feasible_combinations"] == len(accepted)
        assert tuple(np.flatnonzero(result).tolist()) == incumbent
        assert metrics["energy"] == pytest.approx(value, abs=1e-8)
    # Printed in the CI -s job: scientific evidence, not a hardcoded
    # undocumented outcome or a manuscript parity claim.
    print("N20_ALL_EXISTING_GLOBAL_NETWORK_EVIDENCE " + json.dumps({
        "fixed_fixed_direct_links": fixed_fixed,
        "free_fixed_direct_links": free_fixed,
        "free_free_direct_links": free_free,
        "full_35_graph_components": len(components(graph, tuple(range(n)))),
        "all_15_fixed_component_groups_when_all_20_available": [
            list(group) for group in components(graph, tuple(range(n)))
            if any(i >= n for i in group)
        ],
        "K5_total": len(all_source_candidate_sets),
        "K5_global_feasible": len(accepted),
        "K5_global_feasible_sha": sha.hexdigest(),
        "global_status": metrics["status"],
        "K5_global_optimal_local_indices": list(incumbent) if incumbent else None,
        "K5_global_optimal_original_energy": value if incumbent else None,
        "source_original_local_optimum_unchanged": True,
    }, sort_keys=True))
