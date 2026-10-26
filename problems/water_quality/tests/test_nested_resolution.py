"""Source-backed nested-cohort gates; no heavy SCIP or SA experiment."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from problems.water_quality.nested_resolution import (
    INITIAL_TIERS, REFERENCE_GEOJSON, _validate_tiers, build_nested_instances,
)
from prototypes.streamlit_water_quality.model import (
    NOTEBOOK_WEIGHTS, evaluate, load_data, make_instance,
)

SOURCE_SHA256 = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
FROZEN_N20_MASTER_POSITIONS = (
    5253, 2394, 1894, 1557, 3225, 4623, 47, 5409, 3922, 2408,
    2694, 4136, 2567, 1164, 4973, 4537, 2726, 968, 16, 1762,
)


@pytest.fixture(scope="module")
def study():
    return build_nested_instances()


@pytest.mark.parametrize("tiers", [
    (), (20, 20), (50, 20), (20, 200), (20, 50.0),
])
def test_reject_unsupported_or_noncanonical_tiers(tiers):
    with pytest.raises(ValueError):
        _validate_tiers(tiers)


def test_source_identity_and_all_tier_prefixes(study):
    assert study.source_sha256 == SOURCE_SHA256
    assert study.source_sha256 == sha256(REFERENCE_GEOJSON.read_bytes()).hexdigest()
    assert study.source_feature_count == 5417
    assert len(study.fixed_master_positions) == 15
    assert not study.fixed_simulated
    assert tuple(row.n_free for row in study.tier_instances) == INITIAL_TIERS
    full = study.tier_instances[-1].candidate_master_positions
    for row in study.tier_instances:
        instance = row.instance
        assert row.candidate_master_positions == full[:row.n_free]
        assert len(set(row.candidate_master_positions)) == row.n_free
        assert not set(row.candidate_master_positions) & set(study.fixed_master_positions)
        assert tuple(int(i) for i in instance.free_indices) == row.candidate_master_positions
        assert tuple(int(i) for i in instance.fixed_indices) == study.fixed_master_positions
        assert len(instance.coords) == row.n_free + len(study.fixed_master_positions)
        assert len(instance.linear) == row.n_free
        assert len(instance.neighbors) == row.n_free
        assert len(instance.fixed_neighbors) == row.n_free
        assert instance.budget == 5


def test_feature_ids_are_not_confused_with_source_positions(study):
    data = load_data(REFERENCE_GEOJSON)
    assert study.fixed_feature_ids == tuple(int(data.ids[i]) for i in study.fixed_master_positions)
    for row in study.tier_instances:
        assert row.candidate_feature_ids == tuple(int(data.ids[i]) for i in row.candidate_master_positions)


def test_frozen_n20_model_selection_energy_and_feasibility(study):
    row = study.tier_instances[0]
    assert row.candidate_master_positions == FROZEN_N20_MASTER_POSITIONS
    bits = np.zeros(20, dtype=int)
    bits[[0, 1, 3, 6, 7]] = 1
    result = evaluate(row.instance, bits)
    assert result["feasible"]
    assert result["energy"] == pytest.approx(-3.3012934918564643, abs=1e-6)
    data = load_data(REFERENCE_GEOJSON)
    independently_built, simulated = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    assert not simulated
    np.testing.assert_array_equal(row.instance.free_indices, independently_built.free_indices)
    np.testing.assert_array_equal(row.instance.fixed_indices, independently_built.fixed_indices)
    np.testing.assert_allclose(row.instance.linear, independently_built.linear, rtol=0, atol=0)
    assert row.instance.quadratic == independently_built.quadratic


def test_manifest_records_provenance_not_solver_claims(study):
    manifest = study.manifest()
    encoded = json.loads(json.dumps(manifest))
    assert encoded["schema_version"] == "nested-source-cohorts-v1"
    assert encoded["source_sha256"] == SOURCE_SHA256
    assert encoded["solver_executed"] is False
    assert encoded["paper_parity_claimed"] is False
    assert [t["n_free"] for t in encoded["tiers"]] == [20, 50, 100]
    assert encoded["tiers"][0]["candidate_master_positions"] == list(FROZEN_N20_MASTER_POSITIONS)


def test_independent_raw_source_fps_recovers_all_three_tiers(study):
    """Independent notebook Cell 3 reconstruction: no production FPS helpers.

    Rebuilds the 10k bbox lattice directly from *raw* GeoJSON coordinates,
    water hull containment, nearest-master unique eligible pool and sequential
    farthest-point choices. Confirms N50/100 are not just mutually consistent
    results of a defective shared helper.
    """
    from scipy.spatial import cKDTree
    from shapely import concave_hull
    from shapely.geometry import MultiPoint, Point

    raw = json.loads(REFERENCE_GEOJSON.read_text(encoding="utf-8"))["features"]
    source_xy = np.array([f["geometry"]["coordinates"][:2] for f in raw], dtype=float)
    fixed = np.flatnonzero([
        bool(f["properties"].get("has_existing_station", False))
        for f in raw
    ])
    assert tuple(fixed) == study.fixed_master_positions
    water = concave_hull(MultiPoint(source_xy), ratio=0.05, allow_holes=True)
    xmin, ymin = source_xy.min(axis=0)
    xmax, ymax = source_xy.max(axis=0)
    dx = np.sqrt(((xmax - xmin) * (ymax - ymin) / 10000) / (np.sqrt(3) / 2))
    dy = dx * np.sqrt(3) / 2
    candidates = []
    for row in range(int(np.ceil((ymax - ymin) / dy)) + 1):
        y = ymin + row * dy
        if y > ymax:
            continue
        for col in range(int(np.ceil((xmax - xmin) / dx)) + 1):
            x = xmin + col * dx + (0.5 * dx if row % 2 else 0)
            if x <= xmax and water.contains(Point(float(x), float(y))):
                candidates.append((x, y))
    snapped = cKDTree(source_xy).query(np.array(candidates), k=1)[1]
    eligible = np.unique(snapped[~np.isin(snapped, fixed)])
    distances = cKDTree(source_xy[fixed]).query(source_xy[eligible], k=1)[0]
    independent: list[int] = []
    for _ in range(100):
        offset = int(np.argmax(distances))
        independent.append(int(eligible[offset]))
        difference = source_xy[eligible] - source_xy[eligible[offset]]
        distances = np.minimum(distances, np.sqrt(np.sum(difference * difference, axis=1)))
        distances[offset] = -1.
    assert tuple(independent[:20]) == FROZEN_N20_MASTER_POSITIONS
    for tier in study.tier_instances:
        assert tier.candidate_master_positions == tuple(independent[:tier.n_free])
