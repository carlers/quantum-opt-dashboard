# Academic research repository conventions — applied M0/M4 checklist

This is a **concrete research-software checklist**, not an assertion that GitHub code review or standard app deployment proves scientific validity. The linked reference materials are external guidance; all specific N20/N50/N100 findings below originate from the repository's source/tests/CI, not from those references.

## Outside research-software guidance reviewed 2026-10-26

- **FAIR for research software:** Barker et al., *Introducing the FAIR Principles for research software*, *Scientific Data* **9**, 622 (2022), https://www.nature.com/articles/s41597-022-01710-x. Applied here: findability, clear source software identities, separated interoperable manifests, licenses/provenance, and reuse boundaries. FAIR principles are **not** evidence that this implementation is FAIR compliant or that field results are true.
- **The Turing Way, Reproducible Environments:** https://book.the-turing-way.org/reproducible-research/renv/ ; *Research Data Management*: https://book.the-turing-way.org/reproducible-research/rdm/ . Applied here: capture OS/Python/NumPy/SciPy/PySCIPOpt/OpenJij/BLAS versions, seeds, exact source-data hashes and execution constraints, and preserve all raw data and regenerating analysis code.
- **RO-Crate research-object package:** https://www.researchobject.org/ro-crate/specification ; research-object metadata should link people, code, raw inputs, derived data and provenance. The current specification page lists RO-Crate **1.3** as released. **Do not** create a fictitious crate identifier or claim compliance before validating the actual machine-readable metadata and third-party redistribution licenses.
- **CodeMeta user guide:** https://codemeta.github.io/user-guide/ ; `codemeta.json` helps discovery and software citation. A complete file should reflect reviewed software identity, version, development status, authors, licensing, and publication link. **Do not** invent authors, licenses, versioned releases or DOIs from a username or uploaded paper.
- **The Turing Way reproducible research guide:** https://book.the-turing-way.org/reproducible-research/reproducible-research/ ; the guide explicitly distinguishes providing rerunnable data/code from merely sharing screenshots.

## Research-science vs web-software CI

**Engineering gate:** build, lint/imports, unit tests, UI browser coverage, privacy and configuration, deployment smoke. Necessary but not sufficient. The user-facing dashboard is **read-only for costly experiments**; no unreviewed N100 stochastic benchmark on every Streamlit rerun.

**Scientific input gate:** exact GeoJSON bytes, original notebook Git blob, factor semantics, feature identities, numeric coordinate system, frozen source/derived coefficients and graph. Do not silently replace a road-proximity D2 source with a manuscript-described population factor. Keep historical model variants separate.

**Scientific formulation gate:** original bounded K/source objective vs augmented auxiliary-slack QUBO, different connectivity definitions, solver incumbent/gap/optimality status, fixed-station rules, global-vs-local comparison, independent LP/HiGHS verification. Include negative tests for false results and infeasible selections.

**Scientific experiment gate:** manifest a single immutable run plan with parent/child seeds, read count, sweeps, pairwise penalties, experimental error handling and independent blocks; execute and record all trials, including failures. Set explicit CPU/memory/wall limits. Encode float64 source coefficients exactly (hex string), not just 7-decimal tables. Two identical seeded replays are not added to the inferential sample count.

**Statistical gate:** predefine endpoints, multiplicity corrections, bootstrap resampling unit, time-budget effects, missingness and stopping rules before drawing confirmatory data. Descriptive 72-draw pilot heatmaps require a prominent limitation label. A benchmark plot must disclose cold construction, preprocessing, solver call, LP export, artifact serialization and total worker wall separately.

**Publication/archival gate:** exact code release/tag SHA, complete raw input source and license checks, raw output+infeasible samples, solver LPs, checksummed manifests, independent verifier receipt, versioned figures/scripts, limitations and citation metadata. GitHub Actions' 14-day short-retention archive is **temporary**; provide a curator-approved long-term repository/DOI only after rights and metadata are checked. Ensure archive can be reproduced offline without a living Streamlit deployment.

## Applied change set

- `problems/water_quality/scientific_claim_registry.json` is an **unreleased draft** machine-readable ledger of original input identity, research support statuses and claims explicitly **not** currently warranted.
- `docs/M0_SOURCE_CLAIM_REGISTRY.md` is the human-readable interpretation and discrepancy policy.
- M0 CI checks original source bytes and source-derived N20 witness, all 15 marked fixed stations, true distinction between local and global counterfactual counts, paper-vs-source D2 difference and no fraudulent public-archive/quantum/field/scaling claim.
- Existing M1–M3 PRs remain separately scoped, review-only and unmerged. Original research notebook and GeoJSON remain untouched.

## Remaining owner/reviewer decisions, intentionally unfilled

1. Who is authorized to represent the academic paper as its author/corresponding author and to approve changes to its manuscript claims?
2. Can the original GeoJSON, its property factors, the manuscript file and full experiment records be redistributed under known licenses/permissions? A public repository is not a blanket license.
3. Which curated science archive is appropriate (institutional repository, Zenodo, OSF or other institution-approved destination), what retention/licensing restrictions apply, and who will create the persistent DOI?
4. Which research question is authoritative for publication: reproducibility of **notebook source** or reconciliation of **manuscript AHP/WorldPop D2**? These are separate models until reviewed.
5. What preregistered compute/statistical protocol is approved (see [#146](https://github.com/carlers/quantum-opt-dashboard/issues/146))?

Until these decisions are made: **no paper parity assertion, public archive deposit, new scientific release metadata, long preregistered batch execution, deployment or merge**.
