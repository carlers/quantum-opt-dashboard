# Archived notebook: structural source audit and controlled cleanup plan

**Status:** Audited source inventory for [Phase 3 #5](https://github.com/carlers/quantum-opt-dashboard/issues/5) and reproducibility [#6](https://github.com/carlers/quantum-opt-dashboard/issues/6). This is a **static audit**, not a clean-run proof, publication replication, model modification, or research-result verification. The archived source notebook and GeoJSON have not been modified.

## Source identity and exact scope

| Item | Recorded identity |
| --- | --- |
| Original notebook | `problems/water_quality/notebooks/experiment9 grid search copy.ipynb` |
| Archived Git blob | `a554f4f37957e924c0ed417e53af2dab04e45ffa` |
| Declared raw SHA-256 (from independently validated N20 evidence) | `08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048` |
| Source cells | 25 code cells, 0 markdown cells |
| Execution records | All execution counts are null; no saved output cells |
| Notebook metadata | Jupyter nbformat 4.5; recorded Python 3.12.13 kernel metadata |
| Reference dataset | `problems/water_quality/data/LDB_centroids_clean.geojson` (unchanged) |

**Important:** Null execution counts and absent outputs mean no recorded execution evidence exists in the notebook itself, *not* that the notebook was verified runnable. The pinned source digest must pass actual CI before treating this audit's source guard as independently rerun.

## Repeated sections: what can and cannot be removed mechanically

Indices below are zero-based **original notebook cell positions**, not the notebook's own textual "CELL n" labels.

| Original positions | Title in notebook | Exact source comparison | Consequence |
| --- | --- | --- | --- |
| 4 and 5 | CELL 3 — nested resolution scaling | **Different** at source line 29: second variant adds N=2000 | Both variants must remain pending scientific review |
| 7 and 8 | CELL 5 — SCIP solve | **Different** at source line 324: first branch enters plotting functions; second enters instance-file discovery | Do not infer executable equivalence |
| 9 and 10 | CELL 5b — SCIP deployment plots | **Different** at source line 243: 3×2 versus 2×3 grid | Presentation output changes; retain both pending review |
| 13 and 14 | CELL 7 — penalty grid search | **Source-identical** | Candidate to exclude cell 14 from a separately generated copy only |
| 21 and 22 | CELL 10 — comparison table | **Source-identical** | Candidate to exclude cell 22 from a separately generated copy only |

**Identical source text is not a proof that removing a second execution is numerically equivalent.** Cells may write caches, regenerate random samples, overwrite results or have other effects. We only produce an *optional mechanical candidate*; it has not been executed or approved as an authoritative cleaned notebook. The three divergent pairs are not automatically collapsed.

## Other static reproducibility risks confirmed in source

- **Environment and paths:** CELL 0 and later stages implement hybrid Colab/local path setup, create directories and can mount Drive; the working directory and external Drive state can affect execution.
- **Hidden state and cached objects:** stages load/write pickled intermediate objects. An incomplete configuration hash is separately documented in `docs/NOTEBOOK_MAP.md`; do not reuse caches for validation without demonstrating input and version identity.
- **Factor provenance:** CELL 2 hard-codes eight AHP weights and includes `d2_road_proximity`. The manuscript instead describes D2 as stakeholder/population exposure; the raw expert elicitation and historical published inputs remain unresolved under [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16).
- **Sampling configuration:** CELL 1 defines `CONFIG_SA` but CELL 7 uses `num_sweeps = max(1000, 10 * N)`. Verify the intended experimental protocol before changing the sampler.
- **Stochastic precision:** GitHub #24 documents differences in exact input and sampled outcomes across prior CI runs. A source-only copy cannot eliminate float64/seed environment discrepancies.
- **Authoritative reference:** The separate draft scientific baseline establishes N=20, K=5, 15 explicitly marked existing stations, and SCIP optimum approximately −3.3012934918564643. It does **not** reproduce published paper Table V energy −3.301319 exactly. See [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16) and the draft [N20 validation](https://github.com/carlers/quantum-opt-dashboard/blob/preview/prototypes/streamlit_water_quality/N20_VALIDATION.md).

## Reproduce the structural audit without a solver environment

From repository root, with Python 3.12:

```sh
python scripts/notebook_inventory.py --report /tmp/water-notebook-inventory.json
python -m unittest discover -s scripts/tests -p 'test_notebook_inventory.py' -v
```

To generate a **new, non-authoritative 23-cell copy** excluding *only* second occurrences of exactly identical source cells:

```sh
python scripts/notebook_inventory.py \
  --report /tmp/water-notebook-copy-audit.json \
  --working-copy /tmp/water-notebook-mechanical-copy.ipynb
```

The script refuses source SHA changes, unexpected source structure, overwriting the original, or silently overwriting a derived copy. It **does not execute notebook cells** and requires no third-party libraries. Report properties include source digest, cell/output counts, repeated-section comparisons, and a statement that numerical/execution equivalence is unverified.

## Next scientific cleanup gates (not completed)

1. Establish a read-only original execution protocol: Python/solver dependencies, execution order, caches disabled/quarantined, input provenance, CPU/BLAS environment and resource budget. Do not execute high-N/grid-search cells as a casual CI check.
2. Review divergent cell variants with the original authors; choose canonical intent and document any behavior/plot/runtime differences without silently rewriting the historical source.
3. Produce a *separate* organized notebook or script with parameter/setup/data/model/SCIP/SA/figures separated; retain original equations, objective coefficients and one-hop constraint semantics.
4. Run a bounded, independent N20 cold reconstruction and compare chosen site IDs, 15 fixed sites, exact input arrays, original objective and SCIP-certified status to the reviewed notebook-derived fixture; never label this published-paper parity.
5. Document any cache behavior, optional stochastic tests, meaningful tolerance, environment versions, output manifests, negative results and clean-room execution. Resolve paper #16 and float64 #24 questions separately.

No original file, live app, production, or unmerged scientific branch has been changed by this audit.
