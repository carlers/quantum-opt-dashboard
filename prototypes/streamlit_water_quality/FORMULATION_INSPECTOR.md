# Mathematical Formulation Inspector — first read-only dashboard milestone

**Scope:** Draft PR for [issue #28](https://github.com/carlers/quantum-opt-dashboard/issues/28), *not yet deployed*. This first inspector is built on top of the **previously independently validated** `model.Instance` and `qubo.Qubo` from the research branch. It is not a custom LaTeX input editor and does not change the deployed app, solver, notebook, manuscript or geospatial source data.

## Why it exists

A researcher should be able to verify that the problem selected in the UI is the one actually solved, and identify differences among the **original mathematical MIQP**, the **actual exact SCIP MILP linearization**, and the separately compiled **research QUBO**.

The sidebar already allows N, K, AHP weight source/custom weights, beta/delta and SCIP runtime limit. **Inspect mathematical formulation** builds the selected model but does **not** invoke a solver. The inspector remains active and recompiles against changed settings. **Run SCIP experiment** uses that same constructed `Instance`, then displays an independent check of the original objective/constraints. A previously returned result is hidden when selected settings/dataset SHA no longer match its own recorded inputs.

### Original MIQP view

- Binary free-site decisions `x_i`; objective `min Σ a_i x_i + Σ_{i<j} q_ij x_i x_j`, where fixed-station pair interactions have *already* been absorbed into `a_i`.
- Equality budget `Σ x_i = K`.
- For every free site `i`: **local one-hop adjacency** `x_i <= f_i + Σ_{j in neighbors(i)} x_j`. This does not guarantee a path from each new station to an existing station.
- Full numerical coefficients (with exact IEEE-754 `float.hex()`), local-to-dataset feature positions, every free-neighbor list and fixed-neighbor flag.

### Actual SCIP MILP view

The deployed `solve_scip` uses **binary pair-product linearization** (rather than directly submitting native quadratic `x_i*x_j` terms). For every original pair, the **actual SCIP variable name** is `p{i}_{j}` (for example `p0_1`), binary, with `p{i}_{j} >= x_i + x_j - 1`, `p{i}_{j} <= x_i`, and `p{i}_{j} <= x_j`. The inspector derives those terms from the same `instance.quadratic` used by SCIP, and preserves the original budget/local adjacency. The human-readable table describes the solver implementation; it is not by itself proof of the exact serialized solver input. After pressing **Run SCIP experiment**, the dashboard also offers the **actual `.lp` problem file**, exported by PySCIPOpt from the very same constructed `Model` immediately before `optimize()` (using `trans=False`). This file lets users examine the real submitted variables, objective coefficients and constraints independently of the view.

### Encoded QUBO view (inspection only)

The inspector calls `qubo.make_qubo` on that same `Instance`, displaying all nonzero upper-triangular QUBO coefficients `Q_ij`, constant offset, bit numbering, per-site binary slack bits/weights, separate squared budget and connectivity penalties, and conservative sufficient global-bound guidance. Both penalties can be customized for **inspection only**; changing them does not change SCIP's job.

The explicit auxiliary-slack QUBO is **not the historical notebook's unverified JijModeling converter**. The current Streamlit button **runs SCIP only**. A sufficient global penalty does not imply a classical SA run will reliably find a feasible state, even under fixed seeds. There is **no live OpenJij execution** or mathematical-language parser in this milestone.

## Full JSON export and integrity

`formulation_audit.py` produces a standalone `schema_version=1` JSON artifact including:
- Source `dataset_sha256`, full original settings, original free/fixed dataset feature positions, utilities, projected coordinates and maximum connection distance.
- Original MIQP/adjacency/budget, SCIP pair-product MILP, expanded binary-slack QUBO and all nonzero coefficients.
- Decimal values **and** exact IEEE-754 binary64 `float.hex()` representations for every numeric coefficient; the QUBO offset and penalty values are separately included.
- `model_fingerprint_sha256` calculated over the canonical UTF-8 JSON payload excluding the fingerprint field itself, preserving exact coefficients and settings. It is a model provenance key, **not** proof that two historical paper experiments used identical inputs.
- A separate downloadable `verify_selected` record for the SCIP-returned solution, independently recomputing linear and quadratic contributions, original budget/one-hop residuals, selected indices, minimized-slack QUBO witness, and the same model fingerprint.

The mathematical equation labels are deliberately symbolic for readability; **the authoritative numeric data are taken from `Instance` / `Qubo`, not reconstructed from the rendered LaTeX**. Source-code revision and arbitrary user-entered expressions are not captured in this first version; durable thesis artifacts require a later pinned release and runtime/environment manifest.

## Headless validation

- Pure numerical exhaustive 3-site tests verify every original assignment against the exported objective, independent adjacency and budget evaluation, independently checked QUBO energies and exact binary pair-product MILP constraints.
- Source GeoJSON N20/K5 experiment checks the dataset SHA, fixed/free positions, 12 free-free interactions, real PySCIPOpt optimum `−3.3012934918564643`, original feasibility, exact mapped local selections `[0,1,3,6,7]`, and minimized QUBO-energy witness.
- Deliberate single-ULP coefficient, altered graph, adjusted penalties/settings cause new model fingerprints.
- Streamlit's `AppTest` verifies preview does not invoke SCIP, one real SCIP run is independently auditable, and changed K hides stale solver results.
- A real SCIP LP-export regression confirms the mathematical inspector's variable names match PySCIPOpt's actual model and that `solve_scip(export_lp_path=...)` writes the solver's original MILP without changing the optimization result.
- Scoped GitHub Actions compiles all Python and executes tests and existing scientific CI evidence jobs without deploying any app.

## Later design choices, not part of this PR

1. Review first inspector UI with real users and decide exact numeric table/diagram needs.
2. Add a structured expression/constraint builder with dimensions, units, validation and incompatible formulation diagnostics. **Do not execute arbitrary Python or raw LaTeX.**
3. Support separate evacuation-center mathematical models once chosen with the thesis adviser and validated against geospatial/network source data.
4. Only after that consider a general problem compiler / editor and direct multi-solver dashboard runs, long-running jobs or execution backends.

**Deployment safety:** This isolated draft is stacked on `science-sa-ulp-causal-replay` PR #27. It is not a merge into `plugin-water-streamlit-pilot` or `main`. The existing Streamlit Community Cloud URL is unaffected until the user explicitly authorizes an integration and deploy.
