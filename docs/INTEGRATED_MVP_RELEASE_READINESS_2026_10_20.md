# Phase 1 consolidation: unified research MVP and scientifically honest release gate

**Date:** 2026-10-20  
**Status:** review-only candidate, not deployment or merge authorization.  
**Parent issue:** [#50](https://github.com/carlers/quantum-opt-dashboard/issues/50); downstream scientific UX [#88](https://github.com/carlers/quantum-opt-dashboard/issues/88), real solver evidence [#91](https://github.com/carlers/quantum-opt-dashboard/issues/91), data inputs [#87](https://github.com/carlers/quantum-opt-dashboard/issues/87). This is an integration acceptance plan, **not** an original manuscript amendment.

## What the GitHub ancestry audit actually shows

The **unified Streamlit MVP** [DRAFT PR #51](https://github.com/carlers/quantum-opt-dashboard/pull/51), commit `b9b24aa6e794d0f9bb222a4192bce1fa0ee4b8ed`, **is an ancestor of the current water UX / verified-output stack** [DRAFT PR #101](https://github.com/carlers/quantum-opt-dashboard/pull/101), commit `e5c56bb19f0cc5800af20649088b7c39f02c4715`. The GitHub commit comparison reported **ahead 103, behind 0**, with the exact merge base equal to #51 HEAD. These are NOT two histories that must be separately recombined. The 103 commits encompass UX, data visibility, graph/SCIP checks, dedicated tests and research documentation. The current UX ancestry already contains:

- A single `prototypes/unified_dashboard/app.py` entrypoint routing **Water-quality placement**, **Configure another problem**, **QUBO and classical SA**, and **About the research**.
- The original notebook-derived 15-fixed/20-free/K5 source and actual SCIP local solver, GIS site map, model/LP/evidence exports, and a second modeled **all-15-mandatory-fixed globally connected** geometric search mode. Both models share objective function identity only where coefficients actually match; connectivity is a distinct constraint.
- Configurable user-editable small synthetic math models and safe QUBO/SA inspection. OpenJij is **classical** SA; synthetic evacuation is **not** a real emergency action tool.
- Per-run original source/solver mathematical/result/LP/export verification in the live UX draft, plus separately runnable unsigned second-process/nonce research prototypes. The latter are **not** a signed service or automatically added to the interactive per-user app solve path.

By contrast, scientific [DRAFT PR #96](https://github.com/carlers/quantum-opt-dashboard/pull/96) is on a **diverged** ancestry from the integrated MVP. At the #51→#96 GitHub comparison, the branches were **ahead 150, behind 246**, with the original common `main` base. This separate scientific history has genuinely cold, pinned original N20 real-SCIP notebook replay, independent raw 5,417-point source GeoJSON / full all-15-fixed graph, S4 factor/AHP claims and provenance, numerical cross-host precision experiments, and read-only source/UI comparison tools. **Do not resolve the divergence by a blind merge, cherry-pick, copied notebook, or replacing the current source compiler.**

The already-tested `.github/workflows/ux-n20-runtime-vs-science.yml` is the correct current **non-merging compatibility seam**: it checks out current UX, pinned original backend UX #78 (`8752d17372d9d4dd544acbbfd686b4bb45e33f40`) and original-science source #96 (`093941793b91ecef46c31dad72898da66bf638ac`) independently. It verifies identical original model compiler/geometry implementation, original cold N20 source notebook and GIS/S4, and independently matches the active 35-node graph and exact source coefficient identities. Those comparison results remain CI-produced bounded short-retention artifacts, not automatically authoritative model-data fields or independently trusted signatures.

## Release architecture: preserve a single deployable UI without overmerging research

**Canonical preview-oriented research MVP candidate:** current draft UX head descended from #51, with one Streamlit entry point. Maintain separated standalone experimental CLI programs/workflows and the original archived research sources; do not gate every interactive run on the expensive independent notebook/science replays. **Scientific claim checks** should continue as an independent required CI job, and user-visible source/experimental/paper/physical evidence labels must be deterministic, truthful and tested.

The About-page improvement in this review-only branch introduces explicit, non-interchangeable scientific claims:

| Evidence level | Current acceptance | What it specifically does NOT establish |
| --- | --- | --- |
| Original notebook computation | **Mathematically verified for the pinned 20-free/K5 local source**, 1,077 feasible / 15,504 combinations, winner [0,1,3,6,7] | The published paper's original AHP, GIS layers, D2/population factor, and empirical monitoring performance |
| New all-15-fixed global wireless graph | **Exploratory mathematical/geometry proof**, 860 feasible / 15,504 for a fully connected modeled 35-node graph | Actual RF/backhaul links, surveyed shoreline or antenna reliability |
| Manuscript and historic AHP/GIS provenance | **NOT RECONCILED**; source D2 means road proximity, paper mentions WorldPop/population | Published-text-input parity or reconstructed original expert matrices |
| Physical environmental/telemetry effectiveness | **NOT VALIDATED** | Measured received signal strength, packet-loss, current/DO detection, field maintenance or operational lake station recommendations |
| Quantum/QUBO research | **Classical OpenJij SA demonstration only** | Quantum processor access, quantum advantage or universal constrained QUBO/MIQP support |
| Detached N20 checker | **Unsigned mathematical review demonstration** requiring out-of-envelope nonce and source reference | Independent endorsed reference custodian, nonce replay ledger, first-SCIP process authenticity, protected signing service or field/paper proof |

The alternate cross-run observed original scored-objective SHA forms (`2b238848...` versus `8536a3db...`) are **different exact binary64 model identities**; neither permits cache interchange or paper-quality inferences from a raw negative energy. CI must preserve exact source/coefficient fingerprints, not quietly introduce post-hoc floating tolerances as authority.

## Incremental release sequence and objective exit criteria

### Gate A — unified research MVP scientific labels (this DRAFT)

- [ ] The unified Streamlit **About** route renders original source, exploratory global geometry, manuscript and physical claims separately; no ambiguous single green “validated” statement.
- [ ] Actual `AppTest` confirms all four claim distinctions, correct original/free/fixed/K count and the important D2 road-vs-WorldPop mismatch, and that About navigation executes **no solvers**.
- [ ] Full pilot and unified editor/navigation regression pass at **exact final DRAFT HEAD**, plus genuinely cold original source/UX isolated-checkout CI.
- [ ] `docs/SESSION_STATE.md` points to concrete tested HEAD and next owner decision. No source manuscript/notebook/GeoJSON edit, no main/preview/prod push.

### Gate B — consolidate maintainable release surface (next scoped DRAFT, after human review)

- [ ] Map active entrypoint/module responsibilities. Keep one canonical unified launch path, preserve standalone water/configurable regression CLI, and keep scientific read-only verifier scripts in separate research modules.
- [ ] Replace duplicate/obsolete handoff references with links to one current roadmap + source/material claims. Existing completed PRs stay discoverable; historical evidence immutable.
- [ ] Audit runtime package pins, cached result invalidation, session concurrency, unsafe upload limitations and actual downloadable JSON/LP/ZIP against a precise release manifest; bound Cloud CPU/memory and solve times.
- [ ] Formal review of **independent science #96**: decide whether any pure claim-state adapter or provenance schema should be imported into the deployed code versus remaining isolated as a required CI cross-check. Any actual cross-ancestry integration requires a separate, explicitly reviewed draft merge plan and exact-head tests. Never infer reviewer acceptance from green CI alone.

### Gate C — owner-reviewed staging

- [ ] Human review of the integration DAG and current source/UX/paper claim boundaries.
- [ ] Explicit owner permission to update the **existing persistent preview** branch and Streamlit Cloud app, never a disposable per-PR deployment. Preview: `https://quantum-opt-dashboard-55zt76rpzbn2n3dltqfgis.streamlit.app/` (owner supplied, **live end-to-end runtime not yet independently checked**). Production: `https://v3wzqpbn8w6nmdgkxh5kum.streamlit.app/` (separately deployed branch, unchanged).
- [ ] Manually inspect all four Streamlit pages, local and global optimization and failure statuses, uploads, full evidence exports, classical OpenJij resource limits and browser/mobile interactions with actual Cloud Python 3.12.
- [ ] Explicit separately reviewed merge to `main`, then separately approved production branch change only after sufficient preview evidence; CI green does not authorize either.

### Parallel gate D — credible scientific inputs and broader paper experiments

- [ ] Acquire original raw expert AHP elicitation matrices/weights and the paper's QGIS/WorldPop D2 inputs (with reuse licenses), source transformations and station IDs, or explicitly declare the manuscript not independently reproducible.
- [ ] Obtain authoritative LLDA waterbody/station positions and physically test radio/topology, DO/current transport and sensor-site usefulness before a field-deployment decision-support claim.
- [ ] Preregister and execute the larger N20–N2000 SCIP/greedy/SA benchmark and sensitivity families only after source identities, numerical policy and computational budget are declared; distinguish classical SA from hardware.
- [ ] Review custody and archive expiry for original cold experiment ZIP/JSON, independent report hash, dataset version, environment and licensing. Short-term GitHub CI artifact retention is not long-term academic provenance.

**Next decision requested of the owner:** accept this canonical ancestry strategy (UX child of integrated MVP #51, source #96 external pinned verifier), then authorize a review-only Gate B implementation. Source provenance/physical validation and any signed-run infrastructure remain independent decisions—not automatic blockers to an appropriately labeled academic research MVP.
