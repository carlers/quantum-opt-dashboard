"""No third-party dependencies: verify archived source and mechanical derivative."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.notebook_inventory import (
    IDENTICAL_SECOND_CELLS,
    NOTEBOOK,
    ORIGINAL_CELLS,
    ORIGINAL_SHA256,
    cell_source,
    inspect_notebook,
    load_archived_notebook,
    write_mechanical_copy,
)


class NotebookInventoryTests(unittest.TestCase):
    def test_original_bytes_and_absent_execution_records(self):
        notebook, digest = load_archived_notebook()
        self.assertEqual(digest, ORIGINAL_SHA256)
        self.assertEqual(len(notebook["cells"]), ORIGINAL_CELLS)
        self.assertEqual(hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(), digest)
        report = inspect_notebook(notebook, digest)
        self.assertEqual(report["code_cells"], 25)
        self.assertEqual(report["recorded_executions"], 0)
        self.assertEqual(report["cells_with_outputs"], 0)

    def test_similar_sections_are_not_misreported_as_identical(self):
        notebook, digest = load_archived_notebook()
        groups = inspect_notebook(notebook, digest)["repeated_sections"]
        by_pair = {tuple(group["cell_indices"]): group for group in groups}
        for pair in ((4, 5), (7, 8), (9, 10)):
            self.assertFalse(by_pair[pair]["source_identical"], pair)
            self.assertIsNotNone(by_pair[pair]["first_differing_line"])
        for pair in ((13, 14), (21, 22)):
            self.assertTrue(by_pair[pair]["source_identical"], pair)
            self.assertIsNone(by_pair[pair]["first_differing_line"])

    def test_candidate_retains_all_other_sources_and_metadata(self):
        source, _ = load_archived_notebook()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "working_copy.ipynb"
            write_mechanical_copy(source, output)
            candidate = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(candidate["cells"]), 23)
            self.assertEqual(candidate["metadata"], source["metadata"])
            self.assertEqual(candidate["nbformat"], source["nbformat"])
            expected = [
                cell for i, cell in enumerate(source["cells"])
                if i not in IDENTICAL_SECOND_CELLS
            ]
            self.assertEqual(candidate["cells"], expected)
            self.assertEqual(
                [cell_source(x) for x in candidate["cells"]],
                [cell_source(x) for x in expected],
            )

    def test_protected_source_cannot_be_overwritten(self):
        original, _ = load_archived_notebook()
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            write_mechanical_copy(original, NOTEBOOK)

    def test_modified_archive_is_rejected_before_inspection_or_copy(self):
        source, _ = load_archived_notebook()
        source["cells"][0]["source"].append("\n# accidental source mutation\n")
        with tempfile.TemporaryDirectory() as folder:
            changed = Path(folder) / "changed.ipynb"
            changed.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "immutable SHA-256"):
                load_archived_notebook(changed)

    def test_derived_file_is_never_overwritten_silently(self):
        notebook, _ = load_archived_notebook()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "copy.ipynb"
            write_mechanical_copy(notebook, output)
            with self.assertRaises(FileExistsError):
                write_mechanical_copy(notebook, output)


if __name__ == "__main__":
    unittest.main()
