# Source-pinned N50/N100 first SCIP execution receipt — 2026-10-26

**Status:** Review-only, independently inspected CI artifact for draft PR #140. This document describes **one** bounded execution, not a preregistered experiment or demonstration of manuscript/physical-lake parity. Source: original GeoJSON and the existing notebook-derived historical local one-hop formulation, notebook weights, K=5 new stations, all 15 source-marked existing stations fixed. Original notebook, GeoJSON, fixed N20 code and PR #96 are unchanged.

## Execution and source identity

- Source GitHub Actions run: [40300199685](https://github.com/carlers/quantum-opt-dashboard/actions/runs/40300199685), GitHub artifact [12639189458](https://github.com/carlers/quantum-opt-dashboard/actions/runs/40300199685/artifacts/12639189458), retention **14 days**, not a durable archive. Source PR head of this run: `bb186b2b90405b311797ed71d7d07498b6188ef0`.
- Original GeoJSON SHA-256: `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`.
- **Outer artifact ZIP SHA-256:** `3180ccd99651d7646f649e6be4e3bb033c22f134e25dd816279f0236411f5ece`.
- Runtime: Python 3.12.15, NumPy 2.5.4, SciPy 1.18.1, Shapely 2.2.0, PySCIPOpt 6.3.0, Linux 6.17.0-1022-azure x86_64.
- Budgets: SCIP internal 12 seconds per tier; external process-group 75-second watchdog per tier. The SCIP solve-call timing includes LP export/construction; worker wall time includes a separately measured source model rebuild. All below are **single observed measurements**, not scaling benchmarks.

| Measured/scientific attribute | N=50 | N=100 |
| --- | ---: | ---: |
| SCIP solver status | `optimal` | `optimal` |
| Reported relative solver gap | 0 | 0 |
| Original local-model objective | **−3.3012934918564643** | **−3.4910546048016684** |
| Chosen local (0-based free) positions | `[0,1,3,6,7]` | `[0,3,6,52,54]` |
| Corresponding source GeoJSON feature positions | `[5253,2394,1557,47,5409]` | `[5253,1557,47,5328,2530]` |
| Independent exact-K / local one-hop / decoded source objective | pass | pass |
| Source cohort model rebuild, seconds | 0.186118054 | 0.222217378 |
| SCIP solve function call incl. LP export, seconds | 0.015364990 | 0.048762612 |
| Total child-process worker wall, seconds | 0.435767952 | 0.486364429 |
| Emitted binary MILP LP bytes | 23,594 | 109,193 |
| Input model SHA-256 | `dc25c9c9de5b529e6da34ffe806c283e97ad1dc2438c58c1714c139d6d783079` | `ceec0fa95a6f03573983a687f304fc257ea108eaad8d85116289393bb59246bc` |
| Internal result ZIP SHA-256 | `d6eaae0f6a25dd08c784e5234b52dff78762693a8783aeda68a2e63f07d1cde7` | `9ffabeb616820da53bd8c15eb771b1788bdad3faf9788b4bf9a98dbb092287dc` |

## Separate receipt inspection and cross-tier check

The original downloaded artifact was separately opened (ZIP members `index.json`, `scip-n50-*.zip`, `scip-n100-*.zip`) and the SHA-256 chain was recomputed. The original selected bits were recomputed against the serialized IEEE-754 float-hex linear/pairwise coefficients. Cardinality K=5 and **every selected station's** original local one-hop constraint were checked independently of SCIP's own `evaluate` helper. The record's stated SCIP status and gap remain solver-produced; this receipt is **not** an independent certificate of an upper/lower optimality bound.

Additional reconstruction in the observed bundle:

- N50 free source positions are a prefix of N100; all 15 fixed source positions match.
- Every original N50 linear coefficient equals the N100 first-50 coefficient in binary64 hex. All restricted N100 pair coefficients, original fixed neighbor flags, and N100 subgraph edges agree with the N50 tier.
- Padding N50's five selected bits with 50 zero bits yields a **feasible N100 assignment** of exactly **−3.3012934918564643** under the N100 model. This exactly equals the observed N50 original objective.
- The observed N100 optimum is lower by **0.18976111294520415** original-objective units under this common N100 tier model. Its source feature positions are distinct from those selected at N50.
- The common comparison model here is the **N100 tier**, **not** the original 5,417-site paper/master model.

## Limits and next gates

1. PySCIPOpt's `optimal` status and zero reported gap are from the one observed solver execution. Independent witness checking proves original-model feasibility and recomputed objective, **not independent global optimality**.
2. Historical paper AHP/WorldPop D2 differs from the committed notebook's weights and road-proximity D2. The source model is not the manuscript numerical instance; there is no QUBO/QAOA or physical sensor/radio validation.
3. Float64 coefficients and reproducible seed-sensitive stochastic behavior are environment dependent. A single near-instant SCIP result is **not** a statistical runtime scaling conclusion; fixed K and original local graph may also simplify some sizes.
4. Preserve the artifact outside GitHub's 14-day retention under an approved provenance/license policy before claiming durable thesis reproduction. Do not relabel CI reruns as independent stochastic replications.
5. New CI in this PR verifies nested N50-in-N100 objective conservation and both source LP/witness archives on future review runs; confirm its own commit status before accepting.
