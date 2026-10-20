# First independent structural audit of the emitted original N20 SCIP LP

**Date:** 2026-10-20. **Review-only draft** based on UX mathematical verify-before-render [DRAFT PR #97](https://github.com/carlers/quantum-opt-dashboard/pull/97). The separate scientific source verification chain through [DRAFT PR #96](https://github.com/carlers/quantum-opt-dashboard/pull/96) is **not merged/rebased/imported**. Original GeoJSON, archived author manuscript and notebook are not edited.

## What can actually be proved from original SCIP LP text

Source UX `model.solve_scip()` compiles a nonnegative pair-product binary MILP via PySCIPOpt, exports the **untransformed** original CPLEX LP (`Model.writeProblem(..., trans=False)`), then calls `optimize()`. Previously `runtime_attestation.py` separately proved bounded N20 mathematical feasibility and the exact binary64 objective minimum, and verified the ZIP contained the actual LP bytes. **It did not parse the LP file's constraints**: a read-only problem file with a missing edge/altered budget could have slipped through if an untrusted component supplied consistent bytes and ZIP hashes. The new draft adds an independent limited-syntax LP structural checker as another required mathematical evidence gate.

`prototypes/streamlit_water_quality/scip_lp_structure.py` parses the observed, bounded *ASCII CPLEX LP emitted by the pinned SCIP writer*; checks the expected ordered Minimize, Subject to, Bounds, Binaries and End sections; refuses unknown, duplicated or omitted rows, binary declarations and bounds; and derives from the CURRENT compiled original 20-candidate N20 `Instance`:

- Every site-selection binary `x0...x19` and every pair-product binary `p{i}_{j}` is present and bounded [0,1], without additional or repeated variables.
- The exact original `budget: sum(x_i) = K` equation.
- All 20 named original one-hop rows `connect_i: x_i - sum(x_j for j in N_i) <= f_i`, including the actual original fixed-station neighbor flag and all candidate neighbor indices.
- Every quadratic `p{i}_{j}=x_i*x_j` represented by **exactly three** familiar binary McCormick/AND inequalities (`p>=xi+xj-1`, `p<=xi`, `p<=xj`), not a relaxed alternative or a forged operand.
- Every original linear site score and quadratic pair penalty in the LP objective, at the **SCIP text-writer's 15-significant-digit decimal serialization**.

The LP decimal coefficients are **not exact float64 coefficients**. The active compiled `Instance` and `model.json` still carry full `float.hex` binary64 coefficients verified by `runtime_attestation.model_identity()`, and the separate exhaustive independent rational objective attestor still orders solutions **bit-exactly**, without accepting a near-optimum within the LP print/score tolerance. The LP parser proves the emitted text's *formulation compatibility*, not the exact mathematical equality of arbitrary decimal and binary64 encodings. The parser requires the known original N20 binary MILP grammar and fails closed on foreign native quadratic, nonbinary, unknown LP section or malformed serializations.

`runtime_attestation.inspect_archive()` now *parses* that same byte-verified local SCIP LP before any current selected map/table/ZIP is accepted into the app state, and puts the LP SHA and bounded full formulation certificate inside the on-solve attestation SHA. New `tests/test_scip_lp_structure.py` independently calls **real PySCIPOpt** to export the actual N20/K5 original LP and challenges altered budget RHS, original source graph adjacency, 3-row product bounds, objective decimal, binary bounds, extra variables/constraints and a flat nonnegative objective.

### Evidence and trust limits

This checker independently parses one **provided** LP export from the backend; it **does not cryptographically prove SCIP actually optimized the same submitted file**, authenticate SCIP's underlying compiled internal constraint graph, read/verify a full SCIP process log, or provide a mathematical dual MIP-bound/gap optimality certificate. The independent exhaustive N20 enumeration proves the selected optimum *for the separately compiled model* and validates the LP's consistency with that model, but not independently observable external process execution. SHA of a ZIP or session object is not a signed provenance root and does not defeat an attacker who controls all backend process memory. No actual quantum hardware is asserted.

Source N20 local one-hop original computational regression has 1,077 feasible K5 subsets; distinct exploratory all-15-original-fixed geometric global network has 860/15,504 and 17 new fixed/fixed proxy edges. **Global mode uses exhaustive graph enumeration, not SCIP; it intentionally does not export any fictional SCIP LP.** Geometry depends on raw concave hull and original Dmax, not measured radio/backhaul. Manuscript AHP source-D2-road versus WorldPop/population and original author judgment forms remain blocked; physical DO/current/waterbody and RF measurements are absent.

### Review criteria

- [ ] Existing pilot+actual Streamlit AppTests and source independent triple-checkout CI pass at exact draft PR HEAD after LP integration.
- [ ] Every expected N20 local original constraint+binary variable is independently parseable from the *real emitted LP*, and fabricated linearization/budget/neighbor/objective/variable claims fail.
- [ ] Flat-objective (exact tied) SCIP LP remains acceptable, while near-optimum solutions remain subjected to the separate exact-rational score verifier.
- [ ] No modification/merge of original notebook/dataset/manuscript, main, preview or production and no human publication/physical validity claim.

**Follow-on:** independent human scientific reviewer inspects LP text grammar limitations and float64/decimal boundary, assesses signed per-run SCIP execution and LP/method provenance, and separately approves any final app/science integration/merge/deployment. Do not treat this mathematics-only draft as field-ready monitoring instrumentation.
