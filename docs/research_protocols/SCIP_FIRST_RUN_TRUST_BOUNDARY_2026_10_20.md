# Trust-boundary review: first SCIP run and independent replay

**2026-10-20 · Review-only mathematical and security research.** Separate draft stacked on [DRAFT #99](https://github.com/carlers/quantum-opt-dashboard/pull/99), not on `main`. Original scientific source [DRAFT #96](https://github.com/carlers/quantum-opt-dashboard/pull/96), UX [#78](https://github.com/carlers/quantum-opt-dashboard/pull/78), actual app mathematical gate [#97](https://github.com/carlers/quantum-opt-dashboard/pull/97) and LP parser [#98](https://github.com/carlers/quantum-opt-dashboard/pull/98) remain unmerged. No source notebook, archived Laguna de Bay GeoJSON, manuscript, Streamlit app, deployment or research criterion change.

## Audit finding: first-process selection score is not first-process feasibility

The #99 source/LP replay review independently checks all SCIP LP constraints, models the original N20 source local feasible subsets, and compares both SCIP selection scores to the exact rational optimum. However, until this follow-up, it explicitly recomputed the *second* worker's N20 source one-hop connectivity but **did not independently recompute the FIRST solver's selected vector's one-hop connectivity**. Its first vector was checked for shape/binary/K and exact binary64 optimum score only.

For a constructed **flat zero objective on the actual original lake candidate/fixed adjacency**, all 1,077 feasible K5 combinations and the 14,427 infeasible K5 combinations have exactly equal energy zero. A counterfeit FIRST selection with valid K5 but disconnected selected site(s) could therefore be promoted to an optimal-first-process receipt by supplying a valid second SCIP observation, despite the previous textual LP being structurally valid. **Equal exact score is necessary but not sufficient** for feasible optimality; a valid optimum must satisfy BOTH admissibility and energy constraints. This is a model-logic error, not evidence that a compromised solver has been observed in normal CI.

`scip_lp_reexecution._source_local_feasible()` now independently enforces the original historical source local one-hop rule for **both** first and second process selected K5 vectors after binary/K checks and before rational score/LP bounds. It explicitly rejects an upstream disconnected exact-score tie, and a forged child disconnected tie, even if a record claims `optimal`. The normalized receipt includes both boolean independent graph-feasibility checks.

A related gap allowed contradictory FIRST SCIP metadata (e.g., `optimal=True` but `gap=0.5`, `gap=NaN`, `feasible=False`, `budget_ok=False`, `connectivity_ok=False`, `num_selected` different from K or nonempty `isolated`) to be asserted while still accepting the independent child SCIP `optimal` observation. This follow-up validates these recorded first-process fields and requires a finite nonnegative converged `gap <= 10^-6` **in addition to** independent K, graph, LP structure and source exact objective checks. No numeric score-tolerance permits a rationally worse selected optimum. The global full-15-fixed scenario remains **exact enumeration, not SCIP**.

## Distinct threat assumptions and what is controlled

| Threat or failure | Evidence currently mitigating it | Still NOT established |
|---|---|---|
| Stale/replayed UI model, selected site, displayed score/CSV, ZIP | Current compile SHA, recomputed UI audit, actual ZIP byte/SHA/CSV and independent N20 math before result display (UX draft #97) | A malicious actor controlling *all* server-side state could forge SHA and result together |
| Wrong source local budget, one-hop constraints, product linearization, binary domains or LP printed score | Independent bounded CPLEX LP structural parser of original SCIP LP (draft #98) | The LP was necessarily the one executed by an arbitrarily compromised first SCIP process |
| False optimality, infeasible first/second selection with exact equal score, forged first-status flags | Exact binary64 rational enumeration, independent **both-process feasibility**, bounded primal/dual gap, negative flat-score/adversarial tests (this draft) | Portable independent branch-and-bound dual proof or replay of the first optimization search tree |
| Original LP process confusion | Fresh child Python `-I` calling SCIP `readProblem` and `optimize` with same LP digest (draft #99) | Authenticated first-process identity, OS/host binary integrity or remote CPU attestation |
| Low-ULP original source objective drift across CPU runtimes | Strict `float.hex` coefficient SHA variants, direct-source/UX objective byte contract and independent formula enumeration | Bitwise deterministic compilation across vendor/BLAS/libm; different SHA variants never share strict cache keys |
| Compromised app host / GitHub CI worker, Python libs, malicious or replaced binary | Current GitHub workflow source ref and library versions; read-only tests and 14-day artifacts | Trusted immutable supply chain, independent trusted execution root or signed third-party solver evidence |
| Radio/backhaul/monitoring and published AHP/D2/WorldPop | Original source computational checks with separate manuscript and physical claim gates | Measured lake RF, shore/waterbody, current/DO field sampling, or original author AHP sheets |

**All SHA-256 hashes in these research branches are content-integrity fingerprints, NOT signatures.** Local files and a local subprocess share a host security boundary. Recomputing a checksum or placing a signer key in that same writable host does not authenticate a solver that the host operator controls.

## Recommended next architecture — proposal only, NOT implemented or authorized for production

A release-grade independent trust boundary would require a **separately governed signer/verifier** rather than only a subprocess:

1. Give each request a server-issued unpredictable run ID/nonce with expiry and one-time binding to the normalized input manifest. Include complete source dataset SHA, exact `float.hex` objective coeffs, all original candidate/fixed identities, K, Dmax and local/global topology, exported LP SHA (local-only), solver worker git SHA, package/SCIP binary/build digests, and numerical runtime platform.
2. Route compilation and solution to an isolated resource-limited execution service whose own current model and solver outputs are witnessed by a verifier **outside the app**. Record raw emitted LP, actual process launch arguments/binary hash, first-run SCIP status, feasible incumbent vector, primal/dual bounds and gap, exit code, standard output/error digest, and intended output ZIP checksums as immutable per-run evidence. For original bounded N20, recompute the mathematical optimum and enforce every local constraint independently.
3. If a signature is warranted, the verifier (not merely the untrusted solver process) signs a canonical versioned **verification verdict** using a key protected by an owner-governed signing service such as KMS/HSM. Specify nonce, expiry, signer identity, key rotation, canonical format, replay rejection and owner revocation policy. Treat a signature as an attestation of *that service's checks*; it cannot magically prove arbitrary SCIP internals or physical sensor coverage.
4. Make the deployed UI reject expired, mismatched, unverified or unverifiable run receipts **before** map/export render; only allow a research mathematical badge whose specific verification predicates are proven. Preserve first LP/log and verifier outcome in long-lived controlled archive rather than 14-day CI artifacts, with explicit author/LLDA/WorldPop licensing boundaries.
5. Run hostile forged-input, stale/broken lineage, duplicate run ID, forged signature, disabled verifier, alternate binary64 objective, incorrect budget and false dual/status controls in end-to-end app tests. Independently review resource exhaustion, sandbox permissions, external network access, Python supply chain and release operating cost.

**Decision still needed from owner:** whether the scientific dashboard should require an external signed service at all. For a transparent academic demonstration, carefully scoped source-verified model + reproducible exact mathematical evidence may be more useful than a speculative “secure attestation” badge. Do NOT claim a signed/remote or field-science proof unless an actual trusted boundary and evidence exist.

## Acceptance checklist

- [ ] Genuine first+second PySCIPOpt LP replay and forged *exactly tied but upstream disconnected* N20 K5 regression pass.
- [ ] Forged first SCIP `gap` (nonfinite, nonzero or negative), falsified original feasibility/budget/local connectivity flags, selected count or isolated list cannot be promoted to independent source-verified optimality.
- [ ] Existing live Streamlit AppTests, unified dashboard, and separate source-science triple-checkout remain green at **exact PR HEAD**; no change to original model/LP production code.
- [ ] Human science/security review decides whether to adopt a trusted external execution/signer service, what it is allowed to claim and what it costs. No automatic signing feature, merge, deployment or physical/manuscript status upgrade.

Review artifacts retain original raw SCIP LP and independent child process receipt, never unpublished manuscripts or new third-party restricted lake data. The original source local K5 1,077 feasible subset count and exploratory all-original-fixed global K5 860 feasible are distinct mathematical definitions and remain unchanged.
