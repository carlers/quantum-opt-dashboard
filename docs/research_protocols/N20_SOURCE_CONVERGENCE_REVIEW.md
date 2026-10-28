# Draft-only N20 source/science integration experiment — **not a release**

**Purpose:** demonstrate whether three existing, unmerged scientific review lines can coexist in one tree without rewriting original research or silently promoting scientific claims. This is the isolated branch `integration/n20-source-custody-weights-20261029`, based on [executable N20 draft #56](https://github.com/carlers/quantum-opt-dashboard/pull/56). No merge to main or preview is proposed.

## Source lines, expected GitHub integration sequence

| Change line | Reference | Responsibility |
| --- | --- | --- |
| Curated N20 executable notebook, original notebook structural inventory and SciPy/SCIP/scientific result audit | [#56](https://github.com/carlers/quantum-opt-dashboard/pull/56) at `0dfa9018f48487dc021d4b4f9fbf92b09ddff74d` | Review-only **computational** N20/K5 source reference, not manuscript replication |
| New fixed original notebook+GeoJSON SHA256/Git blob manifest + rights-unknown flags | [#159](https://github.com/carlers/quantum-opt-dashboard/pull/159) at `1d624b26aa12f29f69f8010553563f51a81ab152` | Fast **source bytes and metadata** guard, not the source's ownership certificate |
| Clean derived historical/sensitivity weight input audit + AST extraction | [#160](https://github.com/carlers/quantum-opt-dashboard/pull/160), at source `fd67df4f0f0f5b98da63c61b58a880e456584329` | Fast **input provenance and discrepancy** demonstration, not a second exact N20 notebook |
| Integration-only test of all three and expanded N20 CI path filter | This draft only | Detect cross-branch source/weight/CRS/witness drift before separate scientific replay |

The reviewed source/derived files are copied **byte-for-byte from #160**, which already contains #159, into this separate branch. They are not unverified scientific transformations. A subsequent reviewer must **choose an integration merge route**; do not merge #159/#160 and this branch all independently without checking for duplicate changes, stale refs, or overwritten docs.

## One source reference; distinct validation jobs

1. Historical source identity: `scripts/verify_research_sources.py` checks original 25-cell notebook and GeoJSON hashes, Jupyter source shape, Git blob and rights-unknown manifest.
2. Original duplicate-cell map: `scripts/notebook_inventory.py` from #56 reports the two *exactly identical* repeated sections and three similar-but-different variants. It must **not** remove the historical source cells.
3. Historical input semantics: `scripts/historical_weight_contract.py` statically parses only **original notebook JSON cell index 3**, labeled `CELL 2`, to obtain literal `WEIGHTS` and `FACTOR_NAMES` without `exec`, NumPy, QUBO/SCIP, or Jupyter runtime.
4. Curated executable N20 notebook: `water_quality_n20_reproducible.ipynb` preserves exact literal eight-factor inputs and local one-hop constraints. The new `test_integrated_source_science_contract.py` checks its factor names/weights against the original AST rather than a copied canary; it also checks the N20 driver's expected source SHA-256, candidate count and frozen witness.
5. Separate `derived_historical_weight_audit.ipynb` displays the alternate sensitivity weight constants; it cannot reproduce WorldPop, paper AHP elicitation, original dissertation Table V, field data or a quantum result.

## Required same-head CI before review

- `python -m unittest discover -s problems/water_quality/tests -p 'test_integrated_source_science_contract.py' -v` (stdlib input consistency).
- Original source custody and notebook source-audit workflows.
- Derived weight notebook and historical AST mutation tests.
- Existing broad `water-quality` pytest collection.
- **Fresh-kernel N20 notebook + independent 15,504-subset enumeration + SCIP solver**, with strict 16-case model-manifest adversarial tests.

The N20 workflow now triggers when either source-custody/weight parser or integration test changes, not just the large executable notebook. These tests verify **same-source compatibility**, not external custody, legal redistribution rights, full paper-model equivalence, no quantum advantage, or an independent cloud evidence backup.

## Permanent research/open questions

- The historical GeoJSON factor `d2_road_proximity` is not the paper's described WorldPop exposure; paper and notebook weights differ. Follow [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16).
- Float64 binary ABI/cross-host variation remains under [#24](https://github.com/carlers/quantum-opt-dashboard/issues/24); a matching score alone is not a complete scientific certificate.
- Actual original-source rights, authorship and adviser approval are **unverified**.
- GitHub CI artifact retention is not guaranteed two-year off-host preservation. Owner storage account is **PAYG, $0/month**, Option A versioned two-year operational minimum; cloud provisioning and backup uploads stay blocked. Existing original research evidence must not be published casually.
- This branch is **review-only**, creates no OCI cost, does not change the live Streamlit pilot, Mosaic network/VM, `main`, or permanent `preview`, and does not auto-retry remote native SCIP jobs.

Track [integration issue #162](https://github.com/carlers/quantum-opt-dashboard/issues/162), the original source [PR #56](https://github.com/carlers/quantum-opt-dashboard/pull/56), [#159](https://github.com/carlers/quantum-opt-dashboard/pull/159), and [#160](https://github.com/carlers/quantum-opt-dashboard/pull/160).
