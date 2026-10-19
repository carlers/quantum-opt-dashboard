# Source-derived N20 feasible-set certification — scoped review addendum

**Review-only draft stacked on [PR #56](https://github.com/carlers/quantum-opt-dashboard/pull/56).** No original archived notebook, GeoJSON, lake factor, candidate order, hull predicate, objective, SCIP constraint, solver setting, or published paper value is modified.

## Why

The clean notebook already enumerates exactly **15,504** local N=20/K=5 choices, verifies SCIP `optimal` and independently evaluates original objective for selected sites. However it previously only asserted the **best** solution; a changed one-hop adjacency graph could leave the same winner while introducing or removing other feasible site groups. Existing independent historical frozen-B x-only review reports **1,077 feasible** source-derived K5 combinations. This addendum makes the size and *complete ordered membership* of the feasible region machine-verifiable.

## Exact bounded certificate

During the notebook's existing lexicographic `itertools.combinations(range(20),5)` traversal, for each selection satisfying the **unchanged local one-hop test**, increment `feasible_count` and update SHA-256 with comma-separated local indices followed by **one ASCII newline byte**. Source-derived expected feasible count is **1,077** (not global connectivity or empirical publication parity); record its observed SHA, not an invented fingerprint.

The fresh-kernel runner independently enumerates all 15,504 combinations **from the notebook-emitted fixed flags + free adjacency**, recomputes count and per-subset hash, compares to the notebook report, then asserts the established 1,077 canary. A checker failure blocks the review. An otherwise identical synthetic objective whose unselected station gets an extra fixed neighbor is tested: the chosen optimum still passes original energy/feasibility, but the complete feasible-region certificate fails. Another test verifies a one-character hash tamper; duplicate selected local positions are rejected.

These are **two verifications of a recorded graph**, not an independent re-derivation of the graph from original geospatial geometry; the source archive's unchanged SHA and actual cold notebook execution are still required. This certificate is not universal proof of 2000-site cases, published Table V, actual quantum hardware or original source model intent.

The original `model_input_sha256` remains **byte-exactly scoped to the same mathematical model fields**: extra feasible count+hash are *result evidence*, outside `MODEL_INPUT` and its digest. Note: downstream PR #57/#61/#63 may need intentional schema revalidation before stacked merges; this isolated reviewer branch avoids editing those draft heads.

**Acceptance:** isolated [Clean N20 notebook scientific replay](../.github/workflows/notebook-n20-replay.yml) passes a fresh kernel plus actual SCIP, exact 15,504 exhaustive test, 1,077 feasible-set canary and all adversarial manifest tests. No `main`, preview or production change. **Next steps:** review generated fingerprint/CI, confirm scientific meaning of local adjacency with authors, then decide whether to incorporate the guard into maintained N20 notebook PR #56 during an owner-approved merge plan.
