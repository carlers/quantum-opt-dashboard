"""Synthetic malicious/corrupt evidence archives must never pass preservation check."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from scripts.verify_research_evidence_bundle import validate_bundle


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def nested_zip(filename: str = "record.json", content: bytes = b'{"n":20}\n') -> bytes:
    out = io.BytesIO()
    with ZipFile(out, "w") as z:
        z.writestr(filename, content)
    return out.getvalue()


def make_bundle(
    root: Path,
    *, filename: str = "science-original.zip",
    raw_inside: bytes = b'{"n":20}\n',
    nested_name: str = "record.json",
    change=None,
) -> Path:
    original = nested_zip(nested_name, raw_inside)
    entry = {
        "filename": filename,
        "bytes": len(original),
        "sha256": sha(original),
        "source_run_id": None,
        "source_artifact_id": None,
        "source_artifact_url": None,
        "entries": [{
            "path": nested_name,
            "bytes": len(raw_inside),
            "sha256": sha(raw_inside),
        }],
    }
    manifest = {
        "schema_version": 1, "project": "carlers/quantum-opt-dashboard",
        "included_archives": 1, "entries": [entry],
    }
    file_name = "evidence/" + filename
    contents = {
        "README.md": b"owner-held zip\n",
        "MANIFEST.json": b"",
        "SHA256SUMS": b"",
        file_name: original,
    }
    if change:
        change(manifest, contents)
    contents["MANIFEST.json"] = json.dumps(manifest).encode()
    contents["SHA256SUMS"] = "".join(
        f"{e['sha256']}  evidence/{e['filename']}\n"
        for e in manifest["entries"]
    ).encode()
    path = root / "private-evidence.zip"
    with ZipFile(path, "w") as z:
        for name, blob in contents.items():
            z.writestr(name, blob)
    return path


class EvidenceBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_verified_original_artifact_and_member(self):
        path = make_bundle(self.root)
        report = validate_bundle(path, sha(path.read_bytes()))
        self.assertEqual(report["status"], "verified")
        self.assertEqual(report["artifact_zip_files"], 1)
        self.assertEqual(report["nested_evidence_members"], 1)

    def test_wrong_independent_outer_bundle_digest_fails(self):
        path = make_bundle(self.root)
        with self.assertRaisesRegex(ValueError, "independent owner manifest"):
            validate_bundle(path, "0" * 64)

    def test_changed_outer_original_zip_bytes_fails(self):
        def corrupt(m, contents):
            contents["evidence/science-original.zip"] += b"malicious trailing data"
        with self.assertRaisesRegex(ValueError, "Original artifact SHA-256"):
            validate_bundle(make_bundle(self.root, change=corrupt))

    def test_changed_nested_member_rejected_even_if_outer_digest_updated(self):
        def altered(m, contents):
            changed = nested_zip("record.json", b'{"n":19}\n')
            contents["evidence/science-original.zip"] = changed
            m["entries"][0]["sha256"] = sha(changed)
            m["entries"][0]["bytes"] = len(changed)
            # Deliberately retain old nested member SHA manifest.
        with self.assertRaisesRegex(ValueError, "Nested result SHA-256"):
            validate_bundle(make_bundle(self.root, change=altered))

    def test_unsafe_nested_path_in_zip_fails(self):
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            validate_bundle(make_bundle(self.root, nested_name="../private.txt"))

    def test_unmanifested_extra_outer_file_fails(self):
        def extra(m, contents):
            contents["secret.txt"] = b"unspecified"
        with self.assertRaisesRegex(ValueError, "Unexpected files"):
            validate_bundle(make_bundle(self.root, change=extra))

    def test_duplicate_manifest_entries_rejected(self):
        def repeated(m, contents):
            m["entries"].append(deepcopy(m["entries"][0]))
            m["included_archives"] = 2
        with self.assertRaisesRegex(ValueError, "Duplicate artifact filename"):
            validate_bundle(make_bundle(self.root, change=repeated))

    def test_missing_original_artifact_rejected(self):
        def missing(m, contents):
            del contents["evidence/science-original.zip"]
        with self.assertRaisesRegex(ValueError, "Missing original GitHub artifact"):
            validate_bundle(make_bundle(self.root, change=missing))

    def test_nested_member_missing_fails(self):
        def bad_entry(m, contents):
            m["entries"][0]["entries"][0]["path"] = "different-file.json"
        with self.assertRaisesRegex(ValueError, "Missing original nested study result"):
            validate_bundle(make_bundle(self.root, change=bad_entry))

    def test_invalid_original_filename_fails(self):
        def bad_name(m, contents):
            m["entries"][0]["filename"] = "../science-original.zip"
        with self.assertRaisesRegex(ValueError, "Invalid original artifact ZIP filename"):
            validate_bundle(make_bundle(self.root, change=bad_name))

    def test_missing_sha256s_is_rejected(self):
        def bad(m, contents):
            del contents["SHA256SUMS"]
        with self.assertRaisesRegex(ValueError, "Missing original README"):
            validate_bundle(make_bundle(self.root, change=bad))

    def test_manifest_record_count_mismatch_fails(self):
        def bad(m, contents):
            m["included_archives"] = 2
        with self.assertRaisesRegex(ValueError, "declared archive count"):
            validate_bundle(make_bundle(self.root, change=bad))


if __name__ == "__main__":
    unittest.main()
