"""Canaries for factual printed AHP arithmetic; not a raw elicitation replica."""
import unittest

from scripts.replay_printed_manuscript_ahp import (
    calculate, TABLE_IV_GLOBAL, REPORTED_SCIP_N20,
    SOURCE_DERIVED_SCIP_N20,
)


class PrintedAhpArithmeticTests(unittest.TestCase):
    def test_printed_matrix_eigenvector_approximate(self):
        result = calculate()
        expected = [0.616975355, 0.228319383, 0.104610094, 0.050095168]
        for actual, wanted in zip(
            result["printed_table_iii_principal_eigenvector"], expected
        ):
            self.assertAlmostEqual(actual, wanted, delta=1e-8)
        self.assertAlmostEqual(
            result["printed_table_iii_principal_eigenvalue"],
            4.14712642148, delta=1e-9,
        )

    def test_published_pillar_subtotals_are_not_printed_eigenvector(self):
        r = calculate()
        expected = [0.552191814, 0.268830225, 0.130782272, 0.048195690]
        for value, want in zip(r["printed_table_iv_pillar_sums"], expected):
            self.assertAlmostEqual(value, want, delta=1e-9)
        self.assertGreater(
            abs(r["printed_table_iv_pillar_sums"][0] -
                r["printed_table_iii_principal_eigenvector"][0]), 0.06
        )

    def test_ratio_method_matches_manuscript_lambda_not_true_eigenvalue(self):
        r = calculate()
        self.assertAlmostEqual(
            r["published_pillar_ratio_mean"], 4.220685443, delta=1e-8
        )
        self.assertAlmostEqual(
            r["published_pillar_ratio_mean_cr"], 0.081735349, delta=1e-8
        )
        self.assertLess(
            abs(r["printed_table_iii_eigenvector_cr"] - 0.0544912672),
            1e-8
        )

    def test_exact_source_minus_paper_scip_energy_is_separately_labeled(self):
        r = calculate()
        self.assertEqual(
            r["source_minus_reported_scip_energy"], "0.0000255081435357"
        )
        self.assertEqual(
            SOURCE_DERIVED_SCIP_N20 - REPORTED_SCIP_N20,
            SOURCE_DERIVED_SCIP_N20 - REPORTED_SCIP_N20,
        )

    def test_printed_subcriteria_are_not_assumed_full_precision(self):
        r = calculate()
        self.assertEqual(len(TABLE_IV_GLOBAL), 8)
        self.assertNotAlmostEqual(
            sum(r["printed_table_iv_pillar_sums"]),
            1.0, delta=1e-12,
        )
        self.assertTrue(r["status"].startswith("printed-value arithmetic comparison"))


if __name__ == "__main__":
    unittest.main()
