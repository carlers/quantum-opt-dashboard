"""Bounded, offline-only N50/N100 original-local SCIP evidence bundles.

SCIP is classical exact MILP; optimality is reported only when SCIP says
optimal. A valid incumbent is not a certified optimum, and the no-incumbent
or interrupted cases are retained. Neither paper nor QUBO parity is claimed.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import io
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np

from problems.water_quality.nested_resolution import (
    REFERENCE_GEOJSON, build_nested_instances,
)
from prototypes.streamlit_water_quality.model import Instance, solve_scip

EXPECTED_SOURCE_SHA = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
SCHEMA = "offline-scip-nested-v1"
TIERS = (50, 100)
MAX_LP_BYTES = 8_000_000
MAX_STDOUT_BYTES = 100_000
MAX_ARCHIVE_BYTES = 12_000_000
MEMORY_CEILING_BYTES = 6 * 1024 ** 3


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def _finite_float(value: object) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Nonfinite or nonnumeric result")
    return float(value)


def _ver(distribution: str) -> str | None:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def model_record(instance: Instance, source_sha: str) -> dict:
    """Exact IEEE binary64 coefficients; free and fixed source indices separate."""
    n = len(instance.free_indices)
    return {
        "schema": SCHEMA, "source_sha256": source_sha,
        "N_free": n, "K": int(instance.budget),
        "graph": "historical local one-hop", "weights": "notebook source",
        "source_coordinates_crs": "EPSG:32651",
        "free_master_positions": [int(x) for x in instance.free_indices],
        "fixed_master_positions": [int(x) for x in instance.fixed_indices],
        "linear_float64_hex": [float(x).hex() for x in instance.linear],
        "quadratic_float64_hex": [
            [int(i), int(j), float(q).hex()] for i, j, q in instance.quadratic
        ],
        "free_neighbors": [list(map(int, row)) for row in instance.neighbors],
        "fixed_neighbors": [int(x) for x in instance.fixed_neighbors],
        "d_max_float64_hex": float(instance.d_max).hex(),
        "binary64_note": "Exact coefficients for this runtime, not universal bit-exact replay",
        "solver_encoding": "PySCIPOpt exact MILP linearization of nonnegative pair terms",
        "quantum_executed": False, "paper_parity_claimed": False,
    }


def independent_witness(model: dict, chosen: object, energy: object) -> dict:
    """Independent arithmetic and graph check; never call model.evaluate."""
    n, k = model["N_free"], model["K"]
    if type(n) is not int or not (1 <= n <= 100) or type(k) is not int:
        raise ValueError("Invalid model dimensions")
    if type(chosen) is not list or len(chosen) != n or any(type(b) is not int or b not in (0, 1) for b in chosen):
        raise ValueError("Selection is not an exact binary N-vector")
    if len(model["linear_float64_hex"]) != n or len(model["free_neighbors"]) != n or len(model["fixed_neighbors"]) != n:
        raise ValueError("Incorrect objective or graph dimensions")
    if len(set(model["free_master_positions"])) != n or set(model["free_master_positions"]) & set(model["fixed_master_positions"]):
        raise ValueError("Duplicate/overlapping master source positions")
    active = [i for i, bit in enumerate(chosen) if bit]
    violated = []
    for i in active:
        row = model["free_neighbors"][i]
        if type(row) is not list or any(type(j) is not int or j < 0 or j >= n or j == i for j in row):
            raise ValueError("Invalid neighbor list")
        if not model["fixed_neighbors"][i] and not any(chosen[j] for j in row):
            violated.append(i)
    if len(active) != k or violated:
        raise ValueError("Claimed solution violates original K / local one-hop requirements")
    linear = sum(float.fromhex(model["linear_float64_hex"][i]) for i in active)
    quadratic = 0.0
    for i, j, q in model["quadratic_float64_hex"]:
        if not (type(i) is int and type(j) is int and 0 <= i < j < n):
            raise ValueError("Invalid quadratic pair")
        if chosen[i] and chosen[j]:
            quadratic += float.fromhex(q)
    total = linear + quadratic
    if not math.isclose(total, _finite_float(energy), rel_tol=1e-10, abs_tol=1e-7):
        raise ValueError("Independent source objective differs from solver report")
    return {
        "original_feasible": True, "budget_residual": len(active) - k,
        "violated_local_one_hop": [],
        "selected_local_positions": active,
        "selected_master_positions": [model["free_master_positions"][i] for i in active],
        "linear_component": linear, "quadratic_component": quadratic,
        "original_objective": total,
        "note": "Independent original model witness, not an independent optimality certificate",
    }


def archive_bundle(model: dict, result: dict, lp: bytes | None) -> bytes:
    files = {"model.json": canonical(model), "result.json": canonical(result)}
    if lp is not None:
        if not lp or len(lp) > MAX_LP_BYTES:
            raise ValueError("Emitted LP absent or exceeds storage bounds")
        files["emitted_scip_model.lp"] = lp
    files["SHA256SUMS.json"] = canonical({
        "sha256": {k: sha256(v).hexdigest() for k, v in files.items()},
        "source_geojson_sha256": model["source_sha256"],
        "not_a_signed_external_attestation": True,
    })
    stream = io.BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            archive.writestr(name, content)
    content = stream.getvalue()
    if len(content) > MAX_ARCHIVE_BYTES:
        raise ValueError("Research archive exceeds bounded size")
    return content


def verify_bundle(raw: bytes) -> dict:
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("Bundle too large")
    with ZipFile(io.BytesIO(raw)) as zipped:
        names = zipped.namelist()
        if len(names) != len(set(names)) or not {"model.json", "result.json", "SHA256SUMS.json"}.issubset(names):
            raise ValueError("Missing or duplicated evidence files")
        if set(names) - {"model.json", "result.json", "emitted_scip_model.lp", "SHA256SUMS.json"}:
            raise ValueError("Unexpected ZIP member")
        if any(entry.file_size > MAX_LP_BYTES for entry in zipped.infolist()):
            raise ValueError("Oversize member")
        checksum = json.loads(zipped.read("SHA256SUMS.json"))
        expected = {k: sha256(zipped.read(k)).hexdigest() for k in names if k != "SHA256SUMS.json"}
        if expected != checksum["sha256"]:
            raise ValueError("Bundle checksum mismatch")
        model, result = json.loads(zipped.read("model.json")), json.loads(zipped.read("result.json"))
        if model["source_sha256"] != checksum["source_geojson_sha256"] or model["schema"] != SCHEMA:
            raise ValueError("Wrong source identity or schema")
        if result["model_sha256"] != sha256(zipped.read("model.json")).hexdigest():
            raise ValueError("Result is not tied to exact model coefficients")
        if result["classification"] in ("optimal", "feasible_not_proven_optimal"):
            audit = independent_witness(model, result["binary_solution"], result["solver_objective"])
            if result["independent_audit"] != audit:
                raise ValueError("Independent witness or output mismatch")
            if result["classification"] == "optimal" and result["solver_status"] != "optimal":
                raise ValueError("Falsely claimed SCIP optimality")
        elif result["classification"] not in (
            "no_incumbent", "solver_error", "worker_exit_error", "wall_timeout"
        ):
            raise ValueError("Unknown result status")
        if result["classification"] not in ("optimal", "feasible_not_proven_optimal"):
            if result.get("binary_solution") is not None or result.get("independent_audit") is not None:
                raise ValueError("Failure record contains invented solution")
        return result


def _worker(request: Path, reply: Path, lp_path: Path) -> None:
    """Linux child; only the original source-model SCIP solver is executed."""
    data = json.loads(request.read_text(encoding="utf-8"))
    if data["schema"] != SCHEMA or data["model"]["N_free"] not in TIERS:
        raise ValueError("Invalid scientific worker request")
    if sys.platform != "linux":
        raise EnvironmentError("Bounded offline SCIP experiment requires Linux")
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_CEILING_BYTES, MEMORY_CEILING_BYTES))
    n = data["model"]["N_free"]
    # Separate cold scientific construction; no pickled historical caches.
    t0 = perf_counter()
    study = build_nested_instances(tiers=(n,))
    entry = study.tier_instances[0]
    actual = model_record(entry.instance, study.source_sha256)
    if canonical(actual) != canonical(data["model"]):
        raise ValueError("Worker reloaded a different source-derived model")
    model_build_seconds = perf_counter() - t0
    result = {
        "schema": SCHEMA, "solver_status": None, "classification": "solver_error",
        "solver_executed": False, "binary_solution": None, "solver_objective": None,
        "solver_gap": None, "independent_audit": None,
        "model_build_seconds": model_build_seconds, "solve_call_seconds": None,
        "error": None,
    }
    t1 = perf_counter()
    try:
        values, metrics = solve_scip(entry.instance, time_limit=data["time_limit_seconds"],
                                     export_lp_path=lp_path)
        result["solve_call_seconds"] = perf_counter() - t1
        result["solver_executed"] = True
        result["solver_status"] = str(metrics["status"])
        result["classification"] = ("optimal" if metrics["optimal"] else "feasible_not_proven_optimal")
        result["binary_solution"] = [int(v) for v in values]
        result["solver_objective"] = float(metrics["energy"])
        gap = float(metrics["gap"])
        result["solver_gap"] = gap if math.isfinite(gap) else None
        result["independent_audit"] = independent_witness(actual, result["binary_solution"], result["solver_objective"])
    except Exception as exc:
        result["solve_call_seconds"] = perf_counter() - t1
        result["solver_executed"] = True
        result["classification"] = ("no_incumbent" if isinstance(exc, RuntimeError)
                                    and str(exc).startswith("SCIP returned no feasible solution")
                                    else "solver_error")
        result["error"] = type(exc).__name__ + ": " + str(exc)[:500]
    reply.write_bytes(canonical(result))


def run(tiers: tuple[int, ...], time_limit: int, wall_timeout: int, out: Path) -> dict:
    if sys.platform != "linux":
        raise EnvironmentError("Bounded source SCIP research runner requires Linux")
    if not tiers or any(type(n) is not int or n not in TIERS for n in tiers) or len(set(tiers)) != len(tiers):
        raise ValueError("Only unique N50/N100 offline tiers are supported")
    if type(time_limit) is not int or not (1 <= time_limit <= 60):
        raise ValueError("SCIP limit must be 1..60 seconds")
    if type(wall_timeout) is not int or wall_timeout <= time_limit + 10 or wall_timeout > 180:
        raise ValueError("Wall limit must exceed solve limit + 10s, max 180s")
    study = build_nested_instances(tiers=tuple(sorted(set((20,) + tiers))))
    if study.source_sha256 != EXPECTED_SOURCE_SHA or study.fixed_simulated or len(study.fixed_master_positions) != 15:
        raise ValueError("Not the pinned real source/fixed-station cohort")
    out.mkdir(parents=True, exist_ok=True)
    ledger = {"schema": SCHEMA, "source_sha256": study.source_sha256,
              "fixed_station_count": len(study.fixed_master_positions),
              "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                          "numpy": _ver("numpy"), "scipy": _ver("scipy"),
                          "shapely": _ver("shapely"), "pyscipopt": _ver("PySCIPOpt")},
              "time_limit_seconds": time_limit, "hard_wall_timeout_seconds": wall_timeout,
              "study_n20_50_100_prefix_verified": True,
              "not_new_independent_stochastic_runs": True,
              "tiers": []}
    for entry in study.tier_instances:
        if entry.n_free not in tiers:
            continue
        model = model_record(entry.instance, study.source_sha256)
        model_bytes = canonical(model)
        result = {"schema": SCHEMA, "model_sha256": sha256(model_bytes).hexdigest(),
                  "N_free": entry.n_free, "time_limit_seconds": time_limit,
                  "hard_wall_timeout_seconds": wall_timeout, "worker_wall_seconds": None,
                  "solver_status": None, "classification": "worker_exit_error",
                  "solver_executed": None, "binary_solution": None, "solver_objective": None,
                  "solver_gap": None, "independent_audit": None, "error": None,
                  "model_build_seconds": None, "solve_call_seconds": None}
        with TemporaryDirectory(prefix="qopt-offline-scip-") as temp:
            folder = Path(temp)
            req, reply, lp_path = (folder / name for name in ("request.json", "reply.json", "emitted.lp"))
            req.write_bytes(canonical({"schema": SCHEMA, "model": model, "time_limit_seconds": time_limit}))
            env = dict(os.environ)
            env.update({"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
            start = perf_counter()
            cmd = [sys.executable, "-m", "problems.water_quality.offline_scip_batch",
                   "--worker", str(req), str(reply), str(lp_path)]
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     start_new_session=True, env=env)
            try:
                stdout, stderr = child.communicate(timeout=wall_timeout)
                elapsed = perf_counter() - start
                result["worker_wall_seconds"] = elapsed
                if child.returncode == 0 and reply.is_file():
                    reported = json.loads(reply.read_text(encoding="utf-8"))
                    result.update(reported)
                    result["model_sha256"] = sha256(model_bytes).hexdigest()
                    result["N_free"] = entry.n_free
                    result["time_limit_seconds"] = time_limit
                    result["hard_wall_timeout_seconds"] = wall_timeout
                    result["worker_wall_seconds"] = elapsed
                    if result["classification"] in ("optimal", "feasible_not_proven_optimal"):
                        result["independent_audit"] = independent_witness(
                            model, result["binary_solution"], result["solver_objective"]
                        )
                else:
                    result["error"] = ("Worker exit code: " + str(child.returncode)
                                       + " / " + stderr.decode("utf-8", "replace")[-450:])
                if len(stdout) > MAX_STDOUT_BYTES or len(stderr) > MAX_STDOUT_BYTES:
                    result["error"] = "Worker output exceeded declared bound"
                    result["classification"] = "worker_exit_error"
                    result["binary_solution"] = None
                    result["independent_audit"] = None
                    result["solver_objective"] = None
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.communicate()
                result["classification"] = "wall_timeout"
                result["worker_wall_seconds"] = perf_counter() - start
                result["error"] = "Hard wall budget exceeded; solver status unknown"
            lp = lp_path.read_bytes() if lp_path.exists() and 0 < lp_path.stat().st_size <= MAX_LP_BYTES else None
            archive = archive_bundle(model, result, lp)
            verified = verify_bundle(archive)
            name = f"scip-n{entry.n_free}-{result['model_sha256'][:12]}.zip"
            (out / name).write_bytes(archive)
            ledger["tiers"].append({
                "N_free": entry.n_free, "classification": verified["classification"],
                "solver_status": verified["solver_status"],
                "archive": name, "archive_sha256": sha256(archive).hexdigest(),
                "model_sha256": result["model_sha256"],
                "verified_feasible_witness": verified["independent_audit"] is not None,
                "optimality_claim": verified["classification"] == "optimal",
            })
    (out / "index.json").write_bytes(canonical(ledger))
    return ledger


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", nargs=3, metavar=("REQUEST", "RESULT", "LP"))
    parser.add_argument("--tiers", nargs="+", type=int, default=[50, 100])
    parser.add_argument("--time-limit", type=int, default=12)
    parser.add_argument("--wall-timeout", type=int, default=75)
    parser.add_argument("--out", type=Path, default=Path("research-results/offline-scip"))
    args = parser.parse_args()
    if args.worker:
        _worker(*(Path(x) for x in args.worker))
    else:
        ledger = run(tuple(args.tiers), args.time_limit, args.wall_timeout, args.out)
        print(json.dumps(ledger, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
