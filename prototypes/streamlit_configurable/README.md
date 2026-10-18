# Experimental configurable Streamlit research UI

**Not the deployed water-quality Streamlit site.** This is an isolated v0 prototype for issue [#40](https://github.com/carlers/quantum-opt-dashboard/issues/40), built on the typed dataset/formulation bundle contract [#38](https://github.com/carlers/quantum-opt-dashboard/issues/38) / draft PR #39. Only synthetic artificial data is supported through the user-input interface. The independently pinned original Laguna de Bay source is accessible to backend research tests, **not** uploaded into this UI.

## Intended hands-on behavior

- Select an illustrative **evacuation synthetic**, **generic binary quadratic**, **synthetic CSV variable-score table**, or **projected synthetic water-quality GeoJSON** preset.
- CSV requires exactly `variable,linear_coefficient` with 1–16 safe binary variable IDs; the general budget changes through named `rhs_overrides.budget`. A spreadsheet string beginning with `=` is rejected as a variable name, not executed.
- Water GeoJSON requires an explicit `EPSG:32651` projected point FeatureCollection, site property IDs, eight factor values and explicit fixed-station indicators. N/K and the eight criterion weights are editable parameters (UI capped at N≤12, ≤200 features, ≤20-second SCIP budget); **the equation's local one-hop constraint is not globally connected deployment**.
- Pick a supported mathematical formulation. For evacuation the choices are capacity-aware, two-stage location–allocation or binary maximal **potential** covering. Changing formulation genuinely switches the solver model, not the equation label.
- Edit the currently selected **JSON, CSV, or GeoJSON** dataset in its dedicated text area, or upload a local file **of the same selected type**, **1 MB maximum**; upload takes precedence. Real shelter/hazard data is not admitted. Edit formulation-specific parameters as JSON, including K (`max_open`) or named binary constraint RHS overrides.
- The backend validates the source type and schema for the chosen mathematical adapter, domain units, variable types, objective coefficient bounds, geometry/CRS, reachability, eligibility, budget bounds, safe path and supported model/formulation identifiers. It never interprets arbitrary LaTeX or Python code.
- Click **Validate and preview formulation**. It displays a model description with the actual current numeric coefficients/demand/capacity/budget, exact source hashes and full resolved input. Preview **does not invoke SCIP**.
- Explicitly click **Run this validated synthetic model with SCIP**. This uses the exact same fingerprinted dataset/formulation/parameters and independently checks the original objective/constraint interpretation; the downloaded ZIP includes `input-source.json`, `input-bundle.json`, `run.json`, SHA `manifest.json`, and actual original SCIP `.lp` model(s) exported from the same solver instance.
- Changing any input invalidates preview and stale results, so users must re-preview before rerunning and cannot accidentally download an old run as if it matched the new formula.

No real evacuation routing, user authorization, data rights clearance, domain-generic QUBO converter, publication-quality environment lock, remote job queues or arbitrary algebra editor is implemented.

### Run locally on isolated research branch

```bash
python -m pip install 'numpy>=2,<3' 'scipy>=1.11,<2' 'shapely>=2,<3' 'pyscipopt>=5,<7' 'pytest>=8' 'streamlit>=1.43,<2'
streamlit run prototypes/streamlit_configurable/app.py
```

The CI workflow `.github/workflows/configurable-ui.yml` executes Streamlit's **AppTest** interactions without hosting the app online, including preview-only, real SCIP execution, changed-formulation/constraint parameters, invalid input preflight and stale-result safeguards. It also rechecks the independent synthetic mathematical reference and bundle validation tests.

**No deployment to `main` or `plugin-water-streamlit-pilot` is authorized.** This prototype should only be integrated with the tested Laguna de Bay MIQP/QUBO inspector after cross-branch review and an explicit safe integration plan. In final architecture the user interface should render equations from the same typed resolved model submitted to solvers and disclose incompatible solver/formulation combinations rather than coercing them.
