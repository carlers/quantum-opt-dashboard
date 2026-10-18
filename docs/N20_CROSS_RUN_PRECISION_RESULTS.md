# N20 cross-run exact coefficient study: observed results and limitations

**Scope:** #24, stacked draft PR #57 atop review-only notebook PR #56. No historical notebook/data edits, retuned penalties, output replacement, OpenJij runs, or paper-parity claims. The original project model and N20/K5 solver selection remain unchanged.

## Study A — preregistered original-model replay, 2026-10-18 UTC

[GitHub Actions run #39165632021](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39165632021), same `science-n20-cross-run-manifests` code SHA `8b4611b36df79f1bb2522482fcd33db0e5297339`, three independently provisioned GitHub-hosted Ubuntu 24.04 jobs, **two fresh Python/Jupyter kernel executions each** (six in total). Fixed direct versions: Python 3.12, NumPy 2.5.4, SciPy 1.18.1, Shapely 2.2.0, PySCIPOpt 6.3.0, Matplotlib 3.11.2, nbclient 0.11.0, nbformat 5.11.1, ipykernel 6.31.0; all achieved SCIP optimal and independent exact N20 reference canaries.

| Runner group | Reported CPU model | Two local cold processes | Original-model SHA-256 |
| --- | --- | --- | --- |
| r1 | AMD EPYC 9V74 80-Core | **Exactly identical** | `82685349f850c7df836c2aa84d502bef5e7b014c29cd5de7659aa178f7b3103f` |
| r2 | AMD EPYC 7763 64-Core | **Exactly identical** | `75ef109a9a5488bf553b9dbfd0ef3b3c2e2bf98a273d3982f6f146e4ac6eedd8` |
| r3 | AMD EPYC 7763 64-Core | **Exactly identical** | `75ef109a9a5488bf553b9dbfd0ef3b3c2e2bf98a273d3982f6f146e4ac6eedd8` |

**Four exact-bit differences, all in free-site original linear coefficients only:**

| N20 local index | Abs. coefficient difference | ULP-distance estimate* |
| --- | ---: | ---: |
| `linear_float64_hex[9]` | `1.1102230246251565e-16` | 4 |
| `linear_float64_hex[10]` | `1.1102230246251565e-16` | 16 |
| `linear_float64_hex[17]` | `2.220446049250313e-16` | 2 |
| `linear_float64_hex[19]` | `1.1102230246251565e-16` | 128 |

*ULP distance as `abs(a-b)/max(ulp(a),ulp(b))` for the respective values, **not** a relative error claim or calibrated research effect size. The apparently large 128-ULP count for the smallest-magnitude coefficient corresponds to an absolute difference of approximately `1.1e-16`.*

**No changes detected** in source hashes, candidate/fixed ordering, projected coordinates, quadratic interactions, factor weights or parameter settings, one-hop adjacency, exact-K budget, selected sites, or SCIP-certified original objective. All six reported objective `−3.3012934918564643` and selected local sites `[0,1,3,6,7]`. The aggregation reported `semantic_pass_with_tolerance=true` under the declared diagnostic criterion `rel_tol=1e-12, abs_tol=1e-10`, exact independently replayed original energies to `1e-7`.

**Artifact evidence**: comparison [artifact #12150661640](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39165632021/artifacts/12150661640), retaining all raw `float.hex()` differences and three restricted runner records. Three individual runner artifacts: #12150646641 (r1), #12150103051 (r2), #12150521374 (r3).

**Caution:** Hardware/CPU family association is **observational and not causal**. GitHub-hosted runners can differ in host configuration or lower-level instruction dispatch despite matching directly pinned Python package versions. The serialized source-derived SHA here cannot be equated to older `instance.json` or explicit historical QUBO hashes.

## Study B — utility-stage diagnostic instrumentation, 2026-10-18 UTC

[Run #39165864942](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39165864942), code SHA `867c68bc5691bf152d3f8c3594442b9d280cbec2`. Additional **read-only serialized fields** were added to the *draft working notebook* model payload (not to the source dataset or computational equations): `utility_numerator_free_float64_hex`, `utility_denominator_free_float64_hex`, `utility_free_float64_hex`, `linear_before_fixed_pairs_float64_hex`. That creates a new hash schema payload; **do not directly compare Study A's SHA with Study B's SHA**.

All six independent processes across three separate jobs again passed real SCIP, exhaustive N20, original-model checksum and semantics checks. All three jobs reported **AMD EPYC 7763 64-Core**, and all produced the **same exact new-input digest** `301afef26e86802852ec3f87412d11405b79e9e9067856e5503daa85253b4af2`; no coefficient/utility-stage fields differed within this observed CPU-family sample.

**Artifact:** [#12150328888](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39165864942/artifacts/12150328888), comparing all six verified source-derived N20 records. Standalone scientific replay [#39165864964](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39165864964) and original water-quality fast CI [#39165861455](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39165861455) both passed on the **same Study B SHA**.

**Interpretation:** Study B supports repeatability for the observed 7763 runs. The utility-numerator-versus-interaction source of the Study A hardware-associated linear-bit drift is **still unresolved**, because Study B did not encounter a contrasting CPU configuration. It would be incorrect to infer that the added fields “fixed” scientific numerical instability. Repeating the instrumented workload on an independently provisioned host is an exploratory follow-up, not the originally preregistered Study A.

## Remaining Issue #24 gates

- Identify whether original weighted utility numerator, missingness denominator, final utility or pair contribution first changes **in a run that actually exhibits contrasting exact-bit input**.
- Compare with legacy precision probe carefully (different model serialization conventions; do not assume equal SHA formats).
- Once exact inputs are frozen, **separately** rerun the original preregistered OpenJij read seeds against an exactly identical QUBO and penalty offset across independent processes. Only this can meaningfully test fixed-input classical-SA replay as distinct from coefficient drift.
- Preserve negative and positive experiments, the 14-day Action retention limit, and software/data rights; no retrospective baseline rounding/normalization.

**Research claim presently supported:** At least two different exact float64 N20 original-model coefficient payloads occurred across hosted runs while solver-certified original objective, selection, and constraints remained the same within the declared tolerances. **Not supported:** a demonstrated CPU cause, an explanation of historical 665-vs-698 SA outcomes, universal cross-host bitwise equality or published-manuscript parity.
