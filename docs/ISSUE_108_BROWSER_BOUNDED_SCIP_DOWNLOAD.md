# Issue #108 — Stage 15: two real local browser SCIP solves and actual downloaded evidence ZIPs

**Parent:** review-only, six-workflow-green DRAFT #122 source HEAD
`a81df536644bce97ad76dd04db6df3fc89c4a223`. This separate
child draft never merges independent original author source DRAFT #96.

## Previously untested user journey

Earlier AppTest controls exercised original SCIP and inspected its ZIP
in Streamlit session state, and the Stage 5 browser workflow observed
two genuinely independent Chromium/WebSocket contexts navigating
the scientific workbench **without clicking solve or download**.
Neither is an actual browser download acceptance test.

This stage adds `scripts/browser_bounded_scip_download.py` and one
dedicated Ubuntu 24.04 / Python 3.12 / Playwright Chromium CI job.
It starts a real ephemeral `127.0.0.1` unified Streamlit server
with the operator-only environment variable
`QOPT_REVIEW_BOUNDED_SCIP=1` set **only on that disposable local
server**, never in the current Cloud preview or default deployment.
Two independent browser contexts open distinct Streamlit WebSockets,
verify the default original local N20/K5 page, and invoke
`Find monitoring locations (SCIP)` via asynchronous concurrent
browser-button actions. Each must independently observe the original
SCIP optimal status and perform the browser's actual
`Download experiment, verified result and actual SCIP LP (.zip)`
download via Playwright's `expect_download`, not by accessing hidden
Streamlit session state or manually constructing a ZIP.

The script independently inspects both **downloaded binary ZIPs**
inside ephemeral CI browser download storage. Each ZIP must contain
exactly the original `model.json`, `result.json`,
`selected_sites.csv`, `actual_scip_model.lp` and
`SHA256SUMS.json` documents; all member digests are verified.
The model fingerprint and original GeoJSON SHA are checked against
the result and checksum manifest. The original source-based
independent SCIP LP parser runs on the **actually downloaded LP
bytes** against a newly constructed source original N20/K5
`model.Instance`; budget, local one-hop constraints, variables,
quadratic-product linearization and source objective must match.
Each archive must independently certify the [0,1,3,6,7]
candidate selection in the original local one-hop model.
All observations record source PR HEAD separately from GitHub
synthetic test-merge checkout SHA.

**No downloaded ZIPs, original LP binary or original lake GeoJSON
are uploaded as GitHub artifacts.** Only a bounded JSON report
with archive/original-LP/source SHA256s and local server logs is
retained for 14 days; this is unsigned ephemeral review evidence,
not a permanent academic research archive or remote attestation.

## Limits and nonclaims

Concurrently initiated browser clicks do **not** prove that both SCIP
optimizations executed at precisely the same OS instant; the
separate Stage 11 shared-gate workflow actually proved two independent
bounded LP solver child processes overlapped, under its own
N20 model scope. Both browser sessions do run under the opt-in
Stage 13 bounded local SCIP subprocess adapter and Stage 14
parent-death safety. This workflow verifies a real UI download
**on the same-host ephemeral loopback app**, NOT the current
permanent Streamlit Cloud preview, deployed authentication,
browser permissions or a production network path.

It does not stress cgroup resident RAM/CPU exhaustion, prove
tenant isolation from arbitrary hostile Python affecting shared
`sys.modules`, eliminate forged qualified namespace hooks,
certify real-world RF/backhaul/dissolved-oxygen/current sensor
performance, match author manuscript WorldPop criterion D2
historical source road scoring, sign remote provenance, or show
a quantum processor/advantage; OpenJij is classical SA. The
Linux `RLIMIT_AS` values only limit virtual address space, not
resident memory. The review-only operator flag remains disabled by
default and is **not** enabled in Cloud.

Historical original one-hop local N20/K5 feasibility is
1,077/15,504. Distinct all-15-fixed exploratory global connected
graph feasibility is 860/15,504 with membership SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`;
both select [0,1,3,6,7] under their distinct assumptions.
Strict original IEEE754 objective coefficient SHA modes
`2b238848...` and `8536a3db...` are not interchangeable.

No merge, staging/deployment, protected `main`/`preview` update,
signed remote result, source notebook/5,417-site GeoJSON/S4/manuscript
or original scientific `model.py`/SCIP/QUBO change. Issue #108
remains OPEN pending hostile qualification/production scope and
explicit owner approval for any Cloud preview tests/deployment.
