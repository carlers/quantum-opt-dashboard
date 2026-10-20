# Issue #108 — import namespace migration, inventory stage (review only)

**Ancestor verified 2026-10-21:** DRAFT #106, branch
`release-runtime-provenance-import-origin-audit`, source HEAD
`1d5a8930d54a59ccdd0cc5ff50e3a39fd86c1b04`. DRAFT #106 is
unmerged, based on DRAFT #104. Original independent scientific DRAFT #96
is a **separate checkout**, not an ancestor to transplant or merge.

## Stage 1 deliverable and its limits

`scripts/import_namespace_inventory.py` parses Python **source AST only**
across `prototypes/`, `problems/`, `framework/python/qopt/`, and `scripts/`.
It emits sorted candidate unqualified-local import edges, `sys.path` mutation
sites, observed `runpy.run_path` execution points and per-affected-file SHA256.
It never executes app or science code or imports third-party GIS/SCIP libraries.
The generated JSON is a **review inventory**, not a complete dynamic import
graph, concurrent isolation test, lockfile, binary64 model identity, or signature.

`test_import_namespace_inventory.py` preserves a reproducible baseline and
an isolated negative control: an already-imported foreign `model` module in
`sys.modules` wins even after a new canonical directory is prepended to
`sys.path`. This reproduces Python's process-global import-cache hazard,
**not** a malicious-user Streamlit test or a fix.

## Observed entrypoints and import transition

| Current entrypoint | Existing mechanism | Proposed reviewed migration |
| --- | --- | --- |
| `prototypes/unified_dashboard/pages/water.py` | Prepends water prototype directory and executes standalone app with `runpy.run_path`; thread-local page flag | Use a stable qualified water app entrypoint and import tree; retain standalone `streamlit run` behavior explicitly |
| `prototypes/unified_dashboard/pages/custom.py` | Prepends configurable directory and executes standalone app; thread-local page flag | Use qualified configurable app namespace; preserve per-run Streamlit page context |
| `prototypes/unified_dashboard/research.py` | Prepends water prototype and imports `model`, `mvp_audit`, `qubo`, `sa_benchmark`, `formulation_audit` without qualification | Qualified water study imports; do not change penalty selection or scientific coefficients |
| `prototypes/streamlit_water_quality/app.py` | Imports `model`, `mvp_audit`, `wireless_topology`, `runtime_attestation` unqualified | Consistent water namespace throughout scientific wrapper and transitive dependencies, including late-import paths |
| `prototypes/streamlit_configurable/app.py` | Prepends four different library, adapter and editor search paths | Explicit qualified configurable/evacuation/water adapters; resolve framework `qopt` as a package at environment installation |
| `problems/evacuation_centers/bundle_runner.py` | Prepends framework path on import, and water adapter path only when `water_quality.reference` is executed | Qualified dependency imports, preserve lazy GIS loading for synthetic-only runs and direct CLI mode |
| `problems/water_quality/water_bundle_adapter.py` | Imports `notebook_reference_model` unqualified | Qualified source adapter; preserve archived notebook/source implementation byte-for-byte |
| `prototypes/streamlit_configurable/guided_math_ui.py` | Imports `guided_math` without qualification | Qualified editor namespace and tests for both page and standalone modes |

The table is a **transition proposal**, not evidence that the changes are
implemented. A subsequent **separate draft** should migrate one coherent
package boundary at a time, documenting exact packages/install commands and
avoiding hidden fallbacks between aliases in `sys.modules`.
No global `sys.path` snapshot reset and no process-wide lock covering
a 30-second SCIP solve. A one-time process-global root insertion is also
**not** equivalent to genuine per-session namespace isolation.

## Required next implementation and validation (not yet completed)

1. Choose package installation and namespaced entrypoint strategy; record a
   precise old import -> qualified import mapping, including CLI and
   `TYPE_CHECKING`/lazy imports. Validate package discoverability under
   Python 3.12 and Streamlit Cloud-style launch from a clean environment.
2. Migrate complete dependent modules, not just page top-level imports; do not
   silently allow bare-name alias fallbacks on module import failure.
3. Add **fail-closed actual module-origin tests** under deliberately injected
   foreign same-name modules; clean-interpreter cold starts; repeated
   water -> custom -> research -> about -> water navigation; lazy synthetic
   reference bundle execution; and two *independent, overlapping* Streamlit
   browser sessions (AppTest sequencing is insufficient for this last item).
4. Independently verify original source N20/K5 1,077/15,504 locally feasible
   and exploratory all-15-fixed global 860/15,504, global membership SHA
   `3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
   selected `[0,1,3,6,7]`, genuine LP/graph/ZIP member checksums,
   session-mode invalidation, and distinct observed strict objective SHAs
   `2b238848...` and `8536a3db...`.
5. Require on the **exact new PR source HEAD** the existing Python 3.12
   observed runtime, unified domain/editor, full 174-test pilot, and separate
   cold pinned original notebook/SCIP/5,417-feature GeoJSON/S4/full global
   graph workflows. Record GitHub synthetic CI merge SHA **separately**
   from PR HEAD. Never call an unrun or skipped path-filtered workflow green.

## Non-negotiable scientific and release boundaries

This stage modifies **no original author notebook**, 5,417-feature source
GeoJSON, S4 GIS inputs, historical scientific model coefficients, or manuscript
DOCX. Original historical D2 is **road proximity**, whereas the manuscript
describes population/WorldPop; expert AHP/input parity is unverified.
No physical field RF/backhaul/DO/current validation; OpenJij is classical
simulated annealing, not proof of quantum advantage. Existing 30-second solver
timeouts are **not OS-enforced per-user CPU/memory quotas**.

No existing draft PR merges, main/preview changes, Streamlit Cloud staging,
live browser-download certification, signer/KMS work, or deployment may be
inferred from a green static audit. Permanent preview and actual download
browser validation require explicit owner authorization first. CI evidence
retention is temporary, not an academic archive.

**Review decision requested:** approve or revise the qualified packaging/
entrypoint strategy before broad import rewrites; the audit-only stage does
not close Issue #108.
