# Scientific notebook → dashboard feature parity (2026-10-26)

**Scope/ref:** Original notebook Git blob `a554f4f37957e924c0ed417e53af2dab04e45ffa`, `preview` baseline `d7af3a81ed05753dc8d629a216ce87170e0cb322`. This is a source-inventory and planning document, **not** a claim of successful new experiment execution, manuscript parity, or approval to release.

**Vocabulary:** I = implemented in existing dashboard/research path; P = partially implemented or fundamentally different; N = notebook-only; H = historical placeholder; D = source defect/risk to investigate. Source cell numbers are the **zero-based JSON cell indexes**; labels are the historical notebook's cell titles. Several are duplicate versions.

| JSON cell | Notebook role | Present dashboard / code | Status | Milestone |
| --- | --- | --- | --- | --- |
| 0 | CELL 0 local/Colab environment and package setup | `requirements.txt`, separate CI / packaging | P: no notebook-compatible execution environment | M0/M4 |
| 1 | CELL 0.5 deployments, reduced MIQP, QUBO matrix plots | `prototypes/streamlit_water_quality/app.py`, `formulation_audit.py`, `prototypes/unified_dashboard/research.py` | P: N20 map/inspector, not multi-tier publication plots | M3 |
| 2 | CELL 1 flags and SA/SQA/benchmark configurations | `prototypes/streamlit_water_quality/sa_benchmark.py`, `sa_paired_replication.py` | P/H: controlled N20 SA; historical SQA configuration unused | M0/M2/M5 |
| 3 | CELL 2 GeoJSON ingest, weights and master model | `prototypes/streamlit_water_quality/model.py`, `problems/water_quality/notebook_reference_model.py`, source test | P: frozen N20 source-derived model; no paper-data parity | M0/M1 |
| 4 | first CELL 3 FPS nested tiers N20…1000 | `model.select_sites`; new offline nested cohort builder (draft) | P/D: older duplicate hardcodes 1000; not the final active tier config | M1 |
| 5 | second CELL 3 FPS nested tiers N20…2000 | `model.select_sites`; `problems/water_quality/nested_resolution.py` (draft) | P: N20/50/100 offline candidates; larger tiers not integrated | M1/M4 |
| 6 | CELL 4 per-tier pairwise/SCIP/QUBO data and adjacency | `model.make_instance`, `qubo.py`, `formulation_audit.py` | P: direct N20 formulation / different slack QUBO compiler | M1/M2 |
| 7 | first CELL 5 multi-tier SCIP solving + artifact exports | `model.solve_scip`, independent N20 source audits | P: N20 only interactive; distinct SCIP linearization | M1/M4 |
| 8 | second CELL 5 multi-tier SCIP solving + artifact exports | same | P/D: duplicate solver cell; use later revision for audit | M1/M4 |
| 9 | first CELL 5b IEEE-style SCIP deployment grid | N20 map in water Streamlit page | P/D: duplicated plot cell; no six-tier grid | M3 |
| 10 | second CELL 5b IEEE-style SCIP deployment grid | same | P: notebook-only composite renderer | M3 |
| 11 | CELL 5c MIQP heatmap grid | `formulation_audit.py` numeric inspector | P: no tier-grid publication heatmaps | M3 |
| 12 | CELL 6 coefficient bound, augmented QUBO & 2D grid config | `qubo.py`, `sa_benchmark.notebook_row_sum_bound`, `safe_penalty` | P: explicit slack QUBO, bounds distinguished; no interactive 2D grid | M2 |
| 13 | first CELL 7 parallel multi-tier penalty grid execution | bounded N20 `research.py` / `sa_benchmark.py` | P/D: no parameter-grid runner; hardcoded sweeps in notebook | M2/M4 |
| 14 | second CELL 7 parallel multi-tier penalty grid execution | same | N: notebook has duplicate worker logic; no production batch workflow | M2/M4 |
| 15 | CELL 8 summary tables and CSV/LaTeX exports | evidence ZIP/CSV in water page and research page | P: no cross-N IEEE table/LaTeX | M3/M6 |
| 16 | CELL 9 figures: feasibility, penalties, contour, scaling, comparisons | N20 research page and attestation | N: multi-tier result-derived figures absent | M3/M6 |
| 17 | CELL 9b greedy reference | water standalone evidence, exact N20 reference modules | P: no multi-tier greedy experiment comparison | M2/M3 |
| 18 | short Pandas display cell | Streamlit data tables | P: display convenience only | M3 |
| 19 | CELL 8b winning-λ QUBO matrix grid | `qubo.py`, `formulation_audit.py` | P/D: notebook reads `b_edges`/`c_edges` absent from some generation outputs; matrix evidence unverified | M2/M3 |
| 20 | CELL 5c greedy deployment map grid | water Streamlit N20 map | N: no multi-tier greedy deployment grid | M3 |
| 21 | first CELL 10 SCIP/greedy/SA final comparison | N20 classical SA vs SCIP evidence | P: no comparable cross-N summary | M3/M6 |
| 22 | duplicate CELL 10 final comparison | same | D: duplicate cell; do not count as independent research | M0/M6 |
| 23 | CELL 10.5 posthoc SA deployment rerun | N20 bounded SA and evidence export | P/D: historical unseeded rerun not equivalent to archived winning trial | M2/M6 |
| 24 | runtime-comparison display with derived SA timing | N20 timed runs and separated numerical attestations | P/D: divides tier time by points × repeats; measured solver time not independently isolated | M3/M4/M6 |

