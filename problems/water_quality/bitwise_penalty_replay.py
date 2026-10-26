"""Fail-closed, bytewise two-run replay comparison for frozen N20 classical SA.

No OpenJij runs here. This compares complete already generated M2 study
directories (e.g. two bounded CI smoke executions) and differentiates
stochastic seed replay from independent scientific replication.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
from pathlib import Path

SCHEMA = "two-independent-penalty-N20-classical-SA-smoke-v1"
SOURCE = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
FILES = ("summary.json", "compiled_source_model.json", "trials.csv",
         "samples.csv", "SHA256SUMS.json")
PROFILE = "add84856f0f933eecd4a82b615c239430a85e524d7f00d796c4753f7b4ba4101"


def fail(message: str) -> None:
    raise ValueError("Frozen classical N20 seed-replay gate: " + message)


def canonical(value):
    return (json.dumps(value, separators=(",", ":"), sort_keys=True,
                       allow_nan=False) + "\n").encode("utf-8")


def read_directory(path: Path):
    if not path.is_dir():
        fail("missing research directory: " + str(path))
    raw = {}
    for name in FILES:
        file = path / name
        if not file.is_file() or file.stat().st_size > 2_000_000:
            fail("missing or oversized original evidence member: " + name)
        raw[name] = file.read_bytes()
    manifest = json.loads(raw["SHA256SUMS.json"])
    if manifest.get("schema") != SCHEMA or manifest.get("source_sha256") != SOURCE:
        fail("manifest model or source schema does not match original research")
    actual = {name: sha256(raw[name]).hexdigest()
              for name in FILES if name != "SHA256SUMS.json"}
    if actual != manifest.get("file_sha256"):
        fail("per-file SHA256 manifest disagrees with source observations")
    summary = json.loads(raw["summary.json"])
    model = json.loads(raw["compiled_source_model.json"])
    if (summary.get("schema") != SCHEMA
            or summary.get("source_sha256") != SOURCE
            or summary.get("N_free") != 20 or summary.get("K") != 5
            or summary.get("fixed_station_count") != 15
            or summary.get("nonquantum_classical_only") is not True
            or summary.get("inference_or_optimal_penalty_grid_claimed") is not False
            or summary.get("grid_shape") != [3, 3]
            or summary.get("independent_axes") != [
                "lambda_budget", "lambda_connectivity"
            ]):
        fail("wrong scientific scope or an unsupported quantum/ranking claim")
    if (summary.get("original_model_sha256") != PROFILE
            or summary.get("numerical_profile_sha256") != PROFILE
            or actual["compiled_source_model.json"] != PROFILE):
        fail("original frozen-profile model bytes changed")
    if model.get("source") != SOURCE or model.get("N_free") != 20 or model.get("K") != 5:
        fail("recorded source/model dimensions changed")
    threads = summary.get("numerical_thread_environment")
    if not isinstance(threads, dict) or any(
        threads.get(x) != "1" for x in (
            "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"
        )
    ):
        fail("numerical thread isolation differs from frozen replay protocol")
    samples = list(csv.DictReader(io.StringIO(raw["samples.csv"].decode("utf-8"))))
    trials = list(csv.DictReader(io.StringIO(raw["trials.csv"].decode("utf-8"))))
    parents = summary["parent_seeds"]
    reads = summary["reads_per_parent_per_cell"]
    if (not isinstance(parents, list)
            or not (1 <= len(parents) <= 8)
            or len(set(parents)) != len(parents)
            or type(reads) is not int or not (1 <= reads <= 32)):
        fail("invalid parent-seed block protocol")
    needed = 9 * len(parents) * reads
    if (len(samples) != needed or len(trials) != 9 * len(parents)
            or summary.get("sampled_source_states") != needed
            or summary.get("parent_cell_trials") != len(trials)):
        fail("source observations / parent-trial counts are incomplete")
    sample_keys = set()
    child_seeds = set()
    grid_hashes = {str(i): set() for i in range(9)}
    for row in samples:
        key = (row["parent_seed"], row["grid_index"], row["read_index"])
        if (key in sample_keys or row["parent_seed"] not in {str(v) for v in parents}
                or row["grid_index"] not in grid_hashes
                or not 0 <= int(row["read_index"]) < reads):
            fail("missing, duplicate or unknown parent-grid-read identity")
        sample_keys.add(key)
        child = row["child_seed"]
        if child in child_seeds:
            fail("reused one-read child seed")
        child_seeds.add(child)
        grid_hashes[row["grid_index"]].add(row["qubo_coefficient_sha256"])
        if (len(row["original_decisions"]) != 20 or
                any(v not in "01" for v in row["original_decisions"]) or
                not row["full_slack_quo_bits"].startswith(row["original_decisions"])):
            fail("corrupted original/auxiliary bits in sample archive")
        if row["original_feasible"] not in ("True", "False"):
            fail("malformed source feasibility record")
    for parent in parents:
        for cell in range(9):
            if sum(key[0] == str(parent) and key[1] == str(cell)
                   for key in sample_keys) != reads:
                fail("missing one-read child in parent/grid cell")
    if any(len(hashes) != 1 for hashes in grid_hashes.values()):
        fail("coefficient identity drifted within one grid cell")
    for row in trials:
        if not (0 < float(row["sampler_wall_seconds"]) < 180):
            fail("missing independent observed sampler wall duration")
    return raw, summary, samples, trials, grid_hashes


def compare_directories(first: Path, second: Path):
    a, sa, _, trials_a, hashes_a = read_directory(first)
    b, sb, _, trials_b, hashes_b = read_directory(second)
    # Stronger than only matching seeds/feasible counts or numeric tolerance:
    # every source coefficient, auxiliary bit and sample energy is identical.
    for key in ("compiled_source_model.json", "samples.csv"):
        if a[key] != b[key]:
            fail("replay was NOT bitwise identical for " + key)
    if hashes_a != hashes_b:
        fail("per-cell compiled QUBO coefficients differ")
    ignored = {"software"}
    if {k: v for k, v in sa.items() if k not in ignored} != {
        k: v for k, v in sb.items() if k not in ignored
    }:
        fail("experimental protocol/parameters differ beyond git/software runtime metadata")
    # Timing is observational and expected to vary, but all non-timing
    # trial measurements and every actual sampled state must be identical.
    if len(trials_a) != len(trials_b):
        fail("different number of parent/cell trials")
    for aa, bb in zip(trials_a, trials_b):
        for key in aa:
            if key != "sampler_wall_seconds" and aa[key] != bb.get(key):
                fail("parent-cell non-timing summary differs: " + key)
    return {
        "schema": "m2-frozen-source-72-draw-bitwise-replay-v1",
        "source_geojson_sha256": SOURCE,
        "frozen_original_model_sha256": PROFILE,
        "source_model_bytes_identical": True,
        "sample_CSV_bytes_identical": True,
        "all_full_original_and_slack_bits_identical": True,
        "all_original_and_augmented_energies_identical": True,
        "all_per_grid_qubo_coefficient_hashes_identical": True,
        "sample_source_CSV_sha256": sha256(a["samples.csv"]).hexdigest(),
        "sample_count_per_execution": sa["sampled_source_states"],
        "parent_blocks_per_execution": len(sa["parent_seeds"]),
        "num_penalty_cells": 9,
        "observed_feasible_counts_by_grid": [
            sum(row["original_feasible"] == "True" for row in
                csv.DictReader(io.StringIO(a["samples.csv"].decode("utf-8")))
                if int(row["grid_index"]) == i)
            for i in range(9)
        ],
        "runtime_bytes_expected_to_differ": True,
        "executions_are_replays_not_independent_parent_block_samples": True,
        "quantum_hardware_executed": False,
        "winner_or_statistical_inference_permitted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = compare_directories(args.first, args.second)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(record))
    print(json.dumps(record, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
