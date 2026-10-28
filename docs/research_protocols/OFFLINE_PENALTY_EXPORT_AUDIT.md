# Offline verification of historical CELL 7/8 stochastic penalty exports

**Status:** review-only provenance aid. This verifies *internal arithmetic* in original researcher-supplied grid-search JSON/CSV data, not model optimality or manuscript reproduction. The manuscript itself and source research ZIPs must **not** be uploaded to public CI. This documentation deliberately includes **no unpublished manuscript rows**.

## Evidence contract from the original 25-cell notebook

Original notebook JSON cell index **13**, labeled **CELL 7**, writes `grid_search_N{N}_{config_hash}.json`. For every grid point, it computes `penalty_sum = lambda_budget + lambda_conn`, plus feasibility and energy statistics from repeated SA runs.

Original notebook JSON cell index **15**, labeled **CELL 8**, selects the grid point with **minimum penalty sum** whose mean feasibility meets `GRID_CONFIG.FEAS_THRESHOLD` (otherwise the first point with maximum mean feasibility). It writes `grid_search_winners_{config_hash}.json` containing Unicode keys `λ_budget`, `λ_conn`, `Penalty Sum` and `Feasibility (%)`; it also writes `cross_tier_summary_{config_hash}.csv` with `Winner λ_budget`, `Winner λ_conn` and `Winner Penalty Sum`.

These are empirical run exports; a code inspection **does not show that any particular manuscript table was generated from them**.

## Verify one original historical resolution tier *offline*

```sh
python scripts/audit_penalty_export.py \
  --grid "/secure/local/grid_search_N50_<config_hash>.json" \
  --winners "/secure/local/grid_search_winners_<config_hash>.json" \
  --summary "/secure/local/cross_tier_summary_<config_hash>.csv"
```

The summary is optional but strongly recommended. Replace placeholder paths with **original read-only files stored outside public GitHub**. The code uses only the Python standard library; it reads bounded input files, validates all per-point penalty arithmetic, enforces consistency with the actual CELL 8 winner-selection rule, compares optional CSV summary, and outputs SHA-256 digests of the supplied input bytes. It prints **no original lambda or objective measurements** and writes/deletes nothing. It does not contact OCI, run SCIP/SA, retry jobs, or certify a manuscript correction.

Check all relevant N tiers individually. Redact private raw path information from any report before publishing.

## Validity and limitations

- An exported winner can be internally consistent **and still be from the wrong run**, configuration, dataset or manuscript version. Confirm the source commit, config hash, original notebook cache state, `P_min`, repeat count, 1024 reads, sweep count, random seeds, solver versions and file creation times independently.
- Original code uses Python floating point; comparisons use an absolute tolerance of `1e-9` or relative `1e-12` to avoid falsely rejecting sub-ULP summation drift. That tolerance does not excuse material discrepancies.
- No raw manuscript, LLDA record, WorldPop layer, respondents or original experiment source ZIP is checked into this PR.
- **No actual historical grid exports have been provided or verified at PR creation**. Passing synthetic tests proves only the checker itself is functioning.

This belongs to manuscript source reconciliation [issue #16](https://github.com/carlers/quantum-opt-dashboard/issues/16) and scientific reproducibility [issue #6](https://github.com/carlers/quantum-opt-dashboard/issues/6). Data rights and the owner's OCI PAYG **$0/month** limit remain unchanged.

## Another source-code caveat: SCI(P) master vs SA tier energies

The immutable historical notebook's **CELL 5** computes SCIP `energy = tier_energy` from the current tier's `a, Q_edges`, **and separately** constructs `master_energy` by mapping the station selection onto the full master coefficients. **CELL 7** samples SA and scores each sample using `compute_energy_batch(X, a, Q)`, i.e. **tier** coefficients. But the final comparison **CELL 10** uses `scip_res.get("master_energy")` for the SCIP column and `winner["Best Feasible Obj"]` for the SA column; its inline comment treats the SA statistic as already on master coefficients, which CELL 7's source does not establish.

The read-only `scripts/audit_notebook_energy_domains.py` verifies those exact paths against the historical notebook SHA-256; five negative tests and CI require no solver, pickle loading or original run data. It **does not calculate** the numerical difference between master and tier energy or prove which cached values produced a manuscript table. This creates a specific provenance hypothesis, **not a correction**.

To compare solver energies validly, ask for the original exact same-run `scip_result_N{N}_{config_hash}.pkl` and `instance_data_N{N}_{config_hash}.pkl`, `master_data_{config_hash}.pkl` or equivalent **safe JSON exports** of tier and master coefficients/feature indices and selection. Original pickle files are potentially unsafe to deserialize; handle only in a separately trusted and isolated investigator environment. Prefer a plain read-only JSON data export with SHA-256 and numeric `energy` versus `master_energy` fields, and independently decode objectives in both domains before adjusting a published table.

## What a researcher should supply privately to close the evidence gap

1. `grid_search_N50_*.json` from CELL 7, with the original config hash and `grid_points` array; preferably the full N20/N50/N100 set.
2. The **matching** `grid_search_winners_*.json` and `cross_tier_summary_*.csv` generated by CELL 8; preserve unrounded numbers and original filenames.
3. For the solver-energy comparison, independently exported and source-authenticated **both tier and master objective** terms, selected-site indices, `scip_result_N{N}_*.pkl` metadata and original feature-mapping/config hash; **do not email untrusted pickle files for direct execution**. Prefer safe JSON exports.
4. If the files were generated by a different version of the historical notebook, the exact source commit/notebook bytes and `MASTER_QUBO_CONFIG`/hash calculation used for that execution.

Until those are available, the report can establish that manuscript figures are **arithmetically inconsistent**, but must not decide which historical data cell to edit.
