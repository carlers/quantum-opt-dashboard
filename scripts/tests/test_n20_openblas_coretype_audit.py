"""Adversarial immutable-sample and same-host OpenBLAS target checks."""
from __future__ import annotations

from copy import deepcopy
import math
import unittest

from scripts.n20_frozen_math_microprobe import FROZEN_CASES, fingerprint
from scripts.n20_openblas_coretype_audit import (
    ARMS, STUDY, compare, verify_record,
)


def synthetic():
    out = []
    for h in range(1, 4):
        for arm in ARMS:
            for repeat in ("a", "b"):
                arch = ("SkylakeX" if arm == "auto" and h < 3 else "Haswell")
                out.append({
                    "schema_version": 1,
                    "study": STUDY,
                    "arm": arm,
                    "replica": f"r{h}-{arm}-{repeat}",
                    "frozen_input_sha256": fingerprint(FROZEN_CASES),
                    "openblas_coretype_env": ARMS[arm],
                    "openblas_selected_architecture": arch,
                    "runtime": {
                        "numpy": "2.5.4", "python": "3.12.15",
                        "machine": "x86_64", "libc": ["glibc", "2.39"],
                        "cpu_model": f"synthetic-{h}",
                        "show_runtime_allowlisted": [{
                            "architecture": arch, "internal_api": "openblas",
                            "user_api": "blas",
                        }],
                        "extensions_sha256": [{
                            "basename": f"test-{i}.so", "sha256": str(i) * 64,
                        } for i in range(1, 4)],
                    },
                    "case_results": [{
                        **deepcopy(c), "result_float64_hex": "0x1.0p+0",
                        "diagnostic_stages": (
                            {"squares_float64_hex": ["0x1.0p+0", "0x1.0p+0"]}
                            if c["operation"] == "numpy.linalg.norm" else
                            {"math_exp_float64_hex": "0x1.0p+0"}
                        ),
                    } for c in FROZEN_CASES],
                })
    return out


class OpenBLASCoretypeTests(unittest.TestCase):
    def test_negative_result_all_12_fresh_processes(self):
        res = compare(synthetic())
        self.assertEqual(res["total_processes"], 12)
        self.assertTrue(all(h["within_arm_repeatable"] for h in res["hosts"]))
        self.assertTrue(all(not x for x in res["observed_target_changes"].values()))

    def test_exact_norm_change_under_forced_target_not_hidden(self):
        cases = synthetic()
        for c in cases:
            if c["replica"].startswith("r1-haswell"):
                c["case_results"][1]["result_float64_hex"] = math.nextafter(
                    1.0, math.inf
                ).hex()
        r = compare(cases)
        self.assertEqual(r["observed_target_changes"]["r1"], ["norm_f9_fixed26"])
        self.assertTrue(r["hosts"][0]["within_arm_repeatable"])

    def test_unsupported_forced_target_rejected(self):
        cases = synthetic()
        cases[2]["openblas_selected_architecture"] = "SkylakeX"
        cases[2]["runtime"]["show_runtime_allowlisted"][0]["architecture"] = "SkylakeX"
        with self.assertRaisesRegex(ValueError, "Haswell override"):
            verify_record(cases[2])

    def test_altered_source_operand_rejected(self):
        cases = synthetic()
        cases[3]["case_results"][0]["hex_operands"][0] = "0x1.0p+0"
        with self.assertRaisesRegex(ValueError, "source input"):
            compare(cases)

    def test_changed_compiled_library_on_same_host_rejected(self):
        cases = synthetic()
        cases[0]["runtime"]["extensions_sha256"][0]["sha256"] = "9" * 64
        with self.assertRaisesRegex(ValueError, "compiled binary drift"):
            compare(cases)

    def test_unexpected_numpy_simd_control_is_not_conflated(self):
        cases = synthetic()
        cases[2]["openblas_coretype_env"] = "DYNAMIC"
        with self.assertRaisesRegex(ValueError, "preregistered"):
            verify_record(cases[2])

    def test_mismatched_one_process_count_fails(self):
        with self.assertRaisesRegex(ValueError, "12 independent"):
            compare(synthetic()[:-1])

    def test_one_different_repeat_is_observable(self):
        cases = synthetic()
        cases[1]["case_results"][0]["result_float64_hex"] = math.nextafter(
            1.0, math.inf
        ).hex()
        report = compare(cases)
        self.assertFalse(report["hosts"][0]["within_arm_repeatable"])


if __name__ == "__main__":
    unittest.main()
