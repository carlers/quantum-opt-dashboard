# Independent spatial adjacency audit continuation — 2026-10-19

**Owner requests continued work with explicit “Next steps” in each response.** New review-only branch `science-n20-independent-spatial-adjacency` stacked on [draft #66](https://github.com/carlers/quantum-opt-dashboard/pull/66) → [curated working N20 draft #56](https://github.com/carlers/quantum-opt-dashboard/pull/56), without changes to existing numerical-precision PRs #57/#61/#63. No permission to merge or deploy.

**New isolated source-geometry gate** `scripts/n20_independent_geometry_audit.py` recreates the original GeoJSON 5,417-point concave hull and 20+15 site positions directly from immutable source bytes, derives original fixed spacing via stdlib hypot, and independently rebuilds 190 possible free/free and 300 free/fixed one-hop links from hull-contained segments. It compares every free neighbor and fixed-neighbor flag exactly against notebook-emitted model fields, independently recomputes 1,077 K5 feasible subsets and their ordered SHA, and records all direct free/fixed link identities, geometry SHA and Dmax proximity. No reweighting, notebook-model correction, QUBO, stochastic sampling or SCIP change. Same Shapely/GEOS hull semantics remain a scientific limitation, not independent shoreline verification.

New test `scripts/tests/test_n20_independent_geometry_audit.py` falsifies changed nonselected graph links, source coordinate/spacing/candidate flags, U-shaped polygon cross-land connections, boundary-point adjacency and 1e-7m threshold ambiguity; original actual GeoJSON reconstruction belongs to `.github/workflows/notebook-n20-replay.yml` after fresh SCIP notebook replay and is published as second bounded 14-day artifact. Protocol and boundaries are recorded **before examining actual geometry results** in `docs/N20_INDEPENDENT_SPATIAL_REVIEW.md`.

**Next steps:** open stacked DRAFT PR; run CI and resolve genuine geometry source discrepancies without modifying archived files or the model; archive exact result; update Issues #5/#6/#2 and PR descriptions; seek research-team review before eventual canonical source acceptance or merge.

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