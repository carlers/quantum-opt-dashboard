# Issue #108 — Stage 12: qualified water Streamlit page without runpy (review-only)

**Parent:** green/unmerged DRAFT #119, source HEAD
`ed07ad08f14a7bd7da4e826292e9b44da3abde28`. This is a new
review-only child DRAFT; independent original source science DRAFT #96
stays unmerged and separately pinned in the cold verification workflow.

## Change boundary

The unified `pages/water.py` wrapper formerly executed the historical
standalone page with `runpy.run_path(..., run_name="__main__")`.
With Stage 10's installed unchanged legacy water modules in the runtime,
we can import the original standalone page as a stable qualified module.
A minimal `prototypes.streamlit_water_quality` `__init__.py` and an
explicit root setuptools package anchor make that module resolvable.
The wrapper now preserves the original ScriptRunner thread-local
`_qopt_unified_page` marker via `try/finally`, checks cached and unloaded
bare-module origins both before and after import, and calls
`prototypes.streamlit_water_quality.app.render_water_page()`.
No process-global `sys.path` or `runpy` mutation occurs there.

**Exact source preservation proof at transformation time:** the full
19,713-character original rendering/calculation source body, consisting
of original `st.title`/`st.caption`/`st.warning` plus the original
dataset construction/sidebar/scientific scenario/SCIP/global graph/
map/download block, is reproduced **exactly** by removing one indentation
level from the new `render_water_page() -> None` body. The scientific
helper imports, `@st.cache_data`/`@st.cache_resource` declarations,
`_placement_deck`, constants and original direct model/SCIP/QUBO code
remain at their previous source locations, unchanged. Only original
page UI expression nesting and two direct-call entrypoints changed.
Standalone `streamlit run prototypes/streamlit_water_quality/app.py`
calls `render_water_page()` when `__name__ == "__main__"` and still
sets the original page config; under the unified ScriptRunner context
the original config is suppressed as intended.

This **does change the byte hash of UI `app.py`**; it does NOT claim
byte-identical *UI file*, nor does it rewrite original pinned scientific
model/graph/SCIP/verifier modules, author notebook, 5,417-feature raw
GeoJSON, S4 factor inputs, manuscript or independent source DRAFT #96.
The independent actual cold-original-source-versus-current-UX workflow
must pass again at this new source HEAD.

## Fresh acceptance controls

Actual installed Python 3.12 `pip check` and package provenance;
new AST rejection of water wrapper `runpy`/`sys.path`; tests of
normal unsolved standalone water pilot and route transitions
`custom → water → research → water`, stable
`prototypes.streamlit_water_quality.app` file origin, repeated
rendering, no spontaneous SCIP/SA sampling, and the original manual-only
SCIP evidence generation. Existing negative poisoned module controls
still reject forged `model` before page scientific import.

All required exact source-HEAD gates: source runtime/provenance,
full unified dashboard and full original SCIP/Streamlit pilot,
actual local dual-Chromium browser/WebSocket route navigation,
the Stage 11 Linux two-bounded-SCIP-children *test-only* gate,
and pinned separately checked original N20 notebook/SCIP/GeoJSON/
S4/global graph source science versus UX. Record GitHub's synthetic
test checkout SHA separately from original PR source HEAD.

## Explicit unresolved scientific and isolation risks

- Water `runpy` removal improves stable module identity but **does not**
  isolate historically bare `model`, `mvp_audit`, `qubo`,
  `runtime_attestation`, etc. from global `sys.modules` or hostile
  qualified `prototypes.streamlit_water_quality` injection. Stage 8/10
  origin checks are non-atomic and a malicious concurrent ScriptRunner
  with arbitrary Python access can still race or replace cached modules.
- The actual Streamlit original local SCIP solve is **still in-process**.
  Stage 11's two Linux resource-bounded re-solvers are a separate test,
  NOT integrated into the live app; no per-user admission control,
  cancellation, cgroup resident-memory cap, signed receipt or malicious
  concurrent user quota has been established.
- Historical original one-hop local N20/K5 feasible **1,077/15,504**,
  distinct all-15-fixed exploratory global feasible **860/15,504**,
  global feasible set SHA
  `3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
  selected best positions [0,1,3,6,7]; distinct strict IEEE754 coefficient
  SHA identities `2b238848...` and `8536a3db...` cannot be
  interchanged. Manuscript AHP/D2 WorldPop-versus-road input parity,
  field RF/backhaul/current/dissolved oxygen and any quantum hardware
  advantage remain unverified (OpenJij SA is classical).

No merge, staging/deployment, changes to `main`/`preview`,
original scientific source edits, external signing or real Cloud
ZIP-click assertions are authorized by CI success. Issue #108 remains
open for actual bounded in-app SCIP workers and hostile module isolation.
