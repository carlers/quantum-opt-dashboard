"""Bounded, read-only proof of mathematical solver outcomes on specified inputs.

Does not verify SCIP execution logs, physical radio links, expert AHP weights,
source GIS truth, or an arbitrary unbounded optimization instance. A model may
still be a scientifically invalid proxy even when its optimum is proved.
"""
from __future__ import annotations

from hashlib import sha256
from itertools import combinations
import math

from scripts import science_claim_gate as gate
from scripts.scientific_dashboard_adapter import (
    GLOBAL_TOPOLOGY, SOURCE_TOPOLOGY, scenario_signature,
)

MAX_ENUMERATED_SUBSETS = 200_000
SCHEMA = 1
REPORTED_STATUSES = frozenset(("optimal", "optimal_exhaustive", "time_limit", "infeasible"))
REPORT_KEYS = frozenset((
    "scenario_sha256", "selected_local_positions",
    "reported_energy", "reported_solver_status",
))


def _local_links(model: dict) -> tuple[tuple[frozenset[int], ...], tuple[bool, ...]]:
    """Read source-local rule, but do not use solver-provided feasibility flags."""
    n = len(model["candidate_master_feature_positions"])
    groups = model.get("free_neighbor_indices")
    flags = model.get("fixed_neighbor_flags")
    if (not isinstance(groups, list) or len(groups) != n
            or not isinstance(flags, list) or len(flags) != n):
        raise ValueError("Original local one-hop adjacency is missing")
    if any(type(flag) is not int or flag not in (0, 1) for flag in flags):
        raise ValueError("Invalid fixed-neighbor flags")
    adj = []
    for i, row in enumerate(groups):
        if (not isinstance(row, list)
                or any(type(j) is not int or j == i or j < 0 or j >= n for j in row)
                or len(set(row)) != len(row)):
            raise ValueError("Invalid free-neighbor adjacency")
        adj.append(frozenset(row))
    if any(i not in adj[j] for i, row in enumerate(adj) for j in row):
        raise ValueError("Free-neighbor graph is not symmetric")
    return tuple(adj), tuple(bool(v) for v in flags)


def _global_graph(model: dict, graph: dict | None, expected_sha: str) -> tuple[tuple[int, ...], ...]:
    """Require exact complete edge payload including fixed/fixed connections.

    Edge inputs are modeled assumptions, NOT independently measured RF links.
    The graph's bytes must agree with the active scenario's declared digest.
    """
    n = len(model["candidate_master_feature_positions"])
    m = len(model["fixed_master_feature_positions"])
    size = n + m
    if not isinstance(graph, dict) or set(graph) != {"node_count", "undirected_edges"}:
        raise ValueError("Global topology requires complete typed modeled-edge input")
    if type(graph["node_count"]) is not int or graph["node_count"] != size:
        raise ValueError("Missing existing stations or candidates in global graph")
    if not isinstance(graph["undirected_edges"], list):
        raise ValueError("Invalid global graph edges")
    seen = set()
    adj = [set() for _ in range(size)]
    for edge in graph["undirected_edges"]:
        if (not isinstance(edge, list) or len(edge) != 2
                or any(type(i) is not int for i in edge)):
            raise ValueError("Invalid global edge representation")
        i, j = edge
        if not (0 <= i < j < size) or (i, j) in seen:
            raise ValueError("Global edges must be unique sorted unordered pairs")
        seen.add((i, j))
        adj[i].add(j)
        adj[j].add(i)
    if gate.full_manifest_digest(graph) != expected_sha:
        raise ValueError("Active global graph digest does not match modeled edge payload")
    # The currently frozen source model also contains local adjacency. Reject a
    # claimed global graph which contradicts the source's free/free and fixed flags.
    if "free_neighbor_indices" in model and "fixed_neighbor_flags" in model:
        free, fixed = _local_links(model)
        for i in range(n):
            if {j for j in adj[i] if j < n} != set(free[i]):
                raise ValueError("Global graph disagrees with supplied source free/free links")
            if bool(any(j >= n for j in adj[i])) != fixed[i]:
                raise ValueError("Global graph disagrees with supplied fixed link flags")
    return tuple(tuple(sorted(row)) for row in adj)


