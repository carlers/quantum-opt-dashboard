"""N=20 independent reference reconstruction from notebook Cells 2-4.

Do not interpret agreement with this reconstruction as publication replication:
the paper's AHP weights, existing-station configuration, and D2 semantics differ.
This test deliberately does not import pilot sampling/objective/feasibility helpers.
"""
from __future__ import annotations

from itertools import combinations
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pytest
from scipy.spatial import cKDTree
from shapely import concave_hull
from shapely.geometry import LineString, MultiPoint, Point

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import (NOTEBOOK_WEIGHTS, PAPER_WEIGHTS, load_data, make_instance, solve_scip)

ROOT = Path(__file__).resolve().parents[3]
GEOJSON = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
NOTEBOOK = ROOT / "problems/water_quality/notebooks/experiment9 grid search copy.ipynb"
FACTOR_KEYS = (
    "a1_river_proximity", "a2_runoff_proximity", "b1_fishpen_density",
    "b2_hypoxic_proximity", "c1_bathymetric_depressions",
    "c2_outlet_proximity", "d1_boatramp_proximity", "d2_road_proximity",
)
NOTEBOOK_EXPECTED = np.array(
    [0.3671, 0.1224, 0.2508, 0.0502, 0.1278, 0.0183, 0.0476, 0.0159]
)
PAPER_EXPECTED = np.array(
    [0.276095907, 0.276095907, 0.179220150, 0.089610075,
     0.087188181, 0.043594091, 0.024097845, 0.024097845]
)
# Counterfactual AHP scenario: principal eigenvector of the *printed*
# Table III main matrix, split by its own four 2x2 local matrices.
# This is not the published Table IV vector or a claim of original elicitation.
PAPER_MATRIX_EIGEN_WEIGHTS = np.array([
    0.30848767748481226, 0.30848767748481226,
    0.15221292182361240, 0.07610646091180620,
    0.06974006275820807, 0.03487003137910404,
    0.02504758407882235, 0.02504758407882235,
])
PAPER_ENERGY_N20 = -3.301319
PAPER_SELECTED_N20 = [0, 1, 3, 6, 7]


