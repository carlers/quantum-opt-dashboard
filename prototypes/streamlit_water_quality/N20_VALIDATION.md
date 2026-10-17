# N=20 SCIP source-parity validation (issue #12 / #6)

**State:** Automated verification **passed** on draft PR #15 (including [GitHub Actions run 39071712498](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39071712498)); 14 tests passed, with final golden-fixture CI checks repeated after updates. Source-formula and exact optimality parity have been established for the cold build. This is *not* a claim of exact published numerical replication.

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
| Existing stations | 15 existing (methods) | **15 marked existing stations verified** in the committed GeoJSON; fallback to 3 is not used for this dataset | Count reconciled for the committed dataset; paper's exact fixed-station identifiers not independently available |
| D2 | Stakeholder/population exposure (Table I) | `d2_road_proximity` (GeoJSON factor named in notebook Cell 2) | Weighting D2 does **not** convert roads into population exposure |
| Solver | SCIP MIQP via JijModeling/OMMX notebook Cell 5 | PySCIPOpt with auxiliary binary pair-product linearization | MILP can be equivalent on the *same coefficients*, but solver equivalence does not imply data equivalence |
| Results | N=20 energy **−3.301319**, local selections **0,1,3,6,7**, reported feasible (Table V) | Notebook weights: **−3.3012934918564643**, selected **0,1,3,6,7**, proven optimal | Local choices agree; energy differs by **+0.0000255081435356** (pilot minus paper) |
| Cached source | Notebook stages can load cached pickles keyed by an incomplete config hash | Pilot rebuilds from committed GeoJSON | Notebook cache may be stale or from different weights; a cold rebuild is the comparison baseline |

Additional publication clarification: Table VI reports an SA best energy −3.301293 at N=20; that is a *different solver* and must not be substituted for the SCIP figure.

## Verified result — 2026-10-18

GitHub Actions run [39070257316](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39070257316) successfully installed PySCIPOpt 6.3.0 on Python 3.12.15 (NumPy 2.5.4, SciPy 1.18.1, Shapely 2.2.0); syntax compilation and **10 tests passed**. Both N=20 scenarios matched the independently reconstructed instance arrays and exhaustive 15,504-combination enumeration.

| Measurement | Notebook weights | Published Table IV weights applied to the same GeoJSON |
|---|---:|---:|
| Exact SCIP optimum energy | **−3.3012934918564643** | **−3.473640036773477** |
| Independent enumerated optimum | −3.3012934918564647 | −3.473640036773477 |
| Local selected candidate positions | 0,1,3,6,7 | 0,1,3,6,7 |
| Marked fixed stations | 15 | 15 |
| Quadratic free-free edges | 12 | 12 |
| D_max (m) | 9873.27073466548 | 9873.27073466548 |
| SCIP status | optimal | optimal |

The candidate position order in the deterministic N=20 cohort is `[5253,2394,1894,1557,3225,4623,47,5409,3922,2408,2694,4136,2567,1164,4973,4537,2726,968,16,1762]`. The selected **GeoJSON master feature positions** are `[5253,2394,1557,47,5409]`; do not confuse them with local candidate positions.

Source data: 5,417 GeoJSON points, **15 actually flagged existing stations** (not simulated). SHA-256 of GeoJSON: `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`. SHA-256 of notebook: `08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048`.

An additional third **counterfactual** test using AHP priorities re-derived from the printed Table III (not the published Table IV weights) gives SCIP / enumerated optimum **−3.629863700075275** and the same selected local indices **[0,1,3,6,7]**. It is not a fourth source of historical experimental truth.

The **published** SCIP N=20 energy (−3.301319) differs from the cold notebook-formula/SCIP optimum by `+0.0000255081435356` (calculated minus published). Intriguingly, the **published SA** N=20 energy is −3.301293 (Table VI), numerically close to our SCIP result; this resemblance **does not demonstrate** a typo, nor prove which source configuration was used for the paper. Applying published weights instead changes energy by approximately −0.172321 relative to the published SCIP figure. Published source instance coefficients, versioned cache, and original OMMX solver output are required to assign a cause.

These values are now frozen as **notebook-derived fixture canaries** in the test, distinct from the paper's reported figure. They are not assertions that changing the weights is scientifically justified.

## New discrepancy: Table III AHP matrix does not generate Table IV priorities

**Source:** the previous manuscript, page 4, Tables III–IV; this source is user-provided and *not committed to Git*. `tests/test_paper_ahp_consistency.py` manually transcribes the tables so its computations are independently rerunnable. No assertion is made about the unavailable raw expert questionnaires.

The Table III main-criteria pairwise matrix is

```text
         A       B       C       D
A        1       4       6       8
B       1/4      1       3       5
C       1/6     1/3      1       3
D       1/8     1/5     1/3      1
```

