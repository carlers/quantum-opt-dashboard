"""Explicit water-blocked wireless graph and exact all-station connectivity.

This module creates a NEW exploratory dashboard scenario. The archived
notebook's intentional local one-hop model is NOT modified. Actual radio
propagation, Fresnel clearance, antennas and fixed infrastructure are unknown.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from itertools import combinations
import json
import math
import time
from typing import TYPE_CHECKING

import numpy as np
from shapely import concave_hull
from shapely.geometry import LineString, MultiPoint, Point

if TYPE_CHECKING:
    from model import Instance, LakeData

GLOBAL_MODE = "all_stations_connected"
LOCAL_MODE = "source_local"
GEOMETRY_HULL_RATIO = 0.05
RESULT_SCHEMA = 1


@dataclass(frozen=True)
class WirelessGraph:
    """Site indices: first n_free new candidates, then n_fixed original sites."""

    edges: tuple[tuple[int, int], ...]
    neighbors: tuple[tuple[int, ...], ...]
    n_free: int
    n_fixed: int
    fingerprint: str

    def as_record(self) -> dict:
        return {
            "schema_version": RESULT_SCHEMA,
            "mode": GLOBAL_MODE,
            "site_order": "original_free_then_original_fixed",
            "free_count": self.n_free,
            "fixed_count": self.n_fixed,
            "undirected_edges": [list(pair) for pair in self.edges],
            "fingerprint_sha256": self.fingerprint,
            "limitations": (
                "Edges are geometric proxies: pinned-source concave hull, "
                "strict water-only straight segment and source Dmax. "
                "No measured radio link or fixed backhaul was invented."
            ),
        }


def _canonical(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def graph_from_source(data: "LakeData", instance: "Instance",
                      *, dataset_sha256: str) -> WirelessGraph:
    """Derive free/free, free/fixed AND fixed/fixed links from original geometry.

    No fabricated fixed network. Independently cross-check original collapsed
    one-hop flags to fail closed if spatial model construction differs.
    """
    n = len(instance.free_indices)
    m = len(instance.fixed_indices)
    if n != 20 or m != 15 or len(instance.coords) != n + m:
        raise ValueError("Pinned exploratory global mode requires 20 free and 15 fixed")
    if not isinstance(dataset_sha256, str) or len(dataset_sha256) != 64:
        raise ValueError("Pinned source SHA-256 is required")
    pts = np.asarray(instance.coords, dtype=float)
    if pts.shape != (n + m, 2) or not np.isfinite(pts).all():
        raise ValueError("Invalid projected original coordinates")
    if not math.isfinite(float(instance.d_max)) or instance.d_max <= 0:
        raise ValueError("Invalid source Dmax")
    hull = concave_hull(MultiPoint(np.asarray(data.coords, dtype=float)),
                        ratio=GEOMETRY_HULL_RATIO, allow_holes=True)
    if hull.is_empty or not hull.is_valid:
        raise ValueError("Original source-derived lake hull is not valid")
    inside = [hull.contains(Point(float(p[0]), float(p[1]))) for p in pts]
    links: list[tuple[int, int]] = []
    adjacent = [set() for _ in range(n + m)]
    dmax = float(instance.d_max)
    for i in range(n + m):
        if not inside[i]:
            continue
        for j in range(i + 1, n + m):
            if not inside[j]:
                continue
            a, b = pts[i], pts[j]
            # Distance check before expensive GEOS segment predicate.
            if math.hypot(float(b[0] - a[0]), float(b[1] - a[1])) > dmax:
                continue
            if not hull.contains(LineString((tuple(a), tuple(b))):
                continue
            adjacent[i].add(j)
            adjacent[j].add(i)
            links.append((i, j))
    # Compare ALL source free/free links and the historically collapsed
    # free-to-any-existing flags; never rewrite original model terms.
    source_free = tuple(tuple(sorted(k)) for k in instance.neighbors)
    rebuilt_free = tuple(tuple(sorted(j for j in adjacent[i] if j < n))
                         for i in range(n))
    if rebuilt_free != source_free:
        raise ValueError("Global direct graph disagrees with source free/free edges")
    for i in range(n):
        real_fixed = any(j >= n for j in adjacent[i])
        if real_fixed != bool(instance.fixed_neighbors[i]):
            raise ValueError("Global graph disagrees with source free/fixed flags")
    record = {
        "site_positions_epsg32651_float64_hex": [
            [float(x).hex(), float(y).hex()] for x, y in pts
        ],
        "source_dataset_sha256": dataset_sha256,
        "d_max_float64_hex": dmax.hex(),
        "hull_ratio": GEOMETRY_HULL_RATIO,
        "allow_holes": True,
        "undirected_edges": links,
        "free_feature_positions": [int(i) for i in instance.free_indices],
        "fixed_feature_positions": [int(i) for i in instance.fixed_indices],
    }
    fingerprint = hashlib.sha256(_canonical(record)).hexdigest()
    return WirelessGraph(tuple(links), tuple(tuple(sorted(s)) for s in adjacent),
                         n, m, fingerprint)


def components(graph: WirelessGraph, active_free: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    """Connected components of ALL 15 existing + ONLY selected new stations."""
    if len(active_free) != len(set(active_free)):
        raise ValueError("Duplicate selected candidate")
    if any(type(i) is not int or i < 0 or i >= graph.n_free for i in active_free):
        raise ValueError("Invalid selected candidate")
    active = set(active_free) | set(range(graph.n_free, graph.n_free + graph.n_fixed))
    result = []
    while active:
        start = min(active)
        visited = {start}
        pending = [start]
        active.remove(start)
        while pending:
            i = pending.pop()
            for j in graph.neighbors[i]:
                if j in active:
                    active.remove(j)
                    visited.add(j)
                    pending.append(j)
        result.append(tuple(sorted(visited)))
    return tuple(result)


def fully_connected(graph: WirelessGraph, active_free: tuple[int, ...]) -> bool:
    """Every original fixed site AND every selected new site connected."""
    return len(components(graph, active_free)) == 1


def evaluate_original_energy(instance: "Instance", chosen: tuple[int, ...]) -> float:
    """Same MIQP as original local notebook, no connectivity penalty retuning."""
    s = set(chosen)
    return float(sum(float(instance.linear[i]) for i in chosen) +
                 sum(float(q) for i, j, q in instance.quadratic if i in s and j in s))


def exact_global_search(instance: "Instance", graph: WirelessGraph,
                        *, timeout_seconds: float = 30.0) -> tuple[np.ndarray | None, dict]:
    """Enumerate all C(20,K) to mathematically certify optimum or infeasibility.

    A full-graph disconnectedness precheck is a valid infeasibility proof:
    selecting a subset cannot add edges absent from the complete 35-site graph.
    No source-SCIP optimality is claimed for this separate enumeration.
    """
    n, k = graph.n_free, int(instance.budget)
    if n != len(instance.free_indices) or k < 0 or k > n:
        raise ValueError("Invalid original K budget / network size")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("Timeout must be a positive finite number")
    total = math.comb(n, k)
    full_components = components(graph, tuple(range(n)))
    if len(full_components) > 1:
        return None, {
            "status": "infeasible_certified_full_graph_disconnected",
            "optimal": False,
            "solver": "exact_graph_precheck",
            "budget": k,
            "combinations_total": total,
            "combinations_examined": 0,
            "feasible_combinations": 0,
            "all_35_site_graph_components": [list(g) for g in full_components],
            "reason": (
                "Even all 20 possible new sensors together cannot connect "
                "all 15 existing stations under the source water-only link rule."
            ),
        }
    deadline = time.monotonic() + timeout_seconds
    best = math.inf
    best_ids: tuple[int, ...] | None = None
    feasible = 0
    examined = 0
    for candidate in combinations(range(n), k):
        if examined % 1024 == 0 and time.monotonic() > deadline:
            return None, {
                "status": "time_limit_no_certified_optimum",
                "optimal": False,
                "solver": "bounded_exhaustive_enumeration",
                "budget": k,
                "combinations_total": total,
                "combinations_examined": examined,
                "feasible_combinations_seen": feasible,
                "reason": "Full exact enumeration not completed; no optimum is asserted.",
            }
        examined += 1
        if not fully_connected(graph, candidate):
            continue
        feasible += 1
        energy = evaluate_original_energy(instance, candidate)
        if energy < best:
            best, best_ids = energy, candidate
    if best_ids is None:
        return None, {
            "status": "infeasible_certified",
            "optimal": False,
            "solver": "exact_exhaustive_enumeration",
            "budget": k, "combinations_total": total,
            "combinations_examined": examined,
            "feasible_combinations": 0,
            "reason": "No subset satisfies connectivity of ALL fixed and selected new stations.",
        }
    x = np.zeros(n, dtype=int)
    x[list(best_ids)] = 1
    assert fully_connected(graph, best_ids)
    return x, {
        "status": "optimal_exhaustive", "optimal": True,
        "solver": "exact_exhaustive_enumeration",
        "budget": k,
        "combinations_total": total,
        "combinations_examined": examined,
        "feasible_combinations": feasible,
        "selected_local_positions": list(best_ids),
        "energy": best,
        "all_station_components": [list(g) for g in components(graph, best_ids)],
        "graph_fingerprint_sha256": graph.fingerprint,
    }


def global_evidence_zip(model: dict, graph: WirelessGraph, solver: dict,
                        selected_sites_csv: bytes) -> bytes:
    """Export truthful exact-search/graph evidence; NOT a fictitious SCIP LP."""
    import io
    from zipfile import ZIP_DEFLATED, ZipFile

    files = {
        "model.json": _canonical(model),
        "wireless_graph.json": _canonical(graph.as_record()),
        "result.json": _canonical({
            "schema_version": RESULT_SCHEMA,
            "connectivity_mode": GLOBAL_MODE,
            "algorithm": solver["solver"],
            "status": solver["status"],
            "optimal_proven": bool(solver["optimal"]),
            "search": solver,
            "source_dataset_sha256": model["dataset_sha256"],
            "model_fingerprint_sha256": model["model_fingerprint_sha256"],
            "graph_fingerprint_sha256": graph.fingerprint,
            "note": (
                "Exploratory all-stations wireless graph using a lake hull proxy; "
                "this is exact enumeration/precheck, NOT SCIP or radio validation."
            ),
        }),
        "selected_sites.csv": selected_sites_csv,
    }
    files["SHA256SUMS.json"] = _canonical({
        "files_sha256": {
            name: hashlib.sha256(blob).hexdigest() for name, blob in files.items()
        },
        "source_data_sha256": model["dataset_sha256"],
    })
    output = io.BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as zipped:
        for name in sorted(files):
            zipped.writestr(name, files[name])
    return output.getvalue()
