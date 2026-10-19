"""Adversarial tests: source-signed wake symmetry and coefficient placement."""
from __future__ import annotations

import math
import unittest
from unittest.mock import patch

import numpy as np
from shapely.geometry import Polygon

from scripts.studies import n20_wake_w0_w1 as study


class SourceWakeFormulaTests(unittest.TestCase):
    def test_east_versus_west_sign_symmetry(self):
        for cosine in [0.70711, .9, 1, .95, 0.7071, .70709, .001, 0]:
            self.assertAlmostEqual(
                study.source_wake_pair(cosine, 600),
                study.source_wake_pair(-cosine, 600), places=15
            )

    def test_signed_branch_equivalent_to_east_west_alignment(self):
        for c in [-1., -.99, -.7071001, -.7071, -.2, 0., .1, .7071, .7071001, 1.]:
            actual = study.source_wake_pair(c, 850)
            expected = math.exp(-.85) * abs(c) if abs(c) > study.CONE else 0.
            self.assertAlmostEqual(actual, expected, places=15)

    def test_exact_cone_boundary_has_no_wake(self):
        self.assertEqual(study.source_wake_pair(.7071, 1), 0)
        self.assertEqual(study.source_wake_pair(-.7071, 1), 0)
        self.assertGreater(study.source_wake_pair(.70710000001, 1), 0)
        self.assertGreater(study.source_wake_pair(-.70710000001, 1), 0)

    def test_north_south_axis_has_zero_wake(self):
        self.assertEqual(study.source_wake_pair(0, 100), 0)

    def test_negative_or_zero_distance_rejected_without_fake_coefficient(self):
        for distance in (-1, 0, math.nan):
            with self.assertRaises(ValueError):
                study.source_wake_pair(.9, distance)

    def test_invalid_cosine_rejected(self):
        with self.assertRaises(ValueError):
            study.source_wake_pair(math.nan, 850)

    def test_source_wake_decreases_with_separation(self):
        self.assertGreater(study.source_wake_pair(1, 100),
                           study.source_wake_pair(1, 1000))

    def test_selective_wake_removal_only_two_registered_deltas(self):
        with self.assertRaisesRegex(ValueError, "Only frozen"):
            study.source_case({}, [], None, delta=.5)

    def test_ordered_five_selection_energy_uses_pair_indicator_not_nearest(self):
        case = {"linear_float64_hex": [float(-1).hex(), float(-2).hex()],
                "quadratic_ij_float64_hex": [[0, 1, float(.4).hex()]]}
        self.assertAlmostEqual(study.score(case, (0, 1)), -2.6)
        self.assertAlmostEqual(study.score(case, (0,)), -1.)

    def test_fixed_pair_adds_linear_and_free_pair_adds_quadratic(self):
        # One free/free within 100m, one free/fixed east at 100m,
        # another fixed far. Simulate original 20+15 positions with
        # a giant source-geometry hull; coordinate duplicates are not
        # eligible because the source skips zero-distance pairs.
        points = [(2_000., 2_000.) for _ in range(35)]
        points[0] = (100., 100.)
        points[1] = (200., 100.)
        points[20] = (300., 100.)
        # Put the other station sites far beyond 2Lc to exclude links.
        for i in range(2, 20):
            points[i] = (30_000. + i*1000, 40_000.)
        for i in range(21, 35):
            points[i] = (35_000. + i*1000, 40_000.)
        hull = Polygon([(-1, -1), (100_000, -1), (100_000, 100_000), (-1, 100_000)])
        model = {
            "utility_free_float64_hex": [float(.5).hex()] * 20,
            "d_max_m_float64_hex": float(500.).hex(),
            "site_coords_epsg32651_float64_hex": [
                [float(x).hex(), float(y).hex()] for x, y in points
            ],
        }
        # Original dataset positions here intentionally synthetic and in
        # *different order*, but the source_case guards identity for real runs.
        with patch.object(study, "EXPECTED_FREE", list(range(20))), \
             patch.object(study, "EXPECTED_FIXED", list(range(20, 35))):
            case = study.source_case(model, points, hull, delta=1.0)
            self.assertTrue(any((i, j) == (0, 1)
                                for i, j, _ in case["quadratic_ij_float64_hex"]))
            self.assertGreater(float.fromhex(case["linear_float64_hex"][0]), -.5)
            self.assertGreater(float.fromhex(case["linear_float64_hex"][1]), -.5)

    def test_frozen_source_identity_and_algebra_constants(self):
        self.assertEqual(study.N_FREE, 20)
        self.assertEqual(study.N_FIXED, 15)
        self.assertEqual(study.K_NEW, 5)
        self.assertEqual(study.L_C, 7500.)
        self.assertEqual(study.L_W, 1000.)
        self.assertEqual(study.CONE, .7071)


if __name__ == "__main__":
    unittest.main()
