# Issue #108 — Stage 16: distinct K=5 and K=4 browser sessions, independent LP/ZIP evidence

This review-only child is stacked on seven-gate-green DRAFT #123,
exact parent source SHA
`3f88fd30e8af266f157d55d163c2fa67aa6f3704`.
Original scientific author-source DRAFT #96 remains independently
cold-pinned and unmerged. No source notebook, 5,417-feature
GeoJSON, S4 factors, scientific `model.py`/SCIP/graph/QUBO
compiler or manuscript edits.

## Why two identical K5 browser downloads were not sufficient

Stage 15 demonstrated two independent Chromium WebSockets, concurrent
UI solve clicks, and real independently mathematically checked ZIP
downloads, but both contexts used the **same N20/K5 input**. Identical
results cannot detect all accidental result-copy/cross-session bleed.
This new test parameterizes that same original local source scenario
without changing scientific model assumptions: browser A remains
**N20/K5**, while browser B changes the sidebar
`New sensors to place (K)` input to **N20/K4**.

The test explicitly waits for B's new input to settle and checks
A's K5 remains unchanged. Both trigger the operator-only
`QOPT_REVIEW_BOUNDED_SCIP=1` experimental Linux subprocess
solver in concurrently initiated browser button actions. Each real
browser session downloads its own ZIP using the genuine Playwright
download event. Each ZIP must pass all existing Stage 15 member
SHA-256 checks, original source GeoJSON digest and model fingerprint,
current result mathematical attestation, and source LP structural
certification. A browser archive's reported `budget_rhs` must equal
its own 5/4, its `water-mvp-<fingerprint>` filename must match its
own complete fingerprint, and the two archive byte digests and model
fingerprints **must differ**.

To avoid treating original SCIP's status alone as an independent
optimality oracle, the runner now also enumerates every combination
of K distinct indices from 20 source candidates separately for each
archive (20 choose 5 = 15,504; 20 choose 4 = 4,845). It applies
the ORIGINAL *local one-hop* feasibility rule using original fixed
station neighbors and selected free-neighbor adjacency, and directly
sums original source linear and quadratic terms for each feasible
assignment to cross-check the downloaded selection has minimum
source objective (1e-7 tolerance). The historical K5 count must
remain exactly 1,077. K4's feasible count is **observed** from the
original source run, not guessed from the source-paper or converted
to global graph feasibility. This is an additional independent
enumeration path to the original SCIP LP structure check; it does
not assert an externally validated real-lake physical graph.

The new dedicated
`.github/workflows/issue108-browser-distinct-budgets.yml`
uses the same actual local Playwright/Streamlit/SCIP runtime as the
previous dedicated browser ZIP workflow and runs
`scripts/browser_bounded_scip_download.py --different-budgets`.
Its exact-source-HEAD approval requires distinct first/second
fingerprints, ZIPs and K counts, two independent source LP structural
certificates, bounded numerical evidence and no session exception.
Both original baseline same-K5 browser workflow and this distinct
scenario must pass on the same proposed source HEAD, alongside
installed Python3.12, full SCIP/Streamlit pilot, unified app,
two-local-browser navigation, Linux kernel-bounded original source LP
worker and independently pinned cold original N20 notebook,
5,417-site GeoJSON/S4/global graph source-science vs current UX.

## What it cannot prove

These are independent local Streamlit ScriptRunner sessions with
distinct source inputs, **not malicious arbitrary Python running
inside the same process**. They rule out observed ordinary
cross-session stale ZIP/fingerprint bleed for these budgets but
do not atomically isolate global `sys.modules`, defend against
arbitrary hostile qualified package cache takeover, certify
multi-tenant admission/authentication, or bound cgroup resident RAM
on Cloud. Concurrency of UI clicks does not prove simultaneous
wall-clock SCIP optimization; prior separate gated worker test
covered two concurrently executing original LP child processes.
The operator flag remains OFF by default; no production Cloud
preview or real deployed browser is tested or modified.

Original source local one-hop N20/K5 has 1,077/15,504 feasible.
A distinct exploratory all-15-existing-fixed global graph model
has 860/15,504 feasible and membership SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`.
These are not interchangeable. Original float64 coefficient SHA
modes `2b238848...` and `8536a3db...` are distinct;
manuscript D2 WorldPop-versus-road scientific parity, empirical
RF/dissolved oxygen/current/backhaul and quantum advantage are
unverified (OpenJij SA is classical).

GitHub artifacts hold only unsigned bounded SHA/model-observation JSON
and ephemeral local Streamlit server logs for 14 days, not original
author data/LP/ZIP bytes or durable signed scientific archival.
No merge, staging, preview deployment, owner-side signing,
unapproved scientific assumption or closure of Issue #108.
