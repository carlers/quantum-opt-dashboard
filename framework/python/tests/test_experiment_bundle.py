"""Fast framework-package safety tests; no external SCIP/Streamlit dependency.

Scientific solver acceptance remains in the separate domain/UI workflows.
"""
import json
from hashlib import sha256
from pathlib import Path

import pytest

from qopt.core.experiment_bundle import canonical, load_bundle


def _write(tmp_path: Path, *, budget: int = 1, data=None) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    model = ({"classification": "SYNTHETIC_BINARY_QUADRATIC",
              "variables": ["a", "b"],
              "objective": {"sense": "minimize", "constant": 0,
                            "linear": {"a": -2, "b": -1}, "quadratic": []},
              "constraints": [{"id": "budget", "sense": "<=", "rhs": 1,
                               "linear": {"a": 1, "b": 1}}]}
             if data is None else data)
    source = tmp_path / "synthetic.json"
    source.write_bytes(canonical(model))
    manifest = {
        "schema_version": 1, "classification": "SYNTHETIC",
        "problem_id": "binary_quadratic.synthetic",
        "formulation_id": "binary_quadratic",
        "dataset": {"path": "synthetic.json",
                    "expected_sha256": sha256(source.read_bytes()).hexdigest()},
        "parameters": {"rhs_overrides": {"budget": budget}},
    }
    config = tmp_path / "bundle.json"
    config.write_bytes(canonical(manifest))
    return config


def test_source_bytes_manifest_digest_and_resolved_experiment_are_auditable(tmp_path):
    config = _write(tmp_path)
    bundle = load_bundle(config)
    assert bundle.source_format == ".json"
    assert bundle.dataset_sha256 == sha256((tmp_path / "synthetic.json").read_bytes()).hexdigest()
    assert bundle.manifest_sha256 == sha256(config.read_bytes()).hexdigest()
    assert bundle.problem_id == "binary_quadratic.synthetic"
    assert bundle.formulation_id == "binary_quadratic"
    assert bundle.audit()["actual_dataset"]["variables"] == ["a", "b"]
    assert bundle.fingerprint == load_bundle(config).fingerprint


def test_user_changed_rhs_changes_fingerprint_without_source_change(tmp_path):
    first = load_bundle(_write(tmp_path / "a", budget=1))
    second = load_bundle(_write(tmp_path / "b", budget=0))
    assert first.dataset_sha256 == second.dataset_sha256
    assert first.fingerprint != second.fingerprint


def test_source_replacement_with_same_formulation_changes_fingerprint(tmp_path):
    first = load_bundle(_write(tmp_path / "a"))
    copied = json.loads((tmp_path / "a" / "synthetic.json").read_text())
    copied["objective"]["linear"]["a"] = -20
    second = load_bundle(_write(tmp_path / "b", data=copied))
    assert first.dataset_sha256 != second.dataset_sha256
    assert first.fingerprint != second.fingerprint


def test_forged_reference_and_unsigned_mutation_are_rejected(tmp_path):
    config = _write(tmp_path / "a")
    raw = json.loads(config.read_text())
    raw["classification"] = "RESEARCH_REFERENCE"
    config.write_bytes(canonical(raw))
    with pytest.raises(ValueError, match="allowlisted"):
        load_bundle(config)

    config = _write(tmp_path / "b")
    (tmp_path / "b" / "synthetic.json").write_text("{}")
    with pytest.raises(ValueError, match="sha256 mismatch"):
        load_bundle(config)


def test_path_escape_and_symlink_denied(tmp_path):
    config = _write(tmp_path / "a")
    raw = json.loads(config.read_text())
    raw["dataset"] = {"path": "../outside.json"}
    config.write_bytes(canonical(raw))
    with pytest.raises(ValueError, match="traversal"):
        load_bundle(config)

    config = _write(tmp_path / "b")
    (tmp_path / "b" / "synthetic.json").unlink()
    outside = tmp_path / "elsewhere.json"
    outside.write_text("{}")
    (tmp_path / "b" / "synthetic.json").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        load_bundle(config)
