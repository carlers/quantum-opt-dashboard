"""Pure-statistics tests for pre-registered paired SA replication #22.

Synthetic examples deliberately contain infeasible blocks and uneven optimum
hits to catch denominator confusion, pseudoreplication, and unpaired CIs.
"""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sa_paired_replication import (
    BASELINE, BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED, COMPARE, PARENT_SEEDS,
    PENALTIES, READS_PER_PARENT, SWEEPS, summarize_blocks,
)


# Each [a,b] pair denotes whether a trial draw is infeasible (0),
# feasible but suboptimal (1), or feasible at the certified optimum (2).
SYNTHETIC = {
    "notebook-local-row-sum": ((2, 0), (0, 0), (1, 1), (2, 2)),
    "midpoint-exploratory": ((1, 1), (2, 0), (2, 1), (0, 1)),
    "global-feasibility-bound": ((2, 1), (1, 1), (0, 0), (2, 0)),
}


def synthetic_records():
    trials, samples = [], []
    for penalty in PENALTIES:
        for block, outcomes in enumerate(SYNTHETIC[penalty]):
            seed = 11 + block
            trials.append({
                "penalty": penalty, "seed": seed, "sample_count": 2,
                "feasible_sample_count": sum(x > 0 for x in outcomes),
                "exact_optimum_hits": sum(x == 2 for x in outcomes),
            })
            for j, outcome in enumerate(outcomes):
                samples.append({
                    "penalty": penalty, "seed": seed, "read_index": j,
                    "sample_seed": seed * 100 + j, "occurrences": 1,
                    "feasible": outcome > 0,
                    "raw_objective": -5 if outcome == 2 else -3 if outcome == 1 else 0,
                })
    return trials, samples


def report(trials=None, samples=None):
    original_trials, original_samples = synthetic_records()
    return summarize_blocks(
        original_trials if trials is None else trials,
        original_samples if samples is None else samples,
        seeds=(11, 12, 13, 14), reads=2, optimum=-5.0,
        bootstrap_iterations=1000, bootstrap_seed=2026,
    )


def test_seed_manifest_is_frozen_and_disjoint_from_exploratory_pilot():
    assert len(PARENT_SEEDS) == 32
    assert PARENT_SEEDS[0] == 270010001
    assert PARENT_SEEDS[-1] == 270010032
    assert len(set(PARENT_SEEDS)) == 32
    assert not set(PARENT_SEEDS) & {20261018, 20261019, 20261020, 1970, 1971}
    assert READS_PER_PARENT == 32 and SWEEPS == 300
    assert BOOTSTRAP_ITERATIONS == 10_000 and BOOTSTRAP_SEED == 734021
    assert BASELINE == "notebook-local-row-sum"
    assert COMPARE == ("midpoint-exploratory", "global-feasibility-bound")


def test_paired_bootstrap_produces_expected_counts_rates_and_fixed_intervals():
    trials, samples = synthetic_records()
    result = report(trials, samples)
    a, b, c = (result["aggregate"][p] for p in PENALTIES)
    assert [x["feasible_draws"] for x in (a, b, c)] == [5, 6, 5]
    assert [x["exact_optimum_hits"] for x in (a, b, c)] == [3, 2, 2]
    assert [x["feasible_percent"] for x in (a, b, c)] == [62.5, 75., 62.5]
    assert [x["exact_optimum_percent"] for x in (a, b, c)] == [37.5, 25., 25.]
    assert a["best_feasible_raw_objective"] == -5
    assert result["bootstrap"]["unit"] == "paired_parent_seed_block"
    assert result["bootstrap"]["iterations"] == 1000
    assert result["num_parent_seed_blocks"] == 4

    hits = result["endpoints"]["exact_optimum_percent"]
    feasible = result["endpoints"]["feasible_percent"]
    for p in COMPARE:
        key = f"{p}_minus_{BASELINE}"
        assert hits["paired_contrasts"][key]["estimate_percentage_points"] == -12.5
    assert feasible["paired_contrasts"][f"{COMPARE[0]}_minus_{BASELINE}"][
        "estimate_percentage_points"] == 12.5
    assert feasible["paired_contrasts"][f"{COMPARE[1]}_minus_{BASELINE}"][
        "estimate_percentage_points"] == 0.

    # Fixed-bootstrap reproducibility and bounded endpoints; deliberately
    # do not assert data-dependent best penalty as a software invariant.
    assert report(trials, samples) == result
    for endpoint in result["endpoints"].values():
        for item in endpoint["rates"].values():
            lower, upper = item["interval_95_percent"]
            assert 0 <= lower <= upper <= 100
        for contrast in endpoint["paired_contrasts"].values():
            lower, upper = contrast["interval_95_percentage_points"]
            assert -100 <= lower <= upper <= 100


def test_missing_read_or_seed_collision_cannot_enter_statistics():
    trials, samples = synthetic_records()
    with pytest.raises(AssertionError, match="Missing sampled"):
        report(trials, samples[:-1])

    bad = deepcopy(samples)
    bad[1]["sample_seed"] = bad[0]["sample_seed"]
    with pytest.raises(AssertionError, match="not distinct"):
        report(trials, bad)

    changed = deepcopy(trials)
    changed[0]["exact_optimum_hits"] = 99
    with pytest.raises(AssertionError, match="optimum-hit counts"):
        report(changed, samples)

    changed = deepcopy(samples)
    changed[0]["raw_objective"] = -6.0
    with pytest.raises(AssertionError, match="beat proven SCIP"):
        report(trials, changed)


def test_all_infeasible_samples_keep_null_feasible_objective():
    trials, samples = synthetic_records()
    for trial in trials:
        trial["feasible_sample_count"] = 0
        trial["exact_optimum_hits"] = 0
    for sample in samples:
        sample["feasible"] = False
        sample["raw_objective"] = 0.
    result = report(trials, samples)
    for p in PENALTIES:
        row = result["aggregate"][p]
        assert row["feasible_draws"] == 0
        assert row["exact_optimum_hits"] == 0
        assert row["best_feasible_raw_objective"] is None
        assert row["mean_feasible_raw_objective"] is None
        assert row["best_feasible_gap_vs_scip"] is None
        assert result["endpoints"]["exact_optimum_percent"]["rates"][p][
            "interval_95_percent"] == [0.0, 0.0]
