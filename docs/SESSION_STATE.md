# First SCIP selection feasibility and solver provenance trust-boundary audit — 2026-10-20

**New review-only UX science branch:** `science-scip-replay-first-run-feasibility-threat-audit`, child of unmerged original LP separate-process study DRAFT #99 at `028fcb32dcb45c23ddc5e835e5dbc508803c42d2`, separate original source independent science ancestry #96. No original notebook/GeoJSON/archived manuscript or app/source model/SCIP compiler modifications. Existing UX independent runtime model gate and LP structural checks unchanged.

**Concrete science integrity flaw fixed:** prior `check_independent_process_receipt()` required original first SCIP selection to have exactly optimal binary64 rational energy and K sites, but independently checked **only second child** selection's source local graph. On actual original N20 site geometry with synthetic exactly flat objective, a counterfeit FIRST K5 infeasible set has same score 0 and could pass as optimal. New independent `_source_local_feasible` requires original one-hop source connectivity for **BOTH** chosen sets before score comparison. New original first SCIP metadata checks require `feasible, budget_ok, connectivity_ok` true, correct `num_selected`, no `isolated` sites, and finite converged optimal `gap <=1e-6`. Parametrized adversarial original-source tests forge first/second disconnected exact tied-score K5, first-run gap NaN/negative/0.5/missing and falsified original metric fields. These are artificial adversarial perturbations, not historical source data edits. Full threat model and future external signature decision criteria in `docs/research_protocols/SCIP_FIRST_RUN_TRUST_BOUNDARY_2026_10_20.md`.

**Status:** code/tests/protocol created pending new review-only DRAFT and exact-HEAD all four CI. The true 3,516-byte original LP, separate second SCIP process, first and second source mathematical optimum remain original research scope, not authenticated host/SICIP binary/first actual process log or third-party signed solution. Do **not** add an untrusted cryptographic signer or automatically integrate a second process into interactive Streamlit. Original D2-road vs paper WorldPop population/AHP and field RF/backhaul/DO/current/shoreline remain BLOCKED.

**Next:** open DRAFT PR child #99, verify new genuine SCIP replay tests plus full live-app Streamlit pilot, unified dashboard and pinned original source scientific triple-checkout. Fix only observed failures on this review branch; record exact-HEAD evidence and issue #91/#88 comments. No merges/rebases/deploys or original manuscript/file changes.

---

# Independent second SCIP process on emitted original N20 LP verified — 2026-10-20

