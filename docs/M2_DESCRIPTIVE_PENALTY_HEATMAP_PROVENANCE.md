# M2/M3 descriptive two-penalty feasibility heatmap — source integrity gate

This **offline-only** M2 chart is stacked on draft #144's first real 3×3 independent budget/connectivity classical-SA experiment, which is stacked on original nested-source draft #131. It is **not** a live Streamlit tuner, selection of an optimal penalty, preregistered inferential result, or reproduction of manuscript AHP / WorldPop parameters.

All 9 configurations are constructed from the actual historical N20/K5 source model with 15 flagged fixed stations, notebook source weights, road-based D2, and local one-hop. The two λ axes are the original notebook Cell 6 row-absolute-sum **single-flip heuristic**, an explicitly exploratory midpoint, and the positive **globally sufficient penalty bound** (`P > 2B`) for a feasible constrained problem. The stronger P does not guarantee a finite-sweep annealer finds a feasible site selection.

The plot is only generated after checking the complete original **OpenJij classical SA evidence ZIP**, including its three SHA-256 manifest entries, model/source hash, 9 source-recomputed separate-penalty QUBO coefficient digests, all 18 parent-cell summaries and **every one of 72 original+auxiliary sampled bitstrings**. The offline checker recomputes each energy using both expanded QUBO and unexpanded budget/connectivity squared residuals, verifies exact original-source candidate positions, graph constraints and child seeds, and refuses posthoc fabricated feasibility flags (even if file checksums are recomputed). Any missing cell, invalid bitstring, unknown model, changed energy, dropped infeasible state or duplicated child-seed/index fails closed.

Outputs: `verified_penalty_grid.json`, `verified_feasibility_counts.csv`, `descriptive_feasible_counts.png`. The figure is a **3×3 grid of exactly observed feasible counts, each out of 8** (2 fixed parent blocks × 4 independent one-read samples), with strong language forbidding statistical inference, ranking or causal performance claims. Zero optimum hits here indicate no original-pinned SCIP-optimal raw solutions were observed in the tiny sample. These rows must **not** be cited as a tuned optimal λb/λc for the lake.

```sh
python -m problems.water_quality.independent_penalty_grid --out /tmp/M2-source --parents 270010001,270010002 --reads 4 --sweeps 40
# Package the four source outputs into a ZIP with those names at root.
python -m problems.water_quality.penalty_grid_report original-research-samples.zip --out /tmp/M2-reviewed-figure
```

CI repeats the real 72 one-read OpenJij executions and rechecks every bit before plotting, and contains a post-check adversarial test that changes a feasible/infeasible outcome, rehashes every file, and demands semantic detection. GitHub artifacts currently expire after **14 days**; preserve original source data, environment/version records and full results under an approved durable thesis archive policy.

**Next decisions:** approve a serious preregistration protocol *before any adequately powered sampling*—parent-seed block count, reads/sweeps budget, primary metric (unconditional exact N20 optimum-hit fraction vs unconditional feasibility), paired-block inference, stopping rules, and multiple-comparison safeguards. No quantum/QAOA/SQA, original manuscript conversion parity, field radio validation, runtime scaling, or release is claimed. Keep the user-facing dashboard free of automatic SA execution.
