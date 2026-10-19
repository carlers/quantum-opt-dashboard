# Manuscript–notebook provenance audit (source comparison, not a correction)

**Review-only, issue [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16).** Source reviewed: owner-supplied DOCX titled *QUBO-Based Sensor Placement Framework for Water Quality Monitoring in Laguna de Bay*, available in the research conversation on **2026-10-19**. Table references below refer to the **source document's own labels**, not Python indices. We examined its actual Word tables and surrounding prose; the user-supplied manuscript is **not copied or edited in the GitHub repository**. Archived notebook and GeoJSON inputs remain historical evidence. Numerical values explicitly labeled “independent” are computations from printed manuscript values, **not assertions about unretrieved expert or solver artifacts**.

## 1. AHP matrix and reported global weights are not the same eigenvector

The manuscript's **Table III**, main criteria A/B/C/D, prints the reciprocal pairwise matrix

[
A =
egin{bmatrix}
1 & 4 & 6 & 8\
1/4 & 1 & 3 & 5\
1/6 & 1/3 & 1 & 3\
1/8 & 1/5 & 1/3 & 1
end{bmatrix}.
]

The **Table IV** printed sub-criteria global weights are:

| Printed subcriterion | Printed Table IV global weight |
| --- | ---: |
| A1, tributary/river inflow proximity | 0.276095907 |
| A2, urban/agricultural runoff proximity | 0.276095907 |
| B1, aquaculture/fishpen density | 0.179220150 |
| B2, low dissolved oxygen | 0.089610075 |
| C1, bathymetric depression | 0.087188181 |
| C2, circulation/outlet proximity | 0.043594091 |
| D1, lakeshore infrastructure access | 0.024097845 |
| D2, stakeholder/population exposure | 0.024097845 |

**Independently calculated, not printed as such:** The principal right eigenvector normalized to one from the *printed* Table III matrix is approximately **[0.616975355, 0.228319383, 0.104610094, 0.050095168]** for the A/B/C/D main criteria. Its principal eigenvalue is **4.14712642148**, yielding **CR≈0.0544912672** with RI(4)=0.90.

However, summing the manuscript Table IV subcriteria by pillar yields **[0.552191814, 0.268830225, 0.130782272, 0.048195690]** (tiny rounding error in total). The manuscript prose states **λmax≈4.2207 and CR≈0.0817**; these latter values are approximately reproduced by calculating the **average component-wise ratio** `mean((A @ published_main_priorities) / published_main_priorities)`, rather than the principal eigenvalue. **That numerical relationship does not prove which actual elicitation or aggregation algorithm the authors used**. Raw AHP questionnaires, aggregation workbook, procedure/version, and expert signoff were not in the provided manuscript and remain necessary.

The archived source notebook weights were previously verified in [issue #16](https://github.com/carlers/quantum-opt-dashboard/issues/16) as **[0.3671, 0.1224, 0.2508, 0.0502, 0.1278, 0.0183, 0.0476, 0.0159]**, also distinct from manuscript Table IV. Do not silently replace notebook values with manuscript values or vice versa: their sources and intended role may differ. An earlier labeled counterfactual N20 analysis under manuscript Table IV weights yielded source-derived optimum **−3.473640036773477**, and the Table III eigenvector counterfactual yielded **−3.629863700075275**; these are *sensitivity outputs, not recovered original publication runs*.

## 2. D2's actual input semantics need authoritative provenance

- **Manuscript Table I:** `D2 — Stakeholder/population exposure`.
- **Manuscript Table II:** `D2 — WorldPop`.
- **Manuscript Figure 2 caption:** `D2: Population exposure`.
- **Archived notebook/committed GeoJSON factor label (previous source audit in #16):** `d2_road_proximity`.

These labels are not interchangeable measures. The provided manuscript alone **cannot establish** whether the archived notebook variable names are stale, the GeoJSON layer is sourced from another processing step, or the published text refers to a different data revision. An author-approved original QGIS/export recipe and raster/WorldPop metadata are required before any decision on renaming or reweighting this factor.

## 3. N=20 SCIP optimum: manuscript and source-derived model differ

| Evidence layer | N=20, K=5 | Status |
| --- | --- | --- |
| **Manuscript Table V, SCIP** | `−3.301319`, selected `0,1,3,6,7` | Reported by manuscript |
| **Manuscript Table VII, SCIP** | `−3.301319` | Repeated publication figure |
| **Manuscript Table VII, classical SA** | `−3.301293` | Distinct SA row, not SCIP |
| **Independently checked archived-notebook-derived SCIP N20** | `−3.3012934918564643`, selected local `[0,1,3,6,7]` | Proven for **this source-derived instance** by SCIP + exhaustive N20/K5 verification |
| **Difference (source-derived minus manuscript SCIP)** | **`+0.0000255081435356`** | Not resolved by observed ~10⁻¹⁶ host precision drift |

The published optimal *site indices* agree, but **the two SCIP objective values do not**; agreement on selected sites alone does not validate published coefficient, weight, data, or solver parity. The manuscript reports SCIP on N=20–2000; only **the source-derived N=20 instance** has the cold independent exact proof described here. Earlier numerical-runtime studies in PRs #57/#61/#63 explain **ULP-sized** free/fixed differences, **not** this materially larger paper-source gap. Do not force parity by adding offsets, changing weights or rounding raw objective values.

Additional editorial review needed: the manuscript's spatial suitability prose refers to “AHP-derived weights from **Table V**”, whereas printed weights are in **Table IV** and Table V is the SCIP-results table. This is a likely internal table reference mismatch, not evidence of the original computation used. No manuscript edit is authorized.

## 4. What scientific claims are *not* established by this audit

- Cannot identify whether expert pairwise matrix, elicitation, Table IV weights, or old source weights correspond to the actual optimization run without raw questionnaires and build/revision information.
- Cannot prove the source of the 2.55×10⁻⁵ SCIP gap, reconstruct all published larger-N results, establish new accepted AHP priorities or certify published QUBO equivalence from the N=20 source alone.
- Cannot conclude “quantum advantage”: OpenJij `SASampler` is **classical simulated annealing** and no measured QPU result is presented in this source-derived audit.
- Cannot retrospectively transform existing “reported manuscript values” into “independently reproduced” results. Keep manuscript values and source-verified values in **separate columns**.

## 5. What to request from the research authors/adviser

1. The exact historical expert judgments/pairwise questionnaires, aggregation procedure, any versioned priority-weight calculation spreadsheet, and formal confirmation of the intended **Table III vs IV** mapping.
2. Original N20 coefficient matrix and raw MIQP file/export, saved station selection/feature order, `beta/delta`, dataset/GeoJSON SHA, notebook/source revision, solver/JijModeling/OMMX settings, and any objective offset convention for manuscript Table V.
3. Approved D2 layer derivation: source WorldPop files, acquisition date, QGIS processing/field name mapping, road network relation (if any), and feature license.
4. Explicit decision to retain both historical and working implementations, publish an erratum, or revise future analysis methods. This is an **author-led disposition**, not an automated model change.

**Next steps:** record this report in #16, obtain the unretrieved source artifacts, agree on accepted manuscript correction/provenance narrative, and add regression tests only after an authorized mathematical/reproducibility decision. No original DOCX/notebook/GeoJSON or deployed site was changed by this audit.
