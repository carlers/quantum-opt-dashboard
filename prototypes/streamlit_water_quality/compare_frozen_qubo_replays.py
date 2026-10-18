"""Independently compare every full bitstring from six frozen-QUBO OpenJij runs.

Different outputs are a scientific observation and do not automatically fail CI.
Changed input bytes, seeds, invalid energy/feasibility, or missing reads DO fail.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from evidence import canonical_bytes
from replay_frozen_qubo import (
    ARCHIVED_SOURCE_B_SHA256, EXPECTED_READS,
    FROZEN_FILE, FROZEN_QUBO_SHA256, FROZEN_SHA256, SCIP_REFERENCE,
)

ENERGY_TOLERANCE = 1e-6


def audit_result(payload: dict, frozen: dict) -> dict:
    if payload.get("design") != "issue58_frozen_historical_B_qubo_crosshost_classical_sa":
        raise ValueError("Unexpected frozen-QUBO replay protocol")
    if (payload.get("frozen_fixture_file_sha256") != FROZEN_SHA256
            or payload.get("frozen_qubo_canonical_sha256") != FROZEN_QUBO_SHA256
            or payload.get("source_archived_B_sha256") != ARCHIVED_SOURCE_B_SHA256):
        raise ValueError("Original exact frozen fixture/archived-source digest drift")
    if payload.get("n_samples") != EXPECTED_READS:
        raise ValueError("Sampler output does not contain 1024 read-level results")
    if payload["environment"].get("openjij") != "0.12.2" or (
        payload["environment"].get("numpy") != "2.5.4"
    ):
        raise ValueError("OpenJij or numpy version differs from pinned protocol")
    samples = payload["full_samples"]
    if len(samples) != EXPECTED_READS:
        raise ValueError("Missing, extra or compressed returned samples")
    state_manifest = []
    model = frozen["source_model"]
    linear = [float.fromhex(s) for s in model["linear_float64_hex"]]
    quadratic = [(i, j, float.fromhex(q))
                 for i, j, q in model["quadratic_float64_hex"]]
    neighbors = model["neighbors"]
    fixed = model["fixed_neighbor"]
    qubo = frozen["qubo"]
    terms = [(i, j, float.fromhex(q))
             for i, j, q in qubo["coefficient_terms_float64_hex"]]
    offset = float.fromhex(qubo["offset_float64_hex"])
    pb = float.fromhex(qubo["budget_penalty_float64_hex"])
    pc = float.fromhex(qubo["connectivity_penalty_float64_hex"])
    assert pc == pb
    feasible = hits = 0
    for index, row in enumerate(samples):
        parent_index, read_index = divmod(index, 32)
        parent = frozen["seed_protocol"]["parent_seeds"][parent_index]
        child = frozen["seed_protocol"]["child_seeds_uint32"][parent_index][read_index]
        if (row.get("seed"), row.get("read_index"), row.get("sample_seed")) != (
            parent, read_index, child
        ):
            raise ValueError(f"Read {index} mismatches the frozen child-seed ordering")
        if row.get("occurrences") != 1:
            raise ValueError(f"Missing/merged OpenJij response read {index}")
        bitstr = row["full_bits"]
        if not isinstance(bitstr, str) or len(bitstr) != 46 or any(
            bit not in "01" for bit in bitstr
        ):
            raise ValueError(f"Invalid full 46-bit sampler state at read {index}")
        bits = [int(c) for c in bitstr]
        x = bits[:20]
        selected = [i for i, v in enumerate(x) if v]
        isolated = [
            i for i in selected
            if not (fixed[i] or any(x[j] for j in neighbors[i]))
        ]
        raw_original = sum(a * x[i] for i, a in enumerate(linear)) + sum(
            q * x[i] * x[j] for i, j, q in quadratic
        )
        budget_ok = len(selected) == 5
        onehop_ok = not isolated
        original_feasible = budget_ok and onehop_ok
        optimum = original_feasible and abs(raw_original - SCIP_REFERENCE) <= 1e-7
        direct_energy = raw_original + pb * (sum(x) - 5) ** 2
        for i, (group, magnitudes) in enumerate(zip(
            qubo["slack_variables"], qubo["slack_weights"]
        )):
            slack = sum(bits[var] * weight for var, weight in zip(group, magnitudes))
            residual = fixed[i] + sum(x[j] for j in neighbors[i]) - x[i] - slack
            direct_energy += pc * residual**2
        expanded_energy = offset + sum(
            q * bits[i] * bits[j] for i, j, q in terms
        )
        if not math.isclose(direct_energy, expanded_energy, abs_tol=ENERGY_TOLERANCE,
                            rel_tol=1e-9):
            raise ValueError(f"Read {index}: expanded vs direct squared QUBO mismatch")
        original_fields = {
            "budget_ok": budget_ok,
            "connectivity_ok": onehop_ok,
            "feasible": original_feasible,
            "optimum_hit": optimum,
            "selected_count": len(selected),
            "isolated_selected_count": len(isolated),
        }
        if any(row.get(k) != v for k, v in original_fields.items()):
            raise ValueError(f"Read {index}: source feasibility fields do not match")
        if json.loads(row["selected_local_indices"]) != selected:
            raise ValueError(f"Read {index}: selected index list wrong")
        for key, expected in (
            ("raw_objective", raw_original),
            ("qubo_augmented_energy", expanded_energy),
            ("qubo_energy_without_offset", expanded_energy - offset),
        ):
            if not math.isclose(float(row[key]), expected, rel_tol=1e-9,
                                abs_tol=ENERGY_TOLERANCE):
                raise ValueError(f"Read {index}: {key} disagrees with independent audit")
        feasible += int(original_feasible)
        hits += int(optimum)
        state_manifest.append({
            "parent_seed": parent, "read_index": read_index,
            "child_seed": child, "full_bits": bitstr,
        })
    if payload["feasible_count"] != feasible or payload["optimum_hit_count"] != hits:
        raise ValueError("Count totals disagree with audited individual states")
    if hashlib.sha256(canonical_bytes(samples)).hexdigest() != payload[
        "full_samples_sha256"
    ]:
        raise ValueError("Full sample/metadata digest mismatch")
    if hashlib.sha256(canonical_bytes(state_manifest)).hexdigest() != payload[
        "ordered_full_state_sha256"
    ]:
        raise ValueError("Ordered full-state digest mismatch")
    return {
        "replica": payload["replica"],
        "sha256": payload["ordered_full_state_sha256"],
        "feasible": feasible,
        "optimal": hits,
        "environment": payload["environment"],
        "states": [row["full_bits"] for row in samples],
        "flags": [bool(row["feasible"]) for row in samples],
    }


def compare_validated(records: list[dict]) -> dict:
    if len(records) != 6:
        raise ValueError("Exactly 3 hosts × 2 independently seeded processes required")
    ordered = sorted(records, key=lambda r: r["replica"])
    expected = [f"r{host}-{proc}" for host in range(1, 4) for proc in ("a", "b")]
    if [r["replica"] for r in ordered] != expected:
        raise ValueError("Missing or duplicate replica names")
    reference = ordered[0]
    observations = []
    for rec in ordered:
        diff = [
            i for i, (a, b) in enumerate(zip(reference["states"], rec["states"]))
            if a != b
        ]
        flags = [
            i for i, (a, b) in enumerate(zip(reference["flags"], rec["flags"]))
            if a != b
        ]
        if len(rec["states"]) != EXPECTED_READS or len(rec["flags"]) != EXPECTED_READS:
            raise ValueError("Truncated sample list cannot be compared")
        observations.append({
            "replica": rec["replica"],
            "state_sha256": rec["sha256"],
            "full_bitstring_mismatch_count_vs_r1a": len(diff),
            "full_bitstring_mismatch_indices_vs_r1a": diff,
            "original_feasibility_flip_count_vs_r1a": len(flags),
            "original_feasibility_flip_indices_vs_r1a": flags,
            "original_feasible_draws": rec["feasible"],
            "exact_optimum_hits": rec["optimal"],
            "environment": rec["environment"],
        })
    versions = [
        (r["environment"]["numpy"], r["environment"]["openjij"])
        for r in ordered
    ]
    if len(set(versions)) != 1:
        raise ValueError("Cannot compare unpinned sampler dependencies")
    distinct = sorted(set(r["sha256"] for r in ordered))
    return {
        "schema_version": 1,
        "issue": 58,
        "design": "exact_frozen_historical_B_qubo_six_fresh_processes",
        "frozen_fixture_file_sha256": FROZEN_SHA256,
        "frozen_qubo_canonical_sha256": FROZEN_QUBO_SHA256,
        "frozen_read_seeds": 1024,
        "observed_processes": 6,
        "distinct_ordered_state_hashes": distinct,
        "all_six_observed_processes_bitwise_equal": len(distinct) == 1,
        "observations": observations,
        "important_limits": [
            "OpenJij is classical simulated annealing, not a QPU",
            "Identical observed results do not prove universal cross-host determinism",
            "Different observed full states on identical coefficients suggest a runtime/"
            "sampler reproducibility question, not an automatic CPU-causality claim",
            "Old 665/698 counts belong to historical A/B penalty-ULP comparison, "
            "not newly calibrated benchmarks",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    frozen_path = FROZEN_FILE
    raw = frozen_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_SHA256:
        raise ValueError("Frozen fixture source bytes changed")
    frozen = json.loads(raw)
    entries = sorted(args.input_dir.rglob("frozen-samples-r*-*.json"))
    if len(entries) != 6:
        raise ValueError(f"Expected six independent sampler records; found {len(entries)}")
    validated = []
    for file in entries:
        data = json.loads(file.read_text(encoding="utf-8"))
        result = audit_result(data, frozen)
        if file.name != f"frozen-samples-{result['replica']}.json":
            raise ValueError("Samplers mislabeled a replica's source artifact")
        validated.append(result)
    report = compare_validated(validated)
    if args.report.exists():
        raise FileExistsError("Will not replace existing cross-host comparison")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(canonical_bytes(report))
    print("FROZEN_OPENJIJ_CROSSHOST " + json.dumps({
        "replicas": report["observed_processes"],
        "distinct_state_hashes": len(report["distinct_ordered_state_hashes"]),
        "all_equal": report["all_six_observed_processes_bitwise_equal"],
        "feasible": [x["original_feasible_draws"] for x in report["observations"]],
        "optimum_hits": [x["exact_optimum_hits"] for x in report["observations"]],
        "cpu": [x["environment"]["cpu_model"] for x in report["observations"]],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
