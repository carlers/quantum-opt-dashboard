# M1 review-only N20/50/100 resolution explorer

Stacked on scientific draft PR #131. The selector is additive to the **existing** Streamlit water page, not a new backend or a change to the frozen N20 solver.

- **N20 default:** all existing K, weight presets, β/δ, local/global graph, independent SCIP/graph verification, attested ZIP/LP and session-state semantics remain unchanged.
- **N50/100:** display-only source-backed candidate maps, 15 existing stations, raw GeoJSON feature positions vs property IDs, historical notebook utility, full SHA-256, N20 ⊂ N50 ⊂ N100 comparison, and CSV/JSON source-manifest downloads. Never show solver controls, optimization results, feasible placements, quantum claims, or invented runtimes in this mode.
- On switching N20 → N50/100, clear `mvp_result` before rendering. Returning to N20 requires a fresh SCIP solve; an old N20 ZIP/LP is never re-labelled as N50/100.
- Historical notebook AHP weights, road proximity D2, fixed-seeded FPS and historical local one-hop geometry are used for **all** generated cohorts. Custom weights / global network solver are restricted to N20.
- `@st.cache_data(max_entries=1)` caches only source-identity-keyed geometry and its deterministic numerical arrays, never SCIP or SA output.

**Acceptance:** N20 regression + unified routing tests, UI candidate-only tests and prior independent source reconstruction CI must pass. This draft does not authorize deployment, merge, scientific endorsement, or extrapolation to N200–2000. Next separate research PR: persisted, independently checked N50/N100 SCIP/batch artifacts with explicit budget, timing scope and solver status; only then interactive cross-N results.
