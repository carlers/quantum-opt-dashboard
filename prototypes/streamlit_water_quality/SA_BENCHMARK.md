# N=20 classical OpenJij simulated-annealing benchmark

**Status:** Isolated research experiment on draft PR #21, stacked on QUBO proof PR #19. Results must be read from the successful CI run; all numerical claims below are design targets until checked in the run log.

## Scientific question and sources

Can a fixed, small-budget *classical* OpenJij `SASampler` find feasible new sensor placements under the same 20-free/15-fixed-site source-notebook constraints that SCIP solves to a certified global optimum? This is a solver-behavior pilot, **not** an evaluation of quantum advantage or a reproduction of the paper's historical SA score.

- The original notebook Cells 6 and 7 use JijModeling, its `instance.to_qubo(penalty_weights=...)`, OpenJij `SASampler`, penalty sweeps and repetitions. **Our QUBO is different:** it is the explicit, separately validated binary-slack formulation in `QUBO_ENCODING.md`. Do not compare sampler landscapes as if their QUBO encodings were verified identical.
- The committed GeoJSON contains 5,417 candidate positions and **15 actually flagged** existing stations. The paper-reported Table V SCIP energy −3.301319 is not an equivalent-input benchmark. Notebook-derived SCIP's certified N20/K5 optimum is −3.3012934918564643; refer to `N20_VALIDATION.md`.
- Published manuscript AHP matrix/priority discrepancies and D2 factor semantics remain unresolved under issue #16. Only **notebook hard-coded weights** are sampled here.

Official external references: [OpenJij SASampler guide](https://tutorial.openjij.org/en/tutorial/001-openjij_introduction.html), [OpenJij Python package 0.12.2](https://pypi.org/project/openjij/0.12.2/). OpenJij's tutorial describes sampling as a stochastic heuristic rather than a method guaranteed to attain global optimality.

## Experiment registered prior to inspecting outcomes

| Setting | Value |
|---|---|
| Solver | OpenJij `SASampler` **classical SA**, pinned `openjij==0.12.2` |
| Source problem | Frozen `N_free=20`, `K_new=5`, 15 actual fixed stations, notebook Cell 2 AHP weights |
| Comparator | PySCIPOpt certified exact MILP of same original objective + independent enumeration of all `C(20,5)=15,504` selections |
| Penalties | Same `P` for squared budget residual and per-site squared connectivity residual with explicit binary slacks |
| Penalty point A | Original notebook Cell 6 row-sum single-flip coefficient heuristic `max_i(|a_i| + sum_j |Q_ij|)`; **not** a global-feasibility theorem |
| Penalty point B | Arithmetic midpoint between A and C; exploratory |
| Penalty point C | Globally sufficient conservative `2B+1`, `B=sum_i |a_i| + sum_{i<j}|Q_ij|`, conditional on original feasibility |
| Independent seeds | `20261018`, `20261019`, `20261020` |
| Sampling | `num_reads=32`, `num_sweeps=300` for **each** of nine penalty×seed trials |
| Computational ceiling | 9 trials × 32 reads = **288 total returned draws**, with bounded CLI limits on reads, sweeps, seed count |
| Sample decoding | Use response `indices` to map *both original and slack variables*; honor `num_occurrences` for weighting |
| Optimum success definition | Original constraints feasible and original *unpenalized* objective within `1e-7` of SCIP optimal energy |

## Independent validation and reporting

`sa_benchmark.py` refuses the comparison unless SCIP reports **optimal** and its numerical energy/selected sites agree with independent exhaustive enumeration. It then checks **every returned encoded sample**, not just the best result, against the canonical expanded QUBO and a separately evaluated *unexpanded* budget/connection squared penalty. It distinguishes:
- Original feasibility: **exact budget** + notebook's **local one-hop connectivity**. This is not a guarantee of global graph connectivity to a fixed station.
- Original/raw MIQP energy (for both feasible and infeasible samples, clearly labeled).
- Full augmented QUBO energy including nonnegative penalties and constant offset. Sampler's raw `response.record.energy` omits the separately stored constant offset, so offset handling is checked explicitly.
- Row-wise number of occurrences, which weights **all reported feasible fractions and averages**. A compressed record is not counted as a single read unless its occurrence count is 1.

**Metrics:** seed-level feasible fraction, feasible/infeasible counts, best/mean *feasible* raw energy, gap to SCIP among feasible results, number of exact-optimum hits, and elapsed wall seconds; aggregated counts, fractions, best/mean raw energies and gaps per penalty. Null best/gap means **no feasible draws**, not zero energy or solver failure. Seeded replay is tested within the same pinned CI environment, not promised across different platforms or later OpenJij versions.

## Artifact contract and replay

From the repo root:

```sh
python -m pip install "numpy>=2,<3" "scipy>=1.11,<2" "shapely>=2,<3" "pyscipopt>=5,<7" "openjij==0.12.2" "pytest>=8"
python -m pytest prototypes/streamlit_water_quality/tests -q -s
python prototypes/streamlit_water_quality/sa_benchmark.py \
  --output-dir /tmp/n20-sa-benchmark \
  --seeds 20261018,20261019,20261020 --reads 32 --sweeps 300
```

The branch's scoped GitHub Actions workflow also exports artifact `n20-openjij-sa-benchmark` (14-day retention):

- `summary.json` — run configuration, SRC hashes, source feature positions, environment and OpenJij versions, SCIP certificate, exhaustive reference, penalty grid and aggregate summaries.
- `trials.csv` — all 9 individual penalty×seed trial summaries, with durations and sample counts.
- `samples.csv` — every sample record including its complete binary string, occurrence count, selected indices, budget/connection indicators, raw and augmented energies. **Infeasible rows retained.**
- `manifest.json` — SHA-256 for each exported file to detect any post-run alteration. Runtime and run identifiers mean byte-for-byte artifacts need not match across machines or replays.

### Interpretation limitations

Three seeds and 288 samples form a **small methodological smoke benchmark**, not a statistically conclusive estimate of algorithm quality. The conservative penalty can make stochastic exploration numerically difficult despite its exact global-minimizer guarantee. If the higher penalty yields fewer feasible samples under this small budget, that is not a contradiction: the proof concerns *global minimizers*, not heuristics. Penalty tuning or larger workloads require a pre-declared follow-up sweep and resource budget. Do not silently increase reads/sweeps after seeing outcomes and report the resulting estimate as unbiased.

The live Streamlit page was not invoked, measured or redeployed. The prior paper's historical SA score does not have verified identical input weights, solver/compiler versions or auxiliary constraints and is **not** used for inferential claims.
