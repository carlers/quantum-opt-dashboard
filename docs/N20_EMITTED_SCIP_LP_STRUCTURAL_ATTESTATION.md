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

- [x] Initial exact executable-code/docs HEAD pilot+actual Streamlit AppTests and independent pinned original cold source triple-checkout passed; final documentation-only checkpoint CI still to be checked.
- [x] Every expected N20 local original constraint+binary variable was independently parsed from *real emitted SCIP LP*, and adversarial linearization/budget/neighbor/objective/variable mutations were rejected.
- [x] Genuine SCIP flat-objective LP is supported and validated; near-optimum solutions remain subject to the separate exact-rational verifier.
- [ ] No modification/merge of original notebook/dataset/manuscript, main, preview or production and no human publication/physical validity claim.

**Follow-on:** independent human scientific reviewer inspects LP text grammar limitations and float64/decimal boundary, assesses signed per-run SCIP execution and LP/method provenance, and separately approves any final app/science integration/merge/deployment. Do not treat this mathematics-only draft as field-ready monitoring instrumentation.


## First independently executed results — 2026-10-20

At first implementation/documentation SHA `d80bc2edffbb8beef12323e0d052172e7ee15c98` the full required workflow triad independently succeeded:
- [Streamlit pilot #39400327388](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39400327388) **SUCCESS: 111/111 tests** in 19.41s, including actual PySCIPOpt-executed original LP capture, 11 LP-specific adversarial/flat-objective tests, existing real local/global Streamlit result/ZIP/map tests, and independent all-original-fixed network canary `860/15504`, original source local `1077`.
- [Unified dashboard #39400327386](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39400327386) **SUCCESS** with navigation, editor and domain solver regression.
- [Independent triple-checkout science #39400327424](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39400327424) **SUCCESS: 24 targeted real-attestor/Streamlit tests** in 10.42s, plus completely fresh pinned original source notebook/real SCIP, raw 5417-point GeoJSON and S4, separate scientific claim gates, independently rebuilt full 35-node all-15-mandatory-fixed graph, exact global math and existing pinned original UX source-compiler identity. Source global membership SHA `3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`, selected `[0,1,3,6,7]`; source and separate UX exact objective SHA were `2b238848f43d1763fe093b38360941677e2fa46f1a6c01d05b5b359a62dc5809` *in this execution only*. Different historical `8536a3db...` scoring SHA variants are still distinct identities.

The real N20 example emitted an LP with **20 binary x variables**, **12 binary pair-product p variables**, and **57 distinct verified named constraints**: one budget, 20 site-neighbor and 36 three-row pair-product inequalities. Other source/weights may alter the number of pair terms and LP constraints; the parser derives expected numbers from the ACTUAL current compiled instance rather than hardcoding 12 pairs.

[Research artifact #12254442672](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39400327424/artifacts/12254442672), GitHub-provided SHA-256 `140718573bafbf2c7df7e811a9c8899b5d1efdde76652b1e0d6241babe4868c7`, expires **2026-11-03 09:24:51 UTC**; content limited to independently executed source/UX JSON research, not author DOCX or licensed additional GIS data. GitHub expiry requires owner/institutional long-term archive handling.

**Still missing even after these passes:** independent authenticated SCIP optimization process/status/gap record, original MILP solution trace and external signed session source, scientifically justified paper AHP/D2 criteria reconstruction, surveyed actual Laguna de Bay waterbody and field radio/backhaul/water-quality calibration. The LP structural attestor does not establish any of those and never upgrades claim status on its own. Both science and UX PR histories remain review-only drafts and unmerged.