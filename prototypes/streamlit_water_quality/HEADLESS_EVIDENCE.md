# Headless N=20 SCIP evidence (no manual Streamlit interaction)

This experiment bundle is a **machine-generated baseline for the committed
notebook-derived Streamlit pilot**, not a reconstruction of the unpublished
historical input snapshot underlying the paper's reported optimal energy.
It preserves the source notebook, GeoJSON, solver, and deployed UI unchanged.

## Verified automated run

- [PR #17](https://github.com/carlers/quantum-opt-dashboard/pull/17) provides the executable implementation.
- [GitHub Actions run 39072903613](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39072903613) passed **17 tests**, including three SCIP + exact enumeration export scenarios.
- [Download archived JSON/CSV evidence](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39072903613/artifacts/12115499202) (GitHub-generated artifact, 14-day retention). The ZIP includes all three scenario directories and `manifest.json`.
- Results are auditable against source checksums and the supplied prior paper, but **are not the historical paper's raw experimental artifacts**.

## Execute locally or in GitHub Actions

Run from the repository root using Python 3.12 and SCIP dependencies:

```sh
python -m pip install "numpy>=2,<3" "scipy>=1.11,<2" "shapely>=2,<3" "pyscipopt>=5,<7"
python prototypes/streamlit_water_quality/evidence.py --output-dir /tmp/n20-scip-evidence
```

This builds and solves all three N=20, K=5 scenarios with the existing
`model.py` implementation, requires a **proven optimal** SCIP outcome, and
independently enumerates all 15,504 possible five-site subsets to verify
the same optimum and local budget/connectivity constraints. An infeasible
or merely time-limited incumbent causes failure. No Streamlit account,
manual button press, or deployed app access is required.

The automated `Streamlit water-quality pilot` GitHub Actions job also runs
the CLI on every PR touching `prototypes/streamlit_water_quality/**` or
its scoped workflow and uploads artifact **`n20-scip-evidence`** (14-day
retention). Go to the PR → Checks → successful workflow → Artifacts.
It contains this structure:

```text
manifest.json
notebook/
  config.json
  instance.json
  result.json
  sites.csv
paper-table-iv/
  config.json
  instance.json
  result.json
  sites.csv
table-iii-eigen/
  config.json
  instance.json
  result.json
  sites.csv
```

`config.json` records exact factor weights, model constants, source file
paths and SHA-256 checksums. `instance.json` records candidate and fixed
GeoJSON *feature positions* and *property IDs* separately, projected
EPSG:32651 coordinates, utility, exact linear and free-free pairwise
coefficients, all local neighbor links, fixed neighbors, and the
connectivity threshold. The instance SHA-256 is taken over canonical JSON
using sorted keys and compact separators, with a trailing newline.

`result.json` includes SCIP status, optimality, gap, solver runtime,
selected positions and IDs, objective decomposition, independent budget
and one-hop connectivity checks, exhaustive-enumeration optimum,
provenance versions, and the source code SHA when available. The
published paper's energy and local indices are clearly marked as
**non-equivalent historical comparison references**.

`sites.csv` is a human-readable table of all 20 N=20 free candidates
and their selected flag, master feature position and optional property ID,
projected location, utility, linear coefficient, and graph degrees.
`manifest.json` records the SHA-256 of every exported JSON/CSV file;
a changed file will no longer match its hash.

## Scenarios

| Scenario ID | AHP weight source | Cold-build SCIP energy (2026-10-18 baseline) |
|---|---|---:|
| `notebook` | Hard-coded code weights from notebook Cell 2 | −3.3012934918564643 |
| `paper-table-iv` | Paper's Table IV weights applied to committed data | −3.473640036773477 |
| `table-iii-eigen` | Counterfactual eigenvector from the paper's printed main AHP matrix (Table III) | −3.629863700075275 |

All three select local candidate positions `[0,1,3,6,7]` in this
fixed N=20 cohort and use **15 real stations already flagged in the
committed GeoJSON**. These facts are backed by exhaustive enumeration
and PySCIPOpt tests, not claims about the paper's unseen cached inputs.

## Explicit limitations and next gates

- The deployed Streamlit app has **not** been executed or inspected by
  this runner. The automated evidence is generated against the same
  pilot `model.py`, not an independent production-service evaluation.
- Original JijModeling/OMMX solver, paper-era AHP elicitation and
  original cached MIQP input files are not present here. See issue #16.
- The paper calls D2 *population exposure*, but the code and dataset
  use road proximity. This is an unresolved feature semantics conflict;
  exported factors are labeled with their actual code names.
- Hashes capture source/config/coefficients, not guarantees that two
  independent environments generate bit-identical floating-point
  results. Runtime and SCIP version must also be inspected.
- JSON/CSV output includes no geospatial WGS84 conversions, only
  EPSG:32651 input coordinates. Use an explicit coordinate transformer
  when mapping them.
- `SCIP time_limit_s` is reported separately from actual elapsed
  time. Optimality is never inferred from a small numeric gap alone.
- No original code, deployed branch, or production resources are modified
  by running the evidence builder.

### Test commands

```sh
python -m compileall -q prototypes/streamlit_water_quality
python -m pytest prototypes/streamlit_water_quality/tests -q -s
```

A valid result needs all CI tests and the evidence upload step passing.
