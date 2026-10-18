# Philippine evacuation-center source and provenance feasibility audit

**Version:** 2026-10-18 source reconnaissance for research [issue #30](https://github.com/carlers/quantum-opt-dashboard/issues/30). **No datasets downloaded or licensed for reuse by this PR.** Finding a website or map layer is NOT equivalent to a reusable, stable, validated research dataset.

## A. Source inventory and evidence status

| Proposed field(s) | Primary source leads checked | What was actually confirmed on 2026-10-18 | What is NOT yet established / next gate |
|---|---|---|---|
| Zone population (people) | [PSA official 2024 POPCEN](https://psa.gov.ph/content/2024-census-population-popcen-population-counts-declared-official-president) | Official barangay Table C spreadsheets are linked by region, including NCR and CALABARZON | Need a selected study area, stable table snapshot, permitted redistribution, PSGC-to-boundary join, error/missing handling and year-match. Total people ≠ number evacuating |
| Stable geographic identifiers | [PSA Philippine Standard Geographic Code](https://psa.gov.ph/classification/psgc/) | PSA maintains PSGC master list / classification | Need consistent 2024 vintage and geographic reorganization handling; codes must be treated as *strings*, not lossy integers |
| Administrative boundary geometry | [Geoportal Philippines](https://www.geoportal.gov.ph/) and agency datasets | Public map/layer discovery exists | Exact authoritative boundary file, CRS, licensing, scale, timestamp, resolution and matching PSGC keys not confirmed; no undocumented scrape |
| Road network and candidate point hints | [Geofabrik Philippines OSM extract](https://download.geofabrik.de/asia/philippines.html) | Downloadable OSM region extracts available | Need scope-clipped roads, travel-mode tags, barriers/speed rules, graph topology, flooding closures, road completeness, data vintage and reality checks. OSM tags/POIs do NOT certify official evacuation shelters |
| Road license | [OpenStreetMap Copyright & License](https://www.openstreetmap.org/copyright) | OSM database is licensed **ODbL**; attribution, share-alike obligations and conditions are described | Need legal/data-steward review of any published transformed network and attribution, particularly if combined with differently licensed official layers; do not erase provenance |
| Flood / earthquake / other hazard layers | [HazardHunterPH](https://hazardhunter.georisk.gov.ph/index.php/map), [its Terms](https://hazardhunter.georisk.gov.ph/terms-of-use), [Geoportal](https://www.geoportal.gov.ph/) | HazardHunterPH draws from relevant Philippine agencies, warns that its source information may be outdated or refined; terms restrict reproduction/redistribution; Geoportal displays e.g. flood hazard, active faults, NCR safe open spaces | **No verified licensed bulk hazard download** from these portals in this audit. Must obtain source-agency permission, access method, spatial scale, scenario semantics, allowed sharing and valid-time/version before ingestion. Map visualization ≠ machine-readable hazard input |
| Shelter locations / candidates | To be identified with chosen LGU / DRRMO, authorized facilities/agency | **Not verified** | Need actual official shelter register, contact/authorization, GIS accuracy, operational status, hazard eligibility and deduplication; no auto-claim from OpenStreetMap school/building points |
| Usable shelter capacity | Relevant local DRRMO/facility manager and approved inventories | **No capacity values verified** | Need per-facility *usable* person capacity, update time, seasonality, accessibility and whether occupancy/availability is recorded. Unknown C_j ≠ zero and is never guessed |
| Evacuation participation/at-risk demand | Official hazard exposure study or predeclared scenario assumption | Only a conceptual derived demand field is defined | Need population exposure model / d_i = population_i × scenario evacuation fraction_i with chosen assumptions, time horizon, rounding, sensitivity and documented limitations |
| Network hazard closures | Hazard-agency scenario polygons + routed network | Nothing verified yet | Need explicit spatial join/scenario rule to remove unsafe shelter candidates and blocked road segments; hazard suitability of a *point* alone is insufficient for safe access |
| Ethics/privacy | Public aggregate statistics and agency authorizations | No individual data ingested | Prefer aggregate zone demands; require disclosure minimization, reviewer approval for sensitive facility/occupancy information, and omit private addresses/medical data |

References record discovery **not** endorsement of accuracy for emergency use. PSA 2024 POPCEN is a statistical denominator; a total-count table alone cannot distinguish evacuees, accessibility constraints or actual shelter availability. OSM and government hazard sources may be updated asynchronously.

## B. Missingness, rights and integrity policy (blocking requirements)

1. Each dataset must have: owner/institution, URL or controlled access reference, title/vintage, retrieval timestamp, acquisition method, checksum SHA-256, geographic CRS/unit, spatial granularity, license/usage agreement and redistribution status. Keep the originally acquired immutable bytes in an authorized store; derived/corrected tables have separate hashes and transformation code. Never commit unlicensed restricted raw hazard/shelter records to GitHub.
2. Keep three states separate in candidate data: **verified eligible**, **verified ineligible**, **unknown/unaudited**. An unknown facility must not silently be treated as safe, open, or as having adequate capacity.
3. Record unknown/infinite travel and disconnected arcs explicitly, and exclude them from the optimization's set E. A missing road edge is not "zero-minute travel". Static OSM network travel must not be labeled safe evacuation time without field/hazard validation.
4. Distinguish estimated evacuee demand from raw census counts, using explicit scenario and assumptions; do not impute the same evacuation ratio as an observed demographic fact.
5. Require all source tables to specify target geographic unit, keys and release year; match PSGC codes by string, with a join-audit report counting unmatched, duplicated, subdivided or renamed units.
6. If redistribution terms conflict or are unclear, publish only derived code/synthetic fixtures/metadata permitted by license; a public result map can still expose restricted locations, so treat that as part of the rights review.
7. Explicitly record ethics and operational restrictions: dashboard should say **research prototype, not an emergency response or shelter safety recommendation**; no automated live official advice or public claims of shelter certification.

## C. Proposed normalized dataset contract (NOT yet implemented)

**Each file below is a schema proposal, not a real downloaded dataset.**

`demand_zones.csv`:

| Column | Type/unit | Validation |
|---|---|---|
| `zone_id` | unique stable string | not blank, unique; preserve leading zeros |
| `psgc_code` | string (if applicable) | declared vintage, no float/int coercion |
| `population` | nonnegative integer, persons | official data source/year cited; not already treated as evacuees |
| `evacuation_fraction` | scenario fraction in [0,1] | source vs explicit synthetic/assumed scenario label |
| `demand_persons` | nonnegative persons | derivation and rounding explicitly declared |
| `geometry_ref` | licensed polygon/representative point reference | CRS documented, join to boundary supported |
| `group_id` | optional aggregate group category | only when lawful, sufficient, and independently validated |

`shelter_candidates.csv`:

| Column | Type/unit | Validation |
|---|---|---|
| `site_id` | unique string | source agency stable ID preferred |
| `geometry_ref` | point or polygon reference | CRS/precision documented |
| `capacity_persons` | verified nonnegative integer or null | **null cannot silently become zero** |
| `eligibility` | `verified_safe` / `verified_unsafe` / `unverified` | explicit scenario and timestamp |
| `activation_cost` | optional declared currency or comparable proxy | cost unit and economic year required |
| `source_ref` | source document/inventory reference | permission + access checked |

`reachable_arcs.csv`:

| Column | Type/unit | Validation |
|---|---|---|
| `zone_id`, `site_id` | string foreign keys | must exist in source tables |
| `travel_minutes` | nonnegative numeric | shortest-path algorithm, mode, network snapshot logged |
| `scenario_id` | string | ties to hazard/closure/speed assumptions |
| `reachable` | boolean | explicit threshold/routing rule; unreachable arcs excluded from solver |
| `route_ref` | optional path metadata | no claim of real-time safety |

`scenario.json`: model ID/version, locale and boundary, input SHA list, travel mode, hazard source/version, sites/edges excluded and why, K **or** B policy, travel-time cutoff, population-to-demand calculation, optimization priority (minimize unserved first), algorithm versions, random seeds if stochastic, licenses, privacy/release status, and a provenance hash.

Derived `assignments.csv` is produced *after* solver validation: (`zone_id`, `site_id`, `served_persons`), plus `unserved_by_zone.csv` and `site_loads.csv`. Their totals must match the input demand and capacity inequalities to a predeclared numerical tolerance.

## D. Data acceptance tests BEFORE real scenario solving

- Each zone and site resolves unambiguously to the exact selected geographic boundary and snapshot; CRS recorded, coordinates transformed explicitly and sanity-checked.
- No negative people, capacities, costs, or times. No duplicated identifiers, missing population counts, unknown capacity masquerading as usable, unlicensed site coordinates, or invalid adjacency.
- Verified eligible sites and feasible road arcs are separately reviewed; a safe building with unsafe/unroutable roads is not automatically reachable.
- Hash the original source bytes and all transformations; log external tool versions, network extract timestamp, route calculation and speed assumptions.
- Publish summary counts: source zones, valid demand zones, available candidate sites, verification state distribution, total estimated demand, total verified capacity, disconnected zones, area/population excluded and assumptions.
- Test total potential capacity against demand, but **do not** mistake a capacity sum for feasible network assignment; a capacity cut can still make full serving impossible.
- Work from synthetic fixtures until all required legal and scientific gates are satisfied.

## E. Priority data acquisition and review sequence

1. Decide geography and scenario; a dataset cannot be called adequate independently of the geographic target and hazard.
2. Obtain PSA 2024 POPCEN relevant barangay Table C and PSGC vocabulary via authorized means; inspect actual download license/rights and version rather than assuming official equals unrestricted.
3. Obtain recognized LGU/DRRMO shelter candidate and verified usable capacity list, or explicitly select a hypothetical greenfield site variant and abandon claims about real evacuation centers.
4. Obtain authoritative hazard inputs with redistribution/processing authorization and clear legend/scenario semantics. HazardHunterPH terms must be respected; if no permit, select an openly licensed alternative and disclose limitations.
5. Acquire region-bounded versioned OSM network only after clarifying ODbL/attribution obligations; build shortest-path travel matrix and audited disconnected-zone report.
6. Confirm the initial synthetic formulation/solver verification tests; only then authorize a separately scoped field-data model and dashboard integration.

## F. Sources inspected (links and cautions)

- **PSA 2024 POPCEN:** https://psa.gov.ph/content/2024-census-population-popcen-population-counts-declared-official-president — region-specific barangay Table C listed; publication does not confer exposure/evacuation rate or data-subset reuse permission by itself.
- **PSA PSGC:** https://psa.gov.ph/classification/psgc/ — code vintages must be reconciled.
- **Geofabrik Philippines:** https://download.geofabrik.de/asia/philippines.html — extract/format discovery; version/time cannot be inferred just from this static document.
- **OpenStreetMap license:** https://www.openstreetmap.org/copyright — official ODbL conditions/attribution and share-alike obligations; check original full license for distribution.
- **HazardHunterPH map/disclaimer:** https://hazardhunter.georisk.gov.ph/index.php/map — third-party underlying information can be old or change; site location and hazard overlays have limitations.
- **HazardHunterPH terms:** https://hazardhunter.georisk.gov.ph/terms-of-use — notably restrict copying/reproduction and redistribution. Treat as **not automatically redistributable**.
- **Geoportal Philippines:** https://www.geoportal.gov.ph/ — layer discovery, not evidence that a specific dataset download/redistribution is licensed.
- **FAIR principles:** https://doi.org/10.1038/sdata.2016.18 — dataset and pipeline metadata, access and reuse requirements.

**Outcome of this reconnaissance:** Population estimates and road source leads exist. Actual permitted hazard geometry, approved sites/capacities, scenario evacuation ratios and full route safety remain **unverified**. No real-world study should be declared ready until these gates are passed.
