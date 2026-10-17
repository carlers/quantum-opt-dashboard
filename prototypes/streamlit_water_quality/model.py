"""Small water-quality MIQP pilot adapted from the committed research notebook.

Unvalidated against publication. SCIP solves an exact MILP linearization of
nonnegative pair penalties, replacing notebook's JijModeling/OMMX adapter.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from shapely import concave_hull
from shapely.geometry import LineString, MultiPoint, Point

FACTOR_NAMES = (
    "a1_river_proximity", "a2_runoff_proximity", "b1_fishpen_density",
    "b2_hypoxic_proximity", "c1_bathymetric_depressions",
    "c2_outlet_proximity", "d1_boatramp_proximity", "d2_road_proximity",
)
NOTEBOOK_WEIGHTS = np.array([.3671, .1224, .2508, .0502, .1278, .0183, .0476, .0159])
PAPER_WEIGHTS = np.array([
    .276095907, .276095907, .179220150, .089610075,
    .087188181, .043594091, .024097845, .024097845,
])

# Notebook Cell 2 and Cell 3 defaults, not necessarily paper experiment defaults.
L_C = 7500.0
L_W = 1000.0
CURRENT_VECTOR = (1.0, 0.0)
D_MAX_BUFFER = 1.15
POOL_SIZE = 10000
HULL_RATIO = .05


@dataclass(frozen=True)
class LakeData:
    coords: np.ndarray  # EPSG:32651 in meters
    factors: np.ndarray
    existing: np.ndarray
    ids: np.ndarray


@dataclass(frozen=True)
class Instance:
    coords: np.ndarray  # free sites then fixed sites
    free_indices: np.ndarray  # master dataset indices
    fixed_indices: np.ndarray
    utility: np.ndarray
    linear: np.ndarray
    quadratic: tuple[tuple[int, int, float], ...]
    neighbors: tuple[tuple[int, ...], ...]  # free-to-free
    fixed_neighbors: np.ndarray
    budget: int
    d_max: float


def load_data(path: str | Path) -> LakeData:
    with open(path, encoding="utf-8") as f:
        geojson = json.load(f)
    features = geojson["features"]
    if not features:
        raise ValueError("No candidate-site features found")
    coords, factors, existing, ids = [], [], [], []
    for idx, feature in enumerate(features):
        geom = feature["geometry"]
        if geom["type"] != "Point":
            raise ValueError(f"Feature {idx} is not a point")
        coords.append(geom["coordinates"][:2])
        props = feature["properties"]
        factors.append([np.nan if props.get(name) is None else float(props[name])
                        for name in FACTOR_NAMES])
        existing.append(bool(props.get("has_existing_station", False)))
        ids.append(int(props.get("id", idx)))
    arr = np.asarray(coords, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2 or not np.isfinite(arr).all():
        raise ValueError("Invalid coordinates")
    if np.all(abs(arr[:, 0]) <= 180) and np.all(abs(arr[:, 1]) <= 90):
        raise ValueError("Coordinates appear to be lon/lat; expected EPSG:32651 meters")
    return LakeData(arr, np.asarray(factors, dtype=float),
                    np.asarray(existing, dtype=bool), np.asarray(ids, dtype=int))


def site_utility(factors: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Same missing-factor, per-site renormalization as notebook Cell 2."""
    weights = np.asarray(weights, dtype=float)
    if weights.shape != (8,) or not np.isfinite(weights).all() or (weights < 0).any() or weights.sum() <= 0:
        raise ValueError("Eight finite, nonnegative factor weights with positive total required")
    valid = np.isfinite(factors)
    den = np.sum(valid * weights, axis=1)
    num = np.nansum(np.where(valid, factors * weights, 0.0), axis=1)
    return np.clip(num / np.where(den == 0, 1.0, den), 0.0, 1.0)


def existing_stations(data: LakeData, utility: np.ndarray) -> tuple[np.ndarray, bool]:
    marked = np.flatnonzero(data.existing)
    if marked.size:
        return marked, False
    # Notebook fallback: simulate 3 stations 12 km apart when possible.
    selected = [int(np.argmax(utility))]
    for _ in range(2):
        dists = cdist(data.coords, data.coords[selected]).min(axis=1)
        valid = np.flatnonzero((dists >= 12000) & (~np.isin(np.arange(len(dists)), selected)))
        index = int(valid[np.argmax(utility[valid])]) if len(valid) else int(np.argmax(dists))
        if index in selected:
            raise ValueError("Not enough distinct sites for station fallback")
        selected.append(index)
    return np.asarray(selected, dtype=int), True


