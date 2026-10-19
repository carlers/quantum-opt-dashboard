# Issue #62 — controlled NumPy dispatch and compiled-binary comparison

**Scope:** Observational numerical-runtime diagnosis on the six source-verified N20 exact float64 operand cases from [pair trace PR #61](https://github.com/carlers/quantum-opt-dashboard/pull/61), not a correction to the scientific N20 model. New work in [draft PR #63](https://github.com/carlers/quantum-opt-dashboard/pull/63). Methods and failed preflight amendment: [N20_NUMPY_DISPATCH_PROTOCOL.md](N20_NUMPY_DISPATCH_PROTOCOL.md).

## Study 1 — within-host NumPy dispatch intervention (2026-10-19 UTC)

[GitHub Actions run #39180686631](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39180686631), source commit `1d9185139dca4d9009277e62016c91d8b4943a0a`: **SUCCESS** — all three Ubuntu 24.04 x86 jobs, independent fourth aggregation, **10/10 adversarial tests**. Three independently provisioned hosts each ran **two fresh Python 3.12/NumPy 2.5.4 baseline processes** and **two fresh processes with `NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4`**, before NumPy import. The masked arm actually reported both dispatch targets disabled. Frozen operand manifest SHA `d3df1108165745b8b29723604dfbf682478a512f5b05ce18dd3182631b394785`; no original source data, QUBO, optimizer, or model coefficients changed. **All 12 processes audited**, exact repeats within each host/arm.

**Methodological correction retained:** Initial preflight attempts using `AVX2,FMA3` failed because this pinned NumPy 2.5.4 reports `__cpu_baseline__=['X86_V2']` and `__cpu_dispatch__=['X86_V3','X86_V4','AVX512_ICL','AVX512_SPR']`. This was recognized **before the successful paired study**. Failed Action runs and the protocol amendment remain visible; there is no hidden, cherry-picked successful old intervention.

| Host | Observed CPU | OpenBLAS auto architecture | Main `np.exp` result changed by X86_V3/V4 mask? | Main `np.linalg.norm` changed? |
| --- | --- | --- | --- | --- |
| r1 | AMD EPYC 9V45 | `SkylakeX` | **Yes, both frozen exponents, one ULP** | No, all four unchanged |
| r2 | Intel Xeon Platinum 8573C | `SkylakeX` | **Yes, both frozen exponents, one ULP** | No, all four unchanged |
| r3 | AMD EPYC 7763 | `Haswell` | No, both exponents already match masked mode | No, all four unchanged |

**Across-host binary provenance:** all three hosted jobs installed **exactly the same byte-level x86 numerical artifacts**, verified by SHA-256:

- `_multiarray_umath.cpython-312-x86_64-linux-gnu.so`: `b185dfe64b07180bedc7c15fb2735b0d0f4f4e09eb9c15bd8e67f74568aebcbf`.
- `_umath_linalg.cpython-312-x86_64-linux-gnu.so`: `2e075f582c3a25a21fe97a55931a0fdb22ceb84f4fce8203a5040d405ccf65ce`.
- Bundled OpenBLAS `libscipy_openblas64_-f48b354e.so`: `432e1c1739731468ba305771af96773939e43016643e2d630f58cb45b6670e96`.
- Bundled `libgfortran` and `libquadmath` SHAs also identical within and across hosts. All used Python 3.12.15, Linux glibc 2.39, NumPy 2.5.4, `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`.

**Mask-specific result:** Both frozen exponent cases (`exp_f3_fixed28`, `exp_f19_fixed22`) changed exactly **one binary64 ULP** on r1/r2 with the NumPy dispatch mask. The new masked mode matched r3's baseline. The diagnostic **length-one `np.exp` array operation also changed**, while `math.exp` did **not** change in the paired same-host test. This supports **NumPy ufunc-dispatch sensitivity for these exact `exp` operands on the observed hosts**, not a demonstrated individual SIMD instruction or proof of CPU architecture causation.

**Norm-specific result:** None of the four `np.linalg.norm` outputs changed with the NumPy SIMD mask **within** any host; the previously observed one-ULP **cross-host difference persisted in both arms**. Critically, the frozen-operand *alternative diagnostic* `np.square`, `np.sum`, `np.sqrt` and `math.hypot` outputs were **bitwise identical across r1 and r3** for all four norm cases, while the original public `np.linalg.norm` output was not. The reported OpenBLAS selected runtime architecture also differed (`SkylakeX` vs `Haswell`), although the bundled library SHA was identical. This implicates a **possibly independent BLAS/runtime code path** for the observed norm difference, without establishing causality.

**Exact raw evidence:** [paired comparison artifact #12156535253](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39180686631/artifacts/12156535253), [r1 original four-process archive #12156505288](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39180686631/artifacts/12156505288), [r2 #12155744076](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39180686631/artifacts/12155744076), [r3 #12156241343](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39180686631/artifacts/12156241343). These are 14-day Actions artifacts (expire approximately November 2, 2026 UTC). The records include allowlisted platform/CPU/SIMD/BLAS runtime fields, full exact hex values for all six operations, per-stage diagnostic values, and compiled binary hashes; no full filesystem paths or credentials.

## Follow-up decision after observing Study 1

The *next* experiment is explicitly **post-observation exploratory**, not a second preregistered confirmation. Without modifying the frozen input bytes or NumPy/Python binaries, launch two fresh processes per host with **`OPENBLAS_CORETYPE=HASWELL`** before import, compared with two fresh baseline processes on the same host. Independently verify OpenBLAS reports architecture `Haswell` in the overridden processes. This tests whether a selected OpenBLAS kernel mode is associated with the previously unchanged norm result, separately from the NumPy SIMD-mask intervention. The protocol must be committed **before running this new study**, and a negative result is meaningful.

OpenBLAS documents `OPENBLAS_CORETYPE` as an override for a DYNAMIC_ARCH build: https://www.openmathlib.org/OpenBLAS/docs/runtime_variables/ . NumPy explicitly states `numpy.linalg` may rely on CPU-specific BLAS/LAPACK: https://numpy.org/doc/stable/reference/routines.linalg.html .

**Limits:** This is a tiny finite set of six source-derived operands, not broad platform certification. Matching extension SHAs excludes differing *those measured binary files* as the proximate difference in this run, but does **not** exclude differing dynamic CPU dispatch, libc, OS, or hidden runtime states. No original notebook weights, historical article numbers, input QUBO penalties, source archive or prior benchmark results have been changed. All branches stay draft/unmerged, no deployment.

## Study 2 — same-host OpenBLAS Haswell coretype override, post-result exploratory

[GitHub Actions run #39181329033](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181329033), scientific code head `b1448392a186a372cb4732567c7d92d41569dc6d`: **SUCCESS**, three separately allocated x86 Ubuntu 24.04 jobs × **two fresh auto + two fresh `OPENBLAS_CORETYPE=HASWELL` processes each**, **12/12 process records**, complete independent comparison, **8/8 synthetic falsification tests** passed. The six frozen IEEE754 input groups, pinned NumPy 2.5.4/OpenBLAS binary file checksums, Python 3.12 and one-thread direct numeric settings were unchanged from Study 1. The override was set on the **process launcher before importing NumPy** and confirmed by the `threadpoolctl` OpenBLAS selected architecture. [Read-only pre-result protocol](N20_OPENBLAS_CORETYPE_PROTOCOL.md).

| Runner | CPU reported | OpenBLAS architecture, auto → forced | Four `np.linalg.norm` inputs | Two NumPy `np.exp` inputs |
| --- | --- | --- | --- | --- |
| r1 | AMD EPYC **9V74** | Haswell → Haswell | No change, **negative control** | No change |
| r2 | AMD EPYC **7763** | Haswell → Haswell | No change, **negative control** | No change |
| r3 | Intel Xeon **6973P-C** | **SkylakeX → Haswell** | **All four changed one binary64 ULP**, matching r1/r2's Haswell results | No change |

**Original public `np.linalg.norm` numerical outputs on the actually affected r3 host:**

| Frozen pair | Auto SkylakeX `np.linalg.norm` | Forced Haswell `np.linalg.norm` |
| --- | --- | --- |
| free0/fixed32 | `0x1.2223d36ece989p+14` | `0x1.2223d36ece988p+14` |
| free9/fixed26 | `0x1.89bffffffff11p+12` | `0x1.89bffffffff10p+12` |
| free10/fixed30 | `0x1.6d09d5acd89cep+12` | `0x1.6d09d5acd89cfp+12` |
| free17/fixed25 | `0x1.51800000000b0p+12` | `0x1.51800000000afp+12` |

Both repeated processes in *each arm* were bitwise identical, on *every host*. The separately calculated `np.square`, `np.sum`, `np.sqrt`, `math.hypot`, `math.exp`, and NumPy `np.exp` diagnostics **did not change under this Haswell override on any host**. Thus this comparison isolates a **within-machine OpenBLAS target-selection-sensitive norm difference** for these exact N20-derived vectors; the NumPy SIMD-mask Study 1 separately demonstrated an exp-sensitive change. Two distinct documented configuration interventions control the two different observed operation families.

**Raw evidence:** [comparison artifact #12156386935](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181329033/artifacts/12156386935) and unmodified host-process records [r1 #12155989133](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181329033/artifacts/12155989133), [r2 #12156043556](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181329033/artifacts/12156043556), [r3 #12155773518](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181329033/artifacts/12155773518). Retention until approximately November 2, 2026 UTC. Original source provenance and exact compiled NumPy/OpenBLAS SHA equality within each host were validated. Method is **exploratory** because it was chosen after observing Study 1; retain the two natural-Haswell negative hosts as reported.

### Combined scientific interpretation

Both conditions differ by a single explicitly controlled runtime setting **within the same host and identical compiled NumPy/OpenBLAS binaries**. The reported case-dependent output-bit changes are therefore linked to the **NumPy dispatch target selection for `np.exp`** and **OpenBLAS dynamic target selection for `np.linalg.norm`** in the observed hosted environments. This is stronger than inferring a cause from CPU names or floating-point source coefficients alone.

Still **not supported**: assignment to one individual assembler instruction, universal NumPy/BLAS cross-platform reproducibility, scientific relevance of one ULP in other N/K instances, mathematical correction of the historical manuscript, QPU performance claims, or automatically adding an `OPENBLAS_CORETYPE`/NumPy SIMD mask to the production dashboard. The latter could change scientific computation globally and would require a separately reviewed reproducibility policy with sensitivity tests. Original full N20 SCIP/exhaustive canaries already passed in parent PRs #56/#57/#61 and were not rerun inside these tiny diagnostic processes.

