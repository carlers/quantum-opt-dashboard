# Review-only scientific evidence adapter for future Streamlit — 2026-10-19

**Current draft:** child of source-only scientific claim gate DRAFT #86 on a new branch `science-dashboard-evidence-readonly-adapter`. Issue #85 scientific objective/claim gate is independently verified on #86 at `d8a39099761a`; Issue #88 remains **open** for later real dashboard implementation. Separate UX chain #55 → #77 → #78 is not on this branch and has not been integrated.

**Scope:** new pure Python `scripts/scientific_dashboard_adapter.py` gates display classification on genuine cold source + S4 evidence and exact objective/site/graph/topology identity; `scenario_sha256` invalidates a stale result binding; cached results are **never** treated as independently solver verified. Shows original source road D2 vs manuscript WorldPop, AHP Table III/IV mismatch, explicit blocked manuscript/physical claims. New adversarial adapter tests, dedicated exact-head cold N20+SCIP/S4 CI and `docs/SCIENTIFIC_DASHBOARD_ADAPTER_PLAN.md` document the follow-up. No current Streamlit app changes, notebook/GeoJSON changes, scientific assumption correction, new sensitivity parameters, merge or deployment.

**Current gate:** exact-head CI of this new draft is required; pending at branch preparation time. Passing this research adapter CI alone does not certify Streamlit, user-modified numerical scenarios or field water-quality/radio validity.

**Next steps:** open this as a DRAFT PR targeting #86; verify its exact HEAD test and cold SCIP/GeoJSON/S4 research artifact; update #85/#88 with technical dependency plan; require separate owner-reviewed integration with UX #78 and real AppTest before preview/production. Obtain #87 original expert GIS/AHP, independent lake polygon, RF/backhaul and DO/current evidence before new physical model adoption.

---

# Scientific claim integrity gate for future water dashboard — review-only (2026-10-19)

**Latest owner intent:** build a new scientifically/mathematically accurate research dashboard and **do not** assume previous manuscript or notebook data definitions are correct. Under earlier authorization, preserve the source-derived original N20/K5 as a **historical computational regression fixture**, and distinguish physical validity and published-paper parity.

