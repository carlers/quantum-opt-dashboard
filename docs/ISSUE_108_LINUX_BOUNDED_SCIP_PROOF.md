# Issue #108 — Stage 11: two Linux-bounded original LP re-solvers (review-only)

**Parent:** source-science-green, unmerged DRAFT #118, exact parent source HEAD
`41761edd22e5e036176461442831ce33d191f149`. This is a
separate review-only child DRAFT. Independent original author-science
DRAFT #96 continues to be pinned and checked in a **separate cold**
source tree rather than being merged.

## Research hypothesis and narrow measurable evidence

A 30-second `SCIP limits/time` parameter limits a solver's own
optimization time: it is **not** a Linux process CPU, virtual-memory,
open-file, output-size, or wall-clock quota, and it cannot clean up a
stuck child process. The existing unchanged N20
`scip_lp_reexecution_worker.py` already accepts a SHA256-verified
actual SCIP `.lp` file and reads/optimizes it in an independent process.
The workflow tests whether **two** such existing workers can be
released at once with actual **kernel-enforced** Linux resource ceilings
and subsequently mathematically checked against source N20 feasibility.

The new test-only driver
`scripts/issue108_bounded_scip_concurrency.py`:

1. Constructs the unchanged original N20/K5 *local one-hop* model
   using the original `model.py` and committed GeoJSON in a temporary
   directory. Executes original `solve_scip` with real CPLEX LP export;
   demands optimum, source-local feasible incumbent, and structural
   LP certificate/digest. No JSON or LP from an invented synthetic
   problem is substituted.
2. Launches two distinct isolated process groups with `subprocess.Popen`
   and Linux util-linux `prlimit` **before Python runs**.
   Exact observed limits: CPU soft 55 / hard 60 seconds per child;
   `RLIMIT_AS` 4 GiB virtual address space; `RLIMIT_FSIZE` 1 MiB;
   `RLIMIT_NOFILE` 256; plus shared wall-clock deadline 75 seconds.
   Does not use `preexec_fn` (unsafe in multithreaded callers), a
   shell command, inherited mutable `sys.modules` or filename from
   an untrusted Streamlit request. Sets child numerical library
   thread counts to 1.
3. Both child entrypoints persist their **actual kernel**
   `resource.getrlimit()` receipt, and block on the same control gate.
   The parent requires both distinct PIDs to be alive and ready,
   checks recorded kernel limits and only then releases the gate.
   Each process `os.execv`s the original **unchanged** LP SCIP reader:
   CPU/AS/NOFILE/FSIZE constraints survive `exec`, and both read the
   same verified original LP digest in newly initialized SCIP processes.
4. The parent enforces one 75-second deadline for both workers, caps
   stdout size, refuses nonzero exit/bogus status/invalid JSON, and
   uses the original existing `scip_lp_reexecution.py` analytical
   verifier (loaded by *fixed source path*, not through an unsafe
   bare `sys.path` manipulation) to compare each child's emitted
   actual LP, primal, dual, gap, original feasibility and exact
   binary64 N20 objective against the upstream source optimum.
   Both source/child optimal positions must be [0,1,3,6,7] for this
   exact study scenario in the CI acceptance contract.
5. In `finally`, terminates/reaps **both** process groups even if a
   child crashes or a validation fails. Separate negative-control
   unit test starts a bounded process waiting on a gate that is never
   opened, reads its real kernel-limit receipt, explicitly kills its
   process group and verifies it was reaped. It never runs SCIP.
6. Produces **only unsigned, bounded numerical/OS metadata** JSON
   to the CI artifact. No full GeoJSON, original LP file or source
   manuscript is re-distributed in that artifact. Record actual
   GitHub source PR HEAD separately from the synthetic test checkout
   and use 14-day artifacts only for short-lived review evidence.

The dedicated Ubuntu 24.04 Python 3.12 workflow
`.github/workflows/issue108-bounded-scip-workers.yml` must pass
in addition to existing installed Python/provenance, unified
Streamlit/SCIP pilot, two-live-Chromium local browser navigation,
synthetic adapter tests and the separately pinned original cold
science/UX workflow **on the same new actual PR source HEAD**.

## Precisely what this does NOT prove

This is an independent **test-only worker proof**, not a replacement
for the live Streamlit `model.solve_scip` call, and does not route
actual user sessions or downloads through separate subprocess workers.
Linux `RLIMIT_AS` limits virtual address space, **not a cgroup
resident-RAM guarantee**; observed configured values are **not** a
memory-exhaustion stress test or independent OS hardening audit.
`RLIMIT_CPU` is process CPU, not complete parent/descendant-tree CPU
accounting. There is no per-user fair-share queue, authentication,
limit on concurrent total users, cgroup v2 worker pool, public
Cloud staging, real browser ZIP click, KMS signature, distributed
trust root or external remote attestation. A hostile user executing
arbitrary Python inside the **same** Streamlit process can still
manipulate process-global `sys.modules`, import hooks and startup
site packages; the Stage 10 origin guard is not atomic isolation.

A malicious original/worker executable or privileged process can
falsify the local receipt. The new `prlimit` launcher is only
available on Linux; it must fail closed rather than silently fall back
to an unbounded worker on another OS. Review and deploy a separately
designed genuine production worker-process service with subprocess
response contract, cancellation, OS quotas and science/original
source compatibility if/when explicitly approved. Do not infer
production runtime isolation from the local CI experiment.

## Pinned academic and scientific boundaries

Original author notebook, 5,417-feature GeoJSON, S4 factor inputs,
historical water compiler/SCIP/graph math, original QUBO/SA modules
and manuscript are **unchanged**. This test uses the source one-hop
N20/K5 model where 1,077/15,504 are feasible. It does **not**
substitute the distinct exploratory all-15-original-fixed *global*
graph (860/15,504 feasible, membership SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`).
Both have best candidate positions [0,1,3,6,7] under their separate
assumptions. Independently observed strict original source float64
objective SHA modes `2b238848...` and `8536a3db...`
are distinct and not interchangeable. Manuscript AHP/D2 population/
WorldPop versus historical D2 road input parity, physical Lake RF,
DO/current/backhaul observations, and quantum hardware or quantum
advantage remain unverified. OpenJij SASampler is classical.

No merge, preview staging, live permanent Cloud deploy, original
scientific source rewriting, signed attestation or closure of Issue
#108 is authorized. The next stages must test actual **live**
isolated SCIP user-session integration, malicious qualified-module
collisions and surviving OS worker processes under interruption.
