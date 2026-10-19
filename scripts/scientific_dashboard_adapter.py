"""Read-only research evidence adapter for a future water-quality dashboard.

Source evidence is recomputed server-side via the historical cold science gate.
This module does not ship a UI, verify arbitrary solver results or certify physics.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from scripts import science_claim_gate as gate

SCHEMA = 1
SOURCE_TOPOLOGY = "local_one_hop"
GLOBAL_TOPOLOGY = "global_all_stations"
SUPPORTED_TOPOLOGIES = frozenset((SOURCE_TOPOLOGY, GLOBAL_TOPOLOGY))
SUPPORTED_SOLVERS = {SOURCE_TOPOLOGY: "scip", GLOBAL_TOPOLOGY: "exact_enumeration"}
SOURCE_ORIGIN = "frozen_source_N20"
SCENARIO_KEYS = frozenset((
    "model_input", "topology_mode", "graph_sha256", "input_origin",
    "solver_backend", "controls",
))
RESULT_KEYS = frozenset(("scenario_sha256",))


def _sha256_hex(s: str) -> bool:
    return isinstance(s, str) and len(s) == 64 and all(c in "0123456789abcdef" for c in s)


def scenario_signature(scenario: dict) -> str:
    """Bind UI results to objective, topology, compiler controls and solver.

    This detects stale result reuse; it is not an authenticated solver signature.
    The future trusted backend must construct controls from actual compiled inputs.
    """
    if not isinstance(scenario, dict) or set(scenario) != SCENARIO_KEYS:
        raise ValueError("Incomplete or unexpected scenario input keys")
    mode = scenario["topology_mode"]
    if not isinstance(mode, str) or mode not in SUPPORTED_TOPOLOGIES:
        raise ValueError("Unsupported graph topology mode")
    if scenario["solver_backend"] != SUPPORTED_SOLVERS[mode]:
        raise ValueError("Solver backend does not match the modeled topology")
    if not _sha256_hex(scenario["graph_sha256"]):
        raise ValueError("Graph input requires an exact SHA-256")
    if scenario["input_origin"] not in (SOURCE_ORIGIN, "exploratory"):
        raise ValueError("Input origin not declared")
    controls = scenario["controls"]
    if not isinstance(controls, dict) or any(not isinstance(k, str) for k in controls):
        raise ValueError("Scenario controls must be a keyed manifest")
    if scenario["input_origin"] == SOURCE_ORIGIN and controls:
        raise ValueError("Custom controls cannot masquerade as frozen source inputs")
    objective_sha = gate.objective_fingerprint(scenario["model_input"])
    return sha256(gate.canonical({
        "schema_version": SCHEMA,
        "objective_sha256": objective_sha,
        "topology_mode": mode,
        "graph_sha256": scenario["graph_sha256"],
        "input_origin": scenario["input_origin"],
        "solver_backend": scenario["solver_backend"],
        "controls": controls,
    })).hexdigest()


def make_scientific_view(original: dict, s4: dict, scenario: dict,
                         result_record: dict | None = None) -> dict:
    """Recheck source evidence; never elevate manuscript/physical/solver claims.

    The result record is only a cache freshness hint, not proof of optimality.
    """
    certificate = gate.validate_evidence(original, s4)
    source_disclosure = gate.require_display_claim(certificate, gate.ALLOWED_DISPLAY_CLAIM)
    signature = scenario_signature(scenario)
    active_objective_sha = gate.objective_fingerprint(scenario["model_input"])
    source_objective_sha = certificate["source_objective_fingerprint_sha256"]
    same_objective = active_objective_sha == source_objective_sha
    source_profile = (
        same_objective
        and scenario["model_input"] == original["model_input"]
        and scenario["topology_mode"] == SOURCE_TOPOLOGY
        and scenario["graph_sha256"] == certificate["independent_geometry_sha256"]
        and scenario["input_origin"] == SOURCE_ORIGIN
        and scenario["solver_backend"] == "scip"
        and scenario["controls"] == {}
    )
    if result_record is None:
        result_visibility = "none"
    else:
        if not isinstance(result_record, dict) or set(result_record) != RESULT_KEYS:
            raise ValueError("Result record must contain only its scenario binding")
        prior = result_record["scenario_sha256"]
        if not _sha256_hex(prior):
            raise ValueError("Invalid result binding fingerprint")
        result_visibility = "bound_unverified" if prior == signature else "hide_stale"
    return {
        "schema_version": SCHEMA,
        "display_only_not_a_solver_certificate": True,
        "historical_reference_disclosure": source_disclosure,
        "active_scenario_label": (
            "Frozen source N20/K5 mathematical profile" if source_profile
            else "New exploratory mathematical scenario"
        ),
        "active_scenario_is_frozen_source_profile": source_profile,
        "active_objective_sha256": active_objective_sha,
        "source_objective_sha256": source_objective_sha,
        "same_exact_objective": same_objective,
        "raw_energy_scientific_superiority_established": False,
        "raw_energy_cross_objective_comparison_permitted": same_objective,
        "topology_mode": scenario["topology_mode"],
        "graph_sha256": scenario["graph_sha256"],
        "scenario_sha256": signature,
        "result_visibility": result_visibility,
        "current_solver_optimality_independently_verified": False,
        "source_D2_criterion": "d2_road_proximity",
        "manuscript_D2_discrepancy": "Paper describes WorldPop/population exposure; source uses road proximity.",
        "manuscript_AHP_discrepancy": "Printed Table III, Table IV and source weights are not reconciled.",
        "manuscript_status": certificate["claim_gates"]["historical_manuscript_parity"]["status"],
        "physical_status": certificate["claim_gates"]["physical_scientific_validation"]["status"],
        "wireless_disclosure": "Topology edges are geometric proxies; no measured RF/backhaul evidence.",
        "limitations": (
            "Source mathematical verification does not establish physical monitoring quality; "
            "a cache signature match does not independently verify a current solver output."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite prior evidence presentation")
    original = json.loads(args.reference.read_text(encoding="utf-8"))
    s4 = json.loads(args.provenance.read_text(encoding="utf-8"))
    certificate = gate.validate_evidence(original, s4)
    profile = {
        "model_input": original["model_input"],
        "topology_mode": SOURCE_TOPOLOGY,
        "graph_sha256": certificate["independent_geometry_sha256"],
        "input_origin": SOURCE_ORIGIN,
        "solver_backend": "scip",
        "controls": {},
    }
    view = make_scientific_view(original, s4, profile)
    if not view["active_scenario_is_frozen_source_profile"]:
        raise AssertionError("Cold original source profile failed identity gate")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gate.canonical(view))
    print("N20_DASHBOARD_SCIENCE_ADAPTER " + json.dumps({
        "active_scenario_label": view["active_scenario_label"],
        "source_objective_sha256": view["source_objective_sha256"],
        "manuscript_status": view["manuscript_status"],
        "physical_status": view["physical_status"],
        "current_solver_optimality_independently_verified": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
