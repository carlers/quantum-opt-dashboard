"""User CSV input is a bounded transformed typed model, not executable text."""
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "framework" / "python"))
sys.path.insert(0, str(ROOT / "problems" / "evacuation_centers"))

from qopt.core.experiment_bundle import canonical, load_bundle
from bundle_runner import execute

EXAMPLE = ROOT / "problems/evacuation_centers/examples/generic-csv-linear-bundle.json"
SOURCE = ROOT / "problems/evacuation_centers/examples/fake-binary-scores.csv"


def _scenario(tmp_path, text=None, config_edit=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    config = json.loads(EXAMPLE.read_text())
    (tmp_path / "scores.csv").write_text(
        SOURCE.read_text() if text is None else text, encoding="utf-8"
    )
    config["dataset"] = {"path": "scores.csv"}
    if config_edit:
        config_edit(config)
    bundle = tmp_path / "config.json"
    bundle.write_bytes(canonical(config))
    return bundle


def test_csv_is_replaceable_executed_linear_binary_optimization(tmp_path):
    a = _scenario(tmp_path / "a")
    b = _scenario(tmp_path / "b", text=(
        "variable,linear_coefficient\nalpha,-2\nbeta,-9\ngamma,-1\n"
    ))
    sa = execute(a, tmp_path / "a" / "out")
    sb = execute(b, tmp_path / "b" / "out")
    assert sa["result"]["scip"]["objective"] == pytest.approx(-4)
    assert sa["result"]["scip"]["selected_variables"] == ["alpha"]
    assert sb["result"]["scip"]["objective"] == pytest.approx(-9)
    assert sb["result"]["scip"]["selected_variables"] == ["beta"]
    assert sa["bundle_audit"]["source_format"] == ".csv"
    assert sa["bundle_audit"]["resolved_bundle_fingerprint_sha256"] != sb[
        "bundle_audit"]["resolved_bundle_fingerprint_sha256"
    ]
    assert "x_beta" in (tmp_path / "b" / "out" / "actual-scip-binary-milp.lp").read_text()


@pytest.mark.parametrize("text,error", [
    ("variable,linear_coefficient\na,NaN\n", "nonfinite"),
    ("variable,linear_coefficient\na,-2\na,-4\n", "Duplicate"),
    ("variable,linear_coefficient\n=cmd,-3\n", "Invalid"),
    ("var,linear_coefficient\na,-1\n", "header"),
    ("variable,linear_coefficient\na,-1,malformed\n", "extra"),
    ("variable,linear_coefficient\na,-1\nb,\n", "Invalid"),
])
def test_csv_format_never_executes_formula_or_silently_loses_columns(tmp_path, text, error):
    bundle = _scenario(tmp_path, text=text)
    with pytest.raises(ValueError, match=error):
        load_bundle(bundle)


def test_csv_is_not_generic_replacement_for_unverified_shelter_data(tmp_path):
    b = _scenario(tmp_path, config_edit=lambda m: m.update(
        problem_id="evacuation.synthetic", formulation_id="capacitated_lexicographic"
    ))
    with pytest.raises(ValueError, match="supports synthetic binary"):
        load_bundle(b)
    c = _scenario(tmp_path / "real", config_edit=lambda m: m.update(
        classification="RESEARCH_REFERENCE"
    ))
    with pytest.raises(ValueError, match="allowlisted"):
        load_bundle(c)
