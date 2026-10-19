# Evidence-based mathematical and scientific claims for the new water-quality dashboard

**Research issue:** [#85](https://github.com/carlers/quantum-opt-dashboard/issues/85). This is a **review-only research contract** stacked on [source S4 #84](https://github.com/carlers/quantum-opt-dashboard/pull/84), [protocol #83](https://github.com/carlers/quantum-opt-dashboard/pull/83) and [baseline source #68](https://github.com/carlers/quantum-opt-dashboard/pull/68). It does NOT ship to the deployed Streamlit app, change the manuscript, approve a revised mathematical model, merge any branch, or imply measurement-backed physical validation.

## Three different kinds of truth

| Level | Requirements | Historical Laguna N20/K5 status | What is allowed to say |
| --- | --- | --- | --- |
| **1. Source computational verification** | Pin original GeoJSON and archived source notebook SHA, 20 original candidate master features, 15 original marked fixed sites and original eight factor names, validate the complete IEEE-754 model manifest, independenty calculate all 1,077 original feasible K5 placements, original objective energy, true SCIP `optimal` and raw-GeoJSON one-hop graph and factor provenance | **PASS** for source-derived **N=20,K=5** historical instance only | “Verified notebook-derived N=20/K=5 computational result.” |
| **2. Historical manuscript reconciliation** | Resolve printed Table III eigenvector vs printed Table IV weights vs source hard-coded weights (including **different subcriterion splits**); identify D2 road vs WorldPop/population; recover original manuscript N20 coefficients and solver environment explaining energy discrepancy | **BLOCKED** — original expert worksheets, GIS processing and manuscript experiment payload absent | No claim of exact paper replication, published input parity or author-approved corrected weights |
| **3. Field/physical scientific validity** | Verified shoreline/islands CRS, actual wireless ranges/antennas/backhaul, risk-factor derivation, water-quality and spatial/current measurements, field-monitor validation and human adviser approval of a replacement model | **BLOCKED** — original geometric and criterion proxies are not field measurements | No claim of viable wireless deployment, validated downstream pollutant transport or optimal real-world lake coverage |

The 2026-10-19 source-only S4 audit [#84](https://github.com/carlers/quantum-opt-dashboard/pull/84) confirms **zero missing eight-factor fields across all 5,417 original records** and the 20 original N20 candidates. This is data completeness of the *provided fields*, not proof that each field is scientifically meaningful. Source `D2=d2_road_proximity`; the manuscript describes **stakeholder/population exposure using WorldPop**. These values must NEVER be silently equated. Original weights sum **1.0001**, and notebook utility uses available-weight normalization. Those are historical facts, not verified original expert elicitation.

The source `Dmax≈9873.27m` derives from 1.15 times existing-station nearest-spacing, **NOT** an observed wireless range. Wake/currents are model proxies as documented in [#72](https://github.com/carlers/quantum-opt-dashboard/issues/72), and the original local one-hop model **allows disconnected clusters**. The optional new all-stations graph [DRAFT #78](https://github.com/carlers/quantum-opt-dashboard/pull/78) is a separate exploratory topology with 17 geometry-derived existing/existing edges and is **not a radio field survey**.

## Executable contract and claims

The scoped Python module `scripts/science_claim_gate.py` consumes **two freshly generated and independently checked internal artifacts**:
1. Original curated notebook `N20_CLEAN_RESULT` from real `scripts/run_n20_reference_notebook.py`, fresh Jupyter/SCIP, independently reverified `verify_result`.
2. S4 source-only provenance report generated from raw GeoJSON via `scripts.studies.n20_s4_parameter_provenance`, with `certify_geometry` regenerated inside the claim gate.

The gate checks immutable historical source bytes, original factored site identities and eight factor names, source-only weight vector and available-weight normalization, 1,077 original one-hop feasible SHA, true solution/energy, independently recomputed geometry graph SHA and verified S4 source-only status. It does **not** accept a supplied `physically_validated=true` flag or `manuscript_reconciled=true` as evidence.

**Output is a bounded JSON research claim certificate** with three statuses: `verified`, `blocked_no_authoritative_inputs`, `blocked_no_field_calibration`. It intentionally offers only the exact allowed display label `verified_notebook_derived_N20_computation`. No executable code in this PR certifies the physical or publication gates, because the requisite evidence does not exist. A future independently governed, source-backed and human-reviewed **new contract version** would be required to make that possible. A generated JSON file, absent authenticated GitHub CI provenance and a human review, is **not cryptographic certification** that a model is scientifically true; files can be forged.

### Raw mathematical objective energy comparability

The module defines a conservative `objective_fingerprint` over:
- Committed source SHA, exact ordered original candidate and fixed master feature positions, projected coordinates, budget, eight factor *identities* and exact binary `float.hex()` weights;
- All exact source `float.hex()` linear energy terms and all source `(i,j,q)` quadratic terms; objective form and source normalization policy.

`compare_raw_energies(a,b)` only permits describing both scores as evaluations of the **same mathematical objective over identically named candidate sites** when these manifests are identical. Merely having the same units, negative scores, a shared source paper or `SCIP optimal` status is insufficient. Even matching mathematical objectives do **not** establish field-scientific superiority or make differences due to changed **feasibility constraints/topology** a change in source scoring function. More-negative source objective under a different G1 candidate pool (or printed Table IV weights) is **not** evidence of better environmental monitoring. Legitimate G0-vs-G1 comparisons require a common separately validated outcome metric (for example measured detection, or preregistered nearest-monitor distance labeled a proxy), not a bare difference of energies from different mathematical functions.

**Cross-host numerical nuance:** the source `float.hex()` objective identity is a bit-exact gate for traceability; an exact digest mismatch may be just one ULP in existing [precision issue #24](https://github.com/carlers/quantum-opt-dashboard/issues/24). For numeric equivalence studies, inspect actual coefficient-level drift with an independently specified tolerance and feasible-set canaries. Do **not** automatically label 1-ULP drift a different physical model. Equally, tolerance similarity does **not** permit silently mixing different site sets or criterion meanings.

## Dashboard integration is a **separate future PR**, not included here

A review-only dashboard patch should eventually:
- Show a plain-language source-only label and a prominent “manuscript / physical validation pending” explanation next to the optimizer; present factor identities (including road D2) and original 15 fixed/20 available/5 chosen, with exact mode and source hashes.
- Display **original / scenario / scientific validity** as distinct user-visible concepts. When changing AHP weights, candidate generation, geometry or topology, register a new manifest, rerun the solver, invalidate old results and report the changed mathematical definition.
- For **Global connectivity**, use only explicit modeled links including independently derived existing/existing edges, with no invented wireless backhaul. Retain original **Local clusters** default and show both modes are modeled RF proxies.
- Provide downloadable evidence with the actual solver and objective certificate, not “paper reproduced”, “validated physical optimal sensors”, “real quantum device” or unsupported precision claims.

This integration must get a **separate explicitly authorized promotion/review gate** from the user for preview/main/production. The current #85 code stays in the isolated *science branch* and must not be imported opportunistically into app/worker/framework code.

## Negative-result and security boundaries

The gate rejects: altered original source SHA/identity; missing or ambiguous original factor names; road-D2 converted to manuscript population semantics; forged sensitivity interval or scientific status; duplicate site IDs or quadratic terms; numeric infinities; mismatched source/S4 model fingerprints; objective-energy ranking attempted on different mathematical functions. Tests include adversarial synthetic certificates, but the **actual** raw source CI is authoritative for baseline mathematical data.

The gate itself is NOT a replacement for cryptographically signed institutional review, peer review, radio validation, data stewardship, or ethical/environmental impact assessment. No user-uploaded scientific data can be declared field-validated by an unreviewed checkbox or arbitrary "evidence provided" string.

**Next steps:** verify exact-head cold-source gate CI and evidence, file results under Issue #85/#73/#16, and separately determine whether physically grounded source inputs can be obtained before any S4 range sweep or model replacement. No original manuscript/notebook/GeoJSON/main/preview/production changes, and no publication or deployment.
