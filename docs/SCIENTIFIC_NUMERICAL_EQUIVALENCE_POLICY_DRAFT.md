# Proposed numerical equivalence and runtime policy — decision draft

**Status: PROPOSAL ONLY.** Research [issue #64](https://github.com/carlers/quantum-opt-dashboard/issues/64); evidence from draft PRs [#56](https://github.com/carlers/quantum-opt-dashboard/pull/56), [#57](https://github.com/carlers/quantum-opt-dashboard/pull/57), [#61](https://github.com/carlers/quantum-opt-dashboard/pull/61), [#63](https://github.com/carlers/quantum-opt-dashboard/pull/63), and independent historical QUBO/SA [#59](https://github.com/carlers/quantum-opt-dashboard/pull/59). This document is not a change to original science, solver coefficients, historical results or deployed application. The research owner and adviser must approve any numerical acceptance thresholds or runtime mode.

## 1. What are we actually trying to reproduce?

Treat **four separate targets**, never as synonyms:

1. **Source fidelity:** the original archived notebook and input GeoJSON have known immutable SHA-256, and the reviewed maintained N20 working notebook is an explicit derivative, not a replacement of original evidence.
2. **Mathematical/model equivalence:** the same *N20/K5 instance* includes the same 20 ordered candidate IDs, **15 existing station IDs actually flagged by the GeoJSON**, site utilities/factor definitions, 12 original free–free quadratic terms, local one-hop graph, objective, and exactly five new sites. Independently enumerate all `C(20,5)=15,504` choices and verify exactly **1,077** original-feasible choices.
3. **Solver/scientific outcome:** independently recompute feasibility, raw unpenalized original objective, source-selected local sites `[0,1,3,6,7]`, and original source-derived SCIP optimum **approximately `−3.3012934918564643`**. The published `−3.301319` is an **unresolved different reported input/number**, not a baseline to fit by rounding.
4. **Bitwise numerical/runtime reproducibility:** exact IEEE754 coefficients and 46-bit SA trajectories might differ when compiled numerical dispatch changes. Bit-for-bit reproducibility is a **separate diagnostic target**, not the sole pass/fail criterion for scientific conclusions. On one exactly frozen historic B QUBO/seed list, 6×1,024 classical OpenJij samples matched bitwise in the tested versions/hosts; this is bounded, not universal.

### Source hierarchy (pending review, not a revision of history)

- **Historical original:** `problems/water_quality/notebooks/experiment9 grid search copy.ipynb`, SHA-256 `08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048`.
- **Original geospatial evidence:** committed N20 reference GeoJSON, source SHA-256 `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`; it has **15 marked existing stations**. Do not silently substitute three simulated stations.
- **Working maintained N20 reference:** source-derived, preserved-order derivative on draft PR #56; float64/source-provenance studies are separate stacked PRs #57/#61/#63. PR #56 is **not yet merged**, so labeling it canonical in `main` requires explicit owner approval.
- **Manuscript:** source **as reported**, including Table III/IV/V conflicts documented in [MANUSCRIPT_NOTEBOOK_PROVENANCE_AUDIT.md](MANUSCRIPT_NOTEBOOK_PROVENANCE_AUDIT.md). Do not silently harmonize AHP weights, D2 semantics or objective values.

## 2. Three different kinds of tests

| Category | Proposed acceptance gate | Why |
| --- | --- | --- |
| **Invariant / exact** | Source byte SHA-256; ordered 20+15 station IDs; exact K=5, neighborhood graph and 12 quadratic free/free pairs; 15,504 considered and 1,077 feasible; no duplicate/missing records | Changes are model/provenance differences, not harmless floating-point noise |
| **Numeric result / science** | SCIP status `optimal`; raw original objective independently recalculated; selected local site set `[0,1,3,6,7]`; energy close to independently certified source-derived optimum within an explicitly adviser-approved bound | Focus on physical optimization conclusion and feasibility |
| **Diagnostic float64 / bitwise** | Store exact `float.hex` source coefficient/penalty/term digests and runtime provenance; report all host bit-mode differences and effects separately; **do not fail physical model science solely because a 1-ULP intermediate differs** | Last-bit `np.linalg.norm`/`np.exp` changes have been controlled experimentally |

**Candidate energy threshold for review, NOT ADOPTED:** `abs(energy - (−3.3012934918564643)) <= 1e−7` on the **same committed source-derived N20 model**. This is only a regression guard reflecting already run prototype checks; it is **not** a scientific resolution criterion or tolerance for changing datasets, feature weights, penalties, source equation, or the manuscript's 2.55×10⁻⁵ discrepancy. Proposed coefficient checks should retain **both** absolute ULP size and a dimensionally meaningful physical tolerance to be chosen by the research team.

A “successful CI” with a numeric energy tolerance **does not** certify identical QUBO, probabilities, SA feasibility rates, or published data provenance. Report the pass type and inputs explicitly.

## 3. Runtime environment tiers (select, do not silently impose)

| Tier | Intended usage | Must record | Cannot claim |
| --- | --- | --- | --- |
| **R0 – mathematically equivalent results** | Routine exploratory N20 SCIP validation across local/CI machines | Source hashes, Python/NumPy/SciPy/Shapely/PySCIPOpt direct versions, site IDs, original constraints, numerical objective and exact enumeration | Identical coefficients at every `float.hex` |
| **R1 – bounded environment reproducibility** | Thesis/external review of a source-derived fixed N20 protocol | Above + OS/CPU, NumPy/OpenBLAS versions, actual selected BLAS runtime architecture, SIMD dispatch, numeric threading, original model-input canonical SHA | Globally portable bitwise behavior on all CPUs |
| **R2 – frozen binary-input experiment** | Testing exact same classical SA and QUBO, or narrow numerical kernel causality | Frozen binary64 source operands and SHA; QUBO/offset and read-seed manifest; binary wheel/.so checksums; all sampled full states; restricted process runtime metadata | Reproducing a *different* notebook or the manuscript by holding only sampler bits fixed |

Findings motivating R1/R2:
- [PR #61](https://github.com/carlers/quantum-opt-dashboard/pull/61): among 300 actual free–fixed pair records, 20 differed in low bits, 12 first at NumPy norm, four at separately evaluated NumPy exponential, and four at propagated accumulator values; final original linear changes occurred only at free sites 9,10,17,19 and did **not** change the N20 optimum.
- [PR #63](https://github.com/carlers/quantum-opt-dashboard/pull/63): same Python/NumPy 2.5.4 and byte-identical NumPy/OpenBLAS library files; a **verified `X86_V3,X86_V4` NumPy dispatch mask** changed only the two tested `np.exp` results on two of three hosts. A **separate preregistered-after-first-study OpenBLAS `OPENBLAS_CORETYPE=HASWELL`** intervention changed four `np.linalg.norm` outputs on a host auto-selecting SkylakeX, not `np.exp`; natural Haswell hosts were negative controls. These are observation-bounded mechanisms, not justification for deploying either environment variable.

Do **not** apply either experimental mask to the working notebook or production without separately approved validation: even an apparently stable one-ULP fix can change optimization penalties and stochastic sample paths.

## 4. Design of any proposed stabilization/sensitivity experiment

Before running: record scientific question, exact source/input SHAs, environment/binary SHA, which **single** variable is intervened on, fixed seed schedule if applicable, expected measurable outputs, full success/failure gates and plan for negative outcomes. Implement as an **independent branch** with original untouched.

For hypothetical 1-ULP candidate terms at 9/10/17/19, independently report:
- Original model coefficient hex, perturbed coefficient hex and original raw energy delta for each *feasible* selected subset.
- Exactly selected stations, original K/one-hop feasibility, SCIP optimum and independently enumerated objective.
- If QUBO penalty changes, treat this as a **new explicitly labeled input sensitivity condition**; do not relabel original historical A/B results or assume a solver package's random seed forces cross-version parity.
- For sampled classical OpenJij, denominator, complete child-seed list, 46-bit state vectors, feasible/optimum hit counts and model/penalty SHA; separate counts from universal probabilistic claims.

No unreviewed coefficient rounding, norm implementation swap, OpenBLAS coretype pin, `NPY_DISABLE_CPU_FEATURES` switch, or historical retuning.

## 5. Provenance, storage, authorship

- Separate fast source/manifest/unit tests from deliberately triggered heavyweight scientific runs; avoid spending resources rerunning a 1,024-read study on every documentation-only commit. See [issue #34](https://github.com/carlers/quantum-opt-dashboard/issues/34).
- Record protocol *before* outcomes; preserve negative and positive runs and the explicit amendment history; archive raw files, run URLs, complete provenance, `SHA256SUMS` and checksums. **GitHub Actions is not a durable archive**, typically 14-day retention here.
- A private owner-held evidence ZIP and standalone SHA manifest were generated on **2026-10-19** from **26** downloaded CI ZIPs (64 inner files), **all outer and inner ZIP bytes verified**; this is **not a complete historical archive nor a public deposit**. Outer bundle SHA-256: `462add7e32375916957607b6f90f646fee046e73f21edd4818d3b8e1abadfdbc`. See [RESEARCH_EVIDENCE_INVENTORY_2026_10_19.md](RESEARCH_EVIDENCE_INVENTORY_2026_10_19.md). Owner retains the private downloadable copy supplied in the conversation.
- Raw GIS layers, expert questionnaires, LLDA data and manuscript may have different rights; do not post these to GitHub/Zenodo without author and data-rights review.

## 6. Decisions explicitly requested of owner/adviser

- [ ] Confirm the original data/notebook SHA and whether the unmerged N20 working derivative will become the **canonical analysis reference** (while always retaining historical original).
- [ ] Approve a meaningful **numerical tolerance criterion** (not just “1 ULP everywhere”), definition of physically meaningful effect and solver objective precision.
- [ ] Pick a preferred reproducibility tier R0, R1 or R2 for each publication table, experiment and notebook notebook pipeline.
- [ ] Decide whether any runtime pin/sensitivity study is warranted before the final water-quality paper, and whether environment features must be documented in an appendix.
- [ ] Resolve manuscript Table III–IV AHP, D2 source definition, N20 Table V SCIP energy, and all upstream third-party data rights in issue #16.
- [ ] Choose an approved durable archive destination and access policy before remaining CI artifact expiration.

**Next steps:** review these options in issue #64; select numerical equivalence gates with the adviser; separately preserve lawful raw data and reviewer-approved runtime manifests; only then authorize code/experiment changes. **No merge, deployment, or paper revision is implied.**
