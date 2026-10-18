"""Predeclared paired-parent-seed classical SA replication for one N=20 instance.

See SA_PAIRED_REPLICATION.md and issue #22: all 32 seeds, endpoints and
bootstrap settings were frozen before examining the experiment outcomes.
This is an observational Monte Carlo comparison on ONE fixed optimization
instance; paired bootstrap intervals are descriptive, not population claims.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from evidence import canonical_bytes
from sa_benchmark import run_benchmark

PARENT_SEEDS = tuple(range(270010001, 270010033))
PENALTIES = ("notebook-local-row-sum", "midpoint-exploratory",
             "global-feasibility-bound")
BASELINE = PENALTIES[0]
COMPARE = PENALTIES[1:]
READS_PER_PARENT = 32
SWEEPS = 300
BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 734021
OPTIMUM_TOLERANCE = 1e-7


def _require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def summarize_blocks(
    trials: list[dict], samples: list[dict], *,
    seeds: tuple[int, ...], reads: int,
    optimum: float, bootstrap_iterations: int, bootstrap_seed: int,
) -> dict:
    """Summarize complete per-read data; resample whole paired parent blocks.

    The original feasible-and-near-optimal endpoint is counted over ALL
    returned reads, including infeasible draws, never conditioned on success.
    """
    _require(len(seeds) >= 2 and len(set(seeds)) == len(seeds),
             "Expected at least two distinct paired parent blocks")
    _require(reads >= 1 and bootstrap_iterations >= 100,
             "Invalid read or bootstrap count")
    _require(len(trials) == len(seeds) * len(PENALTIES),
             "Missing, repeated or unexpected parent-penalty trials")
    expected_samples = len(seeds) * len(PENALTIES) * reads
    _require(sum(int(row["occurrences"]) for row in samples) == expected_samples,
             "Missing sampled states or unexpected multiplicity")

    trial_by_key: dict[tuple[int, str], dict] = {}
    for trial in trials:
        key = (int(trial["seed"]), str(trial["penalty"]))
        _require(key not in trial_by_key and key[0] in seeds and key[1] in PENALTIES,
                 "Duplicated or unexpected parent-penalty trial")
        _require(int(trial["sample_count"]) == reads, "Incorrect reads per parent")
        trial_by_key[key] = trial

    grouped: dict[tuple[int, str], list[dict]] = {
        (seed, penalty): [] for seed in seeds for penalty in PENALTIES
    }
    for sample in samples:
        key = (int(sample["seed"]), str(sample["penalty"]))
        _require(key in grouped, "Sample has unknown parent seed or penalty")
        _require(sample["sample_seed"] is not None and sample["read_index"] is not None,
                 "Every sample requires an independently logged child seed and read index")
        grouped[key].append(sample)

    n = len(seeds)
    feasibility = np.zeros((n, len(PENALTIES)), dtype=float)
    hits = np.zeros_like(feasibility)
    aggregate: dict[str, dict] = {}
    for col, penalty in enumerate(PENALTIES):
        penalty_rows = [sample for sample in samples if sample["penalty"] == penalty]
        feasible_energy_rows = [row for row in penalty_rows if bool(row["feasible"])]
        feasible_count = sum(int(s["occurrences"]) for s in feasible_energy_rows)
        opt_count = 0
        for row in feasible_energy_rows:
            _require(float(row["raw_objective"]) >= optimum - OPTIMUM_TOLERANCE,
                     "SA feasible sample appears to beat proven SCIP optimum")
            if abs(float(row["raw_objective"]) - optimum) <= OPTIMUM_TOLERANCE:
                opt_count += int(row["occurrences"])
        best = min((float(s["raw_objective"]) for s in feasible_energy_rows), default=None)
        mean_feasible = (
            sum(float(s["raw_objective"]) * int(s["occurrences"])
                for s in feasible_energy_rows) / feasible_count
            if feasible_count else None
        )
        for row_idx, seed in enumerate(seeds):
            key = (seed, penalty)
            rows = grouped[key]
            _require(len(rows) == reads and key in trial_by_key,
                     "Every parent-penalty block must contain exactly one row per read")
            _require({int(s["read_index"]) for s in rows} == set(range(reads)),
                     "Duplicate or omitted read indices in a parent block")
            _require(len({int(s["sample_seed"]) for s in rows}) == reads,
                     "Read-level random seeds are not distinct within a block")
            _require(all(int(s["occurrences"]) == 1 for s in rows),
                     "Replication protocol requires exactly one draw per child seed")
            count_feasible = sum(bool(s["feasible"]) for s in rows)
            count_opt = sum(
                bool(s["feasible"]) and
                abs(float(s["raw_objective"]) - optimum) <= OPTIMUM_TOLERANCE
                for s in rows
            )
            _require(count_feasible == int(trial_by_key[key]["feasible_sample_count"]),
                     "Trial and decoded sample feasibility counts disagree")
            _require(count_opt == int(trial_by_key[key]["exact_optimum_hits"]),
                     "Trial and decoded sample optimum-hit counts disagree")
            feasibility[row_idx, col] = count_feasible / reads
            hits[row_idx, col] = count_opt / reads

        total = n * reads
        _require(feasible_count == int(round(feasibility[:, col].sum() * reads)),
                 "Feasible aggregate does not match independent block counting")
        _require(opt_count == int(round(hits[:, col].sum() * reads)),
                 "Optimal hit aggregate does not match independent block counting")
        aggregate[penalty] = {
            "total_draws": total,
            "feasible_draws": feasible_count,
            "feasible_percent": 100 * feasible_count / total,
            "exact_optimum_hits": opt_count,
            "exact_optimum_percent": 100 * opt_count / total,
            "best_feasible_raw_objective": best,
            "mean_feasible_raw_objective": mean_feasible,
            "best_feasible_gap_vs_scip": (best - optimum if best is not None else None),
        }

    # Bootstrap paired PARENT BLOCKS, not each read: same resampled indices
    # are applied to all penalty columns and to the primary/secondary metric.
    rng = np.random.default_rng(bootstrap_seed)
    indices = rng.integers(0, n, size=(bootstrap_iterations, n))
    results: dict[str, Any] = {}
    for name, values in (
        ("exact_optimum_percent", hits),
        ("feasible_percent", feasibility),
    ):
        actual = values.mean(axis=0) * 100
        distribution = values[indices].mean(axis=1) * 100
        intervals = np.quantile(distribution, [0.025, 0.975], axis=0)
        rates = {}
        for col, penalty in enumerate(PENALTIES):
            rates[penalty] = {
                "estimate_percent": float(actual[col]),
                "interval_95_percent": [
                    float(intervals[0, col]), float(intervals[1, col])
                ],
            }
        deltas = {}
        for penalty in COMPARE:
            col = PENALTIES.index(penalty)
            paired_delta = distribution[:, col] - distribution[:, 0]
            deltas[f"{penalty}_minus_{BASELINE}"] = {
                "estimate_percentage_points": float(actual[col] - actual[0]),
                "interval_95_percentage_points": [
                    float(v) for v in np.quantile(paired_delta, [0.025, 0.975])
                ],
            }
        results[name] = {"rates": rates, "paired_contrasts": deltas}

    return {
        "schema_version": 1,
        "reference_scip_optimum": optimum,
        "num_parent_seed_blocks": n,
        "reads_per_parent_penalty": reads,
        "bootstrap": {
            "unit": "paired_parent_seed_block",
            "iterations": bootstrap_iterations,
            "seed": bootstrap_seed,
            "interval": "unadjusted_percentile_2.5_97.5",
            "scope": "descriptive uncertainty for same frozen instance",
        },
        "aggregate": aggregate,
        "endpoints": results,
    }


def run_protocol() -> tuple[dict, list[dict], list[dict], dict]:
    """No runtime options to change pre-registered seeds, sweeps or endpoints."""
    _require(len(PARENT_SEEDS) == 32 and not set(PARENT_SEEDS).intersection(
        {20261018, 20261019, 20261020, 1970, 1971}),
        "Registered follow-up seed manifest changed")
    batches = [PARENT_SEEDS[start:start + 8]
               for start in range(0, len(PARENT_SEEDS), 8)]
    _require(len(batches) == 4 and all(len(batch) == 8 for batch in batches),
             "Expected four bounded batches of eight blocks")

    reference: dict | None = None
    all_trials: list[dict] = []
    all_samples: list[dict] = []
    for batch in batches:
        output, trials, samples = run_benchmark(
            seeds=batch, reads=READS_PER_PARENT, sweeps=SWEEPS
        )
        if reference is None:
            reference = output
        else:
            for key in ("scenario", "N_free", "K_new", "penalty_points",
                        "scip", "enumeration", "sources"):
                _require(output[key] == reference[key],
                         f"Independent batch changed fixed reference: {key}")
        all_trials.extend(trials)
        all_samples.extend(samples)
    assert reference is not None
    _require(len(all_trials) == 96 and len(all_samples) == 3072,
             "Run failed fixed sample budget")

    report = summarize_blocks(
        all_trials, all_samples, seeds=PARENT_SEEDS,
        reads=READS_PER_PARENT, optimum=float(reference["scip"]["energy"]),
        bootstrap_iterations=BOOTSTRAP_ITERATIONS, bootstrap_seed=BOOTSTRAP_SEED,
    )
    protocol = {
        "schema_version": 1,
        "issue": 22,
        "design": "preregistered_paired_seed_classical_sa_n20",
        "parent_seeds": list(PARENT_SEEDS),
        "read_seed_derivation": reference["read_seed_derivation"],
        "reads_per_parent_per_penalty": READS_PER_PARENT,
        "sweeps_per_call": SWEEPS,
        "penalty_points": reference["penalty_points"],
        "num_penalties": len(PENALTIES),
        "expected_samples": len(PARENT_SEEDS) * len(PENALTIES) * READS_PER_PARENT,
        "objective_tolerance": OPTIMUM_TOLERANCE,
        "primary": "feasible AND raw objective within tolerance of SCIP optimum, denominator all draws",
        "secondary": "original budget/local-adjacency feasibility, denominator all draws",
        "comparison": "midpoint minus row sum; global minus row sum",
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "provenance": {
            "scenario": reference["scenario"],
            "N_free": reference["N_free"],
            "K_new": reference["K_new"],
            "scip": reference["scip"],
            "sources": reference["sources"],
            "runtime": reference["runtime"],
        },
        "limitations": "One frozen lake instance; this is classical SA and NOT historical paper parity, quantum advantage, or cross-instance inference.",
    }
    return protocol, all_trials, all_samples, report


def write_bundle(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol, trials, samples, report = run_protocol()
    files = {}
    for name, payload in (("protocol.json", protocol), ("summary.json", report)):
        path = output_dir / name
        path.write_bytes(canonical_bytes(payload))
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name, rows in (("trials.csv", trials), ("samples.csv", samples)):
        path = output_dir / name
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "file_sha256": files,
        "contains_all_returned_samples": True,
        "sample_count": 3072,
    }
    (output_dir / "manifest.json").write_bytes(canonical_bytes(manifest))
    for name, digest in files.items():
        _require(hashlib.sha256((output_dir / name).read_bytes()).hexdigest() == digest,
                 "Exported file failed SHA-256 integrity verification")
    for penalty, metrics in report["aggregate"].items():
        print("N20_PAIRED_REPLICATION " + json.dumps(
            {"penalty": penalty, **metrics}, sort_keys=True, allow_nan=False))
    print("N20_PAIRED_ENDPOINTS " + json.dumps(
        report["endpoints"], sort_keys=True, allow_nan=False))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    write_bundle(args.output_dir)


if __name__ == "__main__":
    main()
