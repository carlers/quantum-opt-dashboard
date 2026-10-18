"""Exploratory frozen-operand NumPy microprobe for N20 precision issue #60.

After observing source-derived per-edge traces, pin *identical hexadecimal
operands* and call precisely the NumPy public operations used by the working
notebook. These microcases are diagnostic, not a model reconstruction or QUBO.
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

SOURCE_RUN = 39177889565
FROZEN_CASES = (
    # Exact source-verified IEEE754 N20 displacement fields from run #39177889565.
    {"id": "norm_f0_fixed32", "operation": "numpy.linalg.norm",
     "hex_operands": ["-0x1.7c87abdfc7720p+13", "-0x1.b616b40494300p+13"]},
    {"id": "norm_f9_fixed26", "operation": "numpy.linalg.norm",
     "hex_operands": ["0x1.2448984a83480p+11", "-0x1.6d9ffffffff00p+12"]},
    {"id": "norm_f10_fixed30", "operation": "numpy.linalg.norm",
     "hex_operands": ["0x1.4ffaf6f795f40p+12", "-0x1.1d72e87906a00p+11"]},
    {"id": "norm_f17_fixed25", "operation": "numpy.linalg.norm",
     "hex_operands": ["0x1.2448984a834c0p+12", "-0x1.5180000000200p+11"]},
    {"id": "exp_f3_fixed28", "operation": "numpy.exp",
     "hex_operands": ["-0x1.748da045f362dp+3"]},
    {"id": "exp_f19_fixed22", "operation": "numpy.exp",
     "hex_operands": ["-0x1.0d03a2a2a712cp+3"]},
)
EXPECTED_NUMPY = "2.5.4"


def canonical(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       allow_nan=False, ensure_ascii=False) + "\n").encode("utf-8")


def fingerprint(obj: object) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def safe_cpu_model() -> str | None:
    f = Path("/proc/cpuinfo")
    if f.is_file():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.partition(":")[2].strip()
    return platform.processor() or None


def calculate_cases() -> list[dict]:
    if np.__version__ != EXPECTED_NUMPY:
        raise RuntimeError("Frozen NumPy direct version changed")
    result = []
    for case in FROZEN_CASES:
        values = [float.fromhex(s) for s in case["hex_operands"]]
        if not all(math.isfinite(x) for x in values):
            raise ValueError("Nonfinite frozen input")
        if case["operation"] == "numpy.linalg.norm":
            assert len(values) == 2
            # Preserve the working notebook's exact np.linalg.norm call shape.
            answer = float(np.linalg.norm(np.array(values, dtype=np.float64)))
        elif case["operation"] == "numpy.exp":
            assert len(values) == 1
            answer = float(np.exp(np.float64(values[0])))
        else:
            raise ValueError("Unrecognized frozen numeric operation")
        if not math.isfinite(answer):
            raise ValueError("Nonfinite frozen math result")
        result.append({**case, "result_float64_hex": answer.hex()})
    return result


def run_one(replica: str) -> dict:
    return {
        "schema_version": 1,
        "study": "issue60_exploratory_frozen_numpy_operations",
        "source_n20_trace_run_id": SOURCE_RUN,
        "frozen_input_sha256": fingerprint(FROZEN_CASES),
        "replica": replica,
        "cases": calculate_cases(),
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "cpu_model": safe_cpu_model(),
            "numeric_thread_environment": {
                k: os.environ.get(k)
                for k in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS")
            },
        },
    }


def compare_six(items: list[dict]) -> dict:
    if len(items) != 6:
        raise ValueError("Expected six independent frozen math process results")
    by_name = {item.get("replica"): item for item in items}
    expected = {f"r{h}-{p}" for h in range(1, 4) for p in ("a", "b")}
    if set(by_name) != expected:
        raise ValueError("Missing or duplicate host/process identity")
    for record in items:
        if record.get("study") != "issue60_exploratory_frozen_numpy_operations":
            raise ValueError("Wrong microprobe experiment type")
        if record.get("source_n20_trace_run_id") != SOURCE_RUN or (
            record.get("frozen_input_sha256") != fingerprint(FROZEN_CASES)
        ):
            raise ValueError("Frozen mathematical input fingerprint differs")
        if record["runtime"]["numpy"] != EXPECTED_NUMPY:
            raise ValueError("Changed pinned NumPy package version")
        if len(record["cases"]) != len(FROZEN_CASES):
            raise ValueError("Missing diagnostic operation")
        for source, result in zip(FROZEN_CASES, record["cases"]):
            if {k: result[k] for k in source} != source:
                raise ValueError("Modified frozen float64 input or case ordering")
            value = float.fromhex(result["result_float64_hex"])
            if not math.isfinite(value):
                raise ValueError("Nonfinite result for fixed math case")
    rows = []
    for index, case in enumerate(FROZEN_CASES):
        values = {name: by_name[name]["cases"][index]["result_float64_hex"]
                  for name in sorted(by_name)}
        modes = sorted(set(values.values()))
        lower = [float.fromhex(v) for v in modes]
        rows.append({
            "id": case["id"],
            "operation": case["operation"],
            "exact_hex_operands": case["hex_operands"],
            "result_modes": modes,
            "exact_distinct_results": len(modes),
            "max_absolute_difference": max(lower) - min(lower),
            "result_by_replica": values,
        })
    return {
        "schema_version": 1,
        "exploratory_after_source_trace": True,
        "source_run_id": SOURCE_RUN,
        "frozen_input_sha256": fingerprint(FROZEN_CASES),
        "process_count": 6,
        "cases": rows,
        "numeric_operations_with_multiple_modes": [
            r["id"] for r in rows if r["exact_distinct_results"] > 1
        ],
        "runtime_by_replica": {name: by_name[name]["runtime"] for name in sorted(by_name)},
        "interpretation_limits": [
            "A matching mode does not prove cross-architecture determinism",
            "A changed frozen NumPy operation result suggests library/runtime-dependent behavior, not a proven CPU instruction",
            "This is a post-observation exploratory microbenchmark, not a new preregistered replication",
            "No historical input or sampler/solver mathematics were changed",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replica")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--inputs-root", type=Path)
    parser.add_argument("--report", type=Path)
    a = parser.parse_args()
    if a.replica and a.output and not a.inputs_root and not a.report:
        if a.output.exists():
            raise FileExistsError("Cannot overwrite immutable microprobe evidence")
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_bytes(canonical(run_one(a.replica)))
    elif a.inputs_root and a.report and not a.replica and not a.output:
        entries = sorted(a.inputs_root.rglob("math-micro-*.json"))
        if len(entries) != 6:
            raise ValueError(f"Need 6 fresh microprobe records, got {len(entries)}")
        records = [json.loads(p.read_text(encoding="utf-8")) for p in entries]
        report = compare_six(records)
        if a.report.exists():
            raise FileExistsError("Refusing to overwrite experimental comparison")
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_bytes(canonical(report))
        print("N20_FROZEN_NUMPY_MICROPROBE " + json.dumps({
            "processes": report["process_count"],
            "different_operations": report["numeric_operations_with_multiple_modes"],
            "modes": {v["id"]: v["exact_distinct_results"] for v in report["cases"]},
        }, sort_keys=True))
    else:
        parser.error("Choose --replica + --output OR --inputs-root + --report")


if __name__ == "__main__":
    main()