[Issue #85](https://github.com/carlers/quantum-opt-dashboard/issues/85) scopes research claim/objective integrity separately from [S4 original source audit DRAFT #84](https://github.com/carlers/quantum-opt-dashboard/pull/84), [S4 provenance protocol #83](https://github.com/carlers/quantum-opt-dashboard/pull/83), and original source #68. This new branch `science-n20-claim-integrity-gates` adds **only** `scripts/science_claim_gate.py`, 12 adversarial tests `scripts/tests/test_science_claim_gate.py`, `docs/SCIENTIFIC_CLAIM_CONTRACT.md`, separate cold scientific CI workflow `.github/workflows/n20-scientific-claim-gate.yml`, and this checkpoint. No app/worker/UI, original notebook/GeoJSON, weights, spatial hull, Dmax, existing network topology, main, preview or production change.

**Executable semantics:** require actual original frozen dataset+source SHA, verified source N20 model/SCIP+1,077 K5 feasible membership, independent raw GeoJSON original graph, current S4 source all-5417-factor-complete audit and consistent original D2 `d2_road_proximity`. Emit machine-readable three-level certificate: **source computational pass**, **manuscript AHP/D2/SCIP parity BLOCKED**, **physical shoreline/radio/transport validity BLOCKED**. Never elevate a source calculation based on arbitrary user/JSON `validated` flag. Objective fingerprint binds exact original ordered sites/criteria/weights/linear+quadratic float.hex and K; different objectives permit no direct raw objective-energy quality ranking. Same score function is still not real-world monitoring performance.

**Next steps:** review exact-head cold-source CI and adversarial test pass/fail, correct only implementation defects; update Issue #85/#16/#73 and PR; owner obtains actual GIS/AHP questionnaires, physical RF, lake-current/DO/shoreline data before real-world/model acceptance, and separately approves any dashboard integration/merge/promotion. No declaration of peer-reviewed science, paper exact reproduction, physical radio coverage or quantum hardware.

---

# S4 source-only spatial and AHP provenance results — 2026-10-19 UTC

**Source and manuscript gate (no parameter sweeps):** protocol [DRAFT #83](https://github.com/carlers/quantum-opt-dashboard/pull/83), source-only audit [DRAFT #84](https://github.com/carlers/quantum-opt-dashboard/pull/84), all above unchanged original source scientific #68, data source SHA `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`. Source manuscript DOCX reviewed locally, **not committed/uploaded** to CI, SHA `f667995bc2bbf1bee191b5294fc26f366767bc72b78478e547419689b6eaf2be`. Manuscript Table III and IV documentary **transcriptions are not historical source solver inputs**.

[Successful initial fixed-test CI #39235152085](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39235152085): **11 tests passed**, fresh original N20 source SCIP and independent raw source GeoJSON, 1,077 original K5 region SHA, source coefficient/geometry identity. **0 of 5,417 source features and 0 of original 20 candidates missing any eight criterion field**. All original 20 utility numerator/denominator values match actual source; sum of original eight weights **1.0001**. Exact Dmax **9873.27073466548m**, closest source interior candidate-relevant segment distance to original threshold **25.727322060418373m**, free/free **11** and free/fixed **34** original links. Original N20 solution [0,1,3,6,7] and objective unchanged. Original missing-data renormalization is coded but no source record in committed source exercises missing values.

**AHP discrepancy:** notebook category totals A/B/C/D `[.4895,.3010,.1461,.0635]`; manuscript printed Table IV category totals `[.552191814,.268830225,.130782272,.048195690]`; Table III principal eigenvector `[.616975355,.228319383,.104610094,.050095168]`, λmax≈4.14712642, CR≈0.05449127, **different from reported manuscript** λmax≈4.2207/CR≈0.0817. Within-pillar ratios also differ source ~3:1/5:1/7:1/3:1 from published 1:1/2:1/2:1/1:1. Manuscript **D2 WorldPop/population** vs source **`d2_road_proximity`** remains unresolved, not repaired by completeness.

[Full baseline research report](https://github.com/carlers/quantum-opt-dashboard/blob/science-n20-s4-source-provenance-audit/docs/research_results/N20_S4_PARAMETER_PROVENANCE_FINDINGS_2026_10_19.md). CI numerical evidence [artifact #12178666221](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39235152085/artifacts/12178666221) 14-day expiration 2026-11-02T10:07:52 UTC, private custody owner NOT confirmed. Initial synthetic test CI #39234991248 failed **before** original source execution due invalid D2=8 upper-clipping assumption; only synthetic test input corrected to 80, no original math/source changes. Final report-head CI must be checked separately.

**Next steps:** rerun exact-head CI, update #73/#16/#69 and owner decisions; seek verified shoreline, RF range/fixed backhaul, spatial DO/current covariance, original AHP elicitation/WorldPop GIS provenance BEFORE specifying any hull/Dmax/Lc/Lw/AHP numerical sensitivity values. No original notebook/GeoJSON, `main`/`preview`/production edits, merges or releases.

---

# S4 original N20 parameter and manuscript AHP provenance (2026-10-19)

**Owner scope:** review-only scientific-model audit and preregistered studies. For S4 [issue #73](https://github.com/carlers/quantum-opt-dashboard/issues/73), all *new parameter values and experimental ranges are deliberately BLOCKED* until source/domain rationale and owner research decision. This is a no-sweep *forensic provenance audit*, NOT a randomized or adaptive sensitivity experiment.

Protocol-only first [DRAFT #83](https://github.com/carlers/quantum-opt-dashboard/pull/83) pinned to scientific source [DRAFT #68](https://github.com/carlers/quantum-opt-dashboard/pull/68), describing original **0.05 hull**, fixed-station-buffer **1.15**, Lc=7.5km, Lw=1km, source 8 original criteria/weights, AHP printed Table III/IV and source D2 road vs manuscript WorldPop. The owner-provided manuscript DOCX was inspected locally; exact manuscript SHA recorded in protocol, DOCX not committed to GitHub or fed into CI. No original source, GeoJSON, manuscript or dashboard modified.

Child branch `science-n20-s4-source-provenance-audit` adds only `scripts/studies/n20_s4_parameter_provenance.py`, 11 synthetic AHP/schema/missing-data tests and a focused cold original N20 notebook+SCIP/GeoJSON CI workflow. It records source factor missingness across all 5,417 and 20 original candidates, original available-weight normalization (source sum 1.0001), original graph threshold margins and source AHP/manuscript documentary mismatches. **It does not apply different weights or vary hull/Dmax/Lc/Lw.**

**Next steps:** open child DRAFT; run exact-head cold original scientific CI and inspect machine-readable provenance, publish findings including nulls/errors; discuss missing source expert AHP records, original WorldPop/road processing, validated shoreline and physical wireless measurements with research owner. A future actual parameter sweep needs its own dated preregistration with **exact justified numeric values**, not guessed ±10%. No merges or deploys.

---

# Combined scientific N20 reference integration validated — 2026-10-19 UTC

**Owner must see “Next steps” in all updates.** Review-only [DRAFT PR #68](https://github.com/carlers/quantum-opt-dashboard/pull/68) merges existing experimental *logic* from sibling source science branches, not GitHub pull requests into main. Base is unchanged draft #63 (source precision #61→#57→#56); source independent spatial fork #66→#67 unchanged. **No deployment, archived paper, GeoJSON, original notebook or base-pr branch updates.**

At scientific code SHA **`8d3af1a7a2eb4f5303bcc857692ef42d33b30326`** original two scientific CI workflows SUCCESS: [clean SCIP geometry #39191911068](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39191911068) **21/21 anti-tampering tests**, 1 real notebook/SCIP, original 1,077 feasible/11 free-free/34 free-fixed and same complete feasible SHA; [six independent full numeric source kernels #39191911072](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39191911072) **8+7+10 unit tests**, all six actual source kernels, **two last-bit numeric model SHA modes and 20/300 pair traces differing**, but **same exact structural graph SHA `148d4d276b61305cd969d426afacd3c81634486818deca816014d67cef7908ae` and all 1,077 feasible-set identities**. New `scripts/verify_n20_joint_integrity.py` tests that a changed off-winner one-hop link fails even when model hex checksum was rehashed and the reported optimum remains equivalent. All evidence in `docs/N20_INTEGRATED_SCIENCE_VALIDATION.md` and short-retention Actions artifacts (expire approximately Nov 2). Existing scientific model input scope and equations are unchanged.

**Next steps:** update PR #68 results + #2/#5/#6/#24 issue checkpoints; request adviser validation of original hull, D2 and AHP/paper Table V (#16) and numerical policy (#64); plan explicitly authorized base-first integration of sibling research branches (avoid force-pushing/rebasings existing scientific experiments). Obtain owner-approved durable archival store (#34). No merge/preview/prod/main changes.

---

# Integrated N20 scientific certificate replay checkpoint — 2026-10-19

**Owner standing preference:** every response must include explicit **Next steps**. No merge/deployment authorization.

**Current isolated DRAFT work branch:** `science-n20-integrated-certificate-replay` on top of unmerged runtime/precision #63→#61→#57→#56. Parent science source #56 also has separately reviewed #66→#67 feasible-region and raw GeoJSON geometry certificates, both green. PR branches are kept unchanged to preserve scientific history.

- In the combined original 23-cell notebook, **cell 12 and original `MODEL_INPUT` from #63** are retained (source read-only 300 free/fixed pair trace, IEEE754 hex numerical coefficients, input original trace SHA); separate original enumeration cell 14 and cell 13 explanation are drawn from #67; result cell 22 **appends** `feasible_combinations` and `feasible_site_sets_sha256` to the existing #63 precision-result record *outside* `MODEL_INPUT` so numerical manifest has not been silently changed.
- Imported independent `scripts/n20_independent_geometry_audit.py`, its 11 geometry adversarial checks, and the original #67 fresh SCIP/geometry CI. Adopted the more stringent #66 `scripts/run_n20_reference_notebook.py` + 10 manifest/feasible tests. Source GIS and original archived notebook untouched.
- `docs/N20_INTEGRATED_SCIENCE_VALIDATION.md` preregisters actual combined CI acceptance, caveats and no-retuning boundary.

**Next steps:** open separate DRAFT integration PR on #63; obtain exact-head N20 clean SCIP/geometry and #57/#61 six-kernel numerical precision CI outcomes; fix only integration issues; update #2/#5/#6/#24 and handoff; coordinate owner/adviser scientific approval before any future merges.

---

# Issue #62 runtime cause narrowed — paired NumPy and OpenBLAS controls (2026-10-19 UTC)

**Owner workflow preference:** Every response/handoff must state **next steps** explicitly. New independent [draft stacked PR #63](https://github.com/carlers/quantum-opt-dashboard/pull/63) on source-N20 operation trace PR #61. No merges/production/preview/main/history writes.

**Study 1 (preregistered; explicitly amended pre-result after masked preflight):** GitHub [#39180686631](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39180686631) SUCCESS: 3 x86 hosts × 2 baseline/2 `NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4` NumPy 2.5.4 processes each = 12; 10/10 adversarial tests, source fixed SHA and NumPy/OpenBLAS shared extension SHA identical across all hosts. AMD EPYC 9V45 and Intel Xeon 8573C each showed 2 one-ULP `np.exp` changes under mask; AMD EPYC 7763 no change; **all four original `np.linalg.norm` cases unchanged under this mask** on each host, while cross-host norm modes persisted. Wrong old-style `AVX2,FMA3` preflight was **not** valid and is documented in `docs/N20_NUMPY_DISPATCH_PROTOCOL.md`. Strong but bounded NumPy ufunc dispatch sensitivity.

**Study 2 (separately declared after Study 1):** [#39181329033](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181329033) SUCCESS, 3 hosts × 2 auto/2 `OPENBLAS_CORETYPE=HASWELL` processes each, original frozen operands and x86 compiled binary SHA invariant; 8/8 adversarial tests. Intel Xeon 6973P-C auto-`SkylakeX` changed **all four original norm results by one ULP** when forced to `Haswell`, matching the natural Haswell modes of EPYC 9V74/7763; exp unchanged. Two other hosts already selected Haswell and had zero change. Within-arm fresh-process replicates bitwise identical. **Observed OpenBLAS-selected target sensitivity** for norm independent of NumPy ufunc dispatch control; not one proven CPU instruction or approved universal numerical fix.

**Results and protocols:** `docs/N20_NUMPY_DISPATCH_RESULTS.md`, `docs/N20_NUMPY_DISPATCH_PROTOCOL.md`, `docs/N20_OPENBLAS_CORETYPE_PROTOCOL.md` with raw 14-day artifact links (expire around Nov 2 UTC). Source N20 scientific notebook, 25-cell archival version, GeoJSON, AHP/D2 manuscript, source MIQP/K5 constraints and history B QUBO/SA all unchanged.

**Next steps:** Finish exact-head PR #63 CI review after the documentation checkpoint; write evidence comments into issue #62, #24, roadmap #2; create a separate scientific reproducibility policy proposal (pin runtime, report exact input+original outcome tolerance, run multi-host and sensitivity checks) before any numerical stabilization is ever adopted. Keep PR #63 **draft/unmerged** and do not change main/preview/production.

---

# Issue #62 — fixed NumPy binary/dispatch intervention phase (2026-10-19 UTC)

**Owner instruction:** Continue independent scientific work and **always state next steps in every work handoff/response**. The user did not authorize merging or changing live deployment. New feature branch `science-n20-numpy-dispatch-controls` stacked on last reviewed trace PR #61 at `0239baa1`, itself on PR #57 and clean scientific N20 notebook PR #56.

- Freeze **same six exact IEEE754 NumPy operands** from validated 300 free-to-existing station trace #60. Source reference and prior results unchanged. No original archive, GeoJSON, notebook model mathematics, QUBO, SA sample, main, preview or prod modification.
- New `scripts/n20_numpy_dispatch_audit.py` records `np.show_runtime(mode="dicts")` allowlisted SIMD/BLAS metadata and SHA-256 of installed NumPy compiled extensions/bundled libraries (no full paths), and exact frozen `np.linalg.norm`, `np.exp` plus *separately labeled* diagnostic square/reduce/sqrt, math.hypot and math.exp stages. Pinned NumPy 2.5.4.
- New `scripts/tests/test_n20_numpy_dispatch_audit.py` has 10 adversarial tests (altered binary, missing host, missing SIMD mask, different frozen operands, 1-ULP mode change, etc.)
- New `.github/workflows/n20-numpy-dispatch-controls.yml` runs **3 independently allocated Ubuntu 24.04 x86 GitHub hosts**, each with **2 baseline new interpreters + 2 new interpreters launched with `NPY_DISABLE_CPU_FEATURES=AVX2,FMA3`**, meaning 12 separate fixed-input NumPy observations. Numeric threading env fixed to 1 across arms, same binaries required within host, compiled SHA and CPU features observed. An aggregate job checks and reports all differences. Original clean-N20 SCIP/exhaustive and prior full 300-pair controls are inherited reference evidence, not replaced.
- `docs/N20_NUMPY_DISPATCH_PROTOCOL.md` preregisters the comparison, intervention and limitations before seeing new output. Neither an equal result nor changed mode automatically proves CPU instruction/BLAS causal attribution.

**Next steps:** Open stacked draft PR; check exact-head CI, debug invalid source/logs only if necessary, archive all 12 raw process reports and test evidence; update #62, #24, #2 and PR. Propose only a separately reviewed future numerical portability policy, never a silent rounding fix. Do not merge or deploy without separate explicit authorization.

---

# Finalized issue #60 computational evidence — exact frozen operands across x86 and ARM (2026-10-18 UTC)

Draft [PR #61](https://github.com/carlers/quantum-opt-dashboard/pull/61) stacked on unmerged original-model precision PR #57 and working N20 notebook PR #56. Source N20 pair trace verified **20 of 300 free–fixed pair records** differed across 3 separate host jobs × 2 fresh N20 SCIP/exhaustive notebooks; 12 records first changed at `np.linalg.norm` distance, 4 at a separately evaluated `np.exp` diagnostic with identical exponent input, and 4 only reflected earlier changed accumulators. Original 20×15 pair identity/linear increment reconstruction and scientific N20 objective/constraints all passed. **Last-bit changes only in final free-site linear positions 9,10,17,19.**

**Exploratory frozen-input microcontrol**: initial six host processes [#39178324563](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39178324563) all sampled AMD EPYC 7763, reported identical norm/exp results (negative but valid observation). A later intentionally architecture-diverse three-host run [#39178474623](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39178474623) (x86 EPYC 9V74, x86 EPYC 7763, ARM64) used **exact same committed operand hex values and pinned NumPy 2.5.4**; all six frozen norm/exp cases produced 2 distinct IEEE754 output modes across hosts and exact equality within each host, six falsification tests green. ARM64 matched EPYC 7763 rather than 9V74, so **architecture label alone does not explain the difference**. Latest scientific source N20 [#39178474612](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39178474612) and six-kernel cross-host trace [#39178474597](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39178474597) green. This supports originating arithmetic-operation-level input drift in NumPy public norm/exp operations, **not** a unique lower-level CPU/libm/BLAS cause. All exact hashes, pairs, field modes, artifacts and limitations in `docs/N20_FREE_FIXED_ULP_TRACE_RESULTS.md`. Branch draft/unmerged; no original GeoJSON/archive/paper/production/preview/main writes.

---

# Issue #60 follow-up checkpoint — frozen math microprobe (2026-10-18 UTC)

Original N20 edge trace [CI #39177889565](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39177889565) showed 20/300 free-fixed records different across CPU-heterogeneous runs; 12 first at identical-displacement `np.linalg.norm`, 4 first at separately evaluated `np.exp`, 4 only propagated an already different linear accumulator. Affected final free-site indices 9,10,17,19, original SCIP/exhaustive N20 parity unchanged; stage details `docs/N20_FREE_FIXED_ULP_TRACE_RESULTS.md`. Separate frozen-operand experiment [#39178324563](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39178324563) passed 6 fast tests and 6 process executions, but *all* sampled EPYC 7763 hosts and got identical norm/exp results. This negative observation motivated one explicitly exploratory **two-x86 + one-ARM** same-NumPy hex-operand follow-up, committed before inspecting that run's outcome. No model, source dataset or historical QUBO/SA change. Current PR #61 draft/unmerged.

---

# Precision Phase #60 — original N20 free-to-fixed pair-stage trace (2026-10-18 UTC)

Owner requested to continue; work specifically follows issue #60 after verified prior frozen-QUBO classical SA experiment PR #59 and prior original-model study PR #57. Current branch `science-n20-free-fixed-ulp-trace` **stacks on unmerged `science-n20-cross-run-manifests` at `cac8dbfb`**, which stacks on source-reviewed working N20 reference PR #56. All original historical notebook, source GeoJSON, main, preview and production remain unchanged.

**Code:** Existing curated working N20 notebook loop now records 300 free-to-fixed station pair stages and IEEE754 values with read-only traces of hull/radius rejection, distance/displacement, redundancy/wake/directional cosine, added coefficient, and before/after original linear addition. Computation, pair traversal and exact-K/one-hop math remain unchanged. A separate diagnostic `np.exp` invocation is identified as **not** the original expression's call result. Independent `scripts/compare_n20_pair_trace.py` validates exact 300 pair identities, all sequential increments and final original linear, hashes, and first observed per-pair differing stage; adversarial tests cover 1-ULP, changed addends, omitted pair and tampered hashes. `.github/workflows/n20-cross-run-precision.yml` now runs the pair comparator across three independent CI host jobs, two cold notebook kernels each (six replays). Detailed *pre-results* plan `docs/N20_FREE_FIXED_ULP_TRACE_PROTOCOL.md`.

**Gate:** Open a *new draft stacked PR*, validate latest-head full six-process N20/SCIP source model and independent stage audit (plus fast tests), then record precise path and host observations in issue #60 and an auditable research report. If six hosts happen to produce only one exact coefficient mode, record **negative result**, not “fixed.” Do not infer CPU causation, modify the model, normalize rounding, revise old seed experiments or merge/deploy unreviewed branches.

---

# Current verified #24 precision checkpoint — three batches completed (2026-10-18 UTC)

Draft stacked PR #57, final instrumented head tested at `907be6158d0ca61fa35824b83754d2924c141bd0` before this documentation-only checkpoint. **Study A** found two exact original-model float SHA types across 3 fresh hosts / 6 independent N20 notebook executions, with four differing final linear terms (indices 9,10,17,19), absolute difference 1–2e-16. **Study B** instrumented existing weighted utility/numerator/denominator/pre-fixed-pair linear values but sampled only EPYC 7763 machines and found no drift. **Study C** captured EPYC 7763 versus Intel Xeon 8370C; exactly the same four final linear coefficients drifted, **all utility-stage inputs remained bitwise identical**, so the first recorded variation occurs inside/after free–fixed interaction formation, not source utility calculation. All original canaries/SCIP proofs/15,504-combination enumeration remain green. CPU association is observational not causal. Detailed stage-by-stage evidence, CPU model notes, exact SHA values and artifacts: `docs/N20_CROSS_RUN_PRECISION_RESULTS.md`; controlled preregistration: `docs/N20_CROSS_RUN_PRECISION_PROTOCOL.md`.

**Next independent issue #24 research:** freeze an identical legacy QUBO coefficient/offset/seed vector and run replicated classical OpenJij with exact original feasibility auditing; separately isolate the particular geometric/distance/wake accumulation operation causing 1–2e-16 model drift. No retrospective normalization and no claims that this explains prior 665 vs 698 feasible rates. PR #57 remains DRAFT, stacked on unmerged PR #56. Immutable research source files, `main`, `preview` and production are not changed.

---

# Precision run checkpoint — measured before exploratory repeat (2026-10-18 UTC)

The original controlled Study A (head `8b4611b3`, CI #39165632021) independently executed **six N20 notebook runs** in three Ubuntu runner jobs, each self-consistent but with **two distinct exact float64 model hashes**. Runner r1 reported AMD EPYC 9V74; r2/r3 AMD EPYC 7763. Differences isolated to four small N20 linear terms (local 9/10/17/19, absolute `1.1e-16` or `2.2e-16`), while all six original objectives, local site decisions, quadratic coefficients and constraints agree; hardware association is **not causal proof**. Study B (head `867c68bc`, CI #39165864942) added **read-only** weighted utility numerator/denominator, initial utility and pre-fixed-pair linear values to the model manifest; its three separate runner jobs all reported EPYC 7763 and all six input hashes matched. Both stages green, comparator has 8/8 adversarial tests, working SCIP fresh-kernel and old water CI are green. Exact factual report: `docs/N20_CROSS_RUN_PRECISION_RESULTS.md`, formal protocol: `docs/N20_CROSS_RUN_PRECISION_PROTOCOL.md`. Stage A/B exact SHAs are incomparable because Stage B adds debug fields.

**Next gate:** one explicitly exploratory re-run with identical scientific notebook/calculation/dependency settings to sample alternate hosted CPUs; if no alternate CPU sampled, record that negative result (do not infer root cause). Then, only in a separately designed research issue/PR, freeze the legacy exact QUBO coefficients and test recorded OpenJij seeds. Do not change preregistered historical results or deploy to `main`/production. This PR #57 is stacked on unmerged PR #56.

---

# Precision phase — independent N20 fresh-process manifests (2026-10-18)

**Working task:** Scientific reproducibility issue #24, stacked branch `science-n20-cross-run-manifests` based on **review-only draft PR #56** exact head `0c48f74c`. The proposed N20 working notebook remains unchanged; archived source GeoJSON/notebook and the Streamlit app remain untouched.

**Added study:** `scripts/compare_n20_replays.py`, isolated adversarial comparator tests, `docs/N20_CROSS_RUN_PRECISION_PROTOCOL.md`, and `.github/workflows/n20-cross-run-precision.yml`. Three independent Ubuntu runner jobs run two fresh Python/Jupyter kernel replays each (six observations) with fixed direct numerical dependencies. Records exact `model_input_sha256`, all coefficient hex fields and restricted host metadata, then performs within-host and across-job comparisons. Classifies exact-bit variation separately from source/model structural changes and tolerance-level energy/coefficient differences. Does **not** generate the original QUBO or run OpenJij/SA; prior 665 vs 698 outcomes #24 remain unresolved pending separate frozen-QUBO experiment. Do not claim causal attribution from digest observations.

**Next gate:** Create/verify scoped stacked draft PR and inspect exact-head CI including 6 individual replays, aggregator, source hashes and potentially differing CPU models; record all observed values (including negative/null results) in #24 and docs. Keep branch draft/unmerged and preserve prior CI science evidence. Original N20 reference v2 and historic source must not be rewritten.

---

# Current Phase 3 task — curated reproducible N20 notebook (2026-10-18)

Branch `science-source-notebook-audit`, draft PR #56, original base `main=41cdc510`. Per owner's request the cleaned, readable N20 source-derived notebook `problems/water_quality/notebooks/water_quality_n20_reproducible.ipynb` has now been created alongside immutable `experiment9 grid search copy.ipynb`. It has **12 Markdown + 11 executable code cells**, explicit assumptions/data checks, 15 real existing stations, 20 FPS candidates, original quadratic energy and local one-hop feasibility, exhaustive 15,504-subset proof, actual PySCIPOpt MILP, selected-site figure, and a machine-readable result. A dedicated `scripts/run_n20_reference_notebook.py` drives fresh-kernel CI with source hashes and scientific canaries. This is proposed as the ongoing **N20 computational reference**, not an unauthorized rewrite of history or a claim that paper Table IV/V is reproducible. The source-only legacy inventory and optional mechanically deduplicated 23-cell candidate are retained as forensic materials; they are not the recommended research notebook. New quick `problems/water_quality/tests/test_clean_notebook_contract.py` also gives previously zero-collection water-quality CI meaningful assertions.

**Gate:** Verify all three workflows and exact resulting scientific metric records, then log details in #5/#6 and PR #56. Keep draft/unmerged. The user's prior Streamlit MVP acceptance is provisional; `main`, `preview` and the production branch must not be updated without separate approval. Historical larger-N and SA studies remain covered by their old documented artifacts; post-cleanup reproducibility study and #16/#24 remain open.

---
# Current review-only science task — 2026-10-18

**Scope:** Phase 3 notebook structural reproducibility audit, issue #5. Feature branch `science-source-notebook-audit` was created from unchanged `main` at `41cdc510`, deliberately independent of the Streamlit MVP release stack. The owner has provisionally accepted the unified MVP for current use; this is **not** authorization to merge, redeploy, change production, or freeze UX permanently.

**Deliverable:** `scripts/notebook_inventory.py`, stdlib-only source-integrity tests, CI workflow `notebook-source-audit.yml`, and `docs/WATER_NOTEBOOK_SOURCE_AUDIT.md`. The source hash is pinned; 25 original code cells, two source-identical second occurrences (14,22), three non-identical repeated sections (4/5,7/8,9/10), and absent saved execution records are documented. An optional working copy excludes only identical repeat text, without executing cells. It is **not** mathematically or execution-equivalent until scientifically evaluated.

**Next gate:** Run the new exact-head CI, log test results in GitHub issue #5, review divergent variants, and independently reconstruct a cold N20 source scenario with rigorous provenance under #6/#16/#24. Original notebook and GeoJSON remain untouched. Previous scaffold checkpoint below is retained as historical, not the current active task.

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