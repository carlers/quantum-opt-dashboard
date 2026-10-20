"""Independent N20 bounded mathematical attestation BEFORE Streamlit result display.

This module is a NEW experimental UX runtime port. It does not import the
unmerged scientific PR stack; dual-checkout scientific consistency is
separately evidenced by DRAFT #96. Its exact binary64 mathematical oracle is
independent of the SCIP MILP optimizer and UX global enumeration algorithm.

It is NOT cryptographic authentication of a solver process, a parsed MILP/LP
proof, an independently surveyed shoreline, measured radio backhaul/coverage,
the manuscript's AHP/D2 elicitation, or measured lake-water outcome.
"""
from __future__ import annotations

import csv
from fractions import Fraction
from hashlib import sha256
from io import BytesIO, StringIO
from itertools import combinations
import json
import math
from zipfile import ZipFile

import numpy as np

from model import FACTOR_NAMES, NOTEBOOK_WEIGHTS, PAPER_WEIGHTS
from mvp_audit import EXPECTED_GEOJSON_SHA256, canonical, check_selected
from wireless_topology import GLOBAL_MODE, LOCAL_MODE

MAX_SUBSETS = 200_000
SCHEMA = 1


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("Independent current-run attestation: " + reason)


def digest(obj: object) -> str:
    return sha256(canonical(obj)).hexdigest()


def model_identity(instance, model: dict, graph) -> str:
    """Rebind declared model to the ACTUAL compiled instance, never a UI SHA alone."""
    require(isinstance(model, dict), "active model must be a JSON object")
    active = dict(model)
    supplied_sha = active.pop("model_fingerprint_sha256", None)
    require(supplied_sha == digest(active), "active compiled model fingerprint mismatch")
    require(model.get("dataset_sha256") == EXPECTED_GEOJSON_SHA256,
            "source 5417-feature GeoJSON SHA not pinned")
    n = len(instance.free_indices)
    require(n == 20 and len(instance.fixed_indices) == 15 and
            len(instance.coords) == 35 and type(instance.budget) is int,
            "original 20 free and all 15 fixed station identities required")
    k = instance.budget
    require(0 <= k <= n and math.comb(n, k) <= MAX_SUBSETS,
            "bounded N20/K mathematical attestation limit exceeded")
    mode = model.get("settings", {}).get("connectivity_mode")
    require(mode in (LOCAL_MODE, GLOBAL_MODE), "actual connectivity mode not modeled")
    settings = model["settings"]
    require(settings["candidate_sites_n"] == n and settings["new_sensors_k"] == k,
            "current K or candidate count differs from model")
    require(settings["scip_time_limit_seconds"] == 30
            and type(settings["beta"]) in (float, int)
            and type(settings["delta"]) in (float, int)
            and 0 <= settings["beta"] <= 10 and 0 <= settings["delta"] <= 10,
            "solver/interaction controls changed")
    weights = settings["eight_factor_weights"]
    require(len(weights) == len(FACTOR_NAMES) == 8 and
            all(type(w) in (int, float) and math.isfinite(w) and w >= 0 for w in weights)
            and sum(weights) > 0, "source eight-factor weight definitions invalid")
    selected_preset = settings["weights_source"]
    if selected_preset.startswith("Notebook"):
        require(weights == [float(w) for w in NOTEBOOK_WEIGHTS], "notebook weight preset altered")
    elif selected_preset.startswith("Paper"):
        require(weights == [float(w) for w in PAPER_WEIGHTS], "paper weight preset altered")
    else:
        require(selected_preset.startswith("Custom"), "unknown current weight source")
    require(model["objective"]["linear_float64_hex"] ==
            [float(v).hex() for v in instance.linear] and
            model["objective"]["quadratic_terms"] == [
                {"i": int(i), "j": int(j), "q_float64_hex": float(q).hex()}
                for i, j, q in instance.quadratic
            ] and model["objective"]["sense"] == "minimize",
            "full objective coefficient bytes differ from current solver input")
    mapping = model["mapping"]
    require(mapping["free_master_feature_positions"] ==
            [int(i) for i in instance.free_indices] and
            mapping["fixed_master_feature_positions"] ==
            [int(i) for i in instance.fixed_indices] and
            mapping["projected_coords_easting_northing_m"] ==
            [[float(v) for v in point] for point in instance.coords],
            "current ordered station ids/coordinates changed")
    require(model["d_max_m_float64_hex"] == float(instance.d_max).hex()
            and math.isfinite(instance.d_max) and instance.d_max > 0,
            "wireless range / Dmax is stale")
    constraints = model["constraints"]
    require(constraints["budget_rhs"] == k
            and constraints["fixed_neighbor_flags"] ==
            [int(x) for x in instance.fixed_neighbors]
            and constraints["free_neighbors"] ==
            [list(map(int, ns)) for ns in instance.neighbors],
            "actual original one-hop rules changed")
    require(set(map(int, instance.free_indices)).isdisjoint(map(int, instance.fixed_indices)),
            "existing stations collide with free candidate positions")
    if mode == GLOBAL_MODE:
        require(graph is not None and graph.n_free == n and graph.n_fixed == 15
                and model.get("wireless_graph") == graph.as_record(),
                "active global graph differs from verified modeled graph")
        require(constraints["global_path_connectivity"] and
                model["problem"] == "notebook_derived_water_quality_global_network_counterfactual",
                "global topology mislabeled as original local")
        require(graph.neighbors and len(graph.neighbors) == 35,
                "all 15 original fixed nodes must be explicit")
        # Reconstruct adjacency from every modeled edge instead of trusting
        # the graph's cached neighbor arrays.
        adjacency = [set() for _ in range(35)]
        seen = set()
        for i, j in graph.edges:
            require(type(i) is int and type(j) is int and 0 <= i < j < 35
                    and (i, j) not in seen, "fabricated/reversed/duplicate modeled link")
            seen.add((i, j))
            adjacency[i].add(j)
            adjacency[j].add(i)
        require(tuple(tuple(sorted(a)) for a in adjacency) == graph.neighbors,
                "graph neighbor arrays do not correspond to direct links")
        for i in range(n):
            require(tuple(sorted(j for j in adjacency[i] if j < n))
                    == tuple(instance.neighbors[i])
                    and int(any(j >= n for j in adjacency[i]))
                    == int(instance.fixed_neighbors[i]),
                    "global direct links disagree with actual original source one-hop graph")
    else:
        require(graph is None and "wireless_graph" not in model
                and constraints["global_path_connectivity"] is False,
                "source-local cannot impersonate global or import an old graph")
    return mode


