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