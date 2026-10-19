"""Synthetic decision-boundary tests for independent science vs UX export review.

The genuine dual-backend + real Streamlit AppTest runs separately in CI;
these synthetic fixtures are not empirical source evidence.
"""
from __future__ import annotations

from copy import deepcopy
from unittest import TestCase, mock

from scripts import science_claim_gate as gate
from scripts.run_n20_reference_notebook import (
    EXPECTED_FREE_MASTER, EXPECTED_FIXED_MASTER, EXPECTED_NOTEBOOK_SHA,
)
from scripts.studies import n20_dual_checkout_ux_contract as contract


def source_input():
    n = 20
    model = {
        "model_family": "notebook_derived_laguna_N20_local_one_hop",
        "dataset_sha256": gate.EXPECTED_DATA_SHA,
        "archived_notebook_sha256": EXPECTED_NOTEBOOK_SHA,
        "budget_exact": 5,
        "candidate_master_feature_positions": list(EXPECTED_FREE_MASTER),
        "fixed_master_feature_positions": list(EXPECTED_FIXED_MASTER),
        "factor_column_names": list(gate.FACTOR_NAMES),
        "factor_weights_float64_hex": [float(w).hex() for w in gate.ORIGINAL_WEIGHTS],
        "linear_float64_hex": [float(-0.1 - i * 0.01).hex() for i in range(n)],
        "quadratic_ij_float64_hex": [[0, 1, float(.2).hex()]],
        "site_coords_epsg32651_float64_hex": [
            [float(330000+i).hex(), float(1500000+i).hex()] for i in range(35)
        ],
        "free_neighbor_indices": [[] for _ in range(n)],
        "fixed_neighbor_flags": [1] * n,
        "d_max_m_float64_hex": float(9000).hex(),
    }
    return {
        "model_input": model,
        "model_input_sha256": gate.full_manifest_digest(model),
        "feasible_site_sets_sha256": "7" * 64,
    }


