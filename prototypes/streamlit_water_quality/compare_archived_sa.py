"""Independent post-run comparison of three GitHub Actions SA ZIP artifacts.

CLI only reads existing archives. It never reruns or changes the scientific
experiment. Run manually after downloading the old A, old B, and controlled
ZIP files. See SA_ULP_CONTROLLED_REPLAY.md for the exact archive URLs.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import zipfile

from evidence import canonical_bytes

ORIGINAL_PENALTY = "notebook-local-row-sum"
REPLAY_A = "A-linear_A-penalty"
REPLAY_B = "B-linear_B-penalty"
COLUMNS = (
    "sample_seed", "full_bits", "selected_local_indices", "feasible",
    "budget_ok", "connectivity_ok", "occurrences",
    "raw_objective", "qubo_augmented_energy", "qubo_energy_without_offset",
)


def checked_zip(path: Path) -> tuple[list[dict], dict]:
    with zipfile.ZipFile(path) as z:
        manifest = json.loads(z.read("manifest.json"))
        if "file_sha256" not in manifest:
            raise ValueError("Archive has no SHA-256 manifest")
        for name, hexdigest in manifest["file_sha256"].items():
            actual = hashlib.sha256(z.read(name)).hexdigest()
            if actual != hexdigest:
                raise ValueError(f"{path.name}: SHA-256 manifest invalid for {name}")
        rows = list(csv.DictReader(io.StringIO(z.read("samples.csv").decode("utf-8"))))
        summary = json.loads(z.read("summary.json"))
    return rows, summary


def keyed(rows: list[dict], label: str) -> dict[tuple[int, int], dict]:
    subset = [r for r in rows if r["penalty"] == label]
    index: dict[tuple[int, int], dict] = {}
    for r in subset:
        key = (int(r["seed"]), int(r["read_index"]))
        if key in index:
            raise AssertionError(f"Duplicated per-parent read in {label}: {key}")
        index[key] = r
    if len(index) != 1024:
        raise AssertionError(f"Expected exactly 1024 one-read rows in {label}")
    if any(int(r["occurrences"]) != 1 for r in subset):
        raise AssertionError("Unexpected non-unit occurrence in single-read replay")
    if len({int(r["sample_seed"]) for r in subset}) != 1024:
        raise AssertionError("Distinct per-read child seeds required")
    return index


def compare(archived_a: Path, archived_b: Path, controlled: Path) -> dict:
    a_rows, a_summary = checked_zip(archived_a)
    b_rows, b_summary = checked_zip(archived_b)
    c_rows, c_summary = checked_zip(controlled)
    a, b = keyed(a_rows, ORIGINAL_PENALTY), keyed(b_rows, ORIGINAL_PENALTY)
    aa = keyed(c_rows, REPLAY_A)
    bb = keyed(c_rows, REPLAY_B)
    arms = {}
    for original, replay, label in ((a, aa, "A"), (b, bb, "B")):
        if set(original) != set(replay):
            raise AssertionError(f"Different parent and read index keys for {label}")
        differences = Counter({
            column: sum(original[k][column] != replay[k][column] for k in original)
            for column in COLUMNS
        })
        if any(differences.values()):
            raise AssertionError(f"Replay {label} differs from original: {dict(differences)}")
        arms[label] = {
            "matching_samples": len(original),
            "identical_reported_fields": list(COLUMNS),
            "archived_feasible_count": sum(r["feasible"] == "True"
                                           for r in original.values()),
            "replayed_feasible_count": sum(r["feasible"] == "True"
                                           for r in replay.values()),
            "exact_full_46_bit_states_match": True,
        }
    if arms["A"]["archived_feasible_count"] != 698 or arms["B"]["archived_feasible_count"] != 665:
        raise AssertionError("Referenced archives do not match logged historical A/B modes")

    def count_changed(x: dict, y: dict, field: str) -> int:
        if set(x) != set(y):
            raise AssertionError("Paired seed manifest changed between controlled arms")
        return sum(x[k][field] != y[k][field] for k in x)

    linear_a = keyed(c_rows, "A-linear_B-penalty")
    penalty_a = keyed(c_rows, "B-linear_A-penalty")
    assert sum(r["feasible"] == "True" for r in linear_a.values()) == 665
    assert sum(r["feasible"] == "True" for r in penalty_a.values()) == 698

    return {
        "schema_version": 1,
        "comparison": "original archived A/B vs controlled same-child-seed 4-arm replay",
        "archived_exact_replays": arms,
        "within_controlled_changes": {
            "linear_only_full_bitstrings_changed": count_changed(bb, linear_a, "full_bits"),
            "penalty_only_full_bitstrings_changed": count_changed(bb, penalty_a, "full_bits"),
            "penalty_only_feasibility_flags_changed": count_changed(bb, penalty_a, "feasible"),
            "combined_vs_baseline_full_bitstrings_changed": count_changed(bb, aa, "full_bits"),
        },
        "source_archive_A_checksum": c_summary["source_archive_A"],
        "source_archive_B_checksum": c_summary["source_archive_B"],
        "scientific_limit": "One pinned classical sampler version and one frozen instance; this does not identify the upstream origin of ULP coefficient variability.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archived-a", type=Path, required=True)
    parser.add_argument("--archived-b", type=Path, required=True)
    parser.add_argument("--controlled", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.archived_a, args.archived_b, args.controlled)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(report))
    print("N20_ARCHIVE_EXACT_REPLAY " + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