The standard principal-eigenvector method on *this printed matrix* yields:

| Main criterion | Principal-eigenvector priority | Table IV global subcriteria subtotal |
|---|---:|---:|
| A pollution capture | 0.61697535 | 0.552191814 |
| B aquatic stress | 0.22831938 | 0.268830225 |
| C hydrodynamic vulnerability | 0.10461009 | 0.130782272 |
| D operational accessibility | 0.05009517 | 0.048195690 |

The principal eigenvalue is **4.147126421479674**, giving CI = (λmax − 4)/3 and **CR = 0.0544912672146942** when the standard RI(4) = 0.90 is used. The manuscript instead reports **λmax = 4.2207** and **CR = 0.0817**, and both pass its CR ≤ 0.10 rule.

**Reconstructed arithmetic:** Taking the *published Table IV main weights* and calculating the mean of `(A @ w) / w` gives **4.220685443420795** and **CR = 0.08173534941510918**. These round to the paper's reported λmax and CR. Thus the reported consistency statistics can be recreated *from the reported weight vector* even though that vector **is not** the principal eigenvector of the printed matrix. The 2×2 local judgments do reproduce the paper's within-pillar 1:1 and 2:1 splits. The original derivation/aggregation of its four main priorities remains unverified.

**Counterfactual N=20 optimization:** Applying the eigenvector-derived eight-factor weights from the *printed Table III* to the same committed dataset yields **SCIP optimum −3.629863700075275**. Independent exhaustive enumeration agrees, and local selected candidates remain **[0,1,3,6,7]**, with 15 fixed stations. This is a *new sensitivity scenario*, **not** a reproduction or retraction of the reported Table IV method. In the three tested weight scenarios, candidate choices happened to remain stable; this does not establish geographic or methodological robustness outside N=20.

This should **not** be silently "corrected" in the notebook or Streamlit model. Options for the research team to resolve: obtain the actual elicitation matrix or original weight computation, document the intended weighting algorithm, and issue a carefully labeled manuscript correction or alternative sensitivity scenario if warranted. Existing numerical baselines remain preserved.

## Reproducible method and pass/fail meaning

Run from repository root on the branch, with Python 3.12:

```sh
python -m pip install "numpy>=2,<3" "scipy>=1.11,<2" "shapely>=2,<3" "pyscipopt>=5,<7" "pytest>=8"
python -m pytest prototypes/streamlit_water_quality/tests/test_n20_reference.py -q -s
```

The test runs **three** cases: **notebook-code weights**, **paper-reported Table IV weight sensitivity**, and **Table III eigenvector weight sensitivity (counterfactual)**. For each it:

1. Reloads the committed GeoJSON from disk; reconstructs utility, existing/fallback station selection, water mask, hex-pool snapping, FPS and coefficients using the original notebook Cells 2–4 as the specification, **without calling the pilot's reconstruction or feasibility functions**.
2. Asserts that the pilot's free and fixed master indices (zero-based GeoJSON feature positions), utilities, complete linear coefficients, all nonzero free-free interactions, neighborhood graph, fixed neighbors and D_max equal the independently reconstructed arrays.
3. Exhaustively enumerates all `C(20,5) = 15,504` subsets, independently checks each connectivity condition and evaluates linear + quadratic energy.
4. Runs the real PySCIPOpt optimizer and requires proven `optimal` status, feasibility, correct budget, and energy equal to the brute-force global minimum with absolute tolerance `1e-7`. Tied optimal site sets are permitted.
5. Emits lines beginning `N20_VALIDATION ` with source SHA-256, environment versions, settings, site identifiers, coefficient count, solution, reference optimum and **non-equivalence-labeled** delta from the published energy.

The existing PR #14 SCIP tiny-model tests remain separate: they prove elementary solver/linearization behavior, not notebook instance construction. The new comparisons can detect changes to source weights, site ordering, utility calculation, interactions, connectivity or solver output.

**Acceptance boundary:** These passing tests establish internal notebook-formula ↔ pilot-model agreement on a cold N=20 build and independently verified optimum. It does **not** establish that the uploaded paper was produced with those data, source revisions, station positions or weight vector, nor that the original JijModeling/OMMX notebook environment was rerun. Research claims need additional provenance for the paper's original inputs, cached instances, outputs, and original solver environment, and a user-supplied live Streamlit N=20 result (including its settings).

## Review and deployment safety

This development branch starts from `plugin-water-scip-regression` (PR #14 head). The new PR targets that **non-live** branch (stacked), not the active `plugin-water-streamlit-pilot` deployment branch. No source notebook or data are rewritten; no Streamlit UI code or solver math is changed. No merge into the live app without explicit user approval.
