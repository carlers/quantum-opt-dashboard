# Water-quality Streamlit feasibility prototype

**Status: pilot, not yet validated against the previous paper.** The custom dashboard is deferred. This small experiment tests whether Streamlit Community Cloud can run real notebook-derived SCIP optimization with a mobile-accessible interface.

## Run locally

From the repository root:

    python -m pip install -r prototypes/streamlit_water_quality/requirements.txt
    streamlit run prototypes/streamlit_water_quality/app.py

For model unit tests without Streamlit or SCIP:

    python -m pip install numpy scipy shapely pytest
    python -m pytest prototypes/streamlit_water_quality/tests -q

## Deploy manually

1. Sign into [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub.
2. Select branch **plugin-water-streamlit-pilot** of **carlers/quantum-opt-dashboard**.
3. Select entry point **prototypes/streamlit_water_quality/app.py**, Python 3.12 if configurable, and deploy.
4. Watch the install logs. Open the new app URL on your phone and press **Run SCIP experiment**, initially at N=20, K=5.
5. Record the status, objective and chosen coordinates, or any deployment/solver error.

The repository's main branch remains unchanged. Do not enable an automatic production deployment without review. Cloud compute may be insufficient for full-scale experiments; this pilot is synchronous and N is deliberately capped at 20 or 50.

## Scientific provenance

Reference materials:
- [Original notebook](../../problems/water_quality/notebooks/experiment9%20grid%20search%20copy.ipynb)
- [Committed GeoJSON](../../problems/water_quality/data/LDB_centroids_clean.geojson)
- [Notebook map](../../docs/NOTEBOOK_MAP.md)
- The previous paper, *QUBO-Based Sensor Placement Framework for Water Quality Monitoring in Laguna de Bay* (uploaded in ChatGPT; not currently committed).

Ported from the notebook:
- Cell 2: eight factor names and code weights, per-site missing-factor renormalization, existing-station identification or notebook's simulated 3-station fallback, coordinates in EPSG:32651, concave hull and D_max.
- Cell 3: approximate 10k-site bbox hex pool, pool filtering, nearest-master deduplication, seeded farthest point sampling (FPS).
- Cell 4: negative utility, free-free quadratic redundancy plus symmetric wake interactions within 2*L_c, fixed-site terms folded into the linear coefficients, exact K budget, and local connectivity.
- Cell 5: SCIP optimization; the pilot uses **PySCIPOpt with an exact binary pair-product MILP linearization of nonnegative quadratic penalties**, instead of the source notebook's JijModeling/OMMX SCIP adapter. Mathematical equivalence is intended but **not yet verified numerically**.

Defaults: L_c = 7500m, L_w = 1000m, beta=delta=1, current eastward, D_max buffer=1.15, K=5.

## Critical open scientific discrepancy

The previous paper reports **different AHP weights** from those hard-coded in the committed notebook. Its reported **15 existing stations** are also not necessarily identical to the dataset flags or the notebook's fallback **3 simulated stations**. Additionally, the published D2 criterion is stakeholder/population exposure, while the notebook reads the road-proximity factor. The app exposes notebook/paper weight sets rather than silently choosing one.

The paper's SCIP energy of approximately **-3.301319 at N=20** is a comparison target, not a passing parity test. Candidate indices, input site order, numeric coefficients and solver statuses must be compared under identical configurations.

## Deliberately out of scope

QUBO penalty grid search, OpenJij SA, live long-running background jobs, persistent resume/fork/cache, general application plugins, N=500–2000, and production hosting. Streamlit Cloud is a feasibility experiment, not a replacement for scientific validation.

## Acceptance checklist

- [ ] Cloud deployment installs runtime dependencies and imports the SCIP solver.
- [ ] N=20 / K=5 runs with independent budget and connectivity checks.
- [ ] Numerical inputs and outputs are matched to the original notebook's generated instance.
- [ ] Any differences from paper results are documented and explained.
- [ ] Decide whether Streamlit alone is sufficient or whether an external worker is needed.

No deployment, merge, or claims of replicated publication findings are authorized by this prototype.
