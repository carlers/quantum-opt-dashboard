"""Read-only, SHA-checked archive comparison: historical B vs frozen QUBO replays.

No GitHub token, network access, or experiment rerun is needed: download the
original and new workflow artifact ZIPs, then compare all original-mode-B
1024 read-level outcomes. Does not modify either historical archive.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

from evidence import canonical_bytes

REFERENCE_MODE = "notebook-local-row-sum"
EXPECTED_OLD_COUNT = 1024
FIELDS = (
    "full_bits", "selected_local_indices", "selected_count",
    "isolated_selected_count", "budget_ok", "connectivity_ok", "feasible",
    "raw_objective", "qubo_augmented_energy", "qubo_energy_without_offset",
    "sample_seed", "occurrences",
)


def original_csv_from_zip(path: Path) -> tuple[dict, dict[tuple[int, int], dict]]:
    with ZipFile(path) as z:
        filenames = set(z.namelist())
        if not {"manifest.json", "protocol.json", "samples.csv", "summary.json"} <= filenames:
            raise ValueError("Not an original issue #22 archive")
        manifest = json.loads(z.read("manifest.json"))
        for filename, expected in manifest["file_sha256"].items():
            if filename not in filenames or hashlib.sha256(z.read(filename)).hexdigest() != expected:
                raise ValueError(f"Historical archive checksum mismatch: {filename}")
        protocol = json.loads(z.read("protocol.json"))
        summary = json.loads(z.read("summary.json"))
        if protocol.get("design") != "preregistered_paired_seed_classical_sa_n20":
            raise ValueError("Wrong original paired-seed scientific protocol")
        if (protocol.get("parent_seeds") != list(range(270010001, 270010033))
                or protocol.get("reads_per_parent_per_penalty") != 32
                or protocol.get("sweeps_per_call") != 300):
            raise ValueError("Historical read-seed schedule changed")
        if float(protocol["penalty_points"][REFERENCE_MODE]).hex() != (
            "0x1.190ab5b15d1b3p+0"
        ):
            raise ValueError("Historical archive does not have frozen B row-sum penalty")
        raw_rows = list(csv.DictReader(io.StringIO(z.read("samples.csv").decode())))
    relevant = [r for r in raw_rows if r["penalty"] == REFERENCE_MODE]
    if len(raw_rows) != 3072 or len(relevant) != EXPECTED_OLD_COUNT:
        raise ValueError("Expected complete historical 3072 trials and 1024 B-mode reads")
    original = {}
    for row in relevant:
        key = (int(row["seed"]), int(row["read_index"]))
        if key in original or not 0 <= key[1] < 32 or key[0] not in protocol["parent_seeds"]:
            raise ValueError("Duplicate or wrong original read key")
        original[key] = row
    if (int(summary["aggregate"][REFERENCE_MODE]["feasible_draws"]) != 665
            or int(summary["aggregate"][REFERENCE_MODE]["exact_optimum_hits"]) != 13):
        raise ValueError("Original B observation does not match the archived scientific result")
    return protocol, original


def compare_rows(old: dict[tuple[int, int], dict], new_rows: list[dict]) -> dict:
    if len(old) != EXPECTED_OLD_COUNT or len(new_rows) != EXPECTED_OLD_COUNT:
        raise ValueError("Expected all 1024 child-seeded reads in both records")
    visited = set()
    mismatch = {field: [] for field in FIELDS}
    for record in new_rows:
        key = (int(record["seed"]), int(record["read_index"]))
        if key not in old or key in visited:
            raise ValueError("Unrecognized or duplicate new parent/read key")
        visited.add(key)
        historic = old[key]
        for field in FIELDS:
            left, right = historic[field], str(record[field])
            if left != right:
                mismatch[field].append({
                    "parent_seed": key[0], "read_index": key[1],
                    "archived": left, "frozen_replay": right,
                })
    if visited != set(old):
        raise ValueError("New archive omitted original child seed/read combinations")
    return {
        "compared": EXPECTED_OLD_COUNT,
        "mismatch_counts": {field: len(rows) for field, rows in mismatch.items()},
        "mismatches": {field: rows for field, rows in mismatch.items() if rows},
        "all_12_audited_fields_exact": all(not rows for rows in mismatch.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical", required=True, type=Path)
    parser.add_argument("--replay", required=True, type=Path, action="append")
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    protocol, old = original_csv_from_zip(args.historical)
    output = []
    for zip_path in args.replay:
        with ZipFile(zip_path) as z:
            names = sorted(n for n in z.namelist() if n.startswith("frozen-samples-")
                           and n.endswith(".json"))
            if not names:
                raise ValueError(f"No replay JSON records in {zip_path}")
            for name in names:
                data = json.loads(z.read(name))
                if data.get("frozen_fixture_file_sha256") != (
                    "51d47e9a6ad320784019f02110e6543abee60da92453bc26e5c39b91e52398cb"
                ):
                    raise ValueError("Unexpected new replay fixture provenance")
                report = compare_rows(old, data["full_samples"])
                output.append({
                    "zip_name": zip_path.name,
                    "entry": name,
                    "replica": data["replica"],
                    **report,
                })
    if len({p["replica"] for p in output}) != len(output):
        raise ValueError("Duplicate replay identity across ZIPs")
    result = {
        "schema_version": 1,
        "purpose": "archived_B_1024_full_binary_reads_vs_frozen_new_replay",
        "archived_mode": "B",
        "archived_row_sum_penalty_float_hex": float(
            protocol["penalty_points"][REFERENCE_MODE]
        ).hex(),
        "historical_archive_sha256": hashlib.sha256(args.historical.read_bytes()).hexdigest(),
        "replicas": output,
        "all_observed_replays_match_historical_b": all(
            p["all_12_audited_fields_exact"] for p in output
        ),
        "limits": (
            "Bitwise equality for downloaded archived evidence only; "
            "not a universal OpenJij reproducibility theorem or paper parity."
        ),
    }
    if args.report.exists():
        raise FileExistsError("Refusing to overwrite historical comparison")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(canonical_bytes(result))
    print("FROZEN_B_ARCHIVED_COMPARISON " + json.dumps({
        "new_replays_checked": len(output),
        "archived_B_reads_per_replica": EXPECTED_OLD_COUNT,
        "all_12_fields_exact": result["all_observed_replays_match_historical_b"],
        "changed_records": [r["mismatch_counts"] for r in output],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
