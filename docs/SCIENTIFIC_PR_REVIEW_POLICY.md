# Scientific pull-request review policy — computational research, not ordinary feature CI

**Review-only policy proposal.** This repository contains an immutable historical Laguna de Bay water-quality placement source, separate classical/optimization methods, research UI, and several unmerged scientific branches. **A passing app unit test is not automatically evidence of scientific validity**. Use the default [GitHub PR template](../.github/PULL_REQUEST_TEMPLATE.md) to make the evidence type and limits explicit.

## Match evidence to the type of change

| Change | Minimal appropriate evidence | Not established by that evidence |
|---|---|---|
| Source custody / notebook archival | Exact original bytes and hashes, cell inventory, source origin/rights status, no uncontrolled rewrite | Correct science, author authenticity, license clearance |
| Objective, model or input data | Variables/index/units/CRS, source IDs, equation and constraints, independent small-case reference | Paper AHP or WorldPop parity without original published inputs |
| SCIP / compiled solver | Versioned emitted LP/MPS, coefficient and variable mappings, feasibility and objective decoder, status/gap | Global optimum unless proof status/verified bounds support it |
| Binary QUBO formulation | Offset, penalties, slack/aux variables, energy decode, all feasibility constraints and independent negative checks | Equivalence to historical JijModeling/OMMX, or quantum advantage |
| Classical SA / stochastic study | Seed plan, paired or independent repeats, reads/sweeps, per-trial failures, feasible rates, budget accounting and dispersion | Quantum hardware result, universal speedup, unbiased generalization from N20 |
| Notebook/plot/UI | Output-free code in Git, reproducible run path, input manifest, rendered values traceable to model and result IDs | New experimental evidence from a screenshot or mock map |
| OCI/storage/API/worker | Separately approved credentials/IAM and cost bounds, isolated smoke/recovery, independent off-machine restore where claimed | OCI deployment, disaster durability, or two-year enforcement from mocked CI |

## Source-controlled scientific evidence is layered

1. **Original source identity**: historical 25-cell notebook + GeoJSON SHA-256 are pinned; that proves known bytes, not publication/authorship rights. Original D2 is road proximity, whereas manuscript descriptions reference population/WorldPop exposure; notebook and manuscript AHP weights differ.
2. **Mathematical semantics**: document coordinates/CRS, selected-site indices, existing stations, K constraints, one-hop adjacency versus global wireless topology, objective source terms and numerical tolerance.
3. **Solver-input fidelity**: freeze emitted LP/QUBO with exact coefficients/offset and independent decode; avoid conflating an SCIP MIQP/MILP representation with historical JijModeling/OMMX QUBO.
4. **Numerical and experimental evidence**: status/gap, independent feasible-region certificate where tractable, stochastic replication design, seeds, problem tiers and environment CPU/BLAS/solver versions.
5. **Claims and retention**: clearly mark restricted N20/K5 results as local-source classical results, not broad manuscript parity, physical field validation or quantum advantage. Persist long-lived artifacts only after approved confidentiality, storage and rights review.

## Lightweight PRs are welcome

A narrow fast unit test, source fingerprint check, or documentation correction does **not** need an expensive SCIP run when the PR explicitly marks modeling/solver experiments N/A. Conversely, a mathematical change must not pass review by checking UI snapshots alone. Keep fast source/structural CI separate from expensive or probabilistic scientific acceptance runs; include the exact head commit and reproducible commands.

## Overlapping research branches

The [existing executable N20 notebook draft #56](https://github.com/carlers/quantum-opt-dashboard/pull/56) contains real N20/SCIP and exhaustive-combination checks. New [source-provenance draft #159](https://github.com/carlers/quantum-opt-dashboard/pull/159) is a **narrow independent fast source guard**, while [derived weight notebook draft #160](https://github.com/carlers/quantum-opt-dashboard/pull/160) is an **input-difference audit**, stacked on #159. Do **not** merge redundant reference notebooks or source-audit scripts without one reviewed canonical implementation. Other scientific PRs #155–157 form a separate private queue/API/evidence staging stack, not a release of the public product.

## Human-controlled gates

- Do not invent author lists, DOIs or software/data licenses. Record these as unresolved until the researcher and relevant data owner confirm them.
- Keep the original notebook/GeoJSON and live Streamlit pilot untouched unless the scoped owner approves a distinct change. Draft PR acceptance does not imply a merge.
- Owner confirmed **OCI PAYG, Option A private versioned backups, at least two-year retention, and $0/month incremental storage budget**. This precludes assuming a paid infrastructure pathway; no OCI apply, IAM expansion, active uploads, retention rule, or networking change is authorized.
- Confidential research evidence and credentials must never go into public GitHub PR attachments or CI logs. An independent object restore requires actual remote evidence and separately approved storage.
- Review original-source rights, student/adviser research question, licensing, and publication claims with humans before any formal release.

See [academic reproducibility survey](ACADEMIC_REPRODUCIBILITY_SURVEY.md), [notebook parity matrix](NOTEBOOK_DASHBOARD_PARITY_2026_10_26.md) and [umbrella roadmap #2](https://github.com/carlers/quantum-opt-dashboard/issues/2).
