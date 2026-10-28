# First clean derived notebook: source-authenticated input-weight comparison

**Status:** draft educational/scientific data-inspection tool. It does not solve a QUBO or claim manuscript reproduction.

Derived notebook: [`problems/water_quality/notebooks/derived_historical_weight_audit.ipynb`](../../problems/water_quality/notebooks/derived_historical_weight_audit.ipynb)

## Scope

The historical 25-cell notebook is preserved byte-for-byte; it contains duplicate stages, historical configuration and substantial experiment code. It is **not cleaned or executed** in place. This new eight-cell notebook is a small **derived, output-free**, independently testable entrypoint that:

1. Finds the checked-out research repository and verifies the immutable original notebook+GeoJSON source fingerprints using [source provenance draft PR #159](https://github.com/carlers/quantum-opt-dashboard/pull/159).
2. Shows the **eight historical notebook factor weights** and the **eight distinct paper-weight sensitivity constants** as represented by the draft `problems/water_quality/notebook_reference_model.py`. It avoids changing or normalizing either vector.
3. Uses Python's exact decimal arithmetic to show notebook weight sum `1.0001`, alternate sum `1.000000001`, and factor-by-factor differences. This is an **input discrepancy inspection**, not an output or objective-value comparison.
4. Explicitly identifies D2 as historical **road proximity** and treats manuscript WorldPop/AHP input parity as unverified.

**No NumPy, SCIP, OMMX, OpenJij, stochastic seeds, network, notebook package installation, site selection, data redistribution, model execution, plots, production Streamlit or OCI is needed**. The separate fast CI workflow exercises all four code cells in order under a clean Python interpreter context and checks original source fingerprints. This test demonstrates that the derived notebook runs, not that the original complete 25-cell notebook does.

## Reproduce

From the checkout root containing source integrity PR #159:

```bash
python scripts/verify_research_sources.py
python -m unittest discover -s problems/water_quality/tests -p test_derived_weights_notebook.py -v
```

To open interactively, install Jupyter in your **local** environment; no notebook package is required for CI. Run all cells from a working directory **inside the repository**. Re-run the first source validation cell before interpreting weights. Every code cell has null execution count and empty stored outputs in Git.

## Provenance and source caveats

The historical notebook's Cell 2 uses notebook weights `[.3671,.1224,.2508,.0502,.1278,.0183,.0476,.0159]`. The research `notebook_reference_model.py` stores a different `PAPER_WEIGHTS` vector `[.276095907,.276095907,.179220150,.089610075,.087188181,.043594091,.024097845,.024097845]`. These are **already present in an unmerged scientific draft**; copying them into a derived notebook is not independent manuscript authentication. Source rights and university requirements are not yet verified.

The original historical `d2_road_proximity` data is not a WorldPop population raster or a census-based human-exposure signal. Do not interpret weight changes as paper validity, identical geographic input, improved lake monitoring or quantum advantage.

## Relationship to the existing executable N20 notebook

An **earlier unmerged** [scientific draft PR #56](https://github.com/carlers/quantum-opt-dashboard/pull/56) already contains `problems/water_quality/notebooks/water_quality_n20_reproducible.ipynb`, a distinct executable SCIP/exhaustive N20 reference notebook with an independent verification protocol. Do **not** recreate or overwrite it. The eight-cell notebook in this PR deliberately covers **only** the narrower historical-versus-sensitivity input-weight comparison and can be reviewed before the heavier N20 execution path.

Before using PR #56 as a publication-grade basis, review its original-source rights, frozen manifests, tested solver/environment versions, LP/QUBO lineage, full feasible-set certificate and precision tolerances against the newer science branches. That work is not complete merely because PR #159 or this tiny input notebook passes. Keep all derived notebooks separate from the historical original; use bounded tests and no confidential outputs in Git.

References: [source custody](./ORIGINAL_WATER_SOURCE_CUSTODY.md), [notebook cell parity matrix](../NOTEBOOK_DASHBOARD_PARITY_2026_10_26.md), [academic reproducibility survey](../ACADEMIC_REPRODUCIBILITY_SURVEY.md).
