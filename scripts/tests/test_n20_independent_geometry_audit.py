"""Adversarial N20 local geometry contract tests, no lake GIS or SCIP needed.

A separate cold CI job runs these alongside the ACTUAL 5417-feature
source-verified original GeoJSON and fresh notebook result.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from shapely.geometry import Polygon

from scripts import n20_independent_geometry_audit as geom


def fixture():
    """Artificial 35-site polygon/positions: tests logic, not lake science."""
    free = [(10.0 + i * 4.0, 15.0 + (i % 5) * 6.0) for i in range(20)]
    fixed = [(15.0 + (i % 5) * 20.0, 65.0 + (i // 5) * 8.0)
             for i in range(15)]
    features = [(1.0, 1.0)] * 5417
    for id_, pos in zip(geom.EXPECTED_FREE, free):
        features[id_] = pos
    for id_, pos in zip(geom.EXPECTED_FIXED, fixed):
        features[id_] = pos
    polygon = Polygon([(0, 0), (120, 0), (120, 110), (0, 110)])
    dmax = geom.original_fixed_spacing(fixed)
    edges = geom.reconstruct(free + fixed, polygon, dmax, 20)
    feasible, digest = geom.feasible_subsets(
        edges["free_neighbor_indices"], edges["fixed_neighbor_flags"]
    )
    record = {
        "dataset_sha256": geom.EXPECTED_DATA_SHA,
        "model_input_sha256": "0" * 64,  # synthetic no claims of a real source model
        "feasible_combinations": feasible,
        "feasible_site_sets_sha256": digest,
        "model_input": {
            "dataset_sha256": geom.EXPECTED_DATA_SHA,
            "candidate_master_feature_positions": geom.EXPECTED_FREE[:],
            "fixed_master_feature_positions": geom.EXPECTED_FIXED[:],
            "site_coords_epsg32651_float64_hex":
                [[p[0].hex(), p[1].hex()] for p in free + fixed],
            "hull_ratio_float64_hex": geom.HULL_RATIO.hex(),
            "fixed_spacing_buffer_float64_hex":
                geom.FIXED_SPACING_BUFFER.hex(),
            "d_max_m_float64_hex": dmax.hex(),
            "free_neighbor_indices": edges["free_neighbor_indices"],
            "fixed_neighbor_flags": edges["fixed_neighbor_flags"],
        },
    }
    return record, features, polygon, feasible


class IndependentGeometryTests(unittest.TestCase):
    def test_synthetic_lake_edges_and_full_region_validate(self):
        record, coords, hull, count = fixture()
        with (patch.object(geom, "source_coordinates",
                           return_value=(coords, geom.EXPECTED_FIXED)),
              patch.object(geom, "concave_hull", return_value=hull),
              patch.object(geom, "EXPECTED_FEASIBLE", count)):
            report = geom.certify_geometry(record)
        self.assertEqual(report["spatial_graph"]["feasible_combinations"], count)
        self.assertEqual(report["spatial_graph"]["feasible_site_sets_sha256"],
                         record["feasible_site_sets_sha256"])
        self.assertEqual(
            report["spatial_graph"]["free_neighbor_indices_from_geojson"],
            record["model_input"]["free_neighbor_indices"],
        )

    def test_changed_unselected_graph_edge_detected_independently(self):
        record, coords, hull, count = fixture()
        record["model_input"]["fixed_neighbor_flags"][19] = (
            1 - record["model_input"]["fixed_neighbor_flags"][19]
        )
        with (patch.object(geom, "source_coordinates",
                           return_value=(coords, geom.EXPECTED_FIXED)),
              patch.object(geom, "concave_hull", return_value=hull),
              patch.object(geom, "EXPECTED_FEASIBLE", count)):
            with self.assertRaisesRegex(AssertionError, "Free/fixed one-hop flags"):
                geom.certify_geometry(record)

    def test_changed_reported_coordinate_detected_before_graph_compare(self):
        record, coords, hull, count = fixture()
        record["model_input"]["site_coords_epsg32651_float64_hex"][19][0] = (
            (float.fromhex(
                record["model_input"]["site_coords_epsg32651_float64_hex"][19][0]
            ) + 0.5).hex()
        )
        with (patch.object(geom, "source_coordinates",
                           return_value=(coords, geom.EXPECTED_FIXED)),
              patch.object(geom, "concave_hull", return_value=hull)):
            with self.assertRaisesRegex(AssertionError, "coordinates differ"):
                geom.certify_geometry(record)

    def test_forged_spacing_threshold_rejected(self):
        record, coords, hull, count = fixture()
        record["model_input"]["d_max_m_float64_hex"] = float(25).hex()
        with (patch.object(geom, "source_coordinates",
                           return_value=(coords, geom.EXPECTED_FIXED)),
              patch.object(geom, "concave_hull", return_value=hull)):
            with self.assertRaisesRegex(AssertionError, "spacing and Dmax"):
                geom.certify_geometry(record)

    def test_forged_feasible_hash_detected_even_if_adjacency_is_valid(self):
        record, coords, hull, count = fixture()
        record["feasible_site_sets_sha256"] = "f" * 64
        with (patch.object(geom, "source_coordinates",
                           return_value=(coords, geom.EXPECTED_FIXED)),
              patch.object(geom, "concave_hull", return_value=hull),
              patch.object(geom, "EXPECTED_FEASIBLE", count)):
            with self.assertRaisesRegex(AssertionError, "membership SHA-256"):
                geom.certify_geometry(record)

    def test_crossing_land_does_not_create_false_water_edge(self):
        # Two vertices are inside opposing arms of the U; the straight
        # connection crosses land/exterior, although their distance is < 9m.
        hull = Polygon([
            (0, 0), (12, 0), (12, 12), (8, 12),
            (8, 4), (4, 4), (4, 12), (0, 12),
        ])
        points = [(2.0, 10.0), (10.0, 10.0), (2.0, 2.0)]
        result = geom.reconstruct(points, hull, 9.0, 2)
        self.assertEqual(result["free_neighbor_indices"], [[], []])
        self.assertEqual(result["fixed_neighbor_flags"], [1, 0])
        self.assertEqual(result["free_fixed_raw_edges"], 1)

    def test_boundary_point_is_excluded_like_hull_contains(self):
        hull = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        points = [(0.0, 5.0), (2.0, 5.0), (2.0, 7.0)]
        result = geom.reconstruct(points, hull, 4.0, 2)
        self.assertEqual(result["free_neighbor_indices"], [[], []])
        self.assertEqual(result["fixed_neighbor_flags"], [0, 1])

    def test_source_sha_is_required_before_parsing_source_geojson(self):
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "altered.geojson"
            file.write_text('{"features":[]}', encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "SHA-256"):
                geom.source_coordinates(file)

    def test_invalid_threshold_is_fatal(self):
        hull = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        with self.assertRaisesRegex(ValueError, "threshold"):
            geom.reconstruct([(2, 2), (5, 5)], hull, math.nan, 1)

    def test_near_threshold_edge_requires_manual_precision_review(self):
        # Geometry audit itself records the ambiguous point; the strict
        # top-level scientific validator refuses automatic confidence.
        hull = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        audit = geom.reconstruct([(2.0, 2.0), (5.0, 2.0)], hull, 3.0, 1)
        self.assertEqual(len(audit["near_threshold_pairs_1e_minus_7_m"]), 1)

    def test_original_station_spacing_calculated_not_trusted_from_record(self):
        fixed = [(1.0, 1.0), (4.0, 1.0), (4.0, 5.0)]
        self.assertAlmostEqual(
            geom.original_fixed_spacing(fixed), 4.0 * 1.15, places=12
        )


if __name__ == "__main__":
    unittest.main()
