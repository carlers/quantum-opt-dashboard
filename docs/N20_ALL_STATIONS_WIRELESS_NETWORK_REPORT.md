# Two-mode wireless topology: complete 15-existing-station global network

**Date:** 2026-10-19. **Status:** bounded code-and-source-model verification in [review-only DRAFT PR #78](https://github.com/carlers/quantum-opt-dashboard/pull/78). No deployment, merge, historical notebook rewrite, physical wireless survey or published-paper parity claim.

## The owner's finalized scientific requirement

Exactly **two** dashboard modes:

1. **Local clusters — historical/default:** original local one-hop constraint from the committed Laguna de Bay notebook; existing clusters can be disconnected. Do not reinterpret as a historical global connected network.
2. **Global connectivity — all stations:** every one of the **15 original existing stations** AND every one of K chosen new stations must belong to **one connected wireless-link component**, with paths possibly using multiple intermediate sensors. No disconnected existing stations, no arbitrary virtual station-to-station backhaul. The original source objective, K, candidate set and station positions remain unchanged.

For the new global mode, direct modeled edges join two sites only if their entire straight segment is strictly inside the original source lake concave hull (ratio 0.05, holes allowed) and the projected Euclidean distance is within the same original Dmax. Unlike historical optimization, the graph explicitly **calculates fixed-to-fixed geometric links** using the same rule; it never claims those are **measured radio links**. Real power, antenna height, Fresnel clearance, bandwidth, operating status and original fixed-station backhaul were **not supplied**.

This requirement is **NOT** the prior preregistered S2 in [#75](https://github.com/carlers/quantum-opt-dashboard/pull/75): S2 required only **all selected new nodes** and at least one fixed station in one component, allowing other fixed stations to remain disconnected and not constructing fixed-to-fixed edges. Its **110** feasible five-site choices must not be represented as a result for this owner's full-global definition.

## Exact original N20/K5 observations

After implementation, the genuine pinned 5,417-feature source was rebuilt in [Streamlit CI #39225164320](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39225164320) and independently checked using a **separate union-find full enumeration** of all `C(20,5)=15,504` possible selections.

| Frozen source mathematical result | Count / value |
| --- | ---: |
| Original one-hop local mode feasible K5 sets | **1,077** |
| NEW all-existing plus five new globally connected K5 sets | **860** |
| Complete ordered all-station global feasible-set SHA-256 | `3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40` |
| Direct free/free modeled edges | **11** |
| Direct free/fixed modeled edges | **34** |
| **Newly derived fixed/fixed modeled links** | **17** |
| Full 35-site graph connected components | **8** (seven optional isolated candidate sites; all 15 mandatory original stations lie in **one** possible combined graph component) |
| Original source-local winning new indices | `[0,1,3,6,7]` |
| Exact globally connected winning new indices | **`[0,1,3,6,7]`** |
| Same original source objective value | `−3.3012934918564643` |

**Interpretation:** The global requirement removes **217** of the 1,077 original local-feasible five-site combinations but, in this specific original N20/K5 instance, **does not change the optimum**. The fixed-to-fixed links explain why the fully modeled all-original network has more viable candidates than the older S2 graph (860 versus 110), without relaxing the owner's new *all-stations* definition. All counts and this optimum are **conditional on the geometric radio-link proxy** and the original source dataset, not an empirical claim that every station can actually communicate.

## Implementation contract and solver honesty

- New `prototypes/streamlit_water_quality/wireless_topology.py` constructs and fingerprints an actual explicit 35-vertex graph using the source projected station coordinates, original link geometry and Dmax; compares all rebuilt free/free neighbors and free/any-fixed contact flags against the source instance.
- Source local mode continues to call **real SCIP** and retains original objective/constraints and source optimum canary. Global mode uses **exact deterministic subset enumeration**, not SCIP. It certifies feasible count and winning original objective for the chosen K. The full-graph component check may prove infeasibility **only if mandatory fixed stations belong to different full-graph components**; optional isolated candidates alone cannot prove impossibility.
- A 30-second search cutoff is reported as **indeterminate**, not incorrectly as proven infeasible or optimal. Complete enumeration proves either a minimum or infeasibility at that K.
- Dashboard mode selection changes the actual optimization predicate, manifest/settings/fingerprint and cached results. Map draws only modeled links whose *both endpoints are active*; metadata and selected-site CSV are exported without falsely adding an `actual_scip_model.lp` in global exact-enumeration cases.
- Local default/legacy source tests, original no-JSON input flow and unified dashboard smoke tests remain part of CI.

## What is NOT yet validated

The 17 existing-to-existing links are a **new *derived* graph scenario** constructed from the same original concave hull and distance bound; the old notebook did **not** assert/verify them as field radio connections. No separate telemetry, packet loss, gateway/backhaul, RF line-of-sight, physical calibration, actual shoreline survey, cross-host exact-bit or published paper weight/D2 replication. These are necessary for field deployment claims and must not be inferred from a graph-connected mathematical optimum.

**Next steps:** inspect the exact-head CI after final documentation, preserve its source-network JSON/graph/solver certificate as a short-lived artifact, review in [Issue #76](https://github.com/carlers/quantum-opt-dashboard/issues/76) and obtain research-owner approval **separately** before merging or promoting preview/production. Original data/notebook and deployed apps unchanged.
