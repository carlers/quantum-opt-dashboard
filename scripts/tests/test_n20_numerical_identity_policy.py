"""Adversarial tests: observed low-bit agreement never authorizes cache reuse."""
from __future__ import annotations

from copy import deepcopy
import math
import unittest

from scripts import n20_numerical_identity_policy as policy
from scripts import science_claim_gate as gate
from scripts.run_n20_reference_notebook import (
    EXPECTED_FREE_MASTER, EXPECTED_FIXED_MASTER, EXPECTED_NOTEBOOK_SHA,
)


def model() -> dict:
    n = len(EXPECTED_FREE_MASTER)
    return {
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
            [float(330000+i).hex(), float(1500000+i).hex()]
            for i in range(n + len(EXPECTED_FIXED_MASTER))
        ],
        "free_neighbor_indices": [[] for _ in range(n)],
        "fixed_neighbor_flags": [0] * n,
        "d_max_m_float64_hex": float(9873.27).hex(),
        "free_fixed_pair_trace": [{"diagnostic": "no source proof"}],
    }


OBSERVED_PAIRS = {
    9: ("-0x1.7ef780983da1ap-3", "-0x1.7ef780983da1ep-3"),
    10: ("-0x1.5504f3b222e88p-5", "-0x1.5504f3b222e78p-5"),
    17: ("0x1.940eba845152ep-1", "0x1.940eba845152cp-1"),
    19: ("0x1.2b6a379dd0180p-8", "0x1.2b6a379dd0200p-8"),
}


def observed_pair():
    a, b = model(), model()
    for index, (left, right) in OBSERVED_PAIRS.items():
        a["linear_float64_hex"][index] = left
        b["linear_float64_hex"][index] = right
    b["free_fixed_pair_trace"] = [{"diagnostic": "different stage trace, not solver proof"}]
    return a, b


