"""Independently audit the actual N20 read-only free/fixed coefficient trace.

All 300 pair records must be accounted for, and every recorded addition must
replay to the exact binary64 coefficient in the authoritative original model.
The report identifies the first *observed* recorded divergence, not a causal
hardware/library conclusion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

def canonical(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


N_FREE = 20
N_FIXED = 15
ORDERED_STAGES = (
    "stage", "displacement_float64_hex", "distance_float64_hex",
    "within_one_hop_radius", "redundancy_float64_hex",
    "cosine_unclipped_float64_hex", "cosine_float64_hex",
    "decay_exponent_float64_hex", "decay_probe_separate_call_float64_hex",
    "wake_forward_float64_hex", "wake_backward_float64_hex",
    "coefficient_float64_hex", "linear_before_add_float64_hex",
    "linear_after_add_float64_hex",
)
ALLOWED_STAGES = {
    "geometry_rejected", "zero_distance", "outside_interaction_radius",
    "below_coefficient_threshold", "added_to_linear",
}
HEX_PREFIX = ("0x", "-0x")


def as_number(value: str) -> float:
    if not isinstance(value, str) or not value.startswith(HEX_PREFIX):
        raise ValueError("Invalid recorded hexadecimal IEEE754 coefficient")
    parsed = float.fromhex(value)
    if not math.isfinite(parsed):
        raise ValueError("Non-finite diagnostic coefficient")
    return parsed


def scientific_core_sha(record: dict) -> str:
    model = record["model_input"]
    clean = {k: v for k, v in model.items() if k != "free_fixed_pair_trace"}
    return hashlib.sha256(canonical(clean)).hexdigest()


def verify_record(record: dict) -> list[dict]:
    model = record["model_input"]
    trace = model.get("free_fixed_pair_trace")
    if not isinstance(trace, list) or len(trace) != N_FREE * N_FIXED:
        raise ValueError("Expected precisely 300 free/fixed original loop pairs")
    expected_free = model["candidate_master_feature_positions"]
    expected_fixed = model["fixed_master_feature_positions"]
    if len(expected_free) != N_FREE or len(expected_fixed) != N_FIXED:
        raise ValueError("Invalid original free/fixed master positions")
    running = [
        as_number(v) for v in model["linear_before_fixed_pairs_float64_hex"]
    ]
    if len(running) != N_FREE:
        raise ValueError("Wrong original linear starter length")
    for index, record_pair in enumerate(trace):
        i, fixed_slot = divmod(index, N_FIXED)
        j = N_FREE + fixed_slot
        if (record_pair["free_local"], record_pair["fixed_local"],
            record_pair["free_master_feature"],
            record_pair["fixed_master_feature"]) != (
                i, j, expected_free[i], expected_fixed[fixed_slot]
        ):
            raise ValueError(f"Unexpected free/fixed pair ordering or master IDs at {index}")
        stage = record_pair.get("stage")
        if stage not in ALLOWED_STAGES:
            raise ValueError(f"Unknown interaction trace stage {stage}")
        if stage != "geometry_rejected":
            coords = record_pair.get("displacement_float64_hex")
            if len(coords) != 2:
                raise ValueError("Missing projected displacement")
            for item in coords:
                as_number(item)
            as_number(record_pair["distance_float64_hex"])
        if stage in {"below_coefficient_threshold", "added_to_linear"}:
            for key in (
                "redundancy_float64_hex", "cosine_float64_hex",
                "wake_forward_float64_hex", "wake_backward_float64_hex",
                "coefficient_float64_hex",
            ):
                as_number(record_pair[key])
            coefficient = as_number(record_pair["coefficient_float64_hex"])
            if stage == "below_coefficient_threshold" and abs(coefficient) > 1e-12:
                raise ValueError("Coefficient threshold trace contradicts source code")
        if stage == "added_to_linear":
            coefficient = as_number(record_pair["coefficient_float64_hex"])
            if abs(coefficient) <= 1e-12:
                raise ValueError("Pair marked added despite original coefficient threshold")
            if as_number(record_pair["linear_before_add_float64_hex"]) != running[i]:
                raise ValueError(f"Linear coefficient addition order changed at pair {index}")
            running[i] += coefficient
            if as_number(record_pair["linear_after_add_float64_hex"]) != running[i]:
                raise ValueError(f"Linear after-add differs from recorded pair term {index}")
        else:
            if ("linear_before_add_float64_hex" in record_pair or
                    "linear_after_add_float64_hex" in record_pair):
                raise ValueError("No addition should be recorded for skipped pairs")
    final = [as_number(v) for v in model["linear_float64_hex"]]
    if final != running:
        raise ValueError("Trace sum not exactly identical to authoritative model linear terms")
    return trace


def compare(records: list[tuple[str, dict]]) -> dict:
    if len(records) != 6:
        raise ValueError("Must compare exactly six independent N20 cold-kernel executions")
    # Require source-level fingerprint verification before interpreting diagnostics.
    normalized = []
    for name, rec in sorted(records):
        if rec.get("schema_version") != 2 or rec.get("scip_status") != "optimal":
            raise ValueError("Missing source-verified SCIP N20 result")
        if rec.get("enumerated_combinations") != 15504:
            raise ValueError("Missing independent 15,504-combination exact check")
        digest = hashlib.sha256(canonical(rec["model_input"])).hexdigest()
        if digest != rec["model_input_sha256"]:
            raise ValueError("Tampered or truncated N20 model-input SHA-256")
        normalized.append((name, rec, verify_record(rec)))
    source_name, source, initial = normalized[0]
    pairs_differing = []
    for index, left in enumerate(initial):
        right_values = [entry[index] for _, _, entry in normalized[1:]]
        changed = [field for field in ORDERED_STAGES if any(
            left.get(field) != item.get(field) for item in right_values
        )]
        if changed:
            i, fixed_slot = divmod(index, N_FIXED)
            pairs_differing.append({
                "pair_index": index,
                "free_local": i,
                "fixed_local": N_FREE + fixed_slot,
                "free_master_feature": left["free_master_feature"],
                "fixed_master_feature": left["fixed_master_feature"],
                "first_differing_recorded_field": changed[0],
                "all_differing_recorded_fields": changed,
                "values_by_replica": {
                    name: {field: values[index].get(field)
                           for field in changed}
                    for name, _, values in normalized
                },
            })
    original_mode_shas = sorted({scientific_core_sha(rec) for _, rec, _ in normalized})
    return {
        "schema_version": 1,
        "issue": 60,
        "scope": "read_only_free_fixed_pair_trace_in_existing_N20_combinations_loop",
        "baseline": source_name,
        "replays": [
            {
                "file": name,
                "core_scientific_model_sha256_without_new_trace": scientific_core_sha(rec),
                "diagnostic_model_sha256": rec["model_input_sha256"],
                "original_linear_hex": rec["model_input"]["linear_float64_hex"],
                "original_energy": rec["original_energy"],
                "selected_local_positions": rec["selected_local_positions"],
            }
            for name, rec, _ in normalized
        ],
        "distinct_original_scientific_model_hashes": original_mode_shas,
        "pair_count": N_FREE * N_FIXED,
        "different_pair_count": len(pairs_differing),
        "pair_differences": pairs_differing,
        "first_pair_with_recorded_difference": (
            pairs_differing[0] if pairs_differing else None
        ),
        "limitations": [
            "Only selected read-only stages are observed: no claim of a single causal CPU instruction",
            "A diagnostic decay value is a separate np.exp invocation, not the value captured from an objective call",
            "When all hosts agree, this is a negative sample, not proof of universal numerical stability",
            "Historical A/B slack-QUBO and simulated annealing are out of scope here",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    files = sorted(args.inputs_root.rglob("replicate-*.json"))
    if len(files) != 6:
        raise ValueError(f"Expected six raw N20 process results; found {len(files)}")
    data = [(str(p.relative_to(args.inputs_root)),
             json.loads(p.read_text(encoding="utf-8"))) for p in files]
    report = compare(data)
    if args.report.exists():
        raise FileExistsError("Refusing to overwrite read-only trace analysis")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(canonical(report))
    print("N20_FREE_FIXED_PAIR_TRACE " + json.dumps({
        "pairs": report["pair_count"],
        "different_pairs": report["different_pair_count"],
        "distinct_original_model_hashes": len(report["distinct_original_scientific_model_hashes"]),
        "first_differing_pair": (
            None if report["first_pair_with_recorded_difference"] is None else
            {key: report["first_pair_with_recorded_difference"][key] for key in (
                "free_local", "fixed_local", "first_differing_recorded_field",
            )}
        ),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
