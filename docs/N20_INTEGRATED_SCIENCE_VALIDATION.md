# Combined N20 reference validation — integration protocol

**Scope:** Review-only integration candidate that combines **existing** scientific validation without changing the archived lake data, source N20 objective, one-hop constraints or original SCIP/K5 results. It is intentionally based on [precision dispatch draft PR #63](https://github.com/carlers/quantum-opt-dashboard/pull/63), which itself depends on [#61](https://github.com/carlers/quantum-opt-dashboard/pull/61)→[#57](https://github.com/carlers/quantum-opt-dashboard/pull/57)→[#56](https://github.com/carlers/quantum-opt-dashboard/pull/56). The separate feasible/geometry line [#66](https://github.com/carlers/quantum-opt-dashboard/pull/66)→[#67](https://github.com/carlers/quantum-opt-dashboard/pull/67) also depends on #56.

## Why a separate branch?

Both lines modify the **same source notebook cell 22**. Merging by file replacement would remove the original #61 `free_fixed_pair_trace` precision evidence or the #66 `feasible_site_sets_sha256` certificate. Merely seeing each branch pass on its own does **not** prove their combination works.

This independent candidate keeps the entire notebook from #63, preserves its existing precision trace computation in cell 12 and the full `MODEL_INPUT` (source/machine float64 SHA, 300 original free-fixed pair diagnostics, remaining parameters), and adds only the certified feasibility **result** metadata from #66. Cells 13/14 and the independent geometric verifier/test/CI are transferred directly from #67. `model_input_sha256` continues to cover the same scientific source input fields and numerical diagnostic trace as #63; `feasible_combinations` and `feasible_site_sets_sha256` remain **outside** the original model hash as report evidence.

The original #63 runtime microprobes and historical source A/B QUBO/SA paths are **unchanged and never used to alter the lake objective**. The combined notebook still has 23 cells, 12 Markdown + 11 code, no stored output, stable candidate identities, 15 genuinely existing stations, K=5, source 12 quadratic coefficients and original one-hop constraints.

## Pre-result acceptance checks

1. Full cold Jupyter kernel, real SCIP and independently tested all 15,504 choices; the new guard recomputes **1,077** actually feasible subsets and all subset SHA.
2. Recompute free/free and free/fixed links from *archived raw GeoJSON* (not notebook-reported adjacency): strict Shapely/GEOS hull segment coverage, original fixed station spacing, 490 candidate links, 1,077 exact feasible-set membership. No model changes.
3. Preserve **all 300** existing source original free-fixed pair trace records, true model coefficients and exact float64 input hash; original #57 six-kernel cross-host and #61 pair-stage numerical comparators must remain green, retaining observable host/NumPy small-bit drift without changing acceptance thresholds.
4. Check all available synthetic/adversarial tests: original exact manifest integrity, changed unselected graph, corrupted geographic coordinates/thresholds, historical coefficient differences and NumPy fixed-input studies. Prefer existing scope-specific CI over rerunning large historical SA/QUBO trajectories.
5. Publish raw full model and geographic manifests as short-retention CI artifacts. Require owner-approved durable storage separately.

### Interpretation and limitations

- This is **integration verification**, *not* a new successful manuscript reproduction, reviewed numerical policy, shoreline survey, proof of global sensor connectivity or quantum-hardware advantage.
- The two original research lines remain reviewable and unchanged. This PR is **stacked and draft**, not a merge into `main` or production, and does **not** resolve branch ancestry/merge-base conflicts for eventual cherry picking.
- If any combined numerical result differs, **do not silently alter model weights, geometry or rounding**. Preserve run logs, investigate this exact integration candidate, and re-run after an explicit scoped correction.

**Next steps:** execute integrated exact-head CI (one fresh source/SCIP geometry test and six separate source precision executions), compare observed input SHA modes with #61, update master issue #2 and science source issues #5/#6/#24, then request owner/adviser review. Do not merge or deploy without separate explicit authorization.
