# S4 source-only spatial/AHP parameter provenance audit — findings and research gates

**Completed forensic source check:** 2026-10-19 UTC. **Scope:** review-only source-provenance checks, NOT a parameter-sensitivity grid, source-paper exact replication, physical GIS/RF calibration or authorization to rewrite the original notebook/GeoJSON/weights. Tracked by [Issue #73](https://github.com/carlers/quantum-opt-dashboard/issues/73), parent [#69](https://github.com/carlers/quantum-opt-dashboard/issues/69), manuscript-provenance [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16), numerical-policy [#64](https://github.com/carlers/quantum-opt-dashboard/issues/64).

### Evidence timeline and non-blind source context

Original baseline remains unmerged source-derived [DRAFT #68](https://github.com/carlers/quantum-opt-dashboard/pull/68), commit `29397a69d8e45dab2cf2f635b6adfdc2196f37d9`. Historical original GeoJSON SHA-256 `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`; original archived notebook SHA-256 `08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048`. No historical inputs were edited.

The provenance gate **before implementation** was committed in separate [DRAFT PR #83](https://github.com/carlers/quantum-opt-dashboard/pull/83), commit `43dd343d6e7672ade785015fb58ae4519a4e0909`. The child executable baseline audit lives in [DRAFT PR #84](https://github.com/carlers/quantum-opt-dashboard/pull/84). Its first CI run [#39234991248](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39234991248) **failed before original source execution**: a deliberately synthetic test set only D2=8 and mistakenly expected clipping at 1, ignoring D2's small original relative weight. Source-normalized utility was **correctly** ≈0.127; fixing the **test input only** to D2=80 exercised the upper clip. No weights, thresholds, historical source math, study scope or hypothesis were changed. The corrected [CI #39235152085](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39235152085) **SUCCESS**, **11/11** synthetic AHP and missing-data tests, fresh original N20/SCIP from Jupyter kernel, independent raw original GeoJSON geometry reconstruction, and source-data parameter/completeness review.

Evidence [source notebook + independent graph + S4 machine-readable provenance artifact #12178666221](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39235152085/artifacts/12178666221), GitHub retention through **2026-11-02T10:07:52 UTC**. This is a new archive; older owner-saved research bundles do not imply it was saved.

The owner-provided **manuscript DOCX** was examined locally at its uploaded path (SHA-256 `f667995bc2bbf1bee191b5294fc26f366767bc72b78478e547419689b6eaf2be`). This exact manuscript **was not pushed to GitHub nor fed to CI**. Printed manuscript tables quoted below were transcribed by inspection and recomputed programmatically, not obtained from the 5,417-point source GIS. This is **documentary evidence**, not original raw AHP questionnaires.

## Original N20 computation/source parameter checks

| Provenance item | Observed source-verified baseline | Interpretation |
| --- | --- | --- |
| Source selection | 20 original ordered candidate indices, 15 genuinely marked existing, K=5; SCIP `optimal` [0,1,3,6,7], **−3.3012934918564643** | Historical numerical regression only; not physical quality |
| Original feasible K5 region | **1,077** of 15,504 choices, full membership SHA `2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a` | Preserves intended local one-hop rule |
| Concave hull | **0.05**, `allow_holes=True`, strict line containment | Reproduced exactly in Shapely/GEOS; no surveyed shoreline/error estimate |
| Dmax construction | `1.15 × max(fixed nearest-neighbor spacing)` = **9,873.27073466548 m**; raw hex `0x1.348a2a76efb11p+13` | Not a validated radio link budget |
| Original geometric pair checks | 490 candidate-related pairs = 190 free/free + 300 free/fixed; 114 geometrically interior; exactly **11 free/free** and **34 free/fixed** within radius | Source adjacency reproduces independently with the same GEOS hull |
| Nearest original eligible segment's **distance to Dmax** | **25.727322060418373 m**, `0x1.9ba31c74f2800p+4` | Computational threshold *margin* for frozen coordinates, **NOT** RF measurement, confidence interval or justified sweep range |
| Correlation lengths | `Lc=7,500 m`, `Lw=1,000 m`, `β=δ=1` | Manuscript performance paragraph reports them; no measured correlation/current uncertainty |
| Original eight AHP weights | `[0.3671,0.1224,0.2508,0.0502,0.1278,0.0183,0.0476,0.0159]`, sum **1.0001** | Source numerical convention reproduced, not manually normalized to 1 |
| Original GIS factor missingness | **0 of 5,417** source point records missing any of the eight original criterion fields; **0 of 20** original selected candidates missing any | Current source **has complete criterion fields**, so missing-data renormalization does not explain current N20 numerical/paper discrepancy |
| Source utility calculation | `clip(nansum(criteria × source weights)/nansum(weights for available fields),0,1)`; all 20 original utility numerators/denominators/values agree with emitted `MODEL_INPUT` to source-replay regression tolerance | For complete records denominator is original sum 1.0001; behavior with missing factors is coded but not exercised by original committed rows |

### Three **different** AHP main-criterion priority vectors

Owner-provided manuscript printed **Table III** main criteria A/B/C/D pairwise matrix:
```
    A      B     C     D
A   1      4     6     8
B   1/4    1     3     5
C   1/6    1/3   1     3
D   1/8    1/5   1/3   1
```

Deriving the standard **principal right eigenvector** directly from that printed matrix yields `[0.616975355, 0.228319383, 0.104610094, 0.050095168]`, λmax ≈**4.14712642148**, and principal-eigenvector CR (RI₄=0.90) ≈**0.0544912672**. The manuscript instead **reports** λmax≈4.2207 and CR≈0.0817; earlier issue #16 found a way to reproduce these reported values from another *weight-vector calculation*, but the original elicitation and aggregation method remains unverified. Do **not** quietly change the printed manuscript claim to match the eigensolver.

| Source of parent A/B/C/D priority | A | B | C | D |
| --- | ---: | ---: | ---: | ---: |
| **Notebook original** sum of each pair of eight hard-coded weights | **0.489500000** | **0.301000000** | **0.146100000** | **0.063500000** |
| **Manuscript Table IV printed global** eight weights, summed per parent | **0.552191814** | **0.268830225** | **0.130782272** | **0.048195690** |
| **Manuscript Table III derived principal eigenvector** | **0.616975355** | **0.228319383** | **0.104610094** | **0.050095168** |

**Additional issue beyond parent priorities:** the **within-parent subcriteria split** in the notebook is approximately **3:1 (A1/A2), 5:1 (B1/B2), 7:1 (C1/C2), 3:1 (D1/D2)**, whereas the printed manuscript within-pillar tables and final Table IV encode approximately **1:1, 2:1, 2:1, 1:1**. Thus the notebook difference is NOT merely a different A/B/C/D parent vector. Original raw expert pairwise judgments and revision history are needed to decide which are authoritative; no current computation determines that.

**D2 mismatch is unchanged:** The manuscript calls D2 **stakeholder/population exposure** from **WorldPop** (Tables I/II), while the actual GeoJSON and executable N20 notebook contain `d2_road_proximity`. Complete field availability is **not evidence of correct criterion identity**. No original WorldPop processing files or author-provided data mapping were verified.

## Scientifically required decisions before varying source parameters

**Blocked input and sign-off gates:**
1. **GIS shoreline:** an authoritative time-stamped lake/land/islands polygon in a documented projection, rights/license, and independent mapping accuracy for the original source-derived concave hull. Decide separately whether different hull ratios regenerate the original 20 candidate locations or hold candidate positions fixed and only rebuild allowed wireless edges. The two experiments test different scientific questions.
2. **Actual wireless links:** radio-frequency hardware specifications, station positions and antenna heights, line-of-sight/Fresnel obstruction, packet reliability and any existing station-to-station backhaul. Source Dmax=9.87km is generated from original **fixed station spacing**, not demonstrated physical wireless range. The newer optional all-15-existing dashboard network study #78 uses only geometric proxies.
3. **Redundancy/wake lengths:** measured spatial DO/pollutant cross-correlation, hydrology or defensible source model with units/seasonal coverage, and rationale for original Lc=7.5km and Lw=1km; prior [wake audit #82](https://github.com/carlers/quantum-opt-dashboard/pull/82) found the source east–west wake formula orientation-symmetric, not a measured downstream transport operator.
4. **AHP:** original expert elicitation questionnaires, respondent/aggregation method, actual AHP workbook, subcriteria weights and table revisions, alongside data provenance for the D2 road vs WorldPop mismatch. Printed Table III/IV and source notebook are **separately labeled, incompatible** source claims. See #16.
5. **Statistical/experimental design:** preregister *exact physical or documentary justified values* for each parameter family before running it; source snapshots/commit+SHA, whether 20 candidate IDs frozen, upstream missing-data policy, exact N20 K5 exhaustive results, objective-specific energy rather than cross-scale comparisons, pair threshold margins, full graph feasible membership hashes and adverse/no-feasible cases. No tuning parameters to match the manuscript's published SCIP energy.

### Outcome and scope boundary

**This S4 source-provenance audit did not run even one alternative numerical parameter point.** It neither establishes statistical sensitivity bounds nor validates field radios, shoreline, GIS factors, AHP elicitation, hydrodynamics, QUBO scaling, published N=50–2000 results or quantum advantage. It establishes which inputs are source-complete and which assumptions have unsupported physical/provenance semantics.

The historical lake notebook and committed original GeoJSON remain untouched. Parent source branch #68, protocol #83 and evidence child #84 remain **DRAFT/unmerged**. Neither `main`, `preview` nor production has been modified or deployed.

**Next steps:** verify final report HEAD CI green; post owner-friendly decision requests on #73 and #16. When authoritative evidence is obtained, create **a NEW preregistered S4 run protocol** for exactly one family of parameter variations with justified values. Until then, proceed with non-disruptive paper/source-provenance reconciliation rather than inventing uncertainty percentages.
