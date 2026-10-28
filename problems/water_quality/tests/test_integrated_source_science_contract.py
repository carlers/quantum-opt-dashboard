"""Cross-branch scientific source lineage: no SCIP, notebook execution or network.

The executable N20 notebook is exercised separately by notebook-n20-replay CI.
This checks *literal input semantics*, so matching a SHA or an objective alone
is not mistakenly presented as proof that the new notebook used historical D2.
"""
from __future__ import annotations

import ast
from decimal import Decimal
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.historical_weight_contract import extract_original_weights
from scripts.notebook_inventory import (
    ORIGINAL_SHA256, inspect_notebook, load_archived_notebook,
)
from scripts.verify_research_sources import (
    ANCHORS, GEOJSON, NOTEBOOK, verify as verify_sources,
)

CLEAN = ROOT / "problems/water_quality/notebooks/water_quality_n20_reproducible.ipynb"
DERIVED = ROOT / "problems/water_quality/notebooks/derived_historical_weight_audit.ipynb"
DRIVER = ROOT / "scripts/run_n20_reference_notebook.py"


def _assignment(tree, name):
    found = [statement.value for statement in tree.body
             if isinstance(statement, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == name
                     for target in statement.targets)]
    if len(found) != 1:
        raise AssertionError("Ambiguous or missing literal input: " + name)
    return found[0]


def read_clean_factor_literals(notebook):
    """Parse the N20 *working* notebook's input cell without importing NumPy."""
    cells = notebook["cells"]
    if len(cells) != 23:
        raise AssertionError("Expected curated N20 working notebook")
    source = "".join(cells[4]["source"])
    tree = ast.parse(source)
    factor_expr = _assignment(tree, "FACTOR_NAMES")
    factors = ast.literal_eval(factor_expr)
    if type(factors) is not tuple or len(factors) != 8:
        raise AssertionError("Expected eight literal factor names in curated N20")
    expr = _assignment(tree, "WEIGHTS")
    if not (isinstance(expr, ast.Call)
            and isinstance(expr.func, ast.Attribute)
            and isinstance(expr.func.value, ast.Name)
            and expr.func.value.id == "np" and expr.func.attr == "array"
            and len(expr.args) == 1 and not expr.keywords
            and isinstance(expr.args[0], ast.List)
            and len(expr.args[0].elts) == 8):
        raise AssertionError("N20 historical weights must be literal np.array")
    weights = []
    for literal in expr.args[0].elts:
        if not isinstance(literal, ast.Constant) or type(literal.value) not in (float, int):
            raise AssertionError("N20 factor weight is not a literal")
        raw = ast.get_source_segment(source, literal)
        weights.append(Decimal(raw))
    return tuple(factors), tuple(weights)


def read_driver_literal(name):
    source = DRIVER.read_text(encoding="utf-8")
    return ast.literal_eval(_assignment(ast.parse(source), name))


class IntegratedScienceReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = verify_sources()
        cls.historical, cls.digest = load_archived_notebook()
        cls.report = inspect_notebook(cls.historical, cls.digest)
        cls.factors, cls.weights = extract_original_weights()
        cls.n20 = json.loads(CLEAN.read_text(encoding="utf-8"))

    def test_source_gate_and_historical_inventory_have_same_identity(self):
        self.assertEqual(self.digest, ORIGINAL_SHA256)
        self.assertEqual(self.digest, ANCHORS[NOTEBOOK])
        self.assertEqual(self.digest, self.source["original_notebook_sha256"])
        self.assertEqual(ANCHORS[GEOJSON], self.source["original_geojson_sha256"])
        self.assertFalse(self.source["paper_or_worldpop_parity_proven"])

    def test_historical_cell_map_preserved_instead_of_silent_deduplication(self):
        self.assertEqual(self.report["original_cells"], 25)
        self.assertEqual(len(self.report["repeated_sections"]), 5)
        self.assertEqual(self.report["mechanically_excludable_second_cell_indices"], [14, 22])
        self.assertTrue(all(cell["outputs"] == [] for cell in self.historical["cells"]))

    def test_curated_n20_inputs_equal_original_cell_literals(self):
        factors, weights = read_clean_factor_literals(self.n20)
        self.assertEqual(factors, self.factors)
        self.assertEqual(weights, self.weights)
        self.assertEqual(factors[-1], "d2_road_proximity")
        self.assertEqual(sum(weights), Decimal("1.0001"))

    def test_mutated_n20_weight_detected_by_original_source_comparison(self):
        altered = json.loads(json.dumps(self.n20))
        src = "".join(altered["cells"][4]["source"])
        altered["cells"][4]["source"] = [src.replace("0.3671", "0.3672")]
        self.assertNotEqual(read_clean_factor_literals(altered)[1], self.weights)

    def test_mutated_n20_d2_detected_by_original_source_comparison(self):
        altered = json.loads(json.dumps(self.n20))
        src = "".join(altered["cells"][4]["source"])
        altered["cells"][4]["source"] = [src.replace("d2_road_proximity", "d2_population_exposure")]
        self.assertNotEqual(read_clean_factor_literals(altered)[0], self.factors)

    def test_n20_replay_driver_expected_hashes_match_original_and_working_contract(self):
        self.assertEqual(read_driver_literal("EXPECTED_NOTEBOOK_SHA"), ANCHORS[NOTEBOOK])
        self.assertEqual(read_driver_literal("EXPECTED_DATA_SHA"), ANCHORS[GEOJSON])
        self.assertEqual(read_driver_literal("EXPECTED_SELECTED"), [0, 1, 3, 6, 7])
        self.assertEqual(len(read_driver_literal("EXPECTED_FREE_MASTER")), 20)
        self.assertEqual(len(read_driver_literal("EXPECTED_FIXED_MASTER")), 15)
        self.assertEqual(read_driver_literal("EXPECTED_MASTER"), [5253, 2394, 1557, 47, 5409])

    def test_both_derived_notebooks_have_no_stored_execution_results(self):
        other = json.loads(DERIVED.read_text(encoding="utf-8"))
        for notebook in (self.n20, other):
            for cell in notebook["cells"]:
                if cell["cell_type"] == "code":
                    self.assertIsNone(cell["execution_count"])
                    self.assertEqual(cell["outputs"], [])

    def test_integration_is_not_manuscript_or_quantum_proof(self):
        self.assertFalse(self.source["paper_or_worldpop_parity_proven"])
        self.assertFalse(self.source["redistribution_rights_verified"])
        self.assertFalse(self.source["historical_notebook_executed"])
        self.assertFalse(self.source["current_research_model_validated_by_this_check"])


if __name__ == "__main__":
    unittest.main()
