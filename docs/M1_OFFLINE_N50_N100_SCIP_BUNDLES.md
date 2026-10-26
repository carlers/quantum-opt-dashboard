# First offline N50/N100 SCIP result-bundle gate (M1 → M4)

Stack on #131's verified source-cohort branch, **not** on deployed Streamlit. This standalone Python runner performs bounded classical SCIP solves for the **historical local one-hop formulation and K=5** using unmodified `model.solve_scip`. No QUBO, SA, SQA, QAOA, custom weights, or physical deployment is executed.

Command (from Linux repository root with NumPy/SciPy/Shapely/PySCIPOpt installed):

```sh
python -m problems.water_quality.offline_scip_batch --tiers 50 100 --time-limit 12 --wall-timeout 75 --out /tmp/laguna-research
```

It first derives pinned 20/50/100 nested source cohorts and checks the 15 marked fixed stations. For each N50/N100 it independently rebuilds the source model in a fresh Linux child and verifies that its binary64 coefficient record is exactly the expected one. A subprocess watchdog terminates the process group after a bounded wall interval, and a 6 GiB virtual-address limit is requested in the child. The reported SCIP limit is not the same as the external wall limit.

Each source-linked ZIP carries `model.json` (hex-float coefficients, master indices and adjacency), `result.json` (SCIP status/gap, measured construction, solve-call and worker wall scopes; nulls when unmeasured), optionally `emitted_scip_model.lp`, and `SHA256SUMS.json`. The outer `index.json` records runtime versions, checksums and per-tier classifications. The independent verifier recomputes the original objective and one-hop constraints **from serialized model bytes** without calling the existing `evaluate` helper. `optimal` is only a SCIP status claim, not an independent global optimality proof; `feasible_not_proven_optimal` means the binary assignment passed the verifier but SCIP did not certify optimality. `no_incumbent`, `solver_error`, `worker_exit_error`, and `wall_timeout` remain explicit outcomes with no fake solution.

The CI run is a **bounded source-science smoke**, not a statistically independent trial or fair benchmark: N50 and N100 receive the same 12-second SCIP time limit but construction/solve/total wall time are separate. The emitted LP is a solver-generated representation, not the previous paper's JijModeling/OMMX native source. The binary64 coefficients may drift across different numerical environments, so source SHA and exact float hex values remain necessary. GitHub's default short retention is not a durable thesis archive.

**Acceptance gates:** no source changes; independent geometric prefix N20/50/100; exact source hash and fixed stations; bounded complete ZIPs even on solver failures; tamper-rejection tests; no N50/N100 energy chart before review of comparable completed artifacts. Release and merge require explicit separate authorization. Next: independent validation of non-optimal SCIP bounds and common-master objective, then cross-N visualization in a separate review-only PR.
