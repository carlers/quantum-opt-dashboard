# Academic computational-research repo survey and acceptance policy (draft)

**Scope:** 2026-10-18 research for [Phase 1 #3](https://github.com/carlers/quantum-opt-dashboard/issues/3) and umbrella [#2](https://github.com/carlers/quantum-opt-dashboard/issues/2). The repository is *not yet* validated as publication-grade. This is a source-linked recommendation, not an assertion that any journal/adviser requires a specific file or software stack.

## 1. Primary/specialist sources and what they actually recommend

- **FAIR Guiding Principles**: Wilkinson et al. (2016), *Scientific Data*, https://doi.org/10.1038/sdata.2016.18 . FAIR means findable, accessible, interoperable, reusable research objects with identifiers, metadata, licenses and provenance; the principles include **algorithms/tools/workflows**, not only underlying data. They are principles, not mandatory implementation standards.
- **Software Citation Principles**: Smith, Katz & Niemeyer et al. (2016), *PeerJ Computer Science*, https://doi.org/10.7717/peerj-cs.86 . Treat scientific software as a cited research object with identifiable/versioned authorship; recording exact solver/compiler versions matters alongside article citations.
- **The Turing Way — Reproducible Research**: https://book.the-turing-way.org/reproducible-research/reproducible-research/ . Explains reproducibility as making code/data available to re-run an analysis, with clear methodological/environmental documentation.
- **The Turing Way — Project Design**: https://book.the-turing-way.org/project-design/pd-overview/pd-overview-methods.html . Research methodology, collection and tooling should be designed before interpreting outcome results; sharing policy/license must match the actual objects.
- **The Turing Way reproducible-project-template**: https://github.com/the-turing-way/reproducible-project-template . Example project structure and README/citation/license guidance; illustrative rather than compulsory. The existing project's layout need **not** be replaced with the template's structure.

### What scientific verification adds beyond standard application CI

Ordinary application CI proves that a particular codebase imports, passes selected assertions and can be packaged/deployed. It does **not** by itself prove published objective terms, geospatial data interpretation, solver status, statistical independence, or paper-to-code parity.

The optimization thesis should test at least these distinct layers:
1. **Source evidence**: immutable original notebook, publication reference, dataset bytes+rights, stated mathematical problem and unresolved source discrepancies.
2. **Model semantics**: explicit indices, units, objective decomposition, constraints, feasible/invalid cases, and separate independent implementation/sanity checks.
3. **Compiled solver fidelity**: exact SCIP LP/MPS or QUBO coefficients/offset/slacks; mapping between human-readable equation and actual solver input; independent energy/feasibility decode.
4. **Statistical experimental design**: problem instances, seeds, predeclared endpoints, budgets, exact solvers' proof statuses vs stochastic sampling behavior; no cherry-picked run.
5. **Environment**: Python and binary solver versions, architecture/precision observations, dependency lock strategy, runtime limits, original raw inputs and transformation code revision.
6. **Artifact retention**: scripts that reproduce plots/tables and input manifest with canonical SHA/DOI or immutable release, not only short-lived CI artifact URLs.
7. **Scientific claims**: scope/uncertainties; one N20 classical SA benchmark cannot prove quantum advantage or cross-instance behavior.

## 2. Verified repo condition as of this research

- **GitHub main** is still the older scaffold with placeholder framework and separate original water-quality source data/notebook. All water-quality scientific tests/SCIP/QUBO/OpenJij implementation and the Streamlit formulation inspector are **unmerged draft branches**, not actually integrated into main.
- **Live Streamlit** pilot is already deployed on the separate `plugin-water-streamlit-pilot` branch, not production main. Do not merge or mutate without explicit approval.
- **Scientific CI on draft #29** previously passed 41 tests and generated independent SCIP/SA evidence; these are validations on a draft-stack head. This research PR is **docs-only and independently branched from main**; its own CI does not imply those tests are present on main.
- **Critical open provenance**: manuscript vs notebook AHP weights, D2 factor semantics, old JijModeling/OMMX QUBO compiler vs explicit new slack QUBO, and machine-level source float differences. See GitHub issue #16 and #24; later controlled replay isolated a one-ULP penalty sensitivity, not original floating-point source operation.
- **GitHub Actions artifact retention** is currently 14 days in scoped CI, insufficient as the sole archival medium for a final manuscript/thesis.

## 3. Prioritized research infrastructure changes (proposed, not yet implemented)

| Priority | Change | Scientific acceptance test |
|---|---|---|
| P0 | Review/merge plan for separate draft PR stack, with user approval and no accidental Streamlit production update | Human-reviewed architecture; branch differences and source refs recorded; no automatic merge |
| P0 | Independent `RESEARCH_SPEC` and dataset access/rights gate for each application | Mathematical equations, units, primary metrics, baseline solver, provenance matrix and unresolved assumptions are documented |
| P0 | Versioned artifact manifest and long-lived release/archive strategy | A clean-environment script can regenerate declared tables/results from licensed source or publicly distributable synthetic fixtures |
| P0 | Explicit fast-unit vs slow-integration/science CI separation | Fast suite < bounded reviewer target; solver/run probes in separate named workflow; no zero-test green builds |
| P1 | Scientific top-level README and CITATION.cff plus licenses/citation decision | Citation author/version/DOI checked; code and source-data redistribution rights separately reviewed |
| P1 | Python environment versions / dependency lock strategy per validated workflow | Fresh runner resolves exact version and confirms imported solver ABI; float-level parity or documented tolerance |
| P1 | Research-model inspector's derived equations and actual SCIP LP/QUBO exports | Data/model/solver input fingerprints agree and independent decoded solution verification passes |
| P2 | Pluggable domain interface **after** two mathematically validated domains | Water-quality and evacuation-center instances satisfy shared schema without hidden semantic losses |
| P2 | Custom web frontend, async job lifecycle, sweeps and resumability after an actual need | Staged functional tests demonstrate persisted jobs, checkpoints and audit export; not just API route placeholders |

**No single CI badge or passing stochastic run completes these gates.** A reasonable thesis minimum is a frozen research question, source dataset and license, mathematical model, certified exact baselines where tractable, statistically documented stochastic methods, clean-room reproduction, uncertainty analysis, and readable, accurate plots/claims.

## 4. Suggested future directory/artifact conventions (do not move source originals now)

- `problems/water_quality/notebooks/experiment9 grid search copy.ipynb` and committed GeoJSON remain **immutable original sources**.
- A new `problems/evacuation_centers/` domain may be created **only after an approved formulation and data rights assessment**, initially with artificial fixtures and no hidden externally sourced facilities.
- `docs/EVACUATION_RESEARCH_SPEC.md` and `docs/EVACUATION_DATA_AUDIT.md` contain domain-specific proposal/rights gates.
- Each approved model later gets a versioned, independently checkable objective/constraint specification and a schema/units/data dictionary.
- Each study run gets `protocol.json` + `source_manifest.json` + `environment.json` + `solver_input.lp|qubo.json` + `samples.csv` + `metrics.json` + `checksums.sha256`; do not claim this all exists yet.
- Release archive should contain reproduction instructions, declared sample/seed plan, failures and negative results. Source license restrictions can mean publishing only code/metadata/synthetic fixtures with access instructions, NOT prohibited raw copies.

## 5. Owner/adviser decision register (OPEN)

- Academic program/adviser evaluation rubric; whether thesis contribution should be **new problem formulation**, a **comparative algorithmic study**, a **research software platform**, or explicitly more than one.
- Geographic/hazard scope, scenario realism/ethics, genuine refuge-site permissions/capacities, evacuation fraction, cost/budget interpretation, and travel-mode/flooded-road treatment.
- License holder/author name information for citations and reuse of earlier student manuscript. Do not invent CITATION.cff names or paper publication equivalence.
- Whether a structured formula editor is essential before a two-domain validated static compiler; current read-only inspector proves a narrower value.
- Long-lived artifact location and storage budget; favor official Zenodo/OSF/GitHub release only when actual ownership and distribution rights are established.

This survey does **not** close Phase 1 issue #3: owner/adviser review, site/dataset approval, final thesis research question and archive policy are still needed. It does provide cited research/design material and a prioritized audit trail for the next planning decision.
