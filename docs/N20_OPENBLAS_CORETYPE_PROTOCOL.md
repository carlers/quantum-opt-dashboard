# Issue #62 — exploratory OpenBLAS architecture intervention after NumPy dispatch study

**Pre-result protocol committed before reading any of the OpenBLAS intervention's own numeric outputs.** This is a new, explicitly **adaptive follow-up** to the original NumPy SIMD-mask experiment, rather than a posthoc modification of its outcome. [Study 1 fixed-input results](N20_NUMPY_DISPATCH_RESULTS.md) and [initial study method](N20_NUMPY_DISPATCH_PROTOCOL.md) are preserved separately.

## Research question

In the observed N20 floating-point source scenario, the four frozen `np.linalg.norm` outputs differed by approximately one binary64 ULP across x86 CI hosts, while the same host's `NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4` intervention had **no** effect on norms. Its separately evaluated NumPy square/sum/sqrt/hypot diagnostics were identical across differing hosts; `threadpoolctl` described auto-selected **SkylakeX** versus **Haswell** OpenBLAS runtime architectures with identical compiled OpenBLAS SHA across hosts.

**Proposed isolated intervention:** Does `OPENBLAS_CORETYPE=HASWELL` (set on the child interpreter launcher **before importing NumPy**) change the exact original `np.linalg.norm` result on hosts that otherwise auto-select a different OpenBLAS target, when source operands and binaries are identical?

OpenBLAS documents `OPENBLAS_CORETYPE` for a DYNAMIC_ARCH build: https://www.openmathlib.org/OpenBLAS/docs/runtime_variables/ .

## Method, fixed before outcomes

- Reuse the **same committed `FROZEN_CASES` with exactly six source-derived IEEE754 operand groups** from validated Issue #60. Four two-component `np.linalg.norm` vectors and two scalar `np.exp` arguments. Source SHA `d3df1108165745b8b29723604dfbf682478a512f5b05ce18dd3182631b394785`.
- Three independent x86 Ubuntu 24.04 GitHub-hosted runner jobs. Within each: two fresh **auto OpenBLAS target** processes and two fresh **forced Haswell target** processes; **12 observations** in total. Direct Python 3.12, NumPy 2.5.4 and threadpoolctl 3.6.0 pinned. `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`. No `NPY_DISABLE_CPU_FEATURES` setting in either arm.
- Fail if forced arm does not report an allowlisted OpenBLAS `architecture` equal to `Haswell`, or if full installed SHA of NumPy compiled `_multiarray_umath`, `_umath_linalg` and bundled OpenBLAS libraries changes *within the same host*. Capture allowlisted CPU model, feature dispatch, libc, OpenBLAS implementation/version/architecture and exact frozen inputs/outputs.
- Prespecify **same-host auto vs Haswell differences**, both repeated process results for each arm, binary hashes and cross-host result modes. Retain all intermediate alternative diagnostics from `np.square`, `np.sum`, `np.sqrt`, `math.hypot` and `math.exp`, but **do not replace** the source notebook's actual `np.linalg.norm` or `np.exp` calls with any diagnostic.
- A change in `np.linalg.norm` when only `OPENBLAS_CORETYPE` was intentionally changed within a host is evidence of **OpenBLAS-selected-target sensitivity under the tested software/runtime conditions**, not uniquely a given assembler instruction, threading race, processor family, or proof of a numerical error.
- If auto already chose Haswell, it is a **negative within-host control**; do not discard that run or claim a new cross-host cause. If a requested target is unsupported on any host, fail visibly and report the limitation rather than substituting another target based on the desired result.
- No randomized seed/annealing/SCIP work happens in microprocesses. The archived N20 model/GeoJSON, validated source notebook N20 formulation, historic QUBO, master/fixed candidate ordering, published AHP/D2 claims and old 665-vs-698 SA observations are untouched.

**Research interpretation:** Study 1's NumPy CPU-mask finding pertains to two `np.exp` cases; this OpenBLAS follow-up pertains to the four `np.linalg.norm` cases. Do not conflate the two interventions. Preserve both original and exploratory studies, source SHAs and all 14-day GitHub artifacts; do not propose a universal numerical fix, constant rounding or deployed app change without independent scientific review. All work remains DRAFT and requires separate owner approval to merge.
