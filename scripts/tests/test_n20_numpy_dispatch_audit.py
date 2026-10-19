"""Adversarial controls for Issue #62 paired NumPy dispatch protocol."""
from __future__ import annotations

from copy import deepcopy
import math
import unittest

from scripts.n20_numpy_dispatch_audit import (
    EXPERIMENT, FROZEN_CASES, MODE_ENV, compare, fingerprint, validate_observation,
)


def records() -> list[dict]:
    results = []
    for h in range(1, 4):
        for mode in MODE_ENV:
            for p in ("a", "b"):
                rec = {
                    "schema_version": 1,
                    "experiment": EXPERIMENT,
                    "replica": f"r{h}-{mode}-{p}",
                    "mode": mode,
                    "source_trace_run": 39177889565,
                    "frozen_input_sha256": fingerprint(FROZEN_CASES),
                    "runtime": {
                        "numpy": "2.5.4",
                        "cpu_model": f"synthetic-cpu-{h}",
                        "machine": "x86_64", "libc": ["glibc", "2.39"],
                        "cpu_features_enabled": {
                            "X86_V3": mode == "baseline",
                            "X86_V4": mode == "baseline",
                        },
                        "env": {
                            "NPY_DISABLE_CPU_FEATURES": MODE_ENV[mode]
                        },
                        "extensions_sha256": [
                            {"basename": "multiarray.so", "bytes": 100,
                             "sha256": "1" * 64},
                            {"basename": "linalg.so", "bytes": 100,
                             "sha256": "2" * 64},
                        ],
                    },
                    "case_results": [],
                }
                for c in FROZEN_CASES:
                    stage = (
                        {
                            "squares_float64_hex": ["0x1.0p+0", "0x1.0p+0"],
                            "np_sum_squares_float64_hex": "0x1.0p+1",
                            "np_sqrt_sum_float64_hex": "0x1.6a09e667f3bcdp+0",
                            "math_hypot_float64_hex": "0x1.6a09e667f3bcdp+0",
                        }
                        if c["operation"] == "numpy.linalg.norm" else {
                            "math_exp_float64_hex": "0x1.0p+0",
                            "numpy_exp_array_one_float64_hex": "0x1.0p+0",
                        }
                    )
                    rec["case_results"].append({
                        **deepcopy(c),
                        "result_float64_hex": "0x1.0p+0",
                        "diagnostic_stages": stage,
                    })
                results.append(rec)
    return results


class DispatchAuditTests(unittest.TestCase):
    def test_all_paired_hosts_equal_is_negative_evidence(self):
        report = compare(records())
        self.assertEqual(report["hosts"], 3)
        self.assertEqual(report["processes"], 12)
        self.assertTrue(all(not h["paired_intervention_changed_cases"]
                            for h in report["groups"]))

    def test_mask_changes_one_case_without_pretending_others_changed(self):
        data = records()
        for r in data:
            if r["replica"].startswith("r2-no-x86-v3-v4"):
                r["case_results"][3]["result_float64_hex"] = math.nextafter(
                    1.0, math.inf
                ).hex()
        report = compare(data)
        self.assertEqual(report["groups"][1]["paired_intervention_changed_cases"], [
            "norm_f17_fixed25"
        ])
        self.assertTrue(report["groups"][1]["within_arm_repeats_all_exact"])

    def test_mismatched_binary_wheels_on_same_host_rejected(self):
        data = records()
        data[1]["runtime"]["extensions_sha256"][1]["sha256"] = "3" * 64
        with self.assertRaisesRegex(ValueError, "different installed NumPy binaries"):
            compare(data)

    def test_mask_must_be_verified_as_active(self):
        data = records()
        data[3]["runtime"]["cpu_features_enabled"]["X86_V3"] = True
        with self.assertRaisesRegex(ValueError, "not actually active"):
            validate_observation(data[3])

    def test_unset_mask_environment_is_invalid(self):
        data = records()
        data[2]["runtime"]["env"]["NPY_DISABLE_CPU_FEATURES"] = None
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_observation(data[2])

    def test_modified_original_hex_operand_is_rejected(self):
        data = records()
        data[0]["case_results"][0]["hex_operands"][0] = "0x1.0p+0"
        with self.assertRaisesRegex(ValueError, "source operand"):
            compare(data)

    def test_missing_one_process_never_passes(self):
        with self.assertRaisesRegex(ValueError, "twelve processes"):
            compare(records()[:-1])

    def test_changed_host_metadata_mid_paired_test_rejected(self):
        data = records()
        data[1]["runtime"]["cpu_model"] = "different-model"
        with self.assertRaisesRegex(ValueError, "Host environment changed"):
            compare(data)

    def test_bitwise_repeat_difference_is_not_hidden(self):
        data = records()
        data[1]["case_results"][0]["result_float64_hex"] = math.nextafter(
            1.0, math.inf
        ).hex()
        report = compare(data)
        self.assertFalse(report["groups"][0]["within_arm_repeats_all_exact"])

    def test_nonfinite_diagnostic_rejected(self):
        data = records()
        data[0]["case_results"][0]["diagnostic_stages"]["np_sum_squares_float64_hex"] = "nan"
        with self.assertRaises((ValueError, OverflowError)):
            validate_observation(data[0])


if __name__ == "__main__":
    unittest.main()
