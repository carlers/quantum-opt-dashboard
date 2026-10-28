"""Static identification of different energy domains in the archived notebook.

Only checks immutable historical source text. Does not unpickle cached results,
execute notebook cells, run SCIP/OpenJij, or infer actual unpublished values.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "problems/water_quality/notebooks/experiment9 grid search copy.ipynb"
SOURCE_SHA256 = "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"


class EnergyDomainError(ValueError):
    """Historical source changed or reporting paths cannot be established."""


def _cell_source(notebook, index):
    try:
        cell = notebook["cells"][index]
        source = cell["source"]
        return "".join(source) if isinstance(source, list) else source
    except (TypeError, KeyError, IndexError) as exc:
        raise EnergyDomainError("Historical notebook cell missing") from exc


def inspect_historical_energy_scopes(notebook_path=NOTEBOOK):
    """Establish where the *code* obtains published comparison inputs."""
    path = Path(notebook_path)
    if (path.is_symlink() or not path.is_file()
            or not 0 < path.stat().st_size <= 500_000):
        raise EnergyDomainError("Missing or unsafe historical notebook")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != SOURCE_SHA256:
        raise EnergyDomainError("Original notebook SHA-256 has changed")
    try:
        nb = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EnergyDomainError("Malformed notebook JSON") from exc
    scip_cell = _cell_source(nb, 7)    # historical CELL 5
    sa_cell = _cell_source(nb, 13)     # historical CELL 7
    table_cell = _cell_source(nb, 21)  # historical CELL 10
    expected = (
        ("tier solver energy", scip_cell, '"energy": tier_energy'),
        ("master recomputation", scip_cell, 'scip_result["master_energy"] = master_energy_val'),
        ("SA sampled tier energy", sa_cell, 'energies = compute_energy_batch(X, a, Q)'),
        ("SA reported tier statistic", sa_cell,
         '"best_feasible_obj_mean": float(np.mean(best_feas_energies))'),
        ("SCIP final comparison column", table_cell,
         'scip_energy = scip_res.get("master_energy", np.nan)'),
        ("SA final comparison column", table_cell,
         'sa_energy = winner["Best Feasible Obj"]'),
    )
    for label, source, snippet in expected:
        if snippet not in source:
            raise EnergyDomainError("Historical energy path not found: " + label)
    return {
        "schema": "qopt-original-notebook-energy-domain-inspection-v1",
        "original_notebook_sha256": SOURCE_SHA256,
        "scip_table_10_energy_field": "master_energy",
        "scip_solver_tier_energy_field": "energy",
        "sa_table_10_energy_field": "Best Feasible Obj",
        "sa_grid_cell_7_statistic_source": "compute_energy_batch(X,a,Q) on tier data",
        "same_energy_basis_confirmed": False,
        "reported_energy_domain_mismatch_detected": True,
        "numeric_magnitude_of_domain_difference_measured": False,
        "historical_cache_and_config_hash_verified": False,
        "original_notebook_executed": False,
        "manuscript_provenance_proven": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        print(json.dumps(inspect_historical_energy_scopes(), sort_keys=True))
    except EnergyDomainError as exc:
        print("Historical scope audit FAILED: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
