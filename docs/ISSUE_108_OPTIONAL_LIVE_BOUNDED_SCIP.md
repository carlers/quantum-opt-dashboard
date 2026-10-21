# Issue #108 — Stage 13: explicitly opted-in bounded SCIP from the actual water Streamlit route

**Review only.** Parent is nine-gate-green, unmerged DRAFT #120
at source HEAD `fecbee11c7072efb3abf6461217a81d63269d967`.
Independent original scientific author-source DRAFT #96 stays pinned
and separately cold-checked, never merged or edited.

## Integration, deliberately disabled by default

The original historical local one-hop Streamlit water page still invokes
its unchanged `model.solve_scip(instance, time_limit=30,
export_lp_path=...)` by default. **Only** explicit environment
`QOPT_REVIEW_BOUNDED_SCIP=1` changes that call site, to
`prototypes.isolated_water_scip.solve_scip_bounded`. That opt-in is
exercised in CI with a real routed `AppTest` pressing `mvp_run`.
There is **no** silent fallback to in-process SCIP when the Linux
resource tool is missing, any child fails, a 75-second deadline expires,
the admission slots are occupied or source coefficients differ.
No version of this optional flag has been enabled in permanent
`preview` or production.

The parent Streamlit ScriptRunner still independently constructs the
same original `model.Instance` in the same way, including original
N20 candidate locations, original 15 fixed stations, source exact K,
floating objective coefficients, graph neighbors and penalties. The new
`prototypes/isolated_water_scip.py` adapter serializes the **already
constructed instance** into strict bounded JSON with canonical
`float.hex()` representations of every binary64 coefficient/coordinate,
never pickles a Python object, arbitrary executable or callback.
It binds source-model file SHA256, random per-request nonce and exact
request SHA256. Its child is a brand-new `python -I` process under
Linux util-linux `prlimit`, which verifies all bounds and the exact
original scientific `model.py` file hash before reconstructing the
original `Instance` class and calling **unchanged**
`model.solve_scip` with the original 30-second SCIP limit.

The kernel limits are CPU soft/hard 55s/60s, Linux virtual address
space 4 GiB, file size 1 MiB, open file descriptors 256. There is
one 75-second wall-clock deadline, temp directory 0700, no shell,
isolated child process group and explicit kill/reap `finally` path.
Linux `flock` admission permits at most two opted-in child processes
per OS user across concurrent local requests; a third is rejected
without blocking. The parent requires a bounded JSON result, exact
nonce/input/model source SHA, 20 binary site flags, source
`model.evaluate` feasibility, original objective within 1e-7, finite
solver status/gap and actual emitted SCIP LP SHA. It reruns the
**original unchanged** `scip_lp_structure.certify_emitted_scip_lp`
against the original **parent** instance before copying the LP into
the existing normal evidence path. The existing
`mvp_audit.check_selected`, `attest_current_result`, source model
fingerprint and evidence ZIP tests execute afterwards as before.
No altered scientific compiler or detached source oracle.

## Required actual demonstrations

- Cold Python 3.12 install and `pip check`; pure source Instance
  hex-float serializer roundtrip with exact coords, coefficients and
  pair lists, no pickle.
- Real child Linux SCIP with original N20/K5/LP, actual emitted LP
  structural verifier and expected exact selected source sites.
- Negative malformed request checksum is rejected before SCIP starts.
  Both local Linux admission slots are occupied and a third must fail
  without queueing/fallback. Two concurrent parent threads submit
  independent fresh child solves, each returning validated optimum.
- Real unified Streamlit `AppTest` opt-in `mvp_run` produces the
  existing *original* source-local optimum and re-attested ZIP with
  actual emitted SCIP LP and correct fingerprint; the normal
  default-off app tests also run with unchanged in-process source SCIP.
- Full pilot/SCIP/LP/ZIP, unified scientific editor, local overlapping
  Chromium browser sessions, Stage 11 genuine gated dual Linux
  original-LP worker tests and **independently pinned cold original
  notebook/5,417-feature GeoJSON/S4/global graph source versus UX**
  all required at the **same new PR source HEAD**; record synthetic
  merge-checkout SHA separately.

## Limitations; NOT an arbitrary user security boundary

This is a review-only **opt-in local Linux child** with a small bounded
admission control. It does NOT mean all Streamlit source-local
`solve_scip` paths now run out of process, does NOT give different
authenticated users distinct operating-system identities, and does
NOT protect the parent process from malicious Python already running
with Streamlit privileges, forged qualified packages or arbitrary
`sys.modules` monkeypatching. Stage 10 import-origin checks remain
non-atomic. The parent still builds/attests the original source model
and globally modeled exact enumeration remains a separate in-process
non-SCIP computation; the explicit opt-in does not change it.

`RLIMIT_AS` is virtual address space, **not** a cgroup resident-memory
guarantee. `RLIMIT_CPU` is per process, not a complete descendant
hierarchy or multi-user quota. Linux `flock` coordinates requests on
one local filesystem/OS account, not a geographically distributed
fair-share queue or production database admission controller.
The test does not simulate malicious memory exhaustion, high-volume
multi-tenant load, process privilege separation, portable Windows/macOS
security, hostile qualified import hooks, remote cryptographic signing,
real Cloud browser ZIP-click acceptance or survival of arbitrary
forking descendants. The child inherits the same filesystem/UID and
packages as its parent; only its resource limits/process lifetime
are distinct. The local checksum/nonce verify consistency, **not**
trust against a compromised app host.

**Scientific and paper boundaries:** original source one-hop
N20/K5 1,077/15,504 feasible vs different exploratory all-15-fixed
global graph 860/15,504, global membership SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
source optimum sites [0,1,3,6,7]. Different strict original
binary64 coefficient SHA modes `2b238848...` and `8536a3db...`
are not interchangeable. Manuscript AHP/D2 WorldPop population
versus historical D2 road parity is still unresolved; measured
lake RF/backhaul/dissolved oxygen/current is not validated,
and classical OpenJij SA is not a quantum advantage claim.

No change to original author notebook, 5,417-feature source GeoJSON,
S4, manuscript, `model.py`, QUBO/scip/graph/compiler/verifier
scientific implementations or independent science DRAFT #96.
Only the review flag branch in original water **UI** code, installed
non-scientific subprocess adapter, tests, workflows and docs change.
No merge, preview staging, production deploy, remote signer, science
input rewrite or issue closure authorized by passing CI.
