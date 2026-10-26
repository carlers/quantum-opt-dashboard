"""Adversarial detached verifier tests using real original SCIP LP and child.

No signer is simulated: caller-provided expected challenge/source are inputs
OUTSIDE the evidence envelope, and the output remains explicitly unsigned.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from detached_n20_verifier import canonical, digest, verify, _read_json
from model import NOTEBOOK_WEIGHTS, load_data, make_instance, solve_scip
from mvp_audit import source_sha
from scip_lp_reexecution import reexecute_emitted_lp_in_child

DATA = Path(__file__).resolve().parents[3] / "problems/water_quality/data/LDB_centroids_clean.geojson"
NONCE = "a" * 48


def envelope_for(instance, lp, first, metrics, report, dataset_digest):
    source = {
        "dataset_sha256": dataset_digest,
        "criterion_semantics": "historical_8_factor_original_D2_road_proximity_not_WorldPop",
        "n_free": 20,
        "n_fixed": 15,
        "budget": int(instance.budget),
        "free_master_feature_positions": [int(i) for i in instance.free_indices],
        "fixed_master_feature_positions": [int(i) for i in instance.fixed_indices],
        "linear_float64_hex": [float(x).hex() for x in instance.linear],
        "quadratic_terms": [
            {"i": int(i), "j": int(j), "q_float64_hex": float(q).hex()}
            for i, j, q in instance.quadratic
        ],
        "fixed_neighbor_flags": [int(i) for i in instance.fixed_neighbors],
        "free_neighbors": [list(map(int, ns)) for ns in instance.neighbors],
    }
    upstream = {
        "status": metrics["status"],
        "optimal": metrics["optimal"],
        "gap": float(metrics["gap"]),
        "feasible": metrics["feasible"],
        "budget_ok": metrics["budget_ok"],
        "connectivity_ok": metrics["connectivity_ok"],
        "isolated": metrics["isolated"],
        "num_selected": int(metrics["num_selected"]),
        "energy": float(metrics["energy"]),
        "binary20": [int(v) for v in first],
    }
    return {
        "schema_version": 1,
        "scope": "N20_original_source_local_unsigned_process_review",
        "challenge_nonce": NONCE,
        "source": source,
        "source_sha256": digest(source),
        "lp_sha256": sha256(lp).hexdigest(),
        "upstream": upstream,
        "child": deepcopy(report["observed_child_receipt"]),
    }


@pytest.fixture(scope="module")
def real_evidence():
    data = load_data(DATA)
    instance, fallback = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    assert not fallback
    with TemporaryDirectory() as temp:
        lp_file = Path(temp) / "original.lP".replace(".lP",".lp")
        first, metrics = solve_scip(instance, time_limit=30, export_lp_path=lp_file)
        lp = lp_file.read_bytes()
        report = reexecute_emitted_lp_in_child(instance, lp, first, metrics)
    envelope = envelope_for(instance, lp, first, metrics, report, source_sha(DATA))
    return instance, lp, envelope


def checked(envelope, lp, *, nonce=NONCE, source_digest=None, dataset_digest=None):
    return verify(envelope, lp, expected_nonce=nonce,
                  expected_source_sha256=source_digest or envelope["source_sha256"],
                  expected_dataset_sha256=dataset_digest or envelope["source"]["dataset_sha256"])


def test_real_source_detached_exact_optimum_lp_and_unsigned_verdict(real_evidence):
    inst, lp, env = real_evidence
    record = checked(env, lp)
    assert record["feasible_n20_k5_count"] == 1077
    assert record["exact_optimum_witness"] == [0, 1, 3, 6, 7]
    assert record["first_selected"] == record["second_selected"] == [0, 1, 3, 6, 7]
    assert record["structural_lp_constraint_count"] == 21 + 3 * len(inst.quadratic)
    assert record["challenge_nonce"] == NONCE
    assert record["independently_expected_source_sha256"] == digest(env["source"])
    assert record["signed_by_separately_governed_key"] is False
    assert record["nonce_replay_consumption_enforced_by_service"] is False
    assert record["first_solver_process_externally_authenticated"] is False


@pytest.mark.parametrize("alteration", ["wrong_nonce", "wrong_reference", "wrong_dataset",
                                         "extra_field", "wrong_mode"])
def test_no_fake_challenge_source_reference_or_mode(real_evidence, alteration):
    inst, lp, env = real_evidence
    f = deepcopy(env)
    kwargs = {"nonce": NONCE, "source_digest": env["source_sha256"],
              "dataset_digest": env["source"]["dataset_sha256"]}
    if alteration == "wrong_nonce":
        f["challenge_nonce"] = "b" * 48
    elif alteration == "wrong_reference":
        kwargs["source_digest"] = "0" * 64
    elif alteration == "wrong_dataset":
        kwargs["dataset_digest"] = "1" * 64
    elif alteration == "extra_field":
        f["trusted_signature"] = True
    elif alteration == "wrong_mode":
        f["scope"] = "N20_all_fixed_global_SCIP_optimal"
    with pytest.raises(ValueError):
        checked(f, lp, **kwargs)


@pytest.mark.parametrize("field,bad", [
    ("status", "timelimit"), ("optimal", False), ("gap", .4),
    ("feasible", False), ("budget_ok", False), ("connectivity_ok", False),
    ("isolated", [3]), ("num_selected", 4),
    ("energy", -7.0),
])
def test_forged_first_solver_status_and_claims_rejected(real_evidence, field, bad):
    inst, lp, env = real_evidence
    f = deepcopy(env)
    f["upstream"][field] = bad
    with pytest.raises(ValueError):
        checked(f, lp)


@pytest.mark.parametrize("field,bad", [
    ("status", "infeasible"), ("input_lp_sha256", "a" * 64),
    ("reported_relative_gap", 0.5), ("dual_bound_lp_decimal", 123.0),
    ("original_upstream_scip_execution_authenticated", True),
    ("published_manuscript_or_physical_lake_quality_validated", True),
    ("best_solution_count", 0),
])
def test_forged_second_solver_and_trust_escalation_rejected(real_evidence, field, bad):
    inst, lp, env = real_evidence
    f = deepcopy(env)
    f["child"][field] = bad
    with pytest.raises(ValueError):
        checked(f, lp)


def test_first_and_second_disconnected_selection_rejected_on_real_source_graph(real_evidence):
    inst, lp, env = real_evidence
    bad = next(subset for subset in combinations(range(20), 5)
               if any(
                   not inst.fixed_neighbors[i]
                   and not any(j in subset for j in inst.neighbors[i])
                   for i in subset
               ))
    f = deepcopy(env)
    f["upstream"]["binary20"] = [int(i in bad) for i in range(20)]
    with pytest.raises(ValueError, match="first SCIP selection"):
        checked(f, lp)
    f = deepcopy(env)
    f["child"]["original_binary20"] = [int(i in bad) for i in range(20)]
    with pytest.raises(ValueError, match="second SCIP selection"):
        checked(f, lp)


def test_source_and_lp_byte_tampering_rejected_even_when_submitted_SHA_updated(real_evidence):
    inst, lp, env = real_evidence
    f = deepcopy(env)
    f["source"]["fixed_neighbor_flags"][0] ^= 1
    f["source_sha256"] = digest(f["source"])
    with pytest.raises(ValueError, match="reference commitment"):
        checked(f, lp, source_digest=env["source_sha256"])
    altered_lp = lp.replace(b" = +5\n", b" = +4\n", 1)
    assert altered_lp != lp
    f = deepcopy(env)
    f["lp_sha256"] = sha256(altered_lp).hexdigest()
    with pytest.raises(ValueError, match="constraint budget"):
        checked(f, altered_lp)


def test_semantics_invalid_even_if_reviewer_is_tricked_into_accepting_new_manifest(real_evidence):
    inst, lp, env = real_evidence
    f = deepcopy(env)
    f["source"]["criterion_semantics"] = "paper_population_WorldPop_not_reconciled"
    f["source_sha256"] = digest(f["source"])
    with pytest.raises(ValueError, match="criterion source"):
        checked(f, lp, source_digest=f["source_sha256"])


def test_separate_expected_nonce_not_automatically_consumed(real_evidence):
    inst, lp, env = real_evidence
    first = checked(env, lp)
    second = checked(env, lp)
    # Deliberately NOT calling this a one-time-use service or a signed result.
    assert first == second
    assert first["nonce_replay_consumption_enforced_by_service"] is False


def test_forged_whole_source_reference_can_still_succeed_if_reviewer_also_colludes(real_evidence):
    # This is a DOCUMENTED LIMIT: this module cannot anchor a modified model
    # against an owner reference if that *outside* reference is also replaced.
    inst, lp, env = real_evidence
    f = deepcopy(env)
    f["source"]["dataset_sha256"] = "9" * 64
    f["source_sha256"] = digest(f["source"])
    result = checked(f, lp, source_digest=f["source_sha256"],
                     dataset_digest="9" * 64)
    assert result["first_solver_process_externally_authenticated"] is False
    assert result["signed_by_separately_governed_key"] is False


def test_duplicate_JSON_keys_rejected_before_trust_check(tmp_path):
    input_path = tmp_path / "dup.json"
    input_path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match="duplicate JSON keys"):
        _read_json(input_path)


def test_nonfinite_JSON_constant_rejected_before_trust_check(tmp_path):
    input_path = tmp_path / "nan.json"
    input_path.write_text('{"gap":NaN}')
    with pytest.raises(ValueError, match="invalid JSON constant"):
        _read_json(input_path)


def test_synthetic_flat_objective_allows_other_feasible_exact_tied_first_result(real_evidence):
    inst, _, _ = real_evidence
    zero = replace(inst, linear=np.zeros(20, dtype=float), quadratic=tuple())
    with TemporaryDirectory() as temp:
        lpfile = Path(temp) / "flat.lp"
        first, metrics = solve_scip(zero, time_limit=30, export_lp_path=lpfile)
        raw_lp = lpfile.read_bytes()
        report = reexecute_emitted_lp_in_child(zero, raw_lp, first, metrics)
    env = envelope_for(zero, raw_lp, first, metrics, report,
                       source_sha(DATA))
    witness = [i for i, v in enumerate(first) if v]
    alternative = next(subset for subset in combinations(range(20), 5)
                       if list(subset) != witness and all(
                           zero.fixed_neighbors[i] or any(
                               j in subset for j in zero.neighbors[i]
                           ) for i in subset
                       ))
    env["upstream"]["binary20"] = [int(i in alternative) for i in range(20)]
    # Synthetic perturbation of recorded first sites, NOT the original source
    # geometry; true exact 0-score ties can both be feasible/optimal.
    result = checked(env, raw_lp)
    assert result["first_selected"] == list(alternative)
    assert result["exact_binary64_optimum_numerator"] == "0"
