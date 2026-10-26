"""Source-grounded and adversarial 2D budget/connectivity QUBO gates."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from problems.water_quality.nested_resolution import build_nested_instances
from problems.water_quality.independent_penalty_grid import (
    FROZEN_N20_OPTIMUM, SOURCE_SHA256, LEVEL_NAMES,
    notebook_single_flip_bound, penalty_levels, grid,
    child_seeds, inspect_one_read, qubo_digest, model_record,
)
from prototypes.streamlit_water_quality.qubo import (
    make_qubo, best_slack_assignment, decoded_penalty_energy,
    safe_penalty, energy as expanded_energy,
)


@pytest.fixture(scope="module")
def instance():
    study = build_nested_instances(tiers=(20,))
    assert study.source_sha256 == SOURCE_SHA256
    assert not study.fixed_simulated
    assert len(study.fixed_master_positions) == 15
    return study.tier_instances[0].instance


def fake_response(qubo, bits, *, energy_shift=0., corrupt_missing=False):
    names = list(range(qubo.n_variables))
    if corrupt_missing:
        names.pop()
    state = np.asarray(bits[:len(names)], dtype=int).reshape(1, -1)
    return SimpleNamespace(
        indices=names,
        record=SimpleNamespace(
            sample=state,
            num_occurrences=np.array([1], dtype=int),
            energy=np.array([
                expanded_energy(qubo, bits) - qubo.offset + energy_shift
            ]),
        ),
    )


def test_2d_grid_has_distinct_axes_and_conservative_bound(instance):
    points = grid(instance)
    assert len(points) == 9
    assert [p["grid_index"] for p in points] == list(range(9))
    lower, middle, upper = penalty_levels(instance)
    assert [k for k, _ in (lower, middle, upper)] == list(LEVEL_NAMES)
    assert 0 < lower[1] < middle[1] < upper[1]
    assert upper[1] == safe_penalty(instance)
    assert lower[1] == notebook_single_flip_bound(instance)
    assert points[0]["lambda_budget"] == lower[1]
    assert points[0]["lambda_connectivity"] == lower[1]
    assert points[2]["lambda_connectivity"] == upper[1]
    assert points[6]["lambda_budget"] == upper[1]
    assert points[6]["lambda_connectivity"] == lower[1]
    assert points[-1]["lambda_budget"] == upper[1]
    assert points[-1]["lambda_connectivity"] == upper[1]
    assert points[2]["lambda_budget"] != points[2]["lambda_connectivity"]


def test_pinned_optimum_has_no_budget_or_connection_cost_at_all_9_penalties(instance):
    chosen = [int(i in (0, 1, 3, 6, 7)) for i in range(20)]
    for point in grid(instance):
        qubo = make_qubo(
            instance, budget_penalty=point["lambda_budget"],
            connectivity_penalty=point["lambda_connectivity"]
        )
        bits = best_slack_assignment(instance, qubo, chosen)
        assert expanded_energy(qubo, bits) == pytest.approx(FROZEN_N20_OPTIMUM, abs=1e-7)
        assert decoded_penalty_energy(instance, qubo, chosen) == pytest.approx(
            FROZEN_N20_OPTIMUM, abs=1e-7
        )
        assert len(qubo_digest(qubo)) == 64
        assert all(i <= j for i, j in qubo.coefficients)


def test_fake_one_read_is_independently_checked_with_distinct_penalty_axes(instance):
    point = grid(instance)[2]
    qubo = make_qubo(
        instance, budget_penalty=point["lambda_budget"],
        connectivity_penalty=point["lambda_connectivity"],
    )
    optimum = [int(i in (0, 1, 3, 6, 7)) for i in range(20)]
    bits = best_slack_assignment(instance, qubo, optimum)
    verified = inspect_one_read(
        fake_response(qubo, bits), qubo, instance,
        parent_seed=270010001, child_seed=201, grid_index=2, read_index=0
    )
    assert verified["original_feasible"] is True
    assert verified["budget_residual"] == 0
    assert verified["isolated_selected_count"] == 0
    assert verified["original_raw_objective"] == pytest.approx(FROZEN_N20_OPTIMUM, abs=1e-7)
    assert verified["budget_penalty_component"] == 0
    assert verified["connectivity_penalty_component"] == 0
    assert verified["sampled_slack_excess_energy"] == pytest.approx(0., abs=1e-7)

    zero = [0] * 20
    second = best_slack_assignment(instance, qubo, zero)
    unchecked = inspect_one_read(
        fake_response(qubo, second), qubo, instance,
        parent_seed=270010001, child_seed=202, grid_index=2, read_index=1
    )
    assert unchecked["original_feasible"] is False
    assert unchecked["budget_residual"] == -5
    assert unchecked["budget_penalty_component"] > 0

    with pytest.raises(ValueError, match="energy"):
        inspect_one_read(
            fake_response(qubo, bits, energy_shift=2.), qubo, instance,
            parent_seed=270010001, child_seed=203, grid_index=2, read_index=2
        )
    with pytest.raises(ValueError, match="auxiliary"):
        inspect_one_read(
            fake_response(qubo, bits, corrupt_missing=True), qubo, instance,
            parent_seed=270010001, child_seed=204, grid_index=2, read_index=3
        )


def test_parent_specific_child_streams_are_stable_and_nonrepeating():
    one = child_seeds(270010001, 0, 4)
    two = child_seeds(270010001, 1, 4)
    other = child_seeds(270010002, 0, 4)
    assert one == child_seeds(270010001, 0, 4)
    assert len(set(one + two + other)) == 12
    for parent in (270010001, 270010002):
        for point in range(9):
            assert len(set(child_seeds(parent, point, 4))) == 4
    with pytest.raises(ValueError):
        child_seeds(270010001, 9, 4)
    with pytest.raises(ValueError):
        child_seeds(270010001, 0, 1000)


def test_coefficient_identity_is_sensitive_to_each_penalty_axis(instance):
    a, b, c = grid(instance)[0], grid(instance)[1], grid(instance)[3]
    configs = []
    for row in (a, b, c):
        q = make_qubo(
            instance, budget_penalty=row["lambda_budget"],
            connectivity_penalty=row["lambda_connectivity"],
        )
        configs.append(qubo_digest(q))
    assert len(set(configs)) == 3
    assert model_record(instance)["N_free"] == 20
    assert model_record(instance)["K"] == 5
