# Independent N50/N100 emitted-LP and HiGHS bound gate (M1)

This is a review-only scientific add-on stacked on draft PR #140, which itself is stacked on #131. It does not modify source data, notebook, N20 solver or Streamlit UI. No merge or deployment is authorized.

The standalone verifier first verifies the checksummed ZIP / source model, parses the **actual emitted** SCIP CPLEX LP without using the SCIP parser, and compares *every* term and constraint with the source's IEEE-754 hex-float formulation: 15-significant-digit decimal LP objective, all binary variables/bounds, exact K, N local one-hop rows, and 3 product linearization rows per quadratic coefficient. Unknown/changed rows fail closed. Next, it solves **those parsed LP coefficients and rows** as a fresh SciPy HiGHS MILP, requiring independent optimal solver status and matching primal and dual bound, K, source objective and candidate graph witness.

The HiGHS result is a **computational second-solver corroboration**, not a signed formal proof or trusted attestation. SCIP LP serialization rounds source coefficients, and the two original algorithms work at numerical tolerances. It is not paper-matching validation: the original source notebook's AHP weights and road-based D2 do not match the paper's WorldPop-based description, and no QAOA/quantum hardware/field telemetry is executed.

To verify a complete downloaded source artifact containing index.json and its N50/N100 ZIPs:

```bash
python -m problems.water_quality.independent_lp_bounds original-artifact.zip --seconds 20 --output independent-highs-bounds.json
```

Dedicated CI generates fresh source-backed N50/N100 SCIP artifacts, then runs the full source/LP/HiGHS check, adversarial mutation tests, and uploads the resulting receipt for human inspection. No objective/runtimes are hardcoded as a purported experiment. CI output is short-retention engineering evidence, not a durable scientific data archive.

**Next gates:** reviewer acceptance; archive under an approved scientific preservation policy; separate source-linked read-only cross-N objective display from verified receipts, with no solver running on UI rerenders; scientific independent repetitions with environment/paper/input reconciliations before any substantive scaling claims.