def _active_connected(graph, subset: tuple[int, ...], n: int) -> bool:
    """Separate union-find implementation from UX graph traversal/BFS."""
    active = set(subset) | set(range(n, n + graph.n_fixed))
    parent = {i: i for i in active}

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in graph.edges:
        if i in active and j in active:
            parent[find(i)] = find(j)
    return len({find(i) for i in active}) == 1


def _local_connected(instance, subset: tuple[int, ...]) -> bool:
    selected = set(subset)
    return all(
        bool(instance.fixed_neighbors[i])
        or any(j in selected for j in instance.neighbors[i])
        for i in subset
    )


def exact_bounded_oracle(instance, mode: str, graph) -> dict:
    """Integer-scaled exact objective and distinct feasibility algorithm.

    Score coefficients are interpreted as EXACT fractions of their original
    binary64 values. Close but different solutions are NOT collapsed by a
    score-tolerance threshold. The oracle retains the first lexicographic
    witness, but any genuinely exact tied optimum can be independently proven.
    """
    n, k = len(instance.free_indices), instance.budget
    total = math.comb(n, k)
    require(n == 20 and total <= MAX_SUBSETS, "exhaustive N20 limit exceeded")
    coeffs = [Fraction.from_float(float(x)) for x in instance.linear]
    pairs = [(int(i), int(j), Fraction.from_float(float(q)))
             for i, j, q in instance.quadratic]
    require(all(math.isfinite(float(v)) for v in instance.linear)
            and all(math.isfinite(float(v)) for _, _, v in pairs),
            "nonfinite actual objective inputs")
    denominator = max((v.denominator for v in coeffs + [p[2] for p in pairs]), default=1)
    linear = [int(v * denominator) for v in coeffs]
    quadratic = [(i, j, int(v * denominator)) for i, j, v in pairs]
    best_score, best_set, count = None, None, 0
    feasible_hash = sha256()
    for subset in combinations(range(n), k):
        if not (_active_connected(graph, subset, n)
                if mode == GLOBAL_MODE else _local_connected(instance, subset)):
            continue
        count += 1
        feasible_hash.update((",".join(map(str, subset)) + "\n").encode("ascii"))
        chosen = set(subset)
        score = (sum(linear[i] for i in subset)
                 + sum(v for i, j, v in quadratic if i in chosen and j in chosen))
        if best_score is None or score < best_score:
            best_score, best_set = score, subset
    return {
        "combination_count": total,
        "feasible_count": count,
        "feasible_set_sha256": feasible_hash.hexdigest(),
        "exact_selected_indices": list(best_set) if best_set is not None else None,
        "exact_numerator": str(best_score) if best_score is not None else None,
        "exact_denominator": str(denominator) if best_score is not None else None,
        "score_approximation": best_score / denominator if best_score is not None else None,
    }