class N20ObservedPrecisionPolicyTests(unittest.TestCase):
    def test_observed_four_coefficient_differences_never_merge_hashes(self):
        a, b = observed_pair()
        r = policy.diagnose_original_n20_objective_pair(a, b)
        self.assertFalse(r["same_exact_objective"])
        self.assertFalse(r["same_complete_model_input"])
        self.assertTrue(r["observed_posthoc_numerical_envelope_only"])
        self.assertEqual(
            {d["index"]: d["ulp_distance_exact_integer"]
             for d in r["changed_linear_coefficients"]},
            {9: 4, 10: 16, 17: 2, 19: 128},
        )
        self.assertFalse(r["raw_energy_as_same_exact_mathematical_function_permitted"])
        self.assertFalse(r["cached_solver_result_reuse_permitted_by_this_diagnostic"])
        self.assertFalse(r["solver_optimality_authenticated_here"])
        self.assertFalse(r["field_radio_or_water_quality_validated"])

    def test_exact_same_model_still_has_no_solved_result_attestation(self):
        a = model()
        r = policy.diagnose_original_n20_objective_pair(a, deepcopy(a))
        self.assertTrue(r["same_exact_objective"])
        self.assertTrue(r["same_complete_model_input"])
        self.assertTrue(r["observed_posthoc_numerical_envelope_only"])
        self.assertFalse(r["cached_solver_result_reuse_permitted_by_this_diagnostic"])
        self.assertFalse(r["independent_source_gis_s4_validation_done_here"])

    def test_unreviewed_other_coefficient_one_ulp_not_assimilated(self):
        a, b = model(), model()
        x = float.fromhex(b["linear_float64_hex"][8])
        b["linear_float64_hex"][8] = math.nextafter(x, math.inf).hex()
        r = policy.diagnose_original_n20_objective_pair(a, b)
        self.assertFalse(r["observed_posthoc_numerical_envelope_only"])

    def test_outside_observed_linear_ulp_envelope_rejected(self):
        a, b = observed_pair()
        b["linear_float64_hex"][9] = math.nextafter(
            float.fromhex(b["linear_float64_hex"][9]), math.inf
        ).hex()
        r = policy.diagnose_original_n20_objective_pair(a, b)
        self.assertFalse(r["observed_posthoc_numerical_envelope_only"])

    def test_changed_dmax_does_not_reuse_cache_even_if_objective_same(self):
        a, b = model(), model()
        b["d_max_m_float64_hex"] = float(10000).hex()
        r = policy.diagnose_original_n20_objective_pair(a, b)
        self.assertTrue(r["same_exact_objective"])
        self.assertFalse(r["same_complete_model_input"])
        self.assertFalse(r["same_nontraced_nonscore_original_metadata"])
        self.assertFalse(r["observed_posthoc_numerical_envelope_only"])
        self.assertFalse(r["cached_solver_result_reuse_permitted_by_this_diagnostic"])

    def test_changed_topology_not_a_numerical_roundoff(self):
        a, b = model(), model()
        b["free_neighbor_indices"][0] = [1]
        r = policy.diagnose_original_n20_objective_pair(a, b)
        self.assertFalse(r["observed_posthoc_numerical_envelope_only"])
        self.assertTrue(r["same_exact_objective"])
        self.assertFalse(r["same_complete_model_input"])

    def test_changed_original_criteria_and_weights_refused(self):
        a, b = model(), model()
        b["factor_column_names"][-1] = "d2_worldpop_population"
        with self.assertRaisesRegex(ValueError, "source-like"):
            policy.diagnose_original_n20_objective_pair(a, b)
        b = model()
        b["factor_weights_float64_hex"][0] = float(.8).hex()
        with self.assertRaisesRegex(ValueError, "source-like"):
            policy.diagnose_original_n20_objective_pair(a, b)

    def test_changed_original_site_order_and_budget_refused(self):
        a, b = model(), model()
        b["candidate_master_feature_positions"][0:2] = b["candidate_master_feature_positions"][0:2][::-1]
        with self.assertRaisesRegex(ValueError, "source-like"):
            policy.diagnose_original_n20_objective_pair(a, b)
        b = model()
        b["budget_exact"] = 6
        with self.assertRaisesRegex(ValueError, "source-like"):
            policy.diagnose_original_n20_objective_pair(a, b)

    def test_wrong_source_data_or_notebook_checksum_refused(self):
        a, b = model(), model()
        b["dataset_sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            policy.diagnose_original_n20_objective_pair(a, b)
        b = model()
        b["archived_notebook_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "source-like"):
            policy.diagnose_original_n20_objective_pair(a, b)

    def test_changed_quadratic_penalty_is_not_the_observed_linear_drift(self):
        a, b = model(), model()
        b["quadratic_ij_float64_hex"][0][2] = float(.25).hex()
        r = policy.diagnose_original_n20_objective_pair(a, b)
        self.assertFalse(r["same_exact_objective"])
        self.assertFalse(r["observed_posthoc_numerical_envelope_only"])

    def test_malformed_or_nonfinite_score_refused(self):
        a, b = model(), model()
        b["linear_float64_hex"][9] = "nan"
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            policy.diagnose_original_n20_objective_pair(a, b)
        b = model()
        b["linear_float64_hex"][9] = "not-hex"
        with self.assertRaisesRegex(ValueError, "exact float.hex"):
            policy.diagnose_original_n20_objective_pair(a, b)

    def test_signed_zero_has_exact_distinct_model_but_not_divergent_math(self):
        a, b = model(), model()
        a["linear_float64_hex"][9] = float(0.0).hex()
        b["linear_float64_hex"][9] = float(-0.0).hex()
        r = policy.diagnose_original_n20_objective_pair(a, b)
        self.assertNotEqual(r["first_exact_objective_sha256"], r["second_exact_objective_sha256"])
        self.assertFalse(r["same_exact_objective"])
        self.assertFalse(r["cached_solver_result_reuse_permitted_by_this_diagnostic"])


if __name__ == "__main__":
    unittest.main()
