# Registered *before study results*: N20/K5 anchor-reachability sensitivity S0–S2

**Preregistration date:** 2026-10-19 (Philippines). **Status: pre-outcome methodology, not an accepted physical model.**

Parent [Issue #69](https://github.com/carlers/quantum-opt-dashboard/issues/69); study [Issue #70](https://github.com/carlers/quantum-opt-dashboard/issues/70). Authorization: owner explicitly permitted **review-only model audit and preregistered sensitivity experiments**, not correction of historical source, public release of restricted data, model adoption, GitHub merges, production or preview deployment.

## Frozen evidence and controls

**S0 is the immutable historical/source-derived computational control**, not a claim that the underlying data/physics is correct.

- Upstream integrated source branch: [DRAFT PR #68](https://github.com/carlers/quantum-opt-dashboard/pull/68), exact starting commit `29397a69d8e45dab2cf2f635b6adfdc2196f37d9`. Its actual full kernel+geometry and six-kernel precision CI passed at that head. This study must validate *a fresh source execution*, not merely reuse committed expected output.
- Original archived notebook content SHA-256 `08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048`, source lake GeoJSON SHA-256 `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`. The historical 25-cell notebook and 5,417-feature GeoJSON are immutable and not copied into the public PR.
- Exactly 20 **source-ordered** candidate indices, 15 actual marked existing stations and budget K=5. Geometry uses original concave hull (ratio 0.05, allow holes), original threshold Dmax from existing-site max nearest spacing ×1.15; source site IDs/coordinates and original source linear and 12 nonzero quadratic MIQP terms *must be identical* in all scenarios. No new population/WorldPop data, alternative station generation or reweights.
- S0 expected **15,504 total five-site sets**, **1,077 original local one-hop feasible sets**, and complete ordered feasible-set SHA `2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a`, original optimum local `[0,1,3,6,7]`, original objective ≈`−3.3012934918564643`. A software guard `1e-7` for the known energy is strictly a regression check, **not an approved scientific tolerance**. Original exact `MODEL_INPUT` binary SHA can differ by last-bit modes on observed CPUs, *without automatically failing the math*.
- **Independence:** the original notebook emits a 20 × fixed-bit adjacency graph; the [#67](https://github.com/carlers/quantum-opt-dashboard/pull/67) verifier reconstructs **full 20 × 15 direct free/fixed station identities from raw source GeoJSON** along with every free/free edge. S1/S2 must use these **actual** original hull/line/spacing links rather than making up fixed/fixed adjacency or treating every existing station as interconnected.

## Hypotheses fixed before running this study

- **H0:** all variants S0/S1/S2 yield identical feasible choices and the same optimum.
- **H1:** S1 (anchored-component rule) removes at least one S0 admissible five-site set because source one-hop lets a mutually connected group of *selected new sites* have **no edge to any existing station**.
- **H2:** S2 (single connected observed network containing all five new sites and at least one existing station, **no unobserved existing/existing edges**) removes at least one S1 admissible five-site set.
- **H3, descriptive only:** the source's **seven zero-neighbor candidate positions** `[2,4,5,8,11,16,18]` cannot occur in S0/S1/S2; this may reveal generator/constraint tension, **not** a need to delete them from historical data.

Each hypothesis is evaluated directly; if false, report the null result without changing parameters or cherry-picking cases.

## Scenario definitions (no alternative source objective)

Use original source graph, original source raw objective `E(x)=Σa_i x_i+Σ_{i<j}q_ijx_ix_j`, exact `Σ_i x_i=5`; no rounding/weight changes.

- **S0 — source local one-hop:** each selected new site `i` has either an explicit directly observed edge to *any* one of the 15 fixed stations, **or** a selected new-site neighbor. This is the historical source predicate. A selected two-node cycle without any fixed link can pass S0; such a component is not necessarily operationally connected.
- **S1 — fixed-anchored selected-component:** S0 plus **every connected component** in the graph induced by selected new sites must contain at least one new node with an observed direct link to at least one fixed station. Distinct components may be anchored to *different* fixed stations. No fixed/fixed edge is assumed.
- **S2 — one shared directly observed component:** S1 plus in the graph induced by all five selected new sites **and the 15 original fixed sites**, with only observed free/free and free/fixed edges (and **no inferred fixed/fixed edges**), all five selected new nodes must be members of the **same** connected component that includes at least one fixed station. Unconnected fixed stations elsewhere are allowed. This is **a topological counterfactual**, not proof of actual radio backhaul, shore access or validated water currents.

No S3 or additional scenario may be introduced without a separately dated amendment **before** looking at its results. Compute from the same pinned input; do not change selected free candidate universe between scenarios.

## Preregistered primary and secondary metrics

**Primary:** exact number of S0/S1/S2 admissible five-site sets; SHA-256 of every admissible tuple in lexicographic ascending order, encoding decimal local indices comma-separated followed by single ASCII `\n`; optimum subset(s) and `E(x)` evaluated with **original source coefficient hex** under each scenario; absence of feasible alternatives explicitly labeled **empty**, not infinity silently or a made-up solution.

**Secondary:** number of S0 alternatives removed by S1; number of S1 alternatives removed by S2; selected subset's count of new-only components and anchored components; count of S0 sets with no existing anchor in ≥1 selected component; zero-neighbor candidate IDs; how the original winner fares under S1 and S2; alternative-vs-source objective gap computed **only within the unchanged source objective**; exact complete source graph SHA and provenance.

For ties, if `abs(E−E_min)<=1e−9`, retain all minimizers and report the tolerance as algorithmic tie grouping; do not convert that into an environmental tolerance. Report whether a selection uniquely best and do not assume any prospective changes improve real-world water monitoring.

## Testing, stops and interpretation

- **Before comparing outcomes:** run original `scripts/run_n20_reference_notebook.py` in a fresh CI kernel and actual `scripts/n20_independent_geometry_audit.py`; insist original sources and graph match; compare full free/fixed link list with collapsed fixed flags.
- New **stdlib-only** study accepts only independently generated `n20-reference-result.json` and `n20-source-geometry-certificate.json`, validates raw source IDs, output hashes, full graph symmetry and fixed-link positions, and iterates all **15,504** `combinations(range(20),5)` deterministically.
- **Adversarial unit tests:** isolated selected two-node component with no fixed link passes S0 but fails S1; two separately anchored components pass S1 but fail S2; common fixed hub can connect otherwise new-disconnected components under S2; a changed/off-winner edge or forged source fingerprint must fail validation; negative or no-feasible outcomes must still serialize honestly.
- **Hard stops:** unexpected source file/model/geometry SHA, original source S0 count/selection/energy mismatch, missing original fixed identities, non-symmetric free neighbors, invalid link indices, changed historic source equation, hidden or missing original notebook result. Do not “fix” by adjusting connectivity range, candidate list or weights.
- **Numerical variability:** use full precision coefficient hex and recorded input hash; keep standard N20 optimum parity gates, warn about host-level ULP differences already observed. Exact graph and full tuple SHA **must match**, but float64 model-input SHA is a recorded diagnostic, not universal same-host canary.
- **Artifacts:** publish only bounded generated numerical metadata/checksums as ordinary PR CI evidence, with ~14-day retention; do not upload new third-party/owner private raw GIS or survey datasets. Durable custody and public release still require separate owner rights review.
- **No physical claim:** S1/S2 enforce graph predicates under the *same constructed GEOS hull*. They are not empirical communication-link feasibility, real lake transport, globally connected fixed sensor infrastructure, or a replacement deployment specification.

## Research owner decision after the evidence exists

Review evidence for all S0/S1/S2 including a null/empty outcome. Decide whether to **keep and disclose** source S0 as an historical definition, obtain actual fixed-to-fixed communications/topology measurements, or preregister a future physically informed connected-network model. Do not automatically promote whichever scenario selects more sites or has a lower raw objective.

**Next steps:** commit this pre-outcome protocol to a **DRAFT protocol PR**; only then prepare code on a separate child DRAFT study PR and execute real source CI. Update #69/#70 with all outcomes and independent negative controls. No merges, deployment or historic model changes.
