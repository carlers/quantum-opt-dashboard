# Issue #108 — Stage 6: installed qopt.core import provenance (review only)

**Parent:** DRAFT #113, verified, unmerged source HEAD
`21e5108de40b6f8e4dd06a5c445bc4d8562ed6c1`. Historical
independent scientific DRAFT #96 remains an isolated pinned cold checkout.
This stage is a new child DRAFT, not a merge, deploy, or preview change.

## Scoped change, no framework source rewrite

The root `quantum-opt-dashboard-ui-imports` package was already installed
with `python -m pip install -r requirements.txt` (or `pip install -e .`
in narrower synthetic CI). Its explicit setuptools package layout now maps
`qopt` and `qopt.core` to their existing `framework/python/qopt` source
location. This installs the existing *source* module paths without copying or
editing `framework/python/qopt/core/*.py`. This is **not** an assertion that
the separate full `framework/python/pyproject.toml` project—with its
API/worker/server dependencies and a different distribution metadata owner—
is installed or safe to co-install. Avoid blindly installing both editable
distributions under the same namespace; choose one governed package ownership
model before production packaging.

The synthetic `problems/evacuation_centers/bundle_runner.py` and
`prototypes/streamlit_configurable/app.py` both already import qualified
`qopt.core.experiment_bundle`, `qopt.core.binary_quadratic` and
`qopt.core.math_ir`. Their sole remaining framework
`sys.path.insert(0, ROOT/.../framework/python)` statements are now
**removed**, and unused `sys` and runner `REPO` symbols are removed.
All direct CLI invocations continue to require the documented editable
package installation. No fallback import aliases, process-wide locks or
racy path-snapshot restores are introduced.

## Evidence and negative controls

Fresh subprocess Python `-I` tests start outside the repository and
verify installed `qopt`, `qopt.core.experiment_bundle`,
`qopt.core.binary_quadratic`, `qopt.core.math_ir` resolve to the exact
expected checked-out source files **without adding the framework directory
to global `sys.path`**. Injected malicious unqualified bare
`experiment_bundle`, `binary_quadratic`, and `math_ir` Python files and
`sys.modules` aliases must not affect `qopt.core` resolved function
identities. The real routed Streamlit navigation provenance test asserts the
same three installed package module origins after reaching the configurable
page. Existing synthetic, water reference bundle and full domain/SCIP CI
continue testing the real supported standalone execution paths.

A passing test does **not** prove isolation against an attacker able to
modify `sys.modules['qopt']` or `sys.modules['qopt.core.*']`, hijack a
qualified namespace, execute process-global import hooks, or mutate package
files. This is module-origin review evidence, not a cross-user security
sandbox. The Python 3.12 pip freeze is observational, not a native wheel
lock, guaranteed reproducible coefficients or certified supply chain.

## Still open for separate review

- Unified `pages/water.py` and `pages/custom.py` still prepend page
  folders and run `runpy.run_path`. Research QUBO page still prepends the
  water source directory. The pinned water backend continues using bare
  `model` / `qubo` / `wireless_topology` / `mvp_audit` module names.
  Migrating that entire graph at once without breaking actual standalone
  entrypoints, class identities, or independent old model SHA requires its
  own bounded review and new exact-head original-science execution.
- Two overlapping Chromium local browser contexts were observed in
  DRAFT #113, but no malignant qualified-name collision under a truly
  adversarial concurrent Session A/B, no actual shared SCIP load/CPU memory
  quota proof, no Cloud preview browser download, and no signed provenance.
- No author notebook, 5,417-feature source GeoJSON, factor S4 dataset,
  manuscript, original pinned water SCIP/graph compiler, independently
  verified DRAFT #96 ancestry or production code is modified.
- Original historical one-hop local N20/K5 source has 1,077/15,504
  feasible; separately modeled all-15-fixed exploratory global graph
  has 860/15,504 feasible, full membership SHA
  `3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40`;
  optimum indices [0,1,3,6,7]. Separate observed original source
  IEEE754 exact objective SHAs `2b238848...` and `8536a3db...`
  must remain **distinct**; observed UI numerical similarity is not an
  exact model identity certificate. AHP D2 road vs manuscript WorldPop
  parity, lake field RF/backhaul/current/DO, and quantum advantage are
  **not** verified. OpenJij SA is classical.

## Required exit checks

Before claiming this stage reviewed: run Python 3.12 actual install,
`pip check`, `python -I` negative tests, routed module origins, full
unified and dedicated configurable/evacuation/water adapter regression,
full SCIP/Streamlit pilot, separate pinned cold source-science/UX workflow,
and the locally scoped two-real-Chromium-session job on this exact
source PR HEAD. Record synthetic CI merge checkout SHA **separately**.
GitHub artifact digests are short-lived observations, not externally
download-verified or institutionally archived proofs.

**No merge, preview, staging, public deployment, signer/KMS or original
scientific data/paper modification is authorized by green checks.**
