# Issue #108 — Stage 4: qualified lazy water adapter imports (review-only)

**Starting source:** separately verified, unmerged DRAFT #111 HEAD
`0d9850048536e18364f1f6a7ee549b6145258820`. This
stage is a separate DRAFT child of #111. Original archival science DRAFT #96
is a pinned, *independent* source tree, never automatically merged here.

## Exact package boundary and changed imports

The existing root editable distribution `quantum-opt-dashboard-ui-imports`
now includes only one extra local package anchor:
`problems.water_quality`. This namespace is intentionally **distinct from**
the separately developed `water_quality` research package under
`problems/water_quality/src/water_quality`. This is not a new data format,
model implementation, independent source verification, or native dependency
lock.

| Caller | Former unqualified dependency | Qualified dependency |
| --- | --- | --- |
| `problems/evacuation_centers/bundle_runner.py` (lazy water branch) | `water_bundle_adapter`, added process-global water path | `problems.water_quality.water_bundle_adapter`, no water-path insertion |
| `problems/water_quality/water_bundle_adapter.py` | `notebook_reference_model` | `problems.water_quality.notebook_reference_model` |
| `prototypes/streamlit_configurable/app.py` | `bundle_runner`, `water_bundle_adapter`, `notebook_reference_model` | `problems.evacuation_centers.bundle_runner`, `problems.water_quality.water_bundle_adapter`, `problems.water_quality.notebook_reference_model` |

Removed three obsolete `sys.path.insert` calls from the configurable
editor (self/water/evacuation) and the *lazy* water path insertion from the
synthetic runner. The editor and runner still add the **framework qopt**
path, and unified page wrappers still mutate process-global paths; no
claim that all import interference is resolved. All standalone file-path
CLI and Streamlit entrypoints depend on the explicit local package install
(`python -m pip install -r requirements.txt` for the integrated app or
`python -m pip install -e .` after installing smaller dedicated CI
dependencies). No fallback to bare-name imports is permitted in the
migrated paths.

## Source preservation

The actual `problems/water_quality/notebook_reference_model.py` scientific
implementation, its original notebook and original 5,417-feature source
GeoJSON are **unchanged**. The new wrapper import name may produce
a *distinct Python module identity* from any pre-existing bare-name
module loaded by legacy scripts; tests may not silently treat independently
loaded classes as identical. Review the tests' **actual callable identity**
and exact source mathematical results; no alias assignment into
`sys.modules` is introduced as a compatibility hack.

## Negative controls and genuine execution

`prototypes/unified_dashboard/tests/test_qualified_water_adapter_imports.py`
runs **fresh Python `-I` subprocesses from outside the repository**:
1. preloads forged bare `bundle_runner`, `water_bundle_adapter`,
   `notebook_reference_model` modules into `sys.modules`, plus malicious
   same-named source files on `sys.path`. Imports the installed namespaced
   runner, executes a real **synthetic EPSG:32651 water bundle**, and verifies
   canonical reference and adapter module origins, numeric-model function
   identity, unchanged poisoned bare cache, no source-directory path
   insertion, and no historical-source claim;
2. executes the same supported synthetic water GeoJSON in a separate
   standalone CLI process, checking the literal `run.json` and checksum
   `manifest.json` exist and identify **synthetic** test data only;
3. checks the migrated import statements remain fully qualified.

These tests are not two real independently initiated overlapping Streamlit
browser sessions or a defense against attacker-controlled
`problems.water_quality` qualified packages. Existing route AppTests
check module origins and solve/result separation sequentially only.

## Required exact-HEAD gates

The new draft must pass: Python 3.12 fresh installed-runtime manifest,
negative controls and `pip check`; all unified routed AppTests and editor/
domain regression; all original full pilot/SCIP/LP/ZIP tests; water data
bundle interchangeability and standalone reference N20 SCIP; configurable
and synthetic dedicated tests; and **separately checked pinned original
notebook/GeoJSON/S4/full 35-node global graph source/UX proof**. A new
CI run MUST be associated with this exact source PR HEAD, not inherited
from an ancestor. Record GitHub's possible PR synthetic merge checkout SHA
separately from the source HEAD.

Historical original local one-hop N20/K5: **1,077/15,504** feasible;
separate all-15-existing-fixed exploratory global modeled graph:
**860/15,504** feasible, global membership SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`;
both best indices **[0,1,3,6,7]**. Original strict IEEE754 source
objective identities `2b238848...` and `8536a3db...` are **different**
and never interchangeable as strict cache keys. These are mathematical
source assertions subject to independent checks, not a manuscript
AHP/D2 population-vs-road reconciliation, measured radio backhaul/shoreline,
field dissolved oxygen/current, actual deployment adequacy or quantum
advantage. OpenJij SA is classical.

No original manuscript/source dataset/notebook edits, independent science
DRAFT #96 ancestry merge, `main`/`preview` push, permanent cloud staging,
live browser ZIP-click claim, OS solver quota claim, signing/KMS service or
production deploy. Owner review remains required before such operations.

**Next review-only scope:** a separately designed qualified water
Streamlit model/research import DAG preserving current pinned source
backend SHA and standalone script behavior, plus **real overlapping
Streamlit sessions** and hostile qualified-name tests.
