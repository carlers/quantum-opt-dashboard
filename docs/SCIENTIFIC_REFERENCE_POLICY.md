# Scientific reference policy — bounded water-quality N20 study

**Decision (2026-10-18, owner-requested):** After successful independent review and exact-head replay, use the [curated N20 notebook](../problems/water_quality/notebooks/water_quality_n20_reproducible.ipynb) as the **working, inspectable specification for future notebook-derived Laguna de Bay N=20, K=5 calculations**. This policy is proposed in [draft PR #56](https://github.com/carlers/quantum-opt-dashboard/pull/56) and is **not active on `main` until approved and merged**. It does not make a notebook a universal specification for unrelated domains or historical experiments.

## Reference roles (do not conflate)

| Research object | Role | What it can substantiate |
| --- | --- | --- |
| `problems/water_quality/notebooks/experiment9 grid search copy.ipynb` | **Immutable historical source**; source hash `08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048` | Historical notebook code and its variants/metadata; **not** necessarily a clean, reproducible published experiment |
| `problems/water_quality/data/LDB_centroids_clean.geojson` | **Immutable committed lake input**; SHA-256 `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7` | Pinned 5,417-feature study input; 15 explicitly marked existing stations |
| `problems/water_quality/notebooks/water_quality_n20_reproducible.ipynb` | **Maintained computational reference for the scoped N20/K5 model** after reviewed CI | Cold, source-pinned 20-candidate objective, one-hop constraints, enumeration, SCIP, selection and readable methods |
| `scripts/run_n20_reference_notebook.py` + `.github/workflows/notebook-n20-replay.yml` | **Executable acceptance gate** | The above notebook really executes in a fresh kernel and passes exact-source and independent N20 objective/constraint checks |
| Earlier manuscript | **Historical scientific claim**, not interchangeable with the new notebook | Its own printed method/tables subject to discrepancies investigated in #16 |
| Larger N / OpenJij / evacuation datasets and formulations | **Independent study scopes** | Require their own accepted references and experimental protocols, not extrapolation from N20 |

## Frozen reference and scientific interpretation

- Source-derived model: N=20 free sensor decisions, K=5 **exact** new selections, **15 real marked** existing stations, notebook eight-factor weight vector, beta=delta=1, factor D2=`d2_road_proximity`.
- Original objective: minimize `sum_i a_i*x_i + sum_{i<j} q_ij*x_i*x_j`, with one-hop inequality `x_i <= fixed_neighbor_i + sum_{j in neighbor(i)} x_j`. **Local adjacency is not global path connectivity.**
- Certified N20/K5 independent SCIP/exhaustive selection: local `[0,1,3,6,7]`; GeoJSON master positions `[5253,2394,1557,47,5409]`, original objective approximately `-3.3012934918564643`, checked over `C(20,5)=15504` subsets. These describe the **notebook-derived** case, not a recreation of historical manuscript Table V energy `-3.301319`.
- Cross-process exact float64 model hashes may vary by last-bit precision (issue #24). The notebook now emits all original-model coefficient terms and one-hop flags in hexadecimal along with a source/parameter digest. **Record the exact digest and environment per run, but never silently round coefficients or reject scientifically equivalent values solely because the exact digest differs.** Use independent tolerance-based objective/coefficient tests and investigate unexpected drift.

## Rules for future development

1. Before modifying water-quality N20 mathematics, data transforms, solver compiler, candidate selection, factor weights, scientific UI or report semantics, read the **curated notebook first** and the archived original for historical interpretation. Read #16 and #24 for unresolved source and precision limitations.
2. Treat the output of `python scripts/run_n20_reference_notebook.py` as a mandatory small-instance scientific regression: source SHA, all 20 candidates and 15 fixed stations, original linear/quadratic terms, one-hop adjacency, independent exhaustive check, and SCIP-certified objective/selection. Do not rely on just matching the final score; review exact model-input manifests (with tolerance-aware comparison) and the actual solver model.
3. Changes to mathematical assumptions must be **new explicitly named experimental scenarios** with their own source/parameter manifest and tests. Do not mutate source data, the archived notebook, saved historical results or the frozen baseline to force a match.
4. Document the difference between the **original binary quadratic problem**, the **SCIP MILP linearization**, the **slack-encoded QUBO**, and **classical** OpenJij SA. Do not claim native quantum hardware, universal constrained-QUBO equivalence, or reproduced publication inputs without evidence.
5. For N>20 scaling/grid sweeps and new evacuation-center formulations, define independent bounded benchmarks, data-rights checks, parameter/algorithm protocols and acceptance tests before calling any result validated. Never use a lake one-hop rule as an evacuation reachability model.
6. Keep `main`, permanent preview and production untouched without explicit owner authorization. The PR may use the curated notebook immediately on its feature branch; a separate reviewed merge is needed to make these rules reachable from `main`.

**Next open research gates:** printed paper AHP/D2/SCIP discrepancies [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16), float64 numerical drift [#24](https://github.com/carlers/quantum-opt-dashboard/issues/24), source notebook cell divergences and large-N/SA coverage [#5](https://github.com/carlers/quantum-opt-dashboard/issues/5), broader reproducibility [#6](https://github.com/carlers/quantum-opt-dashboard/issues/6), and study requirements [#3](https://github.com/carlers/quantum-opt-dashboard/issues/3).