def exact_selection_objective(instance, selected_indices) -> Fraction:
    """Exactly score the selected subset from the ACTUAL binary64 coefficients.

    This is intentionally separate from the integer-scaled search: equality of
    exact rational values accepts genuinely tied optima, but no float score
    tolerance can turn a slightly worse feasible selection into an optimum.
    """
    selected = set(selected_indices)
    return (
        sum((Fraction.from_float(float(instance.linear[i])) for i in selected),
            Fraction(0))
        + sum((Fraction.from_float(float(q)) for i, j, q in instance.quadratic
               if i in selected and j in selected), Fraction(0))
    )


def inspect_archive(model: dict, mode: str, chosen, metrics: dict,
                    archive: bytes, csv_bytes: bytes, lp_bytes: bytes | None,
                    graph) -> str:
    """Re-read every exported byte BEFORE it becomes displayable state."""
    require(type(archive) is bytes and len(archive) <= 2_000_000,
            "missing or oversized UI evidence archive")
    with ZipFile(BytesIO(archive)) as zipped:
        names = zipped.namelist()
        expected = {"model.json", "result.json", "selected_sites.csv", "SHA256SUMS.json"}
        expected.add("actual_scip_model.lp" if mode == LOCAL_MODE else "wireless_graph.json")
        require(len(set(names)) == len(names) and set(names) == expected,
                "unexpected, duplicated, or missing evidence bundle member")
        checksums = json.loads(zipped.read("SHA256SUMS.json"))["files_sha256"]
        require(set(checksums) == expected - {"SHA256SUMS.json"}, "missing member hashes")
        for file in checksums:
            require(sha256(zipped.read(file)).hexdigest() == checksums[file],
                    "evidence ZIP checksum mismatch: " + file)
        require(json.loads(zipped.read("model.json")) == model,
                "ZIP model does not match current compiled backend input")
        require(zipped.read("selected_sites.csv") == csv_bytes,
                "ZIP selected-site CSV is stale")
        exported = json.loads(zipped.read("result.json"))
        require(exported["model_fingerprint_sha256"] == model["model_fingerprint_sha256"],
                "ZIP solver result is bound to a different model")
        if mode == GLOBAL_MODE:
            require(json.loads(zipped.read("wireless_graph.json")) == graph.as_record()
                    and exported["graph_fingerprint_sha256"] == graph.fingerprint
                    and exported["search"] == metrics and
                    exported["connectivity_mode"] == GLOBAL_MODE,
                    "global ZIP graph/status/report differs from actual backend")
        else:
            require(type(lp_bytes) is bytes and len(lp_bytes.strip()) > 0
                    and len(lp_bytes) < 1_000_000
                    and zipped.read("actual_scip_model.lp") == lp_bytes,
                    "real local SCIP LP bytes do not match the optimizer export")
            require(exported["scip_status"] == metrics["status"]
                    and exported["scip_optimal_proven"] == metrics["optimal"]
                    and math.isclose(exported["scip_original_objective"], metrics["energy"],
                                     rel_tol=0, abs_tol=1e-8),
                    "local SCIP exported status or reported score differs")
        expected_sites = [i for i, flag in enumerate(chosen) if flag] if chosen is not None else []
        rows = list(csv.DictReader(StringIO(csv_bytes.decode("utf-8"))))
        require([int(row["local_position"]) for row in rows] == expected_sites
                and [int(row["master_feature_position"]) for row in rows] ==
                [model["mapping"]["free_master_feature_positions"][i] for i in expected_sites],
                "exported CSV station indices do not match current selected result")
    return sha256(archive).hexdigest()


