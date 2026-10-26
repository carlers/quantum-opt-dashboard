# Issue #108 — Stage 2, first qualified-import migration (review-only)

Based **only** on verified DRAFT #109 source HEAD
`ca2f8045d266a45b56c5a818cd48b54854c6b48d`.
This is an independent **child DRAFT**, not merged or deployed.

## Changed import edges (no solver/science changes)

| Caller | Before (unsafe global module name) | After (stable package name) |
| --- | --- | --- |
| `prototypes/streamlit_configurable/app.py` | `from guided_math_ui import show_guided_controls` | `from prototypes.streamlit_configurable.guided_math_ui import show_guided_controls` |
| `prototypes/streamlit_configurable/guided_math_ui.py` | `from guided_math import apply_guided_edit, parse_components` | `from prototypes.streamlit_configurable.guided_math import apply_guided_edit, parse_components` |

Introduced two empty `__init__.py` package anchors under `prototypes/`
and `prototypes/streamlit_configurable/`, plus a narrowly scoped root
`pyproject.toml` specifying **only those two packages** with setuptools.
The root `requirements.txt` installs the local package via `-e .`.
This is an installable editable source package, **not a dependency lockfile**.
An existing runner still installs the same declared Streamlit, SCIP and scientific
dependencies from the existing nested requirements; do not silently infer
portable numerical SHA equality from packaging.

Launch from the repository root after
`python -m pip install -r requirements.txt`:

```sh
streamlit run prototypes/unified_dashboard/app.py
streamlit run prototypes/streamlit_configurable/app.py
```

The second path is a supported **standalone Streamlit entrypoint**; do
not assume merely changing current working directory makes imports available.
`test_qualified_editor_imports.py` starts Python with `-I` from an arbitrary
non-repository working directory, imports the installed namespace, then
injects a malicious `guided_math` module into both `sys.modules` and
a higher-priority directory. The qualified module stays in its expected
on-disk file with original callable identity. This is an **isolated import
collision test**, NOT simultaneous browser/ScriptRunner isolation or a
security boundary against malicious code able to inject into the **qualified**
namespace itself.

## Explicitly not yet migrated

- `pages/water.py` and `pages/custom.py` still prepend paths globally
  and use `runpy.run_path`; editor app still prepends framework, water,
  and evacuation paths for *other* unqualified imports.
- Water `model`, `wireless_topology`, `mvp_audit`,
  `runtime_attestation`, `qubo`, `sa_benchmark`, and original
  research page import graph still use bare names. Original
  `prototypes/streamlit_water_quality/model.py`, `mvp_audit.py`,
  `wireless_topology.py`, `export_global_reference.py` are intentionally
  **byte-for-byte unchanged** for the separately pinned original scientific
  source-vs-UX comparison; importing those files with a new name can
  duplicate classes and break canonical original compiler identity if
  done without a complete approved cross-module migration.
- Synthetic evacuation `bundle_runner` and `synthetic_reference`
  remain unqualified; one leaf migration does not certify them.
- Two genuinely overlapping external browser sessions, malicious
  qualified-name collisions, standalone CPU/memory quotas and Cloud
  preview download clicks remain unverified. No snapshot-based `sys.path`
  restoration or long global solver lock was added.

## Independent scientific and release acceptance

Require at the **actual new PR source HEAD**:
1. Python 3.12 clean install and `pip check`, `-I` qualified/editor
   negative controls, sequential module-origin tests, and exact freeze
   recording. Record GitHub synthetic merge checkout SHA separately.
2. Full unified routed pages and editor/domain tests; original SCIP/Streamlit
   pilot; pinned independent cold original science/UX check; no
   broad import compatibility relaxation.
3. Original historical one-hop local N20/K5 mathematical feasible 1,077
   of 15,504 and separate modeled all-15-fixed global 860 of 15,504,
   graph feasible-membership SHA
   `3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
   optimum indices `[0,1,3,6,7]`, and genuinely generated
   SCIP LP/graph/ZIP proof. Observed original exact coefficient SHA
   `2b238848...` and `8536a3db...` remain distinct identities.
4. Original notebook, source GeoJSON, S4 factor inputs, manuscript,
   scientific compiler and independent DRAFT #96 tree untouched.
   AHP/D2 WorldPop manuscript parity and actual lake RF/backhaul/DO/current
   are **unverified**; OpenJij SA is classical, not quantum advantage.

No update to `main`, `preview`, production or public Streamlit Cloud;
no merging this or ancestor drafts. Future stages must complete the
water/synthetic DAG and actual session concurrency tests in independent
review-only drafts.
