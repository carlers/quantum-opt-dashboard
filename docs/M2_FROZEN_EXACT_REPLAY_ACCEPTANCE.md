# M2 two-execution bitwise replay gate — review only

This branch is stacked on draft **#145** (source-checked descriptive penalty chart), above draft **#144** (frozen-profile independent-penalty 3×3 source runner), above original source science #131. It adds an **engineering replay acceptance gate**, not new research trials, a new optimization method, or a revised scientific claim.

**Original checked evidence:** two successful 2026-10-26 independent CI workflows, [#40314225342](https://github.com/carlers/quantum-opt-dashboard/actions/runs/40314225342) and [#40314233600](https://github.com/carlers/quantum-opt-dashboard/actions/runs/40314233600), share the exact frozen N20 source model SHA-256 `add84856f0f933eecd4a82b615c239430a85e524d7f00d796c4753f7b4ba4101` and entire `samples.csv` SHA-256 `2a446a313224e1dd366059a356c00a8b9d6c6dff85dec8ca97a6099f04111702`. All 72 original and auxiliary bitstrings, original raw and augmented energies, per-read seeds, nine QUBO hashes and original feasible flags match exactly. Their measured sampler wall times and Git commit metadata differ as expected. Feasible smoke counts (budget rows x connectivity columns; each denominator 8): `[[6,2,0],[2,6,4],[0,2,5]]`.

**This automated CI** now runs the entire real, original-source, pinned-float64 N20/K5 3×3 classical OpenJij smoke **twice**, using identical parent seeds and the same declared `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1` limits. The fail-closed comparator checks each run's complete per-file SHA chain, frozen source coefficient bytes, exact numerical profile hash, OpenJij protocol/claim scope, all 9 coefficient hashes, all 72 unique parent/grid/child-seed read identities, all source plus slack sample bytes, and all parent/cell trial values **except measured sampler wall time**. It permits only software `github_sha` and per-trial measured wall time differences; no other experiment configuration drift.

A new adversarial test suite checks mismatched original bits even after recomputing checksums, missing/repeated seed index, wrong source model or source SHA, changed numerical threading, forged quantum/claim flags, and changed protocol despite identical files. The workflow uploads both complete source experiment directories and a JSON comparison receipt.

**What this is not:** the two identical executions are *deterministic replays* of the **same two parent blocks**. They DO NOT double the sample size from 72 to 144, demonstrate cross-platform replay on every hardware/compiler build, establish unbiased independent stochastic blocks, choose optimal penalty values, reproduce historical JijModeling QUBO conversion, or constitute quantum hardware experiments. The chosen frozen numerical coefficients are source-identity/topology-verified against the unchanged historical generator with small allowed binary64 regeneration error, rather than silently modifying its N20 original SCIP workflow.

**Remaining approval-dependent work:** issue **#146** proposes a 32-parent-block × 9-grid × 32-one-read confirmatory study (9,216 source+aux states). That batch must not run until a user approves the research design, compute budget and licensed durable archive. Existing GitHub Actions artifacts have 14-day retention; a downloaded transfer copy is not DOI/persistent preservation.

Run the comparator on complete N20 grid result folders:

```sh
python -m problems.water_quality.bitwise_penalty_replay \
  /tmp/grid-first /tmp/grid-replay \
  --output /tmp/bitwise-checked-replay.json
```

This PR is **draft-only**; never merge to `preview`, `main` or deploy without release approval.
