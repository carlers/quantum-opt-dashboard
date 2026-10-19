# Issue #62 — fixed-input NumPy compiled-runtime and dispatch sensitivity study

**Preregistered experiment scope, created before inspecting this experiment's samples.** Builds on review-only [PR #61](https://github.com/carlers/quantum-opt-dashboard/pull/61), which traced the *original* N20/K5 free-to-existing station coefficients to differences in the observed `numpy.linalg.norm` and separately evaluated `numpy.exp` outputs at exactly identical IEEE754 inputs. Original paper-model parity and a unique lower-level root cause **remain unverified**. Parallel frozen OpenJij QUBO PR #59 tests a distinct historical sampler question.

## Pre-result amendment: NumPy 2.5.4 CPU-dispatch target names

Initial preflight CI at [#39180500530](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39180500530) **failed before any paired numerical evidence was collected**. The original protocol attempted the documented older-style `NPY_DISABLE_CPU_FEATURES=AVX2,FMA3`, but the pinned **NumPy 2.5.4 build explicitly reported** `__cpu_baseline__=['X86_V2']` and dispatched targets `['X86_V3','X86_V4','AVX512_ICL','AVX512_SPR']`. Hardware `AVX2=True` and `FMA3=True` did not verify that a dispatch target was masked.

**Before inspecting any paired baseline-vs-intervention results**, the attempted diagnostic intervention was therefore amended to set `NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4`, with strict verification that NumPy reports **both dispatched target flags disabled** in each new masked process. This is an explicit version-specific protocol amendment prompted by the failed preflight, **not** a successful prior control, a new source-model coefficient policy, or an adaptive response to sampler outcomes. The earlier unsuccessful runs remain in the GitHub Actions history.

## Hypothesis and controls

*Null observational hypothesis:* within each host, masking NumPy's optional X86_V3/X86_V4 CPU-dispatch paths **before importing NumPy** will leave all six frozen NumPy numerical outputs bit-for-bit identical. *Alternative:* at least one six-case result changes in the masked arm on that same host, in which case the observed behavior is sensitive to this specific dispatch intervention, but it does **not** identify a single compiled function, instruction or CPU cause.

Use exact six hex-encoded operands from validated [Issue #60 source N20 trace run #39177889565](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39177889565): four two-dimensional N20 station displacements evaluated with precisely `np.linalg.norm(np.array(values, dtype=np.float64))` and two N20 wake exponents evaluated with `np.exp(np.float64(value))`. **Never regenerate candidate lake coordinates, change the model, reselect seeds, tune a penalty or round input coefficients.** `numpy==2.5.4` and Python 3.12 are direct-version pinned.

Three independently allocated x86 `ubuntu-24.04` hosts, each with two paired intervention arms:

- **baseline**: `NPY_DISABLE_CPU_FEATURES` absent before invoking the Python process. Run two *fresh interpreters*, labeled `rH-baseline-a/b`.
- **no-x86-v3-v4**: `NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4` present at the process launcher before importing NumPy. Run two *fresh interpreters*, `rH-no-x86-v3-v4-a/b`; the probe **fails** if NumPy still reports either feature as enabled. NumPy documentation identifies this variable as a dispatch limitation rather than a model change.

**Total:** 3 hosts × 2 modes × 2 fresh processes = **12 observations**. Each host uses the same installed NumPy wheel for all four processes. The audit requires matching SHA-256 of `numpy._core._multiarray_umath`, `numpy.linalg._umath_linalg` and the package's bundled `numpy.libs` binary files *within that host*. It records each basename, file size and SHA without full path. The runtime record includes pinned package/Python version, CPU family, machine architecture, glibc, NumPy `__cpu_features__`, `__cpu_baseline__`, `__cpu_dispatch__`, allowlisted parts of `np.show_runtime(mode='dicts')`, and allowlisted threading/SIMD environment fields only. No credentials, complete OS environment, private paths or hostname are exported.

## Independent arithmetic-stage observations

For each norm input, also separately calculate binary64 `np.square`, `np.sum`, `np.sqrt`, and `math.hypot` on the same frozen values. For each exponent, separately calculate `math.exp` and a one-element `np.exp` array call. These are **diagnostic alternative computations**, not replacements for the notebook's actual scalar `np.linalg.norm` and `np.exp(np.float64)`. Different results among these variants do not prove that NumPy used or did not use a given internal libm or BLAS instruction. Exact hex operands, outputs, and all these diagnostic fields are archived.

Scientific validation gates:
1. Fail any changed frozen source-operand digest or case ordering; missing/duplicate samples, non-finite outputs, missing/ambiguous compiled extension SHA, unexpected NumPy version, or unconfirmed SIMD-mask state.
2. Distinguish **within-process-arm repeat equality**, **within-host baseline versus masked-arm** differences, and **cross-host output modes** without averaging or retroactively choosing favorable machines.
3. A *changed* NumPy public result when the SIMD mask is the only intentionally changed variable on the same host is evidence that these NumPy public operations are affected by the dispatch intervention **in the tested software/runtime configuration**. It is not automatically attributable to X86_V3 or X86_V4 instruction execution in the exact call; masked dispatch may affect multiple routines.
4. A *negative* result leaves earlier heterogeneous-runtime ULP drift intact; masks may be irrelevant for these operations or another runtime factor may dominate. Do **not** claim universal stability.
5. Existing exact N20/K5 SCIP, 15,504-combination original problem verification, 300 free/fixed pair trace and earlier frozen exact historical B QUBO study retain their independent results. No new notebook solver executions are required inside the microbenchmark's 12 tiny processes; the PR base and its existing checks remain the scientific reference.

## Boundaries and decision following the study

NumPy's official runtime CPU-feature control documentation: [NumPy CPU dispatch](https://numpy.org/doc/2.2/reference/simd/build-options.html) and [NumPy runtime inspection](https://numpy.org/devdocs/reference/generated/numpy.show_runtime.html). NumPy runtime features and compiled binaries may be host-dependent despite pinning the *package version*; this protocol records those instead of silently conflating them with processor labels.

Do not run large stochastic sweeps; no OpenJij or quantum hardware in this study. Preserve all exact negative and positive results, code SHA, host metadata and full binary digests. Action artifacts expire after 14 days; create an approved durable scientific archive if these data will support a thesis result. No `main`/preview/production, archived notebook/GeoJSON, AHP coefficients, benchmark seed, scientific objective, or frozen historical QUBO output is modified. Work remains **DRAFT** until reviewed and explicitly authorized for merging. Publication-table discrepancy #16 is independent of this numerical-runtime investigation.