## Scientific gates to preserve

- **Original sources:** do not rewrite the notebook, GeoJSON, manuscript, or independent PR #96. Maintain the existing N20/K5 local one-hop certificate (1,077 feasible of 15,504) distinct from all-15-existing globally connected counterfactual (860/15,504).
- **N ordering:** 20, 50, 100, 200, 500, 1000, 2000 free candidates from nested, deduplicated, fixed-seeded farthest-point selection; existing 15 stations kept separate. First duplicate cell excludes 2000; second corrected cell includes it.
- **Formulation:** distinguish original tier objective, master objective, unpenalized objective, augmented QUBO energy, connectivity/budget penalties, exact solver statuses/gaps/time budgets. The pilot's explicit binary slack QUBO is not certified as JijModeling/OMMX parity.
- **Data semantics:** historical GeoJSON D2 road proximity and notebook weights differ from manuscript WorldPop exposure and AHP weights. The latter do not retroactively transform the former.
- **Randomized results:** record seeds, reads, sweeps, repetition blocks, infeasible trials, coefficient hashes, runtime boundaries and environment. Replaying a seed is not an independent observation.
- **Performance:** large tiers start offline/read-only. Do not equate N2000 solvability, quantum execution, and interactive practicality.
- **Known code risks:** Cell 2/3 cache hashes omit influential config; Cell 7 sweeps override `CONFIG_SA`; SQA is a config placeholder, not QAOA; no verified Optuna branch; multi-tier dense `X @ Q` is a scaling risk.
- **Known manuscript check:** Table VI's N50 stated λb=2.196 and λc=1.167 do not add to the printed sum 2.334. Verify all tabular totals and solver statuses before treating paper values as automated fixtures.

## M0–M6 dependency and sequence

1. **M0:** freeze source/N20, copy-not-clean-original notebook, numerical claim registry, versioned manifest/results schema, exact input hashes and floating-point policy.
2. **M1:** offline 20/50/100 selection + arrays + independent source-index and prefix tests → cross-N selector and read-only comparisons → eventually 200/500/1000/2000 with explicit solver resource gates.
3. **M2:** separate penalty λb/λc grid, global sufficient bound vs single-flip heuristic, repeats/seed blocks, feasibility failures; optional adaptive tuner in separate study.
4. **M3:** real-result-backed deployment comparisons, penalty contours, MIQP/QUBO matrix diagnostics and downloadables; preserve common-master vs tier metrics.
5. **M4:** local batch execution first, sparse ops and bounded workers; timing scopes, canonical artifact manifests, checkpoint/restart only when measured need warrants.
6. **M5:** genuine small-scale QAOA simulator N4/6/8/10 with auxiliary-qubit overhead and finite shot/depth/optimizer budgets; keep SQA and classical OpenJij separate.
7. **M6:** preregistered scientific comparisons, robust statistics, independent verification, licensing, citation, durable artifacts, CI fast/research split.

## Next UI implementation (NOT in first code PR)

Introduce a resolution selector with **N20 certified** vs **N50/100 generated, unvalidated-for-optimality** states; show candidate source IDs, fixed station set, input hash, visualization cost, and explicit solver eligibility. Use offline result bundles rather than SCIP or SA during Streamlit reruns. Compare same K, same formulation and declared common master reference only. Follow with bounded penalty-grid experiments and visualization provenance.
