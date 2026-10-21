# Issue #108 — Stage 3, synthetic runner qualified leaf import (review-only)

Review-only child of green DRAFT #110 source HEAD
`ce435b02034d09f8a0197aa5d0b1810ce531b602`.
Original pinned DRAFT #96 remains a completely separate independent
scientific source checkout. No merges or deployment.

## One exact transition

The synthetic-only `problems/evacuation_centers/bundle_runner.py`
previously imported `synthetic_reference` using an unqualified global name,
after locally inserting framework import paths. It now imports
`problems.evacuation_centers.synthetic_reference` explicitly. Two trivial
`__init__.py` package anchors were added in `problems/` and
`problems/evacuation_centers/`, and `pyproject.toml` now packages
those namespaces in the root editable distribution already introduced in
Stage 2. The actual scientific/synthetic math in
`synthetic_reference.py` and its fixtures remains byte-for-byte unchanged.

### Regression design

- `python -I` launches from a non-repository temporary working directory,
  with a malicious unqualified `synthetic_reference` both in a higher-priority
  import directory and cached in `sys.modules`. The new qualified
  import must resolve the correct on-disk `synthetic_reference.py` with
  identical `SyntheticProblem` and oracle identities inside `bundle_runner`.
- An actual **standalone CLI execution** runs the unchanged capacitated
  synthetic evacuation fixture with `python -I` using the original
  `--bundle` / `--output-dir` flags from that separate working directory.
  This tests the installed package and file-path CLI behavior, not only
  `pytest` import context.
- Existing configurable UI/evacuation/domain tests, exact SCIP/Streamlit
  pilot, Python 3.12 install/runtime, and separately pinned original N20
  notebook/SCIP/GeoJSON/S4/graph scientific workflow must all complete
  successfully on this stage's **exact PR HEAD**.
- The original independent science/UX workflow now watches changes to
  synthetic runner package/entrypoint files too, so a source-science run
  is not incorrectly inherited from a previous PR head.

## Boundaries not yet repaired

The runner continues to modify `sys.path` for framework dependencies,
and its *lazy water-quality adapter* still uses a bare module import and
path mutation. The configurable editor's other imports, unified water
and custom wrappers, research QUBO page and pinned water solver/attestor
remain unqualified. This leaf migration cannot certify two overlapping
Streamlit browser sessions; a poisoned *qualified* module is also
outside this negative test's trust model. No unsafe path snapshot reset
or global SCIP lock was added.

Historical notebook mathematics: local one-hop N20/K5 1,077 of 15,504
feasible; separate exploratory all-15-existing-fixed global graph
860 of 15,504 feasible with full set SHA
`3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`,
selected `[0,1,3,6,7]`. Distinct observed strict binary64 objective
SHA `2b238848...` and `8536a3db...` must not be cache-interchanged.
Manuscript expert AHP/D2 WorldPop parity, field water DO/current/RF/backhaul
and quantum advantage are unverified. Classical OpenJij is not quantum
hardware.

No original source notebook, source GeoJSON, published manuscript,
original water compiler, independent scientific PR #96,
`main`, `preview` or deployed Streamlit environment altered.
The next review-only draft must address the remaining water adapter
and qualified multi-route import graph with stronger concurrent tests.
