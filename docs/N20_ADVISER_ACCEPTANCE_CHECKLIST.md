# N=20 scientific acceptance checklist — adviser review sheet

**Status: EVIDENCE READY FOR REVIEW; NO SCIENTIFIC OR MERGE APPROVAL RECORDED.**  
**Research scope:** source-derived *Laguna de Bay water-quality buoy placement*, 20 candidate new sites, exactly 5 selected, and 15 originally marked existing stations. **Not** a new evacuation-center formulation, published-manuscript replication, larger-N experiment, or quantum-hardware result.

**Recommended meeting duration:** 15–25 minutes. This sheet separates what the executed source and CI have demonstrated from what must be **decided and signed off** by the research owner/adviser. A checked computational test is **not** a checked author approval. Source interpretation remains subject to issues [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16), [#64](https://github.com/carlers/quantum-opt-dashboard/issues/64), and [#5](https://github.com/carlers/quantum-opt-dashboard/issues/5).

## A. Exactly what has been demonstrated — review evidence, not proposed changes

| Gate | Evidence currently available | Scientific scope or limitation |
| --- | --- | --- |
| **A1. Historical files preserved** | Original 25-cell archived notebook SHA-256 `08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048`; committed 5,417-point source GeoJSON SHA-256 `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`. Original source files untouched in the reviewed draft. [PR #56](https://github.com/carlers/quantum-opt-dashboard/pull/56) | Proves provenance of the committed inputs, **not** how third-party GIS layers or expert questionnaires were originally prepared |
| **A2. Model definition** | 20 free candidates, **15 actual flagged** existing stations; exact K=5; eight source-notebook factor weights and `D2=d2_road_proximity`; original local **one-hop** conditions and **12 nonzero free/free quadratic objective interactions**. [Reference policy](https://github.com/carlers/quantum-opt-dashboard/blob/science-source-notebook-audit/docs/SCIENTIFIC_REFERENCE_POLICY.md) | The **12 objective interactions are not the 11 spatial adjacency edges**. Local one-hop is not global network connectivity |
| **A3. Complete small-instance optimum** | Source-derived SCIP `optimal`; selected local indices **`[0,1,3,6,7]`** (original GeoJSON master feature positions `[5253,2394,1557,47,5409]`); raw original objective about **`−3.3012934918564643`**. Independent `C(20,5)=15,504` enumeration, of which **1,077 are locally feasible**. [PR #66](https://github.com/carlers/quantum-opt-dashboard/pull/66) | Certified **on these source-derived inputs**; does not validate the manuscript's separate SCIP `−3.301319` |
| **A4. Reconstructed spatial feasibility** | Independently reread the original GeoJSON and derived the source-specified concave hull (ratio 0.05, holes permitted), fixed-site spacing buffer 1.15, and all **490** free/free or free/fixed pair candidates: **114** strict hull-interior segments; **45** meet Dmax (11 free/free + 34 free/fixed). Feasible-set SHA-256 `2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a`; nearest tested distance to Dmax ≈**25.73 metres**. [PR #67](https://github.com/carlers/quantum-opt-dashboard/pull/67), [fresh source/spatial CI](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39192139080) | Independent graph construction from committed points, **but the same Shapely/GEOS concave-hull model**, not an independent shoreline/hydrology survey |
| **A5. Joint precision and spatial robustness** | Combined [draft PR #68](https://github.com/carlers/quantum-opt-dashboard/pull/68) ran **six actual fresh source notebooks** over three CI hosts; two exact model-input `float.hex` SHA modes and **20/300** free/existing pair arithmetic records differed in their low bits. All six retained **one identical exact graph SHA** `148d4d276b61305cd969d426afacd3c81634486818deca816014d67cef7908ae`, identical **1,077 feasible sets** and source optimum within the prior regression canary. [Exact-head precision CI](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39192139090) | Demonstrates bounded cross-host numerical **scientific outcome** stability in this sample, **not** universal binary reproducibility, an accepted tolerance policy or invariance of historical stochastic simulated-annealing trajectories |
| **A6. No undeclared scientific conversion** | No fixed station fallback of 3, no rewritten original GeoJSON/notebook, no replaced AHP/D2 meaning, no retuned QUBO penalties, no automatic BLAS/NumPy override or source-paper objective correction in the combined integration candidate | The clean reference and all dependent study branches remain **draft/unmerged** |

**Live evidence provenance, independently checked on 2026-10-19 UTC:** [CI #39192139080](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39192139080) and [#39192139090](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39192139090) both **completed successfully at identical exact head `29397a69d8e45dab2cf2f635b6adfdc2196f37d9`** of draft PR #68. Geometry audit passed 10 source/feasibility plus 11 geospatial adversarial tests, one fresh notebook/SCIP replay; precision audit passed 8 comparison, 7 pair-stage and 10 joint spatial tests with six independently executed notebooks. This is **46 tests across multiple suites and seven real notebook executions**, **not** 46 independent scientific experiments. The two precision numeric modes in this particular run were recorded without masking or correcting their differences.

[Geometry certificate artifact #12159589226](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39192139080/artifacts/12159589226), [exact source model record #12159379845](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39192139080/artifacts/12159379845), and [six-process comparison artifact #12159414693](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39192139090/artifacts/12159414693) expire **2026-11-02 UTC** under current CI retention. Evidence links and repository metadata alone do **not** constitute durable custody. Archive permission and destination remain undecided ([#34](https://github.com/carlers/quantum-opt-dashboard/issues/34)).

**Private evidence custody update (2026-10-19):** In addition to the earlier 26-ZIP historical archive, a **new separate** 15-original-ZIP / 37-file integrated N20 archival bundle was prepared, complete with original run/artifact links and outer SHA `7463332681fafc26ee441c9456251e89059722844ba26a548bb4cb20808879c9`. The research owner must **download and store both** in an approved private/institutional location. Conversation delivery is **not** permanent custody or public-release approval. See [updated evidence inventory](RESEARCH_EVIDENCE_INVENTORY_2026_10_19.md).

**Critical provisional scientific review (not a sign-off):** [N20_PROVISIONAL_ADVISER_REVIEW_2026_10_19.md](N20_PROVISIONAL_ADVISER_REVIEW_2026_10_19.md) challenges the *model assumptions*, rather than just reproducing old source code. It documents **7 of 20 candidate nodes impossible to choose**, the winning five new nodes occupying **four new-only connected components**, an east–west symmetric “directional wake” implementation, an N=50 paper penalty-table arithmetic discrepancy, and the difference between source optima and scientifically valid GIS/hydrodynamic decisions. These are reviewer findings and posthoc sensitivity calculations, **not** approved model corrections. Read them before signing B1–B4.

## B. Decisions for the adviser — leave unchecked until explicitly approved

- [ ] **B1 — Source authority.** Approve the **notebook-derived N=20/K=5 case only** as the working computational reference, while preserving the original source notebook and GeoJSON with their exact checksums. If not approved, identify the specific disputed assumptions/inputs.
- [ ] **B2 — Geometry and adjacency scope.** Confirm the source concave hull, strict interior segment rule, 1.15 fixed-spacing buffer and local one-hop constraints are scientifically suitable **for this buoy placement study**. State explicitly whether a separate validated shoreline/hydrology dataset is required before publication.
- [ ] **B3 — Numerical equivalence policy.** Choose and justify an objective/coefficient tolerance independently of observed 1-ULP drift. The existing `1e-7` objective regression check is an **unapproved software canary**, not a research tolerance. Select the required environment tier **R0 / R1 / R2** in [policy draft #64](https://github.com/carlers/quantum-opt-dashboard/issues/64), including which experiments or paper tables need full wheel/binary fingerprints.
- [ ] **B4 — Manuscript disposition.** Resolve—or explicitly keep **unresolved and disclose**—Table III-versus-IV AHP priorities, notebook factor **`d2_road_proximity`** versus paper's population/WorldPop D2, and paper N20 SCIP **`−3.301319`** versus source-derived **`−3.3012934918564643`**. Obtain original elicitation, D2 data processing and published SCIP coefficient/offset files before claiming published-paper reproduction. [Issue #16](https://github.com/carlers/quantum-opt-dashboard/issues/16) and [source manuscript audit](MANUSCRIPT_NOTEBOOK_PROVENANCE_AUDIT.md).
- [ ] **B5 — Research claims and thesis separation.** Approve language that says **“validated notebook-derived N20 buoy-placement computation”**, not “replicated the paper exactly” or “quantum advantage.” Historical OpenJij `SASampler` is **classical SA**, not QPU execution. The proposed evacuation-center project requires its **own data, geospatial/accessibility model, constraints and experimental plan**.
- [ ] **B6 — Data rights and evidence custody.** Assign an approved **private/institutional long-term location** for raw numerical/geometry evidence and provenance manifest before short-lived CI artifacts expire. Determine legal/licensing and human-data restrictions before any public GitHub/Zenodo release; retain negative as well as positive CI evidence.
- [ ] **B7 — Integration/merge authorization, separately.** If B1–B6 are satisfied to the team's standard, choose the reference PR integration order and approved branch-review route; check conflicts and **fresh post-integration CI**. This checkbox is **not** permission to merge any PR, modify `main`, alter the Streamlit app, or deploy. Request a separate explicit action for each.

### Reviewer decision record — completed by humans, not generated by CI

**Research artefact / version reviewed:** PR #68, head `29397a69d8e45dab2cf2f635b6adfdc2196f37d9` (or replace with later reviewed commit: ______).

**Decision for the *source-derived N20/K5 computational reference* (choose one):**

- [ ] **Accept for explicitly bounded computational work**, with unresolved manuscript provenance disclosed and no implication of deployment/publication equivalence.
- [ ] **Conditionally accept**, provided the following specifically enumerated items are addressed: _______________________________________________.
- [ ] **Defer / reject** until the following evidence is supplied: _______________________________________________.

**Objective acceptance tolerance / rationale:** _______________________________________________.

**Environment tier and reproducibility requirements (R0 / R1 / R2):** _______________________________________________.

**Paper Table III/IV/D2/SCIP discrepancy disposition and required originals:** _______________________________________________.

**Geometry/hydrology and input-data provenance decision:** _______________________________________________.

**Evidence preservation destination, access conditions and responsible custodian:** _______________________________________________.

**Scientific reviewer/adviser name, date, and recorded approval reference:** _______________________________________________.

**Research owner confirmation/date:** _______________________________________________.

**Merge/deploy authorization:** **NOT INCLUDED.** Requires a separate explicit owner-approved GitHub action after checking current branches, dependencies and CI. The record above is an **unsigned template** until humans fill it out and approve.

## C. How to use this sheet

1. Open the exact run links and `docs/N20_INTEGRATED_SCIENCE_VALIDATION.md` in [draft PR #68](https://github.com/carlers/quantum-opt-dashboard/pull/68); independently inspect the original source/notebook hash and spatial manifest.
2. Discuss the seven decisions above. Record the chosen scope, numerical and geometry assumptions, missing source records, and explicit caveats; **do not infer approval from existing CI or an assistant comment**.
3. Store a signed/approved decision in the team's appropriately access-controlled records and link a non-sensitive decision summary to [#5](https://github.com/carlers/quantum-opt-dashboard/issues/5), [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16), [#64](https://github.com/carlers/quantum-opt-dashboard/issues/64), and the [roadmap #2](https://github.com/carlers/quantum-opt-dashboard/issues/2). The user determines what may be made public.

**Next steps:** send this sheet to the adviser; obtain B1–B6 decisions; archive numerical evidence under approved rights; plan a separate explicitly authorized dependency-aware scientific PR review and merge; continue evacuation research with an independent domain specification rather than importing the buoy source model unchanged.
