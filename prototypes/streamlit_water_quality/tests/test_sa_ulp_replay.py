"""Exact archived A/B IEEE-754 sensitivity tests (issue #26)."""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sa_benchmark import notebook_row_sum_bound
from sa_ulp_replay import (
    A_LINEAR_OVERRIDES_HEX, B_LINEAR_REFERENCE_HEX, ARMS, B_LINEAR,
    B_QUADRATIC, PENALTY_HEX, build_arms, fixture_instance,
    verify_archived_reference,
)


def test_frozen_archive_input_varies_by_exactly_four_linear_coefficients():
    a = fixture_instance("A")
    b = fixture_instance("B")
    assert len(a.linear) == len(b.linear) == 20
    assert len(a.quadratic) == len(b.quadratic) == 12
    assert a.quadratic == b.quadratic == B_QUADRATIC
    assert a.neighbors == b.neighbors
    assert np.array_equal(a.fixed_neighbors, b.fixed_neighbors)
    assert np.array_equal(a.free_indices, b.free_indices)
    assert np.array_equal(a.fixed_indices, b.fixed_indices)
    assert len(a.fixed_indices) == 15
    changed = {i for i, (v, w) in enumerate(zip(a.linear, b.linear)) if v != w}
    assert changed == {9, 10, 17, 19}
    for index in changed:
        assert a.linear[index].hex() == A_LINEAR_OVERRIDES_HEX[index]
        assert b.linear[index].hex() == B_LINEAR_REFERENCE_HEX[index]
        assert abs(float(a.linear[index] - b.linear[index])) <= 3e-16


def test_four_arms_reproduce_source_energies_and_exact_penalty_bits():
    a = verify_archived_reference(fixture_instance("A"))
    b = verify_archived_reference(fixture_instance("B"))
    assert a["optimal_local_indices"] == b["optimal_local_indices"] == [0, 1, 3, 6, 7]
    assert a["feasible_subsets"] == b["feasible_subsets"] == 1077
    assert a["enumerated_subsets"] == b["enumerated_subsets"] == 15504
    assert a["energy"] == b["energy"] == -3.3012934918564643

    # The four ULP differences enter the notebook's heuristic through
    # local candidate 17: it is the unique maximum abs-linear+pair row.
    for mode in ("A", "B"):
        instance = fixture_instance(mode)
        row = np.abs(instance.linear).copy()
        for i, j, q in instance.quadratic:
            row[i] += abs(q)
            row[j] += abs(q)
        assert int(np.argmax(row)) == 17
        assert float(row[17]).hex() == PENALTY_HEX[mode]
        assert float(notebook_row_sum_bound(instance)).hex() == PENALTY_HEX[mode]

    arms = build_arms()
    assert [x[0] for x in arms] == [x[0] for x in ARMS]
    assert all(q.n_variables == 46 for _, _, q, _ in arms)
    assert all(len(q.coefficients) == 323 for _, _, q, _ in arms)
    for name, inst, qubo, config in arms:
        expected_penalty = PENALTY_HEX[config["penalty_source"]]
        assert qubo.budget_penalty.hex() == expected_penalty
        assert qubo.connectivity_penalty.hex() == expected_penalty
        assert len(config["qubo_sha256"]) == 64
    assert len({config["qubo_sha256"] for _, _, _, config in arms}) == 4
    assert len({config["penalty_hex"] for _, _, _, config in arms}) == 2
