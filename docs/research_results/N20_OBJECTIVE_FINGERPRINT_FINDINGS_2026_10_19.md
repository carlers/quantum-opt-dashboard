# Original N20 exact objective fingerprint replication — observed result, 2026-10-19

**Research issue:** [#24](https://github.com/carlers/quantum-opt-dashboard/issues/24). **Research-only DRAFT:** [#93](https://github.com/carlers/quantum-opt-dashboard/pull/93). Read the frozen-before-result [study protocol](../research_protocols/N20_OBJECTIVE_FINGERPRINT_REPLICATION_2026_10_19.md) first. No historical archived/source notebook, original 5,417-point GeoJSON, weights, source graph, manuscript, QUBO, application, preview, main or production modifications.

## Verified exact experiment

[GitHub Actions run #39289914383](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39289914383) **SUCCESS** at scientific code/test/workflow commit `b2a53b958b81105ea94b30f10b3e3ee95c66f2b4`: 3 independently provisioned Ubuntu 24.04 x86 runner jobs × 2 completely fresh Python/Jupyter original N20+actual SCIP source replays (**six** distinct source processes). Each runner independently reproduced original raw GeoJSON geometry before uploading both full numerical model records. Aggregation independently rechecked all six source model SHA, original notebooks/SCIP/reference canaries, actual original committed data, factor identities and exact source AHP weights, plus source geometry and original objective `float.hex()` terms.

The aggregation job reported **62 unit tests passed**: 12 new objective forensics, 8 original cross-run comparator, 12 scientific claim-gate, 14 scientific adapter, 16 bounded independent solver-result tests. Numeric source comparison passed its declared diagnostic tolerance; it **did not demand or assert bitwise cross-host identity**.

The two historical exact objective fingerprint SHA-256 values from source-only #89/#92 were **both freshly reproduced** by this independent experiment:

| Runner | Observed hosted CPU model | Two original cold processes | Exact scored-objective SHA-256 | Full original model-input SHA-256 |
| --- | --- | --- | --- | --- |
| r1 | AMD EPYC 7763 64-Core | 2/2 same | `2b238848f43d1763fe093b38360941677e2fa46f1a6c01d05b5b359a62dc5809` | `7517c5b387026825c8afb0bc991efe5167c5b4f6ba32014929dd5747905685dd` |
| r2 | Intel Xeon Platinum 8370C | 2/2 same | `8536a3db295bd4f4e0faa8ad599bfbb3c01a0c4391c04ecc145701f83adc3a56` | `b8cf5457e9c719396c0293407b9697d9bbd56cde6382fe31257122e745e4b4a5` |
| r3 | AMD EPYC 7763 64-Core | 2/2 same | `2b238848f43d1763fe093b38360941677e2fa46f1a6c01d05b5b359a62dc5809` | `7517c5b387026825c8afb0bc991efe5167c5b4f6ba32014929dd5747905685dd` |

All six source runs emitted **-3.3012934918564643**, selected local **[0,1,3,6,7]**, N=20, K=5, original 15 fixed and **1,077** original local feasible K5 subsets; raw GeoJSON independent geometry graph SHA was identical `a013051d2634716be0abd347c49474c650b0ef742c73232089a9cae29e2f10d1`. The core `numpy==2.5.4`, `scipy==1.18.1`, `shapely==2.2.0`, `pyscipopt==6.3.0` and Python 3.12.15 versions matched; host metadata recorded no explicit values of `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` or `OMP_NUM_THREADS` at inspection time. This **does not lock binary wheel internals, all transitive libraries or CPU numeric dispatch**.

## Exactly four changed coefficient leaves — raw hex comparison

Baseline r1/r3 vs r2; **no objective structural criterion/site/weight/coordinate/budget/interaction-pair changes**, and no other changed numeric objective leaves were observed.

| Original candidate local coefficient | r1/r3 `float.hex()` | r2 `float.hex()` | Absolute difference | Approx. ULP separation |
| --- | --- | --- | ---: | ---: |
| `linear_float64_hex[9]` | `-0x1.7ef780983da1ap-3` | `-0x1.7ef780983da1ep-3` | 1.1102230246251565e-16 | 4 |
| `linear_float64_hex[10]` | `-0x1.5504f3b222e88p-5` | `-0x1.5504f3b222e78p-5` | 1.1102230246251565e-16 | 16 |
| `linear_float64_hex[17]` | `0x1.940eba845152ep-1` | `0x1.940eba845152cp-1` | 2.220446049250313e-16 | 2 |
| `linear_float64_hex[19]` | `0x1.2b6a379dd0180p-8` | `0x1.2b6a379dd0200p-8` | 1.1102230246251565e-16 | 128 |

The source-model and objective checksum values refer to **different serialized manifest namespaces**. The ULP estimates use `abs(x-y)/max(ulp(x),ulp(y))`, hence the relatively large 128-ULP estimate for a small near-zero coefficient does **not** imply a material difference in original selected sites or a changed source criterion. The old observed four-index precision modes under Issue #24/#57/#61 had identical locations and absolute differences, and the new six-run study independently confirms the latest **scored-objective digest difference** also corresponds to exactly these four coefficient fields. The original older #89/#92 runs did not archive their raw coefficient payloads, so their precise per-file bytes are **not directly recovered** retrospectively.

## Reproduction artifacts

[All four artifacts for CI #39289914383](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39289914383): complete per-run model-input JSON, original SCIP/result canaries, CPU/runtime metadata, per-host geometry and independent aggregation. All scheduled for **2026-11-02** expiry under GitHub's 14-day research retention:
- [Comparison artifact #12204793482](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39289914383/artifacts/12204793482) — full six-row exact objective/source-manifest differences, digest `sha256:0c39a9133e32b16afc96c8a3f4ec50ba28fbf6f6e29ae7da874adba1156fcb90`, expires 16:58:15Z
- [r1 raw #12203943055](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39289914383/artifacts/12203943055) — both original full models, runtime and geometry, expires 16:57:38Z
- [r2 raw #12204237835](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39289914383/artifacts/12204237835) — both original full models, runtime and geometry, expires 16:57:36Z
- [r3 raw #12205495787](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39289914383/artifacts/12205495787) — both original full models, runtime and geometry, expires 16:57:39Z

**Archive warning:** Artifacts are ephemeral and owner-controlled permanent scientific custody is not confirmed. This Markdown summary is a human-reviewed proposed durable *finding*, not a substitute for lossless original model and environment files.

## Conclusions and scientific limitations

1. **Supported:** At fixed source code and the explicitly pinned *direct* Python dependencies, the observed six original N20/SCIP replays produced exactly two scored-objective coefficient SHA-256 modes, caused at the input-data level by the **four listed changed numerical coefficient bytes**. Every process matched its host's two-run mode and preserved mathematical solution and original geometric source graph.
2. **Not supported:** CPU manufacturer/certain compiled NumPy/OpenBLAS/libm dispatch as a **causal** mechanism; only CPU-host association is observed here. Earlier original free/fixed np.linalg.norm/exp trace studies already narrow likely floating-point operations; a separate controlled numerical-dispatch study is required to ascribe a low-level cause.
3. **Model policy:** Do not silently 'fix' original scores through rounding, replace historical frozen penalties/seed schedules or conflate source model hash with objective hash. Record exact source byte/environment identity and use strict `objective_fingerprint` for bit-exact scenario cache identity; identify separately any tolerance-equivalent *numerical* comparisons. A mathematically optimal result for this historical scored function is **not** published-paper AHP/D2 parity or field deployment validity.
4. **Retrospective limits:** The new run reproduced both old SHA strings, but the original older run's complete raw coefficient model was not in its small artifact; no assertion of retrospectively byte-for-byte recovered old raw model or exact CI host provenance.

**Next steps:** record observed positive result on Issue #24; maintain strict mathematical/scientific claim status in Issues #85/#91; review numerical equivalence and cache policy before joined UI work (#88); request original expert/GIS/shoreline/RF/water observations under #87 before any model-science approval. No new numerical parameter bounds or physically validated network claim.
