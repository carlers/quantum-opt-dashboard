"""Tamper and second-engine verification tests for emitted N50/N100 LPs."""
from __future__ import annotations
from copy import deepcopy

import pytest

from problems.water_quality.independent_lp_bounds import audit_structure, check_highs_bound


@pytest.fixture
def synthetic():
    n = 50
    source = {
        "N_free": n, "K": 5, "source_sha256": "synthetic-test-only",
        "free_master_positions": list(range(50)),
        "fixed_master_positions": [500],
        "linear_float64_hex": [(-1. if i < 5 else 0.).hex() for i in range(n)],
        "quadratic_float64_hex": [[0, 1, (0.25).hex()]],
        "free_neighbors": [[] for _ in range(n)],
        "fixed_neighbors": [1] * n,
    }
    rows = [
        "c1: +1 p0_1 -1 x0 -1 x1 >= -1",
        "c2: +1 p0_1 -1 x0 <= +0",
        "c3: +1 p0_1 -1 x1 <= +0",
        "budget: " + " ".join(f"+1 x{i}" for i in range(n)) + " = +5",
    ] + [f"connect_{i}: +1 x{i} <= +1" for i in range(n)]
    lp = ("\n".join([
        "Minimize",
        " Obj: " + " ".join(f"-1 x{i}" for i in range(5)) + " +0.25 p0_1",
        "Subject to", *rows, "Bounds",
        *(f"0 <= x{i} <= 1" for i in range(n)),
        "0 <= p0_1 <= 1",
        "Binaries", " ".join(f"x{i}" for i in range(n)), "p0_1", "End", "",
    ])).encode("ascii")
    return source, lp


def test_reconstructed_full_lp_matches_source(synthetic):
    source, lp = synthetic
    coefficients, rows = audit_structure(source, lp)
    assert len(rows) == 54
    assert coefficients["p0_1"] == .25


def test_independent_highs_bound_recovers_synthetic_optimum(synthetic):
    source, lp = synthetic
    receipt = check_highs_bound(
        source, lp, {"classification": "optimal", "solver_status": "optimal",
                     "solver_objective": -4.75}, seconds=10
    )
    assert receipt["highs_status"] == 0
    assert receipt["highs_primal_objective"] == pytest.approx(-4.75)
    assert receipt["highs_dual_bound"] == pytest.approx(-4.75)
    assert receipt["highs_relative_gap"] == 0
    assert len(receipt["highs_selected_master_positions"]) == 5
    assert receipt["formal_proof_certificate"] is False


@pytest.mark.parametrize("old,new", [
    (b"+0.25 p0_1", b"+0.35 p0_1"),
    (b"budget:", b"fake_budget:"),
    (b"= +5", b"= +6"),
    (b"connect_0: +1 x0 <= +1", b"connect_0: +1 x0 <= +0"),
    (b"c1: +1 p0_1", b"c1: +2 p0_1"),
    (b"Binaries", b"Generals"),
    (b"End\n", b"End\nUNEXPECTED_TRAILING_DATA\n"),
])
def test_all_lp_semantic_changes_rejected(synthetic, old, new):
    model, lp = synthetic
    assert old in lp
    with pytest.raises(ValueError):
        audit_structure(model, lp.replace(old, new))


def test_modified_source_coefficients_or_graph_rejected(synthetic):
    source, lp = synthetic
    changed = deepcopy(source)
    changed["linear_float64_hex"][0] = (-2.).hex()
    with pytest.raises(ValueError):
        audit_structure(changed, lp)
    changed = deepcopy(source)
    changed["free_neighbors"][0].append(1)
    with pytest.raises(ValueError):
        audit_structure(changed, lp)


@pytest.mark.parametrize("classification,status,value", [
    ("feasible_not_proven_optimal", "timelimit", -4.75),
    ("optimal", "timelimit", -4.75),
    ("optimal", "optimal", -10.),
])
def test_unproven_or_forged_scip_claims_never_upgraded(synthetic, classification, status, value):
    source, lp = synthetic
    with pytest.raises(ValueError):
        check_highs_bound(
            source, lp, {"classification": classification, "solver_status": status,
                         "solver_objective": value}, seconds=10
        )
