"""Independent QUBO formulation checks against the source MIQP constraints.

Global exhaustive tests are intentionally limited to small inputs.
The N=20 cohort is independently verified with known SCIP optima in PR #15.
"""
from itertools import combinations, product
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import Instance, NOTEBOOK_WEIGHTS, load_data, make_instance
from qubo import (
    best_slack_assignment, decoded_penalty_energy, energy,
    make_qubo, objective_bound, safe_penalty,
)

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"


def tiny_instance() -> Instance:
    return Instance(
        coords=np.zeros((4, 2)),
        free_indices=np.arange(3),
        fixed_indices=np.array([3]),
        utility=np.zeros(4),
        linear=np.array([-1.8, -1.6, -0.3]),
        quadratic=((0, 1, 0.4), (1, 2, 0.2)),
        neighbors=((1,), (0, 2), (1,)),
        fixed_neighbors=np.array([1, 0, 0]),
        budget=2,
        d_max=9000.0,
    )


def original_direct_objective(inst: Instance, x: tuple[int, ...]) -> float:
    return sum(float(v) * x[i] for i, v in enumerate(inst.linear)) + sum(
        float(v) * x[i] * x[j] for i, j, v in inst.quadratic
    )


def original_direct_feasible(inst: Instance, x: tuple[int, ...]) -> bool:
    return (
        sum(x) == inst.budget
        and all(not x[i] or inst.fixed_neighbors[i] or
                any(x[j] for j in inst.neighbors[i]) for i in range(len(x)))
    )


def test_exhaustive_full_binary_qubo_recovers_exact_constrained_optimum():
    inst = tiny_instance()
    qubo = make_qubo(inst)
    assert qubo.n_free == 3
    assert qubo.n_variables == 8
    assert len(qubo.slack_variables) == 3
    assert qubo.budget_penalty == qubo.connectivity_penalty == safe_penalty(inst)
    assert safe_penalty(inst) > 2 * objective_bound(inst)

    best_full = float("inf")
    best_originals = set()
    for assignment in product((0, 1), repeat=qubo.n_variables):
        x = tuple(assignment[:3])
        value = energy(qubo, list(assignment))
        best_full = min(best_full, value)
        if original_direct_feasible(inst, x):
            best_originals.add(x)

    feasible_energies = {
        x: original_direct_objective(inst, x)
        for x in best_originals
    }
    true_min = min(feasible_energies.values())
    assert best_full == pytest.approx(true_min, abs=1e-10)

    # For every possible x, globally minimizing over ALL slack bitstrings
    # must equal the intended nonlinear isolation/budget penalty formula.
    m = qubo.n_variables - qubo.n_free
    for x in product((0, 1), repeat=qubo.n_free):
        direct = original_direct_objective(inst, x)
        direct += qubo.budget_penalty * (sum(x) - inst.budget) ** 2
        direct += qubo.connectivity_penalty * sum(
            bool(x[i]) and not (inst.fixed_neighbors[i] or
                                any(x[j] for j in inst.neighbors[i]))
            for i in range(qubo.n_free)
        )
        minimum = min(energy(qubo, list(x + aux))
                      for aux in product((0, 1), repeat=m))
        canonical = energy(qubo, best_slack_assignment(inst, qubo, list(x)))
        assert minimum == pytest.approx(direct, abs=1e-10)
        assert canonical == pytest.approx(minimum, abs=1e-10)
        assert decoded_penalty_energy(inst, qubo, list(x)) == pytest.approx(
            direct, abs=1e-10
        )


def test_no_overconnectivity_reward_and_infeasible_budget_detected():
    inst = tiny_instance()
    qubo = make_qubo(inst)
    # x=(1,1,1) has several free neighbors: connectivity cost must be ZERO,
    # rather than the negative reward of x_i*(1 - sum_j x_j).
    all_selected = [1, 1, 1]
    actual = energy(qubo, best_slack_assignment(inst, qubo, all_selected))
    expected = original_direct_objective(inst, tuple(all_selected)) + qubo.budget_penalty
    assert actual == pytest.approx(expected, abs=1e-10)

    # x=(0,0,1) is isolated: one connectivity penalty and one budget penalty.
    isolated = [0, 0, 1]
    actual = energy(qubo, best_slack_assignment(inst, qubo, isolated))
    expected = original_direct_objective(inst, tuple(isolated))
    expected += qubo.budget_penalty + qubo.connectivity_penalty
    assert actual == pytest.approx(expected, abs=1e-10)


def test_n20_qubo_reconstructs_original_energy_and_constraint_penalty():
    data = load_data(DATA)
    inst, simulated = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    assert not simulated
    qubo = make_qubo(inst)
    assert qubo.n_variables > 20
    assert all(i <= j < qubo.n_variables for i, j in qubo.coefficients)

    optimal_local = {0, 1, 3, 6, 7}
    x = [int(i in optimal_local) for i in range(20)]
    assert original_direct_feasible(inst, tuple(x))
    original_energy = original_direct_objective(inst, tuple(x))
    assert original_energy == pytest.approx(-3.3012934918564643, abs=1e-8)
    assert energy(qubo, best_slack_assignment(inst, qubo, x)) == pytest.approx(
        original_energy, abs=1e-8
    )

    # Independent formula against canonical slack QUBO for representative
    # deterministic patterns, including budget and connectivity violations.
    patterns = [[0] * 20, [1] * 20, x]
    rng = np.random.default_rng(1776)
    patterns.extend([rng.integers(0, 2, 20).tolist() for _ in range(40)])
    for selection in patterns:
        qvalue = energy(qubo, best_slack_assignment(inst, qubo, selection))
        expected = decoded_penalty_energy(inst, qubo, selection)
        assert qvalue == pytest.approx(expected, abs=1e-7, rel=0)

    # Under the derived >2B penalty, every infeasible subset costs strictly
    # more than the original globally optimal feasible energy.
    optimum = original_energy
    for subset in combinations(range(20), 5):
        selection = tuple(int(i in subset) for i in range(20))
        if original_direct_feasible(inst, selection):
            assert original_direct_objective(inst, selection) >= optimum - 1e-7
        else:
            assert decoded_penalty_energy(inst, qubo, list(selection)) > optimum


def test_parameter_validation_and_zero_neighbor_corner_case():
    inst = tiny_instance()
    with pytest.raises(ValueError, match="positive"):
        make_qubo(inst, connectivity_penalty=0)
    with pytest.raises(ValueError, match="positive"):
        make_qubo(inst, budget_penalty=-5)
    with pytest.raises(ValueError, match="binary"):
        best_slack_assignment(inst, make_qubo(inst), [1, 0, 2])

    isolated = Instance(
        coords=np.zeros((2, 2)), free_indices=np.array([0]),
        fixed_indices=np.array([1]), utility=np.zeros(2),
        linear=np.array([-1.0]), quadratic=(), neighbors=((),),
        fixed_neighbors=np.array([0]), budget=1, d_max=1.,
    )
    encoded = make_qubo(isolated)
    assert encoded.n_variables == 1  # no auxiliaries needed
    assert encoded.slack_variables == ((),)
    assert energy(encoded, [1]) == pytest.approx(-1 + encoded.connectivity_penalty)
    assert encoded.connectivity_penalty > 2 * objective_bound(isolated)
