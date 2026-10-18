# UX first-run polish · feedback-led MVP slice (2026-10-18)

A real first-time user successfully completed the default water-quality placement, but could not find the eight factor weights and was unable to complete a non-JSON synthetic model change. The classical-SA page was usable but left the choice of QUBO penalty unexplained. The guided improvements below respond to **observed** friction, rather than adding mathematical scope.

## What changes for a researcher

**Water-quality placement** keeps its exact committed N20 model and notebook baseline as the default, with the familiar "number of sensors to place" control. A prominently visible **Eight factors and their importance** panel lists all eight source columns in understandable language and numeric weights. Users may select Notebook, Paper (labeled comparison), or Custom criterion weights and edit each of the eight values with bounded ordinary number fields. The original source GeoJSON criterion scores are not silently rewritten. An optional advanced panel exposes beta (redundancy penalty) and delta (wake overlap penalty), each bounded 0–10 and with hover explanations. Changes recompile the *same* numerical model, update the fingerprint, invalidate previous SCIP results, and appear in the evidence archive. Only N20/K5 notebook weights + beta=delta=1 is treated as the historical notebook baseline. Any edited case is an exploratory scenario with independent original-model verification.

**Configure another problem** keeps the old nine supported scientific presets, numerical validators, typed mathematical compiler, exact SCIP LPs, independent reference and SHA archives. The default fictional capacity-constrained shelter example now exposes **Maximum evacuation centers to open** and **People needing shelter in selected zone (fictional)** as normal number fields. They update the authoritative JSON source/parameters before recomputation—no hidden parallel model, no eval and no real shelter/person data. The raw dataset, uploader and parameters fields remain in optional Advanced panels. A verified SCIP result is summarized using understandable metrics, selected fictional sites and an explicit distinction between people truly served and *potential* covering-model reachability. The exact original report remains under an advanced disclosure. For typed math examples, the guided variable/objective/constraint editor appears before the advanced JSON source.

**QUBO and classical SA** now opens with the scientific question and explains that the penalty changes the extra energy cost of constraint violations. The historical notebook row-sum heuristic remains the transparent starting value; advanced penalty selection is collapsed, each option has in-context explanatory copy and hover help, and the global-bound choice is carefully distinguished from any false guarantee that stochastic OpenJij finds a feasible assignment.

## Scientific guardrails

- No new source data, no changes to historical paper/notebook input or mathematical objective implementation.
- Notebook versus Paper criterion differences remain explicit; custom weights do not imply publication replication.
- Beta/delta adjust only existing original coefficients, not one-hop connectivity or sensor count constraints.
- Constrained generic QUBO compilation remains refused unless mathematical equivalence is independently established.
- OpenJij is **classical** SA; larger penalties may still give infeasible sampled states.
- Scenarios for evacuation centers remain *entirely fictional* and unsuitable for real disaster planning.

## Acceptance

- [ ] Existing N20 notebook baseline remains exactly optimal and source SHA unchanged.
- [ ] Changing a single factor weight or beta changes resolved numerical coefficients/source fingerprint and later output; old results hidden immediately.
- [ ] Changing the default synthetic maximum-open constraint from one to two gives independently verified unserved 2→0, without touching a JSON editor.
- [ ] Changing a fictional demand number updates the exact archived source bytes and validated result.
- [ ] The QUBO penalty has a sensible baseline and real in-context rationale, without falsely promising quantum advantage or sampled feasibility.
- [ ] All existing headless app tests and full scientific test suites green on exact PR head.

## Retest protocol (no click-by-click hints)

Ask the owner to (a) change the importance of one water-quality environmental factor and reproduce a different verified experiment, (b) change a synthetic shelter constraint and explain who is served, and (c) explain the trade-off between baseline and global QUBO penalty in their own words. Where they get stuck indicates the next UX improvement. Do not give procedural instructions; preserve the blind-test value.

This is a **review-only draft** on top of integrated MVP PR #51; do not update `main`, live production, or the permanent `preview` branch until tests/review and appropriate approval.
