# Plan

## Framework core (python) — FC1..FC11
Interfaces, schemas, registry, cache, keys, tracker, storage, DAG, executor, compare, sweep.

## Worker + API — W1..W14
Migrations, FastAPI app, auth, routes (jobs/experiments/problems/artifacts),
SSE, worker pool, lifecycle, pause, cron, rate limit, container.

## Water-quality plugin — P1..P12
Config, ingest, scale, build, solve, grid, analyze, render, cache_key,
enumerate_units, UI bundle, notebook wrapper.

## Frontend — F1..F17
Auth, API client, SSE client, submit (schema-driven), job list, job detail,
control bar, edit sheet, fork dialog, sweep launcher, experiment DAG,
artifact gallery, live metrics, comparison, plugin UI loader, PWA, Vercel.

## Second plugin — P2P1..P2P4
Prove genericity by shipping another domain without framework changes.
