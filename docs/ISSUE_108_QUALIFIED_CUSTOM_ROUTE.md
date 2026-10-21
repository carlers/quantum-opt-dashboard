# Issue #108 — Stage 7, installed configurable Streamlit route (review-only)

**Parent:** separately verified/unmerged DRAFT #114 at source HEAD
`8d2c3425aead143fda05cfaa77dc8ec8b956ec36`. This draft
is strictly stacked on the parent; original scientific PR #96 remains a
separately pinned source-science checkout, never merged.

## What changed

The unified `prototypes/unified_dashboard/pages/custom.py` previously
prepended `prototypes/streamlit_configurable` to *process-global*
`sys.path` and re-executed the standalone app script via
`runpy.run_path(..., run_name="__main__")`. Stage 2 through Stage 6
installed the real configurable editor and its qopt/problem dependencies in
stable qualified namespaces. This wrapper can now use:

```python
from prototypes.streamlit_configurable.app import main as render_configurable_workbench
```

and call that original, **unchanged** `main()` once per Streamlit page run.
The existing `threading.current_thread()._qopt_unified_page` marker is
still set/restored with a `try/finally` around rendering; no process-global
environment variable, search path, cached module alias, lock or
`sys.path` restoration is introduced. The standalone app's existing
`if __name__ == "__main__": main()` remains available, and
`st.set_page_config` continues to apply only when it runs outside unified
thread context.

## Verification

A new AST regression fails if `pages/custom.py` again imports `sys`
or `runpy`, mutates a global import path or substitutes bare-name app
imports. Actual routed `AppTest` runs **water → custom → water →
custom**, checks real headings, no Streamlit exceptions, no unintended
SCIP result and exact cached `prototypes.streamlit_configurable.app`
file origin. Existing source provenance AppTest also asserts the app
module itself. The AST import hazard inventory now expects this custom
wrapper to have **no** search-path or dynamic-`runpy` hazard while still
reporting unchanged legacy **water** and **research** paths.

Python 3.12 installed-runtime provenance CI, full unified scientific
dashboard tests, standalone configurable and full pilot SCIP regressions,
two real overlapping **local** Chromium browser contexts, and separately
pinned original N20 notebook/SCIP/GeoJSON/S4/full-global network-vs-UX
science workflow must all pass on the **new proposed exact PR HEAD**.
CI synthetic test-merge SHA must not be confused with source HEAD.

## Explicitly not certified

The water page wrapper `pages/water.py` still prepends the water prototype
folder and uses `runpy`. The research page still uses process-global
water import paths, with bare `model`, `qubo`, `mvp_audit`,
`sa_benchmark`, `formulation_audit`; pinned water compiler source files
have not been renamed or altered. Real hostile same-name *qualified*
module injection, two concurrent SCIP solve resource budgets, browser ZIP
download on permanent preview, signed external execution, portable native
binary64 identity and production isolation remain unverified.

Original author notebook, 5,417-feature source GeoJSON, S4 input factors,
original UX model/SCIP/graph compiler and author manuscript are untouched.
Historical local one-hop N20/K5 1,077/15,504 and separately exploratory
15-existing-fixed globally connected 860/15,504 remain distinct scenarios,
global feasible-set SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
both optimizer indices [0,1,3,6,7]. Original independently observed
strict objective-coefficient SHA `2b238848...` and `8536a3db...`
are different exact model identities. No paper AHP D2 road-vs-WorldPop
input parity, empirical field lake RF/backhaul/DO/current validation
or quantum processor/advantage claim; OpenJij SASampler is classical.

No merge of this or ancestor drafts, no `main` / `preview` changes,
no public Cloud staging/deployment, no original scientific source edits.
