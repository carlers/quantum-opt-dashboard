# Notebook cell → plugin module map

| Cell | Plugin module |
|---|---|
| 0    | dropped |
| 0.5  | artifacts/renderers.py |
| 1    | config.py |
| 2    | stages/ingest.py |
| 3    | stages/scale.py (second variant) |
| 4    | stages/build.py |
| 5    | stages/solve.py (SCIP) |
| 5b   | artifacts/renderers.py |
| 5c   | artifacts/renderers.py |
| 6    | stages/grid.py (bound) |
| 7    | stages/grid.py (parallel) |
| 8    | stages/analyze.py |
| 8b   | artifacts/renderers.py (see bug: b_edges/c_edges) |
| 9    | stages/analyze.py + artifacts/renderers.py |
| 9b   | solvers/greedy.py |
| 10   | stages/analyze.py |
| 10.5 | stages/solve.py (SA re-run) + artifacts |
| last | artifacts/renderers.py |

## Bugs to fix during port
1. Config hash excludes WEIGHTS, FACTOR_NAMES, HULL_RATIO, GRID_CONFIG, CONFIG_SA.
   Framework solves this: StageSpec.config_deps declares every read.
2. Cell 8b references b_edges/c_edges never produced. Fix: compute QUBO
   via instance.to_qubo(penalty_weights), save full dict per winning λ.
3. FORCE_RETUNE_GRID outside config hash. Gone: cache is content-addressed.
4. CONFIG_SA decorative; Cell 7 hardcodes num_sweeps. Read from SAConfig.
5. Duplicated cells: keep canonical (second) variant.
6. CONFIG_SQA unused: solvers/sqa.py placeholder.
7. USE_WANDB: True but no wandb.init. Wire in plugin's default_tracker.
8. Optuna not present. Framework tracker supports it; plugin opts in.
9. Dense X @ Q at N=2000 dominates runtime. Use scipy.sparse.
