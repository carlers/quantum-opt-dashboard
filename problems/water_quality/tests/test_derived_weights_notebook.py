"""Read-only derived source-weight notebook smoke tests; no solver/runtime deps."""
import contextlib
from decimal import Decimal
from hashlib import sha256
import io
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
DERIVED = ROOT / "problems/water_quality/notebooks/derived_historical_weight_audit.ipynb"
ORIGINAL = ROOT / "problems/water_quality/notebooks/experiment9 grid search copy.ipynb"
GEOJSON = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"

class DerivedNotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = json.loads(DERIVED.read_text(encoding="utf-8"))
        cls.code = [
            "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
            for c in cls.book["cells"] if c["cell_type"] == "code"
        ]

    def test_original_notebook_and_data_unchanged(self):
        self.assertEqual(sha256(ORIGINAL.read_bytes()).hexdigest(),
                         "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048")
        self.assertEqual(sha256(GEOJSON.read_bytes()).hexdigest(),
                         "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7")

    def test_clean_structured_derived_notebook(self):
        self.assertEqual(self.book["nbformat"], 4)
        self.assertEqual(len(self.book["cells"]), 8)
        self.assertEqual(len(self.code), 4)
        ids = [c["id"] for c in self.book["cells"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(c["cell_type"] in {"markdown", "code"}
                            for c in self.book["cells"]))
        for c in self.book["cells"]:
            if c["cell_type"] == "code":
                self.assertIsNone(c["execution_count"])
                self.assertEqual(c["outputs"], [])

    def test_run_all_cells_in_fresh_python_namespace(self):
        context = {"__name__": "__derived_notebook_test__"}
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            for source in self.code:
                exec(compile(source, "<derived-weight-audit-cell>", "exec"), context)
        self.assertEqual(context["project_root"], ROOT)
        self.assertEqual(context["FACTORS"][-1], "d2_road_proximity")
        self.assertEqual(sum(context["NOTEBOOK_WEIGHTS"]), Decimal("1.0001"))
        self.assertEqual(sum(context["PAPER_SENSITIVITY_WEIGHTS"]),
                         Decimal("1.000000001"))
        self.assertFalse(context["verified_sources"]["paper_or_worldpop_parity_proven"])
        text = stream.getvalue()
        self.assertIn("Input-vector audit passed", text)
        self.assertIn("d2_road_proximity", text)
        self.assertIn("manuscript parity remains unverified", text)

    def test_no_native_solver_or_external_service_calls(self):
        source = "\n".join(self.code).lower()
        for forbidden in ("pyscipopt", "scip.", "openjij", "subprocess",
                          "requests", "streamlit", "oci.", "import os",
                          "pip install", "notebook.write", "to_csv(", "to_file("):
            self.assertNotIn(forbidden, source)

    def test_no_manuscript_or_quantum_success_claim(self):
        contents = "\n".join("".join(c["source"]) for c in self.book["cells"]).lower()
        self.assertIn("not", contents)
        self.assertIn("worldpop", contents)
        self.assertIn("notebook", contents)
        self.assertIn("source", contents)

    def test_derived_notebook_is_not_historical_reference(self):
        self.assertNotEqual(sha256(DERIVED.read_bytes()).hexdigest(),
                            sha256(ORIGINAL.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
