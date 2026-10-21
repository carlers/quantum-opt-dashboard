# Issue #108 — Stage 14: Linux parent-death cancellation for the opt-in original SCIP child

**Parent:** unmerged, six-check-green DRAFT #121 at source HEAD
`01c5882cff0deff345ef8732426a878fcb29bc28`. This child
is also review-only and does **not** change the original scientific
SCIP/graph/QUBO implementation, notebook, factor input, GeoJSON, or manuscript.

## Failure closed when the Streamlit host disappears

Stage 13 ensures normal errors/timeouts call
`os.killpg(child_pid, SIGKILL)` and `wait` in a parent `finally`.
Abrupt OS `SIGKILL`, OOM or a host termination skips that Python
cleanup. A once-independent child could otherwise outlive its
originating Streamlit request and consume resources.

Now the **separate Linux child** itself invokes
`prctl(PR_SET_PDEATHSIG, SIGKILL)` via Linux libc `ctypes` *before*
loading or executing the original `model.solve_scip`. The parent
supplies its own PID as a typed internal command-line argument (not
user-supplied); after arming kernel parent-death signaling the child
checks `os.getppid()` equals that expected PID. If its parent
already disappeared before signal setup, it fails closed. If the
kernel supports neither this call nor the expected parent chain, the
worker terminates without falling back to the in-process SCIP path.

A new test launches a disposable intermediate launcher, which
starts a Python child that arms exactly the same kernel parent-death
protection and announces its own PID. The controlling pytest then
kills **only the intermediate parent** with real `SIGKILL`.
It waits for the protected child to be missing or zombie in
Linux `/proc`, without invoking cleanup before that observation;
only afterwards can its finalizer kill/reap residual process-group
members. This isolates the mechanism from the original scientific
SCIP computation. The existing actual original N20 SCIP subprocess
and same-host concurrent-requests/ZIP tests still must pass.

## Limits deliberately retained

This is Linux/locally scoped cancellation improvement, **not**
production user isolation. `PR_SET_PDEATHSIG` tracks the child's
current direct parent, not arbitrary grandchildren, nested SCIP helper
executables, a Kubernetes job graph or a remote service. The kernel
may leave stopped processes as zombies until reaped; a missing-or-zombie
observation shows the worker stopped executing, not guaranteed external
reaping. It cannot establish cgroup v2 resident memory, total subtree
CPU quotas, denial-of-service resistance, per-user identity/rate limit,
authenticated admission, or signed source receipt. The opt-in
`QOPT_REVIEW_BOUNDED_SCIP=1` is still OFF by default; no permanent
Cloud preview, ZIP browser download or deployment has been performed.

All tests must run on the new exact source HEAD in Python 3.12
with `prlimit`, standalone/local Streamlit scientific workflows,
real Chromium two browser contexts, prior simultaneous bounded LP
re-solvers and the **separately pinned original source notebook/SCIP/
5,417-feature GeoJSON/S4/global graph vs current UX**. The GitHub
synthetic merge test checkout SHA is not interchangeable with the
source PR HEAD. GitHub CI ZIP digests are unsigned and retained only
14 days; not a durable academic research archive.

The historical original **local one-hop** N20/K5 scenario has
1,077/15,504 feasible assignments; the distinct exploratory
all-15-original-fixed globally connected scenario has 860/15,504,
global feasible set SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
and both select free-site indices [0,1,3,6,7] under their different
assumptions. Strict original binary64 objective SHA modes
`2b238848...` and `8536a3db...` are distinct; AHP/D2 paper
WorldPop versus historical road inputs, measured physical RF/DO/
current/backhaul and quantum advantage remain unverified. OpenJij
SA is classical.

No merge, deployment, preview staging, remote signing, scientific
source code rewriting or closure of Issue #108 is authorized.
