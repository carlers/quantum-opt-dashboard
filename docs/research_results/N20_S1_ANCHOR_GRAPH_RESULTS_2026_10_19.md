# N20 registered S0–S2 graph sensitivity — results and independent replication

**Study result date:** 2026-10-19 UTC. **Status:** completed bounded post-preregistration computational experiment; **NOT** a revised accepted water-quality or wireless communication model.

The hypotheses, scenarios, original source SHA, frozen metrics, all 15,504-set enumeration, and stopping rules were registered **before the first study run** on [protocol-only DRAFT PR #74](https://github.com/carlers/quantum-opt-dashboard/pull/74), commit `37438b0cc7a00a71095ba1a5fffdb3fa66539409`. This executable experiment is in a **separate child DRAFT [PR #75](https://github.com/carlers/quantum-opt-dashboard/pull/75)**. Parent issue [#69](https://github.com/carlers/quantum-opt-dashboard/issues/69), study [#70](https://github.com/carlers/quantum-opt-dashboard/issues/70). Historical source, input data and original objective remain untouched.

## Cold original-source CI result

[Exact study-code CI run #39219858893](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39219858893), commit `91484f659270735da24df1ff18487b6184ca9726`, **completed SUCCESS**. It first passed **16/16** adversarial graph/source-integrity tests, then genuinely executed the original clean notebook in fresh Python kernel with SCIP and all 15,504 source combinations, and then independently reconstructed all original GEOS/GeoJSON spatial edges (11 free/free and 34 free/fixed). Only after both original controls passed was S0/S1/S2 run.

- Source `MODEL_INPUT` SHA observed on this host: `b8cf5457e9c719396c0293407b9697d9bbd56cde6382fe31257122e745e4b4a5`; different known last-bit input SHA modes can arise across hosts, which is a distinct numerical issue #24/#64.
- Independently reconstructed source geometry record SHA: `a013051d2634716be0abd347c49474c650b0ef742c73232089a9cae29e2f10d1`; full original feasible-set SHA: `2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a`.
- **Raw CI evidence:** [GitHub artifact #12170629530](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39219858893/artifacts/12170629530), expires **2026-11-02 08:02:04 UTC**. This contains unchanged original source model JSON, independently reconstructed geometry JSON, and scenario-result JSON; its archive SHA-256 was independently checked from the downloaded bytes as `1b2a1851ad714d6fd283929818bc3df36af3bbe20439783c9bfb09d39659ce98`. Nested study-result JSON SHA-256: `bd8982e6b6b22444f92c829b4158a8d5e026d48d19c657aba1cfbe88d6874b04`. Owner retains a private conversation download option. GitHub retention is short; choose durable private archive if these results will be cited.
- **Independent second implementation check:** separate offline enumeration using direct source JSON coefficient decoding, standalone connected-component traversal and an independent union-find graph with *observed* fixed links recovered **exactly the same** S0/S1/S2 counts, sorted feasible-set SHA and optimum/energies. This corroborates the actual preserved run but still shares the same source model/GEOS-derived graph inputs.

## Preregistered outcomes

| Scenario | Feasible K5 subsets / 15,504 | Full exact ordered membership SHA-256 | Best selected *local* indices | Original unchanged MIQP objective (minimize) |
| --- | ---: | --- | --- | ---: |
| **S0 — original one-hop** | **1,077** | `2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a` | `[0,1,3,6,7]` | `−3.3012934918564643` |
| **S1 — each new-node component fixed-anchored** | **1,077** | `2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a` | `[0,1,3,6,7]` | `−3.3012934918564643` |
| **S2 — all new nodes share one observed new+fixed component** | **110** | `c57711b21d6730a1821560f36041af0c251b637e867fd2097a12233dcc5db5ae` | `[1,3,6,10,19]` | `−2.121029253124326` |

**Same-objective source energy effect:** stricter S2's best original-objective value is **higher (less favorable for minimization) by `+1.1802642387321383`** relative to S0. Do not interpret this as a scientific loss in water-monitoring quality without physical validation of the graph or source utility.

**Full source S0 induced new-only component histogram:** 1 component: **8** feasible sets, 2 components: **95**, 3: **384**, 4: **461**, 5: **129**, summing to 1,077. This is *not* the number of components after allowing existing-station edges. The original S0 selected set `[0,1,3,6,7]` has **4 new-only components**, all 4 individually anchored in S1, but **fails S2**. Among original candidates, seven sites **[2,4,5,8,11,16,18]** are never individually eligible under unchanged original one-hop graph. S1 introduces **0** exclusions; S2 removes **967** of 1,077 S1 subsets. Sample dropped S1→S2 alternatives include `[0,1,3,6,7]`, `[0,1,3,6,9]`, `[0,1,3,6,10]`. No S0→S1 counterexamples existed.

## Hypotheses disposition — negatives are recorded, not hidden

- **H0 (all scenarios identical): NOT SUPPORTED**: S2 differs.
- **H1 (S1 removes at least one S0 solution): NOT SUPPORTED**: **S0 and S1 are exactly the same feasible subset membership** in this frozen source graph, not merely the same score.
- **H2 (S2 removes at least one S1 solution): SUPPORTED in this source-derived study**: 110 feasible versus 1,077, with a different optimum.
- **H3 (seven original zero-neighbor candidates excluded): CONFIRMED** for this source-derived fixed geometry, not a proof those sites should be omitted from candidate generation.

### Initial pre-data CI problem retained

The first experimental run [#39219698054](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39219698054) **FAILED BEFORE running the original source notebook or generating study results** because a synthetic tamper fixture with *twenty* isolated sites failed the validator's legitimate early **seven-original-zero-neighbor** check, rather than its later S0-set-count assertion. The experiment protocol, variants, original source and test assertion objective were **not** changed. We modified only the synthetic test fixture to introduce a connected ring among the 13 non-isolated source IDs, preserving the original seven isolated identities, allowing the test to correctly exercise the full S0 count guard. Rerun #39219858893 passed all 16 checks and both actual source/geometry gates. No failed or inconvenient real-world scenario was discarded.

## Scientific interpretation and remaining blockers

1. **S1 does not “fix” this source instance**: its full membership is identical to original S0. This avoids wasting effort arguing for a mathematically redundant variant. It does not establish real-world communications feasibility or generalize beyond N20.
2. **S2 demonstrates sensitivity to stronger topological requirements**, not that S2 is scientifically appropriate. It assumes **no** existing-to-existing connectivity even though the original GeoJSON does not characterize actual backhaul/radio coverage. Such unmeasured infrastructure could change S2's feasible set substantially. Lake hull-contained straight lines and Dmax proximity are **not** radio link measurements.
3. **Source candidate-pool flaw remains:** 7 of 20 old candidates can never be selected, although all 20 enter the source generation and denominator. The next research [#71](https://github.com/carlers/quantum-opt-dashboard/issues/71) should preregister and compare an eligibility-aware generator, without rewriting the original 20 IDs or retuning after results.
4. **Other original science gaps are untouched**: directional wake symmetry [#72](https://github.com/carlers/quantum-opt-dashboard/issues/72), unsupported hull/Dmax/AHP physical choices [#73](https://github.com/carlers/quantum-opt-dashboard/issues/73), manuscript AHP/D2/SCIP and penalty table [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16), reproducibility tolerance [#64](https://github.com/carlers/quantum-opt-dashboard/issues/64). No published paper, physical lake network, large-N or hardware quantum parity claimed.

**Next steps:** owner/research team chooses what "connectivity" physically means and what direct links/backhaul data exist; do **not** substitute S2 in main. Preregister [#71](https://github.com/carlers/quantum-opt-dashboard/issues/71) candidate-generation design before any comparison, then run separate grid/wake analyses only after their protocols. All existing original and sensitivity PRs stay draft, no merge/deploy/public data release.
