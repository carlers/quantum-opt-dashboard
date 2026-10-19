"""Adversarial tests for preregistered N20 S0/S1/S2 anchored-graph metrics."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import math
import unittest

from scripts.studies.n20_anchor_connectivity_sensitivity import (
    EXPECTED_ARCHIVE, EXPECTED_DATA, EXPECTED_EMPTY_CANDIDATES,
    EXPECTED_FREE_MASTER, EXPECTED_FIXED_MASTER, EXPECTED_S0_CHOICE,
    EXPECTED_S0_ENERGY, EXPECTED_S0_SETS_SHA,
    admissibility, analyze, canonical, checked_graph, checked_inputs,
    raw_energy, selected_components, sha,
)


def blank_graph():
    return [[] for _ in range(20)], [[] for _ in range(20)]


def synthetic_source():
    neighbors, links = blank_graph()
    model = {
        "schema_version": 1,
        "dataset_sha256": EXPECTED_DATA,
        "archived_notebook_sha256": EXPECTED_ARCHIVE,
        "candidate_master_feature_positions": list(EXPECTED_FREE_MASTER),
        "fixed_master_feature_positions": list(EXPECTED_FIXED_MASTER),
        "budget_exact": 5,
        "free_neighbor_indices": neighbors,
        "fixed_neighbor_flags": [0] * 20,
        "linear_float64_hex": [float(-0.7).hex()] * 20,
        "quadratic_ij_float64_hex": [
            [i, i + 1, float(0.01).hex()] for i in range(12)
        ],
    }
    g = {
        "candidate_master_feature_positions": list(EXPECTED_FREE_MASTER),
        "existing_station_master_feature_positions": list(EXPECTED_FIXED_MASTER),
        "free_neighbor_indices_from_geojson": deepcopy(neighbors),
        "fixed_neighbor_flags_from_geojson": [0] * 20,
        "free_fixed_links_local_existing_positions": links,
        "free_fixed_edges": 0,
        "feasible_combinations": 1077,
        "feasible_site_sets_sha256": EXPECTED_S0_SETS_SHA,
    }
    record = {
        "schema_version": 2,
        "status": "notebook_derived_N20_replay_not_paper_parity",
        "dataset_sha256": EXPECTED_DATA,
        "archived_notebook_sha256": EXPECTED_ARCHIVE,
        "candidate_count": 20,
        "new_station_budget": 5,
        "marked_existing_stations": 15,
        "enumerated_combinations": 15504,
        "feasible_combinations": 1077,
        "feasible_site_sets_sha256": EXPECTED_S0_SETS_SHA,
        "selected_local_positions": list(EXPECTED_S0_CHOICE),
        "scip_status": "optimal",
        "local_one_hop_not_global_connectivity": True,
        "original_energy": EXPECTED_S0_ENERGY,
        "model_input": model,
        "model_input_sha256": sha(model),
    }
    geo = {
        "schema_version": 1,
        "source_data_sha256": EXPECTED_DATA,
        "model_input_sha256": record["model_input_sha256"],
        "spatial_graph": g,
        "spatial_graph_sha256": sha(g),
    }
    return record, geo


class PreregisteredAnchorReachabilityTests(unittest.TestCase):
    def test_unanchored_two_site_cycle_passes_S0_but_not_S1_or_S2(self):
        neighbors, links = blank_graph()
        neighbors[0] = [1]
        neighbors[1] = [0]
        r = admissibility((0, 1), neighbors, links)
        self.assertTrue(r["S0"])
        self.assertFalse(r["S1"])
        self.assertFalse(r["S2"])
        self.assertEqual(r["new_only_component_count"], 1)
        self.assertEqual(r["anchored_component_count"], 0)

    def test_two_components_different_fixed_stations_pass_S1_not_S2(self):
        neighbors, links = blank_graph()
        links[0], links[2] = [0], [1]
        r = admissibility((0, 2), neighbors, links)
        self.assertTrue(r["S0"])
        self.assertTrue(r["S1"])
        self.assertFalse(r["S2"])
        self.assertEqual(r["new_only_component_count"], 2)

    def test_shared_real_fixed_hub_joins_two_separate_new_components_S2(self):
        neighbors, links = blank_graph()
        links[0], links[2] = [0], [0]
        r = admissibility((0, 2), neighbors, links)
        self.assertTrue(all(r[k] for k in ("S0", "S1", "S2")))

    def test_new_only_connectivity_not_automatically_anchored(self):
        neighbors, links = blank_graph()
        neighbors[0], neighbors[1], neighbors[2] = [1], [0, 2], [1]
        r = admissibility((0, 1, 2), neighbors, links)
        self.assertTrue(r["S0"])
        self.assertFalse(r["S1"])
        self.assertFalse(r["S2"])
        self.assertEqual(selected_components((0, 1, 2), neighbors), [(0, 1, 2)])

    def test_one_new_individual_fixed_contact_is_anchored(self):
        neighbors, links = blank_graph()
        links[4] = [13]
        r = admissibility((4,), neighbors, links)
        self.assertTrue(r["S0"])
        self.assertTrue(r["S1"])
        self.assertTrue(r["S2"])

    def test_empty_singleton_without_eligible_neighbor_fails_every_scenario(self):
        neighbors, links = blank_graph()
        r = admissibility((18,), neighbors, links)
        self.assertFalse(r["S0"])
        self.assertFalse(r["S1"])
        self.assertFalse(r["S2"])

    def test_generated_graph_rejects_asymmetric_free_edges(self):
        neighbors, links = blank_graph()
        neighbors[0] = [2]
        with self.assertRaisesRegex(ValueError, "Asymmetric"):
            checked_graph(neighbors, [0] * 20, links)

    def test_stored_fixed_neighbor_flag_must_follow_actual_GeoJSON_links(self):
        neighbors, links = blank_graph()
        links[15] = [2]
        with self.assertRaisesRegex(ValueError, "Fixed flags"):
            checked_graph(neighbors, [0] * 20, links)

    def test_forbid_invented_existing_fixed_station_index(self):
        neighbors, links = blank_graph()
        links[0] = [15]
        flags = [0] * 20
        flags[0] = 1
        with self.assertRaisesRegex(ValueError, "Invalid verified"):
            checked_graph(neighbors, flags, links)

    def test_graph_validation_rejects_forged_off_winner_geometry(self):
        record, geo = synthetic_source()
        geo["spatial_graph"]["fixed_neighbor_flags_from_geojson"][18] = 1
        geo["spatial_graph_sha256"] = sha(geo["spatial_graph"])
        with self.assertRaisesRegex(ValueError, "graph differs"):
            checked_inputs(record, geo)

    def test_graph_validation_rejects_forged_source_geojson_digest(self):
        record, geo = synthetic_source()
        geo["source_data_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "geometry certificate differs"):
            checked_inputs(record, geo)

    def test_graph_validation_rejects_tampered_geometry_digest(self):
        record, geo = synthetic_source()
        geo["spatial_graph_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "geometry certificate differs"):
            checked_inputs(record, geo)

    def test_graph_validation_rejects_swapped_candidate_ids(self):
        record, geo = synthetic_source()
        record["model_input"]["candidate_master_feature_positions"][0] = 100
        record["model_input_sha256"] = sha(record["model_input"])
        with self.assertRaisesRegex(ValueError, "candidate/fixed station"):
            checked_inputs(record, geo)

    def test_invalid_full_model_must_not_fake_an_S0_result(self):
        record, geo = synthetic_source()
        # The fake graph has no feasible 5-site subset, but metadata incorrectly
        # claims the source canary. analyze() MUST independently reject it.
        with self.assertRaisesRegex(ValueError, "Source control S0"):
            analyze(record, geo)

    def test_exact_original_source_energy_uses_original_order_not_fsum(self):
        src = (-0.1, -0.2, -0.3)
        value = raw_energy((0, 1), list(src), [(0, 1, 0.09)])
        self.assertEqual(value, sum([src[0], src[1]]) + 0.09)

    def test_output_json_is_hash_stable_and_float_hex_is_not_rewritten(self):
        sample = {"x": [float(0.5).hex()], "z": -1.2}
        self.assertEqual(sha(sample), hashlib.sha256(canonical(sample)).hexdigest())


if __name__ == "__main__":
    unittest.main()
