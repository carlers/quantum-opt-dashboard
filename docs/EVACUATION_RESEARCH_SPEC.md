# Evacuation-center siting research specification — proposal v0.1

**Status:** Research proposal for review, NOT an approved thesis formulation or operational evacuation plan. Prepared 2026-10-18 as part of [issue #30](https://github.com/carlers/quantum-opt-dashboard/issues/30) and [Phase 1 #3](https://github.com/carlers/quantum-opt-dashboard/issues/3). **No geography, disaster, capacities, or actual input dataset has been authorized yet.**

## A. Why this is a NEW optimization problem

Water-quality sensor placement uses site utility, redundancy/wake interaction, a fixed count K, and **local one-hop** adjacency. An evacuation shelter problem must instead model who needs to evacuate, which approved shelter can accept them, how a **network** makes it accessible, and which facilities/routes become unsafe in a particular hazard scenario. Copying the lake objective or its one-hop interpretation would be scientifically invalid.

Related primary/secondary research includes the classical maximal covering location formulation (Church & ReVelle, 1974, [DOI](https://doi.org/10.1111/j.1435-5597.1974.tb00902.x)) and a published review of shelter siting and routing issues ([2019 European Journal of Operational Research review](https://www.sciencedirect.com/science/article/pii/S0377221718310476)). These support a **problem-family choice**, not a claim of novelty or field applicability.

## B. Research question (proposed, awaiting adviser)

> Under a specified geographic boundary, static hazard scenario, credible shelter candidates/capacities, and budget, how do alternative site-selection algorithms trade off **served evacuee demand**, **network travel burden**, **capacity utilization**, and **distributional equity**, relative to a certified mathematical optimization baseline?

A second, separate question may ask whether an explicit QUBO encoding of an **agreed small binary variant** preserves the original objective/constraints and how classical simulated annealing compares at matched computational budgets. **That is not a quantum-hardware study.** No quantum-advantage, novelty, real-time routing or disaster-response effectiveness is claimed.

### Decision gates requiring actual user/adviser input

1. Geography: named city/municipality/province plus valid administrative boundary and barangay/PSGC vintage. **Do not silently assume NCR/Quezon City.**
2. Hazard: named flooding, earthquake, typhoon/wind or other scenario, return period or authoritative designation, snapshot date, and whether road edges as well as facilities become unavailable.
3. Demand: which population is assumed to evacuate, by demographic group and scenario; **2024 total population is NOT equivalent to evacuation demand**. Choose evacuation rate or authoritative at-risk count and sensitivity ranges.
4. Candidate pool: existing verified evacuation shelters only vs evaluated potential new sites; separate location, usable capacity, safety/structural suitability, ownership, and verified occupancy.
5. Objective hierarchy: prioritize minimum unmet demand before travel time, or covering-only baseline, or other adviser-approved model; agree on treatment of unserved residents and equity.
6. Transport: walking/driving/mixed; road-speed assumptions; accessible route data; disability constraints; capacities for roads are not modeled in the first static baseline.
7. Budget: exactly/at most K facilities, or capital-cost ceiling B. Do not automatically enforce an arbitrary combination of both.
8. Deployment/release: legitimate dataset use, redistribution permissions, privacy, uncertainty and explicit disclaimer that this is research, not an official evacuation recommendation.

## C. Mathematical candidates and definitions

Let I be demand zones (e.g. barangays), J be independently checked candidate shelters, and E be the set of **reachable and permitted demand–shelter pairs** (i,j). Quantities must carry units and scenario provenance:

- d_i >= 0: **scenario evacuee demand (persons)**, NOT raw barangay population.
- C_j >= 0: independently verified usable shelter **capacity (persons)**; not estimated from map point alone.
- c_j >= 0: opening/activation cost (currency or a declared dimensionless proxy).
- t_ij >= 0: precomputed, travel-mode-and-scenario-specific shortest network **travel time (minutes)**, present only on E.
- A_ij in {0,1}: reachability under network state and optional maximum acceptable travel time T; E = {(i,j): A_ij=1}.
- e_j in {0,1}: safety/eligibility flag for candidate j under the chosen hazard scenario; unknown means **unverified, not safe**.
- x_j in {0,1}: open/use candidate j; z_i in {0,1}: demand zone considered covered; y_ij >= 0: assigned **persons** on eligible arc (i,j); u_i >= 0: **unserved persons**.
- K: allowed count of opened centers; B: activation-cost ceiling (if that budget representation is used instead).

All input IDs must be stable across files. Missing t_ij or C_j is not interchangeable with zero.

### Model 1: maximal covering location (introductory binary benchmark)

**Maximize** Σ_i d_i z_i

subject to
- Σ_j x_j <= K;
- z_i <= Σ_{j: (i,j) in E} e_j x_j, for all i;
- x_j <= e_j, for all j;
- x_j, z_i binary.

This is a **coverage potential** metric: there is NO assignment of people and NO shelter capacity, so it does **not** prove everyone covered can fit inside a shelter. Coverage must not be labeled "evacuees served" in a real report. For edge-free areas, z_i must be zero. If d_i=0, tie-breaking of z_i is not scientifically meaningful.

### Model 2: capacitated location–allocation (recommended primary candidate)

First stage: **minimize** Σ_i u_i (unserved persons).

Subject to:
- Σ_{j:(i,j) in E} y_ij + u_i = d_i, for each zone i;
- Σ_{i:(i,j) in E} y_ij <= C_j x_j, for each candidate j;
- x_j <= e_j, for each candidate j;
- Σ_j x_j <= K **OR** Σ_j c_j x_j <= B (a clearly selected policy);
- y_ij >= 0 only on E; u_i >= 0; x_j binary.

Second stage (LEXICOGRAPHIC, not arbitrary weighted sums): after proving minimum unserved U*, **minimize** Σ_{(i,j) in E} t_ij y_ij, retaining Σ_i u_i <= U* + agreed numerical tolerance and every original constraint. Travel cost is person-minutes. If desired, a tertiary stage can reduce activation cost/count without altering the primary goals. Export both stage objectives and statuses.

Why lexicographic? Counting unserved persons (persons) and person-minutes have incompatible units; choosing a sufficiently large scalar penalty is an additional, hard-to-justify modeling decision. This staged formulation makes the service priority explicit.

**Important simplifying assumptions:** continuous y_ij represents divisible aggregated demand, and can split a zone's demand across centers. It does NOT assign indivisible families or individual travelers. It is a **static single-scenario planning model**, not dynamic congestion-aware evacuation routing. Real-time roads or shelter occupancy are not automatically known. The default allows unserved demand so that insufficient capacity is transparently reported rather than causing an unexplained infeasible job. An optional all-served policy should be a deliberately separate infeasibility-tested scenario.

### Later alternatives — explicitly NOT present in v0.1

- Group-specific coverage/equity hard lower bounds or minimax subgroup disparity, but only after validated group-demand data and agreed ethical interpretation.
- Robust/multi-scenario nonanticipativity (one x_j shared across scenarios with scenario-specific y/u). Do not confuse running each scenario independently with one robust decision.
- Facility opening over multiple time periods, flows over capacity-constrained roads, pedestrian accessibility, risk-adjusted travel times, shelter staffing and medical needs.
- QUBO: binary expansion of flow (with documented person granularity and rounding), constrained slack variables and a mathematically justified penalty bound. Large matrices may be worse than the original MILP; no presumption that QUBO outperforms SCIP.

## D. Required quantitative baselines and reports

- **Ground-truth small MILP:** independently enumerated or independently coded exact cases; report feasible status, optimum/best bound, MIP gap, runtime/memory and time-limit behavior. Validate any SCIP model on the actual dataset later.
- **MCLP binary baseline:** same sites, hazard mask, network reachable arcs, K and weights; mark capacity as unmodeled. Do not compare uncovered potential directly with a capacity-constrained served population as though identical.
- **Capacitated exact model:** primary total served/unserved; secondary mean assigned travel time (only over served people), 90th percentile individual trip time only if justified/derivable from assigned flows, worst accessibility, open facilities, load/capacity ratios.
- **Heuristic baseline:** independently implemented greedy + a defensible capacity-aware assignment, measured for original feasibility and the same two-stage objective under identical data/time limit.
- **Equity diagnostics:** at-risk coverage by predefined administrative/demographic groups, unserved rates by group, geographic distribution. Never infer protected individual attributes from aggregate records; define small-area privacy reporting.
- **Scenario robustness:** perturb evacuation participation fractions, capacities, hazard closures, network speeds and K/B; track *both* performance and original constraint violations. Pre-register scenario matrix before claims.

Key outputs: source hashes, license/access notes, scenario timestamp, CRS, source-data cleaning manifest, demand/shelter/edge counts, missing/unreachable rates, model expressions and exact solver artifacts (e.g. LP/MPS), optimizer status/bounds, per-zone assignments and unmet demand, per-site utilization, selected facilities, maps labeled "research only", and versioned environment/code/seed/evaluation manifest.

## E. Synthetic reference gate before geographic data ingestion

Construct a separate tiny artificial problem (NOT an evacuation recommendation):
- 2 zones with demand d=(4,3) persons; 2 safe candidate facilities C=(5,5), K=1.
- All four arcs reachable; travel-time matrix in minutes [[1,9],[2,4]] (rows=zones, columns=shelters).
- Minimum possible unmet demand is 2 persons because only one facility with capacity 5 can open. The lexicographic second stage uniquely prefers center 1, assigns 4 persons from zone 1 and 1 from zone 2; 2 people remain unserved in zone 2; total assignment travel burden = 6 person-minutes.
- Test that imposing u_i=0 becomes infeasible, and closing the sole reachable safe shelter changes served capacity to zero. Test a zone with no reachable arcs, a candidate with unknown/zero capacity, a tie case, and a nontrivial capacity constraint.
- Test the MCLP on the **same** tiny input: it can label both demand zones "covered" even though one selected center holds at most 5 of 7 people. This demonstrates why "coverage" and "served demand" must have different labels in the UI.
- Independently cross-check every exported variable, model row and returned assignment. Only after passing this gate build a field-data prototype. No synthetic numbers should be described as measured Philippine demographics or facilities.

## F. Scientific interpretation

1. **Original water-quality science is not this model.** We can reuse scientific artifact format, experiment orchestration, SCIP integration, QUBO verification tests and transparent formulation inspector, but not its objective, adjacency graph semantics, weights or source datasets.
2. **No novelty decision yet.** Facility location / covering are long-established methods; an undergraduate thesis contribution must be argued by research question, data/sensitivity/design/evaluation, adviser guidance and a documented literature comparison.
3. **No operational safety assurance.** Public map data may be incomplete; site structural safety, road conditions, true capacities, evacuation logistics and incident commands require competent authorities. Treat model solutions as research scenarios, not instructions during an emergency.

## G. References / evidence-level boundaries (accessed 2026-10-18)

- Church, R. & ReVelle, C. (1974), "The Maximal Covering Location Problem", *Papers in Regional Science*, 32, 101–118. https://doi.org/10.1111/j.1435-5597.1974.tb00902.x . **Cited for classic model family**, not as claim that this paper used the above capacity formulation.
- "Optimising shelter location and evacuation routing operations: The critical issues" (2019), *European Journal of Operational Research*, https://www.sciencedirect.com/science/article/pii/S0377221718310476 . **Cited for importance of realistic shelter access/operations and stated research gaps**; this proposal's exact equations are a local design, not copied from that paper.
- Philippine Statistics Authority, official 2024 Census of Population (POPCEN) locality tables: https://psa.gov.ph/content/2024-census-population-popcen-population-counts-declared-official-president . **Official population counts exist**, but no evacuation participation fraction, shelter capacity, or immediate safety information follows from them.
- OpenStreetMap licensing: https://www.openstreetmap.org/copyright ; Geofabrik Philippines extract availability: https://download.geofabrik.de/asia/philippines.html . Map presence does not certify emergency accessibility.
- Geoportal Philippines: https://www.geoportal.gov.ph/ ; HazardHunterPH methodology/disclaimer https://hazardhunter.georisk.gov.ph/index.php/map and rights https://hazardhunter.georisk.gov.ph/terms-of-use . Web visualization does NOT grant bulk reproduction/redistribution.
- Wilkinson et al. (2016), FAIR Guiding Principles, https://doi.org/10.1038/sdata.2016.18 . Apply to code + models + results, not only CSV tables.

**No field data acquired or redistributed in this research-only PR.** See [EVACUATION_DATA_AUDIT.md](EVACUATION_DATA_AUDIT.md) for source-by-source suitability and release blockers.