**Review-only [DRAFT PR #99](https://github.com/carlers/quantum-opt-dashboard/pull/99)** child of unmerged SCIP LP structure DRAFT #98 and UX runtime gate #97, **separate** original source science chain through #96. No original notebook, archival DOCX, 5,417-record GeoJSON, source coefficients or main/preview/production changes; no merges or deployments.

New `scip_lp_reexecution_worker.py` independently loads ACTUAL source N20/K5 original SCIP-emitted LP bytes in a separate Python `-I` PySCIPOpt process; fresh `readProblem`, `optimize` returns independently reported model SHA, 20 selected binary sites, pair binary consistency and SCIP status/primal/dual/gap. Parent `scip_lp_reexecution.py` checks actual LP SHA+structural certificate and true original compiled source local N20 exact binary64-rational enumerated objective and separate process bounds; refuses forged child and upstream status, model SHA, false selected vectors, source neighbor changes and trust upgrades. Experimental only — not installed into Streamlit run-path, not cryptographic remote attestation of first SCIP process, no authenticated original branch-bound log/dual proof. `export_scip_reexecution_reference.py` writes both literal original LP and independent process receipt, GitHub CI artifacts 14-day.

**Verified initial executable + workflow HEAD `d25931515de2bee497608284fcc7d282cb38aef0`:** [dedicated #39406682562](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39406682562) **SUCCESS 21/21 tests**, fresh original actual LP+independent SCIP `optimal` second selected `[0,1,3,6,7]`, separate reported **primal=dual=-3.301293491856464**, **gap=0.0**, original first status also `optimal`. Original LP SHA `283b3b373499ebde663a8614ca5049f5a3a425ba40e6073a0d3b0fce011d027b` (3,516 bytes), PySCIPOpt 6.3.0/Python 3.12.15, 32 binaries. [Pilot #39406682565](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39406682565) **SUCCESS 121 tests**, [unified #39406682568](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39406682568) **SUCCESS**, [original source triple-checkout #39406682564](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39406682564) **SUCCESS 24 targeted tests + genuine original cold source notebook/SCIP/raw GeoJSON/S4 and independent all-fixed full graph**. Historic local K5 feasible 1,077 vs separate exploratory global K5 860/15,504, viable set SHA `3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`, chosen `[0,1,3,6,7]`. Source & UX score SHA happened to be `8536a3db...` in this run; `2b238848...` from earlier runs is a different exact source model identity.

**Real retained evidence:** [two-file LP+receipt artifact #12256857555](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39406682562/artifacts/12256857555) (ZIP SHA `956390f04b13114024bb0b57cd1372325e88eb8b290af52219943fa5b5993c1c`, expires Nov 3 10:16:22 UTC); original LP SHA above and JSON SHA `9f5581ab73b3cd49a620d88d95ecd91c773529e0dda309b97728c1e6596c3b26`. Independently verified/downloaded; [source four-JSON artifact #12257387273](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39406682564/artifacts/12257387273) ZIP SHA `e9f55439f69be3a381befe632c7cc8af490e40a81f9b0c1fd3df3fc392d61675`, expires Nov 3 10:17:02 UTC, separately downloaded/checked.

**Important:** after this evidence, docs-only commits change the PR head and exact-HEAD CI must be separately checked before declaring final green. Full method, hash/protocol, security/physical limits in `docs/N20_INDEPENDENT_SCIP_PROCESS_REEXECUTION.md`. Research source-only computational verified; published expert AHP/D2 WorldPop reconciliation and actual lake RF/backhaul/DO/current physical calibration remain BLOCKED (#87). Need independent threat-model review before any actual per-user second-process runtime gate, adoption, merge, preview or production deploy.

---

# True source LP re-solve in a separate SCIP process — 2026-10-20

**Review-only new branch `science-independent-scip-lp-reexecution-receipt`**, child of unmerged prior UX actual LP structural verifier DRAFT #98, separate unmerged original scientific source verification DRAFT #96. No app source UI edits or original manuscript, source notebook, GeoJSON, AHP weights/criteria, main, preview or deployment changes.

New `scip_lp_reexecution_worker.py` independently launches fresh PySCIPOpt SCIP in a new Python `-I` process, calls `readProblem` and `optimize` on the ACTUAL first solver-emitted structurally verified N20 original LP bytes; observes its own 20 original selected binary variables, pair-product values, actual local process status and SCIP-reported primal+dual bounds and relative gap. New `scip_lp_reexecution.py` checks exact SHA, independent source original N20 one-hop mathematical feasibility/optimum under actual binary64 rational score, first vs second solution (allow real exact ties), LP-printed decimal score/bounds with explicit tolerances, receipt absence of fraudulently upgraded signatures or physical/manuscript claims. CLI `export_scip_reexecution_reference.py` and new dedicated workflow preserve the first original LP bytes **and** the second SCIP JSON observation/checker report as two 14-day CI artifacts. Adversarial real-SCIP tests under `tests/test_scip_lp_reexecution.py` challenge status, SHA, bounds, selected solution, changed original graph and zero-score real tied optimum. Scientific scope/trust in `docs/N20_INDEPENDENT_SCIP_PROCESS_REEXECUTION.md`.

**Status before CI:** code, tests, research CLI, protocol and workflow created; this is **NOT yet verified** and must not be merged/deployed. Next: open DRAFT child PR, run dedicated actual source SCIP subprocess experiment, existing pilot/unified dashboard and independent source N20/SCIP/GIS/S4 triple-checkout at current head. Fix ONLY observed scope bugs, then record actual artifact digest/exact CI and update #91/#88. The child receipt is an **unsigned same-machine observation, not an externally authenticated SCIP process log or cryptographic certified solver trace**. Source author expert AHP/paper D2-population discrepancy, physical lake waterbody DO/current/RF/backhaul remain blocked.

---

# Bounded structural original SCIP LP independently verified — 2026-10-20

**Review-only [DRAFT PR #98](https://github.com/carlers/quantum-opt-dashboard/pull/98)** child of prior DRAFT UX #97, with separate unmerged original source scientific stack through DRAFT #96. New `scip_lp_structure.py` independently parses actual ASCII CPLEX LP exported by local original N20 SCIP *before* accepting current results and evidence ZIP. Verifies complete binary x/p variable sets & [0,1] bounds, exact K budget, all 20 local-one-hop constraints, three AND linearization rows for every nonnegative pair term, and objective DECIMALS compared to the SCIP writer's 15-digit formatting of the actual compiled binary64 instance. The original `runtime_attestation.py` continues exact Fraction binary64 mathematical optimum proof and binds parsed LP SHA/certificate inside the session result; original global exploratory full graph remains exact exhaustive with **no fake SCIP LP**. New adversarial genuine SCIP-output parser tests reject changed objective, connectivity, budget, pair inequality, bounds, binary set, extra sections/rows and check zero-objective tied case. No change to the original source notebook, 5,417-record GeoJSON, user-provided manuscript or science branch history.

**Verified original executable+docs HEAD `d80bc2edffbb8beef12323e0d052172e7ee15c98`:** [Streamlit pilot #39400327388](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39400327388) **SUCCESS, 111 tests**; [unified dashboard #39400327386](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39400327386) **SUCCESS**; [original scientific triple-checkout #39400327424](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39400327424) **SUCCESS, 24 targeted UX/attestor tests** plus fresh source original N20 notebook/SCIP, raw GIS/S4, honest claim status, independent 35-site all-15-fixed feasible source topology and UX original engine unchanged. Original N20/K5 emitted LP has **20 x +12 p binaries, 57 rows** (1 K +20 original one-hop +36 product). Historic original local 1,077 feasible vs new distinct exploratory all-fixed global 860/15,504, full feasible-set SHA `3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`, selected [0,1,3,6,7], original reference mathematical score -3.3012934918564643. [CI source research artifact #12254442672](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39400327424/artifacts/12254442672) expires Nov 3 09:24:51 UTC. Under independent original source claim gate **source computation verified**, paper AHP/D2 WorldPop parity blocked, real waterbody/DO/current/RF field validity blocked. SCIP LP structural parsing is NOT independently authenticated SCIP process execution, logs, signed session, verified dual bound or laboratory sensor performance.

**Latest documentation-only commits after this verified executable HEAD require new exact-head CI pass** before any final-head green claim. Owner/institution reviewer still needs to examine scope, exact SCIP decimal serialization, signed SCIP execution/LP provenance and paper/field inputs prior to merge/publishing/deployment. No main/preview/production updates, no source manipulations.

---

# Independent original N20 emitted SCIP LP structural audit — 2026-10-20

**Review-only branch:** `ux-water-scip-lp-structural-evidence-review`, child of proven unmerged UX runtime mathematical gate DRAFT #97 (`f75139af2d34a759759574bd7aeb8647298e5ebb`), separate original source science DRAFT #96 unmerged. No original archived source notebook/dataset/manuscript edits, no main/preview/prod changes.

**New code:** `prototypes/streamlit_water_quality/scip_lp_structure.py` independently parses original SCIP's N20/K CPLEX LP **printed from the actual untransformed PySCIPOpt model** and verifies exact decision/pair binary variables, x/p binary bounds, budget sum(x)=K, all 20 source one-hop constraints, all 3 binary-product linearization inequalities per pair, complete objective at SCIP 15-digit text precision. `runtime_attestation.inspect_archive` now calls the parser on the exact previously byte-verified local LP **before publishing result/map/ZIP** and includes LP SHA+structure in the attested session record. Global exact enumeration remains without fake SCIP LP. New adversarial **real original SCIP LP** test suite `tests/test_scip_lp_structure.py` for forged budget/neighbor/pair/objective/domain/foreign row and zero-coefficient flat objective; see `docs/N20_EMITTED_SCIP_LP_STRUCTURAL_ATTESTATION.md`.

**Status:** code, 11 adversarial tests and documentation staged for DRAFT PR, **NOT YET exact-head CI verified**. Test actual SCIP writer decimal formatting, unknown LP expression, section order and real Streamlit existing app regression. LP structural compatibility ≠ authenticated SCIP solver process, independently parsed MIP dual bound or signed trusted session, and source road-D2/manuscript WorldPop/AHP parity & physical antenna/DO/current/shoreline remain blocked.

**Next:** open separate DRAFT PR stacked on UX #97, run existing pilot Streamlit + full independent science checkout and fix scoped tests if needed. On verified final HEAD, update Issue #91/#88 and PR/SESSION_STATE with honest evidence, without any original data/public release/merge permission.

---

# Scientific verifier exact-tie and nonoptimal/error-state hardening — 2026-10-20

**Review-only DRAFT PR #97**, UX child of DRAFT #78, still separate from pinned original source scientific DRAFT #96 and all other science branches. Recovered after timed-out chat: prior full head `90c5e462cf651d1ef1f1db87edb8f3227e926572` [Streamlit #39368755465](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39368755465), [unified #39368755491](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39368755491), [independent science #39368755462](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39368755462) all SUCCESS. Original `main` `41cdc51097ceb98ea2f44194e3b72a0a3aebf3c` and `preview` `0fa4354c6182d70674ce46ffa68870796055ba75` unchanged at beginning of recovery.

**Scoped further research-only implementation:** `runtime_attestation.exact_selection_objective()` now compares **exact binary64 rational selected energy** to exact enumerated optimum instead of requiring lexicographically first winner, allowing genuinely equal-score optima while rejecting falsely close `2^-40` worse outcomes. ZIP member file size/count/expanded total capped before decompression; new test rejects a small compressed malicious >1MB inner model. Global `None` selection with `infeasible_certified_full_graph_disconnected` now verifies **mandatory fixed vertices remain disconnected even with all 20 candidates**, while exhausted `infeasible_certified` checks full enumerated count and `time_limit_no_certified_optimum` rejects impossible post-exhaustion timeout. New real original source **K=0** test detects fake disconnected-fixed vs true budget-infeasibility; original N20 K5 and GeoJSON unchanged. Technical rationale in `docs/N20_UX_RUNTIME_MATHEMATICAL_RESULT_GATE.md`.

**Status:** Last code+unit test commit `c0d5515fb221d217c02bf2e6f71c6e28bdd0cf8c` and research docs subsequently added. **Do not claim these new gates pass until exact FINAL docs HEAD CI has completed**. Required workflow triad: Streamlit pilot fast regression, unified scientific dashboard integration, and independent triple-checkout original cold notebook/SCIP + pinned source GIS/S4 and current UX graph/score contract. If CI fails, patch only current DRAFT and repeat at exact head.

**Still blocked:** parsed/authenticated SCIP LP execution, signed session trust, production/app release, original manuscript AHP/D2/WorldPop expert input parity, physical RF/backhaul/shoreline/DO/current validation. Separate source and UX histories unmerged, no deployment/preview/main/production changes; next update Issue #91/#88 and review-only PR body with **observed final-head CI only**. No original notebook, author DOCX or 5,417-point GeoJSON edits.

---

# Actual UX runtime mathematical verify-before-render proof, independent source cross-check — 2026-10-20

**Review-only [DRAFT PR #97](https://github.com/carlers/quantum-opt-dashboard/pull/97)**, child of unmerged UX DRAFT #78, while science verifier DRAFT #96 remains a separate unmerged ancestry. No source notebook, pinned 5,417 original GeoJSON, archived manuscript or main/preview/production changed; no merges/rebases/deployments. New UX code `runtime_attestation.py` independently reads **actual current compiled model**, original 20 candidate/15 existing station identities, eight source factor weights and original road D2, Dmax, budget, complete local/global graphs; independently enumerates bounded C(20,K) with integer-scaled exact binary64 objective and union-find/local-neighbor feasible checks. Before every selected map/table/ZIP, verifies actual real SCIP LP (only local), selected CSV/master station IDs, each ZIP member SHA, whole current model and global graph identity, solver status and energy, plus a current in-session result/complete attestation SHA. Even edits to displayed independent audit score/master IDs force session result deletion. No authenticated binary SCIP logs/LP proof, signed state, scientific paper parity or physical radio/DO claims.

**Verified executable HEAD `084bca5c42407084dd428f6e0f492d31c4b1937e`:** [Pilot CI #39368288521](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39368288521) **SUCCESS, 96/96 tests** (real app local/global/tamper including forged selected table, ZIP, optimal status); [unified CI #39368288533](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39368288533) SUCCESS; [triple-checkout cold original science vs current UX CI #39368288580](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39368288580) **SUCCESS** with original source real SCIP/GeoJSON/S4 claim, independent full 35-node all-original-fixed graph+exact mathematical solver, current UX backend immutable SHA equivalence to prior #78 and 20 independent/current UX UI attack tests. Original local 1,077 vs global full-15-fixed **860/15,504** feasible, global full membership SHA `3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`, selected **[0,1,3,6,7]**, reference source score -3.3012934918564643, 11/34/17 modeled direct edge categories. The current source and UX exact objective fingerprint SHA in run was `2b238848...` but alternate `8536a3db...` across hosts remains distinct (#24). Original waterbody/RF links are geometry only; source computation verified, manuscript AHP/D2 and physical lake water quality BLOCKED.

**Original science artifact** [#12240426262](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39368288580/artifacts/12240426262) (four JSONs), GitHub ZIP SHA256 `86d5b3536e582056121c316f1f6f1a58458d49f0f15fb79062ba07f82192a207`, downloaded/verified, expires Nov 3 04:14:22 UTC. Permanent project-owner institutional archive not confirmed. Full [scoped protocol and results](docs/N20_UX_RUNTIME_MATHEMATICAL_RESULT_GATE.md).

**NEXT:** Check exact docs-head CI separately before claiming final HEAD green; post on Issue #91 and parent #88 plus UX/science PRs. Human independent review required for UX-side mathematical implementation and model trust beyond original N20, actual SCIP LP log verification, signed per-session result, real shoreline/DO/current/RF and authoritative manuscript AHP/WorldPop inputs before scientific/field claims; no merge/preview/production under current research-only authorization.

---

# UX independently attested current N20 solver result and ZIP gate — 2026-10-20

**Review-only branch:** `ux-water-runtime-verified-export-gate`, from pinned separate UX DRAFT #78 `8752d17372d9d4dd544acbbfd686b4bb45e33f40`. Do not merge with unmerged scientific #96 chain; this branch is an independently authored mathematical verifier installed into UX Streamlit, with no original notebook/GeoJSON/manuscript/main/preview/production edits.

**New changes:** `prototypes/streamlit_water_quality/runtime_attestation.py` independently verifies current actual compiled original 20-candidate/15-fixed model, exact coefficient/controls/adjacency bytes and correct all-15-fixed global graph; enumerates every bounded K subset with union-find/local neighbor proof and **exact integer scaled binary64 objective ordering**, verifies claimed status/score/selected sites and ZIP's actual SHA256SUMS/CSV/LP or wireless graph, then places a narrowly scoped runtime attestation in Streamlit session state **before any result map/table/ZIP is rendered**. Every rerender checks active model, graph, results and archive SHA against that attestation, dropping old data if stale or forged. 11 real-instance/adversarial tests in `tests/test_runtime_attestation.py`. Experimental mathematical proof only; no authentic SCIP logs/LP structure validation, paper D2/AHP or RF/DO field validation and no signed per-user trust boundary. Protocol: `docs/N20_UX_RUNTIME_MATHEMATICAL_RESULT_GATE.md`.

**Status before CI:** Implementation drafted, not yet exact-head verified. Next: open child DRAFT PR on UX #78, run preexisting Streamlit pilot fast regression plus new tests and correct failures only in current isolated DRAFT. Separately maintain science DRAFT #96 cold notebook/source claim and dual checkout audits; actual combined ancestry, preview/main/production require human owner review.

---

# All 15 existing + K selected wireless network source result verified (2026-10-19)

**Owner's precise requirement:** two choices only, original local source one-hop (default) vs all-original+all-selected nodes in one wireless graph component. Both use source-pinned straight-water-link & Dmax geometric proxies. Not previous S1/S2; no physical radio link survey or fixed station backhaul evidence. [Implementation DRAFT PR #78](https://github.com/carlers/quantum-opt-dashboard/pull/78) stacks above docs-only #77, UX #55. No archived source edits, main/preview/prod merge/deploy.

At original code `a2f87394`, [Streamlit fast CI #39225164320](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39225164320) SUCCESS **80/80 tests** and independent union-find global K5 reconstruction; [unified CI #39225164273](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39225164273) SUCCESS. The old local feasible count 1,077, **new fully all-15-existing-station globally connected count 860**, full global membership SHA `3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`; direct links **11 free/free, 34 free/fixed, 17 newly derived fixed/fixed**. Original source local and new global both choose **[0,1,3,6,7]** with source objective `−3.3012934918564643`. The full 35-vertex graph has eight components because seven optional candidate sites are isolated; the **15 mandatory original existing stations are all in the same available graph component**. The global mode cannot infer radios/hydrological correctness from these modeled links.

Integration hardening added exact-source global JSON audit `prototypes/streamlit_water_quality/export_global_reference.py`, CI artifact upload in Streamlit-pilot workflow (14-day retention), and report `docs/N20_ALL_STATIONS_WIRELESS_NETWORK_REPORT.md`. Important fix: don't call a global search **infeasible** if it only hit the 30-second limit. Important earlier fix: disconnected **unused candidate sites** cannot be used to prove required original fixed network infeasible.

**Next steps:** verify newest exact-head Streamlit and unified CI after final doc/source evidence changes, record new graph artifact/custody, update PR #78/Issue #76 and source science #70/#69; obtain optional real RF/backhaul data for physical interpretation. No authorization to merge, preview, production, public release or rewrite original notebook.

---

# Owner-defined all-35-station global wireless mode — reviewed implementation candidate (2026-10-19)

**Owner final definition:** only TWO water dashboard modes: `source_local` original intended local one-hop, AND `all_stations_connected` requiring **every original existing sensor and every newly selected sensor to have a multi-hop modeled wireless path to every other such station**, all in a single graph component. No disconnected existing clusters. Not prior preregistered S2 (which could leave fixed sensors disconnected), and **do not show prior S2=110 feasible as the new global result**. User gave authorization to implement draft and test, no merges/deployment/publication or archived notebook/data modification.

New DRAFT branch `ux-water-all-stations-global-connectivity` on design-only [#77](https://github.com/carlers/quantum-opt-dashboard/pull/77)→existing UX #55. `prototypes/streamlit_water_quality/wireless_topology.py` derives an explicit full **35-node** graph from pinned existing lake GeoJSON and original 0.05 concave hull, strict unobstructed straight-line predicate and original Dmax; includes real **fixed/fixed** modeled *geometry* contacts (previous baseline did not model these), and fails if original free/free adjacency or free/fixed Boolean flags differ. Does not assume remote fixed backhaul or real radio performance. `exact_global_search` enforces all-35 connectivity, certifies an infeasible mathematical model if the full graph disconnects or all subset choices fail, and exhaustively minimizes the **same original source objective** under 20 choose K ≤184756 with a 30s bound and honest timeout status. Pure regression keeps original local SCIP path and original notebook calibration. Global evidence distinguishes exact enumeration from SCIP, includes full graph, checksums and no false SCIP LP.

`prototypes/streamlit_water_quality/app.py` supplies exactly two radio options, records `connectivity_mode`+graph in current model fingerprint, invalidates stale results and shows selected derived direct edges only. Infeasibility displays actual reason and downloadable result; no false optimum. New graph and Streamlit AppTests added, including original control and missing-radio-link counterexamples. Original source paper, GEOS/source archived files, main, preview and prod remain unchanged. **Next steps:** run actual GitHub CI at draft PR exact head, investigate any app/test integration failures without adjusting the original source model or global requirement; document measured real source feasibility and the fixed/fixed link model in #76, then ask user about potential physical range/source limitations before any merge/deploy.

---

# Proposed dashboard wireless-mode selector — documentation-only (2026-10-19)

**Owner clarification:** Historical notebook's **local one-hop** constraint is intentional; direct wireless links are modeled as straight paths not crossing land. Owner would like a dashboard choice between **local clusters, global chain, global connectivity**. Definitions of the last two remain **proposals needing two owner choices**: is "chain" each selected sensor's multi-hop path to any original existing station or literally one single chain; does global include only all selected new sensors in one connected network with at least one original station, or require all original 15 existing stations connected (fixed/fixed topology not given)?

**This draft branch** `ux-water-wireless-topology-modes-spec` stacked on unchanged [UX DRAFT #55](https://github.com/carlers/quantum-opt-dashboard/pull/55) changes **documentation ONLY**. See `docs/WATER_WIRELESS_TOPOLOGY_SELECTOR_SPEC.md` and [Issue #76](https://github.com/carlers/quantum-opt-dashboard/issues/76). It documents actual [preregistered CI #39219858893](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39219858893): original local 1,077 feasible K5; multi-hop-to-fixed also 1,077 with exact same members (null result); one-connected selected network 110, alternative optimum. These are modeled graph counterfactuals, not physically verified wireless designs.

**Technical prerequisite:** Current Streamlit pilot `prototypes/streamlit_water_quality/model.py` `Instance.fixed_neighbors` records only **Boolean** proximity to any fixed station. A truly connected network must preserve the **actual original 20×15 free/fixed edge identities** from GeoJSON; do not invent existing/fixed links. Direct edges are historical concave hull + Dmax proxy, not radio propagation guarantee. Do not create an inert UI selector before there is a properly enforced solver and independent validator.

**Next steps:** open DRAFT docs PR; owner selects exact chain/global meanings; then a distinct implementation DRAFT with actual graph-constrained solver, AppTests, mode-specific fingerprints/exports, negative controls and original unchanged default. No historic notebook, GeoJSON, main, preview, deployment or research model changes.

---

# Current draft: pre-solve lake candidate overview (2026-10-18)

Branch `ux-water-candidate-map-before-solve` is a review-only UX follow-up stacked on preview/PR #53. It shows the same source-pinned 20 candidate + 15 existing stations as a gray/red map before SCIP, and reuses the renderer to show blue selected new sites only after verified solve. Changing K or other fingerprinted inputs invalidates the old result and restores the unsolved map. Headless regression added; CI and Cloud/browser retest must be recorded in GitHub issue #54. No solver, source, reference notebook, main, production, or deployed preview updates.

---

# Owner-provided stable Streamlit preview link — 2026-10-18

**Main (unchanged):** https://v3wzqpbn8w6nmdgkxh5kum.streamlit.app/ tracks `plugin-water-streamlit-pilot`. **Preview (owner supplied):** https://quantum-opt-dashboard-55zt76rpzbn2n3dltqfgis.streamlit.app/ tracks `preview` and uses `prototypes/unified_dashboard/app.py`. The real preview URL is now recorded in the README and deployment guide. Streamlit Community Cloud runtime/browser startup has **not** been independently verified yet; owner should open the page and report any build exception. Preview branch updates should be published only after scientific/UI CI checks. GitHub `main` and the deployed production branch remain unchanged; do not merge or redeploy production without explicit approval.

---

# Canonical integration handoff — 2026-10-18

**Current review-only PR [#51](https://github.com/carlers/quantum-opt-dashboard/pull/51)**: `integration/unified-scientific-mvp` → `main`. The branch combines three diverged Git histories through a real multi-parent commit: [guided and typed optimization workbench #47](https://github.com/carlers/quantum-opt-dashboard/pull/47), [narrow lake MVP #49](https://github.com/carlers/quantum-opt-dashboard/pull/49), and [bounded scientific QUBO/SA/inspector #35](https://github.com/carlers/quantum-opt-dashboard/pull/35) (which includes the original research stack #13–#29). Existing source notebook/GeoJSON and manuscript have not been rewritten. Prior state entries below are retained as dated history, **not the current scope**.

- **One user app**: `streamlit run prototypes/unified_dashboard/app.py`; root `requirements.txt` installs a combined Python 3.12 Streamlit/SCIP/Shapely/OpenJij (pinned classical SA) environment. Sidebar pages: (1) water-quality N20 SCIP/map/LP/ZIP, (2) configurable synthetic JSON/CSV/GeoJSON and guided typed IR, (3) explicit slack-encoded N20 QUBO and manually triggered bounded classical SA with audited seeds/results, (4) scope notes.
- **Standalone apps kept for regression**, `prototypes/streamlit_water_quality/app.py` and `prototypes/streamlit_configurable/app.py`. They use thread-scoped routing context rather than environment-wide flags so multiple Streamlit sessions cannot interfere with `set_page_config`.
- **Science code kept**: provenance/precision probe, controlled one-ULP replay, preregistered paired SA study, QUBO energy checks, evidence exports, original laguna notebook reference and independent synthetic evacuation checks. The expensive five-bundle research workflow is now `workflow_dispatch` only, not triggered automatically by an MVP styling change. Other fast core/unit/regression workflows remain enabled.
- **Scientific caveats**: OpenJij `SASampler` is classical; no quantum advantage; one-hop is not global connectivity; original paper AHP/D2/energy parity unresolved #16; floating precision source drift and SA sensitivity #24; evacuation fixtures entirely synthetic; constrained generic QUBO conversions only where proven.
- **Acceptance status**: integration CI workflows are required green at the latest PR SHA (reverify after edits). A real staged browser/mobile smoke and the owner's explicit merge/deploy approval remain outstanding. `main` and `plugin-water-streamlit-pilot` are not modified by this draft.

---

# Current user-facing customizability checkpoint — synthetic model workbench (2026-10-18)

- **User requirement:** Thesis-specific data and mathematical formulation must be **swappable**, not embedded permanently in a lake/shelter dashboard. The long-term target is a user-configurable and mathematically auditable optimization workbench with user-selectable input sources, supported formulations/solver compatibility and exact input/result provenance.
- **Draft PR #39** https://github.com/carlers/quantum-opt-dashboard/pull/39 (stacked on synthetic PR #36): versioned bundle contract, strict typed data/formula/parameter validation, local JSON swappability, domain-neutral small binary quadratic + independent enumeration/actual SCIP MILP LP, two synthetic evacuation formulations (potential coverage vs capacity-constrained service). User-editable K, constraints and coefficients work via JSON without Python changes. Verified [CI 39116536521](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39116536521) at SHA `6384dd4ac6263a03135a3a530d1047d466c422bb`: 43/43 tests, all 4 example CLIs and two scientific evidence uploads, [bundle artifact](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39116536521/artifacts/12132576353).
- **New isolated draft PR #43** https://github.com/carlers/quantum-opt-dashboard/pull/43, head `ui-synthetic-bundle-configurator`, base #39: **experimental independent Streamlit UI**, editable or uploaded **synthetic local JSON <=1 MB**, choose eligible mathematical formulation, type parameter overrides, validate/preview actual numeric terms and input hashes WITHOUT solver, explicitly run SCIP, and download ZIP with exact user input, original actual SCIP model LP, independent audits and SHA manifest. Changing input or mathematical formulation hides stale results. No executable Python/LaTeX or general unsafe upload parser; no actual shelter or hazard data.
- **UI CI verified** [GitHub Actions #39117149376](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39117149376) at SHA `a92fe3260b2dffeeeb5ae4ac37186bddc7b91cc7`: **4/4 real headless Streamlit AppTest interaction tests + 43/43 backend/scientific bundle tests passed**. No browser screenshot or actual public Streamlit deployment was performed.
- **Follow-ups** [#40](https://github.com/carlers/quantum-opt-dashboard/issues/40) user UI integration with water-quality scientific inspector #29; [#41](https://github.com/carlers/quantum-opt-dashboard/issues/41) GIS/CSV/GeoJSON adapters and verified water-quality N20 parity; [#42](https://github.com/carlers/quantum-opt-dashboard/issues/42) typed general mathematical expression editor and correctly validated optional constrained QUBO compiler. Real evacuation hazard/license/capacity still [#33](https://github.com/carlers/quantum-opt-dashboard/issues/33); manuscript provenance #16/24 remains.
- **Safety:** nothing merged or deployed to `main` or live `plugin-water-streamlit-pilot`. Original notebook, paper and source GeoJSON unchanged. These unmerged branches are independent from the water-quality Streamlit inspector PR #29; combine only after explicit reviewed integration and user approval. Full mathematically arbitrary MIQP/QUBO and user-installed data sources are **NOT** delivered by these synthetic prototype versions.

---

# Active reusable model-contract milestone — swappable synthetic bundles (2026-10-18)

- **Draft PR #39:** https://github.com/carlers/quantum-opt-dashboard/pull/39, branch `framework-configurable-problem-bundles`, base **unmerged** synthetic evacuation PR #36. No live deployment or changes to `main`, `plugin-water-streamlit-pilot`, original lake data/notebook or paper.
- Generic versioned bundle contract `contracts/optimization_bundle.schema.json` and strict core `framework/python/qopt/core/experiment_bundle.py`: `problem_id`, `formulation_id`, local dataset JSON path+optional expected hash, typed adapter-specific parameter overrides, source SHA-256 and deterministic scientific content fingerprint. Untrusted names/path traversal/symlinks/nonfinite values/unknown params and real shelter-classified inputs rejected. Bounded synthetic prototype only.
- Two independent executable adapters: **(A)** evacuation synthetic `maximal_coverage` vs `capacitated_lexicographic`, with user-swappable hypothetical data and K, independent existing SciPy/HiGHS check and true SCIP model exports; **(B)** domain-neutral *small* (`n<=16`) editable binary-quadratic objective+linear-constraint model, exact pair-product SCIP MILP, independent exhaustive enumeration, named constraint RHS edits, true SCIP LP. QUBO coefficients only for **unconstrained** binary objective; constrained QUBO encoding remains a separately required proof.
- Four runnable example bundles under `problems/evacuation_centers/examples/`: same dataset/switch formulation; same formulation/switch data; independent generic binary objective. `bundle_runner.py` produces `run.json`, `manifest.json`, real SCIP `.lp` files and exact input provenance. `docs/CONFIGURABLE_PROBLEM_BUNDLES.md` explains usage and supported vs future UI.
- **Verified CI at PR head `a64ca49f2e286c532b259398bbfe64bfae215eb2`:** [Actions run #39116419543](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39116419543) **43/43 tests passed** (existing 19 + 24 new), both original synthetic reference and four bundle CLI examples succeeded. [Download replaceable-bundle audit artifact](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39116419543/artifacts/12131554626); [existing synthetic evidence](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39116419543/artifacts/12132326678). Artifacts expire ~2026-11-01 09:43 UTC.
- **Important limits:** No deployed dataset uploader, no arbitrary text formula compiler, no real approved Philippine shelters or hazard data. Binary QUBO is previewable only when unconstrained; otherwise scientifically correct response is refusal pending justified penalties/slack and independent parity proof. Full generically editable MIQP/continuous typed IR, dataset adapters CSV/GeoJSON, validated water-quality adapter, frontend preview, durable archive and true thesis final formulation remain future gates. The user asked for a **general user-configurable workbench**, not a hardcoded lake/shelter tool.
- All research PRs remain drafts and review-only, including separate water-quality UI [#29](https://github.com/carlers/quantum-opt-dashboard/pull/29) and separate CI [#35](https://github.com/carlers/quantum-opt-dashboard/pull/35); don't merge or redeploy without approval.

---

# Research milestone checkpoint — evacuation-center thesis specification (2026-10-18)

- **Active proposed second domain:** evacuation-center siting/allocation, not yet validated as a thesis question or deployed application. Documentation only in **isolated draft [PR #31](https://github.com/carlers/quantum-opt-dashboard/pull/31)**, branch `research-evacuation-formulation` based on unchanged `main`. Parent [research issue #30](https://github.com/carlers/quantum-opt-dashboard/issues/30); [umbrella #2](https://github.com/carlers/quantum-opt-dashboard/issues/2) and [academic Phase 1 #3](https://github.com/carlers/quantum-opt-dashboard/issues/3).
- `docs/EVACUATION_RESEARCH_SPEC.md`: identifies separate classical MCLP potential-coverage model vs capacitated location/allocation with explicit unmet people, shelter eligibility/capacity, travel network, and two-stage lexicographic objective. Stated assumptions/units and a **purely synthetic** two-zone numerical acceptance fixture. **No solver or field study was run in this docs-only PR.**
- `docs/EVACUATION_DATA_AUDIT.md`: source/data licensing gates for PSA 2024 barangay population, PSGC, OSM/Geofabrik (ODbL), Philippine hazard-map rights (HazardHunterPH restriction), real LGU shelter-site/capacity verification, CRS/unique keys and uncertainty. **No bulk data downloaded, permitted redistribution asserted, actual candidate capacity inferred, or official crisis recommendations generated.**
- `docs/ACADEMIC_REPRODUCIBILITY_SURVEY.md`: FAIR, software citation and The Turing Way sources; repo scientific-validation maturity, 14-day GH artifact limitation, proposal for durable manifests/releases and fast vs research CI separation.
- Split next independent tasks: [#32 synthetic model proof](https://github.com/carlers/quantum-opt-dashboard/issues/32), [#33 field data and hazard-use authorization](https://github.com/carlers/quantum-opt-dashboard/issues/33), and [#34 fast vs costly scientific CI separation](https://github.com/carlers/quantum-opt-dashboard/issues/34).
- **Human/adviser decisions still required:** study area, hazard, official candidate shelters and *usable* capacities, modeled evacuee fraction, route modes, budget rules, final thesis contribution and dataset rights. Do not silently fill these gaps or claim generalized solver parity/quantum advantage.
- **Previous work remains separate:** deployed Streamlit pilot uses `plugin-water-streamlit-pilot`; scientific code plus Formulation Inspector in unmerged **draft PR #29** stacked on other unmerged research PRs. This research/docs-only PR does not touch UI, `main` production, original water-quality GeoJSON/notebook/paper or any expensive job.
- **Review gate:** Research docs/proposed model and source rights are not merged or finalized without user approval. There is no numerical CI acceptance to claim for this docs-only milestone.

---

# Session checkpoint

Updated: 2026-09-30
Current task: Scaffold committed. Next: FC1 (Problem protocol + schemas).
Status: Repo pushed to GitHub. Source data and reference notebook committed.
No feature branches open yet.

## Completed
- Monorepo scaffold (framework/, problems/, apps/, contracts/, docs/).
- Source geojson at `problems/water_quality/data/`.
- Reference notebook at `problems/water_quality/notebooks/`.
- CI workflows: framework.yml, water-quality.yml, frontend.yml, worker-image.yml.

## Next tasks (in order)
- `framework-problem-protocol` — Problem, StageSpec, contexts, Tracker.
- `framework-plugin-registry` — Entry-point discovery.
- `framework-cache-keys` — Cache-key derivation from StageSpec.
- `framework-cache-storage` — Disk + R2 tiered cache.
- `framework-stage-executor` — Runs one stage-unit. Pivotal task.

Each task is one branch, one PR, one ChatGPT conversation. Branch name matches
the task name above.

## Constraints (durable)
- Framework must not import plugins.
- Every stage declares config_deps and inputs; cache keys derive from these.
- code_version, env_version, seed frozen per job at creation.
- No plt.show() in library code; artifacts return bytes.
- At least two plugins must run before v0.1 ships.
- This is a control center: pause, resume, fork, sweep are hard requirements.

## Files in active work
- (none — no branch open)

## Blockers
- None.

## Workflow
- Feature branch per task. PR to `main`. CI green before merge.
- Branch naming: `<phase><number>-<slug>` (e.g. `fc1-interfaces`).
- Every PR updates this file.