"""Adversarial checks for the research-only future dashboard claim adapter."""
from __future__ import annotations

from copy import deepcopy
import unittest
from unittest.mock import patch

from scripts import science_claim_gate as gate
from scripts import scientific_dashboard_adapter as bridge


def model():
    return {
        "candidate_master_feature_positions": [1, 2],
        "fixed_master_feature_positions": [3],
        "factor_column_names": [
            "a1_river_proximity", "a2_runoff_proximity", "b1_fishpen_density",
            "b2_hypoxic_proximity", "c1_bathymetric_depressions",
            "c2_outlet_proximity", "d1_boatramp_proximity", "d2_road_proximity",
        ],
        "factor_weights_float64_hex": [float(.125).hex()] * 8,
        "linear_float64_hex": [float(-.2).hex(), float(-.7).hex()],
        "quadratic_ij_float64_hex": [[0, 1, float(.1).hex()]],
        "site_coords_epsg32651_float64_hex": [
            [float(x).hex(), float(y).hex()] for x, y in
            [(330000., 1500000.), (330100., 1500000.), (330200., 1500000.)]
        ],
        "budget_exact": 1,
        "dataset_sha256": gate.EXPECTED_DATA_SHA,
    }


def scenario():
    return {
        "model_input": model(),
        "topology_mode": bridge.SOURCE_TOPOLOGY,
        "graph_sha256": "a" * 64,
        "input_origin": bridge.SOURCE_ORIGIN,
        "solver_backend": "scip",
        "controls": {},
    }


def fake_certificate():
    return {
        "schema_version": gate.SCHEMA,
        "certification_scope": "source_notebook_N20_K5_mathematical_parity_only",
        "source_objective_fingerprint_sha256": gate.objective_fingerprint(model()),
        "independent_geometry_sha256": "a" * 64,
        "claim_gates": {
            "computational_source_replay": {
                "status": "verified", "display_claim": gate.ALLOWED_DISPLAY_CLAIM,
            },
            "historical_manuscript_parity": {"status": "blocked_no_authoritative_inputs"},
            "physical_scientific_validation": {"status": "blocked_no_field_calibration"},
        },
    }


class DashboardAdapterTests(unittest.TestCase):
    def view(self, s=None, result=None):
        with patch.object(gate, "validate_evidence", return_value=fake_certificate()):
            return bridge.make_scientific_view(
                {"model_input": model()}, {}, s if s is not None else scenario(), result
            )

    def test_historical_profile_is_only_a_source_calculation(self):
        out = self.view()
        self.assertTrue(out["active_scenario_is_frozen_source_profile"])
        self.assertFalse(out["current_solver_optimality_independently_verified"])
        self.assertFalse(out["raw_energy_scientific_superiority_established"])
        self.assertEqual(out["manuscript_status"], "blocked_no_authoritative_inputs")
        self.assertEqual(out["physical_status"], "blocked_no_field_calibration")
        self.assertEqual(out["source_D2_criterion"], "d2_road_proximity")
        self.assertEqual(out["result_visibility"], "none")

    def test_changed_weights_are_exploratory_not_energy_comparable(self):
        s = scenario()
        s["model_input"]["factor_weights_float64_hex"][0] = float(.2).hex()
        out = self.view(s)
        self.assertFalse(out["active_scenario_is_frozen_source_profile"])
        self.assertFalse(out["raw_energy_cross_objective_comparison_permitted"])

    def test_worldpop_relabel_cannot_impersonate_source(self):
        s = scenario()
        s["model_input"]["factor_column_names"][-1] = "d2_worldpop_population"
        self.assertFalse(self.view(s)["active_scenario_is_frozen_source_profile"])

    def test_same_objective_global_topology_still_exploratory(self):
        s = scenario()
        s.update(topology_mode=bridge.GLOBAL_TOPOLOGY, solver_backend="exact_enumeration")
        out = self.view(s)
        self.assertTrue(out["same_exact_objective"])
        self.assertFalse(out["active_scenario_is_frozen_source_profile"])
        self.assertFalse(out["current_solver_optimality_independently_verified"])

    def test_changed_graph_is_exploratory_even_with_same_objective(self):
        s = scenario()
        s["graph_sha256"] = "b" * 64
        self.assertFalse(self.view(s)["active_scenario_is_frozen_source_profile"])

    def test_custom_origin_or_controls_cannot_be_relabelled_frozen(self):
        s = scenario()
        s["input_origin"] = "exploratory"
        self.assertFalse(self.view(s)["active_scenario_is_frozen_source_profile"])
        s = scenario()
        s["controls"] = {"Dmax_m": 1000}
        with self.assertRaisesRegex(ValueError, "Custom controls"):
            self.view(s)

    def test_freshness_signature_includes_every_semantic_control(self):
        s = scenario()
        stamp = bridge.scenario_signature(s)
        self.assertEqual(self.view(s, {"scenario_sha256": stamp})["result_visibility"],
                         "bound_unverified")
        modified = deepcopy(s)
        modified["input_origin"] = "exploratory"
        modified["controls"] = {"Dmax_m": 1000}
        self.assertEqual(self.view(modified, {"scenario_sha256": stamp})["result_visibility"],
                         "hide_stale")
        self.assertNotEqual(stamp, bridge.scenario_signature(modified))

    def test_changed_topology_and_solver_invalidate_prior_result(self):
        s = scenario()
        stamp = bridge.scenario_signature(s)
        s.update(topology_mode=bridge.GLOBAL_TOPOLOGY, solver_backend="exact_enumeration")
        self.assertEqual(self.view(s, {"scenario_sha256": stamp})["result_visibility"],
                         "hide_stale")

    def test_forced_status_checkbox_or_fake_result_not_accepted(self):
        s = scenario()
        s["physically_validated"] = True
        with self.assertRaisesRegex(ValueError, "keys"):
            self.view(s)
        with self.assertRaisesRegex(ValueError, "only"):
            self.view(result={"scenario_sha256": "a" * 64, "scip_optimal": True})

    def test_unknown_solver_topology_and_corrupt_digest_fail(self):
        s = scenario()
        s["topology_mode"] = "multi_hop_unreviewed"
        with self.assertRaisesRegex(ValueError, "topology"):
            self.view(s)
        s = scenario()
        s["solver_backend"] = "scip_fake_global"
        with self.assertRaisesRegex(ValueError, "Solver"):
            self.view(s)
        s = scenario()
        s["graph_sha256"] = "not-a-sha"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.view(s)

    def test_failed_source_recheck_has_no_usable_view(self):
        with patch.object(gate, "validate_evidence", side_effect=AssertionError("source data invalid")):
            with self.assertRaisesRegex(AssertionError, "source data invalid"):
                bridge.make_scientific_view({"model_input": model()}, {}, scenario())

    def test_changed_coefficients_change_exact_objective_identity(self):
        s = scenario()
        s["model_input"]["quadratic_ij_float64_hex"][0][2] = float(.2).hex()
        self.assertFalse(self.view(s)["same_exact_objective"])
        s = scenario()
        s["model_input"]["candidate_master_feature_positions"][0] = 4
        self.assertFalse(self.view(s)["same_exact_objective"])


if __name__ == "__main__":
    unittest.main()
