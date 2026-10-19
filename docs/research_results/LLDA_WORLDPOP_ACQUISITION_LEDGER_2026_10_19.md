# Authoritative Laguna de Bay dataset acquisition and provenance ledger

**Scope:** Issue [#87](https://github.com/carlers/quantum-opt-dashboard/issues/87); source discovery/review only, as of **2026-10-19**. This is **not** evidence that any previously requested government or WorldPop datasets were obtained, original manuscript methodology reproduced, QGIS factors reconstructed, field RF calibrated, or replacement inputs approved. No external GIS bytes, manuscript DOCX, or sensitive FOI correspondence are included in this branch.

## Why this matters

The independently verified original N20/K5 code is a historical **computational** result, not a physically validated Laguna monitoring proposal. Its source criterion `D2=d2_road_proximity` differs from the manuscript's WorldPop/population-exposure description. The original eight criteria weights sum **1.0001** and diverge from printed manuscript Tables III/IV. The original lake/radio network relies on a source-hull/geometric distance proxy; a solved graph does not establish operable wireless links. See [source audit #84](https://github.com/carlers/quantum-opt-dashboard/pull/84), [three-gate contract #86](https://github.com/carlers/quantum-opt-dashboard/pull/86), and separate [two-mode topology #78](https://github.com/carlers/quantum-opt-dashboard/pull/78).

**Every entry below is classified as source *discovered*, NOT dataset downloaded, verified, matched to original historical inputs, or authorized for public redistribution.**

## Official LLDA FOI leads (independent sources, not current project data)

| Data requirement | Primary-source discovery | What the public record actually establishes | Missing before use |
| --- | --- | --- | --- |
| Tributaries, monitoring stations, lake boundaries, coordinates | [LLDA FOI 2023 tributaries/stations, #DENRLLDA-366345211204](https://www.foi.gov.ph/requests/shapefile-of-laguna-lake-tributaries-and-monitoring-stations/) and [lake boundary/station coordinates, #DENRLLDA-039451800950](https://www.foi.gov.ph/requests/laguna-de-bay-sampling-station-coordinates-and-lake-boundaries/) | Both show a request marked successful in September 2023; official response directs requesters to LLDA and specifies a *standard Access to and Use of Information agreement* before data release | Project-specific written authorization; actual polygons, islands, station IDs/coordinates, CRS, vintage, topology and rights |
| Separate tributary/monitoring shapefile candidate | [LLDA FOI 2022, #DENRLLDA-694952996621](https://www.foi.gov.ph/requests/shapefile-of-laguna-lake-tributaries-and-monitoring-stations-denrllda-694952996621/) | Government response lists `Shapefiles.zip` attachment and marks prior request successful | Attachment bytes independently inspected, contents/CRS verified, exact waterbody and station identity checked, licensed reuse approved |
| Basin/watershed boundary | [LLDA FOI 2026 watershed shapefile, #DENRLLDA-970860230621](https://www.foi.gov.ph/agencies/denrllda/laguna-de-bay-watershed-boundary-shapefile-gis-data/) | Approval is recorded April 6, 2026; record says documents were emailed to that requester | A *watershed boundary is not the lake waterbody shoreline*. Do not substitute this for water polygon/holes. Project-specific release, CRS and rights absent |
| Existing fish sanctuaries, fish-pen claims | [LLDA FOI 2022 lake/fish sanctuary, #DENRLLDA-705841634761](https://www.foi.gov.ph/requests/shapefile-shp-and-other-details-of-the-lake/) | Response explicitly reports fish-pen shapefile **not available** for that request; lists a separate `LdB_Fish_Sanctuary.zip` attachment and historical estimated fishpen/cage area | Do not infer contemporary mapped aquaculture exposure from that old estimate. Need independent vintage, fishpen geometry and use rights |
| Temperature, dissolved oxygen and fish-kill history | [LLDA FOI 2026 water quality request, #DENRLLDA-945540494109](https://www.foi.gov.ph/agencies/denrllda/water-quality-data-in-laguna-de-bay/) | The request sought historical daily temperature/DO and fish-kill records. April 6 official response indicates files were emailed to the recipient | **No verified daily series or measurement frequency** in hand. Need dates, station IDs, method/detection limits, time zone, QA/QC, censoring, use rights and actual files |
| Further multi-layer availability request | [LLDA FOI 2026 lake data and maps, #DENRLLDA-819209733687](https://www.foi.gov.ph/agencies/denrllda/laguna-lake-data-and-maps/) | A third-party graduate research request sought ZOMAP, bathymetry, hydrodynamics, station coordinates, water quality, fish kills | Request does not establish availability, approval, file quality, download rights, or published reproducibility |

**FOI caveat:** Public `SUCCESSFUL` badges sometimes mean the agency replied with contact/agreement instructions or delivered files **privately by email**. A third-party approval is not proof that this project received, can inspect, or can redistribute those files. Do not copy third-party requesters' private correspondence into GitHub.

## WorldPop 2020 Philippines is *not* one uniquely identified input

Official WorldPop 2020 population-count candidate products:

| Provider record | Explicit attributes | Scientific provenance implication |
| --- | --- | --- |
| [WorldPop Philippines 2020, dataset ID 6316, DOI 10.5258/SOTON/WP00645](https://hub.worldpop.org/geodata/summary?id=6316) | Estimated population **per grid cell**, GeoTIFF, geographic WGS84, 3 arc-seconds (~100m at equator); production date listed as 2018-11-01 | Year-labeled estimate is not equivalent to a 2020 production or census source. Record version/method/DOI, never infer original manuscript D2 |
| [WorldPop Philippines 2020, dataset ID 49861, DOI 10.5258/SOTON/WP00684](https://hub.worldpop.org/geodata/summary?id=49861) | Population per pixel, GeoTIFF 3 arc-seconds, geographic WGS84; Built-Settlement Growth Model, production 2020-09-16, mapped unsettled NoData cells | Different data-generating model. NoData may mean modeled unsettled, not necessarily zero population; provenance and sampling semantics required |
| [WorldPop Philippines 2020 UN-adjusted 2020 count, dataset ID 28283, DOI 10.5258/SOTON/WP00660](https://hub.worldpop.org/geodata/summary?id=28283) | Estimates population per grid cell; national totals adjusted to UN Population Division estimate | Denominator/normalization differs; not interchangeable with another count raster |
| [WorldPop legacy Philippines 100m datasets, ID 85, DOI 10.5258/SOTON/WP00216](https://hub.worldpop.org/geodata/summary?id=85) | Lists distinct `PHL_ppp_v2b_2020.tif`, `PHL_ppp_v2b_2020_UNadj.tif`, `PHL_pph_v2b_2020.tif` and other files | Count-per-pixel versus density-per-hectare, adjustment and version are different variables, even where the nominal year matches |

WorldPop maintains [product selection guidance](https://hub.worldpop.org/project/categories?id=3) distinguishing newer Global2 products from archived Global1. [WorldPop FAQ](https://www.worldpop.org/faq/) describes a standard CC BY 4.0 license, while the WorldPop 2020 BSGM dataset page warns that certain derived products using OSM/Microsoft inputs may be subject to ODbL. **License review must be product-specific** and cannot be inferred from the provider name alone.

A future population-based D2 must specify the exact data DOI/version/file SHA, geographic versus projected processing, cell population vs density, relevant shoreline population exposure metric, uncertainty and weighting choices. Selecting a 2020 TIFF solely because the paper says “WorldPop” would manufacture data provenance.

## Intake gates (no new modeling until all prerequisite stages)

1. **Permission and scientific ownership:** Identify original author GIS/QGIS processing recipe, LLDA expert pairwise AHP sheets, any individual/aggregated judgments and source Table III/IV reconciliation. Request LLDA lake-waterbody-with-island-holes geometry, individual station coordinates with stable IDs, lake DO/current time series, quality flags and station metadata. Ask explicitly about publication, archival, redistribution and derived-data rights.
2. **Immutable source intake:** For any authorized files, record collection method, canonical provider URL/ticket, timestamp, file and subresource SHA-256, version/vintage, contact approval in access-controlled records, license/redistribution restrictions, native CRS, formats, missing-values meaning, spatial/temporal coverage, quality/uncertainty. Do **not** upload permission-restricted raw data to public GitHub.
3. **Independent spatial checks:** Check lake **waterbody** vs **watershed**, island-hole inclusion, geometry validity, reprojection to project EPSG:32651, coordinate axis/units, station identifier crosswalk and sampling era. Do not default to the original ad hoc concave hull as authoritative shoreline.
4. **Criteria AHP scientific review:** Compare actual LLDA and original criteria interpretations, document WorldPop variant/proximity kernel or road proxy, make any newly defined D2 a separately versioned mathematical model, reconstruct source vs printed AHP weights without “fixing” historical experiment inputs. Require new elicitation approval if source forms are absent.
5. **Physical connectivity:** Obtain deployment hardware, antenna height and radio band, path-loss/two-way link measurement, shore gateways and backhaul, fixed-to-fixed links, and hydrodynamic/DO transport observations. Old model `Dmax`/wake scales remain **assumptions** pending measurements.
6. **Pre-registered sensitivity design:** Only after source/model assumptions are vetted specify physically motivated parameter bounds and spatial uncertainty scenarios, independent evaluation outcomes and held-out field datasets. Preserve source N20 as a computational regression only, not a calibration target or experimental proof.

## Explicit status and next steps

| Gate | Status |
| --- | --- |
| Government source leads and WorldPop version candidates | **DISCOVERED** via official source pages |
| Raw waterbody/shoreline, source station coordinates, DO/current observations | **NOT RETRIEVED OR VERIFIED HERE** |
| Original author AHP elicitation forms, QGIS D2 processing | **NOT RECOVERED** |
| Public redistribution and dataset-specific licenses | **NOT CLEARED** |
| Historical source N20/K5 computation | Independently verified in separate source-only PR #86 |
| Manuscript parity, field radio/hydrodynamic science, new scenario ranges | **BLOCKED** |

**Next steps:** requester/author obtains exact scientific rights and underlying original AHP/GIS/physical records; confirm which official datasets can be transferred with metadata; then separately review a reproducible intake/validation PR (file hashes, schema, spatial tests) **before** any scientific replacement or Streamlit data publication. No dataset bytes were fetched or adopted in this research note.
