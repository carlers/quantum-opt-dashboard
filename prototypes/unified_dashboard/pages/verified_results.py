"""Review-only historic source-derived computational results page.

This route reads an immutable reviewed CI observation receipt only. It never
imports the interactive SCIP execution function or runs a scientific batch.
"""
from prototypes.unified_dashboard.verified_results import render_verified_results

render_verified_results()
