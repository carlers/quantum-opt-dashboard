# First real science ↔ UX integration contract, WITHOUT combining unmerged branches

**Date:** 2026-10-19. **Parent science:** [draft PR #95](https://github.com/carlers/quantum-opt-dashboard/pull/95) (complete original 35-site independent mathematical source graph). **Independent UX:** [draft PR #78](https://github.com/carlers/quantum-opt-dashboard/pull/78) exact reviewed implementation SHA `8752d17372d9d4dd544acbbfd686b4bb45e33f40`. This cross-stack contract is **read-only**: it never imports the UX code into the science PR, merges the two trees, changes an existing PR base or runs a deployment.

## Actual runtime verification being added

GitHub workflow `.github/workflows/n20-dual-checkout-ux-science.yml` checks out two **separate source trees**: the current science branch in the ordinary workspace, and UX #78 at its exact pinned SHA in `_ux_snapshot`. It verifies the SHA rather than trusting a floating remote branch label.

### Source research runtime

Under directly pinned original numerical dependencies, it executes the real original N20/K5 source notebook in a new Jupyter kernel with real SCIP; independently audits raw original 5,417-feature GeoJSON one-hop geometry, eight original AHP criteria with source road-D2, original S4 provenance and the three-level scientific claims. The original notebook's only certified historical computation remains 1,077 locally feasible five-site sets and original optimum `[0,1,3,6,7]`. It then independently constructs **the complete exploratory global 35-site proxy graph** with 15 mandatory fixed and five selected original new sites, including fixed-to-fixed modeled links, using union-find plus an exact rational objective check independently cross-tested against the bounded BFS/int-scaled objective verifier.

### UX runtime

In an isolated Python virtual environment, the pinned **actual UX source code** runs its 4 real `streamlit.testing.v1.AppTest` tests in `test_wireless_ui.py`. These exercise both original local SCIP and exploratory global exact-search modes, state invalidation across changed modes, no fictional global SCIP LP export, and a real Streamlit session/export. Then the UX backend exporter `export_global_reference.py` separately loads the genuine original source data and computes the complete 35-site geometric graph and all 15,504 K5 subsets in its *own* imported UX code.

### New cross-tree attestation (pure Python, review only)

`scripts/studies/n20_dual_checkout_ux_contract.py` consumes **three separately generated JSON outputs**: the science original notebook source, the independent science full-global witness, and the pinned UX's actual global model/solver/export witness. It fails closed unless:

- Original dataset SHA, source original candidate and all **15 fixed station master indices in order**, original fixed-spacing Dmax and each individual graph direct edge agree. Source graph and UX graph use **different canonical hash schemas**, so exact byte equality is checked for edge lists, not falsely asserted for hash strings.
- Source's local one-hop feasible count and SHA equal UX's independent original local reference; all 15 mandatory fixed and K chosen stations have exact same global viable combination set SHA (`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`) and exact 860/15,504 count.
- UX actually reports `optimal_exhaustive` under exact subset enumeration (not SCIP), complete 15,504 combinations examined, 860 feasible, original global selected `[0,1,3,6,7]`, and matching its *own* graph fingerprint. The cross-check independently reruns the **UX's own original binary64 coefficient model** through a separate `fractions.Fraction` optimization oracle and verifies its reported objective is numerically consistent. The UX export is not accepted simply because its recorded SHA/status says `optimal`.
- Original objective criteria/site identities/weights and full score model are preserved. In case of original cross-host last-bit difference in `linear[9,10,17,19]`, the source-like pair is labeled with the **observed posthoc** numeric precision envelope from PR #94; **the two exact score fingerprints remain distinct, cache/result interchange forbidden**. An unreviewed one-ULP change to another source coefficient or changed quadratic/D2/weights must fail, even if the selected sites happen to match.
- Counterfeit model/site/geometry/fixed-node/Dmax/solver status/energy and unexplained difference scenarios fail adversarial unit tests. Current source science certificates retain `manuscript` and `physical` blocked results, even after all mathematical checks succeed.

**All original numerical outputs are research-only and stored as 14-day GitHub CI artifacts, with no new licensed third-party data or manuscript distributed.**

## What this phase still does NOT prove

This is a **cross-repository-tree consistency test** and first limited actual Streamlit AppTest evaluation, **NOT deployment of the independent science attestor into the Streamlit runtime**. The UX backend and Streamlit app remain **entirely on an independently unmerged branch**. Two valid, individually source-verified processes can generate different exact binary64 coefficients on different runners; their exact objective SHA strings cannot be equated. A historical source mathematical optimum, even if independently cross-checked in both engines, is not authentication of an arbitrary future SCIP log or immutable evidence of a current user's controls.

The UX current per-session graph, selected map, JSON/CSV/ZIP and compiled LP have **not** been instrumented to call the independently trusted science verifier before display. The UX `model_fingerprint_sha256` is a source compiled-model digest, not a cryptographic signed session identity. A malicious UI-level supplied graph/status can still be internally consistent. The bridge's `joint_ux_export_status` is **not approval for live export**. AppTest exercises known original modes but does not replace full adversarial forged-score/graph user interface testing after an actual merge/integration is separately authorized.

Physical waterbody island-hole shoreline, measured fixed antenna/backhaul propagation and coverage, sensor power/battery/boat sampling, dissolved oxygen/water currents and environmental model AHP/D2 manuscript parity remain unverified and blocked under Issue #87. Both graph engines use the same GEOS/Shapely concave-hull proxy; a second code implementation is not a second real-world map measurement.

## Follow-on controlled integration strategy for owner review (not yet performed)

1. Review source scientific chain **#68→#83→#84→#86→#89→#92→#93→#94→#95** and independent UX **#55→#77→#78** as separate drafts; review *which repository tree becomes integration base* and whether to transplant only the audited pure scientific verifier behind an explicit backend port. Do not infer a compatible git merge from passing independent tests.
2. After explicit owner approval of that dependency decision, open another DRAFT integrating a trusted backend-compiled model and 35-vertex graph with per-run solver/provenance evidence in Streamlit. Require independent verify-before-render for both modes (source local SCIP's actual MILP/LP/status and global exhaustive graph status), immutable original source SHA and exact current signed/controlled run signature shared across selected sites, map and every JSON/CSV/ZIP artifact.
3. Add real AppTests for tampered actual current model/graph, stale old ZIP/map after mode/weight/K/Dmax changes, missing fixed nodes, timeout status with/without feasible incumbent, altered manuscript D2 or weights, and unverifiable physical/manuscript claims.
4. Run **joint exact-head full pilot regression and source cold scientific gates**, and require research-owner review before merging anything. Never promote preview, main or production, retune source coefficients to force parity, or invent physical model calibration.

**Success definition now:** signed-off observational consistency of two independently executed, pinned mathematical backends and known original two-mode UI AppTests, with explicit label that this is **NOT yet a trusted live unified dashboard**.
