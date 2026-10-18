# N20 fixed-seed float precision audit — issue #24

**Investigation, not model normalization.** This branch is stacked above draft SA replication PR #23 and does **not** modify the model, source dataset, notebook, sampler schedule, penalty parameters, or deployed Streamlit branch.

## Why the probe exists

Initial successful fixed-seed OpenJij runs on different GitHub Actions runners revealed two observed outcomes for the notebook local row-sum penalty:
- Successful CI run `39096889778` (and later `39097333196`): 698/1,024 original-feasible draws, 13 exact optimum hits. Its *exact* SCIP instance SHA-256 is `22c6bdfce2df49c47263341e0a4fa6f1ab8e8dba60cd552a1e9a8b0b7ac60822`.
- Successful runs `39097001668`, `39097023374`, `39097262915`: 665/1,024 feasible, 13 optimum hits. Exact SCIP instance SHA-256 `0718156034e83d46223fa3e4e086bc9997c16f7252e3c348ca8ac70cf19d5532`.
- Every checked run had the same committed GeoJSON/notebook bytes, N20 candidate/local index ordering, 15 existing stations, certified SCIP energy −3.3012934918564643, and *12-decimal numerical input fingerprint*. Both other penalties produced 790/1,024 feasible draws in these runs, with respectively zero and one optimum hit.
- Last digits of row-sum penalty differ (`1.097819667627033` vs `1.0978196676270329`). The one-to-one association between observed exact input digest and observed row-sum feasibility is **correlational, not yet a causal demonstration**.

## Instrumentation and scientific boundaries

`precision_probe.py` recomputes the N20 source instance without changing parameters, and exports:
- `model_source`: actual Python `float.hex()` values for every free/fixed projected coordinate, all utility coefficients, 20 linear coefficients, 12 free-free pair terms, `D_max`, free/fixed indices and adjacency, plus file hashes.
- Exact source-provenance JSON digest and a separately labeled 12-decimal numerical fingerprint; **neither** is a universal proof of semantic equality.
- Exact **upper-triangular QUBO** coefficients and offset, slack metadata and penalty values (`float.hex()`) for all three penalty settings; separate exact SHA-256 digests for each QUBO.
- Narrowly scoped execution environment: OS/Python/compiler ecosystem package versions, CPU model and selected BLAS/OpenMP thread settings. It does **not** serialize all environment variables or secrets.
- Two independent model+QUBO builds within one Python process and a boolean exact-reproducibility assertion; cross-run reproducibility is **not** asserted because it is the unresolved scientific question.

The scoped CI workflow uploads `n20-precision-probe` with `precision_probe.json` and `manifest.json`, retaining files for 14 days. Compare artifacts from two distinct successful GitHub Actions runs to isolate which numerical components or host details drift.

**Do not silently fix by rounding.** If an explicit coefficient-normalization rule is needed, investigate it in a **new and separately labeled sensitivity experiment** with before/after scientific objective and optimum checks. Neither the preregistered benchmark's raw outcomes nor original scientific sources may be retrospectively rewritten.

Tracking: [issue #24](https://github.com/carlers/quantum-opt-dashboard/issues/24), [PR #23](https://github.com/carlers/quantum-opt-dashboard/pull/23) and broader provenance #16.


## First CI precision-probe run — read-only observation

[GitHub Actions run 39097654775](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39097654775) at initial PR head `12aebde4961b24ca035e5d697723b19abe8f0eb3`: **31/31 tests passed**, original SCIP/SA/paired validation green, `n20-precision-probe` artifact successfully uploaded at [artifact 12125560523](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39097654775/artifacts/12125560523). This run belongs to the previously observed **665-feasible / 1,024 row-sum** mode, with source-notebook scenario exact `instance_sha256=0718156034e83d46223fa3e4e086bc9997c16f7252e3c348ca8ac70cf19d5532`.

Exact observations:
- CPU: **AMD EPYC 9V74 80-Core Processor** (runner-reported).
- NumPy **2.5.4**; OpenJij 0.12.2 from pinned install.
- `precision_probe.model_raw_sha256=4742a3f129d18b64f9c2b1bdc20d484a5c99f223e5d415f55ad27898785ea9f2`
- `precision_probe.qubo_raw_sha256.notebook-local-row-sum=2f0f635c5d662b4d6fad3bdc60ba5bd0a0bcf8f3bd055ce499c24b6ac311be5d`
- `row_sum_penalty_float_hex=0x1.190ab5b15d1b3p+0`
- **Two builds in the same process matched exactly**; this does not imply two independent hosted runner executions will match.

The remainder of this file is a diagnostic plan. A second independent CI run must be compared before asserting a relationship between CPU/platform inputs and observed float drift.
