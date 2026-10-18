# Configurable research problem bundles — v1 proof of concept

**Status:** Early domain-neutral experiment contract on isolated [issue #38](https://github.com/carlers/quantum-opt-dashboard/issues/38) development branch, **not the live dashboard**. The examples are wholly synthetic. Inputs, formulations and parameter choices are not intended to be fixed by the current thesis subject or geography.

## Why this matters

The final user journey should be:

1. **Choose/import a dataset** (eventually CSV/GeoJSON/Parquet with a domain adapter, licensing and CRS checks). This prototype accepts bounded **local JSON only**, marked `SYNTHETIC`. Dataset content is never executed as Python.
2. **Choose a problem adapter** registered by a supported backend (not a hard-coded thesis dataset). The present registered IDs are `evacuation.synthetic` and `binary_quadratic.synthetic`.
3. **Choose a compatible mathematical formulation**. The evacuation adapter currently exposes (A) maximal covering potential (binary; ignores capacity) or (B) two-stage capacitated location–allocation (minimize unserved persons, then assigned person-minutes). The generic binary-quadratic adapter supports user-defined binary variables, objective linear/quadratic coefficients and named linear constraints.
4. **Edit typed parameters** (evacuation `max_open`; arbitrary-binary named constraint RHS overrides), validate schema/units/IDs/bounds, and display the *resolved*, exact numeric formulation. Unsupported choices **fail**, rather than quietly defaulting to a different model.
5. **Inspect what solver will actually receive**: export the original specification, complete input, SHA-256 fingerprint, actual SCIP `.lp` created by the exact `Model` optimized, independently checked original energy/constraints and result. Only when scientifically valid should QUBO be offered.
6. **Save/reload the entire bundle** with data version, formulation ID, parameters, solver model and result. Never confuse an archived synthetic scenario with certified live hazard/facility information.

**Important distinction:** This does not yet implement uploading/typing mathematical expressions in the deployed Streamlit UI. That will use the same validated bundle and mathematical inspector after the independent draft branches are integrated with approval. There is no sandboxed generic LaTeX/Python solver execution.

## Bundle data format

New `contracts/optimization_bundle.schema.json` describes a versioned *execution bundle* — **not** the existing `contracts/problem_manifest.schema.json` for plugin stage discovery. Runtime validation is intentionally strict even where JSON Schema cannot represent domain-specific mathematical semantics.

Example `evac-capacitated.json`:

```json
{
  "schema_version": 1,
  "classification": "SYNTHETIC",
  "problem_id": "evacuation.synthetic",
  "formulation_id": "capacitated_lexicographic",
  "dataset": { "path": "fake-evacuation.json" },
  "parameters": { "max_open": 1 }
}
```

To switch **only the formulation**, change `formulation_id` to `maximal_coverage` (same data). To change a data source, point `dataset.path` to another validated **relative** JSON file in the same bundle folder. To change the budget, edit `parameters.max_open`. For portable integrity, a user can optionally add `dataset.expected_sha256` with the source file's exact lowercase SHA-256. A mismatch is an error.

The generic `binary_quadratic.synthetic` model allows a variable list like `["alpha","beta","gamma"]`, objective `minimize -4 alpha -3 beta -gamma +2 alpha beta`, named budget row `alpha+beta+gamma<=1`, and `parameters.rhs_overrides.budget=0` to change the budget without editing the source model. The adapter enumerates all binary states for **n<=16** and verifies the independent optimum against an exact binary-product SCIP MILP. Models with constraints **do not get a misleading direct QUBO**, because converting them requires a separately validated slack/penalty formulation. Unconstrained binary objectives have an exact QUBO coefficient export (no OpenJij run).

## Example commands (synthetic only)

With Python 3.12 and `numpy scipy pyscipopt` installed:

```bash
python problems/evacuation_centers/bundle_runner.py \
  --bundle problems/evacuation_centers/examples/evac-capacitated.json \
  --output-dir /tmp/qopt-capacitated

python problems/evacuation_centers/bundle_runner.py \
  --bundle problems/evacuation_centers/examples/evac-covering.json \
  --output-dir /tmp/qopt-covering

python problems/evacuation_centers/bundle_runner.py \
  --bundle problems/evacuation_centers/examples/evac-alternate-data.json \
  --output-dir /tmp/qopt-replacement

python problems/evacuation_centers/bundle_runner.py \
  --bundle problems/evacuation_centers/examples/generic-binary-quadratic.json \
  --output-dir /tmp/qopt-binary
```

Output `run.json` contains exact original input values, classification, source/manifests' SHA-256 digests, chosen formulation and resolved typed parameters, result and independent verification. `manifest.json` hashes all generated files. SCIP models export their authentic `.lp` content, enabling a reviewer to inspect the *actual* mathematical problem solved. The deterministic **content fingerprint** changes when dataset bytes, chosen formulation or parameter overrides change (though it is not a provenance substitute for compiled solver hashes and environment records).

## Scientific acceptance

- Same artificial dataset, different evacuation formula: maximal covering reports **7 potentially reachable people**, whereas capacity-constrained location/allocation serves **5** and leaves ~**2** unserved.
- New fabricated dataset (demand [3,3], capacity [6,6]), same capacitated formula and K=1: **zero unserved**; swapping requires no Python edits. All artificial identifiers/values are explicit, not actual Philippines population/shelters.
- Generic binary objective `-4 alpha -3 beta -gamma +2 alpha beta` with budget <=1 selects alpha (energy **-4**). Changing the binary constraint RHS to 0 returns empty selection (energy 0); making beta coefficient -8 selects beta. These changes require only JSON edits and must alter the input fingerprint.
- Fail-closed on unknown mathematical models, nonfinite numbers, unknown/unsafe shelter eligibility/capacity, incorrect units, unknown parameters, unknown vars, duplicate quadratic/constraint terms, traversal/symlink paths and tampered optional hashes.
- Need actual CI acceptance with all synthetic tests green and four example bundles exporting true SCIP LPs before calling this implementation verified.

## Integration design — preserve true extensibility

| Layer | Responsibility | Current status |
|---|---|---|
| Common bundle | Versioned problem ID, formulation choice, source dataset, parameters, stable exact content hashes | This milestone |
| Domain adapter | Validate domain units, geography/eligibility/constraints; build original mathematical model | Synthetic evacuation + generic tiny binary quadratic examples |
| Typed mathematical compiler | Constrained binary/continuous/MIQP IR with audited transforms, constraints and supported solvers | **Partial**: binary quadratic → exact pair-product SCIP; evacuation exact SCIP-specific two-stage adapter. No unrestricted expressions |
| Solver plugins | SCIP and future independently validated OpenJij/QUBO pathways | Small bounded SCIP adapters; OpenJij research in separate unmerged branch, not attached to these bundles |
| Dashboard | Dataset upload, schema validation, formula/constraints editor, generated equation, actual solver input, outcome audit | **Planned**; current unmerged #29 inspector is read-only, user dataset upload not deployed |
| Experimental archive | Bundle + resolved data/rights/version + actual solver LP/QUBO + environment + reproducibility results | SHA/LP prototype; durable DOI/deposit and real rights review not done |

Do not collapse the original lake source utility/wake model into fake shelter attributes merely to prove genericity. A separate future approved water-quality adapter can map source N20 instance to a versioned input bundle; its MIQP/QUBO parity and four known manuscript discrepancies must be preserved. **Genericity means explicit contracts with honest compatibility checks, not “every optimization formula automatically becomes a QUBO.”**

## Safety and follow-ups

All presently runnable examples are **small, artificial, local and bounded** (1 MB per source JSON, <=16 custom binary variables, no arbitrary Python/LaTeX or network access). Real source rights, full geographic data loaders, optimization job queues, robust/intertemporal equations, larger models, persistent deployments, end-user authentication and final thesis model are all outside this first slice. Rejection of an unsupported model is a feature, not an invitation to silently run a different algorithm.

Related: umbrella #2, extensible architecture #7, mathematical preview #28, synthetic original-domain proof #32, scientific source-rights #33, new bundle gate #38. No merges/deployments, original source changes or emergency site recommendations.
