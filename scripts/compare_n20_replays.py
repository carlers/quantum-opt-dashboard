"""Compare *unmodified* N20 cold-replay manifests across independent processes.

This is observational: differences in exact SHA are reported, not normalized away.
The exact source-to-objective checks run in scripts/run_n20_reference_notebook.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
from typing import Any

SCHEMA = "notebook_derived_N20_replay_not_paper_parity"
REL_TOL = 1e-12
ABS_TOL = 1e-10
ENERGY_ABS_TOL = 1e-7
CORE_VERSIONS = ("python", "numpy", "scipy", "shapely", "pyscipopt")


def canonical(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def safe_runtime_metadata(replica: str) -> dict[str, Any]:
    """Record narrow execution provenance, deliberately excluding secrets."""
    model_name = None
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                model_name = line.partition(":")[2].strip()
                break
    return {
        "schema_version": 1,
        "replica": replica,
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_sha": os.environ.get("GITHUB_SHA"),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": model_name,
        "cpu_count": os.cpu_count(),
        "numeric_thread_environment": {
            key: os.environ.get(key)
            for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }


def walk_diff(a: Any, b: Any, prefix: str = "") -> list[dict[str, Any]]:
    """Return leaf-level differences, retaining exact hexadecimal coefficient values."""
    if type(a) is not type(b):
        return [{"path": prefix, "kind": "type", "a": repr(a), "b": repr(b)}]
    if isinstance(a, dict):
        output = []
        for key in sorted(a.keys() | b.keys()):
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in a or key not in b:
                output.append({"path": path, "kind": "missing_field"})
            else:
                output.extend(walk_diff(a[key], b[key], path))
        return output
    if isinstance(a, list):
        if len(a) != len(b):
            return [{"path": prefix, "kind": "length", "a": len(a), "b": len(b)}]
        differences = []
        for i, (left, right) in enumerate(zip(a, b)):
            differences.extend(walk_diff(left, right, f"{prefix}[{i}]"))
        return differences
    if a == b:
        return []
    if isinstance(a, str) and a.startswith(("0x", "-0x")) and "p" in a:
        try:
            x, y = float.fromhex(a), float.fromhex(b)
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError("nonfinite coefficient")
            delta = abs(x-y)
            ulps = delta / max(math.ulp(x), math.ulp(y))
            return [{
                "path": prefix,
                "kind": "float_hex",
                "a": a,
                "b": b,
                "absolute_difference": delta,
                "ulp_distance_estimate": ulps,
                "within_declared_tolerance": math.isclose(
                    x, y, rel_tol=REL_TOL, abs_tol=ABS_TOL
                ),
            }]
        except (ValueError, OverflowError):
            pass
    return [{"path": prefix, "kind": "structural", "a": a, "b": b}]


def compare(records: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    if len(records) < 2:
        raise ValueError("At least two *fresh-process* replay results are required")
    records = sorted(records, key=lambda r: r[0])
    baseline_name, baseline = records[0]
    for filename, payload in records:
        if payload.get("status") != SCHEMA or payload.get("schema_version") != 2:
            raise ValueError(f"{filename}: not a verified notebook-derived N20 v2 record")
        model = payload["model_input"]
        calculated = hashlib.sha256(canonical(model)).hexdigest()
        if payload["model_input_sha256"] != calculated:
            raise ValueError(f"{filename}: model checksum mismatch")
        if payload.get("scip_status") != "optimal":
            raise ValueError(f"{filename}: SCIP did not certify optimality")
        if payload.get("enumerated_combinations") != 15504:
            raise ValueError(f"{filename}: not an exhaustive N20/K5 replay")
        if not math.isclose(payload["original_energy"], payload["enumeration_energy"],
                            abs_tol=ENERGY_ABS_TOL, rel_tol=0.0):
            raise ValueError(f"{filename}: SCIP/independent enumeration energy mismatch")
    observations = []
    reference_fingerprint = baseline["model_input_sha256"]
    semantic_failure = False
    for name, result in records:
        differences = walk_diff(baseline["model_input"], result["model_input"])
        changed_numeric = [d for d in differences if d["kind"] == "float_hex"]
        changed_structural = [d for d in differences if d["kind"] != "float_hex"]
        numerical_outside = [
            d for d in changed_numeric if not d["within_declared_tolerance"]
        ]
        selections_equal = (
            result["selected_local_positions"] == baseline["selected_local_positions"]
            and result["selected_master_feature_positions"]
            == baseline["selected_master_feature_positions"]
        )
        energy_agrees = math.isclose(
            result["original_energy"], baseline["original_energy"],
            rel_tol=0.0, abs_tol=ENERGY_ABS_TOL
        )
        versions_equal = all(
            result["scientific_environment"].get(k)
            == baseline["scientific_environment"].get(k) for k in CORE_VERSIONS
        )
        if changed_structural or numerical_outside or not selections_equal or (
            not energy_agrees
        ) or not versions_equal:
            semantic_failure = True
        observations.append({
            "file": name,
            "model_input_sha256": result["model_input_sha256"],
            "exact_model_equal_to_first": result["model_input_sha256"]
            == reference_fingerprint,
            "numeric_leaf_changes": changed_numeric,
            "structural_leaf_changes": changed_structural,
            "outside_numeric_tolerance": numerical_outside,
            "selected_sites_agree": selections_equal,
            "energy_agrees_within_1e-7": energy_agrees,
            "core_dependency_versions_equal": versions_equal,
            "scientific_environment": result["scientific_environment"],
            "energy": result["original_energy"],
        })
    exact_hashes = sorted({r["model_input_sha256"] for _, r in records})
    return {
        "schema_version": 1,
        "scope": "notebook N20/K5 original-model input only; not historical QUBO or SA",
        "source": baseline_name,
        "number_of_independent_process_records": len(records),
        "exact_model_hashes": exact_hashes,
        "exact_model_fingerprint_stable_in_observed_sample": len(exact_hashes) == 1,
        "observations": observations,
        "semantic_pass_with_tolerance": not semantic_failure,
        "tolerances": {"numeric_relative": REL_TOL, "numeric_absolute": ABS_TOL,
                       "original_energy_absolute": ENERGY_ABS_TOL},
        "interpretation_limits": [
            "A uniform digest in this sample does not prove cross-host determinism",
            "Different raw hashes can represent negligible floating-point differences",
            "This protocol neither compiles QUBO nor runs OpenJij",
            "CPU model association is not causal evidence",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-output", type=Path)
    parser.add_argument("--replica", type=str)
    parser.add_argument("--inputs-root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--min-results", type=int, default=2)
    args = parser.parse_args()
    if args.metadata_output:
        if not args.replica or args.inputs_root or args.report:
            parser.error("metadata mode needs only --metadata-output and --replica")
        args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
        args.metadata_output.write_bytes(canonical(safe_runtime_metadata(args.replica)))
        return 0
    if not args.inputs_root or not args.report:
        parser.error("comparison needs --inputs-root and --report")
    inputs = sorted(args.inputs_root.rglob("replicate-*.json"))
    if len(inputs) < args.min_results:
        raise ValueError(f"Need {args.min_results} fresh result files; found {len(inputs)}")
    parsed = [(str(p.relative_to(args.inputs_root)),
               json.loads(p.read_text(encoding="utf-8"))) for p in inputs]
    report = compare(parsed)
    runtime_paths = sorted(args.inputs_root.rglob("runtime.json"))
    report["host_environment_records"] = [
        json.loads(path.read_text(encoding="utf-8")) for path in runtime_paths
    ]
    output = canonical(report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if args.report.exists():
        raise FileExistsError(f"Refusing to overwrite comparison report: {args.report}")
    args.report.write_bytes(output)
    print(json.dumps({
        "number_of_processes": report["number_of_independent_process_records"],
        "distinct_exact_model_hashes": len(report["exact_model_hashes"]),
        "semantic_pass_with_tolerance": report["semantic_pass_with_tolerance"],
        "host_records": len(runtime_paths),
        "hashes": report["exact_model_hashes"],
    }, sort_keys=True))
    if not report["semantic_pass_with_tolerance"]:
        raise AssertionError("Changed structural model or unacceptable numeric drift")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
