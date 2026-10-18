# Quantum Optimization Research Dashboard

**Status (2026-10-18): Active undergraduate computational-science research, not a validated generalized optimization or emergency-planning service.** This repository preserves earlier **Laguna de Bay water-quality sensor-placement** work and is building toward a transparent, reproducible classical/QUBO optimization workbench. **Evacuation-center siting** is a proposed second application, not yet a validated model or deployed tool.

## Start here

| Goal | Read / open |
|---|---|
| Project roadmap and numbered acceptance gates | [GitHub roadmap #2](https://github.com/carlers/quantum-opt-dashboard/issues/2) |
| Live water-quality experiment pilot | [Existing Streamlit app](https://v3wzqpbn8w6nmdgkxh5kum.streamlit.app/) and [operating issue #12](https://github.com/carlers/quantum-opt-dashboard/issues/12) |
| Original scientific reference | [Original notebook](problems/water_quality/notebooks/experiment9%20grid%20search%20copy.ipynb) and [Laguna de Bay source GeoJSON](problems/water_quality/data/LDB_centroids_clean.geojson) |
| Original experiment stages and known candidate bugs | [Notebook-to-module map](docs/NOTEBOOK_MAP.md) |
| New second-domain mathematical research proposal | [Evacuation center research spec](docs/EVACUATION_RESEARCH_SPEC.md) |
| Philippine data provenance, site capacity and hazard license gates | [Evacuation data audit](docs/EVACUATION_DATA_AUDIT.md) |
| Academic reproducibility standards and missing research infrastructure | [Reproducibility survey](docs/ACADEMIC_REPRODUCIBILITY_SURVEY.md) |
| Current GitHub audit/branch workflow context | [docs/SESSION_STATE.md](docs/SESSION_STATE.md) and [open pull requests](https://github.com/carlers/quantum-opt-dashboard/pulls) |

## Important branch boundaries

- **`main`:** source notebook and GeoJSON, documentation, and early framework/backend scaffolding. Not a complete working research system; several framework files remain placeholders.
- **`plugin-water-streamlit-pilot`:** separately deployed **live Streamlit pilot**. User reported the app working. Its simple SCIP experiment controls are NOT yet publication-paper validated.
- **Draft PR stack (#13 through #29):** independent N=20 SCIP reference/exact small-instance checks, solver-independent QUBO encoding, OpenJij **classical simulated annealing** repeats, numerical-precision investigations and a new **read-only MIQP/SCIP/QUBO Formulation Inspector**. These are not yet merged into `main` or the live Streamlit pilot. Check each PR's actual head and CI; do not treat a proposed draft feature as deployed.
- **Draft research PR for evacuation centers:** documentation only. No field-data ingestion, actual emergency-site capacity validation or new evacuation solver has been implemented. Adviser/user decisions and source rights remain gating.
- **Deployment:** Do not merge or push directly to the live Streamlit branch without user approval. Research can proceed in isolated branches/draft PRs with CI.

## Scientific purpose and boundaries

Current water-quality reference: select `K` new sensors from `N` free candidates, minimize a notebook-derived binary quadratic objective with exact budget and **local one-hop adjacency** constraints. Local adjacency does NOT imply a path from each selected station to a fixed station.

The live pilot runs **SCIP** through a binary pair-product MILP formulation. A separate explicit auxiliary-slack **QUBO** and classical OpenJij sampling are available in **unmerged research branches**. A QUBO does not mean a quantum computer was used. No quantum advantage or old-manuscript compiler parity has been established.

The new evacuation-center proposal is intentionally different: it requires people-demand, verified facility capacity, network travel and hazard eligibility, not water-quality utility/redundancy terms. It compares a potential-coverage baseline to a capacity-constrained, staged location/allocation model. The actual research question, area, hazard and data eligibility remain open. No research result should be treated as evacuation guidance.

### Key unresolved academic issues

- Original manuscript vs committed notebook AHP weights/criterion semantics and SCIP objective provenance: [issue #16](https://github.com/carlers/quantum-opt-dashboard/issues/16).
- Documented last-bit numerical penalty sensitivity: [issue #24](https://github.com/carlers/quantum-opt-dashboard/issues/24). The effect was isolated in a controlled classical sampler experiment, but the original source of floating-point differences is still under investigation.
- Second-domain site/capacity/hazard data rights: [issue #30](https://github.com/carlers/quantum-opt-dashboard/issues/30) and [issue #33](https://github.com/carlers/quantum-opt-dashboard/issues/33).
- Fast-vs-research CI and durable run artifacts beyond 14-day GitHub artifact retention: [issue #34](https://github.com/carlers/quantum-opt-dashboard/issues/34).

## Current repository structure

- `problems/water_quality/` — original GeoJSON, original notebook and early water-quality plugin scaffolding; preserve the source bytes.
- `framework/python/` — proposed reusable scientific workflow API and core; much is not yet implemented.
- `apps/worker/` — early worker scaffold, **not** a working remote job queue.
- `contracts/` — draft problem/experiment schemas.
- `docs/` — historical plans, research design and provenance documentation.
- `prototypes/streamlit_water_quality/` — Streamlit pilot and tested scientific branches, **only on non-main branches** at present.

## Running and reproducing work

The deployed Streamlit pilot is a manually deployed separate branch. To run that pilot locally, first explicitly check out `plugin-water-streamlit-pilot`, then follow its [own README](https://github.com/carlers/quantum-opt-dashboard/blob/plugin-water-streamlit-pilot/prototypes/streamlit_water_quality/README.md). Do not assume `main` contains that app.

Numerical SCIP/QUBO/OpenJij tests and input/result JSON/CSV checksums live on their actual scientific PR heads; find verified run IDs and actual artifact links in the corresponding GitHub issues/PRs. **GitHub Actions passing tests are not automatically a clean-environment paper replication**, and a temporary GitHub artifact is not a durable research deposit. Do not copy results into a thesis without confirming model/data/solver version and statistical design.

## Research integrity and contribution

We aim to meet relevant FAIR data/software/workflow principles ([Wilkinson et al. 2016](https://doi.org/10.1038/sdata.2016.18)) and software citation practices ([Smith et al. 2016](https://doi.org/10.7717/peerj-cs.86)). Authoritative data license/redistribution conditions, thesis adviser decisions, final CITATION.cff, and top-level code/data license **have not been finalized**. Access to a hazard website does not automatically authorize copying its underlying data.

**Contribute through scoped draft PRs and explicit evidence/acceptance checks.** Do not modify original notebook/GeoJSON or deploy changes implicitly. No publication-quality result, generalized domain portability, or emergency safety certification is claimed by this README.
