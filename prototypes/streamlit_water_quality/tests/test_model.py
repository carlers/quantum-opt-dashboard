"""Scientific unit invariants for the Streamlit pilot (SCIP install not required)."""
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import Instance, NOTEBOOK_WEIGHTS, PAPER_WEIGHTS, evaluate, site_utility


def test_missing_factor_uses_notebook_renormalization():
    factors = np.array([[1., np.nan, 0., 0., 0., 0., 0., 0.]])
    assert site_utility(factors, np.ones(8))[0] == pytest.approx(1 / 7)


def test_reference_weight_vectors_are_not_interchangeable():
    assert not np.allclose(NOTEBOOK_WEIGHTS, PAPER_WEIGHTS)
    assert NOTEBOOK_WEIGHTS.sum() == pytest.approx(1, abs=.001)
    assert PAPER_WEIGHTS.sum() == pytest.approx(1, abs=.001)


def test_objective_and_connectivity_checks():
    instance = Instance(coords=np.zeros((3, 2)), free_indices=np.array([0, 1]),
        fixed_indices=np.array([2]), utility=np.ones(3),
        linear=np.array([-2., -1.]), quadratic=((0, 1, .2),),
        neighbors=((1,), (0,)), fixed_neighbors=np.array([1, 0]),
        budget=2, d_max=2000.)
    ok = evaluate(instance, np.array([1, 1]))
    assert ok["feasible"] and ok["energy"] == pytest.approx(-2.8)
    bad = evaluate(instance, np.array([0, 1]))
    assert not bad["feasible"] and bad["isolated"] == [1]


def test_reject_all_zero_weights():
    with pytest.raises(ValueError):
        site_utility(np.ones((1, 8)), np.zeros(8))
