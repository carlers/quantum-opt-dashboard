# Issue #129 — Streamlit Cloud import crash: entrypoint-adjacent requirements omitted local packages

**Status:** isolated hotfix DRAFT against `preview` following the owner's first post-merge private-hosted smoke test on 2026-10-26. Do not apply to `main` or the separately deployed original water-quality production branch.

## What was *actually observed* in the hosted screenshot

The Streamlit shell and global research-only disclaimer rendered, but the water page raised `ModuleNotFoundError` while executing `prototypes/unified_dashboard/pages/water.py` line 10:

```python
from prototypes.water_import_guard import require_water_import_origins
```

The screenshot redacted the missing module's exact name; the failing import is definitely this source line. It cannot independently prove whether `prototypes` was missing altogether or only the `prototypes.water_import_guard` submodule. The other affected routes may share the packaging issue; no host logs or second-route traceback were supplied. No SCIP solver executed at this failing import step.

## Root cause verified from current Git + official Streamlit docs

Streamlit Community Cloud first looks for Python environment files **next to the app entrypoint**, then at the repository root. The published `preview` app's entrypoint is `prototypes/unified_dashboard/app.py`. Its adjacent `prototypes/unified_dashboard/requirements.txt` originally contained:

```text
-r ../streamlit_water_quality/requirements.txt
openjij==0.12.2
PyYAML>=6,<7
```

This covers third-party runtime libraries, **but omits** the root project's `prototypes`/qualified `qopt` package and the 9 unchanged historical **bare-name** water source modules. The *root* `requirements.txt` previously contained both `-e .` and `-e prototypes/streamlit_water_quality`. GitHub CI used the root dependency file and passed all 13 gates. **Cloud's adjacent-file priority meant that root's package installs could be skipped**, explaining the hosted import crash despite green GitHub CI. The exact Cloud installation log is not available for independent examination; the above is a consistent, repository-verified mechanism, not a claim to possess private Cloud logs.

Official primary sources:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization

## Scoped corrective patch

Make the **Cloud-selected adjacent requirements** authoritative:

```text
# prototypes/unified_dashboard/requirements.txt
-r ../streamlit_water_quality/requirements.txt
openjij==0.12.2
PyYAML>=6,<7
-e .
-e prototypes/streamlit_water_quality
```

Streamlit Cloud's working directory is **repository root**, so editable paths resolve to the original source packages without `sys.path` hacks. Root `requirements.txt` now only includes this file with `-r prototypes/unified_dashboard/requirements.txt`, avoiding duplicate editable installation. There is **no recursive requirements inclusion**.

Update existing installed-water contract test to assert the actual Cloud-picked file contains exactly the root and historical editable dependencies and that both distributions install. Add an independent Linux Python 3.12 workflow which:
1. Installs **only** `python -m pip install -r prototypes/unified_dashboard/requirements.txt` (never root as installation entrypoint).
2. Checks `pip check`, both distribution versions, an isolated `python -I` from **/tmp**, qualified guard source location, all 9 original bare-module origins and unchanged read-only fail-closed import preflight.
3. Runs actual unified routed Streamlit `AppTest`, imported origin, collision guard and all-page navigation, without automatically starting a solve.

The regular unified/pilot/original-source comparison and real local Chromium/SCIP evidence CI continue running at the **exact hotfix source SHA**, and original unrelated historical scientific files are untouched.

## Limitations and safe host acceptance

An installed package in GitHub Actions Linux Python 3.12 does **not** prove that Cloud used the same manifest, recreated its virtualenv, loaded its compiled SCIP/numerical wheels, or passed an authenticated private hosted browser run. Official Streamlit docs say changing `requirements.txt` triggers dependency reinstallation, but runner logs and owner smoke test remain necessary before closing #129.

After the owner-approved hotfix **only to preview**, an invited reviewer should:
- Confirm Cloud `Manage app` logs show the **adjacent** requirements file and editable installations `quantum-opt-dashboard-ui-imports` and `quantum-opt-dashboard-legacy-water-imports`.
- Reboot/redeploy only that restricted preview app if Cloud did not rebuild after the dependency change, never production.
- Verify four pages render without `ModuleNotFoundError`, without automatic solves, with the same scientific warning.
- Run one authorized original local N20/K5 SCIP result and verify `[0,1,3,6,7]`, LP evidence ZIP and source hash; avoid posting sensitive log/secrets or raw coordinates publicly.
- Recheck logged-out private-access denial. `QOPT_REVIEW_BOUNDED_SCIP` stays **off** by default.

Academic caveats unchanged: notebook-derived local one-hop original N20/K5 1,077/15,504 feasible is different from exploratory all-15-fixed global graph 860/15,504. Original paper D2 WorldPop/AHP and historical road/notebook criterion inputs differ; no field RF/backhaul/current/DO or quantum hardware advantage established (OpenJij SA is classical). Independent original source-science PR #96 remains unmerged and cold-pinned. No original notebook, 5,417-site GeoJSON, S4, source SCIP/graph/QUBO, manuscript, `main` or production change.

**Fall back safely:** if hosted app still fails, capture a *redacted* full Streamlit Cloud traceback and the dependency-install log, then make a second preview-only hotfix. Never bypass scientific origin guards or silently replace original water models to suppress an import exception.
