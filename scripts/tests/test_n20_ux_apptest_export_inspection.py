"""Synthetic tamper tests for real Streamlit AppTest ZIP inspector.

These fixtures check decision boundaries; the genuine AppTest + real original
SCIP and lake model run only in the dual-checkout CI.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from zipfile import ZIP_DEFLATED, ZipFile
import unittest

from scripts.studies import n20_ux_apptest_export_inspection as inspect


def fixture(mode="all_stations_connected", mutation=None):
    ids = list(range(20))
    chosen = [1 if i in (0, 1, 3, 6, 7) else 0 for i in ids]
    model = {
        "dataset_sha256": inspect.EXPECTED_SOURCE_SHA,
        "settings": {"connectivity_mode": mode},
        "mapping": {
            "free_master_feature_positions": ids,
            "fixed_master_feature_positions": list(range(20, 35)),
        },
        "objective": {
            "linear_float64_hex": [float(-.1).hex()] * 20,
            "quadratic_terms": [],
        },
        "constraints": {"global_path_connectivity":
                        {"all_original_fixed_mandatory": True}
                        if mode != "source_local" else False},
        "d_max_m_float64_hex": float(1000).hex(),
    }
    graph = {
        "fingerprint_sha256": "a" * 64,
        "free_count": 20, "fixed_count": 15,
        "undirected_edges": [[0, 20], [0, 21]],
    }
    if mode != "source_local":
        model["wireless_graph"] = graph
    model["model_fingerprint_sha256"] = sha256(inspect.canonical(model)).hexdigest()
    result = {
        "model_fingerprint_sha256": model["model_fingerprint_sha256"],
    }
    if mode == "source_local":
        result.update({"scip_status": "optimal", "scip_optimal_proven": True})
    else:
        result.update({
            "connectivity_mode": mode, "optimal_proven": True,
            "search": {
                "status": "optimal_exhaustive",
                "solver": "exact_exhaustive_enumeration",
                "feasible_combinations": 860,
                "combinations_examined": 15504,
                "selected_local_positions": [0, 1, 3, 6, 7],
            },
        })
    csv_bytes = ("local_position,master_feature_position,easting_m,northing_m\n"
                 + "".join(f"{i},{i},100,100\n" for i in (0, 1, 3, 6, 7))).encode()
    files = {
        "model.json": inspect.canonical(model),
        "result.json": inspect.canonical(result),
        "selected_sites.csv": csv_bytes,
    }
    if mode == "source_local":
        files["actual_scip_model.lp"] = b"Minimize\n obj: x0\nEnd\n"
    else:
        files["wireless_graph.json"] = inspect.canonical(graph)
    if mutation is not None:
        mutation(model, result, files)
    files["SHA256SUMS.json"] = inspect.canonical({
        "files_sha256": {
            name: sha256(blob).hexdigest() for name, blob in files.items()
        }
    })
    buf = BytesIO()
    with ZipFile(buf, "w", compression=ZIP_DEFLATED) as zipfile:
        for name in sorted(files):
            zipfile.writestr(name, files[name])
    return {
        "fingerprint": model["model_fingerprint_sha256"],
        "chosen": chosen,
        "metrics": {"optimal": True, "status": (
            "optimal" if mode == "source_local" else "optimal_exhaustive"
        )},
        "independent": {"selected_local_positions": [0, 1, 3, 6, 7]},
        "zip": buf.getvalue(),
    }


class ActualAppTestZipAuditorTests(unittest.TestCase):
    def test_valid_global_export_and_no_fabricated_scip_lp(self):
        report = inspect.inspect_ui_zip(fixture(), "all_stations_connected")
        self.assertFalse(report["scip_lp_in_zip"])
        self.assertEqual(report["selected_local_positions"], [0, 1, 3, 6, 7])
        self.assertTrue(report["all_evidence_file_checksums_verified"])
        self.assertEqual(report["global_graph_edges"], [[0, 20], [0, 21]])
        self.assertTrue(report["not_independently_authenticated_live_user_session"])

    def test_valid_original_scip_lp_only_local(self):
        report = inspect.inspect_ui_zip(fixture("source_local"), "source_local")
        self.assertTrue(report["scip_lp_in_zip"])
        self.assertIsNone(report["global_graph_edges"])

    def test_fake_session_fingerprint_rejected(self):
        record = fixture()
        record["fingerprint"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            inspect.inspect_ui_zip(record, "all_stations_connected")

    def test_forged_sha256sum_rejected(self):
        def tamper(model, result, files):
            altered = deepcopy(model)
            altered["dataset_sha256"] = "f" * 64
            files["model.json"] = inspect.canonical(altered)
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            inspect.inspect_ui_zip(fixture(mutation=tamper), "all_stations_connected")

    def test_selected_csv_master_site_mismatch_rejected(self):
        def tamper(model, result, files):
            files["selected_sites.csv"] = files["selected_sites.csv"].replace(
                b"0,0,100,100", b"0,999,100,100"
            )
        with self.assertRaisesRegex(ValueError, "source site master"):
            inspect.inspect_ui_zip(fixture(mutation=tamper), "all_stations_connected")

    def test_fake_global_scip_lp_rejected(self):
        def tamper(model, result, files):
            files["actual_scip_model.lp"] = b"fake"
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            inspect.inspect_ui_zip(fixture(mutation=tamper), "all_stations_connected")

    def test_global_timeout_falsely_claimed_optimal_rejected(self):
        def tamper(model, result, files):
            result["search"]["status"] = "time_limit_no_certified_optimum"
            files["result.json"] = inspect.canonical(result)
        with self.assertRaisesRegex(ValueError, "unproved"):
            inspect.inspect_ui_zip(fixture(mutation=tamper), "all_stations_connected")

    def test_missing_original_fixed_station_refused(self):
        def tamper(model, result, files):
            model["mapping"]["fixed_master_feature_positions"].pop()
            model.pop("model_fingerprint_sha256")
            model["model_fingerprint_sha256"] = sha256(inspect.canonical(model)).hexdigest()
            result["model_fingerprint_sha256"] = model["model_fingerprint_sha256"]
            files["model.json"] = inspect.canonical(model)
            files["result.json"] = inspect.canonical(result)
        with self.assertRaisesRegex(ValueError, "fixed/new ordered"):
            inspect.inspect_ui_zip(fixture(mutation=tamper), "all_stations_connected")

    def test_csv_tamper_without_sha_update_rejected(self):
        a = fixture()
        original = a["zip"]
        with ZipFile(BytesIO(original)) as z:
            content = {name: z.read(name) for name in z.namelist()}
        content["selected_sites.csv"] = content["selected_sites.csv"].replace(
            b"0,0,100,100", b"0,999,100,100"
        )
        b = BytesIO()
        with ZipFile(b, "w", ZIP_DEFLATED) as z:
            for name in sorted(content):
                z.writestr(name, content[name])
        a["zip"] = b.getvalue()
        with self.assertRaisesRegex(ValueError, "checksum"):
            inspect.inspect_ui_zip(a, "all_stations_connected")

    def test_changed_current_binary_selected_flags_rejected(self):
        a = fixture()
        a["chosen"] = [1] * 20
        with self.assertRaisesRegex(ValueError, "five selected"):
            inspect.inspect_ui_zip(a, "all_stations_connected")


if __name__ == "__main__":
    unittest.main()
