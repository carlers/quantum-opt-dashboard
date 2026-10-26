# Nested resolution cohorts (first M1 review gate)

This additive research module builds N=20/50/100 nested source-backed instances with the **existing** frozen notebook-derived source model. It deliberately does **not** change `app.py`, solve with SCIP, run OpenJij, or touch deployment branches.

Call from a repository-root Python 3.12 environment with NumPy, SciPy and Shapely installed:

```python
from problems.water_quality.nested_resolution import build_nested_instances
study = build_nested_instances()
print(study.manifest())
```

The output includes GeoJSON SHA-256, feature **positions** and separate feature `id` properties, fixed-station identities, exact candidate prefixes, geometric model adjacency sizes, and explicit no-solver/no-paper-parity flags. The current implementation invokes the historical model builder separately for each tier and verifies each against a shared maximum-N FPS prefix. This redundant preprocessing favors science parity over premature optimization. Do not interpret source-backed prefixes as proven SCIP optima or validated quantum performance.

Required review: compare original notebook Cells 2, the **second** Cell 3, Cell 4, frozen N20 reference regression; verify no changes in original inputs or N20 certificate. CI intentionally avoids stochastic sampling and heavy solver runs.
