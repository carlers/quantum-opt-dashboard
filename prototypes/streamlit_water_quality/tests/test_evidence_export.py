"""Headless N20 reproducibility bundle contract and scientific evidence checks."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence import (
    BUDGET, N_FREE, PAPER_REPORTED_SCIP_ENERGY, SCENARIO_NOTES,
    TABLE_III, eigenvector_weights, enumerated_optimum, weights_for,
    write_bundle,
)
from model import Instance, PAPER_WEIGHTS, NOTEBOOK_WEIGHTS


def test_ahp_weight_scenario_ids_are_not_interchangeable():
    assert set(SCENARIO_NOTES) == {"notebook", "paper-table-iv", "table-iii-eigen"}
    np.testing.assert_array_equal(weights_for("notebook"), NOTEBOOK_WEIGHTS)
    np.testing.assert_array_equal(weights_for("paper-table-iv"), PAPER_WEIGHTS)
    np.testing.assert_allclose(weights_for("table-iii-eigen"), eigenvector_weights())
    assert float(weights_for("table-iii-eigen").sum()) == pytest.approx(1, abs=1e-12)
    assert not np.allclose(weights_for("notebook"), weights_for("paper-table-iv"))
    assert not np.allclose(weights_for("table-iii-eigen"), weights_for("paper-table-iv"))
    assert TABLE_III.shape == (4, 4)
    with pytest.raises(ValueError, match="Unknown"):
        weights_for("published-historical-scip")


def test_exhaustive_enumerator_respects_all_combinations_and_feasibility():
    # All 20 sites independently adjacent to an existing station; no pairs.
    # The five most negative coefficients have a unique global optimum.
    instance = Instance(
        coords=np.zeros((21, 2)),
        free_indices=np.arange(20), fixed_indices=np.array([20]),
        utility=np.zeros(21),
        linear=np.array([-5, -4, -3, -2, -1] + [0] * 15, dtype=float),
        quadratic=(),
        neighbors=tuple(() for _ in range(20)),
        fixed_neighbors=np.ones(20, dtype=int),
        budget=5, d_max=5000.,
    )
    ref = enumerated_optimum(instance)
    assert ref["combinations_checked"] == 15504
    assert ref["feasible_count"] == 15504
    assert ref["minimum_energy"] == pytest.approx(-15.0)
    assert ref["optimal_local_index_sets"] == [[0, 1, 2, 3, 4]]

    # No station is adjacent to any existing or new station -> infeasible.
    disconnected = Instance(
        coords=instance.coords, free_indices=instance.free_indices,
        fixed_indices=instance.fixed_indices, utility=instance.utility,
        linear=instance.linear, quadratic=(), neighbors=instance.neighbors,
        fixed_neighbors=np.zeros(20, dtype=int), budget=5, d_max=5000.,
    )
    with pytest.raises(RuntimeError, match="No feasible"):
        enumerated_optimum(disconnected)


def test_headless_exports_three_proven_n20_scip_scenarios(tmp_path):
    manifest = write_bundle(tmp_path, tuple(SCENARIO_NOTES), 90.)
    expect = {
        "notebook": -3.3012934918564643,
        "paper-table-iv": -3.473640036773477,
        "table-iii-eigen": -3.629863700075275,
    }
    assert len(manifest["scenarios"]) == len(expect)
    assert len(manifest["file_sha256"]) == 12
    assert json.loads((tmp_path / "manifest.json").read_text()) == manifest
    for relative_path, expected_sha in manifest["file_sha256"].items():
        file = tmp_path / relative_path
        assert file.is_file()
        assert hashlib.sha256(file.read_bytes()).hexdigest() == expected_sha

    for scenario, expected_energy in expect.items():
        directory = tmp_path / scenario
        config = json.loads((directory / "config.json").read_text())
        instance = json.loads((directory / "instance.json").read_text())
        result = json.loads((directory / "result.json").read_text())
        rows = (directory / "sites.csv").read_text().splitlines()
        assert config["scenario"] == result["scenario"] == scenario
        assert config["budget_new_stations"] == BUDGET == 5
        assert config["n_free"] == N_FREE == 20
        assert instance["n_fixed_used"] == instance["num_marked_existing"] == 15
        assert instance["fixed_was_simulated"] is False
        assert instance["num_geojson_features"] == 5417
        assert len(instance["free_master_feature_positions"]) == 20
        assert len(instance["coords_easting_northing_m"]) == 35
        assert len(rows) == 21  # one header and one row per free candidate
        assert result["instance_sha256"] == manifest["scenarios"][
            list(expect).index(scenario)]["instance_sha256"]
        assert result["proven_optimal"] is True
        assert result["status"] == "optimal"
        assert result["solver_energy"] == pytest.approx(expected_energy, abs=1e-7)
        assert result["feasibility"]["feasible"]
        assert result["feasibility"]["local_connectivity_ok"]
        assert result["feasibility"]["budget_ok"]
        assert result["feasibility"]["selected_count"] == 5
        assert result["selected_local_candidate_positions"] == [0, 1, 3, 6, 7]
        assert result["selected_geojson_master_feature_positions"] == [
            5253, 2394, 1557, 47, 5409
        ]
        assert result["paper_comparison_reference_only"][
            "historical_paper_scip_energy"] == PAPER_REPORTED_SCIP_ENERGY
        assert result["paper_comparison_reference_only"][
            "historical_input_equivalence_verified"] is False
        assert result["independent_enumeration"]["combinations_checked"] == 15504
        assert result["solver_energy"] == pytest.approx(
            result["independent_enumeration"]["minimum_energy"], abs=1e-7
        )
        components = result["objective_components"]
        assert components["linear"] + components["quadratic_free_free"] == pytest.approx(
            result["solver_energy"], abs=1e-9
        )

    # A one-byte modification is visibly detectable via the manifest.
    file = tmp_path / "notebook" / "result.json"
    file.write_bytes(file.read_bytes() + b" ")
    assert hashlib.sha256(file.read_bytes()).hexdigest() != manifest["file_sha256"][
        "notebook/result.json"
    ]
