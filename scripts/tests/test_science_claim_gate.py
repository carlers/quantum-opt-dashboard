"""Adversarial source/scenario/physical-claim tests for review-only gate."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import unittest
from unittest.mock import patch

from scripts import science_claim_gate as gate


def mini_model():
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


def source_with_fake_S4():
    m = mini_model()
    m["candidate_master_feature_positions"] = list(gate.EXPECTED_FREE)
    m["fixed_master_feature_positions"] = list(gate.EXPECTED_FIXED)
    m["site_coords_epsg32651_float64_hex"] = [
        [float(i).hex(), float(i + 1).hex()] for i in range(35)
    ]
    m["factor_weights_float64_hex"] = [
        float(x).hex() for x in gate.ORIGINAL_WEIGHTS
    ]
    m["linear_float64_hex"] = [float(i / 20).hex() for i in range(20)]
    m["quadratic_ij_float64_hex"] = []
    m["budget_exact"] = 5
    m["d_max_m_float64_hex"] = float(9873).hex()
    model_sha = gate.full_manifest_digest(m)
    ref = {
        "model_input": m,
        "model_input_sha256": model_sha,
        "original_energy": gate.EXPECTED_FEASIBLE / 1000,
    }
    graph_sha = "a" * 64
    src = {
        "schema_version": 1,
        "scope": "read_only_N20_S4_parameter_and_AHP_provenance_no_sensitivity_sweep",
        "original_source_model_sha256": model_sha,
        "original_source_geojson_sha256": gate.EXPECTED_DATA_SHA,
        "archived_original_notebook_sha256": gate.EXPECTED_ARCHIVE_SHA,
        "reference": {
            "N": 20, "K": 5, "original_fixed_count": 15,
            "original_best_local_indices": [0, 1, 3, 6, 7],
            "original_feasible_subsets": gate.EXPECTED_FEASIBLE,
            "original_feasible_set_sha256": gate.ORIGINAL_FEASIBLE_SHA,
            "original_energy": gate.EXPECTED_FEASIBLE / 1000,
        },
        "original_factor_data": {
            "original_eight_names": list(gate.FACTOR_NAMES),
            "all_source_points": 5417,
            "all_source_features_with_any_missing": 0,
            "selected_20_with_any_missing": 0,
            "original_weights_float64_hex": [
                float(x).hex() for x in gate.ORIGINAL_WEIGHTS
            ],
            "original_weights_sum": 1.0001,
        },
        "original_spatial_inputs": {
            "source_hull_geometry_graph_sha256": graph_sha,
            "source_490_candidate_related_pair_checks": 490,
            "original_direct_free_free_edges": 11,
            "original_direct_free_fixed_edges": 34,
            "original_Dmax_m_float64_hex": m["d_max_m_float64_hex"],
        },
        "sensitivity_status": {
            "new_parameter_values_tested": [],
            "hull_ratio_range_sweep": "BLOCKED_no_source",
            "Dmax_radio_range_sweep": "BLOCKED_no_source",
        },
        "manuscript_transcription_not_original_solver_input": {
            "source_D2_field": "d2_road_proximity",
            "manuscript_D2_label": "stakeholder/population exposure — WorldPop",
            "table_IV_printed_global_eight_weights": list(gate.PRINTED_TABLE_IV),
        },
    }
    geometry = {"spatial_graph_sha256": graph_sha}
    return ref, src, geometry


class SourceClaimGateTests(unittest.TestCase):
    def test_same_exact_mathematical_objective_is_comparable_not_physics(self):
        source = mini_model()
        same = deepcopy(source)
        outcome = gate.compare_raw_energies(source, same)
        self.assertTrue(outcome["same_exact_objective_over_identical_ordered_sites"])
        self.assertFalse(outcome["physical_monitoring_quality_comparison_established"])

    def test_different_candidate_locations_not_same_objective(self):
        a, b = mini_model(), mini_model()
        b["candidate_master_feature_positions"] = [1, 8]
        self.assertFalse(
            gate.compare_raw_energies(a, b)["same_exact_objective_over_identical_ordered_sites"]
        )

    def test_changed_AHP_criterion_meaning_not_same_objective(self):
        a, b = mini_model(), mini_model()
        b["factor_column_names"][-1] = "d2_worldpop_population"
        self.assertNotEqual(gate.objective_fingerprint(a), gate.objective_fingerprint(b))

    def test_changed_AHP_weights_not_same_objective_even_if_coefficients_stale(self):
        a, b = mini_model(), mini_model()
        b["factor_weights_float64_hex"][-1] = float(.2).hex()
        self.assertNotEqual(gate.objective_fingerprint(a), gate.objective_fingerprint(b))

    def test_changed_quadratic_penalty_or_budget_not_same_objective_scope(self):
        a, b = mini_model(), mini_model()
        b["quadratic_ij_float64_hex"][0][2] = float(.2).hex()
        self.assertNotEqual(gate.objective_fingerprint(a), gate.objective_fingerprint(b))
        b = mini_model()
        b["budget_exact"] = 2
        self.assertNotEqual(gate.objective_fingerprint(a), gate.objective_fingerprint(b))

    def test_wrong_source_hash_refused_even_if_other_numerics_identical(self):
        m = mini_model()
        m["dataset_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "another source"):
            gate.objective_fingerprint(m)

    def test_overlapping_site_ids_and_nonfinite_coeffs_refused(self):
        m = mini_model()
        m["fixed_master_feature_positions"] = [2]
        with self.assertRaisesRegex(ValueError, "distinct"):
            gate.objective_fingerprint(m)
        m = mini_model()
        m["linear_float64_hex"][0] = "nan"
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            gate.objective_fingerprint(m)

    def test_duplicate_quadratic_pair_refused(self):
        m = mini_model()
        m["quadratic_ij_float64_hex"].append(m["quadratic_ij_float64_hex"][0][:])
        with self.assertRaisesRegex(ValueError, "distinct"):
            gate.objective_fingerprint(m)

    def test_source_only_evidence_is_not_manuscript_or_physical_validation(self):
        reference, s4, spatial = source_with_fake_S4()
        with patch.object(gate, "_assert_source_bytes"), \
             patch.object(gate, "verify_result"), \
             patch.object(gate, "certify_geometry", return_value=spatial):
            cert = gate.validate_evidence(reference, s4)
        self.assertEqual(cert["claim_gates"]["computational_source_replay"]["status"],
                         "verified")
        self.assertTrue(cert["physical_quality_guarantee"] is False)
        self.assertEqual(cert["claim_gates"]["historical_manuscript_parity"]["status"],
                         "blocked_no_authoritative_inputs")
        self.assertEqual(cert["claim_gates"]["physical_scientific_validation"]["status"],
                         "blocked_no_field_calibration")
        self.assertIn("N=20/K=5", gate.require_display_claim(
            cert, gate.ALLOWED_DISPLAY_CLAIM
        ))
        for label in gate.HIGHER_CLAIMS:
            with self.assertRaises(PermissionError):
                gate.require_display_claim(cert, label)

    def test_forged_physical_or_manuscript_upgrade_cannot_pass_display_gate(self):
        ref, s4, spatial = source_with_fake_S4()
        with patch.object(gate, "_assert_source_bytes"), \
             patch.object(gate, "verify_result"), \
             patch.object(gate, "certify_geometry", return_value=spatial):
            cert = gate.validate_evidence(ref, s4)
        cert["claim_gates"]["historical_manuscript_parity"]["status"] = "verified"
        with self.assertRaises(PermissionError):
            gate.require_display_claim(cert, gate.ALLOWED_DISPLAY_CLAIM)
        cert["claim_gates"]["historical_manuscript_parity"]["status"] = (
            "blocked_no_authoritative_inputs"
        )
        cert["claim_gates"]["physical_scientific_validation"]["status"] = "verified"
        with self.assertRaises(PermissionError):
            gate.require_display_claim(cert, gate.ALLOWED_DISPLAY_CLAIM)

    def test_swapped_D2_or_fabricated_range_is_refused_by_source_gate(self):
        ref, s4, spatial = source_with_fake_S4()
        s4["manuscript_transcription_not_original_solver_input"][
            "source_D2_field"
        ] = "d2_worldpop_population"
        with patch.object(gate, "_assert_source_bytes"), \
             patch.object(gate, "verify_result"), \
             patch.object(gate, "certify_geometry", return_value=spatial):
            with self.assertRaisesRegex(AssertionError, "road vs manuscript"):
                gate.validate_evidence(ref, s4)
        ref, s4, spatial = source_with_fake_S4()
        s4["sensitivity_status"]["new_parameter_values_tested"] = [.1, .2]
        with patch.object(gate, "_assert_source_bytes"), \
             patch.object(gate, "verify_result"), \
             patch.object(gate, "certify_geometry", return_value=spatial):
            with self.assertRaisesRegex(AssertionError, "source-only"):
                gate.validate_evidence(ref, s4)

    def test_model_hash_mismatch_and_wrong_source_dmax_are_refused(self):
        ref, s4, spatial = source_with_fake_S4()
        s4["original_source_model_sha256"] = "9" * 64
        with patch.object(gate, "_assert_source_bytes"), \
             patch.object(gate, "verify_result"), \
             patch.object(gate, "certify_geometry", return_value=spatial):
            with self.assertRaisesRegex(AssertionError, "source model identity"):
                gate.validate_evidence(ref, s4)
        ref, s4, spatial = source_with_fake_S4()
        s4["original_spatial_inputs"]["original_Dmax_m_float64_hex"] = float(4).hex()
        with patch.object(gate, "_assert_source_bytes"), \
             patch.object(gate, "verify_result"), \
             patch.object(gate, "certify_geometry", return_value=spatial):
            with self.assertRaisesRegex(AssertionError, "geometry"):
                gate.validate_evidence(ref, s4)


if __name__ == "__main__":
    unittest.main()
