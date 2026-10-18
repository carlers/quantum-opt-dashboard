"""Corruption and one-ULP controls for read-only pair-stage precision evidence."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import math
import unittest

from scripts.compare_n20_pair_trace import canonical, compare, verify_record


def sample() -> dict:
    trace = []
    for i in range(20):
        for f in range(15):
            pair = {
                "free_local": i,
                "fixed_local": 20 + f,
                "free_master_feature": 100 + i,
                "fixed_master_feature": 1000 + f,
                "stage": "geometry_rejected",
            }
            trace.append(pair)
    # Artificial pair term; tests no scientific numerical claims.
    pair = trace[9 * 15 + 0]
    pair.update({
        "stage": "added_to_linear",
        "displacement_float64_hex": ["0x1.0p+0", "0x0.0p+0"],
        "distance_float64_hex": "0x1.0p+0",
        "within_one_hop_radius": True,
        "redundancy_float64_hex": "0x1.0p-1",
        "cosine_unclipped_float64_hex": "0x1.0p+0",
        "cosine_float64_hex": "0x1.0p+0",
        "decay_exponent_float64_hex": "-0x1.0p-1",
        "decay_probe_separate_call_float64_hex": "0x1.368b2fc6f960ap-1",
        "wake_forward_float64_hex": "0x1.0p-2",
        "wake_backward_float64_hex": "0x0.0p+0",
        "coefficient_float64_hex": "0x1.0p-1",
        "linear_before_add_float64_hex": "0x0.0p+0",
        "linear_after_add_float64_hex": "0x1.0p-1",
    })
    model = {
        "free_fixed_pair_trace": trace,
        "candidate_master_feature_positions": [100 + i for i in range(20)],
        "fixed_master_feature_positions": [1000 + i for i in range(15)],
        "linear_before_fixed_pairs_float64_hex": ["0x0.0p+0"] * 20,
        "linear_float64_hex": [
            "0x1.0p-1" if i == 9 else "0x0.0p+0" for i in range(20)
        ],
    }
    return {
        "schema_version": 2,
        "scip_status": "optimal",
        "enumerated_combinations": 15504,
        "model_input": model,
        "model_input_sha256": hashlib.sha256(canonical(model)).hexdigest(),
        "original_energy": -3.3012934918564643,
        "selected_local_positions": [0, 1, 3, 6, 7],
    }


def rehash(record: dict) -> None:
    record["model_input_sha256"] = hashlib.sha256(
        canonical(record["model_input"])
    ).hexdigest()


def six(base: dict, other: dict | None = None):
    return [
        (f"run-{i}", deepcopy(other if other and i == 5 else base))
        for i in range(6)
    ]


class PairTraceControls(unittest.TestCase):
    def test_all_original_pair_positions_are_accounted_for(self):
        self.assertEqual(len(verify_record(sample())), 300)

    def test_six_equal_traces_are_negative_observation(self):
        report = compare(six(sample()))
        self.assertEqual(report["different_pair_count"], 0)
        self.assertIsNone(report["first_pair_with_recorded_difference"])
        self.assertEqual(len(report["distinct_original_scientific_model_hashes"]), 1)

    def test_one_ulp_pair_coefficient_is_visible_at_first_changed_field(self):
        a, b = sample(), sample()
        pair = b["model_input"]["free_fixed_pair_trace"][9 * 15]
        new = math.nextafter(0.5, math.inf)
        pair["coefficient_float64_hex"] = new.hex()
        pair["linear_after_add_float64_hex"] = new.hex()
        b["model_input"]["linear_float64_hex"][9] = new.hex()
        rehash(b)
        report = compare(six(a, b))
        self.assertEqual(report["different_pair_count"], 1)
        first = report["first_pair_with_recorded_difference"]
        self.assertEqual(first["free_local"], 9)
        self.assertEqual(first["fixed_local"], 20)
        self.assertEqual(first["first_differing_recorded_field"], "coefficient_float64_hex")

    def test_modified_linear_after_without_original_sum_is_rejected(self):
        b = sample()
        b["model_input"]["free_fixed_pair_trace"][9 * 15][
            "linear_after_add_float64_hex"
        ] = "0x1.0p+0"
        rehash(b)
        with self.assertRaisesRegex(ValueError, "Linear after-add differs"):
            verify_record(b)

    def test_mutated_trace_source_master_id_fails_even_with_matching_sha(self):
        b = sample()
        b["model_input"]["free_fixed_pair_trace"][4][
            "fixed_master_feature"
        ] += 1
        rehash(b)
        with self.assertRaisesRegex(ValueError, "ordering or master"):
            verify_record(b)

    def test_fingerprint_tampering_rejected_before_comparison(self):
        a = sample()
        b = deepcopy(a)
        b["model_input"]["free_fixed_pair_trace"][0]["stage"] = "zero_distance"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            compare(six(a, b))

    def test_missing_300_pair_record_cannot_silently_pass(self):
        b = sample()
        b["model_input"]["free_fixed_pair_trace"].pop()
        with self.assertRaisesRegex(ValueError, "300"):
            verify_record(b)


if __name__ == "__main__":
    unittest.main()