def fixtures():
    source = source_input()
    model = source["model_input"]
    # Artificial graph with correct family counts; actual connectivity and
    # optimum are separately checked in cold science integration CI.
    links = (
        [[i, i + 1] for i in range(11)]
        + [[i % 20, 20 + (i % 15)] for i in range(34)]
        + [[20 + i, 20 + j] for i in range(15)
            for j in range(i + 1, 15)][:17]
    )
    # The source graph checker rejects duplicate edges. Ensure 34 unique.
    assert len({tuple(e) for e in links}) == len(links)
    graph = {"node_count": 35, "undirected_edges": links}
    gs = gate.full_manifest_digest(graph)
    best = {
        "all_combinations": 15504, "feasible_subsets": 860,
        "feasible_set_sha256": contract.EXPECTED_GLOBAL_FEASIBLE_SHA256,
        "independently_optimal_indices": list(contract.EXPECTED_GLOBAL_WINNER),
        "best_energy_approximation": -1.,
    }
    science = {
        "source_original_model_input_sha256": source["model_input_sha256"],
        "source_data_sha256": gate.EXPECTED_DATA_SHA,
        "objective_fingerprint_sha256": gate.objective_fingerprint(model),
        "measured_radio_links_or_fixed_backhaul_validated": False,
        "manuscript_D2_AHP_reconciled": False,
        "physical_waterbody_or_transport_calibrated": False,
        "distinct_from_original_notebook_local_one_hop": True,
        "full_global_graph": graph,
        "graph_manifest_sha256": gs,
        "modeled_edge_counts": dict(contract.EXPECTED_EDGES),
        "original_source_local_feasible_subsets": 1077,
        "global_exact_union_find_oracle": best,
        "global_scenario_sha256": "a" * 64,
        "independent_bounded_backend_check": {
            "scenario_sha256": "a" * 64,
            "modeled_graph_sha256": gs,
            "topology_mode": "global_all_stations",
            "feasible_subsets": 860,
            "feasible_sets_sha256": contract.EXPECTED_GLOBAL_FEASIBLE_SHA256,
            "reported_selection_is_independently_optimal": True,
            "solver_execution_and_logs_authenticated": False,
            "real_radio_links_or_physical_monitoring_validated": False,
        },
    }
    ux = {
        "status": "notebook_derived_exploratory_global_wireless_proxy",
        "source_dataset_sha256": gate.EXPECTED_DATA_SHA,
        "source_free_master_feature_positions": list(EXPECTED_FREE_MASTER),
        "source_fixed_master_feature_positions": list(EXPECTED_FIXED_MASTER),
        "source_dmax_float64_hex": model["d_max_m_float64_hex"],
        "modeled_geometry_graph": {
            "schema_version": 1, "mode": "all_stations_connected",
            "site_order": "original_free_then_original_fixed",
            "free_count": 20, "fixed_count": 15,
            "undirected_edges": deepcopy(links),
            "fingerprint_sha256": "f" * 64,
        },
        "all_direct_link_counts": dict(contract.EXPECTED_EDGES),
        "original_local_feasible_count": 1077,
        "original_local_feasible_sha256": source["feasible_site_sets_sha256"],
        "full_source_K5_subsets": 15504,
        "all_stations_global_feasible_count": 860,
        "all_stations_global_feasible_sha256": contract.EXPECTED_GLOBAL_FEASIBLE_SHA256,
        "globally_connected_selected_indices": list(contract.EXPECTED_GLOBAL_WINNER),
        "original_objective_linear_float64_hex": list(model["linear_float64_hex"]),
        "original_objective_quadratic_ij_float64_hex": deepcopy(model["quadratic_ij_float64_hex"]),
        "search": {
            "status": "optimal_exhaustive",
            "solver": "exact_exhaustive_enumeration",
            "optimal": True, "combinations_examined": 15504,
            "feasible_combinations": 860,
            "selected_local_positions": list(contract.EXPECTED_GLOBAL_WINNER),
            "graph_fingerprint_sha256": "f" * 64,
            "energy": -1.,
        },
        "limitations": ["Modeled geometry only, no measured RF."],
    }
    return source, science, ux


def audit(source, science, ux, score=-1.):
    with mock.patch.object(contract, "full_global_subset_oracle", return_value={
        "feasible_subsets": 860,
        "feasible_set_sha256": contract.EXPECTED_GLOBAL_FEASIBLE_SHA256,
        "independently_optimal_indices": list(contract.EXPECTED_GLOBAL_WINNER),
        "best_energy_approximation": score,
    }):
        return contract.compare_source_global_to_ux(
            source, science, ux, ux_commit_sha=contract.UX_COMMIT_EXPECTED
        )


