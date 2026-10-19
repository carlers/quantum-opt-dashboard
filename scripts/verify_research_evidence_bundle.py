"""Verify the private owner-held GitHub Actions evidence pack without publishing it.

Stdlib-only. Checks independently pinned full-bundle SHA (if given), outer ZIP
integrity, exact original artifact ZIP hashes and nested file bytes, member
names, sizes, SHA-256, duplicates, and SHA256SUMS parity. No network or upload.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
from zipfile import ZipFile, BadZipFile

HEX256 = re.compile(r"^[0-9a-f]{64}$")
MAX_INNER_ZIP_BYTES = 250 * 1024 * 1024
REQUIRED_OUTER = {"README.md", "MANIFEST.json", "SHA256SUMS"}


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def safe_path(value: str, *, prefix: str | None = None) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Unsafe or invalid evidence archive member path")
    p = PurePosixPath(value)
    if (p.is_absolute() or str(p) != value or
            any(c in {"..", ".", ""} for c in value.split("/"))):
        raise ValueError("Unsafe evidence archive member path")
    if prefix and not value.startswith(prefix):
        raise ValueError("Evidence archive outside expected safe prefix")
    return value


def zip_members(z: ZipFile) -> list[str]:
    names = [i.filename for i in z.infolist()]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate ZIP entries are not permitted")
    if any(i.is_dir() for i in z.infolist()):
        raise ValueError("Evidence bundle must contain files only")
    for x in names:
        safe_path(x)
    if z.testzip() is not None:
        raise ValueError("ZIP corruption detected")
    return names


def validate_bundle(path: Path, expected_sha256: str | None = None) -> dict:
    if expected_sha256 is not None and not HEX256.fullmatch(expected_sha256):
        raise ValueError("Expected SHA-256 must be exactly 64 lowercase hex digits")
    if not path.is_file():
        raise FileNotFoundError(path)
    raw_bundle = path.read_bytes()
    bundle_sha = digest(raw_bundle)
    if expected_sha256 is not None and expected_sha256 != bundle_sha:
        raise ValueError("Private bundle SHA-256 differs from independent owner manifest")
    with ZipFile(io.BytesIO(raw_bundle)) as outer:
        names = zip_members(outer)
        if not REQUIRED_OUTER.issubset(names):
            raise ValueError("Missing original README, manifest or SHA256SUMS")
        spec = json.loads(outer.read("MANIFEST.json"))
        if (not isinstance(spec, dict) or spec.get("schema_version") != 1
                or spec.get("project") != "carlers/quantum-opt-dashboard"):
            raise ValueError("Unknown research evidence manifest/schema")
        items = spec.get("entries")
        if not isinstance(items, list) or len(items) != spec.get("included_archives"):
            raise ValueError("Manifest declared archive count is inconsistent")
        stored = set(REQUIRED_OUTER)
        sha_lines = []
        n_inner = 0
        for entry in items:
            if not isinstance(entry, dict):
                raise ValueError("Malformed archived artifact manifest row")
            filename = entry.get("filename")
            if (not isinstance(filename, str) or "/" in filename
                    or not filename.endswith(".zip")):
                raise ValueError("Invalid original artifact ZIP filename")
            safe_path(filename)
            name = "evidence/" + filename
            if name in stored:
                raise ValueError("Duplicate artifact filename in original manifest")
            stored.add(name)
            if name not in names:
                raise ValueError(f"Missing original GitHub artifact: {filename}")
            blob = outer.read(name)
            if (len(blob) != entry.get("bytes") or
                    digest(blob) != entry.get("sha256")):
                raise ValueError(f"Original artifact SHA-256 or length changed: {filename}")
            if len(blob) > MAX_INNER_ZIP_BYTES:
                raise ValueError("Archived input too large for safe bounded verifier")
            sha_lines.append(f"{entry['sha256']}  {name}\n")
            try:
                with ZipFile(io.BytesIO(blob)) as nested:
                    original_members = zip_members(nested)
                    documented = entry.get("entries")
                    if not isinstance(documented, list):
                        raise ValueError("Missing nested artifact member manifest")
                    if len(original_members) != len(documented):
                        raise ValueError("Nested ZIP member count differs from manifest")
                    used = set()
                    for inner in documented:
                        pname = safe_path(inner["path"])
                        if pname in used:
                            raise ValueError("Duplicate nested original member manifest")
                        used.add(pname)
                        if pname not in original_members:
                            raise ValueError("Missing original nested study result")
                        data = nested.read(pname)
                        if (len(data) != inner["bytes"] or
                                digest(data) != inner["sha256"]):
                            raise ValueError("Nested result SHA-256 differs from original")
                    if set(original_members) != used:
                        raise ValueError("Unmanifested nested evidence member")
                    n_inner += len(used)
            except BadZipFile as exc:
                raise ValueError("Original artifact cannot be read as ZIP") from exc
        if set(names) != stored:
            raise ValueError("Unexpected files outside the complete original manifest")
        if outer.read("SHA256SUMS").decode("utf-8") != "".join(sha_lines):
            raise ValueError("SHA256SUMS disagrees with manifest order or exact hashes")
    return {
        "status": "verified",
        "bundle_sha256": bundle_sha,
        "artifact_zip_files": len(items),
        "nested_evidence_members": n_inner,
        "source_artifact_links_verified_in_manifest": sum(
            e.get("source_artifact_url") is not None for e in items
        ),
        "warning": (
            "Internal integrity does not prove experimental correctness, full historical "
            "coverage, original-data licensing, or long-term external custody."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", required=True, type=Path)
    p.add_argument(
        "--expected-sha256",
        help="Independent expected outer SHA (e.g. from owner evidence inventory)",
    )
    opts = p.parse_args()
    result = validate_bundle(opts.bundle, opts.expected_sha256)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
