## Scientific change category

- [ ] Historical source/provenance only (no new experiment)
- [ ] Mathematical model, constraint, or data semantics
- [ ] Solver/compiler/quantum or classical algorithm
- [ ] Numerical/statistical experiment or benchmark
- [ ] Read-only research UI/results presentation
- [ ] Infrastructure, credentials, cloud, deployment or paid resource
- [ ] Documentation-only or mechanical refactor

**Specific scope / research question:** <!-- State what this PR demonstrates. Not every PR must run an experiment. -->

**Base and dependencies:** <!-- Main, preview or another draft branch? Link stacked PR(s), issues and upstream hashes. -->

## Scientific evidence and claims

- [ ] Identify original notebook, dataset version/sha256 and documented permission/rights status; mark unknown rights as *unverified* rather than assuming GitHub publication is a license.
- [ ] State the actual factor definitions, AHP weights, units, CRS/index mapping, original versus modified assumptions, and any unresolved manuscript discrepancy (or **N/A**, with explanation).
- [ ] Distinguish original mathematical objective and feasibility constraints from emitted SCIP MILP/LP, QUBO coefficients/offset, or stochastic sampler energies (or **N/A**).
- [ ] Record solver status and objective, independent feasibility/optimality evidence and tolerance/precision policy; do not label a feasible incumbent an exact optimum (or **N/A**).
- [ ] For stochastic experiments, preregister or report instances, seeds, reads/sweeps, repetition count, failure/infeasibility handling, budgets, variance and comparisons (or **N/A**).
- [ ] Declare unsupported claims: paper/WorldPop parity, global wireless connectivity, general multi-tier scaling, quantum hardware advantage, field validation, and external trust attestation (unless actually demonstrated).
- [ ] Name the **independent validator** or explain why this PR has only structural/unit/test coverage.
- [ ] Link a reproducible artifact/manifest or state that the output is *not* retained or independently restorable.

**What this PR does NOT prove:** <!-- Required. Explain if it is just docs, a source check, a UI smoke test, etc. -->

## Reproducibility and checks

**Exact source/model/evidence IDs (redact confidential metadata):**
<!-- Cite SHA/version/commit/manifest fields and where generated. Never paste private OCI keys, SSH material or confidential original research ZIPs. -->

**Environment and budgets:** <!-- Python, solver binary/ABI, CPU/BLAS, seeds, time/memory/storage if relevant; N/A for docs-only. -->

**Validation:** <!-- GitHub Actions run URLs / test counts / fresh-kernel run / independent LP replay. Never write "CI passed" without the exact run and head commit. -->

**Known failures or unresolved differences:** <!-- Keep open questions, numeric deltas, data license questions, negative experiments and limitations visible. -->

## Safe integration and owner approvals

- [ ] Preserve the original 25-cell Laguna de Bay notebook and original GeoJSON byte-for-byte unless explicitly reviewed as new data, not silently rewritten history.
- [ ] Do not conflate Streamlit pilot, permanent preview, `main`, and an unmerged draft-stack branch.
- [ ] No automatic merge or production deployment assumed.
- [ ] OCI PAYG research storage must stay within the owner's **$0/month** budget; no paid operations, Terraform apply, IAM expansion, object upload, WORM lock, or Mosaic changes without separate owner approval.
- [ ] No external/physical deployment, emergency decision support, or uncontrolled native-solver auto-retry from a simulated success.
- [ ] Update the scoped issue and umbrella roadmap with exact CI results and remaining gates.

**Required human review / blocking decisions:** <!-- If none, say none. In particular, scientific claim promotion and dataset rights require authorized review. -->
