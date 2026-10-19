# Scientific PR stack: reviewer and handoff sequence

**As observed 2026-10-19 UTC.** This is a review guide, not merge authorization. Branches and PR statuses can change; consult live GitHub before acting. `main` remains historical application/research scaffold, while the newer scientific reference is in **unmerged** review branches. User's **provisional MVP acceptance** is not permission to merge or change permanent preview/production.

## Dependencies before review

| Stream | Dependency order | What it establishes | What it does **not** establish |
| --- | --- | --- | --- |
| Maintained source N20 | [Draft #56 notebook source audit](https://github.com/carlers/quantum-opt-dashboard/pull/56) → [draft #57 source numeric manifests](https://github.com/carlers/quantum-opt-dashboard/pull/57) → [draft #61 free/fixed 300-pair trace](https://github.com/carlers/quantum-opt-dashboard/pull/61) → [draft #63 NumPy/OpenBLAS controlled runtime](https://github.com/carlers/quantum-opt-dashboard/pull/63) | Bounded original N20 source/provenance, SCIP/exhaustive optimum, observed 1-ULP arithmetic stages and fixed-operand runtime intervention | Full larger-N/published paper parity, universal CPU reproducibility, a sanctioned numerical fix |
| Historical OpenJij/QUBO | [Older historical controlled A/B penalty sensitivity draft #27](https://github.com/carlers/quantum-opt-dashboard/pull/27) → [draft #59 frozen exact historical B input](https://github.com/carlers/quantum-opt-dashboard/pull/59) | Controlled classical SA penalty-input difference and exact 46-bit frozen-B replay under observed hosts | Quantum hardware advantage or an automatically portable published QUBO |
| Data, manuscript and review policy | [Issue #16](https://github.com/carlers/quantum-opt-dashboard/issues/16), [issue #64](https://github.com/carlers/quantum-opt-dashboard/issues/64), **this independent documentation PR** | Source vs paper discrepancy audit, proposed tolerance/runtime tiers, private evidence custody metadata | Authorized paper correction, chosen scientific priorities, or new accepted runtime defaults |

**Key review ordering:** #56 first; inspect source-order and checksum canaries. Then #57 exact model input modes; #61 arithmetic trace; #63 fixed-input runtime configuration. Separately inspect #27 before #59 for the historical QUBO branch. Treat the independent source-paper discrepancy [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16) and numerical policy [#64](https://github.com/carlers/quantum-opt-dashboard/issues/64) as **human review decisions before declaring publication parity**.

## Updated live review snapshot after source verification forks

A fresh read-only GitHub PR-list query on **2026-10-19 UTC**, after PRs #66–#68 were opened, found **32 open PRs, all drafts**, still across **five** root families. The source-reference family rooted at [#56](https://github.com/carlers/quantum-opt-dashboard/pull/56) now contains **seven** PRs: source #56, precision #57→#61→#63, spatial #66→#67, and the combined validation candidate #68 (based on #63 and implementing the complementary spatial tests). The largest family overall remains **13**, and the deepest actual ancestry chain **11**. This is a live read-only count, **not a new run of the PR-stack auditor**; the earlier 29-PR snapshot below is retained as its historical CI evidence.

The concise human decision record is [N20_ADVISER_ACCEPTANCE_CHECKLIST.md](N20_ADVISER_ACCEPTANCE_CHECKLIST.md). Evidence in [combined draft PR #68](https://github.com/carlers/quantum-opt-dashboard/pull/68) can support a bounded source-derived N20 result, **but not a manuscript-parity or merge authorization**. The independent draft [#65](https://github.com/carlers/quantum-opt-dashboard/pull/65) carries the policy and the adviser checklist; no explicit signoff has been supplied.

**Next steps:** review #56 first, then inspect each sibling fork and the combined #68 candidate; obtain the owner's/adviser's B1–B6 scientific decisions and approved evidence custody. Merge/deploy only through a separate explicit authorization and refreshed CI/conflict check.

---

## Live PR dependency snapshot — 2026-10-19 UTC

A read-only [GitHub pull-list audit](https://github.com/carlers/quantum-opt-dashboard/pull/65) found **29 open PRs, all drafts**, partitioned into **five main-rooted review families**. The **largest family contains 13 related PRs**, but its deepest *actual ancestor chain* is **11 PRs**. These are different metrics; a branched family is not a single merge sequence. The new `scripts/audit_scientific_pr_stack.py` CLI and `.github/workflows/scientific-pr-stack-review.yml` compute a refreshed reviewer map without modifying branches, issues or PRs. Current listing has **no unrepresented-parent or ready-child-of-draft-parent warnings**. This structural result does **not** imply conflict-free merges or scientific correctness.

| Root PR against `main` | Live family size | Deepest PR lineage | Suggested review focus |
| --- | ---: | ---: | --- |
| [#56 — curated source N20](https://github.com/carlers/quantum-opt-dashboard/pull/56) | 4 | 4 | #56 → #57 → #61 → #63; source parity first, then numeric trace and runtime experiments |
| [#13 — original deployed-pilot branch](https://github.com/carlers/quantum-opt-dashboard/pull/13) | 13 | 11 | Historical #13→#14→#15→#17→#19→#21→#23→#25→#27; fork #27→#29→#35 (CI split), fork #27→#59 (exact frozen QUBO). Separate #13→#49 application release candidate |
| [#31 — evacuation/scientific platform](https://github.com/carlers/quantum-opt-dashboard/pull/31) | 8 | 8 | #31→#36→#39→#43→#44→#45→#46→#47; historical water and prospective evacuation science **not interchangeable** |
| [#51 — integrated MVP/UX](https://github.com/carlers/quantum-opt-dashboard/pull/51) | 3 | 3 | #51→#53→#55; UX is independent of publication scientific review |
| [#65 — independent numerical-policy/evidence handoff](https://github.com/carlers/quantum-opt-dashboard/pull/65) | 1 | 1 | Proposed criteria, original manuscript audit, private archive integrity and reviewer graph, no scientific model changes |

**Special CI note:** [draft PR #35](https://github.com/carlers/quantum-opt-dashboard/pull/35) already split fast Streamlit AppTest/SCIP correctness from long simulated-annealing evidence and empirically verified docs-only trigger filtering via its temporary #37 test PR. Its remaining issues are a complete lock/runtime policy, source review, and approved durable archiving; do **not** reimplement the existing split. The new reviewer-graph check on #65 is intentionally separate and cheap.

The preferred scientific review sequence is *parent-first, not “merge all 29”*: select the canonical N20 source and unresolved paper-data conventions with the research owner, review the independent exact/QUBO studies by protocol, and separately handle evacuation model and dashboard UX. Every prospective merge requires a fresh base/conflict and CI check plus explicit owner approval.

**Next steps:** inspect the latest generated PR-graph artifact, review #56 with the owner/adviser, decide source priority and numerical acceptance policy #64, and separately schedule only those high-value scientific merges that are approved. Do not merge/deploy any branch as part of this review snapshot.

---

## Review checklist

- [ ] Confirm archival `experiment9 grid search copy.ipynb` **unaltered** (pinned SHA), fixed committed source GeoJSON SHA, 15 true existing stations, N20 candidate order and K5 one-hop graph.
- [ ] Decide canonical reference branch for future analyses; keep original historical source and any mechanically de-duplicated derivative visibly distinct. A source-identical repeated notebook cell is **not automatically execution-equivalent** to deleting a second execution.
- [ ] Review objective and original feasibility against independent N20 exhaustively enumerated 15,504 selected subsets/1,077 feasible choices, actual SCIP solver result, original linear/quadratic coefficients and no spurious new model formulation.
- [ ] Separate original source-derived energy `−3.3012934918564643` from manuscript's `−3.301319` and Table III/IV/D2 issues; require original expert and optimization input provenance before any claim they are “reconciled.”
- [ ] Identify run/environment limits for 1–2e-16 IEEE754 differences; do not impose NumPy/OpenBLAS intervention as a default “fix” solely from six operand cases.
- [ ] Review historical source QUBO exact shape and offset (46 variables/323 nonzero terms) and fixed original read-seed manifest; classical SA never labeled hardware quantum advantage.
- [ ] Define [#64](https://github.com/carlers/quantum-opt-dashboard/issues/64) decision: choose numerical equivalence tolerance, runtime tier, full binary SHA requirements, independent sensitivity study and source manuscript disposition **with owner/adviser approval**.
- [ ] Choose approved private/institutional archival location and rights before remaining Action results expire; the user has an **owner-held**, not GitHub-committed, 26-artifact verification bundle.
- [ ] Only after independent approval plan the PR merge order, branch conflict handling, branch protections and any Streamlit deployment. No existing PR is merged by this guide.

## CI / repository operations

Scientific workflow [issue #34](https://github.com/carlers/quantum-opt-dashboard/issues/34) should separate **fast research logic/source tests** from **deliberately invoked heavy solver or sampled evidence**. The source scientific tests and NumPy/OpenBLAS controlled probes have already run in GitHub Actions on the individual unmerged PR heads; do not confuse green status of a documentation-only PR with a new scientific full-model validation. Requirements for an eventual release should be written as meaningful invariants, not just 0 missing test failures.

The current policy-and-archive verifier changes are **independent and documentation/stdlib-only** so reviewers can evaluate numerical criteria and evidence custody without inheriting or accidentally deploying the unmerged scientific code stacks.

**Next steps:** review this handoff, the evidence inventory and manuscript audit; obtain author/adviser decisions on inputs/tolerances/rights; then consider explicitly authorized merges or new bounded science tests. Preserve production, preview, and original source materials meanwhile.
