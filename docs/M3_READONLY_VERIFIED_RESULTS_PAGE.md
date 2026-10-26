# Review-only Streamlit display of one verified N50/N100 CI execution

This UI PR is stacked **on #139** (read-only N20/50/100 candidate selector), distinct from the source-science solver/LP/report PRs **#140 → #141 → #142**. It is a narrow display gate, not a scientific merge or deployment approval. All research source and original N20 code/data/notebook remain unchanged.

## Provenance and interpretation

`prototypes/unified_dashboard/data/reviewed_n50_n100_2026_10_26.json` is a **frozen summary** of the **successful source-bound M3 research workflow** [GitHub Actions run 40305459517](https://github.com/carlers/quantum-opt-dashboard/actions/runs/40305459517), [source and HiGHS artifact ID 12642311053](https://github.com/carlers/quantum-opt-dashboard/actions/runs/40305459517/artifacts/12642311053). The original downloaded GitHub Actions artifact ZIP SHA-256 is `c0fff39780dc21a42e1de14c126cde7adda16e28ca37d25a38b156497800deb2`; the source GeoJSON SHA-256 is `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`. Original source model and emitted LP SHA-256 identifiers are retained for each N. The reviewed original CI artifact contains source coefficients, solver ZIPs, actual SCIP LP export, independent HiGHS optimal primal/dual results and cross-N embedding checks. GitHub retention is **14 days**, so the CI artifact **must be deposited in a durable scientific archive** (appropriate license/institutional policy) before publication. The committed JSON alone cannot replace an original LP or its full CI execution record.

The independent scientific background appears in #140, #141 and #142; the snapshotted observation values are **not** rerun on each UI page render. On UI entry, the app recomputes the **original numerical objective** of each recorded selection from the still-pinned GeoJSON and nested model (and compares selection identities, one-hop feasibility, budget, native source objective and selected feature positions). It verifies the pinned Git blob SHA of the reviewed JSON, source data SHA and exact original artifact ID/SHA. It does **not** independently replay HiGHS on page load; the independent bound is explicitly described as **archived, solver-produced** evidence. All expensive SCIP/HiGHS work is offline-only.

Read-only route: `pages/verified_results.py` → `prototypes/unified_dashboard/verified_results.py`. It lists two observed original local-model objectives, their SCIP status/HiGHS dual bounds, a two-point scatter chart (no extrapolating trend), archived selected sources on a map, precise source and LP identifiers, and separately scoped measured source-build/SCIP-call/worker wall times. N20 remains a **separate pinned reference** and original N20 SCIP solver remains in the main water page. The N50/100 candidate explorer also remains read-only and must not show blue selected locations until you enter the **separate** archived results page.

### Scientific limits

- One CI execution with exactly N50 and N100, K=5 and 15 original marked fixed source stations. Not randomized repetitions, a runtime scaling benchmark, quality-estimation uncertainty, or a master N=5417 optimum.
- Uses **notebook weights, road-based D2 and historical local one-hop**; published paper's differing AHP/WorldPop D2 and historical Table V–VII remain unreconciled.
- SCIP status + HiGHS primal/dual agreement constitute computational corroboration only, not a formal signed optimality proof, quantum run, real radio coverage, or physical water-monitoring validation.
- Source feature *array positions* and GeoJSON property IDs are different identifiers; only source positions are used here.
- No Streamlit background solver run, auto-solve on navigation, sessions sharing another user's ZIP, live scientific benchmark, production deployment or merge is authorized.

### Review checklist

1. Verify the frozen source CI artifact ZIP SHA-256 matches the recorded digest; examine original LPs, independent HiGHS receipt and cross-tier embedding, and arrange durable archival preservation.
2. In CI run the full unified-page navigation, original pinned N20 SCIP attestation, verified-results source validation and tamper tests, and N50/N100 candidate-only controls.
3. Confirm map selected source positions and archived numerical values, N20 state isolation and absence of any live solve button in the results page.
4. Obtain explicit approval before integrating the stacked PR into `preview` or `main`. This PR does not itself authorize publication or cloud deployment.
