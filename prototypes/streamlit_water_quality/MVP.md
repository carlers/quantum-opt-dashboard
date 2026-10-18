# Water-quality placement MVP: launch candidate

**Status:** review-only draft, **NOT deployed**. This scoped MVP intentionally pauses the bigger plugin/framework/typed-math feature expansion. It is a small reviewable change based on the already deployed `plugin-water-streamlit-pilot` branch, not on the many research PRs (#14–#47).

## The one user journey we intend to ship

**Configure → Inspect → Run → Review/Download**, for the immutable Laguna de Bay GeoJSON and the original notebook-derived 20-candidate SCIP formulation.

1. Open the Streamlit entry point `prototypes/streamlit_water_quality/app.py`. The app displays its one built-in source, **5,417** original GeoJSON features, **15** explicitly flagged existing stations, **20** reproducibly sampled free candidate choices, plus warnings on the unresolved previous-paper discrepancies.
2. In the sidebar, set **K** (new sensors, default 5) and choose Notebook weights (default, current committed notebook) or Paper weights (**exploratory comparison only**). For MVP, N=20, beta=1, delta=1 and SCIP time limit=30 seconds are deliberately fixed. No arbitrary local uploads, custom formulas, QUBO annealer run or hypothetical shelter-data ingestion.
3. See the **actual original binary quadratic objective** and exact budget equality and local one-hop constraint. Inspect coefficient tables, local site→source-feature mapping, and model/dataset SHA. Preview is compiled from the same in-memory `model.Instance` sent to SCIP. **No solver runs on initial page load.** A downloadable JSON preview contains the actual float64 coefficient hex values.
4. Press **Run SCIP placement**. The existing PySCIPOpt solver solves its exact **binary pair-product MILP** (not native MIQP). An optional read-only `.lp` export hook writes exactly the mathematical program the solver optimized. An **independent** original objective/budget/one-hop check verifies the candidate selected by SCIP. Status distinguishes certified optimality from a feasible incumbent with nonzero gap.
5. View objective, count, status, lake map, source-feature positions/Easting/Northing. Download one ZIP containing `model.json`, `result.json`, `actual_scip_model.lp`, `selected_sites.csv` and `SHA256SUMS.json`. Source is not duplicated in ZIP but its pinned original SHA is there. Changing K or weight source **removes stale results**; an old experiment cannot be shown or downloaded under new settings.

This is a source-specific scientific feasibility MVP, **not a certified previous-paper reproduction**. There are unresolved mismatches between the original paper Table IV AHP weights and the notebook defaults, criterion D2 semantics, and the paper's N20 reported energy `−3.301319` versus current committed notebook-derived model `−3.3012934918564643`. Local one-hop adjacency is not full network-path connectivity. No quantum processor, QAOA or annealer runs here; only SCIP.

## Research baseline acceptance

Dataset SHA-256 must be **`e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`**; code refuses to run if those historical source bytes change. For K=5, 20 free candidates, notebook weights and beta=delta=1, previous independent studies certified optimum ≈**−3.3012934918564643**, selected local positions **[0,1,3,6,7]** (source GeoJSON feature positions **[5253,2394,1557,47,5409]**). This *notebook-derived baseline* is an automated regression test and **not** a paper-parity acceptance criterion.

## Running locally (review branch only)

```bash
python -m pip install -r prototypes/streamlit_water_quality/requirements.txt
python -m pip install pytest
python -m pytest prototypes/streamlit_water_quality/tests -q
streamlit run prototypes/streamlit_water_quality/app.py
```

The scoped `.github/workflows/streamlit-pilot.yml` verifies both mathematical invariants and actual headless Streamlit button/parameter/download interactions. It is safe to run on this draft PR: there is no push/merge action, no external database, no credential provisioning, no expensive OpenJij sweep and no auto deployment. CI tests are scientific developer tests, **not** a mobile/browser UX acceptance substitute.

## Explicit deferred backlog (keep it out of MVP PR)

- Generalized mathematical term builder and other app domains (#39–#47) stay as unmerged separately reviewed experiments. They do **not** need to be merged to deliver the first lake Streamlit experience.
- Full per-user arbitrary CSV/GeoJSON upload, column mappings, real shelter demand and flood data, permissions/rights, arbitrary MIQP/DSL, constrained-QUBO penalty design, OpenJij SA benchmarking, QPU integration, persistent experiment history, multi-run comparison, queues, worker/service architecture, Vercel, Appwrite, and advanced graph/routing math.
- Notebook/paper provenance discrepancies remain open #16. Numerical float64/SA cross-run sensitivity remains open #24; do not overclaim full bitwise reproducibility.
- Per-user saved sessions, mobile design polish, user-authenticated datasets, rate limiting and monitoring are deferred until needed.

## Owner-controlled launch gates

- [ ] Scoped PR CI green at exact release candidate SHA including N20 opt/reference, independent original objective/constraint audit, true SCIP LP, Streamlit initial render and stale-result tests.
- [ ] Reviewer reads the concise MVP controls and confirms only the intended notebook-derived problem is modeled (no paper parity claimed).
- [ ] Manual mobile/desktop view and solution/export trial against a **staging URL**, including whether the Community Cloud runtime can reliably perform N20/K5 within 30 seconds.
- [ ] User explicitly approves which target branch to update, and when/where to deploy. **The existing live Community Cloud deployment must remain unchanged until that approval.**
- [ ] Record exact release commit, app URL, test date, original source SHA, and any unresolved numerical issues in a checkpoint.

Reference roadmap: [MVP issue #48](https://github.com/carlers/quantum-opt-dashboard/issues/48), existing deployed pilot PR #13, scientific #15/#17 and inspector #29. Do not merge this PR or alter deployed Streamlit branch automatically.
