"""Focused water-quality Streamlit MVP: reproducible preview and evidence helpers.

This is deliberately NOT a general optimization framework or reproduction of
the previous publication. Original notebook semantics: exact K and local
one-hop adjacency, not global graph connectivity. SCIP solves the existing
exact binary pair-product MILP; the QUBO sampler is NOT used.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from math import isclose, isfinite
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np

from model import Instance

EXPECTED_GEOJSON_SHA256 = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
NOTEBOOK_N20_K5_OPTIMUM = -3.3012934918564643
NOTEBOOK_N20_K5_LOCAL_INDICES = (0, 1, 3, 6, 7)
NOTEBOOK_N20_K5_MASTER_INDICES = (5253, 2394, 1557, 47, 5409)


def canonical(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def source_sha(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_GEOJSON_SHA256:
        raise ValueError(
            "The committed lake reference dataset changed. "
            "MVP source identity check failed: refuse to run."
        )
    return digest


def preview(instance: Instance, *, dataset_sha256: str, weights: list[float],
            weight_source: str, time_limit_seconds: int) -> dict:
    """Create the actual model preview from the same Instance passed to SCIP."""
    n = len(instance.free_indices)
    if not 1 <= n <= 20 or not 0 <= instance.budget <= n:
        raise ValueError("MVP only supports N<=20 and 0<=K<=N")
    if dataset_sha256 != EXPECTED_GEOJSON_SHA256:
        raise ValueError("MVP requires the SHA-pinned source dataset")
    if len(weights) != 8 or any(not isfinite(float(x)) or x < 0 for x in weights):
        raise ValueError("Invalid eight nonnegative weights")
    if time_limit_seconds != 30:
        raise ValueError("MVP SCIP time limit is fixed to 30 seconds")
    settings = {
        "candidate_sites_n": n,
        "new_sensors_k": int(instance.budget),
        "weights_source": weight_source,
        "eight_factor_weights": [float(w) for w in weights],
        "beta": 1.0, "delta": 1.0,
        "scip_time_limit_seconds": time_limit_seconds,
    }
    model = {
        "schema_version": 1,
        "problem": "notebook_derived_water_quality_one_hop_binary_quadratic",
        "dataset_sha256": dataset_sha256,
        "coordinate_system": "EPSG:32651 projected meters",
        "settings": settings,
        "objective": {
            "sense": "minimize",
            "expression": "sum_i a_i*x_i + sum_(i<j) q_ij*x_i*x_j",
            "linear_float64_hex": [float(v).hex() for v in instance.linear],
            "quadratic_terms": [
                {"i": int(i), "j": int(j), "q_float64_hex": float(q).hex()}
                for i, j, q in instance.quadratic
            ],
            "constant_offset": 0,
        },
        "constraints": {
            "budget": "sum_i x_i == K",
            "budget_rhs": int(instance.budget),
            "local_one_hop": "x_i <= f_i + sum_(j in N(i)) x_j",
            "fixed_neighbor_flags": [int(v) for v in instance.fixed_neighbors],
            "free_neighbors": [list(map(int, members)) for members in instance.neighbors],
            "global_path_connectivity": False,
        },
        "mapping": {
            "free_master_feature_positions": [int(v) for v in instance.free_indices],
            "fixed_master_feature_positions": [int(v) for v in instance.fixed_indices],
            "position_meaning": "zero-based feature ordering in committed GeoJSON, not property id",
            "projected_coords_easting_northing_m": [
                [float(x), float(y)] for x, y in instance.coords
            ],
        },
        "d_max_m_float64_hex": float(instance.d_max).hex(),
        "solver_representation": "SCIP exact binary product MILP; not native MIQP or QUBO",
        "quantum_hardware_used": False,
        "source_reproduction": "committed notebook-based N20 implementation; paper parity unresolved",
    }
    model["model_fingerprint_sha256"] = hashlib.sha256(canonical(model)).hexdigest()
    return model


def check_selected(instance: Instance, selected: np.ndarray,
                   solver: dict, model: dict) -> dict:
    """Independently decode original objective and one-hop constraints."""
    x = np.asarray(selected)
    n = len(instance.free_indices)
    if x.shape != (n,) or not np.isin(x, [0, 1]).all():
        raise ValueError("SCIP selection is not a valid binary vector")
    chosen = [int(i) for i in np.flatnonzero(x)]
    linear = sum(float(instance.linear[i]) * int(x[i]) for i in range(n))
    quadratic = sum(
        float(q) * int(x[i]) * int(x[j])
        for i, j, q in instance.quadratic
    )
    violation = [
        int(i) for i in chosen
        if not int(instance.fixed_neighbors[i]) and
        not any(int(x[j]) for j in instance.neighbors[i])
    ]
    feasible = len(chosen) == instance.budget and not violation
    score = float(linear + quadratic)
    if not feasible:
        raise AssertionError("SCIP returned a selection violating original constraints")
    if not isclose(score, float(solver["energy"]), rel_tol=1e-10, abs_tol=1e-7):
        raise AssertionError("Original independent objective differs from SCIP report")
    return {
        "selected_local_positions": chosen,
        "selected_master_feature_positions": [
            int(instance.free_indices[i]) for i in chosen
        ],
        "independent_original_objective": score,
        "objective_linear_component": float(linear),
        "objective_quadratic_component": float(quadratic),
        "budget_residual": len(chosen) - int(instance.budget),
        "violated_local_one_hop_sites": violation,
        "original_feasible": feasible,
        "model_fingerprint_sha256": model["model_fingerprint_sha256"],
    }


def selected_csv(instance: Instance, selected: np.ndarray) -> bytes:
    file = io.StringIO()
    writer = csv.writer(file, lineterminator="\n")
    writer.writerow(["local_position", "master_feature_position", "easting_m", "northing_m"])
    for i in np.flatnonzero(selected):
        writer.writerow([
            int(i), int(instance.free_indices[i]),
            float(instance.coords[i, 0]), float(instance.coords[i, 1])
        ])
    return file.getvalue().encode("utf-8")


def _installed_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "not installed"


def evidence_zip(model: dict, independent: dict, solver: dict,
                 selected_sites_csv: bytes, original_lp: bytes) -> bytes:
    if not original_lp.strip():
        raise ValueError("Cannot archive an empty SCIP LP model")
    result = {
        "schema_version": 1,
        "model_fingerprint_sha256": model["model_fingerprint_sha256"],
        "source_sha256": model["dataset_sha256"],
        "software_versions": {
            "python": platform.python_version(),
            "numpy": _installed_version("numpy"),
            "scipy": _installed_version("scipy"),
            "shapely": _installed_version("shapely"),
            "pyscipopt": _installed_version("PySCIPOpt"),
            "streamlit": _installed_version("streamlit"),
        },
        "solver": "SCIP exact MILP binary-product linearization",
        "scip_status": solver["status"],
        "scip_optimal_proven": bool(solver["optimal"]),
        "scip_gap": float(solver["gap"]),
        "scip_original_objective": float(solver["energy"]),
        "independent_audit": independent,
        "important": "No paper reproduction or quantum-advantage claim.",
    }
    files = {
        "model.json": canonical(model),
        "result.json": canonical(result),
        "selected_sites.csv": selected_sites_csv,
        "actual_scip_model.lp": original_lp,
    }
    checksums = {name: hashlib.sha256(blob).hexdigest()
                 for name, blob in files.items()}
    files["SHA256SUMS.json"] = canonical({
        "files_sha256": checksums,
        "source_geojson_sha256": model["dataset_sha256"],
        "note": "The pinned full historical GeoJSON is not redistributed in this archive.",
    })
    archive = io.BytesIO()
    with ZipFile(archive, "w", ZIP_DEFLATED) as zipfile:
        for name in sorted(files):
            zipfile.writestr(name, files[name])
    return archive.getvalue()