def _global_feasible(chosen: tuple[int, ...], adj: tuple[tuple[int, ...], ...],
                     n: int) -> bool:
    """All existing fixed nodes and all selected candidates in ONE component."""
    active = set(chosen) | set(range(n, len(adj)))
    if not active:
        return False
    reached = {min(active)}
    pending = [min(active)]
    while pending:
        for j in adj[pending.pop()]:
            if j in active and j not in reached:
                reached.add(j)
                pending.append(j)
    return reached == active


def _score(model: dict, chosen: tuple[int, ...]) -> float:
    """Rebuild the specified unpenalized binary objective without a solver."""
    linear = [float.fromhex(v) for v in model["linear_float64_hex"]]
    selected = set(chosen)
    pair = (float.fromhex(q) for i, j, q in model["quadratic_ij_float64_hex"]
            if i in selected and j in selected)
    return math.fsum([*(linear[i] for i in chosen), *pair])


def attest_bounded_result(scenario: dict, report: dict,
                          graph: dict | None = None) -> dict:
    """Prove an N<=20 small mathematical instance by independent full search.

    Claims refer only to the *specified* coefficients and graph. A claimed SCIP
    execution is never independently verified by this read-only function.
    """
    identity = scenario_signature(scenario)
    if not isinstance(report, dict) or set(report) != REPORT_KEYS:
        raise ValueError("Report has missing or forged/unexpected fields")
    if report["scenario_sha256"] != identity:
        raise ValueError("Stale or mismatched scenario/result identity")
    status = report["reported_solver_status"]
    if status not in REPORTED_STATUSES or not isinstance(status, str):
        raise ValueError("Unsupported reported solver state")
    mode = scenario["topology_mode"]
    if mode == SOURCE_TOPOLOGY and status == "optimal_exhaustive":
        raise ValueError("Exhaustive solver status cannot impersonate local SCIP")
    if mode == GLOBAL_TOPOLOGY and status == "optimal":
        raise ValueError("Global enumeration must not impersonate SCIP")
    model = scenario["model_input"]
    gate.objective_manifest(model)  # exact coefficient, identity, finite canaries
    n = len(model["candidate_master_feature_positions"])
    k = model["budget_exact"]
    total = math.comb(n, k)
    if n > 20 or total > MAX_ENUMERATED_SUBSETS:
        raise ValueError("Unbounded instance: independent mathematical proof refused")
    if mode == SOURCE_TOPOLOGY:
        if graph is not None:
            raise ValueError("Local reference uses model one-hop adjacency, not global edges")
        neighbors, fixed = _local_links(model)
        is_feasible = lambda chosen: all(
            fixed[i] or bool(neighbors[i].intersection(chosen)) for i in chosen
        )
        topology_input_status = "source_model_local_links_only"
    elif mode == GLOBAL_TOPOLOGY:
        adj = _global_graph(model, graph, scenario["graph_sha256"])
        is_feasible = lambda chosen: _global_feasible(chosen, adj, n)
        topology_input_status = "explicit_digest_matched_modeled_edges_not_measured"
    else:
        raise ValueError("Unsupported topology")
    selected = report["selected_local_positions"]
    if selected is not None:
        if (not isinstance(selected, list) or len(selected) != k
                or any(type(i) is not int or not 0 <= i < n for i in selected)
                or selected != sorted(set(selected))):
            raise ValueError("Invalid, duplicate or noncanonical selected IDs")
        chosen = tuple(selected)
        if not is_feasible(chosen):
            raise ValueError("Reported chosen station set violates active topology")
        energy = _score(model, chosen)
        measured = report["reported_energy"]
        if (type(measured) not in (float, int) or not math.isfinite(measured)
                or not math.isclose(energy, measured, rel_tol=0.0, abs_tol=1e-8)):
            raise ValueError("Reported objective does not match independent coefficients")
        if status == "infeasible":
            raise ValueError("Infeasible report must not contain a feasible incumbent")
    else:
        if report["reported_energy"] is not None or status in ("optimal", "optimal_exhaustive"):
            raise ValueError("Missing reported optimal selected set or inconsistent energy")
        chosen = None
        energy = None

    feasible_count = 0
    feasible_digest = sha256()
    best = None
    best_energy = None
    for subset in combinations(range(n), k):
        if not is_feasible(subset):
            continue
        feasible_count += 1
        feasible_digest.update((",".join(map(str, subset)) + "\n").encode("ascii"))
        objective = _score(model, subset)
        if best_energy is None or objective < best_energy - 1e-10:
            best, best_energy = subset, objective
    if status == "infeasible" and feasible_count:
        raise ValueError("Reported infeasible but exhaustive search found feasible sites")
    if status in ("optimal", "optimal_exhaustive"):
        if feasible_count == 0 or energy is None or not math.isclose(
            energy, best_energy, rel_tol=0.0, abs_tol=1e-8
        ):
            raise ValueError("Claimed optimal result disagrees with exhaustive mathematical proof")
    independently_optimal = (
        chosen is not None and best_energy is not None and
        math.isclose(energy, best_energy, rel_tol=0.0, abs_tol=1e-8)
    )
    return {
        "schema_version": SCHEMA,
        "scenario_sha256": identity,
        "objective_sha256": gate.objective_fingerprint(model),
        "model_input_sha256": gate.full_manifest_digest(model),
        "topology_mode": mode,
        "modeled_graph_sha256": scenario["graph_sha256"],
        "modeled_topology_input_status": topology_input_status,
        "enumerated_subsets": total,
        "feasible_subsets": feasible_count,
        "feasible_sets_sha256": feasible_digest.hexdigest(),
        "best_energy": best_energy,
        "independent_optimal_set": list(best) if best is not None else None,
        "reported_solver_status_unattested": status,
        "reported_selection": list(chosen) if chosen is not None else None,
        "reported_energy_independently_recomputed": energy,
        "reported_selection_is_independently_optimal": independently_optimal,
        "infeasibility_independently_proved": feasible_count == 0,
        "solver_execution_and_logs_authenticated": False,
        "real_radio_links_or_physical_monitoring_validated": False,
        "historical_manuscript_parity_established": False,
        "new_parameter_model_approved": False,
        "export_allowed_as_physically_validated_monitoring_plan": False,
        "note": ("Bounded proof of stated binary objective and provided graph only; "
                 "not SCIP log authentication, empirical connectivity or water-quality validation."),
    }


def attest_original_source_local(reference: dict) -> dict:
    """Cold N20 fixture: use the actual separately validated notebook result."""
    from scripts.run_n20_reference_notebook import verify_result
    from scripts.n20_independent_geometry_audit import certify_geometry

    verify_result(reference)
    source_graph = certify_geometry(reference)
    from scripts.scientific_dashboard_adapter import SOURCE_ORIGIN
    scenario = {
        "model_input": reference["model_input"],
        "topology_mode": SOURCE_TOPOLOGY,
        "graph_sha256": source_graph["spatial_graph_sha256"],
        "input_origin": SOURCE_ORIGIN,
        "solver_backend": "scip",
        "controls": {},
    }
    report = {
        "scenario_sha256": scenario_signature(scenario),
        "selected_local_positions": reference["selected_local_positions"],
        "reported_energy": reference["original_energy"],
        "reported_solver_status": reference["scip_status"],
    }
    proof = attest_bounded_result(scenario, report)
    if (proof["feasible_subsets"] != 1077
            or proof["feasible_sets_sha256"] != reference["feasible_site_sets_sha256"]
            or proof["independent_optimal_set"] != [0, 1, 3, 6, 7]):
        raise AssertionError("Cold source-only independent mathematical proof failed")
    return proof
