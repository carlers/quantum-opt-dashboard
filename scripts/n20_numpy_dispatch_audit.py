"""Issue #62: identical IEEE754 inputs under original and NumPy SIMD-masked modes.

Execution is observational. NPY_DISABLE_CPU_FEATURES must be set BEFORE
starting Python; do not set it dynamically after importing numpy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform

import numpy as np
from numpy._core import _multiarray_umath
from numpy.linalg import _umath_linalg

from scripts.n20_frozen_math_microprobe import (
    FROZEN_CASES, EXPECTED_NUMPY, canonical, calculate_cases, fingerprint,
    safe_cpu_model,
)

MODE_ENV = {"baseline": None, "no-avx2-fma3": "AVX2,FMA3"}
EXPERIMENT = "issue62_numpy_254_fixed_operands_dispatch_intervention"
CASE_NAMES = tuple(x["id"] for x in FROZEN_CASES)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extensions() -> list[dict]:
    """Hash compiled numerical artifacts without exposing host file paths."""
    candidates = [
        Path(_multiarray_umath.__file__),
        Path(_umath_linalg.__file__),
    ]
    numpy_root = Path(np.__file__).resolve().parent
    libs = numpy_root.parent / "numpy.libs"
    if libs.is_dir():
        candidates.extend(sorted(p for p in libs.iterdir() if p.is_file()))
    seen = set()
    output = []
    for p in candidates:
        if p.name in seen:
            raise ValueError("Ambiguous binary filenames in installed numpy package")
        seen.add(p.name)
        output.append({
            "basename": p.name,
            "bytes": p.stat().st_size,
            "sha256": file_sha256(p),
        })
    return output


def runtime_details() -> dict:
    cpumod = _multiarray_umath
    features = {
        str(k): bool(v) for k, v in sorted(cpumod.__cpu_features__.items())
    }
    raw = np.show_runtime(mode="dicts")
    # NumPy may report absolute wheel paths and host-specific library locations;
    # record only allowlisted runtime metadata. Compiled module SHA is above.
    runtimes = []
    for record in raw:
        if "simd_extensions" in record:
            simd = record["simd_extensions"]
            runtimes.append({
                "simd_extensions": {
                    k: sorted([str(s) for s in simd.get(k, [])])
                    for k in ("baseline", "found", "not_found")
                }
            })
        elif "internal_api" in record or "user_api" in record:
            runtimes.append({
                k: record.get(k) for k in (
                    "architecture", "internal_api", "num_threads",
                    "prefix", "threading_layer", "user_api", "version",
                )
            })
    return {
        "numpy": np.__version__,
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "system": platform.system(),
        "libc": list(platform.libc_ver()),
        "cpu_model": safe_cpu_model(),
        "cpu_baseline": list(cpumod.__cpu_baseline__),
        "cpu_dispatch": list(cpumod.__cpu_dispatch__),
        "cpu_features_enabled": features,
        "show_runtime_allowlisted": runtimes,
        "extensions_sha256": extensions(),
        "env": {
            k: os.environ.get(k) for k in (
                "NPY_DISABLE_CPU_FEATURES", "OPENBLAS_NUM_THREADS",
                "OMP_NUM_THREADS", "MKL_NUM_THREADS",
            )
        },
        "github_head_sha": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
    }


def stage_observations() -> list[dict]:
    cases = []
    public_results = calculate_cases()
    for case, baseline in zip(FROZEN_CASES, public_results):
        values = [float.fromhex(s) for s in case["hex_operands"]]
        if case["operation"] == "numpy.linalg.norm":
            arr = np.asarray(values, dtype=np.float64)
            # These diagnostic operations do NOT replace the notebook's norm.
            squares = np.square(arr)
            reduced = np.sum(squares)
            rooted = np.sqrt(reduced)
            diagnostics = {
                "squares_float64_hex": [float(v).hex() for v in squares],
                "np_sum_squares_float64_hex": float(reduced).hex(),
                "np_sqrt_sum_float64_hex": float(rooted).hex(),
                "math_hypot_float64_hex": math.hypot(*values).hex(),
            }
        else:
            v = values[0]
            diagnostics = {
                "math_exp_float64_hex": math.exp(v).hex(),
                "numpy_exp_array_one_float64_hex": float(
                    np.exp(np.asarray([v], dtype=np.float64))[0]
                ).hex(),
            }
        cases.append({
            **baseline,
            "diagnostic_stages": diagnostics,
        })
    return cases


def measure(replica: str, mode: str) -> dict:
    if mode not in MODE_ENV:
        raise ValueError("Unrecognized diagnostic dispatch mode")
    envval = os.environ.get("NPY_DISABLE_CPU_FEATURES")
    if envval != MODE_ENV[mode]:
        raise ValueError("Dispatch mode must be configured before NumPy import")
    runtime = runtime_details()
    if runtime["numpy"] != EXPECTED_NUMPY:
        raise ValueError("Pinned NumPy direct package version changed")
    if mode == "no-avx2-fma3":
        for feature in ("AVX2", "FMA3"):
            if runtime["cpu_features_enabled"].get(feature) is not False:
                raise ValueError(f"Intended CPU feature was not disabled: {feature}")
    return {
        "schema_version": 1,
        "experiment": EXPERIMENT,
        "design": "within_host_base_vs_mask_pairing_3_hosts_2_processes_each_arm",
        "replica": replica,
        "mode": mode,
        "source_trace_run": 39177889565,
        "frozen_input_sha256": fingerprint(FROZEN_CASES),
        "case_results": stage_observations(),
        "runtime": runtime,
    }


def validate_observation(rec: dict) -> None:
    if rec.get("schema_version") != 1 or rec.get("experiment") != EXPERIMENT:
        raise ValueError("Wrong issue #62 scientific study/schema")
    if rec.get("frozen_input_sha256") != fingerprint(FROZEN_CASES):
        raise ValueError("Different frozen hexadecimal source operands")
    mode = rec.get("mode")
    if mode not in MODE_ENV:
        raise ValueError("Unexpected SIMD intervention arm")
    rt = rec["runtime"]
    if rt.get("env", {}).get("NPY_DISABLE_CPU_FEATURES") != MODE_ENV[mode]:
        raise ValueError("SIMD intervention does not match recorded runtime")
    if rt.get("numpy") != EXPECTED_NUMPY:
        raise ValueError("Core direct NumPy dependency changed")
    features = rt["cpu_features_enabled"]
    if mode == "no-avx2-fma3" and any(
        features.get(k) is not False for k in ("AVX2", "FMA3")
    ):
        raise ValueError("Requested SIMD mask was not actually active")
    if len(rec["case_results"]) != len(FROZEN_CASES):
        raise ValueError("Omitted frozen operation")
    for expected, observed in zip(FROZEN_CASES, rec["case_results"]):
        if {k: observed[k] for k in expected} != expected:
            raise ValueError("Frozen source operand or operation has changed")
        outputs = [observed["result_float64_hex"]]
        stages = observed["diagnostic_stages"]
        required = (
            {"squares_float64_hex", "np_sum_squares_float64_hex",
             "np_sqrt_sum_float64_hex", "math_hypot_float64_hex"}
            if expected["operation"] == "numpy.linalg.norm" else
            {"math_exp_float64_hex", "numpy_exp_array_one_float64_hex"}
        )
        if set(stages) != required:
            raise ValueError("Diagnostic stage missing or altered")
        for v in stages.values():
            outputs.extend(v if isinstance(v, list) else [v])
        if any(not isinstance(x, str) or not math.isfinite(float.fromhex(x))
               for x in outputs):
            raise ValueError("Invalid IEEE754 hexadecimal numerical evidence")
    compiled = rt.get("extensions_sha256", [])
    if len(compiled) < 2 or any(
        not len(x["sha256"]) == 64 or x["bytes"] < 1 for x in compiled
    ):
        raise ValueError("Missing numerical extension binary provenance")


def compare(records: list[dict]) -> dict:
    if len(records) != 12:
        raise ValueError("Require twelve processes: 3 hosts × 2 arms × 2 repeats")
    by_name = {}
    for rec in records:
        validate_observation(rec)
        name = rec["replica"]
        if name in by_name:
            raise ValueError("Duplicate process identity")
        by_name[name] = rec
    expected = {f"r{host}-{mode}-{p}"
                for host in range(1, 4)
                for mode in MODE_ENV for p in ("a", "b")}
    if set(by_name) != expected:
        raise ValueError("Missing process, mode, or host")
    groups = []
    for host in range(1, 4):
        prefix = f"r{host}"
        baseline = [by_name[f"{prefix}-baseline-{p}"] for p in ("a", "b")]
        masked = [by_name[f"{prefix}-no-avx2-fma3-{p}"] for p in ("a", "b")]
        allrec = baseline + masked
        hashes = [
            tuple((f["basename"], f["sha256"]) for f in r["runtime"]["extensions_sha256"])
            for r in allrec
        ]
        if len(set(hashes)) != 1:
            raise ValueError("Different installed NumPy binaries *within same runner*")
        runtimes = [
            (r["runtime"]["machine"], r["runtime"]["cpu_model"],
             r["runtime"]["numpy"], r["runtime"]["libc"]) for r in allrec
        ]
        if len({json.dumps(x) for x in runtimes}) != 1:
            raise ValueError("Host environment changed within paired intervention")
        individual = []
        for idx, case in enumerate(FROZEN_CASES):
            baseline_vals = [r["case_results"][idx]["result_float64_hex"]
                             for r in baseline]
            mask_vals = [r["case_results"][idx]["result_float64_hex"] for r in masked]
            diag_keys = baseline[0]["case_results"][idx]["diagnostic_stages"]
            diag_changes = {
                key: {
                    "baseline": baseline[0]["case_results"][idx]["diagnostic_stages"][key],
                    "masked": masked[0]["case_results"][idx]["diagnostic_stages"][key],
                } for key in diag_keys if (
                    baseline[0]["case_results"][idx]["diagnostic_stages"][key]
                    != masked[0]["case_results"][idx]["diagnostic_stages"][key]
                )
            }
            individual.append({
                "case": case["id"], "operation": case["operation"],
                "baseline_exact_results": baseline_vals,
                "masked_exact_results": mask_vals,
                "baseline_internal_repeat_equal": baseline_vals[0] == baseline_vals[1],
                "masked_internal_repeat_equal": mask_vals[0] == mask_vals[1],
                "paired_dispatch_intervention_changed_result": (
                    baseline_vals[0] != mask_vals[0]
                ),
                "diagnostic_stage_changes": diag_changes,
            })
        groups.append({
            "host": prefix,
            "machine": allrec[0]["runtime"]["machine"],
            "cpu_model": allrec[0]["runtime"]["cpu_model"],
            "numpy_extension_sha256": hashes[0],
            "baseline_enabled_dispatch": sorted(
                k for k, val in baseline[0]["runtime"]["cpu_features_enabled"].items()
                if val
            ),
            "masked_enabled_dispatch": sorted(
                k for k, val in masked[0]["runtime"]["cpu_features_enabled"].items()
                if val
            ),
            "within_host_intervention": individual,
            "paired_intervention_changed_cases": [
                x["case"] for x in individual
                if x["paired_dispatch_intervention_changed_result"]
            ],
            "within_arm_repeats_all_exact": all(
                x["baseline_internal_repeat_equal"] and x["masked_internal_repeat_equal"]
                for x in individual
            ),
        })
    first_arms = {
        mode: {
            c["id"]: {
                group["host"]: by_name[
                    f"{group['host']}-{mode}-a"
                ]["case_results"][i]["result_float64_hex"]
                for group in groups
            }
            for i, c in enumerate(FROZEN_CASES)
        } for mode in MODE_ENV
    }
    return {
        "schema_version": 1,
        "issue": 62,
        "study": EXPERIMENT,
        "frozen_input_sha256": fingerprint(FROZEN_CASES),
        "processes": len(records),
        "hosts": len(groups),
        "exact_processes_per_host_arm": 2,
        "groups": groups,
        "cross_host_modes_by_arm": {
            mode: {
                name: sorted(set(values.values()))
                for name, values in cases.items()
            } for mode, cases in first_arms.items()
        },
        "limits": [
            "A NumPy AVX2/FMA3 mask is a dispatch intervention, not a fixed binary/runtime guarantee",
            "Unchanged norm/exp under a mask cannot exclude BLAS/libm or other dispatched features",
            "A changed result under the mask supports a dispatch-sensitive effect within that observed host",
            "The SIMD mask is NOT applied to the working lake notebook/SCIP/SA science",
            "No quantum-hardware advantage or universal cross-platform result is inferred",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replica", type=str)
    parser.add_argument("--mode", choices=list(MODE_ENV))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--inputs-root", type=Path)
    parser.add_argument("--report", type=Path)
    a = parser.parse_args()
    if a.replica and a.mode and a.output and not a.inputs_root and not a.report:
        if a.output.exists():
            raise FileExistsError("Never replace an existing scientific process record")
        a.output.parent.mkdir(parents=True, exist_ok=True)
        result = measure(a.replica, a.mode)
        a.output.write_bytes(canonical(result))
        print("NUMPY_DISPATCH_RUN " + json.dumps({
            "replica": a.replica, "mode": a.mode, "cpu": result["runtime"]["cpu_model"],
            "binary": result["runtime"]["extensions_sha256"][0]["sha256"],
        }, sort_keys=True))
    elif a.inputs_root and a.report and not a.replica and not a.mode and not a.output:
        paths = sorted(a.inputs_root.rglob("dispatch-*.json"))
        if len(paths) != 12:
            raise ValueError(f"Expected 12 process records, found {len(paths)}")
        payloads = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
        for p, data in zip(paths, payloads):
            if p.stem != f"dispatch-{data['replica']}":
                raise ValueError("Mislabeled host/arm original artifact")
        report = compare(payloads)
        if a.report.exists():
            raise FileExistsError("Never replace cross-host comparison evidence")
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_bytes(canonical(report))
        print("NUMPY_DISPATCH_COMPARE " + json.dumps({
            "hosts": report["hosts"],
            "processes": report["processes"],
            "changes_by_host": {
                g["host"]: g["paired_intervention_changed_cases"]
                for g in report["groups"]
            },
            "exact_within_arm_repeats": all(
                g["within_arm_repeats_all_exact"] for g in report["groups"]
            ),
        }, sort_keys=True))
    else:
        parser.error("Choose --replica/--mode/--output OR --inputs-root/--report")


if __name__ == "__main__":
    main()
