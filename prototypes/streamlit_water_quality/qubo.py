"""Explicit, solver-independent QUBO for the notebook's N-site MIQP.

QUBO energy = original objective + P_b (sum(x)-K)^2
            + P_c sum_i (fixed_i + sum_{j in neighbors(i)} x_j - x_i - s_i)^2.

Each s_i is a nonnegative integer represented by binary auxiliary variables.
Minimizing over those auxiliaries gives exactly one unit of penalty for
each selected site that has no selected/fixed neighbor. Never replace
this with x_i * (1 - fixed_i - sum_j x_j): that expression can become
negative and reward overconnected configurations.

This module is a reviewable QUBO formula, NOT a reimplementation of
JijModeling/OMMX's internal constraint compiler or an SA benchmark.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite, log2
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model import Instance


@dataclass(frozen=True)
class Qubo:
    """Upper-triangular QUBO: E = offset + sum_{i<=j} Q_ij b_i b_j.

    Binary variables b[0:n_free] are the original free-site decisions.
    Remaining variables are nonnegative binary-encoded connectivity slacks.
    """

    n_free: int
    n_variables: int
    coefficients: dict[tuple[int, int], float]
    offset: float
    budget_penalty: float
    connectivity_penalty: float
    slack_variables: tuple[tuple[int, ...], ...]
    slack_weights: tuple[tuple[int, ...], ...]

    def as_index_qubo(self) -> dict[tuple[int, int], float]:
        """Compatible with solvers accepting integer-indexed QUBO pairs."""
        return dict(self.coefficients)


def objective_bound(instance: Instance) -> float:
    """Bound |linear·x + quadratic(x)| for every binary x."""
    return float(sum(abs(float(v)) for v in instance.linear)
                 + sum(abs(float(v)) for _, _, v in instance.quadratic))


def safe_penalty(instance: Instance) -> float:
    """Sufficient *global* penalty if the original constrained problem is feasible.

    For all original x, -B <= E(x) <= B. Any infeasible assignment
    incurs at least one integer squared violation, so P > 2B ensures
    it cannot outrank ANY feasible original assignment after slack
    minimization. Unlike a local flip bound, this is a global comparison.
    It is intentionally conservative and can be poor for stochastic SA.
    """
    return 2.0 * objective_bound(instance) + 1.0


def _validate(instance: Instance) -> int:
    n = len(instance.free_indices)
    if n < 1 or not (0 <= instance.budget <= n):
        raise ValueError("Invalid number of free sites or budget")
    if len(instance.linear) != n or len(instance.neighbors) != n:
        raise ValueError("Linear coefficients and neighbors must match n_free")
    if len(instance.fixed_neighbors) != n:
        raise ValueError("Fixed-neighbor mask must match n_free")
    if any(not isfinite(float(v)) for v in instance.linear):
        raise ValueError("Nonfinite linear coefficient")
    if any(int(v) not in (0, 1) for v in instance.fixed_neighbors):
        raise ValueError("Fixed-neighbor indicators must be binary")
    for i, ns in enumerate(instance.neighbors):
        if len(set(ns)) != len(ns) or any(j == i or j < 0 or j >= n for j in ns):
            raise ValueError("Invalid local connectivity graph")
        if any(i not in instance.neighbors[j] for j in ns):
            raise ValueError("Free connectivity neighbors must be symmetric")
    pairs = set()
    for i, j, q in instance.quadratic:
        if not (0 <= i < j < n) or (i, j) in pairs or not isfinite(float(q)):
            raise ValueError("Invalid free-free quadratic pair")
        pairs.add((i, j))
    return n


def make_qubo(
    instance: Instance, *, budget_penalty: float | None = None,
    connectivity_penalty: float | None = None,
) -> Qubo:
    n = _validate(instance)
    default = safe_penalty(instance)
    pb = default if budget_penalty is None else float(budget_penalty)
    pc = default if connectivity_penalty is None else float(connectivity_penalty)
    if not (isfinite(pb) and isfinite(pc) and pb > 0 and pc > 0):
        raise ValueError("Finite positive penalties required")

    coeff: dict[tuple[int, int], float] = {}
    offset = 0.0

    def term(i: int, j: int, value: float) -> None:
        pair = (min(i, j), max(i, j))
        coeff[pair] = coeff.get(pair, 0.0) + value

    def add_squared_affine(constant: float, linear: dict[int, float], weight: float) -> None:
        nonlocal offset
        offset += weight * constant * constant
        items = sorted(linear.items())
        for i, a in items:
            term(i, i, weight * (a * a + 2.0 * constant * a))
        for z, (i, a) in enumerate(items):
            for j, v in items[z + 1:]:
                term(i, j, 2.0 * weight * a * v)

    # Original objective: no constraints or fixed-site energy constant.
    for i, v in enumerate(instance.linear):
        term(i, i, float(v))
    for i, j, q in instance.quadratic:
        term(i, j, float(q))

    # Equality budget: zero iff exactly K free stations are selected.
    add_squared_affine(-float(instance.budget), {i: 1.0 for i in range(n)}, pb)

    groups: list[tuple[int, ...]] = []
    weights: list[tuple[int, ...]] = []
    next_var = n
    for i in range(n):
        fixed = int(instance.fixed_neighbors[i])
        neighbors = tuple(instance.neighbors[i])
        # feasible slack s_i = fixed + neighbors_selected - x_i
        # is an integer from 0 to (fixed + degree). Reserve enough bits
        # to represent every nonnegative residual, with no gaps.
        max_slack = fixed + len(neighbors)
        bitcount = int(ceil(log2(max_slack + 1))) if max_slack else 0
        indices = tuple(range(next_var, next_var + bitcount))
        magnitudes = tuple(1 << j for j in range(bitcount))
        next_var += bitcount
        groups.append(indices)
        weights.append(magnitudes)
        affine = {i: -1.0}
        for j in neighbors:
            affine[j] = 1.0
        for index, magnitude in zip(indices, magnitudes):
            affine[index] = -float(magnitude)
        add_squared_affine(float(fixed), affine, pc)

    # Keep all original and slack variable indices explicit; the QUBO
    # dictionary may omit zero-weight diagonal entries.
    coeff = {pair: value for pair, value in sorted(coeff.items()) if abs(value) > 1e-14}
    return Qubo(n, next_var, coeff, offset, pb, pc, tuple(groups), tuple(weights))


def best_slack_assignment(instance: Instance, qubo: Qubo, selected: list[int]) -> list[int]:
    """Minimizes connectivity penalty auxiliaries for the specified original x."""
    if len(selected) != qubo.n_free or any(v not in (0, 1) for v in selected):
        raise ValueError("Expected one binary decision per free candidate")
    bits = list(selected) + [0] * (qubo.n_variables - qubo.n_free)
    for i, (indices, weights) in enumerate(zip(qubo.slack_variables, qubo.slack_weights)):
        residual = (int(instance.fixed_neighbors[i])
                    + sum(selected[j] for j in instance.neighbors[i]) - selected[i])
        slack = max(0, residual)
        if slack > sum(weights):
            raise ValueError("Slack binary encoding cannot represent a valid residual")
        for index, magnitude in zip(indices, weights):
            bits[index] = (slack // magnitude) % 2
    return bits


def energy(qubo: Qubo, bits: list[int]) -> float:
    if len(bits) != qubo.n_variables or any(v not in (0, 1) for v in bits):
        raise ValueError("Expected one binary value per QUBO variable")
    return float(qubo.offset + sum(q * bits[i] * bits[j]
                                   for (i, j), q in qubo.coefficients.items()))


def decoded_penalty_energy(instance: Instance, qubo: Qubo, selected: list[int]) -> float:
    """Direct formula, independent of polynomial expansion / slack encoding."""
    if len(selected) != qubo.n_free or any(v not in (0, 1) for v in selected):
        raise ValueError("Expected one binary decision per free candidate")
    base = sum(float(instance.linear[i]) * v for i, v in enumerate(selected))
    base += sum(float(q) * selected[i] * selected[j]
                for i, j, q in instance.quadratic)
    budget_error = (sum(selected) - instance.budget) ** 2
    isolated = sum(
        selected[i] == 1
        and not (instance.fixed_neighbors[i] or
                 any(selected[j] for j in instance.neighbors[i]))
        for i in range(qubo.n_free)
    )
    return float(base + qubo.budget_penalty * budget_error
                 + qubo.connectivity_penalty * isolated)
