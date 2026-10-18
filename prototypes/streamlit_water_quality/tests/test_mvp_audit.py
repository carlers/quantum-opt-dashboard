"""Focused MVP proof: immutable source, original math and exact audit bundle."""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import Instance, NOTEBOOK_WEIGHTS, load_data, make_instance, solve_scip
from mvp_audit import (
    EXPECTED_GEOJSON_SHA256, NOTEBOOK_N20_K5_OPTIMUM,
    check_selected, evidence_zip, preview, selected_csv, source_sha,
)

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"


def toy(k=2):
    return Instance(
        coords=np.array([[510000., 1520000.], [520000., 1520000.], [515000., 1530000.]]),
        free_indices=np.array([0, 1]), fixed_indices=np.array([2]),
        utility=np.ones(3), linear=np.array([-2., -1.]),
        quadratic=((0, 1, 0.2),), neighbors=((1,), (0,)),
        fixed_neighbors=np.array([1, 0]), budget=k, d_max=2000.,
    )


def basic_preview(instance):
    return preview(
        instance, dataset_sha256=EXPECTED_GEOJSON_SHA256,
        weights=NOTEBOOK_WEIGHTS.tolist(), weight_source="Notebook weights · reference",
        time_limit_seconds=30,
    )


def test_preview_is_directly_derived_from_original_instance_without_solver():
    inst = toy()
    report = basic_preview(inst)
    assert report["objective"]["linear_float64_hex"] == ["-0x1.0000000000000p+1", "-0x1.0000000000000p+0"]
    assert report["objective"]["quadratic_terms"][0]["q_float64_hex"] == float(.2).hex()
    assert report["constraints"]["budget_rhs"] == 2
    assert report["constraints"]["global_path_connectivity"] is False
    assert report["mapping"]["free_master_feature_positions"] == [0, 1]
    assert len(report["model_fingerprint_sha256"]) == 64
    assert basic_preview(inst)["model_fingerprint_sha256"] == report["model_fingerprint_sha256"]
    assert basic_preview(toy(k=1))["model_fingerprint_sha256"] != report["model_fingerprint_sha256"]


def test_independent_original_energy_and_constraints_plus_rejection_of_bad_states():
    inst = toy()
    model = basic_preview(inst)
    solution = np.array([1, 1])
    solver = {"energy": -2.8, "status": "optimal", "optimal": True, "gap": 0.}
    checked = check_selected(inst, solution, solver, model)
    assert checked["independent_original_objective"] == pytest.approx(-2.8)
    assert checked["original_feasible"]
    assert checked["selected_master_feature_positions"] == [0, 1]
    assert not checked["violated_local_one_hop_sites"]
    with pytest.raises(AssertionError, match="objective"):
        check_selected(inst, solution, {**solver, "energy": -999}, model)
    with pytest.raises(AssertionError, match="violating"):
        check_selected(inst, np.array([0, 1]), solver, model)
    with pytest.raises(ValueError, match="binary"):
        check_selected(inst, np.array([1, 2]), solver, model)


def test_evidence_archive_contains_genuine_model_and_all_source_checksums():
    inst = toy()
    model = basic_preview(inst)
    solver = {"energy": -2.8, "status": "optimal", "optimal": True, "gap": 0.}
    x = np.array([1, 1])
    witness = check_selected(inst, x, solver, model)
    csv_bytes = selected_csv(inst, x)
    assert csv_bytes.decode().splitlines()[0].startswith("local_position,")
    artifact = evidence_zip(model, witness, solver, csv_bytes, b"Minimize\n objective: x0\nEnd\n")
    with ZipFile(BytesIO(artifact)) as zipped:
        assert {"model.json", "result.json", "selected_sites.csv",
                "actual_scip_model.lp", "SHA256SUMS.json"} == set(zipped.namelist())
        manifest = json.loads(zipped.read("SHA256SUMS.json"))
        for name, digest in manifest["files_sha256"].items():
            assert sha256(zipped.read(name)).hexdigest() == digest
        assert json.loads(zipped.read("model.json"))["model_fingerprint_sha256"] == (
            witness["model_fingerprint_sha256"]
        )
        versions = json.loads(zipped.read("result.json"))["software_versions"]
        assert versions["python"] and versions["numpy"] and versions["scipy"]
        assert versions["pyscipopt"] and versions["streamlit"]
        assert "not reproduced" not in zipped.read("result.json").decode()
    with pytest.raises(ValueError, match="empty SCIP"):
        evidence_zip(model, witness, solver, csv_bytes, b"")


def test_original_geojson_source_is_sha_pinned(tmp_path):
    assert source_sha(DATA) == EXPECTED_GEOJSON_SHA256
    forged = tmp_path / "made_up.geojson"
    forged.write_bytes(b"{}")
    with pytest.raises(ValueError, match="source identity"):
        source_sha(forged)


def test_verified_real_n20_scip_exact_model_and_known_original_optimum(tmp_path):
    assert source_sha(DATA) == EXPECTED_GEOJSON_SHA256
    data = load_data(DATA)
    assert len(data.ids) == 5417
    assert np.count_nonzero(data.existing) == 15
    instance, simulated = make_instance(
        data, NOTEBOOK_WEIGHTS, 20, 5, beta=1., delta=1.
    )
    assert simulated is False
    assert len(instance.free_indices) == 20
    model = basic_preview(instance)
    lp = tmp_path / "original-scip.lp"
    x, solver = solve_scip(instance, time_limit=120., export_lp_path=lp)
    assert solver["status"] == "optimal"
    assert solver["optimal"]
    checked = check_selected(instance, x, solver, model)
    assert checked["original_feasible"]
    assert checked["selected_local_positions"] == [0, 1, 3, 6, 7]
    assert checked["selected_master_feature_positions"] == [5253, 2394, 1557, 47, 5409]
    assert checked["independent_original_objective"] == pytest.approx(
        NOTEBOOK_N20_K5_OPTIMUM, abs=1e-7
    )
    lp_text = lp.read_text()
    assert "budget" in lp_text and "connect_0" in lp_text and "x0" in lp_text
    assert lp.stat().st_size > 200
