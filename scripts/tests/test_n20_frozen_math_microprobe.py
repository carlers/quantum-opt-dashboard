"""Adversarial exact operand and IEEE754 outcome comparisons for #60."""
from copy import deepcopy
import math
import unittest

from scripts.n20_frozen_math_microprobe import FROZEN_CASES, compare_six, fingerprint


def six():
    result = []
    for host in range(1, 4):
        for proc in ("a", "b"):
            result.append({
                "schema_version": 1,
                "study": "issue60_exploratory_frozen_numpy_operations",
                "source_n20_trace_run_id": 39177889565,
                "frozen_input_sha256": fingerprint(FROZEN_CASES),
                "replica": f"r{host}-{proc}",
                "runtime": {"numpy": "2.5.4", "cpu_model": f"test CPU {host}"},
                "cases": [
                    dict(c, result_float64_hex="0x1.0p+0") for c in FROZEN_CASES
                ],
            })
    return result


class MicroprobeChecks(unittest.TestCase):
    def test_equal_results_report_negative_observation(self):
        output = compare_six(six())
        self.assertEqual(output["numeric_operations_with_multiple_modes"], [])
        self.assertTrue(all(x["exact_distinct_results"] == 1 for x in output["cases"]))

    def test_one_ulp_change_in_frozen_norm_is_retained(self):
        data = six()
        data[4]["cases"][1]["result_float64_hex"] = math.nextafter(
            1.0, math.inf
        ).hex()
        output = compare_six(data)
        self.assertEqual(output["numeric_operations_with_multiple_modes"], [
            "norm_f9_fixed26"
        ])
        self.assertEqual(output["cases"][1]["exact_distinct_results"], 2)

    def test_changed_frozen_operand_is_rejected(self):
        data = six()
        data[0]["cases"][0]["hex_operands"][1] = "0x1.0p+0"
        with self.assertRaisesRegex(ValueError, "Modified frozen"):
            compare_six(data)

    def test_missing_host_cannot_be_silently_counted(self):
        with self.assertRaisesRegex(ValueError, "six independent"):
            compare_six(six()[:-1])

    def test_missing_case_cannot_be_accepted(self):
        data = six()
        data[0]["cases"].pop()
        with self.assertRaisesRegex(ValueError, "Missing diagnostic"):
            compare_six(data)

    def test_unpinned_numpy_version_is_rejected(self):
        data = six()
        data[2]["runtime"]["numpy"] = "999"
        with self.assertRaisesRegex(ValueError, "Changed pinned"):
            compare_six(data)


if __name__ == "__main__":
    unittest.main()
