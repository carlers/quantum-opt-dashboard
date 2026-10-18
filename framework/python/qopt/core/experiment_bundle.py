"""Small domain-neutral, versioned *synthetic-only* experiment bundle loader.

Not the unfinished workflow plug-in manifest in contracts/problem_manifest.schema.json.
No eval, arbitrary scripts, internet imports, or unapproved real-world data.
Scientific adapters individually validate their own data model and parameters.
"""
from __future__ import annotations

import csv
from io import StringIO
from math import isfinite
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any


MAX_JSON_BYTES = 1_000_000
MAX_PINNED_GEOJSON_BYTES = 5_000_000
# Exactly the unchanged archived lake GeoJSON, NOT a blanket real-data upload permit.
PINNED_WATER_REFERENCE_SHA = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
_ID = re.compile(r"^[a-z][a-z0-9_.-]{2,63}$")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _parse_json(path: Path, *, limit: int = MAX_JSON_BYTES) -> dict:
    data = path.read_bytes()
    if len(data) > limit:
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
    if type(relative) is not str or Path(relative).suffix not in (".json", ".geojson", ".csv"):
        raise ValueError("Dataset must be a relative JSON, GeoJSON or CSV path")
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


def _load_csv_binary_objective(path: Path) -> dict:
    """Explicit synthetic 2-column CSV -> binary-quadratic *linear* IR.

    The original source bytes are still fingerprinted. Only this declared
    CSV profile is supported: not arbitrary CSV schema or source code.
    """
    raw = path.read_bytes()
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("CSV exceeds bounded synthetic research input limit")
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8") from exc
    if "\\x00" in decoded:
        raise ValueError("CSV must not contain NUL bytes")
    records = csv.DictReader(StringIO(decoded), strict=True)
    if records.fieldnames != ["variable", "linear_coefficient"]:
        raise ValueError("CSV requires exactly variable,linear_coefficient header")
    variables: list[str] = []
    linear: dict[str, float] = {}
    for row in records:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("CSV has extra or missing columns")
        name = row["variable"]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,31}", name) or name in linear:
            raise ValueError("Duplicate/invalid CSV variable ID")
        try:
            value = float(row["linear_coefficient"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid CSV linear coefficient") from exc
        if not isfinite(value) or abs(value) > 1e10:
            raise ValueError("Invalid/nonfinite CSV linear coefficient")
        variables.append(name)
        linear[name] = value
    if not 1 <= len(variables) <= 16:
        raise ValueError("CSV synthetic variables must number 1..16")
    return {
        "classification": "SYNTHETIC_BINARY_QUADRATIC",
        "variables": variables,
        "objective": {
            "sense": "minimize", "constant": 0,
            "linear": linear, "quadratic": [],
        },
        "constraints": [{
            "id": "budget", "sense": "<=", "rhs": len(variables),
            "linear": {name: 1 for name in variables},
        }],
    }


@dataclass(frozen=True)
class Bundle:
    source_manifest: dict
    data: dict
    dataset_sha256: str
    manifest_sha256: str
    fingerprint: str
    dataset_path: Path
    source_format: str

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
            "data_classification": self.source_manifest["classification"],
            "source_format": self.source_format,
            "source_manifest": self.source_manifest,
            "actual_dataset": self.data if self.source_manifest["classification"] == "SYNTHETIC" else {
                "feature_count": len(self.data.get("features", [])),
                "raw_data_omitted": True,
                "note": "Source is the immutable SHA-verified committed original lake GeoJSON; do not redistribute as generic user-upload data.",
            },
            "note": "Exact synthetic source is included; historical lake source remains an immutable hashed reference, not a generic upload permit.",
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
    if manifest["classification"] not in ("SYNTHETIC", "RESEARCH_REFERENCE"):
        raise ValueError("Only SYNTHETIC or explicitly pinned RESEARCH_REFERENCE supported")
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
    suffix = source.suffix
    if manifest["classification"] == "RESEARCH_REFERENCE":
        if (manifest["problem_id"] != "water_quality.reference" or
            manifest["formulation_id"] != "notebook_one_hop_milp" or
            suffix != ".geojson" or digest != PINNED_WATER_REFERENCE_SHA or
            expected != PINNED_WATER_REFERENCE_SHA):
            raise ValueError("Historical water-quality reference requires exact allowlisted source SHA and formulation")
    if suffix == ".csv":
        if manifest["classification"] != "SYNTHETIC" or (
            manifest["problem_id"], manifest["formulation_id"]
        ) != ("binary_quadratic.synthetic", "binary_quadratic"):
            raise ValueError("CSV linear-objective adapter supports synthetic binary-quadratic models only")
        data = _load_csv_binary_objective(source)
    else:
        limit = MAX_PINNED_GEOJSON_BYTES if manifest["classification"] == "RESEARCH_REFERENCE" else MAX_JSON_BYTES
        data = _parse_json(source, limit=limit)
        if suffix == ".geojson" and (
            data.get("type") != "FeatureCollection" or
            type(data.get("features")) is not list
        ):
            raise ValueError("GeoJSON requires a FeatureCollection with features")
    manifest_digest = sha256(manifest_path.read_bytes()).hexdigest()
    # Content-based scientific fingerprint: changing data contents, selected
    # formulation OR typed parameters changes it (no path identity assumptions).
    fingerprint = sha256(canonical({
        "schema_version": 1, "problem_id": manifest["problem_id"],
        "formulation_id": manifest["formulation_id"],
        "parameters": manifest["parameters"], "dataset_sha256": digest,
        "source_format": suffix, "classification": manifest["classification"],
    })).hexdigest()
    return Bundle(manifest, data, digest, manifest_digest, fingerprint, source, suffix)
