# Plugin specification

A plugin is a pip-installable Python package exposing a `Problem` object via
the `qopt.problems` entry point.

## Required
- `name`: str
- `version`: str (semver)
- `display_name`: str
- `config_model`: pydantic BaseModel (extra='forbid')
- `stages`: tuple[StageSpec, ...]
- `run_stage(stage, ctx) -> StageResult`
- `cache_key(stage, cfg, inputs) -> str`

## Optional
- `enumerate_units(stage, cfg) -> list[str]`
- `default_tracker(job_id) -> Tracker`
- `interrupt_handler(stage) -> Callable` (for hard pause)
- frontend UI bundle (npm package `@qopt/plugin-<name>-ui`)

## Rules
- `run_stage` must be deterministic given (cfg, inputs, seed, code_version, env_version).
- `cache_key` must depend on all config fields that affect `run_stage`.
- Declared `config_deps` must be complete; undeclared reads are bugs.
- Outputs must be serializable.
- No `plt.show()` — artifacts return bytes.