class DualCheckoutDecisionTests(TestCase):
    def test_valid_synthetic_fixture_keeps_strict_disclosure_flags(self):
        a,b,c = fixtures()
        r = audit(a,b,c)
        self.assertTrue(r["actual_graph_edge_lists_equal"])
        self.assertTrue(r["ux_exact_objective_matches_science"])
        self.assertTrue(r["independent_ux_exact_binary64_optimum_proved_against_exported_coefficients"])
        self.assertFalse(r["same_signed_compiled_current_user_session_established"])
        self.assertFalse(r["solver_result_cache_reuse_authorized"])
        self.assertFalse(r["physical_radio_or_environmental_monitoring_validated"])
        self.assertFalse(r["paper_D2_AHP_parity_established"])

    def test_independent_ux_mismatched_original_free_sites_rejected(self):
        a,b,c = fixtures()
        c["source_free_master_feature_positions"][0] = 10000
        with self.assertRaisesRegex(ValueError, "candidate/fixed"):
            audit(a,b,c)

    def test_missing_mandatory_fixed_site_rejected(self):
        a,b,c = fixtures()
        c["modeled_geometry_graph"]["fixed_count"] = 14
        with self.assertRaisesRegex(ValueError, "full original"):
            audit(a,b,c)

    def test_ux_changed_real_direct_edge_rejected_not_just_counts(self):
        a,b,c = fixtures()
        c["modeled_geometry_graph"]["undirected_edges"][0] = [0, 19]
        with self.assertRaisesRegex(ValueError, "individual modeled link"):
            audit(a,b,c)

    def test_ux_changed_dmax_rejected_even_with_same_objective(self):
        a,b,c = fixtures()
        c["source_dmax_float64_hex"] = float(12000).hex()
        with self.assertRaisesRegex(ValueError, "Dmax"):
            audit(a,b,c)

    def test_ux_wrong_local_feasible_hash_rejected(self):
        a,b,c = fixtures()
        c["original_local_feasible_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "one-hop"):
            audit(a,b,c)

    def test_ux_false_global_count_or_member_sha_rejected(self):
        a,b,c = fixtures()
        c["all_stations_global_feasible_count"] = 110
        with self.assertRaisesRegex(ValueError, "mandatory-fixed"):
            audit(a,b,c)
        a,b,c = fixtures()
        c["all_stations_global_feasible_sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "mandatory-fixed"):
            audit(a,b,c)

    def test_ux_fake_optimality_or_timeout_not_treated_as_exact_proof(self):
        a,b,c = fixtures()
        c["search"]["status"] = "time_limit_no_certified_optimum"
        with self.assertRaisesRegex(ValueError, "solver status"):
            audit(a,b,c)
        a,b,c = fixtures()
        c["search"]["solver"] = "SCIP"
        with self.assertRaisesRegex(ValueError, "solver status"):
            audit(a,b,c)

    def test_ux_forged_reported_score_rejected(self):
        a,b,c = fixtures()
        c["search"]["energy"] = -900
        with self.assertRaisesRegex(ValueError, "reported energy"):
            audit(a,b,c)

    def test_original_source_or_science_evidence_tampering_rejected(self):
        a,b,c = fixtures()
        a["model_input"]["linear_float64_hex"][0] = float(1).hex()
        with self.assertRaisesRegex(ValueError, "checksum"):
            audit(a,b,c)
        a,b,c = fixtures()
        b["independent_bounded_backend_check"]["solver_execution_and_logs_authenticated"] = True
        with self.assertRaisesRegex(ValueError, "attestation"):
            audit(a,b,c)

    def test_ux_changed_unreviewed_score_even_one_ulp_fails_closed(self):
        import math
        a,b,c = fixtures()
        v = float.fromhex(c["original_objective_linear_float64_hex"][8])
        c["original_objective_linear_float64_hex"][8] = math.nextafter(v, math.inf).hex()
        with self.assertRaisesRegex(ValueError, "ULP modes"):
            audit(a,b,c)

    def test_known_low_bit_original_mode_is_diagnostic_not_cache_approval(self):
        a,b,c = fixtures()
        c["original_objective_linear_float64_hex"][9] = float.fromhex(
            c["original_objective_linear_float64_hex"][9]
        ).hex()
        # A true single ULP difference inside original site-9 empirical cap.
        import math
        v = float.fromhex(c["original_objective_linear_float64_hex"][9])
        c["original_objective_linear_float64_hex"][9] = math.nextafter(v, math.inf).hex()
        r = audit(a,b,c)
        self.assertFalse(r["ux_exact_objective_matches_science"])
        self.assertFalse(r["solver_result_cache_reuse_authorized"])
        self.assertTrue(r["source_vs_ux_posthoc_low_bit_diagnostic"]["observed_posthoc_numerical_envelope_only"])

    def test_unpinned_other_ux_revision_rejected(self):
        a,b,c = fixtures()
        with self.assertRaisesRegex(ValueError, "pinned"):
            contract.compare_source_global_to_ux(a,b,c,ux_commit_sha="e" * 40)


if __name__ == "__main__":
    import unittest
    unittest.main()
