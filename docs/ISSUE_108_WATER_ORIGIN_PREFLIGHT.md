# Issue #108 — Stage 8: preloaded water-module origin guard (review only)

**Ancestor:** green, unmerged DRAFT #115 source HEAD
`fa0e6e65b1c3c192c24ba417df4b14e199b607b2`. This is a
new **child DRAFT**, not a merge into main, preview, production or the
separately pinned author-source science DRAFT #96.

## Why this bounded step is necessary

The original Streamlit water pilot and research/SA modules retain
unqualified `from model`, `from mvp_audit`, `from qubo`, etc.
The unified water wrapper and research page currently prepend the
water scientific prototype directory to **process-global** `sys.path`.
Python consults process-global `sys.modules` **before** path search:
a preloaded foreign `model` can defeat even a correct directory insertion.
Simply importing the water code under `prototypes.streamlit_water_quality`
without converting its complete transitive dependencies would duplicate
scientific module and dataclass identities, which is not acceptable without
independent original code/SCIP mathematical verification.

## Review-only implementation

`prototypes/water_import_guard.py` is a narrow installed *non-scientific*
guard shipped by the existing root `prototypes` Python package. It observes
only names already cached in `sys.modules`, without importing/scanning
the scientific models or mutating state. It refuses unexpected cached
`model`, `mvp_audit`, `wireless_topology`,
`runtime_attestation`, `scip_lp_structure`, `evidence`,
`qubo`, `sa_benchmark`, `formulation_audit`.
Both `module.__file__` and `module.__spec__.origin` must resolve to
the exact canonical `prototypes/streamlit_water_quality/<name>.py`
source file. Entries lacking a real origin, including a cached `None`
slot, are rejected. No fallback import, silent alias replacement, or
process-global import-path restoration is allowed.

The guard is invoked in `pages/water.py` and
`prototypes/unified_dashboard/research.py` **before** either can
change `sys.path`. In particular, the water wrapper still preserves its
original `runpy.run_path` behavior and thread-local Streamlit context.
Original `prototypes/streamlit_water_quality/*.py` source bytes,
standalone water entrypoint, exact model/graph/SCIP compiler and research
numerical semantics are unchanged.

A fresh `python -I` subprocess from an unrelated CWD injects foreign
module files and cache objects for all nine names. It checks real
`__file__`, forged file paths paired with foreign import-spec origins,
unidentified and negative cache entries are all rejected **without any
`sys.path` mutation**; an honestly loaded canonical model is accepted.
A second subprocess executes the actual unified water and research
routing files with poisoned cache entries, proving rejection happens
before the previous route path insertion or original research/SCIP code.
Existing sequential AppTests plus two real overlapping Chromium
loopback-browser sessions still exercise unchanged normal navigation.

## What is NOT fixed

This is a preloaded-bare-module **collision detector**, not a completed
namespace refactor. Code with the ability to mutate `sys.modules`
after preflight, spoof both `__file__` and `__spec__.origin`, replace
module attributes after loading, alter the qualified `prototypes`
package, or race between two ScriptRunner threads can still bypass or
subvert this check. It is **not** a hostile-user sandbox, authentication
primitive, serialized solve/OS quota, native dependency lock or physical
lake security proof. The process-global `sys.path` and `runpy`
water/research debt remains **open**.

The proper follow-up requires choosing a qualified transitive namespace
migration with explicit standalone original-science compatibility tests,
or a distinct worker-process runtime, then adding hostile cross-session
collision and real bounded concurrent SCIP isolation tests. Do not
claim those future outcomes from this stage.

## Scientific and release checks to retain

Four mandatory exact-source-HEAD workflows: Python 3.12 installed/native
observational runtime + origin guard tests; unified routed UI; full
SCIP/Streamlit pilot; separately pinned cold original science N20 notebook/
SCIP/5,417-feature GeoJSON/S4/global graph vs UX. Also require the genuine
local Chromium two-browser job. Match source HEAD separately from GitHub
synthetic PR merge checkout; run independent source science from original
DRAFT #96 as a distinct pinned checkout rather than merging it.

Historical original **local one-hop** N20/K5 has 1,077 of 15,504
combinations feasible, while separate **all-15-fixed exploratory global**
graph model has 860 of 15,504 feasible; global graph set SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
same best indices `[0,1,3,6,7]`. Different observed exact binary64
source coefficient SHA identities `2b238848...` and `8536a3db...`
must never be treated as the same strict cache key.
The manuscript AHP/D2 WorldPop population-vs-historical-road input
parity, field RF/backhaul/DO/current validation, and quantum advantage
remain unverified; OpenJij's classical SA is not quantum hardware.

No original author notebook, 5,417-feature GeoJSON, S4, manuscript, water
solver/compiler or independent pinned scientific DRAFT #96 is edited.
No public Cloud staging, preview branch push, merge, signed remote result,
live browser ZIP-download claim or production deployment authorized.
