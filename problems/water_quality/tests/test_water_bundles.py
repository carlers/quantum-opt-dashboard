"""Research acceptance for interchangeable input files without changing math.

Cold small N20 subset enumeration is performed by water_bundle_adapter.
Unlike old manuscript claims, this asserts parity with COMMITTED notebook
data under the notebook weight vector, not the published Table IV.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "framework" / "python"))
sys.path.insert(0, str(ROOT / "problems" / "evacuation_centers"))
sys.path.insert(0, str(ROOT / "problems" / "water_quality"))

from qopt.core.experiment_bundle import load_bundle, canonical
from bundle_runner import execute

BASE = ROOT / "problems" / "water_quality"
REFERENCE = BASE / "reference-n20.bundle.json"
EXAMPLES = BASE / "examples"


def _snapshot(tmp_path: Path, *, source: str, edit=None, data_edit=None) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    config = json.loads((EXAMPLES / source).read_text())
    dataset = json.loads((EXAMPLES / config["dataset"]["path"]).read_text())
    if edit:
        edit(config)
    if data_edit:
        data_edit(dataset)
    (tmp_path / "source.geojson").write_bytes(canonical(dataset))
    config["dataset"] = {"path": "source.geojson"}
    path = tmp_path / "bundle.json"
    path.write_bytes(canonical(config))
    return path


def test_original_immutable_n20_is_actual_one_hop_scip_and_independent_optimum(tmp_path):
    bundle = load_bundle(REFERENCE)
    assert bundle.source_manifest["classification"] == "RESEARCH_REFERENCE"
    assert bundle.source_format == ".geojson"
    assert bundle.dataset_sha256 == (
        "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
    )
    audit = bundle.audit()
    assert audit["actual_dataset"]["raw_data_omitted"]
    assert audit["actual_dataset"]["feature_count"] == 5417
    result = execute(REFERENCE, tmp_path / "n20")
    study = result["result"]
    assert study["historical_source_scenario"]
    assert study["scip_status"] == "optimal"
    assert study["original_feasible"]
    assert study["one_hop_is_not_global_network_connectivity"]
    assert study["selected_local_positions"] == [0, 1, 3, 6, 7]
    assert study["selected_master_positions"] == [5253, 2394, 1557, 47, 5409]
    assert study["original_objective"] == pytest.approx(-3.3012934918564643, abs=1e-7)
    assert study["independent_enumeration"]["status"] == "optimal_by_enumeration"
    assert study["independent_enumeration"]["combinations"] == 15504
    assert study["independent_enumeration"]["optimum"] == pytest.approx(
        study["original_objective"], abs=1e-7
    )
    contents = (tmp_path / "n20" / "actual-water-scip-milp.lp").read_text()
    for name in ("x0", "x1", "budget", "connect_0", "p0_1"):
        assert name in contents
    for name in ("run.json", "manifest.json", "actual-water-scip-milp.lp"):
        assert (tmp_path / "n20" / name).exists()


def test_same_formulation_accepts_different_projected_synthetic_geojson(tmp_path):
    a = _snapshot(tmp_path / "a", source="fake-water-n5.bundle.json")
    b = _snapshot(tmp_path / "b", source="fake-water-alternate.bundle.json")
    one, two = execute(a, tmp_path / "a" / "out"), execute(b, tmp_path / "b" / "out")
    assert one["bundle_audit"]["dataset_sha256"] != two["bundle_audit"]["dataset_sha256"]
    assert one["bundle_audit"]["resolved_bundle_fingerprint_sha256"] != two[
        "bundle_audit"]["resolved_bundle_fingerprint_sha256"
    ]
    for result in (one, two):
        study = result["result"]
        assert not study["historical_source_scenario"]
        assert study["dataset_point_count"] == 81
        assert study["budget_exactly"] == 2
        # Artificial replacement data can be incompatible with the original
        # notebook's tight geometric one-hop adjacency. Report, do not relax.
        assert study["scip_status"] == "infeasible"
        assert not study["original_feasible"]
        assert study["selected_local_positions"] == []
        assert study["original_objective"] is None
        assert study["independent_enumeration"]["status"] == "infeasible"
        assert study["infeasibility_reason"]
        assert (tmp_path / ("a" if result is one else "b") / "out" /
                "actual-water-scip-milp.lp").exists()


def test_budget_and_weights_are_typed_user_parameters_not_source_code(tmp_path):
    a = _snapshot(tmp_path / "a", source="fake-water-n5.bundle.json")
    b = _snapshot(tmp_path / "b", source="fake-water-n5.bundle.json",
                  edit=lambda d: d["parameters"].update(budget=0))
    c = _snapshot(tmp_path / "c", source="fake-water-n5.bundle.json",
                  edit=lambda d: d["parameters"]["weights"].__setitem__(0, .01))
    ra = execute(a, tmp_path / "a" / "out")
    rb = execute(b, tmp_path / "b" / "out")
    rc = execute(c, tmp_path / "c" / "out")
    assert ra["result"]["budget_exactly"] == 2
    assert rb["result"]["budget_exactly"] == 0
    assert rb["result"]["scip_status"] == "optimal"
    assert rb["result"]["original_feasible"] is True
    assert len(rb["result"]["selected_local_positions"]) == 0
    assert rb["result"]["original_objective"] == pytest.approx(0)
    assert rb["result"]["independent_enumeration"]["status"] == "optimal_by_enumeration"
    assert (ra["bundle_audit"]["resolved_bundle_fingerprint_sha256"] !=
            rb["bundle_audit"]["resolved_bundle_fingerprint_sha256"] !=
            rc["bundle_audit"]["resolved_bundle_fingerprint_sha256"])
    assert ra["result"]["objective_linear_hex"] != rc["result"]["objective_linear_hex"]


@pytest.mark.parametrize("modify,reason", [
    (lambda d: d.pop("crs"), "CRS"),
    (lambda d: d["features"][4]["properties"].update(has_existing_station="yes"), "boolean"),
    (lambda d: d["features"][4]["properties"].update(id=3), "Duplicate"),
    (lambda d: d["features"][4]["geometry"].update(coordinates=[120.8, 14.5]), "lon/lat"),
    (lambda d: d["features"][4]["properties"].update(a1_river_proximity="NaN"), "finite"),
])
def test_fake_geojson_requires_sane_projected_schema(tmp_path, modify, reason):
    bundle = _snapshot(tmp_path, source="fake-water-n5.bundle.json", data_edit=modify)
    with pytest.raises(ValueError, match=reason):
        execute(bundle, tmp_path / "run")


def test_fake_geojson_wrong_formulation_and_unapproved_reference_rejected(tmp_path):
    other = _snapshot(tmp_path / "a", source="fake-water-n5.bundle.json",
                      edit=lambda d: d.update(formulation_id="global_backbone_paths"))
    with pytest.raises(ValueError, match="Unsupported"):
        execute(other, tmp_path / "a" / "out")
    claim = _snapshot(tmp_path / "b", source="fake-water-n5.bundle.json",
                      edit=lambda d: d.update(classification="RESEARCH_REFERENCE"))
    with pytest.raises(ValueError, match="allowlisted"):
        execute(claim, tmp_path / "b" / "out")
