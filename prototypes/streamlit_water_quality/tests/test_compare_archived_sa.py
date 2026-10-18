"""Synthetic ZIP contract checks for independent historical artifact comparator."""
import csv
import hashlib
from io import StringIO
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compare_archived_sa import COLUMNS, compare


def source_rows(feasible: int, *, a: bool):
    records = []
    for slot in range(1024):
        parent = 270010001 + slot // 32
        child = slot % 32
        records.append({
            "penalty": "notebook-local-row-sum", "seed": str(parent),
            "read_index": str(child), "sample_seed": str(slot + 1),
            "full_bits": "1" * 46 if a and slot < 882 else "0" * 46,
            "selected_local_indices": "[0,1,3,6,7]" if a and slot < 882 else "[]",
            "feasible": "True" if slot < feasible else "False",
            "budget_ok": "True" if slot < feasible else "False",
            "connectivity_ok": "True" if slot < feasible else "False",
            "occurrences": "1", "raw_objective": "-3.0",
            "qubo_augmented_energy": "1.0",
            "qubo_energy_without_offset": "0.0",
        })
    return records


def archive(path: Path, rows: list[dict], *, controlled=False):
    strings = StringIO()
    writer = csv.DictWriter(strings, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    entries = {
        "samples.csv": strings.getvalue().encode(),
        "summary.json": json.dumps(
            {"source_archive_A": "A-checksum",
             "source_archive_B": "B-checksum"} if controlled else {}
        ).encode(),
    }
    entries["manifest.json"] = json.dumps(
        {"file_sha256": {
            name: hashlib.sha256(value).hexdigest()
            for name, value in entries.items()
        }}
    ).encode()
    with ZipFile(path, "w") as zipf:
        for name, value in entries.items():
            zipf.writestr(name, value)


def fixture_zips(tmp_path: Path):
    a, b = source_rows(698, a=True), source_rows(665, a=False)
    ca = [dict(r, penalty="A-linear_A-penalty") for r in a]
    cb = [dict(r, penalty="B-linear_B-penalty") for r in b]
    ab = [dict(r, penalty="A-linear_B-penalty") for r in b]
    ba = [dict(r, penalty="B-linear_A-penalty") for r in a]
    paths = tuple(tmp_path / p for p in ("a.zip", "b.zip", "controlled.zip"))
    archive(paths[0], a)
    archive(paths[1], b)
    archive(paths[2], ca + cb + ab + ba, controlled=True)
    return paths


def test_archive_comparison_replays_bitstrings_and_respects_one_read_per_seed(tmp_path):
    paths = fixture_zips(tmp_path)
    report = compare(*paths)
    assert report["archived_exact_replays"]["A"]["matching_samples"] == 1024
    assert report["archived_exact_replays"]["B"]["matching_samples"] == 1024
    assert report["archived_exact_replays"]["A"]["archived_feasible_count"] == 698
    assert report["archived_exact_replays"]["B"]["archived_feasible_count"] == 665
    assert report["within_controlled_changes"]["linear_only_full_bitstrings_changed"] == 0
    assert report["within_controlled_changes"]["penalty_only_full_bitstrings_changed"] == 882
    assert report["within_controlled_changes"]["penalty_only_feasibility_flags_changed"] == 33
    assert set(COLUMNS) >= {"full_bits", "raw_objective", "qubo_augmented_energy"}


def test_archive_comparison_rejects_modified_manifest_or_sample(tmp_path):
    paths = fixture_zips(tmp_path)
    corrupted = tmp_path / "bad.zip"
    with ZipFile(paths[0]) as z:
        archive_contents = {name: z.read(name) for name in z.namelist()}
    archive_contents["samples.csv"] = archive_contents["samples.csv"] + b"\n"
    with ZipFile(corrupted, "w") as z:
        for name, content in archive_contents.items():
            z.writestr(name, content)
    with pytest.raises(ValueError, match="SHA-256"):
        compare(corrupted, paths[1], paths[2])
