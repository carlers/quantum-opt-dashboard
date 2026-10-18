> **[Open the integrated Streamlit preview](https://quantum-opt-dashboard-55zt76rpzbn2n3dltqfgis.streamlit.app/)** — owner-provided URL, tracking permanent `preview` branch with Python 3.12 and `prototypes/unified_dashboard/app.py`. Production remains the [unchanged water-quality pilot](https://v3wzqpbn8w6nmdgkxh5kum.streamlit.app/). Preview deployment/runtime and downloads still need hands-on validation. [Two-app release guide](../../docs/STREAMLIT_MAIN_PREVIEW.md).

# Unified optimization dashboard · MVP integration candidate

**Status: integrated DRAFT branch, not live, not merged.**

This is the **single Streamlit launch entry point** for the water-quality
experiment, configurable synthetic research models, and a bounded,
classical-only OpenJij/QUBO study.

```sh
python -m pip install -r prototypes/unified_dashboard/requirements.txt
streamlit run prototypes/unified_dashboard/app.py
```

Or for Streamlit Community Cloud, choose
`prototypes/unified_dashboard/app.py` as the main application path and
use the unified requirements file. Configure Python 3.12.

### Navigation

1. **Water-quality placement** — original committed lake GeoJSON, exact
   N20 SCIP experiment, result map, genuine LP/audit export.
2. **Configure another problem** — synthetic JSON/CSV/GeoJSON inputs, typed
   variable/constraint/formulation controls, exact SCIP and optional
   unconstrained-binary QUBO export. This page is intentionally marked
   synthetic; it is not an evacuation operations application.
3. **QUBO and classical SA** — original water binary MIQP, actual
   slack-augmented QUBO and penalties; optional **small** 1–16 independent
   individual OpenJij classical SA samples, seeded and fully auditable.
4. **About the research** — scientific limitations and pointers.

Standalone legacy entry points `prototypes/streamlit_water_quality/app.py`
and `prototypes/streamlit_configurable/app.py` remain usable for regression
tests and migration. The unified shell simply routes into them. There are
no new storage, auth, API or worker services.

### Integration policy

This candidate preserves BOTH pre-existing PR histories and separately
tested scientific files via a multi-parent branch integration commit.
It does not imply that every experiment (especially quantum hardware,
published historical solver conversion, true general MIQP, evacuation
source data, or long-run reproducibility) is academically resolved.
No production branch is updated. When the merged MVP is tested and
reviewed, it can be prepared for an owner-approved merge/deployment.

The expensive preregistered SA/ULP replay remains runnable **manually**
through its explicit GitHub Actions workflow and individual scripts. Only
small fast validation belongs in every MVP PR.
