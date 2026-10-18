# Typed, user-configurable mathematical formulation editor (research milestone #42)

**Status:** First validated, bounded mathematical intermediate representation (IR) behind the independent experimental Streamlit workbench. This is a **DRAFT stacked PR**, not production, and not a new claim of quantum performance, historical notebook-paper parity, or real shelter safety.

## Scientific architecture

This milestone does not guess equations from dataset names. The user specifies three typed components in the Structured Math presets:

- **Variables:** an array of unique safe identifiers, explicit `binary`, bounded `integer`, or `continuous` domain and numeric lower/upper bounds. A binary variable is exactly 0..1; integer variables have ≤5 finite domain values; at most 12 total / 8 continuous; at most 4,096 combinations of discrete variables for independent reference.
- **Objective:** `minimize` or `maximize`, numeric constant, any linear terms for the named variables, and optional *distinct binary × binary* quadratic terms. Continuous/integer quadratic interactions are **not** supported, **not** silently linearized.
- **Linear constraints:** named rows with numerical coefficients, `<=`, `==`, `>=` relations and finite RHS. User may supply named `rhs_overrides` in the reusable versioned bundle. Unknown names, duplicate IDs/pairs, nonfinite coefficients, unsupported operators or ranges fail preflight.

The same `validate_ir` object generates the displayed equation (via `render_original`), the **actual SCIP MILP** (via `solve_scip`) and the independent post-solve check. The compiled SCIP linearization introduces a binary auxiliary variable for each pair of binary factors `x_a*x_b`, plus inequalities `z<=x_a`, `z<=x_b`, `z>=x_a+x_b-1`. The exported solver `.lp` is the real model created by SCIP before optimization; it can differ syntactically from the human-readable original quadratic expression because of explicit auxiliary variables. Both must agree numerically for every feasible assignment.

### Independent correctness check

For the bounded research subset, a **separate scientific checker** enumerates all discrete binary/integer states and, if continuous variables are present, constructs independent matrices for a SciPy HiGHS `linprog` assignment LP on each discrete state. It validates the original variable bounds, linear rows and objective without sharing SCIP model objects; resulting optimality/feasibility must match the SCIP status and objective to 1e−6. It therefore detects incorrect auxiliary-pair signs, incorrect original constraints and incorrect objective direction in tiny examples. This is an actual solver-reference agreement, **not** a proof about general large instance accuracy, arbitrary nonlinear problems or publication feasibility.

### Solver compatibility contract

| Problem type | SCIP exact mathematical formulation | QUBO export |
|---|---|---|
| Unconstrained, all binary linear/quadratic objective | Exact binary-product MILP | **Exact**, no penalties required; includes constant offset, correct maximization sign conversion. Every binary configuration is checked in an independent truth table |
| Binary objective and any named linear constraints | Exact binary-product MILP | **Refused.** Requires explicitly proven penalties/slack, capacity and coefficient bounds and independent feasibility equivalence |
| Binary + bounded integer + continuous variables, linear constraints, optional binary-only quadratic terms | Exact MILP with type/bounds | **Refused.** General mixed-domain QUBO needs a justified finite precision encoding and error analysis |
| Quadratic continuous/integer terms, unbounded domains, arbitrary Python/LaTeX formulas | **Rejected** by this compiler | **Rejected** |

The UI describes QUBO as a coefficient export to a **minimizer**; it does not run OpenJij, perform quantum annealing, or claim quantum advantage. The old source paper's JijModeling/OMMX compiler equivalence remains an open scientific issue (#16).

## Completely synthetic worked examples

**Mixed-site staffing (fictional):** binary `open`, integer `staff` in 0..2, continuous `people` in 0..5. Maximize `5 people - 2 open - staff`; constraints link service to open/allocated staff and cap total served to four. Independently checked optimum is open 1, staff 1, people 4, objective **17** (synthetic units). Changing named `limit_served` RHS to 2 changes the optimum to **8**. This is a mathematical proof fixture, **not** a real evacuation facility/demand/capacity model.

**Unconstrained binary quadratic:** maximize `2 + 3a + 2b - 4ab`; exact maximum **5** at a=1,b=0. To supply QUBO to a minimization engine, negate the complete original including offset: `-2 -3a -2b +4ab` with minimum **−5**. Adding a row `b=1` changes the constrained objective and **disables QUBO export**. The compiler must refuse unsupported transformations instead of silently introducing arbitrary penalty strengths.

## Reproducible user workflow

1. In the **separate experimental Streamlit prototype**, select either Structured Math preset. Edit variable types/bounds, objective coefficients and row-based constraints in independent JSON component editors rather than typing executable code. Existing data JSON/CSV/GeoJSON and domain-specific presets remain intact.
2. Click **Validate and preview formulation**. The exact resolved source is validated by `qopt.core.math_ir.validate_ir`, and the source fingerprint includes all term and RHS changes. Preview shows a human-readable expression generated from that object and a truthful SCIP/QUBO compatibility statement. Preview runs no solver.
3. Click **Run this validated synthetic model with SCIP**. The same typed source/fingerprint is revalidated. Download `actual-typed-scip-milp.lp`, `run.json`, `input-source.json`, `input-bundle.json`, and SHA checksums. The `exact-unconstrained-qubo.json` file appears **only when eligible** and its energy agrees for *every* binary assignment.
4. Changing any variable, coefficient, domain, row, source, or parameter invalidates old results and requires new preview before solve. Infeasibility is reported as such, not coerced into an answer.

### Run on this review-only draft branch

```bash
python -m pip install 'numpy>=2,<3' 'scipy>=1.11,<2' 'shapely>=2,<3' 'pyscipopt>=5,<7' 'pytest>=8' 'streamlit>=1.43,<2'
python -m pytest problems/evacuation_centers/tests/test_typed_math_ir.py -q
python -m pytest prototypes/streamlit_configurable/tests/test_typed_math_editor_app.py -q
python problems/evacuation_centers/bundle_runner.py \
  --bundle problems/evacuation_centers/examples/synthetic-typed-mixed.bundle.json \
  --output-dir /tmp/qopt-mixed
streamlit run prototypes/streamlit_configurable/app.py
```

## Non-goals / remaining scientific gates

- No arbitrary LaTeX parser, arithmetic-expression eval, unbounded continuous quadratics, mixed-product MIQP, multiobjective/lexicographic generic IR yet; the synthetic evacuation adapter independently implements its own two-stage policy.
- No general decimal-to-binary capacity discretization, constrained QUBO parity proof, auto penalty tuning, QPU connection or QAOA.
- No real Philippine hazard/facility dataset upload, online job queue, user authentication, persistent storage or deployment. Only small synthetic local inputs accepted in experimental UI.
- No cross-branch refactor of the validated water-quality inspector #29 or deprecated original manuscript notebook; preserve historical source and original scientific provenance.
- Later [#42](https://github.com/carlers/quantum-opt-dashboard/issues/42) phases should add scientifically checked parser/typed IR extensions and explicit solver capabilities, followed by reviewed integration under [#40](https://github.com/carlers/quantum-opt-dashboard/issues/40).

### Primary source
`contracts/typed_math_ir.schema.json` is the shape contract. `framework/python/qopt/core/math_ir.py` enforces semantic validation beyond JSON Schema, including domains, duplicate names, unknown terms, finite bounds, tuple caps, and exact QUBO compatibility. The primary executable truth is **the resolved source → typed IR → SCIP LP → original-feasibility checker**, never a separately hand-written illustrative equation.

**Do not merge into `main` or live `plugin-water-streamlit-pilot` until explicit user review and approval.**
