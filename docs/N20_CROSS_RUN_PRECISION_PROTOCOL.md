# N20 model-coefficient replay: controlled cross-run precision protocol

**Study type:** Observational methods and repeatability investigation, [issue #24](https://github.com/carlers/quantum-opt-dashboard/issues/24). Scientific baseline is the [new reviewed-but-unmerged N20 notebook in draft PR #56](https://github.com/carlers/quantum-opt-dashboard/pull/56), not manuscript Table V, historical JijModeling QUBO nor evacuation-center models.

## Research question

For the **same immutable notebook-derived N20/K5 problem** and fixed **direct numerical dependency versions**, do independent fresh Python/Jupyter executions produce:
1. identical source data, candidate IDs, fixed stations and local one-hop constraints;
2. **bitwise-identical original binary objective coefficients**, as recorded by a canonical SHA-256 over the exact `float.hex()` manifest;
3. numerically equivalent independent/exact SCIP and exhaustive-enumeration results when exact last-bit inputs differ?

An identical hash in three jobs is **only evidence for the six observed process replays**; it cannot prove universal bitwise reproducibility, explain older OpenJij variation or establish superiority of an algorithm.

## Fixed experiment: designed before running

- Code: exact PR-head SHA, [source-pinned working notebook](../problems/water_quality/notebooks/water_quality_n20_reproducible.ipynb); pinned archived notebook and 5,417-point GeoJSON. **No coefficient rounding, model reformulation, cache reuse, or edited historical experiment data.**
- N=20, K=5, 15 marked existing stations, notebook weights, beta=delta=1, exactly the same candidate selection/one-hop model as PR #56.
- Runtime: 3 **separate Ubuntu 24.04 GitHub-hosted runner jobs** (matrix replicas r1/r2/r3), each launching **two independent Python interpreter and Jupyter kernel invocations** from a clean file state. All six observations are taken within **one unchanged workflow SHA**.
- Direct versions pinned to the previously green scientific replay: Python 3.12, NumPy 2.5.4, SciPy 1.18.1, Shapely 2.2.0, PySCIPOpt 6.3.0, Matplotlib 3.11.2, nbclient 0.11.0, nbformat 5.11.1, ipykernel 6.31.0. Transitive packages, runner base OS patches, actual Python patch release and CPU model can differ: record metadata and **do not claim a binary-locked machine image**.
- Capture `runtime.json`: operating system, CPU model/count, Python version, selected numerical-thread configuration, run ID, commit ID, replica ID; **never export secrets/all environment variables**.
- Capture `replicate-<replica>-a.json` and `-b.json`: entire verified schema-v2 `N20_CLEAN_RESULT` model input coefficient hex, model digest, data/source digest, selected sites, exact objective, enumeration and solver status.
- **Within each runner**, compare two files and require tolerance-level unchanged original problem, selected sites and package versions.
- **Cross-run**, download all six artifacts in a fresh aggregation job, independently recompute every manifest hash, and compare reference versus every other observation, including every structural field and bitwise coefficient. Publish all observed differences with exact paths and values.

## Acceptance interpretation

- **Strict exact report:** `exact_model_hashes` counts distinct original-model manifests. A value of 1 means *all observed six* matched bitwise, not that floating-point determinism is proven outside this run.
- **Numerical model threshold** (audit criterion, not hidden rounding): `math.isclose(a,b, rel_tol=1e-12, abs_tol=1e-10)` on each stored original-model numeric hex field. These thresholds are initial *diagnostic acceptance gates*, not a universal justified numerical tolerance policy for all research experiments; revisit in #6/#24.
- **Independent result threshold:** original objective within absolute `1e-7`; identical selected site IDs; original constraints and candidate ordering identical; all core environment versions same; each notebook verifier already demands SCIP `optimal`, independent 15,504-subset feasibility/energy and frozen notebook reference.
- **Failure:** changed non-numeric model field, numerics outside the stated threshold, different selected site IDs, mismatched original and enumerated objective, missing/altered SHA, or incomparable pinned package versions. The report must retain failing numerical differences. Do not conceal them by replacing samples with a rounded input.
- **Important limitation:** This first experiment **does not run OpenJij or regenerate a QUBO**; it therefore **cannot** say whether the original row-sum 665/1024 vs 698/1024 feasibility observation was caused by last-bit input drift. The earlier raw SCIP instance SHA used a different serialization payload from this new notebook `model_input_sha256`, so equality of these two different hash formats is not expected.

## Independent next steps after recording the six runs

1. Compare the new N20 model manifest field-by-field with **legacy precision-probe data** from the prior [#24 investigation](https://github.com/carlers/quantum-opt-dashboard/issues/24); do not assert that historically different encodings produce equal hashes.
2. If model input drift is seen, isolate the first differing coordinates/utility/linear/quadratic/adjacency terms and CPU/library metadata. If not, reproduce across further independently provisioned hosts before drawing broader conclusions.
3. Separately freeze a **fixed exact QUBO** and its penalty/offset, replay **the same pre-registered OpenJij seeds** on fresh processes, and compare full returned spin vectors/feasibility. Only then distinguish sampler instability from changed input data.
4. Preserve a durable scholarly archive strategy before 14-day Action artifacts expire; never distribute unlicensed research data.
5. Keep [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16) manuscript AHP/D2/energy provenance open; a clean N20 replay does not reproduce the earlier paper's historical inputs.

**No original notebook, GeoJSON, algorithm, underlying N20 coefficients or previously preregistered sampling protocol is changed by this PR. No merge, production or Streamlit Preview deployment is authorized.**
