"""Independent AST-only historical factor parser tests, no original code executed."""
from decimal import Decimal
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.historical_weight_contract import (
    HistoricalFactorError, extract_from_cell, extract_original_weights,
)
from scripts.verify_research_sources import ROOT, NOTEBOOK

FACTOR_NAMES = (
    "a1_river_proximity", "a2_runoff_proximity", "b1_fishpen_density",
    "b2_hypoxic_proximity", "c1_bathymetric_depressions",
    "c2_outlet_proximity", "d1_boatramp_proximity", "d2_road_proximity",
)
WEIGHTS = ("0.3671", "0.1224", "0.2508", "0.0502",
           "0.1278", "0.0183", "0.0476", "0.0159")


def artificial_cell():
    return (
        "WEIGHTS = np.array([" + ", ".join(WEIGHTS) + "], dtype=np.float64)\n"
        "FACTOR_NAMES = " + repr(list(FACTOR_NAMES)) + "\n"
    )


class HistoricalWeightAstTests(unittest.TestCase):
    def test_actual_original_cell_parses_with_exact_decimal_tokens(self):
        factors, weights = extract_original_weights()
        self.assertEqual(factors, FACTOR_NAMES)
        self.assertEqual(weights, tuple(Decimal(x) for x in WEIGHTS))
        self.assertEqual(sum(weights), Decimal("1.0001"))

    def test_valid_artificial_static_source(self):
        self.assertEqual(extract_from_cell(artificial_cell())[0], FACTOR_NAMES)

    def test_never_executes_original_python_cell(self):
        source = artificial_cell() + "\nraise RuntimeError('EXECUTION WOULD BE UNSAFE')\n"
        self.assertEqual(extract_from_cell(source)[1][0], Decimal("0.3671"))

    def test_executable_weight_expression_fails_closed(self):
        invalid = artificial_cell().replace("0.3671", "open('/etc/passwd').read()")
        with self.assertRaises(HistoricalFactorError):
            extract_from_cell(invalid)

    def test_missing_or_duplicate_weight_assignment_rejected(self):
        for source in (artificial_cell().split("\nFACTOR_NAMES")[1],
                       artificial_cell()+"WEIGHTS = np.array([0]*8, dtype=np.float64)\n"):
            with self.subTest(sample=source[:10]), self.assertRaises(HistoricalFactorError):
                extract_from_cell(source)

    def test_changed_factor_label_is_not_renamed_to_worldpop(self):
        source = artificial_cell().replace("d2_road_proximity", "d2_population_exposure")
        with self.assertRaises(HistoricalFactorError):
            extract_from_cell(source)

    def test_duplicate_factor_names_rejected(self):
        source = artificial_cell().replace("d2_road_proximity", "d1_boatramp_proximity")
        with self.assertRaises(HistoricalFactorError):
            extract_from_cell(source)

    def test_numpy_dtype_is_explicitly_expected(self):
        source = artificial_cell().replace("np.float64", "np.float32")
        with self.assertRaises(HistoricalFactorError):
            extract_from_cell(source)

    def test_bounded_count_and_source_size_rejected(self):
        source = artificial_cell().replace("0.0159", "0.0159, 0.1234")
        with self.assertRaises(HistoricalFactorError):
            extract_from_cell(source)
        with self.assertRaises(HistoricalFactorError):
            extract_from_cell(" " * 25001)

    def test_original_source_file_mutation_fails_before_ast(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "altered.ipynb"
            original = json.loads((ROOT / NOTEBOOK).read_text(encoding="utf-8"))
            original["cells"][3]["source"].append("\n# synthetic mutation")
            path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaisesRegex(HistoricalFactorError, "frozen source"):
                extract_original_weights(path)

    def test_symlinked_source_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "symlink.ipynb"
            path.symlink_to(ROOT / NOTEBOOK)
            with self.assertRaises(HistoricalFactorError):
                extract_original_weights(path)

    def test_no_import_numpy_solver_or_execute_code(self):
        src=(ROOT/"scripts/historical_weight_contract.py").read_text()
        for forbidden in ("import numpy", "import pyscipopt", "import requests",
                          "subprocess", "eval(", "exec(", "os.system(", "oci"):
            self.assertNotIn(forbidden, src)


if __name__ == "__main__":
    unittest.main()
