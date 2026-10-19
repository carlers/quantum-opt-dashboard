# Evidence and objective-provenance seam for future dashboard integration

**Review-only scope:** Issue #85 and dashboard follow-up #88; child of DRAFT #86. This branch is a pure Python research adapter, **not** a Streamlit integration, main/preview/production release, manuscript correction, new model adoption, or measured field-science approval.

## Dependency and integration plan (2026-10-19)

The isolated scientific PR stack is **#68 → #83 → #84 → #86 → this draft**, while the independently unmerged UX stack is **#55 → #77 → #78**. Draft #78 implements exactly two modes: historical local one-hop with real SCIP; and global all-stations connectivity containing all 15 existing stations and K selected new ones, with complete enumeration and modeled fixed/fixed edges. No measured RF/backhaul is present. Do not retarget existing PRs, assume matching ancestors, merge these stacks blindly or promote either to preview. The old main-branch SESSION_STATE is superseded by dated draft-branch checkpoints.

## Machine-readable contract

The optional library **scripts/scientific_dashboard_adapter.py** accepts an original notebook-result JSON, the independent S4 provenance JSON, a backend-compiled active scenario and optionally a cached result binding. It calls **science_claim_gate.validate_evidence** each time: original exact source SHA, actual SCIP verified reference, exact 1,077 local feasible subsets, raw GeoJSON graph and S4 eight-factor checks. It never accepts a user-provided certificate as proof or upgrades claims based on a “validated” checkbox.

The active scenario must carry:

- Exact objective **model_input** with ordered candidate/fixed site identities, eight factor names and weights, exact float.hex linear and quadratic coefficients, budget and dataset hash.
- **topology_mode** equal to local_one_hop or global_all_stations, plus **graph_sha256** for the actual enforced source geometry/edge policy.
- Backend-origin **input_origin**: frozen_source_N20 or exploratory; **solver_backend**: scip for local or exact_enumeration for global; and a backend-compiled **controls** mapping that must change whenever other active inputs change.

Only unchanged source objective **and** source graph **and** local one-hop **and** frozen source controls/SCIP earn the label “Frozen source N20/K5 mathematical profile”. A global model is **exploratory despite an identical scored function**, because it changes the feasible topology; altered source weights, WorldPop-D2 relabeling, candidate generator, budget, wake coefficients, graph or other controlled inputs also require exploratory status. Only identical complete objective hashes permit comparing numerical energies as values of the *same mathematical score*, never as evidence of physically better water monitoring.

The adapter outputs plain-text claims and explicit blockers: historical source N20 calculation computationally verified, manuscript D2 **source d2_road_proximity versus printed WorldPop population** unresolved, printed Table III/Table IV and source AHP weights unreconciled, physical RF/hydrology/shoreline validation blocked. Historical original source weights sum 1.0001 and must not be secretly corrected to the paper. No “field verified”, “paper reproduced”, “quantum advantage” or expert-authorized updated model claim is permitted.

## Cache and trust boundaries

**scenario_sha256** hashes the exact active mathematical objective, graph identity, topology mode, solver backend, input origin, and compiled controls. A prior result with a different recorded scenario SHA must return **result_visibility=hide_stale**; even a match returns **bound_unverified**, never a solver-optimality or scientific-attestation certificate. A matching SHA alone is not a cryptographic signature or proof that an untrusted UI/JSON run genuinely solved an instance. A trusted backend must construct input provenance and independently verify status, selected IDs, feasibility, objective calculation and evidence exports.

The adapter's CLI produces a bounded numerical **research view JSON** only for the freshly verified frozen N20/K5 local source. It does not display the current UX model or execute that model's optimizer.

## Acceptance for a later separately authorized full Streamlit draft

1. Resolve the independent source (#86) and dashboard UX (#78) histories explicitly; review exact source graph hashes, scoring conventions, candidate IDs, and solver behavior before a focused integration branch.
2. In the active backend, bind model/control/graph/solver snapshots to each run and invalidate prior selected sites, mapped edges, objective values, LP files and ZIP exports on any relevant edit.
3. Render three distinct concepts: verified **historical source computation**, **active exploratory mathematical scenario** and independently checked **current solver status**. Plain text should show manuscript/physical blockers; no decorative “scientific validation passed” badge.
4. Preserve local source SCIP and global all-15-fixed-plus-K enumeration as distinct modeled geometric proxies, with honest no-solution/timeout messages and no invented fixed radio links.
5. Require real Streamlit AppTest with changed weights/D2/graph, forged approval, disconnected-all-fixed, timeout/infeasible, model energy mismatch and stale result/export tests **plus exact-HEAD cold notebook/SCIP/raw-GeoJSON/S4/claim checks**. This research-only PR's test success does **not** satisfy UI integration acceptance.
6. Continue #87 original expert AHP forms, original GIS/D2 recipe, verified shoreline/island geometry, WorldPop provenance and licenses, measured RF/backhaul, and calibrated water quality/current observations before proposing any new physically justified scientific scenario.

**Next steps:** review this draft and exact-HEAD research CI, then separately approve a targeted full UX adapter/integration implementation if branch strategy and proof obligations are satisfactory. No merge, publication, main/preview or production modification without separate owner approval.
