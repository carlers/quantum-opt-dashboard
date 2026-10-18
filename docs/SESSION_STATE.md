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