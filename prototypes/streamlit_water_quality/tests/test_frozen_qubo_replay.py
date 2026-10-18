"""Tests that corrupted frozen science cannot pass and differences are observable."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from evidence import canonical_bytes
from qubo import best_slack_assignment, energy
from replay_frozen_qubo import FROZEN_FILE, FROZEN_SHA256, read_frozen
from compare_frozen_qubo_replays import audit_result, compare_validated


def test_frozen_mode_b_is_byte_pinned_and_independently_feasible():
    raw = FROZEN_FILE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FROZEN_SHA256
    fixture, model, qubo = read_frozen()
    assert fixture["historical_archive_mode"] == "B"
    assert qubo.n_variables == 46 and len(qubo.coefficients) == 323
    assert len(model.fixed_indices) == 15
    bits = best_slack_assignment(model, qubo, [
        int(i in {0, 1, 3, 6, 7}) for i in range(20)
    ])
    assert abs(energy(qubo, bits) + 3.3012934918564643) < 1e-7


def test_tampered_input_bytes_are_rejected_before_any_sampler_calls(tmp_path):
    mutated = FROZEN_FILE.read_bytes().replace(
        b'"historical_archive_mode":"B"', b'"historical_archive_mode":"A"', 1
    )
    assert mutated != FROZEN_FILE.read_bytes()
    path = tmp_path / "mutated.json"
    path.write_bytes(mutated)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        read_frozen(path)


def synthetic_good_result() -> tuple[dict, dict]:
    frozen, model, qubo = read_frozen()
    selected = {0, 1, 3, 6, 7}
    bits = best_slack_assignment(model, qubo, [
        int(i in selected) for i in range(20)
    ])
    state = "".join(str(bit) for bit in bits)
    expanded = energy(qubo, bits)
    raw = float(sum(float(model.linear[i]) for i in selected)
                + sum(q for i, j, q in model.quadratic
                      if i in selected and j in selected))
    records = []
    for parent, seeds in zip(
        frozen["seed_protocol"]["parent_seeds"],
        frozen["seed_protocol"]["child_seeds_uint32"],
    ):
        for read_index, seed in enumerate(seeds):
            records.append({
                "seed": parent, "sample_seed": seed, "read_index": read_index,
                "occurrences": 1, "full_bits": state,
                "selected_local_indices": "[0,1,3,6,7]",
                "selected_count": 5, "isolated_selected_count": 0,
                "budget_ok": True, "connectivity_ok": True, "feasible": True,
                "optimum_hit": True, "raw_objective": raw,
                "qubo_augmented_energy": expanded,
                "qubo_energy_without_offset": expanded - qubo.offset,
            })
    meta = [{
        "parent_seed": row["seed"], "child_seed": row["sample_seed"],
        "read_index": row["read_index"], "full_bits": row["full_bits"],
    } for row in records]
    result = {
        "schema_version": 1,
        "design": "issue58_frozen_historical_B_qubo_crosshost_classical_sa",
        "replica": "r1-a",
        "frozen_fixture_file_sha256": FROZEN_SHA256,
        "frozen_qubo_canonical_sha256": frozen["qubo_canonical_sha256"],
        "source_archived_B_sha256": frozen["archived_original_instance_json_sha256"],
        "environment": {"openjij": "0.12.2", "numpy": "2.5.4"},
        "n_samples": 1024, "feasible_count": 1024, "optimum_hit_count": 1024,
        "ordered_full_state_sha256": hashlib.sha256(canonical_bytes(meta)).hexdigest(),
        "full_samples_sha256": hashlib.sha256(canonical_bytes(records)).hexdigest(),
        "full_samples": records,
    }
    return frozen, result


def test_full_1024_read_independent_audit_validates_original_feasibility():
    frozen, result = synthetic_good_result()
    summary = audit_result(result, frozen)
    assert summary["feasible"] == 1024
    assert summary["optimal"] == 1024


def test_seed_reordering_invalidates_sampler_evidence():
    frozen, result = synthetic_good_result()
    result["full_samples"][0]["sample_seed"] += 1
    with pytest.raises(ValueError, match="frozen child-seed ordering"):
        audit_result(result, frozen)


def test_frozen_qubo_energy_corruption_is_detected():
    frozen, result = synthetic_good_result()
    result["full_samples"][0]["qubo_augmented_energy"] += 1
    with pytest.raises(ValueError, match="qubo_augmented_energy"):
        audit_result(result, frozen)


def test_comparator_reports_mismatched_bits_and_changed_original_feasibility():
    template = {
        "sha256": "a", "feasible": 665, "optimal": 13,
        "states": ["0" * 46] * 1024,
        "flags": [False] * 1024,
        "environment": {"numpy": "2.5.4", "openjij": "0.12.2"},
    }
    records = []
    for h in range(1, 4):
        for p in ("a", "b"):
            record = deepcopy(template)
            record["replica"] = f"r{h}-{p}"
            records.append(record)
    records[4]["states"][0] = "1" + "0" * 45
    records[4]["flags"][0] = True
    records[4]["sha256"] = "b"
    report = compare_validated(records)
    assert not report["all_six_observed_processes_bitwise_equal"]
    assert len(report["distinct_ordered_state_hashes"]) == 2
    assert report["observations"][4]["full_bitstring_mismatch_indices_vs_r1a"] == [0]
    assert report["observations"][4]["original_feasibility_flip_count_vs_r1a"] == 1


def test_comparator_rejects_missing_host_or_replica():
    template = {
        "replica": "r1-a", "sha256": "x", "feasible": 1, "optimal": 0,
        "states": ["0" * 46] * 1024, "flags": [False] * 1024,
        "environment": {"numpy": "2.5.4", "openjij": "0.12.2"},
    }
    with pytest.raises(ValueError, match="Exactly 3 hosts"):
        compare_validated([template])
