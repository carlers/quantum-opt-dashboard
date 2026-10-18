# Replaceable CSV/GeoJSON source adapters and pinned lake reference (draft)

**Status 2026-10-18:** isolated scientific data-interface proposal for [#41](https://github.com/carlers/quantum-opt-dashboard/issues/41). No live Streamlit deployment, no operational hazard/shelter data, no change to the existing manuscript, original notebook or original Laguna de Bay GeoJSON. **The previously verified generic synthetic JSON bundle interface remains available and tested.**

## Data are inputs, not the thesis's fixed identity

A v1 bundle selects a versioned `problem_id`, exact `formulation_id`, relative `dataset.path`, optionally its expected exact SHA-256 and typed `parameters`. The loader constrains sources to **three explicit file extensions**: `.json`, `.geojson` and `.csv`. All use bounded, fail-closed local files: no absolute paths, parent traversal, symlink traversal, source execution, arbitrary online scraping or silent unknown parameter coercion.

| Source | Supported semantic transform | Guardrails |
|---|---|---|
| Synthetic JSON | Existing two evac model variants and generic small binary quadratic (unchanged) | 1 MB limit; explicit synthetic classification; domain-specific strict type checks |
| Synthetic CSV | Explicit **two-column** `variable,linear_coefficient` table → tiny domain-neutral binary optimization with constraint `sum x_i<=K`. Coefficients are objective numeric terms, not scripts | ≤16 binary variables, finite bounded numbers, unique safe IDs, no extra columns or formula execution, independent exhaustive SCIP-vs-enumeration proof. K edited via `parameters.rhs_overrides.budget`; source CSV SHA fingerprinted |
| Synthetic GeoJSON | Original water-quality utility/redundancy/local adjacency solver applied to an entirely fabricated **EPSG:32651** point grid with eight declared factor values and actual synthetic fixed flags | 1 MB size, FeatureCollection, valid finite projected Points, explicit UTM CRS, stable feature property IDs, source-derived one-hop graph; supports weights, beta, delta, N and K |
| Historical Laguna de Bay GeoJSON | **Exactly the original immutable committed** 5,417-feature dataset, N20 notebook weights and existing 15 fixed stations; original validated model/science semantics | Source sha `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7` required explicitly and checked; up to 5 MB only for that one allowlisted input/formulation. Not a broad arbitrary real-data upload permit. Raw lake coordinates excluded from generated run.json, but reference exists in repository |

### How to run each input variant (after checkout of this draft)

```sh
python -m pip install 'numpy>=2,<3' 'scipy>=1.11,<2' 'shapely>=2,<3' 'pyscipopt>=5,<7' 'pytest>=8'
python problems/evacuation_centers/bundle_runner.py \
  --bundle problems/water_quality/reference-n20.bundle.json \
  --output-dir /tmp/water-pinned

python problems/evacuation_centers/bundle_runner.py \
  --bundle problems/water_quality/examples/fake-water-n5.bundle.json \
  --output-dir /tmp/water-artificial

python problems/evacuation_centers/bundle_runner.py \
  --bundle problems/evacuation_centers/examples/generic-csv-linear-bundle.json \
  --output-dir /tmp/csv-synthetic
```

Both the scientific **model choice** and source fingerprint are part of the bundle checksum. Changing a CSV coefficient, GeoJSON feature criterion or weight vector, number of free candidates, budget or problem formulation creates a different content fingerprint. Input validation rejects an attempt to mark a modified synthetic file as the historical research reference.

## Pinned original N20 reference and unresolved publication issues

The original water-quality backend from unmerged science [PR #29](https://github.com/carlers/quantum-opt-dashboard/pull/29) has been copied **with its numerical implementation unchanged** into `problems/water_quality/notebook_reference_model.py` for this independent portability test; it remains separate from the unfinished and unrelated framework scaffolding in `main`. This intentional temporary copy is not a second independent solver implementation. Future integration should consolidate the duplicate **after** tests on a common codepath; never subtly pick one version's floating-point transformations.

For the immutable source `problems/water_quality/data/LDB_centroids_clean.geojson`, the adapter requires N=20/K=5 notebook weights, default interactions, and checks these *source-specific* values: 5,417 input features, 15 marked existing stations, 20 derived free candidate positions, local selected [0,1,3,6,7], original energy ≈−3.3012934918564643 (1e−7 tolerance). A separate implementation enumerates all `C(20,5)=15,504` subsets, recomputing binary objective+one-hop connectivity independently of the SCIP pair-product MILP. It also exports the **actual original SCIP .lp** and raw objective coefficient hexadecimal representations. User-edited weights or synthetic data are separate **counterfactuals**, not reproduction of the manuscript.

The original paper's AHP Table III/IV and criterion-D2 provenance and reported SCIP energy mismatch remain [#16](https://github.com/carlers/quantum-opt-dashboard/issues/16). The notebook/GeoJSON are not silently normalized/reformatted/replaced, and there is no assertion that the historical notebook used this exact modern MILP/QUBO converter. One-hop local adjacency **is not** global graph path connectivity.

## What remains for a truly general, end-user workbench

- Domain-level data schemas must be explicit: an arbitrary CSV cannot automatically provide shelter capacities, road network reachability, hazard masks, or projected water factors. Unsupported format/plugin combinations are errors.
- An eventual safe UI needs file-format selection, column mappings, CRS transformation options (after scientific validation), data-type/units/ID preflight, license and rights metadata, preview of math generated from the *same* compiled solver object, and user-authenticated storage/limits.
- A typed mathematical intermediate representation and constrained QUBO compiler must be proven separately; this adapter does **not** claim every MIQP can be transformed into QUBO without information loss or unreasonable slack growth.
- Current water proof is small-instance-bound and solver/model-specific, not cross-CPU float64 reproducibility or a release archive. Data/code provenance in short-lived CI artifacts is not durable for thesis publications; keep #34 open.

Automated numerical source parity and metamorphic data swapping tests are under `problems/water_quality/tests/test_water_bundles.py` and CSV-scope tests under `problems/evacuation_centers/tests/test_csv_sources.py`. Independent `.github/workflows/water-data-adapters.yml` runs them with SCIP/SciPy/Shapely, builds both synthetic inputs and original reference, and uploads **only derived model/LP/audit outputs**, never raw source GeoJSON as an artifact.

**No unreviewed scientific conclusion, merge or deployment permitted.**
