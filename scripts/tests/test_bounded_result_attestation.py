"""Adversarial tiny-model checks for bounded read-only result attestation."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts import bounded_result_attestation as proof
from scripts import science_claim_gate as gate
from scripts.scientific_dashboard_adapter import scenario_signature


def mini_model() -> dict:
    return {
        "candidate_master_feature_positions": [1, 2, 3],
        "fixed_master_feature_positions": [4, 5],
        "factor_column_names": [
            "a1_river_proximity", "a2_runoff_proximity", "b1_fishpen_density",
            "b2_hypoxic_proximity", "c1_bathymetric_depressions",
            "c2_outlet_proximity", "d1_boatramp_proximity", "d2_road_proximity",
        ],
        "factor_weights_float64_hex": [float(0.125).hex()] * 8,
        "linear_float64_hex": [float(x).hex() for x in [-3, -2, -1]],
        "quadratic_ij_float64_hex": [],
        "site_coords_epsg32651_float64_hex": [
            [float(330000 + i).hex(), float(1500000).hex()]
            for i in range(5)
        ],
        "dataset_sha256": gate.EXPECTED_DATA_SHA,
        "budget_exact": 1,
        "free_neighbor_indices": [[1], [0, 2], [1]],
        "fixed_neighbor_flags": [1, 0, 1],
    }


def local():
    return {
        "model_input": mini_model(),
        "topology_mode": "local_one_hop",
        "graph_sha256": "a" * 64,  # source graph must be verified upstream
        "input_origin": "exploratory",
        "solver_backend": "scip",
        "controls": {},
    }


def global_graph():
    return {
        "node_count": 5,
        "undirected_edges": [[0, 3], [0, 4]],
    }


def global_scenario():
    s = local()
    s["model_input"]["free_neighbor_indices"] = [[], [], []]
    s["model_input"]["fixed_neighbor_flags"] = [1, 0, 0]
    s["topology_mode"] = "global_all_stations"
    s["solver_backend"] = "exact_enumeration"
    g = global_graph()
    s["graph_sha256"] = gate.full_manifest_digest(g)
    return s, g


def report(s, selected=None, energy=None, status="time_limit"):
    return {
        "scenario_sha256": scenario_signature(s),
        "selected_local_positions": selected,
        "reported_energy": energy,
        "reported_solver_status": status,
    }


class BoundedAttestationTests(unittest.TestCase):
    def test_local_independent_mathematical_optimum(self):
        s = local()
        output = proof.attest_bounded_result(s, report(s, [0], -3, "optimal"))
        self.assertEqual(output["independent_optimal_set"], [0])
        self.assertEqual(output["feasible_subsets"], 2)
        self.assertEqual(output["enumerated_subsets"], 3)
        self.assertTrue(output["reported_selection_is_independently_optimal"])
        self.assertFalse(output["solver_execution_and_logs_authenticated"])
        self.assertFalse(output["real_radio_links_or_physical_monitoring_validated"])

    def test_local_neighborless_selected_candidate_rejected(self):
        s = local()
        with self.assertRaisesRegex(ValueError, "violates"):
            proof.attest_bounded_result(s, report(s, [1], -2, "optimal"))

    def test_false_optimality_and_wrong_objective_rejected(self):
        s = local()
        with self.assertRaisesRegex(ValueError, "claimed optimal|Claimed optimal"):
            proof.attest_bounded_result(s, report(s, [2], -1, "optimal"))
        with self.assertRaisesRegex(ValueError, "objective"):
            proof.attest_bounded_result(s, report(s, [0], -100, "optimal"))

    def test_time_limited_feasible_incumbent_not_relabelled_optimal(self):
        s = local()
        out = proof.attest_bounded_result(s, report(s, [2], -1, "time_limit"))
        self.assertFalse(out["reported_selection_is_independently_optimal"])
        self.assertEqual(out["reported_solver_status_unattested"], "time_limit")
        self.assertFalse(out["solver_execution_and_logs_authenticated"])
        no_incumbent = proof.attest_bounded_result(s, report(s))
        self.assertIsNone(no_incumbent["reported_selection"])
        self.assertTrue(no_incumbent["feasible_subsets"] > 0)
        self.assertFalse(no_incumbent["infeasibility_independently_proved"])

    def test_falsely_infeasible_report_rejected(self):
        s = local()
        with self.assertRaisesRegex(ValueError, "Reported infeasible"):
            proof.attest_bounded_result(s, report(s, status="infeasible"))

    def test_true_global_all_fixed_connected_with_one_bridge(self):
        s, g = global_scenario()
        out = proof.attest_bounded_result(
            s, report(s, [0], -3, "optimal_exhaustive"), g
        )
        self.assertEqual(out["feasible_subsets"], 1)
        self.assertTrue(out["reported_selection_is_independently_optimal"])
        self.assertEqual(out["independent_optimal_set"], [0])
        self.assertEqual(out["modeled_topology_input_status"],
                         "explicit_digest_matched_modeled_edges_not_measured")

    def test_global_disconnected_mandatory_fixed_proved_infeasible(self):
        s, _ = global_scenario()
        g = {"node_count": 5, "undirected_edges": [[0, 3]]}
        s["graph_sha256"] = gate.full_manifest_digest(g)
        out = proof.attest_bounded_result(
            s, report(s, status="infeasible"), g
        )
        self.assertEqual(out["feasible_subsets"], 0)
        self.assertTrue(out["infeasibility_independently_proved"])
        self.assertIsNone(out["independent_optimal_set"])

    def test_global_untrusted_graph_sha_rejected(self):
        s, g = global_scenario()
        g["undirected_edges"] = [[0, 3]]
        with self.assertRaisesRegex(ValueError, "digest"):
            proof.attest_bounded_result(s, report(s, [0], -3, "optimal_exhaustive"), g)

    def test_global_free_fixed_flags_cannot_be_fabricated(self):
        s, g = global_scenario()
        s["model_input"]["fixed_neighbor_flags"][2] = 1
        with self.assertRaisesRegex(ValueError, "fixed link flags"):
            proof.attest_bounded_result(s, report(s, [0], -3, "optimal_exhaustive"), g)

    def test_global_duplicate_edges_and_missing_fixed_rejected(self):
        s, _ = global_scenario()
        g = {"node_count": 5, "undirected_edges": [[0, 3], [0, 3], [0, 4]]}
        s["graph_sha256"] = gate.full_manifest_digest(g)
        with self.assertRaisesRegex(ValueError, "unique"):
            proof.attest_bounded_result(s, report(s, [0], -3, "optimal_exhaustive"), g)
        s, _ = global_scenario()
        g = {"node_count": 4, "undirected_edges": [[0, 3]]}
        s["graph_sha256"] = gate.full_manifest_digest(g)
        with self.assertRaisesRegex(ValueError, "Missing existing"):
            proof.attest_bounded_result(s, report(s, status="infeasible"), g)

    def test_global_scip_impersonation_and_local_fake_enumeration_rejected(self):
        s, g = global_scenario()
        with self.assertRaisesRegex(ValueError, "must not impersonate"):
            proof.attest_bounded_result(s, report(s, [0], -3, "optimal"), g)
        s = local()
        with self.assertRaisesRegex(ValueError, "cannot impersonate"):
            proof.attest_bounded_result(s, report(s, [0], -3, "optimal_exhaustive"))

    def test_stale_model_and_dmax_change_rejected(self):
        s = local()
        old = report(s, [0], -3, "optimal")
        s["model_input"]["d_max_m_float64_hex"] = float(1000).hex()
        with self.assertRaisesRegex(ValueError, "Stale"):
            proof.attest_bounded_result(s, old)
        s = local()
        s["model_input"]["linear_float64_hex"][0] = float(-10).hex()
        with self.assertRaisesRegex(ValueError, "Stale"):
            proof.attest_bounded_result(s, old)

    def test_duplicate_selection_nan_and_spoofed_fields_rejected(self):
        s = local()
        r = report(s, [0, 0], -3, "optimal")
        with self.assertRaisesRegex(ValueError, "selected"):
            proof.attest_bounded_result(s, r)
        r = report(s, [0], float("nan"), "optimal")
        with self.assertRaisesRegex(ValueError, "objective"):
            proof.attest_bounded_result(s, r)
        r = report(s, [0], -3, "optimal")
        r["physically_validated"] = True
        with self.assertRaisesRegex(ValueError, "forged"):
            proof.attest_bounded_result(s, r)

    def test_invalid_local_adjacency_refused(self):
        s = local()
        s["model_input"]["free_neighbor_indices"][1] = []
        with self.assertRaisesRegex(ValueError, "symmetric"):
            proof.attest_bounded_result(s, report(s, status="time_limit"))

    def test_large_search_domain_fails_closed(self):
        s = local()
        model = deepcopy(s["model_input"])
        model["candidate_master_feature_positions"] = list(range(21))
        model["fixed_master_feature_positions"] = [21]
        model["site_coords_epsg32651_float64_hex"] = [
            [float(i).hex(), float(0).hex()] for i in range(22)
        ]
        model["linear_float64_hex"] = [float(i).hex() for i in range(21)]
        model["quadratic_ij_float64_hex"] = []
        model["free_neighbor_indices"] = [[] for _ in range(21)]
        model["fixed_neighbor_flags"] = [1] * 21
        model["budget_exact"] = 10
        s["model_input"] = model
        with self.assertRaisesRegex(ValueError, "Unbounded instance"):
            proof.attest_bounded_result(s, report(s))


if __name__ == "__main__":
    unittest.main()
