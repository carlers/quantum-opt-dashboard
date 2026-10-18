"""Adversarial exact-model manifest tests; no solver calls or historical data edits."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest

from scripts.run_n20_reference_notebook import (
    EXPECTED_DATA_SHA,
    EXPECTED_FIXED_MASTER,
    EXPECTED_FREE_MASTER,
    EXPECTED_NOTEBOOK_SHA,
    verify_exact_model,
)


def digest(model: dict) -> str:
    data = (json.dumps(model, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def tiny_contract() -> dict:
    # Artificial coefficients purely to check validator failure paths.
    # The actual scientific reference is replayed from the archived lake data in CI.
    model = {
        "schema_version": 1,
        "model_family": "notebook_derived_laguna_N20_local_one_hop",
        "dataset_sha256": EXPECTED_DATA_SHA,
        "archived_notebook_sha256": EXPECTED_NOTEBOOK_SHA,
        "candidate_master_feature_positions": EXPECTED_FREE_MASTER[:],
        "fixed_master_feature_positions": EXPECTED_FIXED_MASTER[:],
        "site_coords_epsg32651_float64_hex": [
            [float(i).hex(), float(i + 1).hex()] for i in range(35)
        ],
        "factor_weights_float64_hex": [float(0.125).hex()] * 8,
        "budget_exact": 5,
        "linear_float64_hex": [float(0).hex()] * 20,
        "quadratic_ij_float64_hex": [
            [i, i + 1, float(0.125).hex()] for i in range(12)
        ],
        "fixed_neighbor_flags": [1 if i in (0, 1, 3, 6, 7) else 0 for i in range(20)],
        "free_neighbor_indices": [[] for _ in range(20)],
        "d_max_m_float64_hex": float(1).hex(),
        "redundancy_beta_float64_hex": float(1).hex(),
        "wake_delta_float64_hex": float(1).hex(),
    }
    record = {
        "model_input": model,
        "model_input_sha256": digest(model),
        "model_input_hash_scope":
            "IEEE754 exact model; compare tolerance-based parity separately",
        "selected_local_positions": [0, 1, 3, 6, 7],
        "original_energy": 0.25,  # (0,1) and (6,7), both selected
    }
    return record


class N20ModelManifestTests(unittest.TestCase):
    def test_valid_artificial_contract_is_self_consistent(self):
        verify_exact_model(tiny_contract())

    def test_a_one_ulp_coefficient_change_is_exposed_by_digest(self):
        record = tiny_contract()
        old = float.fromhex(record["model_input"]["quadratic_ij_float64_hex"][0][2])
        import math
        record["model_input"]["quadratic_ij_float64_hex"][0][2] = math.nextafter(
            old, math.inf
        ).hex()
        with self.assertRaisesRegex(AssertionError, "SHA-256"):
            verify_exact_model(record)

    def test_a_rehashed_objective_change_still_fails_decoding(self):
        record = tiny_contract()
        record["model_input"]["linear_float64_hex"][0] = float(1.0).hex()
        record["model_input_sha256"] = digest(record["model_input"])
        with self.assertRaisesRegex(AssertionError, "Decoded complete coefficient"):
            verify_exact_model(record)

    def test_a_rehashed_constraint_change_still_fails_feasibility(self):
        record = tiny_contract()
        record["model_input"]["fixed_neighbor_flags"][0] = 0
        record["model_input_sha256"] = digest(record["model_input"])
        with self.assertRaisesRegex(AssertionError, "one-hop rules"):
            verify_exact_model(record)

    def test_malformed_quadratic_term_list_is_rejected(self):
        record = tiny_contract()
        record["model_input"]["quadratic_ij_float64_hex"].append(
            [18, 19, float(1).hex()]
        )
        record["model_input_sha256"] = digest(record["model_input"])
        with self.assertRaisesRegex(AssertionError, "shape changed"):
            verify_exact_model(record)


if __name__ == "__main__":
    unittest.main()
