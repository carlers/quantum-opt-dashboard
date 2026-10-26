# M3 read-only, provenance-verified cross-resolution report (first gate)

**Review-only, offline**. This branch follows #141 (independent emitted-LP HiGHS bound verification), which follows #140 (bounded SCIP source experiment bundles), itself following #131 (nested source candidate construction). The interactive resolution selector #139 remains a separate branch. Nothing in this PR executes an optimizer inside a Streamlit rerun.

Input is a two-member ZIP exported by the independent verification workflow: source-execution.zip (per-tier N50 and N100 source/LP/solver ZIPs with index.json) and highs-bound-receipt.json. The new report program **re-verifies the source bundle and repeats the independent HiGHS validation** rather than trusting unverified HTML, screenshots, JSON, or cloud state. It confirms the dataset SHA-256, exact model and LP hashes, SCIP optimality claims, HiGHS primal/dual statuses, independent original objective, and N50-in-N100 nested model coefficients and feasible solution embedding.

Output is original_objective_by_resolution.csv, verified_comparison.json and original_objective_by_resolution.png. The objective figure contains exactly **two observations from one source-pinned CI execution** (N50 and N100, K5, 15 original fixed stations, notebook source weights, local one-hop). It is not a learning curve or empirical timing benchmark. Solver call, source rebuild and worker wall observations are retained as distinct columns for audit, **not plotted as comparable runtime scaling**; some partial observations remain unmeasured. Neither paper-matching WorldPop D2/AHP inputs, lake-wide 5,417-candidate objective, quantum advantage nor physical efficacy are claimed.

From Linux repository root, after generating a pair of source and HiGHS verification artifacts as in the CI workflow:

```sh
python -m problems.water_quality.offline_resolution_report paired-provenance.zip --seconds 20 --output /tmp/laguna-source-verified
```

The test workflow reconstructs full source instances, calls real SCIP with bounded worker budgets, independently checks actual LP export with HiGHS, and then builds the research chart. The GitHub Actions download is short-lived (14-day retention), not a durable thesis archive.

**Next:** review the source-binding and numerical tolerance gates; deposit approved version-pinned evidence in a durable science archive; design a separately reviewed UI pull request that reads exported summaries without executing experiments. Do not merge or deploy without explicit authorization.
