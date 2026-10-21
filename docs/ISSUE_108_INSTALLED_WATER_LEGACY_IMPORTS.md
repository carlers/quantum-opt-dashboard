# Issue #108 — Stage 10: install unchanged legacy water modules at startup (review-only)

Parent is unmerged, eight-CI-green DRAFT #117 source HEAD
`d0a120c5759bfe7234e5ec39d4f303b9ed659113`. This stage
is a separate review-only child. No merge, protected branch update or Cloud
deployment. Independent original scientific DRAFT #96 remains in its
separate pinned cold source checkout.

## Why startup packaging, rather than silently rewriting the original model

The original water/QUBO model and independent SCIP verifier deliberately use
*unqualified* imports such as `from model import`, `from mvp_audit import`,
`from qubo import` and `from wireless_topology import`. Those files have
historical source SHA and mathematical obligations. Rewriting them piecemeal
would jeopardize their module/class identities and independent source
comparison before the entire graph was reviewed.

A new **metadata-only**
`prototypes/streamlit_water_quality/pyproject.toml` defines an independent,
local editable distribution `quantum-opt-dashboard-legacy-water-imports`.
It declares the nine pre-existing, **unchanged** original modules:
`model`, `mvp_audit`, `wireless_topology`,
`runtime_attestation`, `scip_lp_structure`, `evidence`,
`qubo`, `sa_benchmark`, `formulation_audit`. The root
`requirements.txt` installs it with
`-e prototypes/streamlit_water_quality` alongside the prior root
`-e .` UI/problem/qopt distribution. The first one owns only these bare
module names; the second owns the installed qualified namespaces, and
neither overwrites the other's source files. No new native dependency
versions are asserted or locked.

The Streamlit water wrapper `pages/water.py` retains the original
`runpy.run_path` and ScriptRunner-thread-scoped
`_qopt_unified_page` context **but stops inserting the water folder
into the process-wide `sys.path` on each page run**. The research
module `prototypes.unified_dashboard.research` similarly stops inserting
that directory, while retaining its historical bare scientific imports and
exact rendering/numerical calculations. Imports now resolve from the
environment's installed startup distribution, not from a page-dependent
global mutation. Python's import table `sys.modules` and import resolution
remain process-global; the installer may also arrange a startup-time
editable import hook/path. This is a narrower claim than eliminating all
process-global namespace risks.

## Fail closed when an unimported module points elsewhere

The Stage 8 source-origin preflight already rejected *cached* malicious
`model`/`qubo` entries with wrong real `__file__` and
`__spec__.origin`, without altering them. Its read-only observation now
also checks **unloaded** bare names by consulting
`importlib.util.find_spec` before any actual legacy import, rejecting an
unresolvable or foreign source path. This catches a deterministic foreign
file injected at higher `sys.path` precedence, without executing that
file. The installed originals are validated at exact `__file__` origins
in a fresh `python -I` interpreter launched from outside the repository;
a second isolated process injects such a foreign model and demands
fail-closed non-execution. Existing tests continue checking a legitimate
real loaded `model`, cached `None`, a mismatched module spec, and
unmodified `sys.path` inside the preflight itself.

This is NOT an adversarial sandbox or an atomic
check-then-import transaction. A hostile process capable of changing
`sys.modules`, `sys.path`, import hooks, or source bytes **after**
the check, forging both origin attributes, replacing qualified packages,
or controlling site-packages can still interfere. No global SCIP lock or
unsafe `sys.path` snapshot/reset is added. A genuine per-user or
per-job process isolation boundary, OS quotas and hostile concurrent
ScriptRunner tests remain to be designed separately.

## Scientific source, release and regression evidence

No original notebook, manuscript, 5,417-feature GeoJSON, S4 input factors,
water `*.py` source model, graph/SCIP compiler, detached verifier,
QUBO/SA source, original pinned independent science #96 or any
`qopt.core` implementation is modified. The only new file *inside*
the historical water prototype directory is packaging metadata.
The original standalone water Streamlit file is unchanged; unified
water and standalone execution are covered by full CI.

Before review, require **exact new source-HEAD** Python 3.12 clean root
installation, `pip check`, new cold `-I` source-origin/foreign-import
negative tests, routed water/research AppTests and real source ZIP evidence,
full SCIP pilot, local two-live Chromium browser contexts and separate
pinned cold original source-science notebook/SCIP/GeoJSON/S4/global graph
vs UX CI. Record actual PR source SHA and GitHub's synthetic tested
merge SHA separately. Temporary CI artifact SHA metadata is not a
durable academic archive or independently downloaded byte proof.

Historical original notebook one-hop **local** N20/K5: 1,077/15,504
feasible; distinct all-15-fixed exploratory **globally connected**
model: 860/15,504 feasible, set SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
both best free indices [0,1,3,6,7]. Strict source objective
binary64 modes `2b238848...` and `8536a3db...` are distinct.
Manuscript D2 WorldPop/population-versus-historical-road input
parity, measured lake RF/backhaul/DO/current, signed remote execution
and any quantum advantage remain unverified. OpenJij SA is classical.

Still OPEN for independent review: the water wrapper's `runpy` dynamic
execution; historical bare import cache identity; native dependency
locking; actual hostile qualified-package racing; concurrent SCIP
CPU/memory limits; and a real staged Cloud browser ZIP download.
**No merge, preview/staging push, deployment, signing or original scientific
source modification authorized.**
