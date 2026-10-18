"""File-upload backend boundary tests without relying on unsupported AppTest upload injection.

Streamlit's uploader hands its getvalue() bytes to _prepare; these checks
exercise exactly that path with raw independent in-memory byte strings.
A full browser-level upload test remains a separate integration gate.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import _bundle_spec, _prepare, _model_text


def test_raw_csv_upload_bytes_are_preserved_with_correct_source_suffix(tmp_path):
    manifest, _, suffix = _bundle_spec("Generic binary scores — synthetic CSV")
    raw = b"variable,linear_coefficient\nalpha,-2\nbeta,-13\ngamma,-1\n"
    b = _prepare(manifest, raw, tmp_path, suffix)
    assert b.source_format == ".csv"
    assert b.dataset_path.read_bytes() == raw
    assert b.dataset_sha256 == sha256(raw).hexdigest()
    assert b.data["objective"]["linear"]["beta"] == -13
    assert "-13*beta" in _model_text(b)
    assert json.loads((tmp_path / "bundle.json").read_text())["dataset"]["path"] == "source.csv"


def test_raw_projected_geojson_upload_keeps_original_bytes_and_numeric_formula(tmp_path):
    manifest, raw_text, suffix = _bundle_spec("Water quality — synthetic GeoJSON")
    raw = raw_text.encode("utf-8")
    b = _prepare(manifest, raw, tmp_path, suffix)
    assert b.source_format == ".geojson"
    assert b.dataset_path.read_bytes() == raw
    assert b.dataset_sha256 == sha256(raw).hexdigest()
    equation = _model_text(b)
    assert "local one-hop" in equation
    assert "a_i linear coefficients:" in equation
    assert "q_ij upper quadratic terms:" in equation
    assert "one-hop is NOT global" in equation


def test_untrusted_or_unbounded_uploads_are_rejected_before_execution(tmp_path):
    manifest, _, suffix = _bundle_spec("Generic binary scores — synthetic CSV")
    with pytest.raises(ValueError, match="1 MB"):
        _prepare(manifest, b"x" * 1_000_001, tmp_path, suffix)
    assert not (tmp_path / "source.csv").exists()
    with pytest.raises(ValueError, match="synthetic data only"):
        _prepare({**manifest, "classification": "RESEARCH_REFERENCE"}, b"x", tmp_path, suffix)
    with pytest.raises(ValueError, match="Unsupported dataset extension"):
        _prepare(manifest, b"hello", tmp_path, ".py")
    with pytest.raises(ValueError, match="CSV linear-objective adapter"):
        _prepare(
            {**manifest, "problem_id": "evacuation.synthetic",
             "formulation_id": "capacitated_lexicographic"},
            b"variable,linear_coefficient\nalpha,-1\n", tmp_path, suffix,
        )
