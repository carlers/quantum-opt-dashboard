# Working rules

## Layout
- `framework/python/qopt/`   Domain-agnostic framework. Never imports a plugin.
- `framework/frontend/`      Generic control center. Never imports plugin code at
                             build time; plugin UI is dynamically imported.
- `problems/<name>/`         Pip-installable plugins. Never import each other.
- `apps/worker/`             Thin wiring. Framework + N plugins. No domain logic.
- `contracts/`               Shared JSON schemas.
- `framework/supabase/`      DB migrations are the source of truth.

## Workflow — GitHub-connected, PR-only

- All work happens on a feature branch off `main`. Never commit to `main`.
- Branch name describes the task: `<area>-<short-description>`, e.g.
  `framework-problem-protocol`, `worker-jobs-routes`,
  `plugin-water-ingest`, `frontend-job-list`.
- One task per branch. One PR per task. One task per ChatGPT conversation.
- Open the PR with a description that names the task (by its branch name),
  lists files changed, and includes the `pytest` / `ruff` / `mypy` commands
  run locally.
- Do not merge your own PR. The user merges after CI is green and the diff is
  reviewed.
- Update `docs/SESSION_STATE.md` in the same PR. A PR that leaves the
  checkpoint stale is incomplete.
- If the user requests changes, force-push to the same branch. Do not open a
  second PR for the same task.

## Branch protection (configured on GitHub, not in this repo)

`main` requires:
- PR before merge.
- Framework CI (`framework.yml`) green.
- No direct pushes, no force-push.

Never bypass protection even if you have the credentials.

## Scope and correctness

- Read `docs/SESSION_STATE.md` before starting any task.
- Do exactly the task named in the checkpoint's "Current task" or the user's
  prompt. Do not opportunistically refactor neighbors.
- Preserve numerical behavior from the source notebook unless the change is a
  bug listed in `docs/NOTEBOOK_MAP.md`.
- If a task requires crossing a phase boundary (e.g. touching worker code
  during a framework task), stop and ask.

## Framework rules

- `qopt` must not import any plugin. Enforce with `import-linter` in CI.
- Every stage declares `config_deps` and `inputs`. Undeclared reads are bugs.
- Cache keys derive from `StageSpec`. Never hardcode a key.
- `code_version`, `env_version`, and `seed` are frozen per job at creation.
- `run_stage` must be deterministic given (config, inputs, seed, code_version,
  env_version).
- No `plt.show()` in library code. Artifacts return bytes.
- Framework must support at least two plugins before v0.1 ships. If a change
  only makes sense for one plugin, it belongs in that plugin, not the framework.

## Plugin rules

- Config model is a pydantic `BaseModel` with `extra='forbid'`.
- `run_stage` is the only entry point the framework calls.
- `cache_key` must depend on all config fields that affect `run_stage`.
- Outputs must be serializable (`cache_payload: bytes`).
- Plugin must declare `enumerate_units(stage, cfg)` if any stage has units.
- Plugin frontend UI, if any, ships as a separate npm package
  `@qopt/plugin-<name>-ui` and is dynamically imported.

## Testing

- Every PR includes tests for the behavior it introduces.
- Unit tests for pure functions. Integration tests for stage execution against
  a small fixture.
- No `isinstance(x, SomeClass)` tests — they prove nothing.
- No tests that assert private state or internal structure. Test the public
  contract.
- Mark slow tests with `@pytest.mark.slow`. CI runs `-m "not slow"`; slow tests
  run only when explicitly requested.

## Style

- Python: ruff (line length 100, target 3.12), mypy strict.
- Frontend: TypeScript strict, vitest, eslint.
- Commit messages: `type(scope): summary`, e.g. `feat(framework): problem
  protocol (FC1)`.

## Secrets

- Never commit `data/*.geojson`, `results/*`, `.env*`, `*.key`, `*.pem`.
- R2, Supabase service role, W&B keys live in the worker VM's env file.
- Frontend env vars are public (`VITE_*`); worker secrets are not.

## Definition of done

- Task's acceptance criteria met.
- Focused tests pass locally.
- `ruff check`, `mypy`, and `pytest` pass locally.
- CI green on the PR.
- `docs/SESSION_STATE.md` updated.
- PR description names the task ID and lists files changed.
- No unrelated changes.