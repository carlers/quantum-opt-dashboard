# N=20 SCIP source-parity validation (issue #12 / #6)

**State:** Automated verification in a separate, unmerged development PR. This is *not* a claim that the published N=20 experiment has been reproduced.

## Immutable evidence and experiment boundary

- Original source: `problems/water_quality/notebooks/experiment9 grid search copy.ipynb` (Git blob `a554f4f37957e924c0ed417e53af2dab04e45ffa`).
- Data: `problems/water_quality/data/LDB_centroids_clean.geojson` (Git blob `de79af608585bc02eb0ab05c0fd4cc2f02e9acd7`).
- Baseline Streamlit model: `prototypes/streamlit_water_quality/model.py`, live pilot blob `4a0a75a65313a735af588e3bac4b471ac7a88e32`.
- Paper supplied separately: *QUBO-Based Sensor Placement Framework for Water Quality Monitoring in Laguna de Bay*, Table IV and Table V. Paper data and immutable notebook are **not** interchangeable.
- Fixed experiment parameters: N=20 **new free candidate sites**, K=5 **new stations**, `L_c=7500 m`, `L_w=1000 m`, `beta=delta=1`, eastward current `(1,0)`, `D_max=1.15 × max nearest-neighbor distance among fixed stations` (if multiple), water mask = concave hull ratio 0.05, 10,000-site bbox hex pool, seeded FPS, local one-hop connectivity inequality.

## Known provenance and methodological discrepancies

| Topic | Previous paper | Committed notebook / pilot | Consequence |
|---|---|---|---|
| AHP weights (A1,A2,B1,B2,C1,C2,D1,D2) | `[.276095907,.276095907,.179220150,.089610075,.087188181,.043594091,.024097845,.024097845]` (Table IV) | `[.3671,.1224,.2508,.0502,.1278,.0183,.0476,.0159]` (notebook Cell 2) | Alters utility and possibly which existing sites are simulated; cannot compare final energies directly |
| Existing stations | 15 existing (methods) | GeoJSON `has_existing_station` flags if present, else three simulated sites chosen using utility and 12 km separation | Must record flags, actual fixed-site identities, distance threshold; no 15-site override is justified without source |
| D2 | Stakeholder/population exposure (Table I) | `d2_road_proximity` (GeoJSON factor named in notebook Cell 2) | Weighting D2 does **not** convert roads into population exposure |
| Solver | SCIP MIQP via JijModeling/OMMX notebook Cell 5 | PySCIPOpt with auxiliary binary pair-product linearization | MILP can be equivalent on the *same coefficients*, but solver equivalence does not imply data equivalence |
| Results | N=20 energy **−3.301319**, local selections **0,1,3,6,7**, reported feasible (Table V) | **Not known until the test is run** | Source candidate indexing, coefficient vectors and fixed stations must match before making a replication claim |
| Cached source | Notebook stages can load cached pickles keyed by an incomplete config hash | Pilot rebuilds from committed GeoJSON | Notebook cache may be stale or from different weights; a cold rebuild is the comparison baseline |

Additional publication clarification: Table VI reports an SA best energy −3.301293 at N=20; that is a *different solver* and must not be substituted for the SCIP figure.

## Reproducible method and pass/fail meaning

Run from repository root on the branch, with Python 3.12:

```sh
python -m pip install "numpy>=2,<3" "scipy>=1.11,<2" "shapely>=2,<3" "pyscipopt>=5,<7" "pytest>=8"
python -m pytest prototypes/streamlit_water_quality/tests/test_n20_reference.py -q -s
```

The test runs both the **notebook-code weights** and the **paper-weight sensitivity scenario**. For each it:

1. Reloads the committed GeoJSON from disk; reconstructs utility, existing/fallback station selection, water mask, hex-pool snapping, FPS and coefficients using the original notebook Cells 2–4 as the specification, **without calling the pilot's reconstruction or feasibility functions**.
2. Asserts that the pilot's free and fixed master indices (zero-based GeoJSON feature positions), utilities, complete linear coefficients, all nonzero free-free interactions, neighborhood graph, fixed neighbors and D_max equal the independently reconstructed arrays.
3. Exhaustively enumerates all `C(20,5) = 15,504` subsets, independently checks each connectivity condition and evaluates linear + quadratic energy.
4. Runs the real PySCIPOpt optimizer and requires proven `optimal` status, feasibility, correct budget, and energy equal to the brute-force global minimum with absolute tolerance `1e-7`. Tied optimal site sets are permitted.
5. Emits lines beginning `N20_VALIDATION ` with source SHA-256, environment versions, settings, site identifiers, coefficient count, solution, reference optimum and **non-equivalence-labeled** delta from the published energy.

The existing PR #14 SCIP tiny-model tests remain separate: they prove elementary solver/linearization behavior, not notebook instance construction. The new comparisons can detect changes to source weights, site ordering, utility calculation, interactions, connectivity or solver output.

**Acceptance boundary:** Tests passing establishes internal notebook-formula ↔ pilot-model agreement on a cold N=20 build and independently verified optimum. It does **not** establish that the uploaded paper was produced with those data, source revisions, station positions or weight vector, nor that the original JijModeling/OMMX notebook environment was rerun. Research claims need additional provenance for the paper's original inputs, cached instances, outputs, and original solver environment, and a user-supplied live Streamlit N=20 result (including its settings).

## Review and deployment safety

This development branch starts from `plugin-water-scip-regression` (PR #14 head). The new PR targets that **non-live** branch (stacked), not the active `plugin-water-streamlit-pilot` deployment branch. No source notebook or data are rewritten; no Streamlit UI code or solver math is changed. No merge into the live app without explicit user approval.
