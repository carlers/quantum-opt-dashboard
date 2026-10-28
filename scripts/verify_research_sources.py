"""Fast, stdlib-only immutable-source gate for the original Laguna de Bay study.

Do not execute the notebook, import the scientific model, fetch external inputs,
edit research bytes, invoke a solver, or declare manuscript parity. The pinned
checksums are original-file fingerprints, not signatures or data-use licenses.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs/research_protocols/original_water_sources_v1.json"
NOTEBOOK = "problems/water_quality/notebooks/experiment9 grid search copy.ipynb"
GEOJSON = "problems/water_quality/data/LDB_centroids_clean.geojson"
# Independent in-code cold-source canaries. A catalog change alone cannot
# redefine the original source fingerprints without a code review.
ANCHORS = {
    NOTEBOOK: "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048",
    GEOJSON: "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7",
}
MAX_FILE_BYTES = {NOTEBOOK: 500_000, GEOJSON: 5_000_000}
SCHEMA = "original-water-quality-research-sources-v1"


class SourceIntegrityError(ValueError):
    """Original input/provenance contract violation; does not print file bytes."""


def _load_json_no_duplicates(raw: bytes):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise SourceIntegrityError("Duplicate JSON object key")
            obj[key] = value
        return obj

    try:
        return json.loads(raw, object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceIntegrityError("Invalid source JSON") from exc


def _safe_raw(root: Path, relative: str, limit: int):
    target = root / relative
    if target.is_symlink() or not target.is_file():
        raise SourceIntegrityError("Required regular source file missing")
    # Never silently follow a source symlink or an outside-project ancestor.
    if not target.resolve().is_relative_to(root.resolve()):
        raise SourceIntegrityError("Source path escapes checked-out repository")
    size = target.stat().st_size
    if not 0 < size <= limit:
        raise SourceIntegrityError("Source size outside bounded contract")
    return target.read_bytes()


def _check_notebook(raw: bytes):
    nb = _load_json_no_duplicates(raw)
    if not isinstance(nb, dict) or nb.get("nbformat") != 4:
        raise SourceIntegrityError("Original notebook format changed")
    cells = nb.get("cells")
    if not isinstance(cells, list) or len(cells) != 25:
        raise SourceIntegrityError("Original notebook cell count changed")
    identities = set()
    for i, cell in enumerate(cells):
        if not isinstance(cell, dict) or cell.get("cell_type") != "code":
            raise SourceIntegrityError("Original notebook code-cell structure changed")
        identity = cell.get("id")
        if (not isinstance(identity, str)
                or re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", identity) is None
                or identity in identities):
            raise SourceIntegrityError("Missing or duplicate notebook cell ID")
        identities.add(identity)
        if cell.get("execution_count") is not None or cell.get("outputs") != []:
            raise SourceIntegrityError("Historical notebook must stay output-free")
        source = cell.get("source")
        if not isinstance(source, (list, str)):
            raise SourceIntegrityError("Malformed notebook source cell")
    return len(cells)


def verify(root: Path = ROOT, catalog_path: Path | None = None):
    """Verify immutable historical inputs. Never mutates source or executes code."""
    root = Path(root)
    catalog_path = CATALOG if catalog_path is None else Path(catalog_path)
    if catalog_path.is_symlink() or not catalog_path.is_file():
        raise SourceIntegrityError("Source catalog unavailable")
    if catalog_path.stat().st_size > 16_384:
        raise SourceIntegrityError("Catalog is unexpectedly large")
    catalog = _load_json_no_duplicates(catalog_path.read_bytes())
    if (not isinstance(catalog, dict) or catalog.get("schema") != SCHEMA
            or catalog.get("not_manuscript_dataset_parity") is not True
            or catalog.get("not_redistribution_authorization") is not True
            or catalog.get("not_solver_execution") is not True):
        raise SourceIntegrityError("Catalog schema or limitation flags changed")
    items = catalog.get("sources")
    if not isinstance(items, list) or len(items) != len(ANCHORS):
        raise SourceIntegrityError("Expected exactly two original input records")
    observed = {}
    for item in items:
        if not isinstance(item, dict) or set(item) != {
            "path", "sha256", "git_blob_sha1", "role", "rights_status"
        }:
            raise SourceIntegrityError("Unexpected catalog record")
        path = item["path"]
        if not isinstance(path, str) or path not in ANCHORS or path in observed:
            raise SourceIntegrityError("Unknown or repeated source file")
        if item["sha256"] != ANCHORS[path]:
            raise SourceIntegrityError("Catalog source hash differs from pinned original")
        if item["rights_status"] != "not_independently_verified":
            raise SourceIntegrityError("Source rights must remain unverified")
        if item["role"] != ("historical_notebook" if path == NOTEBOOK else "historical_geojson"):
            raise SourceIntegrityError("Source role changed")
        raw = _safe_raw(root, path, MAX_FILE_BYTES[path])
        actual = sha256(raw).hexdigest()
        if actual != ANCHORS[path]:
            raise SourceIntegrityError("Original source checksum changed")
        # Git object identity detects accidental normalization, re-encoding,
        # stripping or repacking of this fixed byte sequence.
        from hashlib import sha1
        git_blob = sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        if item["git_blob_sha1"] != git_blob:
            raise SourceIntegrityError("Original Git blob identity changed")
        if path == NOTEBOOK:
            _check_notebook(raw)
        observed[path] = {"sha256": actual, "git_blob_sha1": git_blob}
    if set(observed) != set(ANCHORS):
        raise SourceIntegrityError("Required historical source absent")
    return {
        "schema": "original-water-quality-source-audit-result-v1",
        "original_source_bytes_verified": True,
        "historical_notebook_executed": False,
        "original_geojson_sha256": observed[GEOJSON]["sha256"],
        "original_notebook_sha256": observed[NOTEBOOK]["sha256"],
        "paper_or_worldpop_parity_proven": False,
        "redistribution_rights_verified": False,
        "current_research_model_validated_by_this_check": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        report = verify()
    except SourceIntegrityError as exc:
        print("source-provenance check FAILED: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
