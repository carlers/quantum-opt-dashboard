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