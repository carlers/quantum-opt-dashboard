# N20 independent-penalty classical SA: first bounded smoke receipt (2026-10-26)

**Status:** A single engineering CI execution; **not** a preregistered inference, selected optimal penalty, paper input reproduction, or quantum run. Historical GeoJSON pinned at SHA-256 `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7`, K5 and 15 real existing stations, source notebook weights and road-based D2, original local one-hop graph.

**Source execution:** [GitHub Actions 40310924008](https://github.com/carlers/quantum-opt-dashboard/actions/runs/40310924008), [artifact 12644482040](https://github.com/carlers/quantum-opt-dashboard/actions/runs/40310924008/artifacts/12644482040) (GitHub retention 14 days). The separately downloaded artifact SHA-256 was `36567db268af664f34ca2a8463fbe2c9a63c333c081520d70622ffa148ffb1ac`. Its source model SHA-256 is `623821676fc170e68beeb8e83aee28c641f39cbd936ea456b700ea19518f42c2`; all three file SHA-256 values in `SHA256SUMS.json` recomputed successfully. CI used OpenJij **0.12.2**, classical SASampler, 40 sweeps, parents [270010001,270010002], and independently derived child seeds for each grid coordinate and read. **72 distinct one-read seeds, 72 original+auxiliary sampled bitstrings and 18 parent-cell trial summaries** were captured; no rows dropped for infeasibility.

**Grid axes, source-derived:** notebook local-row-sum heuristic = `1.0978196676270329`; exploratory midpoint = `12.92646186401367`; global sufficient bound = `24.755104060400306`. Budget and connectivity penalties vary **independently**. Per cell, the observed feasibility numerator is out of **8** sampled configurations (2 parents × 4 one-read calls).

| Budget penalty \ Connectivity penalty | Local row-sum | Midpoint | Sufficient global |
| --- | ---: | ---: | ---: |
| **Local row-sum** | **4/8** | **2/8** | **0/8** |
| **Midpoint** | **2/8** | **6/8** | **4/8** |
| **Sufficient global** | **0/8** | **2/8** | **5/8** |

All cells reported **0/8 exact N20 SCIP optimum hits**. This does not mean any penalty is better or worse generally: the samples and sweeps are intentionally tiny, with no uncertainty interval, preregistered replicated study, or statistical comparison. In particular, a *theoretically sufficient* penalty means a global QUBO optimum can preserve feasibility (given a feasible constrained model); it does **not** mean this bounded OpenJij SA run will usually find a feasible state.

The code independently checked each sampled OpenJij QUBO energy and offset against expanded and unexpanded source/slack-squared formulas; checked local one-hop and budget feasibility against source bits; and refused feasible solutions that beat the pinned N20 exact optimum `−3.3012934918564643`. No source notebook, data, fixed N20 solver logic or Streamlit files changed.

**Next gate:** license/provenance-approved durable preservation of the full sample archive; predeclare a scientifically adequate parent-block replication plan and statistical endpoints **before** running a large batch. Repeating these original two seeds is replay, not independent replication. Historical paper AHP/WorldPop differences and QUBO conversion equivalence are unresolved, and no QAOA/SQA/hardware or physical monitoring claims are made.
