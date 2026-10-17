# Active scientific-validation checkpoint (2026-10-18)

- Active priority: N=20 water-quality original-notebook → pilot SCIP scientific parity; see roadmap #2, issue #12 and #6.
- Live deployment branch: `plugin-water-streamlit-pilot` (do not update or merge without user approval).
- Earlier draft PR #13 targets `main`; PR #14 targets live branch but remains unmerged.
- Current scoped work: `science-n20-scip-parity` is stacked on PR #14's unmerged head; new PR targets `plugin-water-scip-regression`, which is **not** live.
- Adds independent source-formula/geometry reconstruction, exhaustive 20-choose-5 reference and real SCIP regression tests; scientific evidence document: `prototypes/streamlit_water_quality/N20_VALIDATION.md`.
- This branch makes no solver/UI/data/notebook changes. No claims of paper parity until exact paper inputs and notebook cache provenance can be verified.
- User-confirmed working Streamlit URL: https://v3wzqpbn8w6nmdgkxh5kum.streamlit.app/.
- Next: review N20 CI manifest, inspect unexpected deltas, obtain the live app's N20 settings/output and reconcile published 15 fixed stations versus GeoJSON/fallback. Seek explicit approval before any merge that updates live Streamlit.

---

## Historical scaffold checkpoint (2026-09-30; superseded by issue #2 / #12)

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