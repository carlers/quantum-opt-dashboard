# Issue #108 — Stage 9: stable research-page module identity (review-only)

**Parent:** unmerged, five-check-green DRAFT #116 HEAD
`1c5f7fe137ae5ba1a18e435e0367e563461da4c0`.
Independent original source-science DRAFT #96 remains a separate pinned
checkout, not a merged dependency. This change is a separately reviewable
child DRAFT and does not change main, preview, deployment or scientific inputs.

## Transition boundary

Previously the sidebar wrapper
`prototypes/unified_dashboard/pages/research.py` executed
`unified_dashboard/research.py` with
`runpy.run_path(..., run_name="__main__")` every time the user visited
the QUBO research page. This had no persistent qualified module identity.
The UI source is now installed as the explicit package
`prototypes.unified_dashboard` (new empty `__init__.py` anchor; the
already-root-installed editable setuptools distribution lists this name).

All existing research-page UI statements beginning at the initial
`st.title("QUBO and classical annealing")` are moved as written beneath
`render_research_page() -> None`, with their order and numeric operations
preserved. a dedicated standalone entrypoint `prototypes/research_standalone.py`
calls the same qualified rendering function under normal standalone
`st.set_page_config` context:
`streamlit run prototypes/research_standalone.py`. Invoking
`prototypes/unified_dashboard/research.py` directly with Streamlit
uses the filename `research.py` and conflicts with the existing
`pages/research.py` automatic multipage URL slug; this is **not**
advertised as a supported direct entrypoint. The sidebar now
preflights the original bare water imports and then imports and calls
`prototypes.unified_dashboard.research.render_research_page`. The page
renders again on each actual Streamlit ScriptRunner invocation, but the
scientific module and cached page module get one stable qualified identity
rather than a new `runpy` execution scope each visit.

No water `model.py`, `qubo.py`, `sa_benchmark.py`,
`formulation_audit.py`, `mvp_audit.py`, `wireless_topology.py`,
`runtime_attestation.py`, detached verification or SCIP compiler bytes
have been changed. The direct module import can affect Streamlit's Python
function/cache identity, hence both actual routed and direct standalone
Streamlit AppTests must pass: default QUBO penalty, displayed model metrics,
manual-only classical annealing, water→research→custom→research, no foreign
SCIP result, origin of the loaded research module and prior original N20
mathematical/LP/science identity checks.

## Still unsafe, intentionally not relabeled as fixed

`prototypes.unified_dashboard.research` still invokes the Stage 8
bare-name import preflight, prepends the original water prototype folder
to **process-global** `sys.path` on initial import, and loads bare
`model`, `mvp_audit`, `qubo`, `sa_benchmark`,
`formulation_audit`. The water sidebar wrapper still uses `runpy`
and path insertion; preflight is not an atomic protection against a
malicious concurrent ScriptRunner changing `sys.modules`, spoofing
both origin fields, or taking over a qualified package. This removes
the research *wrapper's* `runpy` edge, **not** cross-session import
isolation or independent scientific-process execution.

A fully source-preserving isolation strategy requires further
review: either a coherent **entire dependency graph** under new
qualified imports with a demonstrable byte-identical source oracle and
standalone launch compatibility, or separate process workers with
observable OS resource boundaries. Do not implement `sys.modules`
aliases, `sys.path` snapshot/reset, or a global lock during a 30-second
SCIP solve as purported safe per-session isolation. No native scientific
dependency lock, physical lake RF/backhaul/DO/current, actual Cloud
preview-download action, cryptographic remote solver attestation, or
quantum hardware/advantage proof is supplied here.

## Evidence required before review

On this **new exact PR source HEAD**, require Python 3.12 clean installed
package and module-origin tests, standalone research AppTest, all unified
navigation and SCIP mathematical tests, full pilot, two truly overlapping
**local** Chromium browser sessions, and the separately pinned original
N20/SCIP/5,417-feature GeoJSON/S4/full-global-graph source-vs-UX science
workflow. Preserve actual source HEAD and GitHub synthetic PR merge SHA as
different identities. GitHub runtime/CI artifact digests are short-lived
observations, not independently downloaded proof or a permanent research
archive.

The independent historical local one-hop N20/K5 source feasible set
contains **1,077 / 15,504**, while the different exploratory all-15-fixed
global connected scenario has **860 / 15,504**, global feasible-set SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
optimal free positions **[0,1,3,6,7]**. Exact float64 original
objective SHA modes `2b238848...` and `8536a3db...` are distinct
and not interchangeable as strict cache keys. Historical D2 is road
proximity whereas the manuscript discusses WorldPop/population, and the
input parity has **not** been reconciled. OpenJij SA is classical.

**No merge, permanent preview staging, source notebook/dataset/model
rewrite, signature, production deploy or new physical-science claim.**
