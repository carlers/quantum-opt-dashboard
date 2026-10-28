"""Pure read-only energy-scope audit tests; no solver or unsafe pickle loading."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.audit_notebook_energy_domains import (
    EnergyDomainError, NOTEBOOK, SOURCE_SHA256,
    inspect_historical_energy_scopes,
)


class HistoricalEnergyScopeTests(unittest.TestCase):
    def test_archived_code_mixes_tier_and_master_energy_fields(self):
        result = inspect_historical_energy_scopes()
        self.assertEqual(result["original_notebook_sha256"], SOURCE_SHA256)
        self.assertEqual(result["scip_table_10_energy_field"], "master_energy")
        self.assertEqual(result["scip_solver_tier_energy_field"], "energy")
        self.assertEqual(result["sa_table_10_energy_field"], "Best Feasible Obj")
        self.assertEqual(result["sa_grid_cell_7_statistic_source"],
                         "compute_energy_batch(X,a,Q) on tier data")
        self.assertTrue(result["reported_energy_domain_mismatch_detected"])
        self.assertFalse(result["same_energy_basis_confirmed"])
        self.assertFalse(result["numeric_magnitude_of_domain_difference_measured"])
        self.assertFalse(result["manuscript_provenance_proven"])

    def test_original_notebook_mutation_rejected_before_inspection(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder) / "mutated.ipynb"
            notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
            notebook["cells"][21]["source"].append("# fake audit correction\n")
            fake.write_text(json.dumps(notebook), encoding="utf-8")
            with self.assertRaisesRegex(EnergyDomainError, "SHA-256"):
                inspect_historical_energy_scopes(fake)

    def test_symlink_not_accepted_as_original_source(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder) / "source.ipynb"
            fake.symlink_to(NOTEBOOK)
            with self.assertRaises(EnergyDomainError):
                inspect_historical_energy_scopes(fake)

    def test_missing_original_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(EnergyDomainError):
                inspect_historical_energy_scopes(Path(folder) / "none.ipynb")

    def test_no_pickle_code_execution_or_cloud_io(self):
        src = (ROOT / "scripts/audit_notebook_energy_domains.py").read_text()
        for forbidden in ("pickle.load(", "import pyscipopt", "import oci",
                          "import requests", "subprocess", "exec(", "eval("):
            self.assertNotIn(forbidden, src)


if __name__ == "__main__":
    unittest.main()
