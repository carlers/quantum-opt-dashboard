"""Adversarial cross-host integration checks; synthetic inputs not source lake data."""
from copy import deepcopy
import hashlib
import math
import unittest

from scripts.verify_n20_joint_integrity import (
    EXPECTED_NAMES, EXPECTED_SELECTION, EXPECTED_ENERGY,
    ORIGINAL_GEOJSON_SHA, ORIGINAL_NOTEBOOK_SHA, SOURCE_GEOJSON_FEASIBLE_SHA,
    canonical, compare,
)


def sample():
    model = {
        "dataset_sha256": ORIGINAL_GEOJSON_SHA,
        "archived_notebook_sha256": ORIGINAL_NOTEBOOK_SHA,
        "candidate_master_feature_positions": list(range(20)),
        "fixed_master_feature_positions": list(range(20, 35)),
        "fixed_neighbor_flags": [1] * 20,
        "free_neighbor_indices": [[] for _ in range(20)],
        "linear_float64_hex": [float(0.125).hex()] * 20,
        "free_fixed_pair_trace": [{"synthetic_index": i} for i in range(300)],
    }
    return {
        "schema_version": 2, "status": "notebook_derived_N20_replay_not_paper_parity",
        "dataset_sha256": ORIGINAL_GEOJSON_SHA,
        "archived_notebook_sha256": ORIGINAL_NOTEBOOK_SHA,
        "candidate_count": 20, "new_station_budget": 5,
        "marked_existing_stations": 15, "enumerated_combinations": 15504,
        "feasible_combinations": 1077,
        "feasible_site_sets_sha256": SOURCE_GEOJSON_FEASIBLE_SHA,
        "selected_local_positions": EXPECTED_SELECTION[:],
        "scip_status": "optimal",
        "local_one_hop_not_global_connectivity": True,
        "original_energy": EXPECTED_ENERGY,
        "model_input": model,
        "model_input_sha256": hashlib.sha256(canonical(model)).hexdigest(),
    }


def six():
    return [(n, sample()) for n in sorted(EXPECTED_NAMES)]


def rehash(r):
    r["model_input_sha256"] = hashlib.sha256(
        canonical(r["model_input"])
    ).hexdigest()


class JointN20Tests(unittest.TestCase):
    def test_matching_source_spatial_and_precision_modes_pass(self):
        report = compare(six())
        self.assertTrue(report["identical_original_one_hop_graph_across_hosts"])
        self.assertEqual(report["feasible_combinations"], 1077)
        self.assertEqual(report["num_source_numeric_modes_in_observed_sample"], 1)

    def test_one_ulp_numerical_input_drift_must_not_fail_same_science(self):
        data = six()
        model = data[3][1]["model_input"]
        model["linear_float64_hex"][0] = math.nextafter(
            float.fromhex(model["linear_float64_hex"][0]), math.inf
        ).hex()
        rehash(data[3][1])
        report = compare(data)
        self.assertEqual(report["num_source_numeric_modes_in_observed_sample"], 2)
        self.assertTrue(report["identical_original_one_hop_graph_across_hosts"])

    def test_changed_unselected_graph_even_with_same_feasible_metadata_fails(self):
        data = six()
        data[0][1]["model_input"]["fixed_neighbor_flags"][18] = 0
        rehash(data[0][1])
        with self.assertRaisesRegex(ValueError, "one-hop graph differs"):
            compare(data)

    def test_modified_feasible_set_sha_alone_fails(self):
        data = six()
        data[0][1]["feasible_site_sets_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "feasible region changed"):
            compare(data)

    def test_dropped_original_300_pair_precision_trace_fails(self):
        data = six()
        data[0][1]["model_input"]["free_fixed_pair_trace"].pop()
        rehash(data[0][1])
        with self.assertRaisesRegex(ValueError, "300 free/fixed"):
            compare(data)

    def test_changed_source_dataset_hash_fails(self):
        data = six()
        data[0][1]["dataset_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "historical data"):
            compare(data)

    def test_tampered_exact_model_sha_fails(self):
        data = six()
        data[0][1]["model_input_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checksum"):
            compare(data)

    def test_fifth_candidate_duplicate_replica_fails(self):
        data = six()
        data[0] = (data[1][0], deepcopy(data[0][1]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare(data)

    def test_missing_fresh_host_process_fails(self):
        with self.assertRaisesRegex(ValueError, "six original source"):
            compare(six()[:-1])

    def test_large_energy_change_fails_even_if_site_indices_same(self):
        data = six()
        data[0][1]["original_energy"] += 0.1
        with self.assertRaisesRegex(ValueError, "objective changed"):
            compare(data)


if __name__ == "__main__":
    unittest.main()
