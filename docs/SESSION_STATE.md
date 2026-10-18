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