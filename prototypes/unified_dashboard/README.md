> **[Open the integrated Streamlit preview](https://quantum-opt-dashboard-55zt76rpzbn2n3dltqfgis.streamlit.app/)** — owner-provided URL, tracking permanent `preview` branch with Python 3.12 and `prototypes/unified_dashboard/app.py`. Production remains the [unchanged water-quality pilot](https://v3wzqpbn8w6nmdgkxh5kum.streamlit.app/). Preview deployment/runtime and downloads still need hands-on validation. [Two-app release guide](../../docs/STREAMLIT_MAIN_PREVIEW.md).

# Unified optimization dashboard · MVP integration candidate

**Status: integrated DRAFT branch, not live, not merged.**

This is the **single Streamlit launch entry point** for the water-quality
experiment, configurable synthetic research models, and a bounded,
classical-only OpenJij/QUBO study.

```sh
python -m pip install -r requirements.txt
streamlit run prototypes/unified_dashboard/app.py
```

For Streamlit Community Cloud, choose
`prototypes/unified_dashboard/app.py` as the main application path, and
configure Python 3.12. **Community Cloud prioritizes the `requirements.txt`
next to that entrypoint**, so `prototypes/unified_dashboard/requirements.txt`
is the canonical Cloud and local package-install manifest. It installs
both editable source distributions (`-e .` and
`-e prototypes/streamlit_water_quality`) from the repository working
directory, plus Streamlit, SCIP and the other research dependencies.
Root `requirements.txt` includes that same canonical manifest for CI/local
runs. The `cloud-entrypoint-dependencies.yml` workflow installs the exact
entrypoint-adjacent file in a separate job and tests import origins with
`python -I` in a foreign working directory. This is a deployment
*installation* check, not live Cloud proof; see
[`docs/ISSUE_129_CLOUD_REQUIREMENTS_PRECEDENCE.md`](../../docs/ISSUE_129_CLOUD_REQUIREMENTS_PRECEDENCE.md).

### Navigation

1. **Water-quality placement** — original lake GeoJSON, separately bounded N20
   SCIP experiment, exact source evidence and original water map.
2. **Verified source results** — reviewed, archived original-source N50/N100
   SCIP+HiGHS observations. These do **not** rerun solvers on navigation.
3. **Run experiments (local)** — NEW researcher-initiated bounded SCIP N20/50/100
   and classical OpenJij N20 jobs; persistent local status/history, site maps,
   complete sample explorer, original-model-identity-checked run comparisons,
   explicit rerun, cancellation and reproducible ZIP download. An optional
   small **2×2 budget × connectivity QUBO penalty grid** is user-triggered
   and capped at four cells/32 samples total.
4. **Configure another problem** — synthetic JSON/CSV/GeoJSON inputs and
   independently checked mathematical representations; not real field operations.
5. **QUBO and classical SA** — existing small interactive source-QUBO inspector
   and manually launched classical sampler. It is not quantum hardware.
6. **About the research** — source/manuscript/field limitations and references.

**Launching research computations locally (never on public Cloud):**

```sh
git switch feat/user-launched-bounded-2x2-sweeps-20261026
python -m pip install -r requirements.txt
export QOPT_LOCAL_EXPERIMENTS=1
# Optionally choose persistent non-repository local experiment storage:
export QOPT_EXPERIMENT_STORE="$HOME/.local/share/quantum-opt-dashboard/experiments"
streamlit run prototypes/unified_dashboard/app.py --server.address localhost
```

The runner launches **only after the researcher clicks**, using fixed,
separate Python worker entrypoints and a single-operator local filesystem job
store. The flag is OFF by default. The code provides **no authentication, user
quotas, tenant separation, stable multiuser cloud queue, hard process isolation
or reliable storage outside that local machine**. **Never enable this flag on a
publicly accessible Streamlit host.** The owner-hosted preview and production
apps are unchanged. See
[`docs/USER_CONTROLLED_EXPERIMENT_WORKBENCH_MVP.md`](../../docs/USER_CONTROLLED_EXPERIMENT_WORKBENCH_MVP.md)
and [`docs/USER_CONTROLLED_BOUNDED_2X2_SWEEPS.md`](../../docs/USER_CONTROLLED_BOUNDED_2X2_SWEEPS.md)
for source restrictions, receipts and deliberate limits.

Standalone legacy entry points `prototypes/streamlit_water_quality/app.py`
and `prototypes/streamlit_configurable/app.py` remain usable. This stacked
DRAFT adds a local worker and local storage only, **not** a remote service,
password system, managed cloud queue or new deployed backend.

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
