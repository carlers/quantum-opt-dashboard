"""Proof that replacing DATA / FORMULATION / PARAMETERS needs no code edits.

Deliberately uses only artificial facilities and arbitrary binary variables.
Each run exports exactly the solver's original LP and input SHA-256 hashes.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "framework" / "python"))

from qopt.core.experiment_bundle import canonical, load_bundle
from qopt.core.binary_quadratic import validate_binary_problem, original_energy
from bundle_runner import execute


EXAMPLES = HERE / "examples"


def make_bundle(tmp_path, base_name, *, update=None, data_edit=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    config = json.loads((EXAMPLES / base_name).read_text())
    data_name = config["dataset"]["path"]
    contents = json.loads((EXAMPLES / data_name).read_text())
    if update:
        update(config)
    if data_edit:
        data_edit(contents)
    data_path = tmp_path / "scenario.json"
    data_path.write_bytes(canonical(contents))
    config["dataset"]["path"] = data_path.name
    manifest = tmp_path / "bundle.json"
    manifest.write_bytes(canonical(config))
    return manifest


def test_same_dataset_switches_formulations_without_code_changes(tmp_path):
    base = make_bundle(tmp_path / "a", "evac-capacitated.json")
    covering = make_bundle(tmp_path / "b", "evac-covering.json")
    service = execute(base, tmp_path / "a" / "out")
    potential = execute(covering, tmp_path / "b" / "out")
    assert service["bundle_audit"]["dataset_sha256"] == potential["bundle_audit"]["dataset_sha256"]
    assert service["bundle_audit"]["resolved_bundle_fingerprint_sha256"] != potential[
        "bundle_audit"]["resolved_bundle_fingerprint_sha256"]
    assert service["result"]["result"]["capacitated_scip"]["served_persons"] == pytest.approx(5, abs=1e-6)
    assert service["result"]["result"]["capacitated_scip"]["unserved_persons"] == pytest.approx(2, abs=1e-6)
    assert potential["result"]["result"]["potentially_reachable_persons_NOT_served"] == 7
    assert "actual-scip-covering.lp" in {p.name for p in (tmp_path / "b" / "out").iterdir()}
    assert "actual-scip-travel.lp" in {p.name for p in (tmp_path / "a" / "out").iterdir()}


def test_swapping_datasets_and_budget_changes_outputs_and_fingerprints(tmp_path):
    base = make_bundle(tmp_path / "a", "evac-capacitated.json")
    replacement = make_bundle(tmp_path / "b", "evac-alternate-data.json")
    a = execute(base, tmp_path / "a" / "out")
    b = execute(replacement, tmp_path / "b" / "out")
    assert a["bundle_audit"]["dataset_sha256"] != b["bundle_audit"]["dataset_sha256"]
    assert b["result"]["result"]["capacitated_scip"]["unserved_persons"] == pytest.approx(0, abs=1e-6)
    assert b["result"]["result"]["capacitated_scip"]["total_travel_person_minutes"] == pytest.approx(9, abs=1e-6)

    two = make_bundle(tmp_path / "c", "evac-capacitated.json",
                      update=lambda m: m["parameters"].update(max_open=2))
    c = execute(two, tmp_path / "c" / "out")
    assert c["result"]["result"]["capacitated_scip"]["unserved_persons"] == pytest.approx(0, abs=1e-6)
    assert a["bundle_audit"]["resolved_bundle_fingerprint_sha256"] != c["bundle_audit"][
        "resolved_bundle_fingerprint_sha256"]


def test_generic_binary_quadratic_is_not_evacuations_hardcoded(tmp_path):
    original = make_bundle(tmp_path / "a", "generic-binary-quadratic.json")
    out = execute(original, tmp_path / "a" / "out")
    value = out["result"]["scip"]
    assert value["status"] == "optimal"
    assert value["objective"] == pytest.approx(-4)
    assert value["selected_variables"] == ["alpha"]
    assert out["result"]["independent_enumeration"]["objective"] == pytest.approx(-4)
    assert out["result"]["independent_enumeration"]["num_assignments_checked"] == 8
    assert out["result"]["qubo_status"].startswith("NOT_COMPILED")
    lp = (tmp_path / "a" / "out" / "actual-scip-binary-milp.lp").read_text()
    for name in ("x_alpha", "x_beta", "pair_alpha_beta", "budget"):
        assert name in lp

    no_open = make_bundle(tmp_path / "b", "generic-binary-quadratic.json",
                          update=lambda m: m["parameters"].update(rhs_overrides={"budget":0}))
    b = execute(no_open, tmp_path / "b" / "out")
    assert b["result"]["scip"]["objective"] == pytest.approx(0)
    assert b["result"]["scip"]["selected_variables"] == []
    assert out["bundle_audit"]["resolved_bundle_fingerprint_sha256"] != b["bundle_audit"][
        "resolved_bundle_fingerprint_sha256"]


def test_user_defined_coefficient_change_changes_generic_optimum(tmp_path):
    original = make_bundle(tmp_path / "a", "generic-binary-quadratic.json")
    adjusted = make_bundle(tmp_path / "b", "generic-binary-quadratic.json",
                           data_edit=lambda d: d["objective"]["linear"].update(beta=-8))
    a = execute(original, tmp_path / "a" / "out")
    b = execute(adjusted, tmp_path / "b" / "out")
    assert a["result"]["scip"]["selected_variables"] == ["alpha"]
    assert b["result"]["scip"]["selected_variables"] == ["beta"]
    assert b["result"]["scip"]["objective"] == pytest.approx(-8)
    assert a["bundle_audit"]["resolved_bundle_fingerprint_sha256"] != b["bundle_audit"][
        "resolved_bundle_fingerprint_sha256"]


def test_exact_qubo_only_for_unconstrained_binary_objective(tmp_path):
    empty = make_bundle(tmp_path / "u", "generic-binary-quadratic.json",
                        data_edit=lambda d: d.update(constraints=[]),
                        update=lambda m: m["parameters"].update(rhs_overrides={}))
    out = execute(empty, tmp_path / "u" / "out")
    q = out["result"]["exact_unconstrained_qubo"]
    assert q["diagonal"]["alpha"] == -4.
    assert q["off_diagonal"][0]["coefficient"] == 2.
    assert q["offset"] == 0.
    assert out["result"]["scip"]["objective"] == pytest.approx(-6)
    assert "linear constraints require" not in out["result"]


def test_archive_records_exact_inputs_scientific_digests_and_actual_lp(tmp_path):
    manifest = make_bundle(tmp_path / "a", "generic-binary-quadratic.json")
    first = execute(manifest, tmp_path / "a" / "out")
    again = execute(manifest, tmp_path / "a" / "other")
    assert first["bundle_audit"]["resolved_bundle_fingerprint_sha256"] == again[
        "bundle_audit"]["resolved_bundle_fingerprint_sha256"]
    for dest in (tmp_path / "a" / "out", tmp_path / "a" / "other"):
        filehash = json.loads((dest / "manifest.json").read_text())["files_sha256"]
        assert "run.json" in filehash
        assert "actual-scip-binary-milp.lp" in filehash
        for filename, digest in filehash.items():
            assert digest == sha256((dest / filename).read_bytes()).hexdigest()
    assert first["bundle_audit"]["source_manifest"]["formulation_id"] == "binary_quadratic"


@pytest.mark.parametrize("mutator,error", [
    (lambda m: m.update(formulation_id="not_a_registered_formula"), "Unsupported"),
    (lambda m: m.update(problem_id="untrusted.python"), "Unknown problem"),
    (lambda m: m["parameters"].update(unknown=123), "Unsupported"),
    (lambda m: m.update(classification="OFFICIAL"), "Only SYNTHETIC"),
    (lambda m: m.update(schema_version=2), "schema"),
    (lambda m: m.update(irrelevant="ignored"), "missing or unknown"),
    (lambda m: m["dataset"].update(expected_sha256="0"*64), "sha256"),
    (lambda m: m["dataset"].update(path="../secrets.json"), "traversal"),
    (lambda m: m["dataset"].update(path="/tmp/elsewhere.json"), "traversal"),
])
def test_strict_manifest_preflight_fails_closed(tmp_path, mutator, error):
    manifest = make_bundle(tmp_path, "evac-capacitated.json", update=mutator)
    with pytest.raises(ValueError, match=error):
        execute(manifest, tmp_path / "out")


@pytest.mark.parametrize("mutator,error", [
    (lambda d: d["demands"].__setitem__(0, None), "Unknown"),
    (lambda d: d["eligible"].__setitem__(0, None), "Eligibility"),
    (lambda d: d["travel_minutes"].__setitem__(0, [-2, 9]), "Travel"),
    (lambda d: d.update(classification="REAL DATA"), "synthetic"),
])
def test_data_preflight_never_coerces_missing_real_world_fields(tmp_path, mutator, error):
    manifest = make_bundle(tmp_path, "evac-capacitated.json", data_edit=mutator)
    with pytest.raises(ValueError, match=error):
        execute(manifest, tmp_path / "out")


@pytest.mark.parametrize("edit,error", [
    (lambda d: d["objective"]["quadratic"].append(
        {"first":"alpha", "second":"beta", "coefficient":3}), "Duplicate"),
    (lambda d: d["objective"]["linear"].update(unknown=1), "unexpected"),
    (lambda d: d["constraints"].append({"id":"budget","sense":"==","rhs":1,
                                       "linear":{"beta":1}}), "duplicate"),
    (lambda d: d["objective"].update(sense="arbitrary_code()"), "minimize"),
])
def test_generic_math_preflight_rejects_invalid_formulas(tmp_path, edit, error):
    manifest = make_bundle(tmp_path, "generic-binary-quadratic.json", data_edit=edit)
    with pytest.raises(ValueError, match=error):
        execute(manifest, tmp_path / "out")


def test_symlink_and_nonfinite_json_rejected_at_trust_boundary(tmp_path):
    folder = tmp_path / "nested"
    folder.mkdir()
    outside = tmp_path / "elsewhere.json"
    outside.write_text("{}")
    (folder / "escape.json").symlink_to(outside)
    manifest = folder / "bundle.json"
    config = json.loads((EXAMPLES / "evac-capacitated.json").read_text())
    config["dataset"] = {"path":"escape.json"}
    manifest.write_bytes(canonical(config))
    with pytest.raises(ValueError, match="symlink"):
        load_bundle(manifest)

    (folder / "escape.json").unlink()
    (folder / "escape.json").write_text('{"bad": NaN}')
    with pytest.raises(ValueError, match="Nonfinite"):
        load_bundle(manifest)
