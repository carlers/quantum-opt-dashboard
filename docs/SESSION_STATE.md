# Independent scientific data-source discovery — review-only (2026-10-19)

**Current scoped branch:** `research-laguna-authoritative-data-intake-ledger` based on unchanged `main` for [Issue #87](https://github.com/carlers/quantum-opt-dashboard/issues/87). This *documents publicly verifiable provider leads only*: LLDA official FOI waterbody/monitoring station/DO request histories and the distinct WorldPop 2020 Philippines dataset variants/DOIs. See `docs/research_results/LLDA_WORLDPOP_ACQUISITION_LEDGER_2026_10_19.md`.

**NOT acquired/authorized:** project-specific LLDA shapefiles, original AHP expert worksheets, QGIS/D2 raster process, source shoreline with island holes, calibrated water-quality time series, measured radio/backhaul, any new model parameter range or permission to redistribute upstream data. `SUCCESSFUL` third-party FOI records are not equivalent to retrievable or reproducible original project data. Historical original notebook and GeoJSON remain unchanged.

**Independent workstreams:** mathematically source-only draft #86 and adapter DRAFT #89 are *separate unmerged research branches*; UI global topology draft #78 is also separate. This data-discovery branch introduces no app, solver, notebook or other branch integration.

**Next steps:** review this ledger's official evidence links and constraints in Issue #87; request source assets and reuse rights from LLDA/experts; only after metadata and license verification create independent structured GIS intake/reproducibility tests. Do not change main, preview or production, merge, deploy or publish a new physical model without separate approval.

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