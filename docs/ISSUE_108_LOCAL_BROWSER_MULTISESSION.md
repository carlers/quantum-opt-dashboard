# Issue #108 — Stage 5 local two-browser Streamlit overlap (REVIEW ONLY)

**Parent**: DRAFT #112 (qualified water adapter) source HEAD
`554db020f3abb9b3a566b7a430b24810c2ccb408`; no
merge, rebase, `main`, permanent `preview`, deployed production, source
notebook, 5,417-feature original GeoJSON, source model or manuscript edit.
Independent scientific source DRAFT #96 stays pinned in its separate
checkout.

## Purpose: real browser concurrency, not fake AppTest sequencing

Stage 1–4 imports/Streamlit AppTests established sequential module origins,
while Python's `sys.path` and `sys.modules` remain process-global.
`AppTest` cannot claim two true overlapping browser/WebSocket sessions.

A new **test-only** GitHub Actions job
`.github/workflows/unified-browser-concurrency.yml` installs current
root Python 3.12 research runtime and **Playwright Chromium solely in the CI
job**. It starts one ephemeral local Streamlit server bound **only to
127.0.0.1** on a free port, performs an actual Streamlit
`/_stcore/health` check, then creates **two distinct Chromium browser
contexts**, separate pages, and two real Streamlit WebSocket connections.
Both contexts stay alive while actions are concurrently scheduled with
`asyncio.gather`.

The full local route matrix is:
| Observation | Browser A | Browser B |
| --- | --- | --- |
| Connected baseline | water | water |
| Overlap 1 | custom editor | QUBO research |
| Overlap 2 | About | water |
| Overlap 3 | QUBO research | custom editor |
| Overlap 4 | water | About |

Each route checks the actual Streamlit page heading, no Streamlit exception
element and no other session's route heading. The script checks both
connections are genuinely observed, captures PR source HEAD and actual
GitHub checkout SHA **separately**, terminates the local server even on
failure and emits a JSON observation with its scientific/security limits.
If any browser connection, navigation, heading, source SHA or required
state check fails, the workflow **fails**. A 14-day CI artifact includes
the JSON and local server stdout/stderr; it does not include original
GeoJSON or a fake signed result.

## What this does NOT establish

A successful test demonstrates navigation liveness and distinct browser
contexts under limited simultaneous activity, **not** malicious cross-user
import-path isolation, hot-reload import collision resistance, capacity
under multiple concurrent 30-second SCIP solver runs, per-user OS quotas,
session authorization, signed output, native numerical reproducibility,
actual `st.download_button` retrieval, or a Streamlit Cloud preview
browser acceptance. The test deliberately does not run a solver, classical
SA, force CPU/memory overload, stage public preview or push to `preview`.
A fuller qualified import migration or OS worker boundary remains
necessary. Cloud browser and ZIP acceptance still requires explicit owner
permission to update the permanent preview first.

Original historical one-hop local N20/K5 source feasible
**1,077/15,504**, separate all-15-fixed exploratory modeled global
**860/15,504**, global feasible set SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
source optimum **[0,1,3,6,7]**, strictly distinct observed
binary64 coefficient SHA `2b238848...` and `8536a3db...`.
Nothing in Chromium navigation validates author AHP/D2 WorldPop input
parity, field RF/backhaul/DO/current, or quantum advantage; OpenJij
SASampler is classical. Historical author scientific source and pinned
source-vs-UX independently executed checks remain separate and required.

Stage 5 is an **independent review-only DRAFT**; none of these tests or
artifacts is permission to merge, deploy, stage preview or rewrite the
scientific source.
