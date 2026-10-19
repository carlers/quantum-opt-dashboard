# Preregistered Laguna de Bay G0–G1 candidate-generation sensitivity — completed result

**Date:** 2026-10-19 UTC. **Status:** source-derived controlled computational study, **not** a corrected historical model, physical radio validation, or adviser-authorized adoption. Research [#71](https://github.com/carlers/quantum-opt-dashboard/issues/71), parent [#69](https://github.com/carlers/quantum-opt-dashboard/issues/69).

## Provenance and chronology

The immutable **pre-outcome** hypothesis, tie/stop/coverage and source-identity protocol was committed on [DRAFT PR #79](https://github.com/carlers/quantum-opt-dashboard/pull/79) at `8aa4d0114c64efe21007a344c9acc3bee086c0bd`, *before* experiment code or outcome. The separate experiment is [DRAFT PR #80](https://github.com/carlers/quantum-opt-dashboard/pull/80), stacked on #79→source-only science #68, **not on the dashboard UX PR**.

The original committed **5,417-point GeoJSON SHA-256 `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`** and original historical notebook SHA-256 `08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048` were verified and **not modified**. The 15 genuine fixed-station original feature positions, N20/K5, original hex target=10,000, snapping, weights with source `d2_road_proximity`, farthest-first behavior, GEOS hull ratio 0.05, Dmax from fixed spacing×1.15, Lc/Lw, redundancy/wake expression and source local one-hop constraint were all fixed.

**Observed CI:** [initial source + 11 adversarial tests #39229988782](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39229988782) success; **[independent-certifier run #39230401305](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39230401305) success** at code SHA `aec9994a546571485ff543ad3b6c318844f0f804`. Second workflow actually cold-executed original notebook+SCIP, independently verified original GeoJSON graph, ran new G0/G1 generator, **independently** reconstructed both graphs via source GeoJSON with `math.hypot`, enumerated all 15,504 K5 choices in a separate script, and ran **two additional SCIP optimizations**, with SciPy `cdist` coverage checks independent of the study's `cKDTree` metric calculation. All agreed. Eleven adversarial tests pass. This is a second computational implementation over the **same physical source data/hull**, not independent field validation.

[Raw original notebook, geometry, G0/G1 comparison and independent SCIP/coverage certificate artifact #12176648487](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39230401305/artifacts/12176648487), scheduled to expire **2026-11-02 09:29:40 UTC**. The owner separately previously confirmed saving the two older research archive packages; that confirmation does **not** imply this new CI artifact was saved.

## Frozen scenarios

**G0 source historical:** select 20 original snapped, nonfixed source master points via original farthest-first process seeded by all 15 fixed sites. Wireless one-hop eligibility is checked **after** candidate selection. G0 IDs reproduce exactly `[5253,2394,1894,1557,3225,4623,47,5409,3922,2408,2694,4136,2567,1164,4973,4537,2726,968,16,1762]`.

**G1 direct-fixed eligibility counterfactual:** from **the identical** hex-snapped, deduplicated nonfixed original source candidate pool, first retain only sites with ≥1 **modeled direct** fixed-station link within the original Dmax and unobstructed GEOS lake LineString. Then run **the identical** original farthest-first selection algorithm/tie rule on that restricted pool, with no utility-based re-ranking, generator retuning or change to the source objective. Exactly **4,485** unique snapped sites survived this eligibility filter, enough for the specified 20. Chosen G1 master positions `[5253,2394,1557,1893,4594,3466,47,3778,2408,2566,2694,1164,4269,5358,4973,4424,4537,968,1762,9]`.

G1 explicitly sacrifices all *relay-only* potential candidate locations with no direct fixed contact, **even though the historical local-one-hop rule could allow them** when connected to a selected new site. G1 is not a replacement network standard.

## Full exact N20/K5 results — source objective minimized

| Metric | G0 historical | G1 prefiltered counterfactual |
| --- | ---: | ---: |
| Generated candidate sites | 20 | 20 |
| Selected new-site local positions with NO allowed one-hop neighbor | **7**: `[2,4,5,8,11,16,18]` | **0** |
| Local-mode feasible K5 subsets out of **15,504** | **1,077** | **15,504** |
| Sorted feasible-member SHA-256 | `2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a` | `bf8b7b0a7c032a256220e431fff9fe03c1fdf4dbd6bc5df147c70e1d13b80712` |
| Source modeled direct new/fixed edges | **34** | **49** |
| Source modeled direct new/new edges | **11** | **17** |
| Best selected NEW original feature IDs | `[5253,2394,1557,47,5409]` | `[2394,1893,4594,3466,47]` |
| Exact source-formula objective of selected optimum | **−3.3012934918564643** | **−3.5442206422431903** |
| Independent SCIP status | `optimal` | `optimal` |

**IMPORTANT:** By G1's prefilter definition every candidate has ≥1 direct existing-station link, so **all 15,504 K5 choices automatically satisfy the local one-hop constraint**. The increased feasible count is an algebraically expected consequence of the filter, **not empirical evidence of better radio deployment**. The lower (more negative) G1 objective uses **different source site identities**, so it cannot be interpreted as an improvement in lake monitoring efficacy without validation of the factor layers, model objective and site suitability.

## Independent spatial-coverage trade-off (metres, across ALL 5,417 committed source points)

These are mathematical **nearest-monitor distance proxies**, not detection delay or hydrological risk coverage. Both comparisons include the original **15 fixed stations** and explicitly distinguish 20 *proposed candidate* stations from five *installed optimal new* stations.

| Coverage set | Metric | G0 | G1 | Consequence |
| --- | --- | ---: | ---: | --- |
| 15 fixed + **20 generated candidates** (hypothetical, not all installed) | Mean nearest distance | **2,303.666 m** | **2,273.414 m** | G1 mean ≈30.252 m lower |
| 15 fixed + **20 generated candidates** | Maximum nearest distance | **4,750.906 m** | **5,013.696 m** | G1 worst ≈262.790 m farther |
| 15 fixed + **five installed optimal new sites** | Mean nearest distance | **3,084.278 m** | **3,176.676 m** | G1 mean ≈92.398 m farther |
| 15 fixed + **five installed optimal new sites** | Maximum nearest distance | **7,996.217 m** | **9,126.976 m** | G1 worst ≈1,130.759 m farther |

**Why this matters:** If one only measures the spread of all 20 generated candidates, G1 can appear slightly better on mean distance. But the physical deployment budget is only **five** new sites, and its actual selected five have a larger nearest-monitor mean and worst distance. These are not optimized by the current source objective, which is based on the original eight criteria and redundancy/wake penalty. A lower model energy therefore need not imply better uniform lake coverage.

## Preregistered hypotheses disposition (including negative/mixed findings)

- **H0 same 20 sites, coefficients and result:** **NOT supported**; site IDs and optimum differ.
- **H1 fewer unreachable candidates in G1:** **supported**, 7 → 0, conditional on the original geometry.
- **H2 more K5-feasible subsets:** **supported algebraically**, 1,077 → 15,504; this is built into G1's direct-fixed requirement, not independent monitoring performance evidence.
- **H3 greater candidate-pool nearest-monitor distance (max and mean): MIXED.** G1's candidate-pool maximum increases by ≈262.790 m, but its candidate-pool **mean decreases** by ≈30.252 m. The original pre-outcome text mentioned both maximum and mean and also called the direction uncertain; we **do not rewrite the preregistration** to erase this conflicting mixed result. At the **five installed** site level, both mean and maximum increase.
- **H4 distinct five-site optimal master IDs:** **supported**, original and alternative site sets differ.

## Review, safety and further decisions

The source connectivity is deliberately local one-hop wireless and remains scientifically intentional. G1 direct-to-fixed prefilter is **stricter** than the original relay-permitting constraint, not a correction required by the notebook. Both use a **water-polygon+Euclidean distance proxy** for potential wireless lines, not physical radio surveys, line-of-sight clearance, antenna heights, actual existing-station backhaul, telemetry or source lake environmental sampling. Weight-source ambiguities and paper Table IV/D2/SCIP mismatches [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16) remain unresolved. Current two-mode dashboard [DRAFT PR #78](https://github.com/carlers/quantum-opt-dashboard/pull/78) is a **separate optional feature** and is not modified or deployed by this study.

**Recommendation:** Keep G0 as the immutable historical computational fixture. Retain G1 as a negative-and-positive scientific design sensitivity: it guarantees candidate direct eligibility but may worsen worst-case spatial coverage at actual K=5. A future scientifically motivated generator needs a preregistered joint coverage/access/risk/relay objective and independent hydrology/radio data. Don't retroactively choose thresholds or pool weights after seeing this comparison.

**Next steps:** research owner reviews source tradeoffs and shares any physical direct-link and lake-risk priors; preregister a *new* G2 protocol if a coverage-aware multi-objective generator is desired (do not silently extend this G1 study); continue separate wake-algebra #72 and spatial uncertainty #73 research; preserve artifact before Nov 2 if future thesis evidence is needed. Historical notebook, GeoJSON, main, preview, production, and all parent research PRs stay unchanged. **No merge/deployment/public release authorization.**
