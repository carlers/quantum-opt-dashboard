"""Adversarial tests: baseline AHP/GIS audit, never an alternative-model sweep."""
from __future__ import annotations

import hashlib
import unittest

import numpy as np

from scripts.studies import n20_s4_parameter_provenance as prov


class S4HistoricalParameterAuditTests(unittest.TestCase):
    def test_main_manuscript_table_III_principal_eigenpair(self):
        r = prov.main_ahp_priority(prov.TABLE_III)
        self.assertAlmostEqual(sum(r["principal_right_eigenvector"]), 1.0, places=14)
        self.assertAlmostEqual(r["lambda_max"], 4.14712642148, places=8)
        self.assertAlmostEqual(r["consistency_ratio_RI4_0_90"], .0544912672, places=7)
        self.assertAlmostEqual(r["principal_right_eigenvector"][0], .616975355, places=7)

    def test_reject_nonreciprocal_manuscript_pairwise_matrix(self):
        bad = [row[:] for row in prov.TABLE_III]
        bad[0][1] = 5.0
        with self.assertRaisesRegex(ValueError, "reciprocal"):
            prov.main_ahp_priority(bad)

    def test_reject_singular_invalid_AHP_matrix(self):
        bad = [row[:] for row in prov.TABLE_III]
        bad[0][0] = 0
        with self.assertRaisesRegex(ValueError, "positive"):
            prov.main_ahp_priority(bad)

    def test_printed_table_IV_and_source_are_not_same_weights(self):
        self.assertNotEqual(list(prov.ORIGINAL_WEIGHTS), list(prov.PRINTED_TABLE_IV))
        self.assertEqual(len(prov.ORIGINAL_WEIGHTS), 8)
        self.assertAlmostEqual(sum(prov.ORIGINAL_WEIGHTS), 1.0001, places=7)
        self.assertAlmostEqual(prov.parent_weight_sums(prov.PRINTED_TABLE_IV)[0],
                               .552191814, places=9)
        self.assertNotAlmostEqual(prov.parent_weight_sums(prov.ORIGINAL_WEIGHTS)[0],
                                  .552191814, places=5)

    def test_D2_semantics_are_not_silently_rewritten(self):
        self.assertEqual(prov.FACTOR_NAMES[-1], "d2_road_proximity")
        self.assertEqual(prov.FACTOR_NAMES[0], "a1_river_proximity")

    def test_single_available_factor_is_normalized_by_its_weight(self):
        data = np.full((2, 8), np.nan)
        data[0, 0] = .7
        numerator, denominator, utility = prov.factor_utility(
            data, prov.ORIGINAL_WEIGHTS
        )
        self.assertAlmostEqual(numerator[0], .7 * prov.ORIGINAL_WEIGHTS[0])
        self.assertAlmostEqual(denominator[0], prov.ORIGINAL_WEIGHTS[0])
        self.assertAlmostEqual(utility[0], .7)
        # The source treats an all-missing record as zero normalized utility;
        # this behavior is documented, not silently replaced with imputations.
        self.assertEqual(float(denominator[1]), 0)
        self.assertEqual(float(utility[1]), 0)

    def test_complete_factors_use_original_1_0001_denominator(self):
        factors = np.full((1, 8), .75)
        numerator, denominator, utility = prov.factor_utility(
            factors, prov.ORIGINAL_WEIGHTS
        )
        self.assertAlmostEqual(float(denominator[0]), 1.0001)
        self.assertAlmostEqual(float(numerator[0]), .75 * 1.0001)
        self.assertAlmostEqual(float(utility[0]), .75)

    def test_out_of_range_factor_not_silently_recast_as_population(self):
        source = np.zeros((1, 8))
        source[0, 7] = 8.0
        num, den, utility = prov.factor_utility(source, prov.ORIGINAL_WEIGHTS)
        self.assertGreater(float(num[0]), 0)
        self.assertEqual(float(utility[0]), 1.0)  # explicit original clipping
        # Tests must not make this upstream source content a WorldPop value.

    def test_infinite_input_must_fail_finite_source_quality_gate(self):
        data = np.zeros((1, 8))
        data[0, 0] = np.inf
        with self.assertRaisesRegex(ValueError, "Infinite"):
            prov.factor_utility(data, prov.ORIGINAL_WEIGHTS)

    def test_canonical_result_hash_is_reproducible(self):
        payload = {"m": [.05, 1.15], "z": ["d2_road_proximity"]}
        self.assertEqual(
            hashlib.sha256(prov.canonical(payload)).hexdigest(),
            hashlib.sha256(prov.canonical(payload)).hexdigest()
        )

    def test_no_arbitrary_sweep_in_this_audit(self):
        self.assertEqual(prov.EXPECTED_FEASIBLE, 1077)
        self.assertEqual(prov.EXPECTED_LOCAL_SHA,
                         "2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a")
        self.assertEqual(tuple(prov.ORIGINAL_WEIGHTS),
                         (.3671,.1224,.2508,.0502,.1278,.0183,.0476,.0159))


if __name__ == "__main__":
    unittest.main()
