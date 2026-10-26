"""Regression: compare whole frozen N20 SA runs without mistaking replay as replication."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import csv
import io
import json
from pathlib import Path

import pytest

from problems.water_quality.bitwise_penalty_replay import (
    PROFILE, SOURCE, SCHEMA, compare_directories, read_directory,
)
from problems.water_quality.independent_penalty_grid import FROZEN_PROFILE_PATH


def write_study(folder: Path, *, duration: float = .1, mutate=None):
    folder.mkdir()
    model = FROZEN_PROFILE_PATH.read_bytes()
    assert sha256(model).hexdigest() == PROFILE
    parents = [270010001, 270010002]
    fields = (
        "parent_seed", "grid_index", "read_index", "child_seed",
        "original_decisions", "full_slack_quo_bits",
        "qubo_coefficient_sha256", "original_feasible",
    )
    rows = [
        {
            "parent_seed": str(parent), "grid_index": str(g),
            "read_index": str(j), "child_seed": str(parent * 1000 + g * 10 + j),
            "original_decisions": "0" * 20,
            "full_slack_quo_bits": "0" * 25,
            "qubo_coefficient_sha256": sha256(str(g).encode()).hexdigest(),
            "original_feasible": "False",
        }
        for g in range(9) for parent in parents for j in range(4)
    ]
    trials = [
        {"parent_seed": str(parent), "grid_index": str(g),
         "reads": "4", "feasible_reads": "0",
         "sampler_wall_seconds": str(duration)}
        for g in range(9) for parent in parents
    ]
    summary = {
        "schema": SCHEMA, "source_sha256": SOURCE, "N_free": 20,
        "K": 5, "fixed_station_count": 15,
        "nonquantum_classical_only": True,
        "inference_or_optimal_penalty_grid_claimed": False,
        "grid_shape": [3, 3], "independent_axes": [
            "lambda_budget", "lambda_connectivity"
        ], "original_model_sha256": PROFILE,
        "numerical_profile_sha256": PROFILE,
        "parent_seeds": parents, "reads_per_parent_per_cell": 4,
        "sampled_source_states": len(rows), "parent_cell_trials": len(trials),
        "numerical_thread_environment": {
            "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        },
        "software": {"github_sha": "run-one"},
    }
    if mutate:
        mutate(summary, rows, trials)
    data = {
        "compiled_source_model.json": model,
        "summary.json": json.dumps(summary, sort_keys=True).encode(),
    }
    for name, content in (("samples.csv", rows), ("trials.csv", trials)):
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(content[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(content)
        data[name] = buffer.getvalue().encode()
    hashes = {n: sha256(v).hexdigest() for n, v in data.items()}
    data["SHA256SUMS.json"] = json.dumps({
        "schema": SCHEMA, "source_sha256": SOURCE,
        "file_sha256": hashes,
    }).encode()
    for name, raw in data.items():
        (folder / name).write_bytes(raw)
    return folder


def test_two_bitwise_identical_replays_allow_different_walltimes_and_github_commit(tmp_path):
    a = write_study(tmp_path / "a", duration=.1)
    b = write_study(tmp_path / "b", duration=.4)
    summary = json.loads((b / "summary.json").read_text())
    summary["software"]["github_sha"] = "run-two"
    data = json.dumps(summary, sort_keys=True).encode()
    (b / "summary.json").write_bytes(data)
    sums = json.loads((b / "SHA256SUMS.json").read_text())
    sums["file_sha256"]["summary.json"] = sha256(data).hexdigest()
    (b / "SHA256SUMS.json").write_text(json.dumps(sums))
    receipt = compare_directories(a, b)
    assert receipt["sample_count_per_execution"] == 72
    assert receipt["sample_source_CSV_sha256"] == sha256((a / "samples.csv").read_bytes()).hexdigest()
    assert receipt["all_full_original_and_slack_bits_identical"]
    assert receipt["executions_are_replays_not_independent_parent_block_samples"]
    assert receipt["observed_feasible_counts_by_grid"] == [0] * 9
    assert not receipt["winner_or_statistical_inference_permitted"]


def test_changed_original_bits_rejected_even_with_new_checksums(tmp_path):
    a = write_study(tmp_path / "a")
    def change(summary, rows, trials):
        rows[0]["original_decisions"] = "1" + "0" * 19
        rows[0]["full_slack_quo_bits"] = "1" + "0" * 24
    b = write_study(tmp_path / "b", mutate=change)
    with pytest.raises(ValueError, match="NOT bitwise identical"):
        compare_directories(a, b)


def test_changed_unlogged_sampler_parameter_rejected(tmp_path):
    a = write_study(tmp_path / "a")
    def change(summary, rows, trials):
        summary["sweeps_per_read"] = 200
    b = write_study(tmp_path / "b", mutate=change)
    with pytest.raises(ValueError, match="protocol"):
        compare_directories(a, b)


def test_incomplete_or_repeated_one_read_index_fails_even_with_rehashed_files(tmp_path):
    def mutate(summary, rows, trials):
        rows[0]["read_index"] = rows[1]["read_index"]
    path = write_study(tmp_path / "a", mutate=mutate)
    with pytest.raises(ValueError, match="duplicate|missing"):
        read_directory(path)


def test_changed_model_status_scope_rejected(tmp_path):
    def mutate(summary, rows, trials):
        summary["nonquantum_classical_only"] = False
    path = write_study(tmp_path / "a", mutate=mutate)
    with pytest.raises(ValueError, match="scientific scope"):
        read_directory(path)


def test_mismatched_sha256_manifest_rejected(tmp_path):
    path = write_study(tmp_path / "a")
    with (path / "samples.csv").open("ab") as dest:
        dest.write(b"forged")
    with pytest.raises(ValueError, match="SHA256"):
        read_directory(path)


def test_changed_N20_frozen_input_or_openblas_threads_rejected(tmp_path):
    def mutate(summary, rows, trials):
        summary["numerical_thread_environment"]["OPENBLAS_NUM_THREADS"] = "16"
    path = write_study(tmp_path / "a", mutate=mutate)
    with pytest.raises(ValueError, match="thread"):
        read_directory(path)
