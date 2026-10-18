# Guided typed-math editor — bounded prototype, 2026-10-18

The experimental, **synthetic-only** Streamlit workbench now has a guided point-and-click layer over the existing typed mathematical JSON editor. It is not a production or historical Laguna de Bay upload tool.

## Single source of mathematical truth

`prototypes/streamlit_configurable/guided_math.py` defines small, pure, **atomic edits** to variables, coefficients, binary pair products and named constraints. Each operation calls the exact existing `qopt.core.math_ir.validate_ir` on both the original and proposed typed source. Invalid changes preserve the original source, show a specific error, and do not silently remove interactions or constraints.

`guided_math_ui.py` displays Streamlit select boxes, numeric fields and buttons in **Variables and bounds**, **Objective and interactions**, and **Constraints** tabs. Existing advanced JSON component fields remain visible for reproducible power-user editing. A successful button callback rewrites the SAME `typed-vars`, `typed-objective`, `typed-constraints` widget values **before rerun**, and invalidates preview and any old solver result. There is no second/competing solver model and no arbitrary LaTeX/Python parser.

### Guided operations

- Select an existing variable, choose `binary`, `integer`, or `continuous`, edit bounds; add a new named variable (defaults binary or bounded 0..1) or remove an **unreferenced** variable. If the model still references that name in the objective, any quadratic pair or constraint, removal fails with a clear message.
- Change objective direction and constant; edit a named linear coefficient or explicitly remove its term; add/edit or remove a pair interaction between **two distinct binary variables only**. Nonbinary interactions are rejected, not guessed.
- Select a named linear constraint and edit `<=`, `==`, `>=`, RHS or any coefficient. Add or remove a named constraint. Named active parameter RHS overrides are displayed and **must be edited/removed explicitly** before altering the underlying row, preventing misleading edits that would not affect the solved problem.
- **Preview → Run:** same validated IR produces readable mathematical equation and exact SCIP MILP model/LP plus independent SciPy/HiGHS reference. Only unconstrained all-binary objectives can export the independently truth-table verified exact QUBO. Adding a constraint disables direct QUBO; removing it restores eligibility.
- Uploaded source file takes precedence over component fields. Guided controls are disabled until the researcher removes an active upload. All input files must be synthetic/declared/within the preexisting 1 MB and variable-bound safety limits.

### Research evidence

`tests/test_guided_math.py` tests atomic full-IR validation, invalid edit nonmutation, named override precedence, explicit term/variable deletion and exact JSON round trips. `tests/test_guided_math_app.py` exercises the actual Streamlit widgets through headless AppTest: change a numeric linear coefficient → independently verified SCIP objective 17→29, change a named constraint bound → objective 8, add a linear constraint → direct QUBO unavailable, remove it → truth-table checked exact QUBO returns, and invalid variable type mutations fail without altering original source. The prior scientific backend, immutable N20 water, and CSV/GeoJSON interface tests run in unchanged workflows.

### Current limitations

This is a **guided form**, not a WYSIWYG algebra canvas, arbitrary expression parser, nonlinear continuous MIQP solver or safe constrained QUBO compiler. It supports only the bounded typed MILP/linear-binary interactions already independently verified in draft PR #46. Each edit can change science; persisted runs must keep exact source SHA, inputs, compiled LP, solver software and independent checks. Integration into the live dashboard, real shelter/hazard inputs, user authentication, and production upload service are **not authorized** and remain separate roadmap gates. Draft PRs are stacked and **not merged**.
