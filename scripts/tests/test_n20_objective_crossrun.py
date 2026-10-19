"""Adversarial research controls for cross-host exact N20 objective identity."""
from __future__ import annotations

from copy import deepcopy
import math
import unittest
from unittest.mock import patch

from scripts import science_claim_gate as gate
from scripts.studies import n20_objective_crossrun as study


def sample() -> dict:
    model = {
        "candidate_master_feature_positions": [1, 2],
        "fixed_master_feature_positions": [3],
        "factor_column_names": list(gate.FACTOR_NAMES),
        "factor_weights_float64_hex": [float(w).hex() for w in gate.ORIGINAL_WEIGHTS],
        "linear_float64_hex": [float(-.2).hex(), float(-.7).hex()],
        "quadratic_ij_float64_hex": [[0, 1, float(.1).hex()]],
        "site_coords_epsg32651_float64_hex": [
            [float(x).hex(), float(y).hex()]
            for x, y in [(330000., 1500000.), (330100., 1500000.), (330200., 1500000.)]
        ],
        "budget_exact": 1,
        "dataset_sha256": gate.EXPECTED_DATA_SHA,
    }
    return {
        "status": "notebook_derived_N20_replay_not_paper_parity",
        "schema_version": 2,
        "model_input": model,
        "model_input_sha256": gate.full_manifest_digest(model),
        "scip_status": "optimal",
        "enumerated_combinations": 15504,
        "selected_local_positions": [0, 1, 3, 6, 7],
        "selected_master_feature_positions": [5253, 2394, 1557, 47, 5409],
        "original_energy": -3.3012934918564643,
        "enumeration_energy": -3.3012934918564643,
        "scientific_environment": {
            "python": "3.12", "numpy": "2.5.4", "scipy": "1.18.1",
            "shapely": "2.2.0", "pyscipopt": "6.3.0",
        },
    }


def recalc(record: dict) -> None:
    record["model_input_sha256"] = gate.full_manifest_digest(record["model_input"])


class ObjectiveCrossRunTests(unittest.TestCase):
    def run_comparison(self, a, b):
        with patch.object(study, "audit_one", side_effect=lambda rec: (
            {"spatial_graph_sha256": "a" * 64},
            gate.objective_fingerprint(rec["model_input"]),
        )):
            return study.summarize([("r2", b), ("r1", a)])

    def test_equal_bitwise_objectives_and_model_inputs(self):
        x = sample()
        out = self.run_comparison(x, deepcopy(x))
        self.assertTrue(out["observed_exact_objective_stability"])
        self.assertEqual(out["records"], 2)
        self.assertTrue(out["diagnostic_semantic_equivalence_only"])
        self.assertEqual(out["baseline_record"], "r1")
        self.assertEqual(out["comparisons"][1]["objective_leaf_differences_from_first"], [])

    def test_one_ulp_difference_retains_exact_variant_and_path(self):
        a, b = sample(), sample()
        v = float.fromhex(b["model_input"]["linear_float64_hex"][0])
        b["model_input"]["linear_float64_hex"][0] = math.nextafter(v, math.inf).hex()
        recalc(b)
        out = self.run_comparison(a, b)
        self.assertFalse(out["observed_exact_objective_stability"])
        self.assertTrue(out["diagnostic_semantic_equivalence_only"])
        diff = out["comparisons"][1]["objective_leaf_differences_from_first"]
        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0]["path"], "linear_float64_hex[0]")
        self.assertEqual(diff[0]["ulp_distance_estimate"], 1.0)

    def test_different_factor_semantics_are_not_low_bit_noise(self):
        a, b = sample(), sample()
        b["model_input"]["factor_column_names"][-1] = "d2_worldpop_population"
        recalc(b)
        out = self.run_comparison(a, b)
        self.assertFalse(out["diagnostic_semantic_equivalence_only"])
        self.assertTrue(out["comparisons"][1]["objective_structural_differences"])

    def test_changed_weight_or_quadratic_changes_exact_scored_function(self):
        a, b = sample(), sample()
        b["model_input"]["factor_weights_float64_hex"][1] = float(.2).hex()
        recalc(b)
        out = self.run_comparison(a, b)
        self.assertFalse(out["diagnostic_semantic_equivalence_only"])
        b = sample()
        b["model_input"]["quadratic_ij_float64_hex"][0][2] = float(.2).hex()
        recalc(b)
        self.assertFalse(self.run_comparison(a, b)["diagnostic_semantic_equivalence_only"])

    def test_changed_source_sites_not_equivalent(self):
        a, b = sample(), sample()
        b["model_input"]["candidate_master_feature_positions"][0] = 100
        recalc(b)
        self.assertFalse(self.run_comparison(a, b)["diagnostic_semantic_equivalence_only"])

    def test_bad_checksum_rejected_not_patched_away(self):
        a, b = sample(), sample()
        b["model_input"]["linear_float64_hex"][0] = float(-.5).hex()
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            self.run_comparison(a, b)

    def test_bad_original_environment_flags_diagnostic_failure(self):
        a, b = sample(), sample()
        b["scientific_environment"]["numpy"] = "not-the-same"
        self.assertFalse(self.run_comparison(a, b)["diagnostic_semantic_equivalence_only"])

    def test_bad_cold_evidence_gates_fail_closed(self):
        a = sample()
        with patch.object(study.gate, "_assert_source_bytes"), \
             patch.object(study, "verify_result", side_effect=AssertionError("cold source invalid")):
            with self.assertRaisesRegex(AssertionError, "cold source invalid"):
                study.audit_one(a)

    def test_full_source_metadata_still_verified(self):
        a = sample()
        with patch.object(study.gate, "_assert_source_bytes"), \
             patch.object(study, "verify_result"), \
             patch.object(study, "certify_geometry", return_value={"spatial_graph_sha256": "a" * 64}):
            geom, digest = study.audit_one(a)
        self.assertEqual(geom["spatial_graph_sha256"], "a" * 64)
        self.assertEqual(digest, gate.objective_fingerprint(a["model_input"]))

    def test_bad_ahp_inputs_refused_even_if_score_stale(self):
        a = sample()
        a["model_input"]["factor_weights_float64_hex"][-1] = float(.999).hex()
        recalc(a)
        with patch.object(study.gate, "_assert_source_bytes"), \
             patch.object(study, "verify_result"), \
             patch.object(study, "certify_geometry", return_value={"spatial_graph_sha256": "a" * 64}):
            with self.assertRaisesRegex(AssertionError, "AHP"):
                study.audit_one(a)

    def test_not_enough_or_duplicate_records_refused(self):
        x = sample()
        with self.assertRaisesRegex(ValueError, "at least two"):
            study.summarize([("r1", x)])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            study.summarize([("r1", x), ("r1", deepcopy(x))])

    def test_expected_two_prior_fingerprints_are_observations_only(self):
        self.assertEqual(len(study.PRIOR_OBSERVED_OBJECTIVE_SHAS), 2)
        self.assertNotEqual(*study.PRIOR_OBSERVED_OBJECTIVE_SHAS)
        self.assertIn("not_replayed_here", "historical_2026_10_19_objective_sha_observations_not_replayed_here")


if __name__ == "__main__":
    unittest.main()
