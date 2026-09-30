# Session checkpoint

Updated: 2026-09-30
Current task: Scaffold monorepo for domain-agnostic qopt framework.
Status: Repo skeleton created; framework + plugin are placeholders.
Next action: Implement FC1 (`qopt.core.problem` interfaces) and FC2 (`qopt.core.schemas`).

## Working set
- framework/python/qopt/
- problems/water_quality/src/water_quality/
- docs/SESSION_STATE.md

## Constraints
- Framework must be domain-agnostic: no imports of any plugin.
- Plugins discover via entry points; framework loads by name.
- Every stage declares config_deps and inputs; cache keys derive from these.
- code_version and env_version frozen per job at creation time.
- seed frozen per job; per-unit seeds derived.
- Support multi-domain: at least two plugins must work before shipping v0.1.

## Remaining
- Framework core (FC1..FC11).
- Worker + API (W1..W14).
- Water-quality plugin (P1..P12).
- Frontend (F1..F17).
- Second plugin proves genericity (P2P1..P2P4).
