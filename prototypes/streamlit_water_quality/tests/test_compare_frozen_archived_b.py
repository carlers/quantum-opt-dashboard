"""Ensure archived B comparison neither drops reads nor conceals drift."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest

from compare_frozen_archived_b import FIELDS, compare_rows


def archive_and_replay():
    old, replay = {}, []
    for parent in range(270010001, 270010033):
        for read_index in range(32):
            key = (parent, read_index)
            base = {
                "seed": str(parent), "read_index": str(read_index),
                "full_bits": "0" * 46, "selected_local_indices": "[]",
                "selected_count": "0", "isolated_selected_count": "0",
                "budget_ok": "False", "connectivity_ok": "True",
                "feasible": "False", "raw_objective": "0.0",
                "qubo_augmented_energy": "41.0",
                "qubo_energy_without_offset": "0.0",
                "sample_seed": str(parent + read_index),
                "occurrences": "1",
            }
            old[key] = base
            replay.append({
                name: int(base[name]) if name in (
                    "selected_count", "isolated_selected_count", "sample_seed",
                    "occurrences",
                ) else (
                    base[name] == "True" if name in (
                        "budget_ok", "connectivity_ok", "feasible",
                    ) else float(base[name]) if name in (
                        "raw_objective", "qubo_augmented_energy",
                        "qubo_energy_without_offset",
                    ) else base[name]
                )
                for name in FIELDS
            } | {"seed": parent, "read_index": read_index})
    return old, replay


def test_all_1024_identical_seeded_fields_are_recognized():
    original, new = archive_and_replay()
    report = compare_rows(original, new)
    assert report["compared"] == 1024
    assert report["all_12_audited_fields_exact"]
    assert all(v == 0 for v in report["mismatch_counts"].values())


def test_one_changed_46_bit_state_is_not_hidden():
    original, new = archive_and_replay()
    new[1]["full_bits"] = "1" + "0" * 45
    report = compare_rows(original, new)
    assert not report["all_12_audited_fields_exact"]
    assert report["mismatch_counts"]["full_bits"] == 1
    assert report["mismatches"]["full_bits"][0]["read_index"] == 1


def test_changed_sample_seed_is_reported_even_if_state_same():
    original, new = archive_and_replay()
    new[1]["sample_seed"] += 1
    report = compare_rows(original, new)
    assert report["mismatch_counts"]["sample_seed"] == 1


def test_duplicate_key_or_missing_read_is_rejected():
    original, new = archive_and_replay()
    new[1] = deepcopy(new[0])
    with pytest.raises(ValueError, match="duplicate"):
        compare_rows(original, new)


def test_short_archives_are_not_treated_as_zero_mismatches():
    original, new = archive_and_replay()
    with pytest.raises(ValueError, match="1024"):
        compare_rows(original, new[:-1])
