"""Adversarial pre-specified independent candidate generator/geometry tests."""
from __future__ import annotations

from pathlib import Path
import hashlib
import math
import unittest
from unittest.mock import patch

import numpy as np
from shapely.geometry import Polygon

from scripts.studies import n20_g1_candidate_eligibility as study


class PreRegisteredCandidatePoolTests(unittest.TestCase):
    def test_water_only_line_crossing_land_is_excluded_even_within_dmax(self):
        # Both points are inside the U's arms, but their connecting segment
        # crosses the upper central gap (modeled land).
        hull = Polygon([
            (0, 0), (10, 0), (10, 10), (7, 10),
            (7, 3), (3, 3), (3, 10), (0, 10),
        ])
        a, b = (2, 8), (8, 8)
        self.assertTrue(hull.contains(study.Point(a)))
        self.assertTrue(hull.contains(study.Point(b)))
        self.assertLess(math.dist(a, b), 12)
        self.assertFalse(study.legal_link(a, b, hull, 12))

    def test_direct_filter_rejects_land_blocked_nonfixed_site(self):
        hull = Polygon([
            (0, 0), (10, 0), (10, 10), (7, 10),
            (7, 3), (3, 3), (3, 10), (0, 10),
        ])
        coords = np.asarray([(2, 8), (8, 8), (8, 6), (9, 1)], dtype=float)
        selected = study.direct_fixed_filter(coords, np.asarray([0, 2]),
                                              np.asarray([1]), hull, 12)
        self.assertEqual(selected.tolist(), [2])

    def test_source_sorted_tie_break_gives_first_index_not_largest_utility(self):
        # Sorted source IDs 1 and 2 are tied in nearest-fix distance; choose
        # smaller *master ID*, never a factor utility / solver-dependent choice.
        coords = np.array([[0, 0], [2, 0], [-2, 0], [100, 100]], float)
        result = study.farthest_first(
            coords, np.asarray([0]), np.asarray([1, 2]), count=2
        )
        self.assertEqual(result, [1, 2])

    def test_pool_requires_source_sorted_master_positions(self):
        coords = np.array([[0, 0], [2, 0], [-2, 0]], float)
        with self.assertRaisesRegex(ValueError, "sorted"):
            study.farthest_first(coords, np.asarray([0]),
                                 np.asarray([2, 1]), count=2)

    def test_duplicate_pool_source_indices_fail(self):
        coords = np.array([[0, 0], [2, 0], [-2, 0]], float)
        with self.assertRaisesRegex(ValueError, "Unique"):
            study.farthest_first(coords, np.asarray([0]),
                                 np.asarray([1, 1]), count=2)

    def test_g1_ineligible_pool_cannot_silently_adjust_source_range(self):
        coords = np.array([[0, 0], [2, 0], [-2, 0]], float)
        with self.assertRaisesRegex(ValueError, "qualifying"):
            study.farthest_first(coords, np.asarray([0]),
                                 np.asarray([1]), count=2)

    def test_original_source_dmax_and_distance_exclude_invalid_hops(self):
        polygon = Polygon([(-100, -100), (100, -100),
                           (100, 100), (-100, 100)])
        self.assertTrue(study.legal_link((0, 0), (30, 40), polygon, 50))
        self.assertFalse(study.legal_link((0, 0), (30, 40), polygon, 49))
        self.assertFalse(study.legal_link((0, 0), (130, 0), polygon, 500))

    def test_original_source_redundancy_only_nonnegative_in_test(self):
        # Counterfactual generator does NOT introduce a distance-benefit
        # coefficient or change the original β/δ assumptions.
        self.assertEqual(study.L_C, 7500.0)
        self.assertEqual(study.L_W, 1000.0)
        self.assertEqual(study.BETA, 1.0)
        self.assertEqual(study.DELTA, 1.0)
        self.assertEqual(study.K_NEW, 5)

    def test_source_checksum_tampering_must_stop_before_experiments(self):
        with patch("pathlib.Path.read_bytes", return_value=b"forged"):
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                study.load_source()

    def test_source_utility_d2_remains_road_not_paper_worldpop(self):
        self.assertEqual(study.FACTOR_NAMES[-1], "d2_road_proximity")
        self.assertAlmostEqual(sum(study.WEIGHTS), 1.0001, places=6)

    def test_all_five_site_combinations_have_stable_sha_protocol(self):
        ids = list(study.combinations(range(5), 2))
        raw = b"".join((",".join(map(str, pair)) + "\n").encode("ascii")
                       for pair in ids)
        self.assertEqual(len(ids), 10)
        self.assertEqual(study.sha_bytes(raw), hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
