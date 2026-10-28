"""All tests use synthetic fixtures, never confidential original run exports."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.audit_penalty_export import ExportAuditError, audit_exports


def records():
    grid = {
        "N": 50, "P_min": 1.2, "config": {"FEAS_THRESHOLD": 0.95},
        "grid_points": [
            {"lambda_budget": 1.2, "lambda_conn": 2.4, "penalty_sum": 3.6,
             "feas_rate_mean": 0.99},
            {"lambda_budget": 1.2, "lambda_conn": 1.2, "penalty_sum": 2.4,
             "feas_rate_mean": 0.96},
            {"lambda_budget": 0.6, "lambda_conn": 0.6, "penalty_sum": 1.2,
             "feas_rate_mean": 0.80},
        ],
    }
    winner = {"50": {"λ_budget": 1.2, "λ_conn": 1.2,
                      "Penalty Sum": 2.4, "Feasibility (%)": 96}}
    return grid, winner


class ExportReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.grid, self.winner = records()

    def run_audit(self, grid=None, winner=None, csvline=None):
        a, b = self.home / "grid.json", self.home / "winner.json"
        a.write_text(json.dumps(self.grid if grid is None else grid))
        b.write_text(json.dumps(self.winner if winner is None else winner))
        c = None
        if csvline is not None:
            c = self.home / "summary.csv"
            c.write_text("N,Winner λ_budget,Winner λ_conn,Winner Penalty Sum\n"
                         + csvline + "\n")
        return audit_exports(a, b, c)

    def test_valid_original_schema_synthetic_points(self):
        report = self.run_audit()
        self.assertEqual(report["selected_grid_position"], 1)
        self.assertFalse(report["scientific_optimality_proven"])
        self.assertFalse(report["original_manuscript_table_verified"])
        self.assertFalse(report["cloud_write_authorized"])

    def test_consistent_original_csv_schema(self):
        self.assertIsNotNone(
            self.run_audit(csvline="50,1.2,1.2,2.4")["summary_sha256"]
        )

    def test_bad_raw_grid_sum(self):
        grid = copy.deepcopy(self.grid)
        grid["grid_points"][1]["penalty_sum"] = 2.3
        with self.assertRaisesRegex(ExportAuditError, "Grid penalty"):
            self.run_audit(grid=grid)

    def test_bad_winner_sum(self):
        winner = copy.deepcopy(self.winner)
        winner["50"]["Penalty Sum"] = 3.4
        with self.assertRaisesRegex(ExportAuditError, "Winner sum"):
            self.run_audit(winner=winner)

    def test_winner_has_valid_sum_but_wrong_grid_row(self):
        wrong = {"50": {"λ_budget": 1.2, "λ_conn": 2.4,
                        "Penalty Sum": 3.6, "Feasibility (%)": 99}}
        with self.assertRaisesRegex(ExportAuditError, "mismatches"):
            self.run_audit(winner=wrong)

    def test_bad_csv_summary(self):
        with self.assertRaisesRegex(ExportAuditError, "CSV summary"):
            self.run_audit(csvline="50,1.2,1.2,3.3")

    def test_missing_tier(self):
        with self.assertRaisesRegex(ExportAuditError, "Missing raw winner"):
            self.run_audit(winner={"20": self.winner["50"]})

    def test_zero_feasibility_uses_fallback(self):
        grid = copy.deepcopy(self.grid)
        grid["config"]["FEAS_THRESHOLD"] = 1.0
        winning = {"50": {"λ_budget": 1.2, "λ_conn": 2.4,
                          "Penalty Sum": 3.6, "Feasibility (%)": 99}}
        r = self.run_audit(grid=grid, winner=winning)
        self.assertEqual(r["selection_rule"], "fallback_highest_feasibility")

    def test_repeated_json_field_rejected(self):
        a, b = self.home / "grid.json", self.home / "winners.json"
        a.write_text('{"N":50,"N":50}')
        b.write_text(json.dumps(self.winner))
        with self.assertRaisesRegex(ExportAuditError, "Duplicate JSON"):
            audit_exports(a, b)

    def test_negative_feasibility_rejected(self):
        grid = copy.deepcopy(self.grid)
        grid["grid_points"][1]["feas_rate_mean"] = -0.1
        with self.assertRaisesRegex(ExportAuditError, "range"):
            self.run_audit(grid=grid)

    def test_nonfinite_json_constant_rejected(self):
        a, b = self.home / "grid.json", self.home / "winner.json"
        a.write_text(json.dumps(self.grid).replace("3.6", "NaN", 1))
        b.write_text(json.dumps(self.winner))
        with self.assertRaisesRegex(ExportAuditError, "Nonfinite"):
            audit_exports(a, b)

    def test_boolean_and_undefined_numbers_rejected(self):
        grid = copy.deepcopy(self.grid)
        grid["grid_points"][1]["lambda_conn"] = True
        with self.assertRaisesRegex(ExportAuditError, "numeric"):
            self.run_audit(grid=grid)

    def test_normal_binary_float_error_accepted(self):
        grid = copy.deepcopy(self.grid)
        grid["grid_points"][1]["penalty_sum"] = 2.400000000000001
        self.assertTrue(self.run_audit(grid=grid)["internal_arithmetic_and_winner_consistent"])

    def test_malformed_raw_grid_rejected(self):
        grid = copy.deepcopy(self.grid)
        grid["grid_points"] = []
        with self.assertRaisesRegex(ExportAuditError, "grid points"):
            self.run_audit(grid=grid)

    def test_symlink_path_rejected(self):
        a, b = self.home / "real.json", self.home / "winner.json"
        a.write_text(json.dumps(self.grid))
        b.write_text(json.dumps(self.winner))
        symlink = self.home / "link.json"
        symlink.symlink_to(a)
        with self.assertRaisesRegex(ExportAuditError, "symlinked"):
            audit_exports(symlink, b)

    def test_no_network_solver_cloud_use(self):
        text = (ROOT / "scripts/audit_penalty_export.py").read_text()
        for forbidden in ("import oci", "import requests", "subprocess",
                          "pyscipopt", "openjij", "terraform apply"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