def independent_reference(weights: np.ndarray) -> dict:
    """Cold reconstruction, independent of model.py, mirroring source cells.

    Reuses NumPy/SciPy/Shapely primitives, not pilot helper functions.
    Indices are zero-based GeoJSON feature positions, not GeoJSON property IDs.
    """
    raw = json.loads(GEOJSON.read_text(encoding="utf-8"))
    features = raw["features"]
    coords = np.array([f["geometry"]["coordinates"][:2] for f in features], dtype=float)
    factors = np.array([
        [np.nan if f["properties"].get(name) is None else
         float(f["properties"][name]) for name in FACTOR_KEYS]
        for f in features
    ])
    actual_marked = np.flatnonzero([
        bool(f["properties"].get("has_existing_station", False))
        for f in features
    ]).tolist()

    # Notebook Cell 2: skip null criterion values, re-normalize per row.
    valid = ~np.isnan(factors)
    numerator = np.nansum(factors * weights, axis=1)
    denominator = np.nansum(valid * weights, axis=1)
    utility = np.clip(numerator / np.where(denominator == 0, 1.0, denominator), 0, 1)
    if actual_marked:
        fixed = actual_marked
    else:
        # Notebook Cell 2: explicitly simulated fallback, never count as observed.
        fixed = [int(np.argmax(utility))]
        for _ in range(2):
            near = np.linalg.norm(coords[:, None] - coords[fixed][None], axis=2).min(axis=1)
            possible = np.flatnonzero(
                (near >= 12000) & (~np.isin(np.arange(len(coords)), fixed))
            )
            best = int(possible[np.argmax(utility[possible])]) if len(possible) else int(np.argmax(near))
            fixed.append(best)
    hull = concave_hull(MultiPoint(coords), ratio=0.05, allow_holes=True)
    # Notebook Cell 3: bbox hex pool -> nearest master -> unique -> seeded FPS.
    xmin, ymin = np.min(coords, axis=0)
    xmax, ymax = np.max(coords, axis=0)
    dx = np.sqrt((xmax - xmin) * (ymax - ymin) / 10000 / (np.sqrt(3) / 2))
    dy = dx * np.sqrt(3) / 2
    pool = [
        (xmin + column * dx + (dx / 2 if row % 2 else 0), ymin + row * dy)
        for row in range(int(np.ceil((ymax - ymin) / dy)) + 1)
        for column in range(int(np.ceil((xmax - xmin) / dx)) + 1)
        if ymin + row * dy <= ymax
        and xmin + column * dx + (dx / 2 if row % 2 else 0) <= xmax
    ]
    water = np.array([point for point in pool if hull.contains(Point(point))])
    assert len(water) > 0, "No water points: cannot form notebook FPS candidates"
    snapped = cKDTree(coords).query(water, k=1)[1]
    remaining = np.unique(snapped[~np.isin(snapped, fixed)])
    assert len(remaining) >= 20
    closest = cKDTree(coords[fixed]).query(coords[remaining], k=1)[0]
    selected = []
    for _ in range(20):
        offset = int(np.argmax(closest))
        chosen = int(remaining[offset])
        selected.append(chosen)
        closest = np.minimum(closest, np.linalg.norm(coords[remaining] - coords[chosen], axis=1))
        closest[offset] = -1.0

    # Notebook Cell 4: neighborhood and symmetric wake interactions.
    positions = np.vstack([coords[selected], coords[fixed]])
    n = 20
    all_fixed = list(range(n, len(positions)))
    d_nearest = cKDTree(coords[fixed]).query(coords[fixed], k=2)[0][:, 1] if len(fixed) > 1 else np.array([])
    d_max = float(np.max(d_nearest) * 1.15) if len(fixed) > 1 else 15000.
    linear = -utility[selected].copy()
    penalties = []
    adjacent = [set() for _ in range(n)]
    has_fixed_neighbor = np.zeros(n, dtype=int)

    for i, j in combinations(range(len(positions)), 2):
        p, q = positions[i], positions[j]
        if not (hull.contains(Point(p)) and hull.contains(Point(q))
                and hull.contains(LineString([p, q]))):
            continue
        vector = q - p
        distance = float(np.linalg.norm(vector))
        if distance == 0:
            continue
        if distance <= d_max:
            if i < n and j < n:
                adjacent[i].add(j)
                adjacent[j].add(i)
            elif i < n and j in all_fixed:
                has_fixed_neighbor[i] = 1
            elif j < n and i in all_fixed:
                has_fixed_neighbor[j] = 1
        if distance > 15000:
            continue
        redundancy = max(0.0, 1.0 - distance / 7500.)
        cosine = float(np.clip(vector[0] / distance, -1.0, 1.0))
        wake_forward = np.exp(-distance / 1000.) * cosine if cosine > 0.7071 else 0.0
        wake_backward = -np.exp(-distance / 1000.) * cosine if -cosine > 0.7071 else 0.0
        coefficient = float(redundancy + wake_forward + wake_backward)
        if abs(coefficient) <= 1e-12:
            continue
        if i < n and j < n:
            penalties.append((i, j, coefficient))
        elif i < n:
            linear[i] += coefficient
        elif j < n:
            linear[j] += coefficient

    return {
        "selected": np.array(selected, dtype=int),
        "fixed": np.array(fixed, dtype=int),
        "marked_count": len(actual_marked),
        "utility": utility,
        "linear": linear,
        "quadratic": tuple(penalties),
        "neighbors": tuple(tuple(sorted(s)) for s in adjacent),
        "fixed_neighbors": has_fixed_neighbor,
        "d_max": d_max,
    }


def exact_brute_force(reference: dict) -> tuple[float, list[tuple[int, ...]]]:
    """Independent objective/feasibility calculation over all C(20,5)=15504 subsets."""
    n = len(reference["selected"])
    best = float("inf")
    ties = []
    for sites in combinations(range(n), 5):
        chosen = set(sites)
        if any(
            not (reference["fixed_neighbors"][i]
                 or bool(chosen.intersection(reference["neighbors"][i])))
            for i in chosen
        ):
            continue
        energy = sum(reference["linear"][i] for i in sites)
        energy += sum(value for i, j, value in reference["quadratic"] if i in chosen and j in chosen)
        if energy < best - 1e-9:
            best, ties = energy, [sites]
        elif abs(energy - best) <= 1e-9:
            ties.append(sites)
    if not ties:
        raise AssertionError("Reference N=20 problem has no feasible five-site selections")
    return float(best), ties


