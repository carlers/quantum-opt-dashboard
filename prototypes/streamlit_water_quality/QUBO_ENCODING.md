# Exact constrained-to-QUBO encoding — validation gate

**Scope:** Development-only mathematical formulation and regression tests;
no OpenJij stochastic benchmarking, no original notebook/data modifications,
and no change to Streamlit's live `plugin-water-streamlit-pilot` branch.

Parent roadmap #2, scientific issue #6, focused issue #18. This work is
stacked above PR #17 (headless N=20 evidence) and uses the original pilot
`model.Instance`, `model.make_instance`, and independent baseline tests.

## Original binary model

The notebook Cell 4/5 objective for `n` free candidate sites is:

```text
minimize  E(x) = sum_i a[i] * x[i] + sum_(i,j) Q[i,j] * x[i] * x[j]
subject to
    sum_i x[i] = K
    x[i] <= f[i] + sum_(j in neighbors(i)) x[j]  for every free site i
    x[i] in {0,1}; f[i] in {0,1} (fixed-station adjacency indicator)
```

The second condition is **local one-hop connectivity**, not global
graph connectivity to a fixed station. It permits a free-only connected
component disconnected from fixed stations; this is a property of the
source constraint, not fixed by this QUBO.

## Explicit exact augmented QUBO

Introduce `s[i]` as an independent **nonnegative integer slack**:

```text
H(x,s) = E(x)
       + Pb * (sum_i x[i] - K)^2
       + Pc * sum_i (f[i] + sum_neighbors x[j] - x[i] - s[i])^2
```

Each `s[i]` is a binary-weighted sum of auxiliary bits
`1,2,4,...` with enough bits to represent every integer up to
`f[i] + degree(i)`. This representation may include values above that
upper bound, but they do not create new zero-residual solutions
for infeasible `x`.

The original `x` bits are indices `0..n-1`; all auxiliary bits follow
in stable free-site order. `qubo.Qubo` stores canonical upper-triangle
integer-pair coefficients, a separate constant offset, original variable
count, auxiliary index groups/weights and explicit penalty multipliers.

For any binary `x`, minimize over slack bits:

```text
min_s H(x,s) = E(x)
  + Pb * (sum(x) - K)^2
  + Pc * number_of_isolated_selected_free_sites(x)
```

Here an isolated selected free site means it has neither a selected
free neighbor nor adjacency to a fixed station. This equivalence is
asserted via independent **full auxiliary-bit enumeration** on
the tiny reference case, not merely by evaluating one hand-chosen slack
configuration.

**Avoid the tempting but incorrect shortcut**
`Pc * x[i] * (1 - f[i] - sum_neighbors x[j])`: with multiple
selected neighbors its value may become negative, **rewarding**
overconnectivity and changing the objective.

## Sufficient global penalty / relationship to notebook

Let `B = sum_i |a[i]| + sum_(i,j) |Q[i,j]|`. Then
`-B <= E(x) <= B` for every binary assignment, including infeasible
ones. If at least one feasible original assignment exists and both
`Pb > 2B` and `Pc > 2B`, **every global QUBO minimizer has a
feasible original x**, because at least one integer budget or connectivity
constraint residual contributes one squared penalty. The default
`2B + 1` is a conservative global guarantee, not an optimized annealer
parameter. For infeasible instances there can be no feasible original
answer regardless of penalty magnitude.

Notebook Cell 6 defines an alternative `P_min` row-sum/single-bit-flip
bound and performs a penalty grid search with JijModeling/OMMX-to-QUBO
conversion. That **local search heuristic is not asserted to imply the
same global guarantee** or the same auxiliary encoding. Differences in
QUBO variable count, offset, or sampler landscape from JijModeling's
historical compiler are expected until its actual converted QUBO is
available for numerical comparison.

## Automated checks

Run in a Python 3.12 environment with NumPy, SciPy, Shapely and pytest:

```sh
python -m pytest prototypes/streamlit_water_quality/tests/test_qubo.py -q
python -m pytest prototypes/streamlit_water_quality/tests -q
```

- Enumerates **all 2^8 full QUBO assignments** for a deterministic
  three-free-site instance and **all auxiliary assignments for each x**.
- Tests exact global optimum and per-original-assignment penalty parity,
  independently of the QUBO expansion.
- Rejects the negative-reward connectivity shortcut, unsupported penalty
  values, and malformed inputs, including the zero-neighbor case.
- Tests N=20/K=5 against the independent frozen notebook-weight SCIP
  solution **−3.3012934918564643**, selected local sites
  `[0,1,3,6,7]`; checks selected-site energy and representative
  infeasible subsets, including a full `C(20,5)` feasibility/penalty
  comparison.
- Existing upstream PR #15/#17 tests retain independent SCIP optimality
  and cold notebook instance coefficient checks.

**Limits:** A QUBO exact global minimum theorem does not imply that
finite-time stochastic simulated annealing finds it. Next stage requires
recorded `openjij` version, independently seeded repeated runs, per-run
budget/connectivity feasibility, raw-objective energy and gap to SCIP,
and a bounded sampling/penalty sweep with time/compute budgets. Do not
report a single favorable stochastic run as solver equivalence.
