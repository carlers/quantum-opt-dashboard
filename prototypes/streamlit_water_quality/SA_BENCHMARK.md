# N=20 classical OpenJij simulated-annealing benchmark

**Status: VERIFIED** on [GitHub Actions run 39096176060](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096176060) for the independently seeded per-read version. The run passed **26 tests**, the standalone 288-read classical SA benchmark, prior three-scenario SCIP evidence export and both artifact upload steps. This draft PR #21 is stacked on QUBO proof PR #19; nothing is merged or deployed.

### Verified CI observation (2026-10-18)

Each configuration had 3 parent-seed trials × 32 individually seeded reads; samples with **infeasible** original budgets/connectivity are included in the denominator. SCIP's independently certified original MIQP optimum is **−3.3012934918564643**.

| Penalty | P | Feasible / samples | Best feasible raw objective | Best feasible gap vs SCIP | Exact optimum hits |
|---|---:|---:|---:|---:|---:|
| Notebook local row-sum heuristic | 1.0978196676270329 | 67/96 (**69.79%**) | −3.3012934918564643 | **0** | **6** |
| Midpoint exploratory | 12.92646186401367 | 80/96 (**83.33%**) | −3.1020113800145808 | +0.1992821118418835 | 0 |
| Sufficient global penalty | 24.755104060400306 | 81/96 (**84.38%**) | −2.7834182199112294 | +0.5178752719452349 | 0 |

This describes these **predeclared tiny-budget trials** only: the row-sum setting had fewer feasible samples but more exact-optimum hits, and the higher two penalty settings were more often feasible. It does not establish statistically stable solver rankings across larger workloads, other seeds, other source data, or other QUBO conversions.

[Download the verified SA `summary.json`, `trials.csv`, `samples.csv`, and SHA manifest](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096176060/artifacts/12125230062). The archival evidence can expire after 14 days. The companion [SCIP N20 evidence artifact](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096176060/artifacts/12125260030) is also uploaded.



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
| Independent parent seeds | `20261018`, `20261019`, `20261020` |
| Sampling | **32 separate** `num_reads=1` sampler calls per penalty×parent-seed trial, 300 sweeps per call; every call uses a distinct recorded child seed |
| Computational ceiling | 9 trials × 32 reads = **288 total returned draws**, with bounded CLI limits on reads, sweeps, seed count |
| Sample decoding | Use response `indices` to map *both original and slack variables*; honor `num_occurrences` for weighting |
| Optimum success definition | Original constraints feasible and original *unpenalized* objective within `1e-7` of SCIP optimal energy |

## Independent validation and reporting

`sa_benchmark.py` refuses the comparison unless SCIP reports **optimal** and its numerical energy/selected sites agree with independent exhaustive enumeration. It then checks **every returned encoded sample**, not just the best result, against the canonical expanded QUBO and a separately evaluated *unexpanded* budget/connection squared penalty. It distinguishes:
- Original feasibility: **exact budget** + notebook's **local one-hop connectivity**. This is not a guarantee of global graph connectivity to a fixed station.
- Original/raw MIQP energy (for both feasible and infeasible samples, clearly labeled).
- Full augmented QUBO energy including nonnegative penalties and constant offset. Sampler's raw `response.record.energy` omits the separately stored constant offset, so offset handling is checked explicitly.
- Row-wise number of occurrences, which weights **all reported feasible fractions and averages**. A compressed record is not counted as a single read unless its occurrence count is 1.\n- **Per-read seed**: pinned OpenJij 0.12.2 tests initially showed that using `num_reads>1` under one fixed seed produced repeated original placement patterns across reads. The fixed benchmark now constructs reproducible child seeds via `numpy.random.SeedSequence(parent_seed).spawn(reads)`, records each 32-bit child seed and its `read_index`, and issues **one OpenJij read per child seed**. This addresses seed-level pseudo-replication in the benchmark configuration. Shared model convergence can still produce duplicate final placements; identical outcomes are not, by themselves, evidence of improper randomization.

**Metrics:** seed-level feasible fraction, feasible/infeasible counts, best/mean *feasible* raw energy, gap to SCIP among feasible results, number of exact-optimum hits, and elapsed wall seconds; aggregated counts, fractions, best/mean raw energies and gaps per penalty. Null best/gap means **no feasible draws**, not zero energy or solver failure. Seeded replay is tested within the same pinned CI environment, not promised across different platforms or later OpenJij versions. Each trial's **32 sampled states are generated using 32 distinct child PRNG seeds**, rather than assuming a `num_reads=32` call with one seed yields statistically independent draws.

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
- `samples.csv` — every sample record including its complete binary string, `parent seed` + `sample_seed` + `read_index`, occurrence count, selected indices, budget/connection indicators, raw and augmented energies. **Infeasible rows retained.**
- `manifest.json` — SHA-256 for each exported file to detect any post-run alteration. Runtime and run identifiers mean byte-for-byte artifacts need not match across machines or replays.

### Interpretation limitations

Three seeds and 288 samples form a **small methodological smoke benchmark**, not a statistically conclusive estimate of algorithm quality. The conservative penalty can make stochastic exploration numerically difficult despite its exact global-minimizer guarantee. If the higher penalty yields fewer feasible samples under this small budget, that is not a contradiction: the proof concerns *global minimizers*, not heuristics. Penalty tuning or larger workloads require a pre-declared follow-up sweep and resource budget. Do not silently increase reads/sweeps after seeing outcomes and report the resulting estimate as unbiased.

The live Streamlit page was not invoked, measured or redeployed. The prior paper's historical SA score does not have verified identical input weights, solver/compiler versions or auxiliary constraints and is **not** used for inferential claims.
