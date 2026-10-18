# Issue #60 — free/fixed coefficient trace observations

**Result type:** Bounded observational precision study, not model correction. Source code: [draft PR #61](https://github.com/carlers/quantum-opt-dashboard/pull/61), stacked on the instrumented working N20 reference [PR #57](https://github.com/carlers/quantum-opt-dashboard/pull/57) and its scientific parent [PR #56](https://github.com/carlers/quantum-opt-dashboard/pull/56). The experiment's original pre-results procedure is in [N20_FREE_FIXED_ULP_TRACE_PROTOCOL.md](N20_FREE_FIXED_ULP_TRACE_PROTOCOL.md).

## First complete six-process study — 2026-10-18 UTC

[GitHub Actions #39177889565](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39177889565) at source SHA `3a992e03be5f1ba8dcc911c09fef0c0c935ed6cd` — **SUCCESS**: three independently provisioned Ubuntu 24.04 runner jobs, each two complete N20 notebook executions in fresh Jupyter kernels, with the same direct scientific dependency versions as PR #57. All six replayed source SHA integrity checks, SCIP optimum and exact 15,504 N20/K5 independent combinations. The original model/constraint tolerance gate passed. The independent pair validator succeeded for all **300 original free–fixed pairs per process**, for all sequential original linear additions and every final original linear coefficient. Fast comparator test suites passed **8/8 + 7/7**.

| Runner | Reported CPU | Two process results, original source model SHA **excluding new diagnostic trace** |
| --- | --- | --- |
| r1 | AMD EPYC 9V45 96-Core | `3047107f6c718ba2774ed90af298f2618a85aeacbd94820ccd8a4c4a9dde0feb` both |
| r2 | AMD EPYC 7763 64-Core | `301afef26e86802852ec3f87412d11405b79e9e9067856e5503daa85253b4af2` both |
| r3 | AMD EPYC 7763 64-Core | Same `301afef26e...` both |

These exact *scientific core* SHA-256 values are the same two original-model modes previously observed in **instrumented** PR #57, not new accidental research inputs. The full trace-bearing manifest has different digests because it adds instrumentation fields. **CPU association remains observational, not causal.**

### All 300 free–fixed pair stages checked

**20 / 300 pair records differed** between r1 and r2/r3, but not all were source-coefficient changes. The first changed field for each differing pair, in the predeclared within-pair observation order, was:

| First changed recorded field | Pair records | Interpretation |
| --- | ---: | --- |
| `distance_float64_hex` | **12** | Identical recorded projected displacement, but different `float(np.linalg.norm(displacement))` last bits; downstream wake/redundancy terms can change |
| `decay_probe_separate_call_float64_hex` | **4** | Identical recorded norm/exponent but a different *separately evaluated* NumPy exponential last bit; some actual wake and pair coefficients also changed |
| `linear_before_add_float64_hex` | **4** | Earlier changed pair additions were carried forward into later terms; these are propagation, not newly different pair calculations |

**Earliest differing pair in the original loops:** free local 0 / fixed local 32, free master feature `5253` / fixed master feature `4613`: the same displacement was recorded but `np.linalg.norm` differed by one low-order bit. That pair was **outside the coefficient interaction radius**, so its norm difference did **not** alter the scientific objective. Do not cite it as the sole cause of the final objective drift.

**Pairs first affecting source-linear coefficients:** original pair coefficients changed for the following nine free/fixed local pairs: `(3,28)`, `(6,24)`, `(9,26)`, `(10,30)`, `(13,20)`, `(13,21)`, `(17,25)`, `(19,22)`, `(19,24)`. Other changed pairs included propagated `linear_before_add` and thresholded/remote diagnostic differences. Despite intermediate differences for more sites, only **final** original linear coefficients at free local indices **9, 10, 17, 19** differed (1.11×10⁻¹⁶ or 2.22×10⁻¹⁶), as in the earlier #57 study.

For those four final changing sites, first scientific-input differences were:

| Free site / fixed pair | First differing recorded field | What follows |
| --- | --- | --- |
| 9 / 26 | `distance_float64_hex` | Redundancy and pair coefficient differ; later 9/28, 9/29 and 9/32 addends use the already different accumulator |
| 10 / 30 | `distance_float64_hex` | Redundancy, directional cosine and wake differ; final candidate 10 coefficient differs |
| 17 / 25 | `distance_float64_hex` | Redundancy/wake differ; candidate **17** has the unique historical row-sum maximum behind the one-ULP QUBO penalty difference (#26) |
| 19 / 22 | `decay_probe_separate_call_float64_hex` | Same displacement, distance and exponential argument; separate exponential result, wake and pair term differ. An additional distance difference occurs for 19/24 |

**Archived evidence:** [six-process per-pair comparison artifact #12154947499](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39177889565/artifacts/12154947499) (14-day retention, approx. expires November 1, 2026). It retains per-pair exact hexadecimal values, first differing fields and six source-model snapshots. Original unmodified runner artifacts [r1 #12155032323](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39177889565/artifacts/12155032323), [r2 #12155057159](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39177889565/artifacts/12155057159) and [r3 #12154932669](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39177889565/artifacts/12154932669) contain the full model and 300 trace records for **both** fresh processes on each host.

## Explicitly exploratory frozen NumPy microprobe — homogeneous x86 sampling

After Study #39177889565, six fresh microprocesses were run against four exact float64 displacement vectors and two exact float64 exponents extracted from that verified original N20 pair trace, using only **pinned NumPy 2.5.4**, not a rebuilt lake/SCIP model. [Micro CI run #39178324563](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39178324563) **SUCCESS**; **6/6** separate adversarial microprobe checks. **All three fresh hosts happened to report AMD EPYC 7763**, and all six observed exact results matched one binary64 mode for all six frozen operations. Raw [comparison artifact #12155710503](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39178324563/artifacts/12155710503). The numerically identical values matched the previously observed EPYC-7763 mode of the source notebook. **This is a negative within-that-CPU sample**, not a proof that the issue disappeared.

**Next follow-up chosen after this negative result (explicitly exploratory, not preregistered confirmation):** run precisely the **same six frozen input operations** on two x86 Ubuntu 24.04 runner jobs and one **Ubuntu 24.04 ARM64 runner** job, each with two fresh processes. Keep Python 3.12 and NumPy 2.5.4 and exact hex inputs fixed; compare all binary64 results and CPU/architecture metadata. **An ARM difference would demonstrate execution-environment sensitivity for those frozen operations, not isolate one CPU instruction or libm implementation.** If the architecture runner or NumPy wheel is unsupported, report an infrastructure failure and preserve the existing negative finding; do not alter source scientific coefficients or substitute alternate rounded inputs.

## Limitations and next exploratory control

The trace **strongly localizes observed last-bit behavior** to the original source's NumPy vector norm and NumPy exponential stages. A matching displacement with a different norm means earlier coordinate preparation is not the cause of that norm difference *in the observed run*. A matching exponential argument with a different separately evaluated exponential value suggests platform-dependent library numeric behavior, **but that diagnostic exp is not the very same function-call return object used in the original wake calculation**. Neither observation identifies a particular compiler flag, underlying libm/OpenBLAS/SIMD kernel, CPU instruction, or universal cause.

**Explicitly exploratory follow-up decided after reading the above results:** freeze the exact float64 input bytes of two changing displacement vectors and two exponential arguments *from this source-verified run*, then evaluate `np.linalg.norm(np.array([x,y], dtype=np.float64))` and `np.exp(np.float64(argument))` under pinned direct NumPy/Python versions across separate newly provisioned hosts and processes **without executing the lake model**. This tests whether the low-bit modes arise from those operations on byte-identical inputs alone. It is not a newly preregistered independent replication and must be reported even if all observed CPUs happen to produce the same numbers. The original source objective equations and past benchmark results remain unchanged.

**Not established:** published manuscript Table V parity, universal bitwise numerical stability, exact underlying C-level mechanism, different hardware causal attribution, or any quantum advantage. The older controlled [PR #27](https://github.com/carlers/quantum-opt-dashboard/pull/27) and frozen [PR #59](https://github.com/carlers/quantum-opt-dashboard/pull/59) experiments already separately quantify one-ULP QUBO-penalty sensitivity and fixed-input classical sampler repeatability; nothing in this trace requires changing their frozen seeds, results or penalty.