@pytest.mark.parametrize(
    ("label", "weights"),
    [("notebook", NOTEBOOK_EXPECTED),
     ("paper-weight sensitivity", PAPER_EXPECTED),
     ("paper-table-iii eigenvector sensitivity", PAPER_MATRIX_EIGEN_WEIGHTS)],
)
def test_n20_reference_matches_pilot_and_scip(label, weights):
    assert GEOJSON.is_file() and NOTEBOOK.is_file(), "Immutable sources must be committed"
    np.testing.assert_allclose(NOTEBOOK_WEIGHTS, NOTEBOOK_EXPECTED, rtol=0, atol=1e-12)
    np.testing.assert_allclose(PAPER_WEIGHTS, PAPER_EXPECTED, rtol=0, atol=1e-12)

    reference = independent_reference(weights)
    data = load_data(GEOJSON)
    instance, simulated = make_instance(data, weights, 20, 5)
    assert simulated == (reference["marked_count"] == 0)
    np.testing.assert_array_equal(instance.free_indices, reference["selected"])
    np.testing.assert_array_equal(instance.fixed_indices, reference["fixed"])
    np.testing.assert_allclose(instance.utility[:20], reference["utility"][reference["selected"]],
                               atol=1e-12, rtol=0)
    np.testing.assert_allclose(instance.linear, reference["linear"], atol=1e-12, rtol=0)
    assert len(instance.quadratic) == len(reference["quadratic"])
    np.testing.assert_allclose(instance.quadratic, reference["quadratic"], atol=1e-12, rtol=0)
    assert instance.neighbors == reference["neighbors"]
    np.testing.assert_array_equal(instance.fixed_neighbors, reference["fixed_neighbors"])
    assert instance.d_max == pytest.approx(reference["d_max"], abs=1e-8)

    expected_energy, expected_sites = exact_brute_force(reference)
    values, result = solve_scip(instance, time_limit=120.)
    assert result["status"] == "optimal", "A time-limited incumbent is not a proof of optimum"
    assert result["feasible"] and result["budget_ok"] and result["connectivity_ok"]
    assert result["num_selected"] == 5
    assert result["energy"] == pytest.approx(expected_energy, abs=1e-7, rel=0)
    assert tuple(np.flatnonzero(values)) in expected_sites

    # Frozen cold-build baselines for THIS COMMITTED dataset, not the paper.
    # These canaries ensure that a source edit cannot silently redefine parity.
    assert hashlib.sha256(GEOJSON.read_bytes()).hexdigest() == (
        "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
    )
    assert hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest() == (
        "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"
    )
    assert len(data.ids) == 5417
    assert reference["marked_count"] == len(instance.fixed_indices) == 15
    np.testing.assert_array_equal(
        instance.fixed_indices,
        [417, 454, 725, 1055, 1076, 1709, 2771, 3402, 3520, 3529, 3732, 3886, 4613, 4868, 5038],
    )
    np.testing.assert_array_equal(
        instance.free_indices,
        [5253, 2394, 1894, 1557, 3225, 4623, 47, 5409, 3922, 2408,
         2694, 4136, 2567, 1164, 4973, 4537, 2726, 968, 16, 1762],
    )
    np.testing.assert_array_equal(np.flatnonzero(values), [0, 1, 3, 6, 7])
    assert len(instance.quadratic) == 12
    if label == "notebook":
        assert expected_energy == pytest.approx(-3.3012934918564647, abs=1e-8)
    elif label == "paper-weight sensitivity":
        assert expected_energy == pytest.approx(-3.473640036773477, abs=1e-8)
    # Third (counterfactual) scenario's observed energy is printed and
    # reviewed before freezing a source-specific numerical baseline.

    # Printed in CI; not golden figures, which would incorrectly conflate studies.
    details = {
        "weight_scenario": label,
        "geojson_sha256": hashlib.sha256(GEOJSON.read_bytes()).hexdigest(),
        "notebook_sha256": hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "shapely": __import__("shapely").__version__,
        "scipy": __import__("scipy").__version__,
        "pyscipopt": __import__("pyscipopt").__version__,
        "N_free": 20, "K_new": 5,
        "geojson_points": len(data.ids),
        "marked_existing": reference["marked_count"],
        "fixed_station_count_used": len(instance.fixed_indices),
        "fixed_was_simulated": simulated,
        "D_max_m": instance.d_max,
        "candidate_master_positions": reference["selected"].tolist(),
        "fixed_master_positions": reference["fixed"].tolist(),
        "scip_selected_candidate_positions": np.flatnonzero(values).tolist(),
        "scip_selected_master_positions": instance.free_indices[values.astype(bool)].tolist(),
        "scip_status": result["status"],
        "scip_energy": result["energy"],
        "independent_optimum_energy": expected_energy,
        "independent_optimum_tie_count": len(expected_sites),
        "quadratic_edges": len(instance.quadratic),
        "paper_reported_energy": PAPER_ENERGY_N20,
        "paper_reported_candidate_positions": PAPER_SELECTED_N20,
        "delta_from_paper_energy_not_equivalence": result["energy"] - PAPER_ENERGY_N20,
    }
    print("N20_VALIDATION " + json.dumps(details, sort_keys=True))