def _hex_pool(bbox: tuple[float, float, float, float]) -> np.ndarray:
    xmin, ymin, xmax, ymax = bbox
    width, height = xmax - xmin, ymax - ymin
    spacing = np.sqrt((width * height / POOL_SIZE) / (np.sqrt(3) / 2.0))
    dx, dy = spacing, spacing * np.sqrt(3.0) / 2.0
    pool = []
    for row in range(int(np.ceil(height / dy)) + 1):
        y = ymin + row * dy
        if y > ymax:
            continue
        for col in range(int(np.ceil(width / dx)) + 1):
            x = xmin + col * dx + (0.5 * dx if row % 2 else 0.0)
            if x <= xmax:
                pool.append((x, y))
    return np.asarray(pool)


def select_sites(data: LakeData, fixed_indices: np.ndarray, n_free: int):
    """Notebook hex-pool -> nearest master -> unique -> seeded FPS."""
    if n_free < 1:
        raise ValueError("At least one free site required")
    coords = data.coords
    hull = concave_hull(MultiPoint(coords), ratio=HULL_RATIO, allow_holes=True)
    pool = _hex_pool((float(coords[:, 0].min()), float(coords[:, 1].min()),
                      float(coords[:, 0].max()), float(coords[:, 1].max())))
    water = np.asarray([p for p in pool if hull.contains(Point(p))], dtype=float)
    if len(water) == 0:
        raise ValueError("No hex-pool sites inside derived water boundary")
    pool_indices = cKDTree(coords).query(water, k=1)[1]
    unique_free = np.unique(pool_indices[~np.isin(pool_indices, fixed_indices)])
    if len(unique_free) < n_free:
        raise ValueError(f"Only {len(unique_free)} free sites in pool, need {n_free}")
    seed_dists = cKDTree(coords[fixed_indices]).query(coords[unique_free], k=1)[0]
    selected = []
    for _ in range(n_free):
        i = int(np.argmax(seed_dists))
        selected.append(int(unique_free[i]))
        seed_dists = np.minimum(seed_dists, np.linalg.norm(coords[unique_free] - coords[unique_free[i]], axis=1))
        seed_dists[i] = -1.0
    return np.asarray(selected, dtype=int), hull


def make_instance(data: LakeData, weights: np.ndarray, n_free: int, budget: int,
                  *, beta: float = 1.0, delta: float = 1.0) -> tuple[Instance, bool]:
    if not isinstance(budget, int) or not (0 <= budget <= n_free):
        raise ValueError("Budget must be between zero and free-site count")
    if not (np.isfinite(beta) and np.isfinite(delta) and beta >= 0 and delta >= 0):
        raise ValueError("Interaction penalties must be finite and nonnegative")
    util = site_utility(data.factors, weights)
    fixed, simulated = existing_stations(data, util)
    free, hull = select_sites(data, fixed, n_free)
    coords = np.vstack([data.coords[free], data.coords[fixed]])
    u = np.concatenate([util[free], util[fixed]])
    m = len(fixed)
    dists, _ = cKDTree(data.coords[fixed]).query(data.coords[fixed], k=2) if m > 1 else (None, None)
    d_max = (float(np.max(dists[:, 1])) * D_MAX_BUFFER) if m > 1 else 15000.0
    quadratic = []
    linear = -u[:n_free].copy()
    neighbors = [set() for _ in range(n_free)]
    fixed_neighbors = np.zeros(n_free, dtype=int)
    v = np.asarray(CURRENT_VECTOR, dtype=float)
    v /= np.linalg.norm(v)
    # Small pilot tiers: N=20/50. Do not run full N=2000 here.
    for i, j in sorted(cKDTree(coords).query_pairs(r=max(d_max, 2 * L_C))):
        p1, p2 = coords[i], coords[j]
        if not (hull.contains(Point(p1)) and hull.contains(Point(p2)) and
                hull.contains(LineString([p1, p2]))):
            continue
        diff = p2 - p1
        d = float(np.linalg.norm(diff))
        if d == 0:
            continue
        if d <= d_max:
            if i < n_free and j < n_free:
                neighbors[i].add(j)
                neighbors[j].add(i)
            elif i < n_free and j >= n_free:
                fixed_neighbors[i] = 1
            elif j < n_free and i >= n_free:
                fixed_neighbors[j] = 1
        if d <= 2 * L_C:
            redundancy = max(0.0, 1.0 - d / L_C)
            cos = float(np.clip(np.dot(diff, v) / d, -1.0, 1.0))
            wake = np.exp(-d / L_W) * abs(cos) if abs(cos) > .7071 else 0.0
            coeff = float(beta * redundancy + delta * wake)
            if coeff > 1e-12:
                if i < n_free and j < n_free:
                    quadratic.append((i, j, coeff))
                elif i < n_free and j >= n_free:
                    linear[i] += coeff
                elif j < n_free and i >= n_free:
                    linear[j] += coeff
    return Instance(coords, free, fixed, u, linear, tuple(quadratic),
                    tuple(tuple(sorted(ns)) for ns in neighbors), fixed_neighbors,
                    budget, d_max), simulated


