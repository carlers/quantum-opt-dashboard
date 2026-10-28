"""Fast original-source tests: synthetic notebook mutation + actual frozen bytes.

No data export, solver, network, notebook execution or third-party imports.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

# Legacy water-quality CI uses the pytest entrypoint, which does not insert
# the repository root into sys.path. Import this read-only repo script explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.verify_research_sources import (
    ANCHORS, CATALOG, GEOJSON, NOTEBOOK, SourceIntegrityError,
    _check_notebook, _load_json_no_duplicates, _safe_raw, verify,
)


def synthetic_notebook():
    return {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {},
        "cells": [
            {"cell_type": "code", "id": f"synthetic{i:02d}", "metadata": {},
             "execution_count": None, "outputs": [], "source": ["x = 1\n"]}
            for i in range(25)
        ],
    }


def encoded(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


class OriginalSourceIntegrityTests(unittest.TestCase):
    def test_real_historical_source_hashes_and_notebook_are_preserved(self):
        result = verify()
        self.assertTrue(result["original_source_bytes_verified"])
        self.assertEqual(result["original_geojson_sha256"], ANCHORS[GEOJSON])
        self.assertEqual(result["original_notebook_sha256"], ANCHORS[NOTEBOOK])
        self.assertFalse(result["historical_notebook_executed"])
        self.assertFalse(result["paper_or_worldpop_parity_proven"])
        self.assertFalse(result["redistribution_rights_verified"])

    def test_original_catalog_is_explicitly_not_redistribution_license(self):
        manifest = json.loads(CATALOG.read_text())
        self.assertTrue(manifest["not_redistribution_authorization"])
        self.assertTrue(manifest["not_manuscript_dataset_parity"])
        self.assertEqual(len(manifest["sources"]), 2)
        self.assertTrue(all(s["rights_status"] == "not_independently_verified"
                            for s in manifest["sources"]))

    def test_synthetic_notebook_shape_is_valid(self):
        self.assertEqual(_check_notebook(encoded(synthetic_notebook())), 25)

    def test_stored_result_is_rejected(self):
        nb = synthetic_notebook()
        nb["cells"][0]["outputs"] = [{"output_type": "stream", "text": ["secret"]}]
        with self.assertRaises(SourceIntegrityError):
            _check_notebook(encoded(nb))

    def test_historical_executed_cell_rejected(self):
        nb = synthetic_notebook()
        nb["cells"][3]["execution_count"] = 12
        with self.assertRaises(SourceIntegrityError):
            _check_notebook(encoded(nb))

    def test_duplicate_cell_id_rejected(self):
        nb = synthetic_notebook()
        nb["cells"][3]["id"] = nb["cells"][4]["id"]
        with self.assertRaises(SourceIntegrityError):
            _check_notebook(encoded(nb))

    def test_added_or_removed_historical_cell_rejected(self):
        nb = synthetic_notebook()
        nb["cells"].pop()
        with self.assertRaises(SourceIntegrityError):
            _check_notebook(encoded(nb))

    def test_markdown_cell_rejected_as_original(self):
        nb = synthetic_notebook()
        nb["cells"][0]["cell_type"] = "markdown"
        with self.assertRaises(SourceIntegrityError):
            _check_notebook(encoded(nb))

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(SourceIntegrityError):
            _load_json_no_duplicates(b'{"schema":"a","schema":"b"}')

    def test_symlinked_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "real").write_text("historical bytes")
            (root / "fake").symlink_to("real")
            with self.assertRaises(SourceIntegrityError):
                _safe_raw(root, "fake", 100)

    def test_source_with_non_matching_catalog_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "catalog.json"
            manifest = json.loads(CATALOG.read_text())
            manifest["sources"][0]["sha256"] = "0" * 64
            target.write_text(json.dumps(manifest))
            with self.assertRaises(SourceIntegrityError):
                verify(catalog_path=target)

    def test_source_catalog_cannot_claim_licensed(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "catalog.json"
            manifest = json.loads(CATALOG.read_text())
            manifest["sources"][0]["rights_status"] = "authorized"
            target.write_text(json.dumps(manifest))
            with self.assertRaises(SourceIntegrityError):
                verify(catalog_path=target)

    def test_historical_sources_are_never_modified_by_verifier(self):
        first = verify()
        second = verify()
        self.assertEqual(first, second)

    def test_verifier_does_not_import_solver_or_upload(self):
        src = (Path(__file__).resolve().parents[3] / "scripts" /
               "verify_research_sources.py").read_text()
        for fragment in ("import oci", "from oci", "import requests",
                         "import numpy", "import pyscipopt", "exec(", "subprocess",
                         "put_object(", "terraform apply", "papermill"):
            self.assertNotIn(fragment, src)


if __name__ == "__main__":
    unittest.main()
