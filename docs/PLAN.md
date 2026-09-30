# Plan

## Task and branch naming

Each task is one branch, one PR, one ChatGPT conversation.

Branch name = task name. Format: `<area>-<short-description>`.

Areas: `framework-`, `worker-`, `plugin-water-`, `plugin-hello-`,
`frontend-`, `docs-`.

Example task names:
- `framework-problem-protocol`
- `worker-jobs-routes`
- `plugin-water-ingest`
- `frontend-job-list`

Read the task name as a sentence: "framework, problem protocol". No
mnemonics, no IDs to memorize.

## Framework
- `framework-problem-protocol` — Problem, StageSpec, contexts, Tracker
- `framework-plugin-registry` — Entry-point discovery
- `framework-cache-keys` — Cache-key derivation
- `framework-cache-storage` — Disk + R2 tiered cache
- `framework-stage-executor` — Runs one stage-unit
- `framework-trackers` — W&B + Optuna
- `framework-storage-clients` — Postgres + R2
- `framework-dag` — Dependencies + cycle detection
- `framework-compare-stage` — Built-in comparison
- `framework-sweep-expansion` — Sweep → DAG
- `framework-hello-world-plugin` — Second plugin

## Worker
- `worker-db-migrations`
- `worker-fastapi-app`
- `worker-auth`
- `worker-jobs-routes`
- `worker-experiments-routes`
- `worker-problems-routes`
- `worker-artifacts-routes`
- `worker-sse-events`
- `worker-slot-pool`
- `worker-job-lifecycle`
- `worker-pause-resume`
- `worker-cron`
- `worker-rate-limit`
- `worker-docker-deploy`

## Water-quality plugin
- `plugin-water-config`
- `plugin-water-ingest`
- `plugin-water-scale`
- `plugin-water-build`
- `plugin-water-solve-scip`
- `plugin-water-grid-search`
- `plugin-water-analyze`
- `plugin-water-render`
- `plugin-water-cache-keys`
- `plugin-water-unit-enum`
- `plugin-water-ui-map`
- `plugin-water-notebook-wrapper`

## Frontend
- `frontend-vite-auth`
- `frontend-api-client`
- `frontend-sse-client`
- `frontend-submit-form`
- `frontend-job-list`
- `frontend-job-detail`
- `frontend-control-bar`
- `frontend-edit-sheet`
- `frontend-fork-dialog`
- `frontend-sweep-launcher`
- `frontend-experiment-dag`
- `frontend-artifact-gallery`
- `frontend-live-metrics`
- `frontend-job-compare`
- `frontend-plugin-ui-loader`
- `frontend-pwa-notifications`
- `frontend-vercel-deploy`