def evaluate(instance: Instance, x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=int)
    if x.shape != (len(instance.free_indices),) or not np.isin(x, [0, 1]).all():
        raise ValueError("Invalid binary solution vector")
    isolated = [i for i, active in enumerate(x) if active and not (
        instance.fixed_neighbors[i] or any(x[j] for j in instance.neighbors[i])
    )]
    energy = float(instance.linear @ x + sum(q * x[i] * x[j] for i, j, q in instance.quadratic))
    return {"energy": energy, "num_selected": int(x.sum()),
            "budget_ok": int(x.sum()) == instance.budget,
            "connectivity_ok": not isolated, "isolated": isolated,
            "feasible": int(x.sum()) == instance.budget and not isolated}


def solve_scip(instance: Instance, *, time_limit: float = 30.0) -> tuple[np.ndarray, dict]:
    """SCIP via PySCIPOpt. Exact MILP representation for nonnegative Q terms.

    Unlike source notebook's OMMX adapter, this introduces z_ij=x_i*x_j.
    A feasible time-limited incumbent is not reported as proven optimal.
    """
    from pyscipopt import Model, quicksum

    if any(q < 0 for _, _, q in instance.quadratic):
        raise ValueError("Requires nonnegative quadratic penalties")
    model = Model("water_quality_pilot")
    model.hideOutput()
    n = len(instance.free_indices)
    x = [model.addVar(name=f"x{i}", vtype="B") for i in range(n)]
    z = []
    for i, j, _ in instance.quadratic:
        pair = model.addVar(name=f"p{i}_{j}", vtype="B")
        model.addCons(pair >= x[i] + x[j] - 1)
        model.addCons(pair <= x[i])
        model.addCons(pair <= x[j])
        z.append(pair)
    model.addCons(quicksum(x) == instance.budget, name="budget")
    for i in range(n):
        model.addCons(x[i] <= int(instance.fixed_neighbors[i]) +
                      quicksum(x[j] for j in instance.neighbors[i]), name=f"connect_{i}")
    objective = quicksum(float(instance.linear[i]) * x[i] for i in range(n))
    objective += quicksum(float(q) * z[k] for k, (_, _, q) in enumerate(instance.quadratic))
    model.setObjective(objective, "minimize")
    model.setRealParam("limits/time", float(time_limit))
    model.optimize()
    status = str(model.getStatus())
    if model.getNSols() == 0:
        raise RuntimeError(f"SCIP returned no feasible solution (status: {status})")
    solution = model.getBestSol()
    values = np.asarray([int(model.getSolVal(solution, var) > .5) for var in x], dtype=int)
    metrics = evaluate(instance, values)
    if not metrics["feasible"]:
        raise RuntimeError("SCIP solution failed independent feasibility check")
    metrics.update({"status": status, "optimal": status == "optimal", "gap": float(model.getGap())})
    return values, metrics