def attest_current_result(instance, model, graph, chosen, metrics, archive: bytes,
                          csv_bytes: bytes, lp_bytes: bytes | None = None) -> dict:
    """Fail closed if model, status, graph, selected sites or ZIP are inconsistent."""
    mode = model_identity(instance, model, graph)
    require(isinstance(metrics, dict) and type(metrics.get("optimal")) is bool
            and type(metrics.get("status")) is str, "untrusted solver outcome format")
    if chosen is None:
        require(mode == GLOBAL_MODE and metrics["optimal"] is False
                and metrics["status"] in (
                    "time_limit_no_certified_optimum",
                    "infeasible_certified",
                    "infeasible_certified_full_graph_disconnected",
                ), "missing selected sites cannot represent a certified optimum")
        selected = None
    else:
        selected = np.asarray(chosen)
        require(selected.shape == (20,) and
                selected.dtype.kind in "biu" and np.isin(selected, (0, 1)).all()
                and int(selected.sum()) == instance.budget,
                "selected original station bits fail K and binary requirements")
    oracle = exact_bounded_oracle(instance, mode, graph)
    if selected is None:
        if metrics["status"].startswith("infeasible"):
            require(oracle["feasible_count"] == 0, "false infeasibility status")
        # A true timeout cannot be promoted to infeasible/optimal from a label.
        require(not metrics.get("optimal"), "timeout is not certified optimum")
    else:
        selected_ids = np.flatnonzero(selected).tolist()
        require((_active_connected(graph, tuple(selected_ids), 20)
                 if mode == GLOBAL_MODE else _local_connected(instance, tuple(selected_ids))),
                "reported selected locations do not satisfy current actual graph")
        require(oracle["feasible_count"] > 0, "selected sites despite proved infeasibility")
        observed_energy = float(sum(float(instance.linear[i]) for i in selected_ids)
                                + sum(float(q) for i, j, q in instance.quadratic
                                      if i in selected_ids and j in selected_ids))
        require(type(metrics.get("energy")) in (int, float)
                and math.isfinite(metrics["energy"])
                and math.isclose(metrics["energy"], observed_energy, rel_tol=0, abs_tol=1e-8),
                "optimizer-reported energy differs from independent objective")
        if metrics["optimal"]:
            best_exact = Fraction(
                int(oracle["exact_numerator"]), int(oracle["exact_denominator"])
            )
            require(metrics["status"] == ("optimal_exhaustive" if mode == GLOBAL_MODE else "optimal")
                    and exact_selection_objective(instance, selected_ids) == best_exact,
                    "unproved optimum or false solver status")
        else:
            require(mode == LOCAL_MODE and metrics["status"] in ("timelimit", "gaplimit")
                    and "optimal" not in metrics["status"],
                    "time-limited SCIP incumbent cannot impersonate optimum")
        if mode == GLOBAL_MODE:
            require(metrics.get("solver") == "exact_exhaustive_enumeration"
                    and metrics.get("combinations_examined") == oracle["combination_count"]
                    and metrics.get("feasible_combinations") == oracle["feasible_count"]
                    and metrics.get("selected_local_positions") == selected_ids
                    and metrics.get("graph_fingerprint_sha256") == graph.fingerprint,
                    "global optimizer did not exhaustively certify active source graph")
    if mode == GLOBAL_MODE and metrics["status"].startswith("infeasible"):
        require(metrics.get("solver") in ("exact_graph_precheck", "exact_exhaustive_enumeration"),
                "global infeasibility proof requires real graph or full enumeration")
    actual_zip_sha = inspect_archive(model, mode,
                                     selected.tolist() if selected is not None else None,
                                     metrics, archive, csv_bytes, lp_bytes, graph)
    selected_bits = selected.tolist() if selected is not None else None
    evidence = {
        "schema_version": SCHEMA,
        "active_model_fingerprint_sha256": model["model_fingerprint_sha256"],
        "dataset_sha256": model["dataset_sha256"],
        "connectivity_mode": mode,
        "active_graph_sha256": graph.fingerprint if graph is not None else None,
        "chosen_binary20": selected_bits,
        "solver_metrics": metrics,
        "actual_evidence_zip_sha256": actual_zip_sha,
        "mathematical_verifier": oracle,
        "strictly_bound_to_compiled_current_run": True,
        "source_mathematical_only_manuscript_parity": False,
        "real_radio_water_quality_validation": False,
        "independent_scip_execution_log_or_lp_structure_authenticated": False,
    }
    return evidence


def check_visible_result(instance, model, graph, current) -> bool:
    """Before EACH map/ZIP render, reject changes to attested current run bytes.

    State-held SHA digests detect ordinary stale/tampered state, but they are
    NOT signatures against an adversary able to rewrite all state members.
    """
    try:
        mode = model_identity(instance, model, graph)
        if not isinstance(current, dict):
            return False
        proof = current["attestation"]
        # State-local checksum detects accidental/tampered oracle verdict edits;
        # it is NOT a signature against a user able to rewrite all state.
        if (current["attestation_sha256"] != digest(proof)
                or current["fingerprint"] != model["model_fingerprint_sha256"]
                or proof["active_model_fingerprint_sha256"] != current["fingerprint"]
                or proof["connectivity_mode"] != mode
                or proof["active_graph_sha256"] != (
                    graph.fingerprint if graph is not None else None
                )
                or proof["chosen_binary20"] != current["chosen"]
                or proof["solver_metrics"] != current["metrics"]
                or sha256(current["zip"]).hexdigest() != proof["actual_evidence_zip_sha256"]):
            return False
        # The UI uses the independent audit to render objective metrics,
        # station rows and locations; recompute it from the CURRENT compiled
        # instance so changing these display-only fields cannot bypass proof.
        if current["chosen"] is None:
            if current["independent"] is not None:
                return False
        else:
            fresh_audit = check_selected(
                instance, np.asarray(current["chosen"], dtype=int),
                current["metrics"], model,
            )
            if current["independent"] != fresh_audit:
                return False
        # Any custom or topology change forces a new independent solve.
        return proof["strictly_bound_to_compiled_current_run"] is True
    except (KeyError, ValueError, TypeError, AttributeError, IndexError, AssertionError):
        return False
