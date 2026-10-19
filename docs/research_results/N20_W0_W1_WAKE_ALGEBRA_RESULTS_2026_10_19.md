# N20 source wake W0/W1: posthoc-aware mathematical and numerical audit

**Completed:** 2026-10-19 UTC. **Outcome:** original source-based wake has orientation-symmetric east–west pair alignment; removing it changes energy but does **not** change the optimal five new stations in the frozen N20/K5 scenario. **NOT** evidence of physically validated downstream lake currents, and **NOT a blind preregistered discovery**.

## Scientific provenance and prior knowledge

Owner authorized a **review-only original source scientific-model audit** without rewriting the source notebook, 5,417-point GeoJSON, mathematical base model, source manuscript or deploying any app. This study is tracked by [issue #72](https://github.com/carlers/quantum-opt-dashboard/issues/72) and [umbrella #69](https://github.com/carlers/quantum-opt-dashboard/issues/69).

The pre-executable controlled protocol was committed first on separate [DRAFT PR #81](https://github.com/carlers/quantum-opt-dashboard/pull/81) at `2ca9c312f1592535f81dfbe19a5fae4bd02c9343`. Executable, postprotocol source study is on separate [DRAFT PR #82](https://github.com/carlers/quantum-opt-dashboard/pull/82), both stacked on scientific source [#68](https://github.com/carlers/quantum-opt-dashboard/pull/68), not the dashboard UX or staging branches. **An earlier provisional adviser-style forensic memo** [#65](https://github.com/carlers/quantum-opt-dashboard/pull/65) had already noted that the wake-off scenario preserved selection and the value ≈−3.302471. Consequently the source W1 replication here is an independent **reproducibility** control of a known exploratory result, not fresh independent statistical confirmation. No new W1 result was concealed or selected after looking at this run.

Original raw source GeoJSON SHA `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`; original archived notebook SHA `08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048`. Fixed N20 free site IDs, 15 marked existing stations, original eight source factors including `d2_road_proximity`, 20+15 original positions in EPSG:32651, original lake hull `ratio=0.05`, Dmax from fixed spacing × 1.15, K=5, Lc=7,500 m, Lw=1,000 m, β=1, and local one-hop constraints unchanged.

## Formula inspection: what “directional wake” actually computes

In the source's ordered combinations over all 35 available station positions, for a positive pair distance `d` and `c=(x_j−x_i)/d` clipped to [−1,1], it adds:

```
fwd = exp(−d/Lw) * c   when c > 0.7071, else 0
back = −exp(−d/Lw) * c  when −c > 0.7071, else 0
wake = fwd + back
```

This is exactly `exp(−d/Lw) * abs(c)` for `abs(c) > 0.7071` and 0 otherwise. The threshold is **strict**: at exactly ±0.7071 the contribution is zero. Reversing the east–west pair direction changes `c→−c` but not the wake, proving the original unordered pair contribution is **orientation-symmetric**. Positive wake penalizes qualifying east–west aligned pairs regardless of which endpoint is more easterly. Synthetic 11-test suite covers both signs, threshold boundary, near-threshold, north/south, invalid zero lengths, and the distinction between new/free pair penalties and free/fixed linear contributions.

This result is algebra, not experimental calibration of Laguna de Bay circulation. A signed/directional advective transport model or temporally varying lake currents **was not tested**. The notebook's original “directional wake” description should be qualified as an **east–west alignment proxy** until empirically justified. Do not silently change the source/paper's historical equation or claim classical OpenJij simulations are quantum hardware.

## Actual source N20/K5 results

The first exact executable-code [GitHub CI #39232910850](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39232910850) completed SUCCESS. Eleven/eleven adversarial tests passed. Original historical N20 notebook ran in a **fresh SCIP kernel** with original source model-input SHA and returned `optimal`; the original **raw GeoJSON** free/free and free/fixed source graph was independently certified: 11 direct free/free edges, 34 direct free/fixed edges, 1,077 original feasible five-site subsets, SHA `2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a`. Only after that historical canary passed was the W1 comparison accepted.

Each W0/W1 scenario separately recomputed the **entire original 35-station pair loop and free/fixed linear contributions**, not just posthoc subtraction from rounded coefficients. The original objective coefficients match fresh source to the prior numerical regression tolerance, and a **second separate exhaustive K5 enumerator and a new PySCIPOpt MILP for EACH scenario** independently reproduced the optima and all feasible-set membership.

| Registered frozen metric | W0: historical δ=1 | W1: wake disabled δ=0 |
| --- | ---: | ---: |
| All N20 K5 subsets examined | 15,504 | 15,504 |
| Source local one-hop feasible K5 subsets | **1,077** | **1,077** |
| Complete sorted feasible K5 SHA | `2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a` | **identical** |
| Optimal local new-site positions | **[0,1,3,6,7]** | **[0,1,3,6,7]** |
| Energy *under each scenario's own objective* (minimize) | **−3.3012934918564643** | **−3.302471040188822** |
| Nonzero new/new quadratic energy terms | **12** | **6** |
| Independent solver | `PySCIPOpt optimal` | `PySCIPOpt optimal` |
| Top-10 feasible five-site set overlap | **10 / 10** | **10 / 10** |

For original winning selection, W0 − W1 = **+0.0011775483323579472**, the source-model positive wake penalty on that selection. **27** original source free/fixed and **9** new/new *geometry-passing interactions* have nonzero positive wake. Note the wake contribution count is across *all candidate pairs*, not that nine nonzero new/new interactions simultaneously occur in the selected five sites.

**Interpretation:** Replacing the source wake with zero lowers the winning energy by about 0.00118 while leaving the winning *locations* unchanged in this fixed N20/K5 instance. This is a different objective, so a numerically more negative energy is **not** an improvement in physical water-quality observations. Same top-10 membership does not imply identical ordering of the ten combinations. The source's original top-one vs second score gap is larger than this one energy difference, but **this does not bound hydrodynamic data or AHP/model error**.

The numerical study only concerns the **historical candidate pool G0**; the separate [G1 generator sensitivity #80](https://github.com/carlers/quantum-opt-dashboard/pull/80) changes candidates and scores and is **not** combined here. Likewise the later dashboard [global wireless topology PR #78](https://github.com/carlers/quantum-opt-dashboard/pull/78) changes graph constraints and is not merged into this wake analysis.

## Explicit limitations and what must NOT be claimed

- Orientation symmetry of the original pair formula **is proven mathematically**. Real lake-current directionality is **not represented or calibrated** by this proof. No measured current velocities, seasonal hydrodynamics, inlet/outlet flows, transport lag, pollutant monitoring detections or fisheries field outcomes were available to validate a downstream penalty.
- The lake contour is the original Shapely/GEOS concave-hull proxy, not an independent shoreline survey; original factor AHP/D2/manuscript SCIP provenance #16 remains unresolved.
- The original source notebook and GeoJSON are **immutable historical evidence**; nothing in this study licenses replacing them with W1 or an inferred real-current model.
- The second SCIP verifier is algorithmically separate but consumes the same source data and GEOS derived geometry; this is **computational corroboration**, not field replication.
- An empirical directional **W2** is **blocked** pending user/adviser-supported current-data sources, units, seasonal variation and an explicit hydrodynamic objective; if those exist, preregister a *new* scenario before model output. No inventing upstream/downstream directions from simple x-coordinates.

## Source artifacts and next actions

Original source/geometry plus full W0/W1 source coefficient manifests and second SCIP certificate in [CI evidence artifact #12177937488](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39232910850/artifacts/12177937488), short GitHub retention expires **2026-11-02T09:49:42Z**. Owner previously confirmed saving **two earlier evidence archives**, which **does not automatically preserve this new study artifact**. The final report commit should trigger a new exact-head rerun; quote the new artifact and exact CI once verified.

**Next steps:** verify final PR #82 exact-head CI, record verified study in issue #72/#69 and the roadmap, choose whether to pursue physical lake-current sourcing before any W2, or preregister separate spatial/AHP uncertainty research #73. No source model, paper, merged branch, preview or production changes permitted without separate explicit owner approval.
