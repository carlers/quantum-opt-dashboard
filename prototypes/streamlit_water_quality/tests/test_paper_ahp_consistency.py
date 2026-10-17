"""Auditable arithmetic for AHP matrices printed in the previous paper.

Source: supplied "QUBO-Based Sensor Placement Framework for Water Quality
Monitoring in Laguna de Bay", page 4, Tables III and IV. The paper is NOT
committed to the repository. Numbers below are manually transcribed; this
fixture does not verify the historical elicitation provenance.

These tests intentionally preserve an observed manuscript discrepancy;
they do not assert that the published weights are eigenvector-derived.
"""
import numpy as np
import pytest

TABLE_III_MAIN = np.array([
    [1, 4, 6, 8],
    [1 / 4, 1, 3, 5],
    [1 / 6, 1 / 3, 1, 3],
    [1 / 8, 1 / 5, 1 / 3, 1],
], dtype=float)
TABLE_III_LOCAL = (
    np.array([[1, 1], [1, 1]], dtype=float),
    np.array([[1, 2], [1 / 2, 1]], dtype=float),
    np.array([[1, 2], [1 / 2, 1]], dtype=float),
    np.array([[1, 1], [1, 1]], dtype=float),
)
TABLE_IV_GLOBAL = np.array([
    0.276095907, 0.276095907, 0.179220150, 0.089610075,
    0.087188181, 0.043594091, 0.024097845, 0.024097845,
])
RI_4 = 0.90  # Standard Saaty random index for n=4.


def principal_priority(matrix: np.ndarray) -> tuple[float, np.ndarray]:
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    major = int(np.argmax(eigenvalues.real))
    lam = float(eigenvalues[major].real)
    priority = eigenvectors[:, major].real
    if priority.sum() < 0:
        priority *= -1
    return lam, priority / priority.sum()


def test_paper_local_ahp_splits_match_its_global_weights():
    # Paper Table III local judgments do yield the Table IV intra-pillar
    # fractions even though the 4x4 top-level priorities do not match.
    main_weights = np.array([
        TABLE_IV_GLOBAL[0:2].sum(), TABLE_IV_GLOBAL[2:4].sum(),
        TABLE_IV_GLOBAL[4:6].sum(), TABLE_IV_GLOBAL[6:8].sum()
    ])
    np.testing.assert_allclose(main_weights.sum(), 1.0, atol=1e-8)
    for group, local_matrix in enumerate(TABLE_III_LOCAL):
        lam, fractions = principal_priority(local_matrix)
        np.testing.assert_allclose(
            TABLE_IV_GLOBAL[group * 2:group * 2 + 2] / main_weights[group],
            fractions, atol=1e-8, rtol=0,
        )
        assert lam == pytest.approx(2., abs=1e-12)


def test_published_main_weights_not_principal_eigenvector_of_table_iii():
    lam, eigenweights = principal_priority(TABLE_III_MAIN)
    reported_main_weights = np.array([
        TABLE_IV_GLOBAL[:2].sum(), TABLE_IV_GLOBAL[2:4].sum(),
        TABLE_IV_GLOBAL[4:6].sum(), TABLE_IV_GLOBAL[6:].sum()
    ])
    np.testing.assert_allclose(
        eigenweights, [0.61697535, 0.22831938, 0.10461009, 0.05009517],
        atol=2e-8, rtol=0,
    )
    assert not np.allclose(eigenweights, reported_main_weights, atol=1e-3)
    assert lam == pytest.approx(4.147126421479674, abs=1e-10)
    assert ((lam - 4) / 3 / RI_4) == pytest.approx(0.0544912672146942, abs=1e-9)
    print("PAPER_AHP_EIGEN " + str({"lambda_max": lam,
          "consistency_ratio": (lam - 4) / 3 / RI_4,
          "eigenvector_pillars": eigenweights.tolist(),
          "published_pillars": reported_main_weights.tolist()}))


def test_paper_consistency_numbers_are_recoverable_from_paper_weights():
    reported_main_weights = np.array([
        TABLE_IV_GLOBAL[:2].sum(), TABLE_IV_GLOBAL[2:4].sum(),
        TABLE_IV_GLOBAL[4:6].sum(), TABLE_IV_GLOBAL[6:].sum()
    ])
    # Mean of componentwise (A @ reported_weights)/reported_weights
    # recreates paper's stated 4.2207, unlike the actual principal eigenvalue.
    estimated_lambda = float(np.mean(
        (TABLE_III_MAIN @ reported_main_weights) / reported_main_weights
    ))
    estimated_cr = (estimated_lambda - 4) / 3 / RI_4
    assert estimated_lambda == pytest.approx(4.2207, abs=5e-5)
    assert estimated_cr == pytest.approx(0.0817, abs=5e-5)
    assert estimated_lambda > max(np.linalg.eigvals(TABLE_III_MAIN).real)
    print("PAPER_AHP_REPORTED_WEIGHT_ESTIMATE " + str({
        "lambda_estimated_from_reported_weights": estimated_lambda,
        "cr_estimated_from_reported_weights": estimated_cr,
    }))
