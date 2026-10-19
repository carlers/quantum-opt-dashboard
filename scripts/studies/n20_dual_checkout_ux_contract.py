"""Read-only science / separate-UX exported N20 global evidence compatibility audit.

Only a dual-checkout CI with independently executed, source-verified producers
can support the provenance asserted by the tool-run combination. An attacker
can fabricate two self-consistent JSON files; this bridge is NOT a signature
service, not an authenticated current user session, not a Streamlit security
boundary and not a physically certified lake monitoring plan.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import math

from scripts import science_claim_gate as gate
from scripts import n20_numerical_identity_policy as precision
from scripts.n20_full_global_source_geometry import (
    EXPECTED_GLOBAL_FEASIBLE, EXPECTED_GLOBAL_FEASIBLE_SHA256,
    EXPECTED_GLOBAL_WINNER, _neighbors, full_global_subset_oracle,
)

SCHEMA = 1
UX_COMMIT_EXPECTED = "8752d17372d9d4dd544acbbfd686b4bb45e33f40"
SCIENCE_K = 5
EXPECTED_EDGES = {"free_free": 11, "free_fixed": 34, "fixed_fixed": 17}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def compare_source_global_to_ux(
    source_reference: dict,
    science_global: dict,
    ux_global: dict,
    *,
    ux_commit_sha: str,
) -> dict:
    """Require two freshly compiled backends to agree on source geometric math.

    Identical objective bytes are not assumed across different CPU/NumPy
    processes: describe any known low-bit variants; never claim that different
    bitwise coefficient manifests or solver executions are interchangeable.
    """
    _require(ux_commit_sha == UX_COMMIT_EXPECTED, "UX reviewed source commit is not pinned")
    _require(isinstance(source_reference, dict)
             and isinstance(science_global, dict)
             and isinstance(ux_global, dict), "Both backend records required")
    # This exact source provenance is separately confirmed by cold SCIP and
    # GeoJSON/S4 tools in the dual-checkout CI. This bridge also rejects
    # incompatible self-declarations even before comparing outcomes.
    source_model = source_reference["model_input"]
    _require(gate.full_manifest_digest(source_model)
             == source_reference["model_input_sha256"], "Source model checksum mismatch")
    _require(science_global["source_original_model_input_sha256"]
             == source_reference["model_input_sha256"], "Science proof is not for current original source")
    _require(science_global["source_data_sha256"] == gate.EXPECTED_DATA_SHA,
             "Science source dataset differs")
    _require(science_global["objective_fingerprint_sha256"]
             == gate.objective_fingerprint(source_model),
             "Science score function differs from source")
    _require(science_global.get("measured_radio_links_or_fixed_backhaul_validated") is False
             and science_global.get("manuscript_D2_AHP_reconciled") is False
             and science_global.get("physical_waterbody_or_transport_calibrated") is False,
             "Unsubstantiated science/physical approval flag")
    _require(science_global.get("distinct_from_original_notebook_local_one_hop") is True,
             "Full global topology mislabeled as historical original local model")

    graph = science_global["full_global_graph"]
    _neighbors(graph)  # reject forged duplicated, bad nodes and links
    _require(graph["node_count"] == 35, "Expected exactly 20 original and 15 mandatory fixed sites")
    science_graph_sha = gate.full_manifest_digest(graph)
    _require(science_global["graph_manifest_sha256"] == science_graph_sha,
             "Science graph digest disagrees with complete source-proxy edges")
    _require(science_global["modeled_edge_counts"] == EXPECTED_EDGES,
             "Science modeled 35-site edge counts changed")
    _require(science_global["original_source_local_feasible_subsets"] == 1077,
             "Science local reference canary changed")
    source_oracle = science_global["global_exact_union_find_oracle"]
    _require(source_oracle["all_combinations"] == 15504
             and source_oracle["feasible_subsets"] == EXPECTED_GLOBAL_FEASIBLE
             and source_oracle["feasible_set_sha256"] == EXPECTED_GLOBAL_FEASIBLE_SHA256
             and source_oracle["independently_optimal_indices"] == EXPECTED_GLOBAL_WINNER,
             "Science global feasible region or optimum canaries differ")
    independent = science_global["independent_bounded_backend_check"]
    _require(
        independent["scenario_sha256"] == science_global["global_scenario_sha256"]
        and independent["modeled_graph_sha256"] == science_graph_sha
        and independent["topology_mode"] == "global_all_stations"
        and independent["feasible_subsets"] == source_oracle["feasible_subsets"]
        and independent["feasible_sets_sha256"] == source_oracle["feasible_set_sha256"]
        and independent["reported_selection_is_independently_optimal"] is True
        and independent["solver_execution_and_logs_authenticated"] is False
        and independent["real_radio_links_or_physical_monitoring_validated"] is False,
        "Science source mathematical attestation does not support the global assertion"
    )

    # User-interface branch export is generated by executing UX's own real
    # model/load_data/make_instance/graph and exact_global_search, NOT by a
    # copy of this science graph record or a mocked UI input.
    _require(ux_global["status"] == "notebook_derived_exploratory_global_wireless_proxy",
             "UX provenance must remain exploratory")
    _require(ux_global["source_dataset_sha256"] == gate.EXPECTED_DATA_SHA,
             "UX data bytes disagree with independent science")
    _require(ux_global["source_free_master_feature_positions"]
             == source_model["candidate_master_feature_positions"]
             and ux_global["source_fixed_master_feature_positions"]
             == source_model["fixed_master_feature_positions"],
             "UX original candidate/fixed ordered identity or count changed")
    _require(ux_global["source_dmax_float64_hex"] == source_model["d_max_m_float64_hex"],
             "UX source Dmax does not match pinned original graph")
    ux_graph = ux_global["modeled_geometry_graph"]
    _require(ux_graph["schema_version"] == 1
             and ux_graph["mode"] == "all_stations_connected"
             and ux_graph["site_order"] == "original_free_then_original_fixed"
             and ux_graph["free_count"] == 20 and ux_graph["fixed_count"] == 15,
             "UX full original fixed network not represented")
    _require(ux_graph["undirected_edges"] == graph["undirected_edges"],
             "UX and science geometry differ at actual individual modeled link")
    _require(ux_global["all_direct_link_counts"] == EXPECTED_EDGES,
             "UX edge family counts differ from source graph")
    _require(ux_global["original_local_feasible_count"] == 1077
             and ux_global["original_local_feasible_sha256"]
             == source_reference["feasible_site_sets_sha256"],
             "UX original local one-hop feasible-set membership differs")
    _require(ux_global["full_source_K5_subsets"] == 15504
             and ux_global["all_stations_global_feasible_count"] == EXPECTED_GLOBAL_FEASIBLE
             and ux_global["all_stations_global_feasible_sha256"]
             == EXPECTED_GLOBAL_FEASIBLE_SHA256,
             "UX global full mandatory-fixed connectivity proof differs")
    _require(ux_global["globally_connected_selected_indices"] == EXPECTED_GLOBAL_WINNER,
             "UX selected global result does not equal independently proved optimum")
    search = ux_global["search"]
    _require(search["status"] == "optimal_exhaustive"
             and search["solver"] == "exact_exhaustive_enumeration"
             and search["optimal"] is True
             and search["combinations_examined"] == 15504
             and search["feasible_combinations"] == EXPECTED_GLOBAL_FEASIBLE
             and search["selected_local_positions"] == EXPECTED_GLOBAL_WINNER,
             "UX solver status, selected output or exhaustive certificate is false")
    _require(search["graph_fingerprint_sha256"] == ux_graph["fingerprint_sha256"],
             "UX optimizer used a different graph than the reported UX export")
    _require(
        not any("actual SCIP" in text for text in ux_global.get("limitations", [])),
        "UX global exact search cannot report a fabricated SCIP run"
    )

    # Build source-like score solely for comparing UX vs science manifests.
    # The new UX model is a distinct constructed model; this is a diagnostic
    # copy, not a rewrite of either source or the UX's deployed formula.
    ux_score_model = dict(source_model)
    ux_score_model["linear_float64_hex"] = ux_global["original_objective_linear_float64_hex"]
    ux_score_model["quadratic_ij_float64_hex"] = ux_global[
        "original_objective_quadratic_ij_float64_hex"
    ]
    observed_precision = precision.diagnose_original_n20_objective_pair(
        source_model, ux_score_model
    )
    _require(observed_precision["observed_posthoc_numerical_envelope_only"],
             "UX numerical score differs beyond previously observed original source ULP modes")
    # Independently recompute the UX claim from ITS actual binary64 coefficients.
    # This does not authenticate the UX solver's execution logs.
    ux_oracle = full_global_subset_oracle(ux_score_model, graph)
    _require(ux_oracle["feasible_subsets"] == EXPECTED_GLOBAL_FEASIBLE
             and ux_oracle["feasible_set_sha256"] == EXPECTED_GLOBAL_FEASIBLE_SHA256
             and ux_oracle["independently_optimal_indices"] == EXPECTED_GLOBAL_WINNER,
             "UX score's exact independent mathematical optimum differs")
    _require(
        type(search["energy"]) in (int, float)
        and math.isfinite(search["energy"])
        and math.isclose(search["energy"], ux_oracle["best_energy_approximation"],
                         rel_tol=0, abs_tol=1e-8),
        "UX reported energy does not match independent scored objective"
    )
    _require(ux_global.get("limitations")
             and all(isinstance(v, str) for v in ux_global["limitations"]),
             "Missing non-field-validity warnings in UX export")

    return {
        "schema_version": SCHEMA,
        "scope": "read_only_two_unmerged_backends_original_source_N20_global_math",
        "science_full_model_sha256": source_reference["model_input_sha256"],
        "science_objective_sha256": gate.objective_fingerprint(source_model),
        "ux_objective_sha256": gate.objective_fingerprint(ux_score_model),
        "science_graph_edges_sha256": science_graph_sha,
        "ux_distinct_graph_fingerprint_sha256": ux_graph["fingerprint_sha256"],
        "actual_graph_edge_lists_equal": True,
        "all_mandatory_fixed_plus_K_connected_feasible_sha256": EXPECTED_GLOBAL_FEASIBLE_SHA256,
        "global_feasible_subsets": EXPECTED_GLOBAL_FEASIBLE,
        "local_one_hop_feasible_subsets": 1077,
        "selected_original_local_sites": list(EXPECTED_GLOBAL_WINNER),
        "ux_exact_objective_matches_science": observed_precision["same_exact_objective"],
        "source_vs_ux_posthoc_low_bit_diagnostic": observed_precision,
        "joint_ux_export_status": "numerically_crosschecked_exploratory_global",
        "independent_ux_exact_binary64_optimum_proved_against_exported_coefficients": True,
        "same_signed_compiled_current_user_session_established": False,
        "independent_scip_or_streamlit_session_logs_authenticated": False,
        "physical_radio_or_environmental_monitoring_validated": False,
        "paper_D2_AHP_parity_established": False,
        "solver_result_cache_reuse_authorized": False,
        "user_facing_trusted_live_export_approved": False,
        "independent_backend_source_provenance_requires_cold_ci": True,
        "ux_source_commit_pinned": ux_commit_sha,
        "note": (
            "Independent research-only cross-check of two separately executed backends. "
            "This does not install an attestor in Streamlit, verify a current user's "
            "run, equate different exact objective hashes, or validate radio and water quality."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-reference", required=True, type=Path)
    p.add_argument("--science-global", required=True, type=Path)
    p.add_argument("--ux-global", required=True, type=Path)
    p.add_argument("--ux-commit-sha", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite prior dual-stack scientific evidence")
    records = [json.loads(x.read_text(encoding="utf-8")) for x in (
        args.source_reference, args.science_global, args.ux_global
    )]
    report = compare_source_global_to_ux(
        *records, ux_commit_sha=args.ux_commit_sha,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gate.canonical(report))
    print("N20_DUAL_CHECKOUT_SCIENCE_UX " + json.dumps({
        "edge_lists_exact": report["actual_graph_edge_lists_equal"],
        "global_feasible": report["global_feasible_subsets"],
        "objective_bytes_exact": report["ux_exact_objective_matches_science"],
        "ux_score_sha": report["ux_objective_sha256"],
        "science_score_sha": report["science_objective_sha256"],
        "real_user_session_attested": False,
        "physical_RFI_and_DO_validated": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
