"""Small domain-neutral, versioned *synthetic-only* experiment bundle loader.

Not the unfinished workflow plug-in manifest in contracts/problem_manifest.schema.json.
No eval, arbitrary scripts, internet imports, or unapproved real-world data.
Scientific adapters individually validate their own data model and parameters.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any


MAX_JSON_BYTES = 1_000_000
_ID = re.compile(r"^[a-z][a-z0-9_.-]{2,63}$")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _parse_json(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) > MAX_JSON_BYTES:
        raise ValueError("Input JSON exceeds prototype size limit")
    def bad_constant(value: str):
        raise ValueError(f"Nonfinite JSON token: {value}")
    result = json.loads(data, parse_constant=bad_constant)
    if type(result) is not dict:
        raise ValueError("Expected a JSON object")
    return result


def _only_keys(record: dict, allowed: set[str], required: set[str], name: str) -> None:
    if set(record) - allowed or required - set(record):
        raise ValueError(f"{name}: missing or unknown fields: " +
                         str(sorted((set(record) - allowed) | (required - set(record)))))


def _safe_child(root: Path, relative: str) -> Path:
    if type(relative) is not str or not relative.endswith(".json"):
        raise ValueError("Dataset must be a relative JSON path")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts or "." in candidate.parts:
        raise ValueError("Absolute/traversal dataset path forbidden")
    base = root.resolve(strict=True)
    part = base
    for token in candidate.parts:
        part = part / token
        if part.is_symlink():
            raise ValueError("Dataset symlink forbidden")
    target = part.resolve(strict=True)
    if not target.is_relative_to(base) or not target.is_file():
        raise ValueError("Dataset escapes declared bundle directory")
    return target


@dataclass(frozen=True)
class Bundle:
    source_manifest: dict
    data: dict
    dataset_sha256: str
    manifest_sha256: str
    fingerprint: str
    dataset_path: Path

    @property
    def problem_id(self) -> str:
        return self.source_manifest["problem_id"]

    @property
    def formulation_id(self) -> str:
        return self.source_manifest["formulation_id"]

    @property
    def parameters(self) -> dict:
        return self.source_manifest["parameters"]

    def audit(self) -> dict:
        return {
            "schema_version": 1,
            "problem_id": self.problem_id,
            "formulation_id": self.formulation_id,
            "dataset_sha256": self.dataset_sha256,
            "manifest_sha256": self.manifest_sha256,
            "resolved_bundle_fingerprint_sha256": self.fingerprint,
            "parameters": self.parameters,
            "data_classification": "SYNTHETIC",
            "source_manifest": self.source_manifest,
            "actual_dataset": self.data,
            "note": "Exact input is included for this tiny synthetic example. Real data requires separate access/redaction rights.",
        }


def load_bundle(manifest_path: Path) -> Bundle:
    manifest_path = Path(manifest_path)
    root = manifest_path.resolve(strict=True).parent
    if manifest_path.is_symlink() or manifest_path.suffix != ".json":
        raise ValueError("Expected a non-symlink JSON bundle manifest")
    manifest = _parse_json(manifest_path)
    _only_keys(manifest,
               {"schema_version", "problem_id", "formulation_id", "dataset",
                "parameters", "classification", "description"},
               {"schema_version", "problem_id", "formulation_id", "dataset",
                "parameters", "classification"}, "bundle")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("Unsupported experiment bundle schema version")
    if manifest["classification"] != "SYNTHETIC":
        raise ValueError("Only SYNTHETIC example data supported; no real facility files")
    if any(type(manifest[k]) is not str or not _ID.fullmatch(manifest[k])
           for k in ("problem_id", "formulation_id")):
        raise ValueError("Invalid problem/formulation registry identifier")
    if type(manifest["parameters"]) is not dict:
        raise ValueError("Parameters must be a JSON object")
    if "description" in manifest and (
        type(manifest["description"]) is not str or len(manifest["description"]) > 500
    ):
        raise ValueError("Invalid description")
    spec = manifest["dataset"]
    if type(spec) is not dict:
        raise ValueError("Dataset must be an object")
    _only_keys(spec, {"path", "expected_sha256"}, {"path"}, "dataset")
    source = _safe_child(root, spec["path"])
    data_bytes = source.read_bytes()
    digest = sha256(data_bytes).hexdigest()
    expected = spec.get("expected_sha256")
    if expected is not None and (
        type(expected) is not str or
        not re.fullmatch(r"[0-9a-f]{64}", expected) or digest != expected
    ):
        raise ValueError("Dataset expected_sha256 mismatch")
    data = _parse_json(source)
    manifest_digest = sha256(manifest_path.read_bytes()).hexdigest()
    # Content-based scientific fingerprint: changing data contents, selected
    # formulation OR typed parameters changes it (no path identity assumptions).
    fingerprint = sha256(canonical({
        "schema_version": 1, "problem_id": manifest["problem_id"],
        "formulation_id": manifest["formulation_id"],
        "parameters": manifest["parameters"], "dataset_sha256": digest,
    })).hexdigest()
    return Bundle(manifest, data, digest, manifest_digest, fingerprint, source)
