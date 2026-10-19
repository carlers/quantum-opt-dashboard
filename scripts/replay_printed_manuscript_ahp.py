"""Independent arithmetic audit of the *printed* manuscript AHP table, not a fix.

The matrix and Table IV subcriterion weights are transcribed from the
owner-supplied paper. This cannot recover original expert questionnaires,
the priority-weight aggregation workbook or published source model files.
Stdlib only.
"""
from __future__ import annotations

from decimal import Decimal
import json

MAIN_PAIRWISE_MATRIX = (
    (1, 4, 6, 8),
    (1 / 4, 1, 3, 5),
    (1 / 6, 1 / 3, 1, 3),
    (1 / 8, 1 / 5, 1 / 3, 1),
)
TABLE_IV_GLOBAL = (
    Decimal("0.276095907"), Decimal("0.276095907"),
    Decimal("0.179220150"), Decimal("0.089610075"),
    Decimal("0.087188181"), Decimal("0.043594091"),
    Decimal("0.024097845"), Decimal("0.024097845"),
)
REPORTED_SCIP_N20 = Decimal("-3.301319")
SOURCE_DERIVED_SCIP_N20 = Decimal("-3.3012934918564643")


def matrix_times(a: tuple[tuple[float, ...], ...], v: list[float]) -> list[float]:
    return [sum(x * y for x, y in zip(row, v)) for row in a]


def calculate() -> dict:
    # Positive reciprocal matrix => Perron eigenvector. Deterministic power
    # iteration is sufficient for this narrow four-by-four printed matrix.
    vec = [0.25] * 4
    for _ in range(10000):
        z = matrix_times(MAIN_PAIRWISE_MATRIX, vec)
        nxt = [x / sum(z) for x in z]
        diff = max(abs(a - b) for a, b in zip(nxt, vec))
        vec = nxt
        if diff <= 1e-15:
            break
    else:
        raise ArithmeticError("Printed AHP principal eigenvector did not converge")
    transformed = matrix_times(MAIN_PAIRWISE_MATRIX, vec)
    lambdas = [a / b for a, b in zip(transformed, vec)]
    lambda_eigen = sum(lambdas) / 4
    pillars = [
        float(TABLE_IV_GLOBAL[0] + TABLE_IV_GLOBAL[1]),
        float(TABLE_IV_GLOBAL[2] + TABLE_IV_GLOBAL[3]),
        float(TABLE_IV_GLOBAL[4] + TABLE_IV_GLOBAL[5]),
        float(TABLE_IV_GLOBAL[6] + TABLE_IV_GLOBAL[7]),
    ]
    # Normalize only for ratios due to tiny printed decimal summation error.
    p = [x / sum(pillars) for x in pillars]
    a_p = matrix_times(MAIN_PAIRWISE_MATRIX, p)
    lambda_published_ratio = sum(x / y for x, y in zip(a_p, p)) / 4
    return {
        "source": "owner-provided paper printed Table III/IV/V, not raw elicitation data",
        "printed_table_iii_principal_eigenvector": vec,
        "printed_table_iii_principal_eigenvalue": lambda_eigen,
        "printed_table_iii_ri_4": 0.90,
        "printed_table_iii_eigenvector_cr": (lambda_eigen - 4) / (3 * 0.90),
        "printed_table_iv_pillar_sums": pillars,
        "published_pillar_ratio_mean": lambda_published_ratio,
        "published_pillar_ratio_mean_cr": (lambda_published_ratio - 4) / (3 * 0.90),
        "source_minus_reported_scip_energy": str(
            SOURCE_DERIVED_SCIP_N20 - REPORTED_SCIP_N20
        ),
        "status": "printed-value arithmetic comparison ONLY; historical provenance unresolved",
    }


if __name__ == "__main__":
    print(json.dumps(calculate(), indent=2, sort_keys=True))
