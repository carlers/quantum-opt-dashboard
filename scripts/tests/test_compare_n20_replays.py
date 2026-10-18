"""Fast adversarial tests for observational (not retuning) cross-run comparison."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import math
import unittest

from scripts.compare_n20_replays import canonical, compare


def sample() -> dict:
    model = {
        "schema_version": 1,
        "dataset_sha256": "unchanged-artificial-data",
        "candidate_master_feature_positions": [10, 20],
        "linear_float64_hex": [float(0.125).hex(), float(-0.5).hex()],
        "quadratic_ij_float64_hex": [[0, 1, float(0.025).hex()]],
        "free_neighbor_indices": [[1], [0]],
    }
    return {
        "schema_version": 2,
        "status": "notebook_derived_N20_replay_not_paper_parity",
        "model_input": model,
        "model_input_sha256": hashlib.sha256(canonical(model)).hexdigest(),
        "scip_status": "optimal",
        "selected_local_positions": [0, 1, 3, 6, 7],
        "selected_master_feature_positions": [5253, 2394, 1557, 47, 5409],
        "original_energy": -3.3012934918564643,
        "enumeration_energy": -3.3012934918564643,
        "enumerated_combinations": 15504,
        "scientific_environment": {
            "python": "3.12.15", "numpy": "2.5.4", "scipy": "1.18.1",
            "shapely": "2.2.0", "pyscipopt": "6.3.0",
        },
    }


def rehash(record: dict) -> None:
    record["model_input_sha256"] = hashlib.sha256(
        canonical(record["model_input"])
    ).hexdigest()


class CrossProcessComparatorTests(unittest.TestCase):
    def test_equivalent_records_have_one_exact_hash(self):
        a = sample()
        report = compare([("a", a), ("b", deepcopy(a))])
        self.assertTrue(report["semantic_pass_with_tolerance"])
        self.assertTrue(report["exact_model_fingerprint_stable_in_observed_sample"])
        self.assertEqual(report["number_of_independent_process_records"], 2)
        self.assertEqual(len(report["exact_model_hashes"]), 1)

    def test_one_ulp_drift_is_retained_not_falsely_classified_as_model_change(self):
        a, b = sample(), sample()
        value = float.fromhex(b["model_input"]["linear_float64_hex"][0])
        b["model_input"]["linear_float64_hex"][0] = math.nextafter(
            value, math.inf
        ).hex()
        rehash(b)
        report = compare([("a", a), ("b", b)])
        self.assertFalse(report["exact_model_fingerprint_stable_in_observed_sample"])
        self.assertTrue(report["semantic_pass_with_tolerance"])
        diffs = report["observations"][1]["numeric_leaf_changes"]
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["ulp_distance_estimate"], 1.0)
        self.assertTrue(diffs[0]["within_declared_tolerance"])

    def test_large_coefficient_drift_fails_even_if_final_score_is_same(self):
        a, b = sample(), sample()
        b["model_input"]["linear_float64_hex"][0] = float(0.25).hex()
        rehash(b)
        report = compare([("a", a), ("b", b)])
        self.assertFalse(report["semantic_pass_with_tolerance"])
        self.assertEqual(len(report["observations"][1]["outside_numeric_tolerance"]), 1)

    def test_changed_adjacency_is_not_numeric_roundoff(self):
        a, b = sample(), sample()
        b["model_input"]["free_neighbor_indices"] = [[], []]
        rehash(b)
        report = compare([("a", a), ("b", b)])
        self.assertFalse(report["semantic_pass_with_tolerance"])
        self.assertTrue(report["observations"][1]["structural_leaf_changes"])

    def test_changed_dependency_version_is_a_confounded_comparison(self):
        a, b = sample(), sample()
        b["scientific_environment"]["numpy"] = "2.5.5"
        report = compare([("a", a), ("b", b)])
        self.assertFalse(report["semantic_pass_with_tolerance"])
        self.assertFalse(report["observations"][1]["core_dependency_versions_equal"])

    def test_modified_payload_without_rehash_is_rejected(self):
        a, b = sample(), sample()
        b["model_input"]["candidate_master_feature_positions"][1] = 23
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            compare([("a", a), ("b", b)])

    def test_solver_and_exhaustive_check_must_be_present(self):
        a, b = sample(), sample()
        b["enumerated_combinations"] = 7
        with self.assertRaisesRegex(ValueError, "not an exhaustive"):
            compare([("a", a), ("b", b)])

    def test_minimum_two_runs(self):
        with self.assertRaisesRegex(ValueError, "At least two"):
            compare([("a", sample())])


if __name__ == "__main__":
    unittest.main()
