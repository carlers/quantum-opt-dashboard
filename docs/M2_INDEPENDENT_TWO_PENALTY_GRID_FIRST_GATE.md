# M2 initial 2D λ-budget / λ-connectivity scientific smoke

**Scope:** One pinned historical **N20 K5** source case, 15 original explicitly flagged fixed Laguna de Bay stations, notebook weights and road-based D2, historical **local one-hop** (not all-stations global connectivity). All original notebook, GeoJSON, N20 SCIP certificate and code are left unchanged. This is a **separate scientific draft PR** based on #131, not a new live Streamlit workload.

## Two mathematically independent penalties

The research QUBO is the existing, reviewed explicit-slack expansion:

```
E_Q(b) = E_original(x)
       + lambda_budget * (sum_i x_i - K)^2
       + lambda_connectivity * sum_i (f_i + sum_{j in N_i} x_j - x_i - s_i)^2
```

Each nonnegative integer slack `s_i` is binary encoded, and `x_i` are the first N original candidate variables. This is **not a claim** that the committed `qubo.py` exactly reproduces JijModeling/OMMX's historical internal conversion. An overconnected node never earns a negative penalty. Minimizing over slacks penalizes each selected isolated source station by one connectivity penalty unit. Auxiliary-bit residual costs are preserved **even when the OpenJij sampler does not minimize slack for its sampled original x**.

Separate 3-point axes use (1) the source notebook's Cell 6 maximum-absolute-row-sum **single-flip heuristic**, (2) its midpoint with the source-derived conservative global bound, and (3) the code's sufficient-global-penalty choice `P = 2 sum(abs(original objective coefficients)) + 1`. The sufficient-bound argument is for the original constrained problem **if feasible**, not a theorem about OpenJij convergence; the local row-sum value itself is **not** a universal feasibility guarantee.

The complete **3 × 3 Cartesian grid** tests all nine budget/connectivity penalty pairs, including different values on the two axes. This is not the old diagonal-only setting `lambda_budget = lambda_connectivity`.

## Bounded first CI execution (engineering, not a scientific significance study)

```sh
python -m problems.water_quality.independent_penalty_grid \
    --out /tmp/laguna-2d-penalty \
    --parents 270010001,270010002 --reads 4 --sweeps 40
```

Every one of the **72** attempted samples uses a separately seeded classical OpenJij SASampler `sample_qubo(... num_reads=1 ...)` call. Paired **parent seed blocks** are reused across the nine configurations, but distinct per-read child seeds are derived using `SeedSequence([parent_seed, grid_index]).spawn(reads)`. This avoids the previously observed pseudo-replication from treating `num_reads>1` under one OpenJij seed as independent original placements. Parent blocks are the appropriate prospective resampling unit; the smoke itself performs **no bootstrap, hypothesis test, uncertainty interval, adaptive tuning or winning-setting assertion**.

Every archived sample includes full original+auxiliary bitstring, exact selected source feature positions, penalty pair, parent+child seed and read index, original source objective, original budget and one-hop violations, raw expanded QUBO energy, reported OpenJij energy without offset, best possible same-x slack energy, and the real squared budget/connection penalty components. The code independently validates the polynomial expansion against the unexpanded source expressions and compares any feasible solution with the independently pinned N20 SCIP/exhaustive optimum **−3.3012934918564643**.

Artifacts: `summary.json`, `trials.csv`, `samples.csv`, and SHA-256 checksums. They preserve *infeasible draws*, unselected solutions and all sample counts; no success-only denominator. Repeated executions with identical child seeds are **replays**, not independent statistical replicates. GitHub Actions artifacts last 14 days and are not a durable thesis archive.

## Claim boundaries and next gates

- Classical SA only; **no QAOA, SQA, quantum hardware, quantum advantage, formal proof, field coverage or paper parity**.
- Notebook source weights and D2 road proximity differ from the manuscript's stated AHP and population/WorldPop D2. Historical penalty Table VI arithmetic discrepancies remain unresolved.
- N20 smoke only. Scaling 3×3 auxiliary-slack QUBOs to N50/100+ requires separate coefficient-sparsity, memory/runtime and solver capacity gates; do not extrapolate from tiny CI.
- Next: verify real captured CI samples/penalty coefficients against original source and archive the reviewed reproducibility bundle; then a preregistered seed-block protocol with larger blocks, confidence intervals over parent blocks, and publication-ready 2D *feasibility* and raw-objective figures. Keep a strict distinction between quadratic QUBO augmented energy, original feasible objective and solver status.
- **No auto-run on Streamlit rerenders, no merge or deployment without user authorization.**
