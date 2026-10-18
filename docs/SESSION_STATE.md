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