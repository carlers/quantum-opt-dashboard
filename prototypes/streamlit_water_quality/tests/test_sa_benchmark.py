"""Reproducibility contract for *classical* OpenJij SA versus proven SCIP."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import Instance
from qubo import make_qubo, energy as expanded_qubo_energy
from sa_benchmark import (
    benchmark_penalties, decode_records, independent_augmented_energy,
    notebook_row_sum_bound, run_benchmark, seed_summary, write_bundle,
)


class FakeRecord:
    def __init__(self, samples, energies, occurrences):
        self.sample = np.asarray(samples, dtype=int)
        self.energy = np.asarray(energies, dtype=float)
        self.num_occurrences = np.asarray(occurrences, dtype=int)


class FakeResponse:
    def __init__(self, indices, record):
        self.indices = indices
        self.record = record


def small_instance():
    return Instance(
        coords=np.zeros((4, 2)), free_indices=np.arange(3),
        fixed_indices=np.array([3]), utility=np.zeros(4),
        linear=np.array([-1.8, -1.6, -0.3]),
        quadratic=((0, 1, 0.4), (1, 2, 0.2)),
        neighbors=((1,), (0, 2), (1,)),
        fixed_neighbors=np.array([1, 0, 0]),
        budget=2, d_max=9000.0,
    )


def test_independent_augmented_energy_matches_qubo_for_all_tiny_binary_states():
    inst = small_instance()
    qubo = make_qubo(inst, budget_penalty=2.5, connectivity_penalty=6.)
    for integer in range(1 << qubo.n_variables):
        bits = [(integer >> i) & 1 for i in range(qubo.n_variables)]
        assert independent_augmented_energy(inst, qubo, bits) == pytest.approx(
            expanded_qubo_energy(qubo, bits), abs=1e-9
        )


def test_sampler_record_indices_not_assumed_order_and_occurrences_counted():
    inst = small_instance()
    qubo = make_qubo(inst, budget_penalty=2.5, connectivity_penalty=6.)
    first = [1, 1, 0] + [0] * (qubo.n_variables - 3)
    second = [0, 0, 0] + [0] * (qubo.n_variables - 3)
    indices = list(reversed(range(qubo.n_variables)))
    record = FakeRecord(
        samples=[[bits[i] for i in indices] for bits in (first, second)],
        energies=[expanded_qubo_energy(qubo, bits) - qubo.offset for bits in (first, second)],
        occurrences=[3, 2],
    )
    rows = decode_records(
        FakeResponse(indices, record), qubo, inst, seed=73, penalty_name="sample"
    )
    assert [r["occurrences"] for r in rows] == [3, 2]
    assert rows[0]["selected_local_indices"] == "[0,1]"
    assert rows[0]["feasible"] is True
    assert rows[1]["feasible"] is False
    assert seed_summary(rows, expected_reads=5, optimum=-3.)["feasible_fraction"] == pytest.approx(3 / 5)
    with pytest.raises(AssertionError, match="instead"):
        seed_summary(rows, expected_reads=4, optimum=-3.)

    incomplete = FakeResponse(indices[:-1], FakeRecord([[0] * (qubo.n_variables - 1)], [0], [1]))
    with pytest.raises(RuntimeError, match="every"):
        decode_records(incomplete, qubo, inst, seed=2, penalty_name="wrong")

    bad_energy = FakeResponse(indices, FakeRecord([[first[i] for i in indices]], [-999.], [1]))
    with pytest.raises(AssertionError, match="Sampler"):
        decode_records(bad_energy, qubo, inst, seed=2, penalty_name="wrong")


def test_seed_config_and_heuristic_v_global_bound_distinction():
    inst = small_instance()
    grid = benchmark_penalties(inst)
    assert set(grid) == {
        "notebook-local-row-sum", "midpoint-exploratory",
        "global-feasibility-bound"
    }
    assert 0 < notebook_row_sum_bound(inst) == grid["notebook-local-row-sum"]
    assert grid["global-feasibility-bound"] > grid["midpoint-exploratory"] > grid["notebook-local-row-sum"]
    with pytest.raises(ValueError, match="seeds"):
        run_benchmark(seeds=(4, 4), reads=2, sweeps=10)
    with pytest.raises(ValueError, match="Bounded"):
        run_benchmark(seeds=(1,), reads=10000, sweeps=10)


def test_real_openjij_n20_seeded_benchmark_and_export_contract(tmp_path):
    import openjij as oj

    assert oj.__version__ == "0.12.2"
    summary = write_bundle(tmp_path, seeds=(1970, 1971), reads=8, sweeps=50)
    assert summary["scip"]["proven_optimal"] is True
    assert summary["scip"]["energy"] == pytest.approx(-3.3012934918564643, abs=1e-7)
    assert summary["scip"]["selected_local_indices"] == [0, 1, 3, 6, 7]
    assert summary["sources"]["fixed_master_feature_positions"] == [
        417, 454, 725, 1055, 1076, 1709, 2771, 3402, 3520, 3529,
        3732, 3886, 4613, 4868, 5038,
    ]
    assert summary["enumeration"]["combinations_checked"] == 15504
    assert summary["runtime"]["openjij"] == "0.12.2"
    assert len(summary["aggregate"]) == 3
    assert len(summary["seeds"]) == 2
    for key, group in summary["aggregate"].items():
        assert group["total_samples"] == 16
        assert group["feasible_samples"] <= group["total_samples"]
        assert group["feasible_fraction"] == pytest.approx(group["feasible_samples"] / 16)
        if group["best_feasible_raw_objective"] is not None:
            assert group["best_feasible_raw_objective"] >= summary["scip"]["energy"] - 1e-7
            assert group["gap_to_proven_scip"] >= -1e-7
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert len(manifest["file_sha256"]) == 3
    for filename, sha in manifest["file_sha256"].items():
        assert hashlib.sha256((tmp_path / filename).read_bytes()).hexdigest() == sha

    # Reuse exactly the same seeds/read/sweep config in the same installed
    # sampler version. Compare returned sampling *data*; skip wall time,
    # machine-specific float last bits and runtime metadata.
    second, trials, _ = run_benchmark(seeds=(1970, 1971), reads=8, sweeps=50)
    assert {p: a["feasible_samples"] for p, a in second["aggregate"].items()} == {
        p: a["feasible_samples"] for p, a in summary["aggregate"].items()
    }
    assert len(trials) == 6
