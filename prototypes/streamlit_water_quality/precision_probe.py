"""Read-only bit-level diagnostics for cross-run N20 coefficient drift (#24).

Do not round/fix QUBO input here. This records the *actual* IEEE-754 values,
parameterized penalty QUBOs, and selected CPU/BLAS provenance so that
different successful GitHub CI runs can be compared without changing science.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version as package_version
import json
import os
from pathlib import Path
import platform

import numpy as np

from evidence import GEOJSON, NOTEBOOK, canonical_bytes, numerical_fingerprint
from model import NOTEBOOK_WEIGHTS, load_data, make_instance
from qubo import best_slack_assignment, energy, make_qubo
from sa_benchmark import benchmark_penalties


def digest(payload: object) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def _cpu_model() -> str:
    """Expose non-sensitive host CPU model, not arbitrary environment values."""
    path = Path("/proc/cpuinfo")
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def _hex(value: float) -> str:
    """Exact binary64 representation, unlike decimal repr or rounding."""
    return float(value).hex()


def build_probe() -> dict:
    data = load_data(GEOJSON)
    inst, simulated = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    if simulated or len(inst.fixed_indices) != 15:
        raise AssertionError("The 15 real fixed stations changed unexpectedly")
    frozen_local = (0, 1, 3, 6, 7)
    x = [int(i in frozen_local) for i in range(20)]
    baseline_energy = float(
        sum(float(a) * x[i] for i, a in enumerate(inst.linear))
        + sum(float(q) * x[i] * x[j] for i, j, q in inst.quadratic)
    )
    if abs(baseline_energy - (-3.3012934918564643)) > 1e-7:
        raise AssertionError("Original N20 SCIP optimum source-formula energy drifted")

    raw = {
        "schema_version": 1,
        "source_geojson_sha256": hashlib.sha256(GEOJSON.read_bytes()).hexdigest(),
        "source_notebook_sha256": hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
        "num_dataset_sites": len(data.ids),
        "fixed_feature_positions": [int(i) for i in inst.fixed_indices],
        "free_feature_positions": [int(i) for i in inst.free_indices],
        "utility_float64_hex": [_hex(v) for v in inst.utility],
        "linear_float64_hex": [_hex(v) for v in inst.linear],
        "quadratic_float64_hex": [
            [int(i), int(j), _hex(v)] for i, j, v in inst.quadratic
        ],
        "coordinates_float64_hex": [
            [_hex(x0), _hex(y0)] for x0, y0 in inst.coords
        ],
        "d_max_float64_hex": _hex(inst.d_max),
        "neighbors": [list(v) for v in inst.neighbors],
        "fixed_neighbors": inst.fixed_neighbors.astype(int).tolist(),
        "solution_original_energy_float64_hex": _hex(baseline_energy),
    }
    numeric = {
        "utility": inst.utility.tolist(), "linear": inst.linear.tolist(),
        "quadratic": [list(t) for t in inst.quadratic],
        "coords": inst.coords.tolist(), "d_max": float(inst.d_max),
    }
    penalty_values = benchmark_penalties(inst)
    qubo_details = {}
    for name, penalty in penalty_values.items():
        qubo = make_qubo(inst, budget_penalty=penalty,
                         connectivity_penalty=penalty)
        coefficients = [
            [int(i), int(j), _hex(value)]
            for (i, j), value in qubo.coefficients.items()
        ]
        encoded = {
            "schema_version": 1,
            "penalty_float64_hex": _hex(penalty),
            "offset_float64_hex": _hex(qubo.offset),
            "n_binary_variables": qubo.n_variables,
            "coefficients_float64_hex": coefficients,
            "slack_variables": [list(group) for group in qubo.slack_variables],
            "slack_weights": [list(group) for group in qubo.slack_weights],
        }
        bits = best_slack_assignment(inst, qubo, x)
        if abs(energy(qubo, bits) - baseline_energy) > 1e-7:
            raise AssertionError("Optimum source assignment changed QUBO energy")
        qubo_details[name] = {
            "raw_qubo_sha256": digest(encoded),
            "full_float64_input": encoded,
        }

    return {
        "schema_version": 1,
        "scientific_label": "read-only original-float precision diagnostics; not normalization or retuning",
        "model_source": raw,
        "raw_model_input_sha256": digest(raw),
        "numeric_model_fingerprint_12_decimal_sha256": numerical_fingerprint(numeric),
        "qubo_by_penalty": qubo_details,
        "environment": {
            "python": platform.python_version(),
            "os": platform.platform(),
            "cpu_model": _cpu_model(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "numpy": np.__version__,
            "scipy": package_version("scipy"),
            "shapely": package_version("shapely"),
            "pyscipopt": package_version("pyscipopt"),
            "openjij": package_version("openjij"),
            "openblas_threads": os.getenv("OPENBLAS_NUM_THREADS"),
            "omp_threads": os.getenv("OMP_NUM_THREADS"),
            "mkl_threads": os.getenv("MKL_NUM_THREADS"),
            "github_commit": os.getenv("GITHUB_HEAD_SHA") or os.getenv("GITHUB_SHA"),
        },
    }


def write_probe(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_probe()
    # Repeat a fresh build inside one process; cross-CI repeatability must be
    # assessed externally, using artifacts from separate GitHub runners.
    again = build_probe()
    same = (report["raw_model_input_sha256"] ==
            again["raw_model_input_sha256"] and
            {k: v["raw_qubo_sha256"] for k, v in report["qubo_by_penalty"].items()} ==
            {k: v["raw_qubo_sha256"] for k, v in again["qubo_by_penalty"].items()})
    report["repeated_build_same_process_bitwise_match"] = bool(same)
    report["second_build_raw_model_sha256"] = again["raw_model_input_sha256"]
    report["second_build_qubo_sha256"] = {
        k: v["raw_qubo_sha256"] for k, v in again["qubo_by_penalty"].items()
    }
    if not same:
        raise AssertionError("Repeated N20 instance or QUBO drifted WITHIN one process")
    file = output_dir / "precision_probe.json"
    file.write_bytes(canonical_bytes(report))
    manifest = {"schema_version": 1,
                "file_sha256": {"precision_probe.json": hashlib.sha256(file.read_bytes()).hexdigest()}}
    (output_dir / "manifest.json").write_bytes(canonical_bytes(manifest))
    print("N20_PRECISION_PROBE " + json.dumps({
        "model_raw_sha256": report["raw_model_input_sha256"],
        "model_12dp_fingerprint": report["numeric_model_fingerprint_12_decimal_sha256"],
        "qubo_raw_sha256": {k: v["raw_qubo_sha256"]
                             for k, v in report["qubo_by_penalty"].items()},
        "row_sum_penalty_float_hex": report["qubo_by_penalty"][
            "notebook-local-row-sum"]["full_float64_input"]["penalty_float64_hex"],
        "cpu_model": report["environment"]["cpu_model"],
        "numpy": report["environment"]["numpy"],
        "openblas_threads": report["environment"]["openblas_threads"],
        "same_process_repeat": same,
    }, sort_keys=True))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    write_probe(args.output_dir)
