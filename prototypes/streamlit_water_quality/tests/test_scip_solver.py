"""Solver-backed scientific smoke tests for the prototype's MIQP linearization.

Checks exact optimality of SCIP MILP against an independent exhaustive enumerator
on small binary instances. These are *not* publication-parity tests.
"""
from itertools import product
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import Instance, evaluate, solve_scip


def small_instance(budget=2):
    # Fixed station is index 4; only candidate 0 is adjacent to it.
    # Other selected candidates need at least one selected neighbor.
    return Instance(
        coords=np.zeros((5, 2), dtype=float),
        free_indices=np.array([0, 1, 2, 3]),
        fixed_indices=np.array([4]),
        utility=np.zeros(5),
        linear=np.array([-1.8, -1.6, -1.0, -0.3]),
        quadratic=((0, 1, 1.2), (0, 2, 0.15), (1, 2, 0.2), (2, 3, 0.4)),
        neighbors=((1,), (0, 2), (1, 3), (2,)),
        fixed_neighbors=np.array([1, 0, 0, 0]),
        budget=budget,
        d_max=1000.0,
    )


def enumerate_feasible(instance):
    possibilities = (
        (np.asarray(bits, dtype=int), evaluate(instance, np.asarray(bits, dtype=int)))
        for bits in product((0, 1), repeat=len(instance.free_indices))
    )
    return [(bits, metrics) for bits, metrics in possibilities if metrics["feasible"]]


@pytest.mark.parametrize("budget", [1, 2, 3])
def test_scip_agrees_with_independent_exhaustive_optimum(budget):
    instance = small_instance(budget)
    expected = enumerate_feasible(instance)
    assert expected, "Tiny reference instance unexpectedly infeasible"
    best_energy = min(metrics["energy"] for _, metrics in expected)

    bits, result = solve_scip(instance, time_limit=20.0)
    assert result["status"] == "optimal"
    assert result["optimal"] is True
    assert result["feasible"] is True
    assert result["num_selected"] == budget
    assert result["energy"] == pytest.approx(best_energy, abs=1e-8)
    assert np.array_equal(bits, np.round(bits).astype(int))


def test_infeasible_instance_does_not_emit_fake_solution():
    # All selected free sites have zero fixed/free connectivity.
    disconnected = Instance(
        coords=np.zeros((2, 2)),
        free_indices=np.array([0]),
        fixed_indices=np.array([1]),
        utility=np.zeros(2),
        linear=np.array([-1.0]),
        quadratic=(),
        neighbors=((),),
        fixed_neighbors=np.array([0]),
        budget=1,
        d_max=1000.0,
    )
    with pytest.raises(RuntimeError, match="no feasible solution"):
        solve_scip(disconnected, time_limit=10.0)
