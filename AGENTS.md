# Working rules

## Layout
- framework/python/qopt/    domain-agnostic framework. Never imports a plugin.
- framework/frontend/       generic control center. Never imports a plugin's
                            code at build time; plugin UI is dynamically imported.
- problems/<name>/          pip-installable plugins. Never import each other.
- apps/worker/              wires framework + N plugins. Thin.
- contracts/                shared JSON schemas.
- framework/supabase/       DB migrations are the source of truth.

## Rules
- Read docs/SESSION_STATE.md first.
- This is a control center: pause/resume/fork/sweep are hard requirements.
- Every stage declares config_deps and inputs. Cache keys derive from these.
- code_version, env_version, seed are frozen per job at creation.
- No plt.show() in library code; artifacts return bytes.
- Framework must work with zero knowledge of water quality (or any domain).
- Two plugins must run before v0.1 ships.

## Definition of done
- Focused tests pass.
- Lint + type check pass.
- Checkpoint updated.
- Diff reviewed.
