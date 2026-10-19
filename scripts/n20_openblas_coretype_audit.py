"""Issue #62 second, explicitly exploratory, frozen-operand OpenBLAS target test.

Set OPENBLAS_CORETYPE=HASWELL BEFORE launching the Python process, never
inside the same imported process. This records observation, not a model change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

from scripts.n20_frozen_math_microprobe import FROZEN_CASES, canonical, fingerprint
from scripts.n20_numpy_dispatch_audit import runtime_details, stage_observations

STUDY = "issue62_exploratory_openblas_target_haswell_vs_auto"
ARMS = {"auto": None, "haswell": "HASWELL"}
N_HOSTS, REPEATS = 3, 2


def runtime_blas_architecture(runtime: dict) -> str:
    infos = [
        item for item in runtime["show_runtime_allowlisted"]
        if item.get("internal_api") == "openblas"
    ]
    if len(infos) != 1:
        raise ValueError(f"Expected exactly one loaded OpenBLAS: got {len(infos)}")
    result = infos[0].get("architecture")
    if not isinstance(result, str) or not result:
        raise ValueError("Missing OpenBLAS selected runtime target")
    return result


def run_one(replica: str, arm: str) -> dict:
    if arm not in ARMS:
        raise ValueError("Unrecognized preregistered target arm")
    if os.environ.get("NPY_DISABLE_CPU_FEATURES") is not None:
        raise ValueError("Cannot conflate NumPy SIMD intervention with BLAS study")
    if os.environ.get("OPENBLAS_CORETYPE") != ARMS[arm]:
        raise ValueError("OpenBLAS target override must be set before NumPy import")
    rt = runtime_details()
    if rt["numpy"] != "2.5.4":
        raise ValueError("NumPy version differs from source microprobe")
    reported_arch = runtime_blas_architecture(rt)
    if arm == "haswell" and reported_arch.lower() != "haswell":
        raise ValueError("Requested OpenBLAS Haswell target was not actually selected")
    return {
        "schema_version": 1,
        "study": STUDY,
        "arm": arm,
        "replica": replica,
        "frozen_input_sha256": fingerprint(FROZEN_CASES),
        "source_n20_pair_trace_run_id": 39177889565,
        "openblas_coretype_env": os.environ.get("OPENBLAS_CORETYPE"),
        "openblas_selected_architecture": reported_arch,
        "case_results": stage_observations(),
        "runtime": rt,
    }


def verify_record(row: dict) -> None:
    if row.get("schema_version") != 1 or row.get("study") != STUDY:
        raise ValueError("Wrong original OpenBLAS experiment")
    if row.get("frozen_input_sha256") != fingerprint(FROZEN_CASES):
        raise ValueError("Different frozen original source operands")
    arm = row.get("arm")
    if arm not in ARMS or row.get("openblas_coretype_env") != ARMS[arm]:
        raise ValueError("Wrong preregistered OpenBLAS override")
    rt = row["runtime"]
    if rt.get("numpy") != "2.5.4":
        raise ValueError("Changed frozen NumPy version")
    if row["openblas_selected_architecture"] != runtime_blas_architecture(rt):
        raise ValueError("OpenBLAS reported target contradicts runtime report")
    if arm == "haswell" and row["openblas_selected_architecture"].lower() != "haswell":
        raise ValueError("Haswell override is not confirmed")
    if len(row["case_results"]) != len(FROZEN_CASES):
        raise ValueError("Truncated frozen operation list")
    for case, result in zip(FROZEN_CASES, row["case_results"]):
        if any(result.get(k) != v for k, v in case.items()):
            raise ValueError("Frozen exact IEEE754 source input was modified")
        values = [result.get("result_float64_hex")]
        stages = result.get("diagnostic_stages", {})
        if not isinstance(stages, dict) or not stages:
            raise ValueError("Missing independent arithmetic diagnostics")
        for val in stages.values():
            values.extend(val if isinstance(val, list) else [val])
        if any(not isinstance(v, str) or not math.isfinite(float.fromhex(v))
               for v in values):
            raise ValueError("Invalid original floating evidence")
    if len(rt.get("extensions_sha256", [])) < 3:
        raise ValueError("Missing compiled numerical binary checksums")


def compare(rows: list[dict]) -> dict:
    if len(rows) != N_HOSTS * len(ARMS) * REPEATS:
        raise ValueError("Exactly 12 independent fixed-input processes required")
    by_name = {}
    for row in rows:
        verify_record(row)
        replica = row["replica"]
        if replica in by_name:
            raise ValueError("Duplicate original process")
        by_name[replica] = row
    names = {f"r{host}-{arm}-{p}" for host in range(1, N_HOSTS + 1)
             for arm in ARMS for p in ("a", "b")}
    if set(by_name) != names:
        raise ValueError("Missing paired host/arm/process results")
    hosts = []
    for h in range(1, N_HOSTS + 1):
        pairs = {
            arm: [by_name[f"r{h}-{arm}-{p}"] for p in ("a", "b")]
            for arm in ARMS
        }
        all_rows = pairs["auto"] + pairs["haswell"]
        binary_ids = [
            tuple((f["basename"], f["sha256"])
                  for f in row["runtime"]["extensions_sha256"])
            for row in all_rows
        ]
        if len(set(binary_ids)) != 1:
            raise ValueError("Within-host NumPy/OpenBLAS compiled binary drift")
        machine = [
            (x["runtime"]["cpu_model"], x["runtime"]["machine"],
             x["runtime"]["python"], tuple(x["runtime"]["libc"]))
            for x in all_rows
        ]
        if len(set(machine)) != 1:
            raise ValueError("Host changed between auto and forced BLAS processes")
        cases = []
        for i, c in enumerate(FROZEN_CASES):
            auto = [row["case_results"][i]["result_float64_hex"]
                    for row in pairs["auto"]]
            forced = [row["case_results"][i]["result_float64_hex"]
                      for row in pairs["haswell"]]
            cases.append({
                "case_id": c["id"], "operation": c["operation"],
                "auto_result_hex": auto,
                "forced_result_hex": forced,
                "auto_repeats_exact": auto[0] == auto[1],
                "forced_repeats_exact": forced[0] == forced[1],
                "openblas_override_changed_result": auto[0] != forced[0],
                "alternative_diagnostics_changed": [
                    k for k, v in pairs["auto"][0]["case_results"][i][
                        "diagnostic_stages"].items()
                    if v != pairs["haswell"][0]["case_results"][i][
                        "diagnostic_stages"].get(k)
                ],
            })
        hosts.append({
            "host": f"r{h}",
            "cpu_model": all_rows[0]["runtime"]["cpu_model"],
            "machine": all_rows[0]["runtime"]["machine"],
            "openblas_auto_architecture": pairs["auto"][0][
                "openblas_selected_architecture"
            ],
            "openblas_forced_architecture": pairs["haswell"][0][
                "openblas_selected_architecture"
            ],
            "numpy_compiled_files_sha256": binary_ids[0],
            "cases": cases,
            "cases_changed_on_same_host": [
                c["case_id"] for c in cases if c["openblas_override_changed_result"]
            ],
            "within_arm_repeatable": all(
                c["auto_repeats_exact"] and c["forced_repeats_exact"] for c in cases
            ),
        })
    return {
        "schema_version": 1,
        "study": STUDY,
        "issue": 62,
        "preregistered_followup_after_numpy_mask_results": True,
        "source_frozen_operand_sha256": fingerprint(FROZEN_CASES),
        "hosts": hosts,
        "total_processes": len(rows),
        "observed_target_changes": {
            g["host"]: g["cases_changed_on_same_host"] for g in hosts
        },
        "limitations": [
            "Overrides only OpenBLAS dynamic kernel selection, not NumPy's SIMD ufunc dispatch",
            "A result difference is observed target sensitivity, not proof of a specific assembly instruction",
            "A host already selecting Haswell is a negative control",
            "Alternative scalar math diagnostics do not replace the original N20 scientific model",
            "Same full NumPy/OpenBLAS file hashes do not binary-lock CPU microcode or runtime state",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--replica")
    p.add_argument("--arm", choices=list(ARMS))
    p.add_argument("--output", type=Path)
    p.add_argument("--inputs-root", type=Path)
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    if a.replica and a.arm and a.output and not a.inputs_root and not a.report:
        if a.output.exists():
            raise FileExistsError("Refusing to overwrite source result")
        a.output.parent.mkdir(parents=True, exist_ok=True)
        result = run_one(a.replica, a.arm)
        a.output.write_bytes(canonical(result))
        print("OPENBLAS_SOURCE_RUN " + json.dumps({
            "replica": a.replica, "target": result["openblas_selected_architecture"],
            "arm": a.arm, "binary_count": len(result["runtime"]["extensions_sha256"])
        }, sort_keys=True))
    elif a.inputs_root and a.report and not a.replica and not a.arm and not a.output:
        paths = sorted(a.inputs_root.rglob("blas-*.json"))
        if len(paths) != 12:
            raise ValueError("Expected exactly twelve independent original records")
        payloads = [json.loads(x.read_text(encoding="utf-8")) for x in paths]
        for path, payload in zip(paths, payloads):
            if path.stem != f"blas-{payload['replica']}":
                raise ValueError("Host process file mislabeled")
        report = compare(payloads)
        if a.report.exists():
            raise FileExistsError("Refusing to overwrite original comparison")
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_bytes(canonical(report))
        print("OPENBLAS_CORETYPE_AUDIT " + json.dumps({
            "hosts": len(report["hosts"]),
            "processes": report["total_processes"],
            "changed": report["observed_target_changes"],
            "auto_targets": {
                h["host"]: h["openblas_auto_architecture"] for h in report["hosts"]
            },
        }, sort_keys=True))
    else:
        p.error("Choose --replica/--arm/--output OR --inputs-root/--report")


if __name__ == "__main__":
    main()
