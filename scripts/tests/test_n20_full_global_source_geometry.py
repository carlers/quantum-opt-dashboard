"""Adversarial independent fully mandatory-fixed global-connectivity tests.

Synthetic unit inputs only. Cold genuine 5417-feature source is tested by CI.
"""
from __future__ import annotations

from copy import deepcopy
import unittest

from shapely.geometry import Polygon

from scripts import n20_full_global_source_geometry as global_source


def graph(size, edges):
    return {
        "node_count": size,
        "undirected_edges": [list(e) for e in edges],
    }


class FullGlobalSourceGeometryTests(unittest.TestCase):
    def test_all_existing_fixed_nodes_always_mandatory(self):
        # New stations 0,1, fixed original 2,3; one fixed is isolated.
        g = graph(4, [(0, 1), (0, 2)])
        self.assertFalse(global_source.independent_union_find_connected(g, (0, 1), 2))
        self.assertEqual(global_source._full_component_count(g), 2)

    def test_derived_fixed_fixed_direct_edge_really_connects(self):
        # Both free/new have some fixed contact, but no component without a
        # specifically modeled existing-existing edge.
        g = graph(4, [(0, 2), (1, 3)])
        self.assertFalse(global_source.independent_union_find_connected(g, (0, 1), 2))
        g["undirected_edges"].append([2, 3])
        self.assertTrue(global_source.independent_union_find_connected(g, (0, 1), 2))

    def test_new_bridge_connects_fixeds_through_two_hops(self):
        g = graph(4, [(0, 1), (0, 2), (1, 3)])
        self.assertTrue(global_source.independent_union_find_connected(g, (0,), 2))
        self.assertTrue(global_source.independent_union_find_connected(g, (0, 1), 2))

    def test_optional_isolated_free_node_does_not_make_fixed_impossible(self):
        g = graph(5, [(1, 3), (1, 4)])
        self.assertTrue(global_source.independent_union_find_connected(g, (1,), 3))
        self.assertFalse(global_source.independent_union_find_connected(g, (0, 1), 3))
        self.assertEqual(global_source._full_component_count(g), 3)

    def test_duplicate_candidate_rejected_and_no_virtual_backhaul(self):
        g = graph(4, [(0, 2), (1, 3)])
        with self.assertRaisesRegex(ValueError, "duplicated"):
            global_source.independent_union_find_connected(g, (0, 0), 2)
        with self.assertRaisesRegex(ValueError, "Invalid or duplicated"):
            global_source.independent_union_find_connected(g, (5,), 2)
        self.assertFalse(global_source.independent_union_find_connected(g, (0, 1), 2))

    def test_invalid_edges_and_missing_fixed_endpoint_rejected(self):
        g = graph(4, [(0, 2), (0, 2)])
        with self.assertRaisesRegex(ValueError, "Repeated"):
            global_source.independent_union_find_connected(g, (0,), 2)
        g = graph(4, [(0, 4)])
        with self.assertRaisesRegex(ValueError, "Repeated or invalid"):
            global_source.independent_union_find_connected(g, (0,), 2)
        g = graph(4, [(2, 0)])
        with self.assertRaisesRegex(ValueError, "Repeated or invalid"):
            global_source.independent_union_find_connected(g, (0,), 2)

    def test_plain_square_geometry_constructs_exact_expected_links(self):
        square = Polygon([(0, 0), (8, 0), (8, 8), (0, 8)])
        sites = [(2., 2.), (6., 2.), (4., 2.), (4., 6.)]
        g = global_source.build_full_graph(sites, square, 4.1, 2)
        self.assertEqual(g["node_count"], 4)
        self.assertEqual(g["undirected_edges"], [[0, 1], [0, 2], [1, 2], [2, 3]])
        self.assertFalse(global_source.independent_union_find_connected(g, (0,), 2))
        self.assertTrue(global_source.independent_union_find_connected(g, (0, 1), 2))

    def test_hull_strictly_excludes_segment_through_land_gap(self):
        # U-shaped water hull; two water points have direct distance 6,
        # but their connecting segment crosses the polygon exterior.
        u = Polygon([
            (0, 0), (10, 0), (10, 10), (7, 10),
            (7, 3), (3, 3), (3, 10), (0, 10),
        ])
        g = global_source.build_full_graph(
            [(2., 8.), (8., 8.), (2., 2.), (8., 2.)], u, 7.0, 2,
        )
        self.assertNotIn([0, 1], g["undirected_edges"])
        self.assertIn([2, 3], g["undirected_edges"])

    def test_hull_boundary_and_too_distant_sites_not_connected(self):
        square = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        g = global_source.build_full_graph(
            [(0., 2.), (1., 2.), (8., 8.)], square, 2.0, 1,
        )
        self.assertEqual(g["undirected_edges"], [])

    def test_distance_threshold_ambiguous_edge_fails_closed(self):
        square = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        with self.assertRaisesRegex(ValueError, "ambiguity"):
            global_source.build_full_graph(
                [(2., 2.), (4., 2.), (8., 8.)], square, 2.0, 1,
            )

    def test_nonfinite_and_invalid_hull_refused(self):
        square = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        with self.assertRaisesRegex(ValueError, "Invalid projected"):
            global_source.build_full_graph(
                [(float("nan"), 1.), (2., 2.)], square, 3., 1
            )
        with self.assertRaisesRegex(ValueError, "invalid"):
            global_source.build_full_graph(
                [(2., 2.), (3., 2.)], Polygon(), 3., 1
            )

    def test_global_oracle_requires_all_original_fixed_stations(self):
        fake_model = {
            "candidate_master_feature_positions": list(range(20)),
            "fixed_master_feature_positions": list(range(20, 35)),
            "budget_exact": 5,
        }
        g = graph(34, [])
        with self.assertRaisesRegex(ValueError, "20/15/K5"):
            global_source.full_global_subset_oracle(fake_model, g)

    def test_numerical_global_matches_known_ux_reference_sha_canary(self):
        self.assertEqual(global_source.EXPECTED_GLOBAL_FEASIBLE, 860)
        self.assertEqual(
            global_source.EXPECTED_GLOBAL_FEASIBLE_SHA256,
            "3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40",
        )
        self.assertEqual(global_source.EXPECTED_FIXED_FIXED_EDGES, 17)
        self.assertEqual(global_source.EXPECTED_GLOBAL_WINNER, [0, 1, 3, 6, 7])


if __name__ == "__main__":
    unittest.main()
