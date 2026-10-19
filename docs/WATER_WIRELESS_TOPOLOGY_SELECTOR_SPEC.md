# Draft design — wireless topology selector for the water-quality dashboard

**Date:** 2026-10-19. **Design-only DRAFT**; user clarification [#76](https://github.com/carlers/quantum-opt-dashboard/issues/76). Historical notebook connectivity is intentional **local one-hop**, not a source bug. The established research changes to connectivity were **preregistered counterfactual tests**, not a new default or physical validation.

## What the user clarified

"Connectivity" means **wireless communications**, modeled by a straight-line path over water: land blocks direct modeled sensor-to-sensor communication. The user requests a dashboard choice among **local clusters, global chain and global connectivity**, while retaining the original historical model unchanged.

This spec's definitions of the latter two are *proposals pending owner confirmation*, not interpretations secretly attributed to the archived notebook.

| ID | User-facing choice | Mathematical behavior | Scientific label |
| --- | --- | --- | --- |
| `source_local` | **Local clusters — original** (default) | Exactly K selected new sensors; each selected new sensor has an unobstructed direct modeled wireless edge to either **one** fixed site or at least one selected new site. Distinct disconnected groups, including a mutually connected group without a gateway, can be allowed. | "Historical local one-hop constraint; does not promise a route to shore or one network" |
| `gateway_reachable` | **Global chain — multi-hop to an existing station** *(provisional)* | Every selected new sensor has a path of **one or more direct modeled wireless links** through other selected new sensors to **at least one** original fixed station. Multiple separately anchored chains/components are permitted. **Not** a literal degree≤2 linear path. | "All new sensors gateway-reachable; several independent fixed-anchored networks can exist" |
| `one_connected_network` | **Global connectivity — one network** *(provisional)* | All K selected new sensors lie in **one** connected component of the graph induced by the chosen new sites and the original existing stations, using only **observed** new/new and new/fixed direct links; at least one existing station is part of that component. Existing stations outside the component may remain disconnected. | "One modeled connected selected-sensor network; unmeasured fixed/fixed links not assumed" |

**Two explicit owner confirmations needed before implementation:** (1) Does **global chain** mean the provisional *potentially branching, multi-hop gateway reachability*, or does the user literally want *one line of relays* (path topology with restricted degree)? (2) Should **global connectivity** require only all **new** selected stations to share a network reaching at least one existing station, or also require **all 15 original existing stations** to be on the network? All-original-fixed connectivity cannot currently be evaluated honestly because fixed-to-fixed radio topology/backhaul is not documented.

## Evidence that separates these modes

The user-authorized, preregistered [#74](https://github.com/carlers/quantum-opt-dashboard/pull/74)→[#75](https://github.com/carlers/quantum-opt-dashboard/pull/75) study **fixed the same original N20/K5 source coefficients and geometry** across the three graph constraints and enumerated all 15,504 five-site subsets exactly. Source code + actual GeoJSON/SCIP CI was green on [run #39219858893](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39219858893). Results:

| Mode | Feasible K5 sets | Optimum new-site local IDs | Original same-objective E |
| --- | ---: | --- | ---: |
| Local clusters (`S0`) | **1,077** | `[0,1,3,6,7]` | `−3.3012934918564643` |
| Gateway-reachable (`S1`) | **1,077**, exactly the same membership SHA | `[0,1,3,6,7]` | `−3.3012934918564643` |
| One connected (`S2`) | **110** | `[1,3,6,10,19]` | `−2.121029253124326` |

**Do not hide the S0=S1 observed null result.** This N20 graph already causes all original feasible new-only components to have at least one direct fixed link; that is an empirical peculiarity of this specific source instance and not proof the rules are mathematically equivalent for other graphs or larger N.

## Required link provenance and scientific caveats

Current review-only UI [#55](https://github.com/carlers/quantum-opt-dashboard/pull/55) has `prototypes/streamlit_water_quality/model.py` with an `Instance` containing **20 candidate free-to-free adjacency lists** and **20 binary** `fixed_neighbors` flags. The latter **discard which specific fixed stations the links reach**. These bits suffice for `source_local`, and even a pure component-anchoring check, but **cannot** prove that two selected groups share the *same* fixed relay. The global mode therefore **must not run** from collapsed booleans. The independent [#67](https://github.com/carlers/quantum-opt-dashboard/pull/67) geometry verifier reconstructs exact **20×15** candidate-to-original-fixed direct-link identities; the new dashboard backend must provide and verify them in its graph provenance.

The link predicate from the historical source model is:
1. Both endpoints are strictly within the concave hull from the 5,417 original committed source centroids (ratio 0.05, holes permitted).
2. The entire **straight line** between endpoints is within that hull, so modeled land crossings block links.
3. Euclidean source CRS EPSG:32651 distance is within the source-derived Dmax (approx. **9,873 m** at original defaults).

This is **not** a surveyed shoreline, actual land-cover mask or measured radio budget. Intervening obstacles beyond the derived hull, antenna heights, lake curvature, Fresnel clearance, actual link availability, shore gateways and fixed/fixed radio or backhaul infrastructure are **not in current data**. Expose the proxy as "**modeled wireless link**" rather than a real-world guaranteed connection. Never fabricate fixed/fixed edges.

## Dashboard interaction proposal

Use a sidebar radio/select control labeled **Wireless connectivity requirement** before running the solver, with default **Local clusters (original notebook)**. A concise explanation should appear under each choice, plus a small warning for more restrictive modes ("Exploratory topology; original notebook used local one-hop"). Show a component-level summary **after** solving, including which selected nodes connect to which fixed sensors, which routes are only modeled, and how many disconnected components exist. On the map, draw allowed **selected** free-to-free / free-to-fixed edges that meet the *same* land-blocked link predicate; never draw fake cross-land connections, inactive candidates or non-observed fixed/fixed edges as confirmed links. Show selected-site maps before solve as usual, and clearly distinguish unsolved versus solved.

The **choice must affect the actual optimization constraints**, not just filter the final map or reject a result after the historical solver returns it. Retain the original objective for comparable baseline science: exact K cardinality, original eight factor weights and original quadratic terms. For N20 small exact modes, a solver formulation or bounded deterministic enumerator is acceptable if accurately labeled; do not claim SCIP certified a scenario that was only enumerated, and don't quietly treat time-limited incumbents as optimal. For larger budgets K, recognize combinatorial complexity and report unsupported cases honestly rather than hang the app.

A change to mode must invalidate existing result state, model fingerprint, exports and provenance. Record `connectivity_mode`, source candidate/fixed site orders, detailed graph-edge lists, derived geometry/parameter/algorithm hashes, original source input SHA, solver algorithm/status, chosen node/gateway IDs, and independent feasibility verification. Keep the source notebook's exact regression label only in `source_local` with the original default weights, K and interactions. A selected global mode must never claim to replicate source/published SCIP energies without its own separately audited result.

## Acceptance tests planned (none claimed executed for a new dashboard implementation)

- With original unchanged data/defaults, `source_local` returns original selected `[0,1,3,6,7]`, source energy, 1,077 feasible-region membership; `gateway_reachable` yields same members/optimum in this specific N20; `one_connected_network` yields 110 members, selected `[1,3,6,10,19]` and its own source-objective energy.
- Synthetic site pair connected only to itself (mutually): passes original local mode, fails gateway-reachable. Two separate anchored groups: passes gateway reachability but fails single global network. Two groups sharing an explicitly observed fixed-station contact pass single global network.
- Edge passing over the original modeled land polygon excluded from **all** modes; no fake links from fixed/fixed edges.
- Changing mode, K, weights, beta/delta or dataset invalidates stale solve and downloads. Unsupported/infeasible inputs show an honest message and no false optimality claim.
- Actual no-JSON Streamlit AppTest (including keyboard focus and mobile hint), new pure-Python link/scenario tests, fresh original N20/SCIP/GeoJSON controls and proven exact implementation. No preview/production promotion or `main` merge without separately explicit authorization.

## Scope boundary / signoff

This PR should include **only this design and handoff**, not a premature on-screen control that doesn't affect solving. It preserves old source N20, historical notebook, original GeoJSON, old SI unit coefficients, the existing #51/#53/#55 MVP UX stack, the deployed pilot, preview and main.

**Next steps:** ask research owner the two meaning questions above; after confirmation, implement a new **DRAFT** solver + Streamlit/AppTest UI task based on the existing UX stack, retaining default local original mode. Run controlled CI and inspect the exact graph+SCIP/enumeration outputs before any merge/deployment request.
