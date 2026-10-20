"""UX current-run trusted BACKEND mathematical gate, adversarial controls.

These are actual pinned original N20 instance/real SCIP and 35-site graph
tests, not mocks of the optimizer or a fake scientific-certificate toggle.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED
import math

import numpy as np
import pytest

from model import NOTEBOOK_WEIGHTS, load_data, make_instance, solve_scip
from mvp_audit import (
    preview, source_sha, canonical, check_selected, evidence_zip, selected_csv,
)
from wireless_topology import (
    GLOBAL_MODE, LOCAL_MODE, graph_from_source, exact_global_search,
    global_evidence_zip,
)
from runtime_attestation import (
    _local_connected, attest_current_result, check_visible_result,
    exact_bounded_oracle, model_identity,
)

DATA = Path(__file__).resolve().parents[3] / "problems/water_quality/data/LDB_centroids_clean.geojson"


@pytest.fixture(scope="module")
def real_source():
    data = load_data(DATA)
    data_sha = source_sha(DATA)
    instance, fallback = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    assert not fallback and len(instance.fixed_indices) == 15
    return data, data_sha, instance


def compiled(instance, data_sha, graph=None):
    base = preview(
        instance, dataset_sha256=data_sha, weights=NOTEBOOK_WEIGHTS.tolist(),
        weight_source="Notebook weights · reference", time_limit_seconds=30,
    )
    base["settings"]["connectivity_mode"] = (
        GLOBAL_MODE if graph is not None else LOCAL_MODE
    )
    if graph is not None:
        base["problem"] = "notebook_derived_water_quality_global_network_counterfactual"
        base["constraints"]["global_path_connectivity"] = (
            "all 15 existing and all K selected new stations in one component"
        )
        base["solver_representation"] = "bounded exact enumeration of 20 choose K, not SCIP"
        base["wireless_graph"] = graph.as_record()
    base.pop("model_fingerprint_sha256")
    base["model_fingerprint_sha256"] = sha256(canonical(base)).hexdigest()
    return base


@pytest.fixture(scope="module")
def local_run(real_source):
    _, sha, instance = real_source
    model = compiled(instance, sha)
    with TemporaryDirectory() as tmp:
        lp = Path(tmp) / "actual_scip_model.lp"
        bits, metrics = solve_scip(instance, time_limit=30., export_lp_path=lp)
        csv = selected_csv(instance, bits)
        raw_lp = lp.read_bytes()
        archive = evidence_zip(model, check_selected(instance, bits, metrics, model),
                               metrics, csv, raw_lp)
    proof = attest_current_result(instance, model, None, bits, metrics, archive, csv, raw_lp)
    return instance, model, bits, metrics, archive, csv, raw_lp, proof


@pytest.fixture(scope="module")
def global_run(real_source):
    data, sha, instance = real_source
    graph = graph_from_source(data, instance, dataset_sha256=sha)
    model = compiled(instance, sha, graph)
    bits, metrics = exact_global_search(instance, graph, timeout_seconds=30)
    assert bits is not None and metrics["optimal"]
    csv = selected_csv(instance, bits)
    archive = global_evidence_zip(model, graph, metrics, csv)
    proof = attest_current_result(instance, model, graph, bits, metrics, archive, csv)
    return instance, model, graph, bits, metrics, archive, csv, proof


def stored(model, bits, metrics, archive, proof):
    return {
        "fingerprint": model["model_fingerprint_sha256"],
        "chosen": bits.tolist(), "metrics": deepcopy(metrics),
        "zip": archive, "attestation": deepcopy(proof),
    }


def test_original_real_scip_independently_proven_before_map(local_run):
    inst, model, bits, metrics, archive, csv, lp, proof = local_run
    assert proof["mathematical_verifier"]["feasible_count"] == 1077
    assert proof["mathematical_verifier"]["exact_selected_indices"] == [0, 1, 3, 6, 7]
    assert proof["source_mathematical_only_manuscript_parity"] is False
    assert proof["real_radio_water_quality_validation"] is False
    assert proof["independent_scip_execution_log_or_lp_structure_authenticated"] is False
    assert check_visible_result(inst, model, None, stored(model, bits, metrics, archive, proof))


def test_all_15_fixed_global_real_export_is_independently_proven(global_run):
    inst, model, graph, bits, metrics, archive, csv, proof = global_run
    oracle = proof["mathematical_verifier"]
    assert oracle["feasible_count"] == 860 and oracle["combination_count"] == 15504
    assert oracle["feasible_set_sha256"] == (
        "3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40"
    )
    assert oracle["exact_selected_indices"] == [0, 1, 3, 6, 7]
    assert check_visible_result(inst, model, graph, stored(model, bits, metrics, archive, proof))


def test_tampered_live_result_selected_sites_hidden(local_run):
    inst, model, bits, metrics, archive, csv, lp, proof = local_run
    state = stored(model, bits, metrics, archive, proof)
    state["chosen"][3] = 0
    assert not check_visible_result(inst, model, None, state)
    assert not check_visible_result(inst, model, None, {**stored(model,bits,metrics,archive,proof),
                                                      "attestation": {"bogus": True}})


def test_tampered_live_result_zip_or_energy_hidden(global_run):
    inst, model, graph, bits, metrics, archive, csv, proof = global_run
    state = stored(model, bits, metrics, archive, proof)
    state["zip"] = state["zip"] + b"changed"
    assert not check_visible_result(inst, model, graph, state)
    state = stored(model, bits, metrics, archive, proof)
    state["metrics"]["energy"] += 1.
    assert not check_visible_result(inst, model, graph, state)


def test_changed_current_dmax_or_weights_cannot_reuse_old_result(global_run):
    inst, model, graph, bits, metrics, archive, csv, proof = global_run
    state = stored(model, bits, metrics, archive, proof)
    bad = deepcopy(model)
    bad["d_max_m_float64_hex"] = float(inst.d_max + .01).hex()
    bad.pop("model_fingerprint_sha256")
    bad["model_fingerprint_sha256"] = sha256(canonical(bad)).hexdigest()
    assert not check_visible_result(inst, bad, graph, state)
    bad = deepcopy(model)
    bad["settings"]["eight_factor_weights"][0] = .999
    bad.pop("model_fingerprint_sha256")
    bad["model_fingerprint_sha256"] = sha256(canonical(bad)).hexdigest()
    assert not check_visible_result(inst, bad, graph, state)


def test_changed_or_missing_fixed_graph_not_allowed(global_run):
    inst, model, graph, bits, metrics, archive, csv, proof = global_run
    bad_graph = replace(graph, edges=graph.edges[1:])
    with pytest.raises(ValueError, match="graph"):
        model_identity(inst, model, bad_graph)
    with pytest.raises(ValueError, match="source-local"):
        model_identity(inst, model, None)


def test_false_solver_optimality_and_wrong_energy_not_accepted(local_run):
    inst, model, bits, metrics, archive, csv, lp, proof = local_run
    fake = deepcopy(metrics)
    fake["energy"] = metrics["energy"] - 1
    with pytest.raises(ValueError, match="energy"):
        attest_current_result(inst, model, None, bits, fake, archive, csv, lp)
    fake = deepcopy(metrics)
    fake["status"] = "timelimit"
    fake["optimal"] = True
    with pytest.raises(ValueError, match="unproved optimum"):
        attest_current_result(inst, model, None, bits, fake, archive, csv, lp)


def test_alternative_feasible_incumbent_is_not_accepted_as_optimal(local_run):
    inst, model, bits, metrics, archive, csv, lp, proof = local_run
    winner = tuple(np.flatnonzero(bits))
    other = next(ids for ids in combinations(range(20), 5)
                 if ids != winner and _local_connected(inst, ids))
    altered = np.zeros(20, dtype=int)
    altered[list(other)] = 1
    fake = deepcopy(metrics)
    fake["energy"] = float(sum(float(inst.linear[i]) for i in other)
                           + sum(float(q) for i,j,q in inst.quadratic
                                 if i in other and j in other))
    with pytest.raises(ValueError, match="unproved optimum"):
        attest_current_result(inst, model, None, altered, fake, archive, csv, lp)


def test_evidence_archive_tamper_rejected_even_if_solver_valid(global_run):
    inst, model, graph, bits, metrics, archive, csv, proof = global_run
    with ZipFile(BytesIO(archive)) as z:
        contents = {name:z.read(name) for name in z.namelist()}
    contents["selected_sites.csv"] = b"fake,local,master\n"
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as z:
        for name in sorted(contents):
            z.writestr(name, contents[name])
    with pytest.raises(ValueError, match="checksum"):
        attest_current_result(inst, model, graph, bits, metrics, out.getvalue(), csv)


def test_false_global_exhaustive_status_rejected(global_run):
    inst, model, graph, bits, metrics, archive, csv, proof = global_run
    fake = deepcopy(metrics)
    fake["combinations_examined"] = 300
    with pytest.raises(ValueError, match="exhaustively"):
        attest_current_result(inst, model, graph, bits, fake, archive, csv)


def test_source_site_and_graph_hash_stale_hidden(global_run):
    inst, model, graph, bits, metrics, archive, csv, proof = global_run
    state = stored(model, bits, metrics, archive, proof)
    state["attestation"]["active_graph_sha256"] = "0"*64
    assert not check_visible_result(inst, model, graph, state)
    state = stored(model, bits, metrics, archive, proof)
    state["fingerprint"] = "1"*64
    assert not check_visible_result(inst, model, graph, state)
