"""Numerical consistency gates for the MIQP / SCIP MILP / QUBO inspector.

Exported coefficients come from exactly one Instance; verify numerical
identity rather than just testing LaTeX text or Streamlit widget shapes.
"""
from dataclasses import replace
import hashlib
from itertools import product
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from formulation_audit import build_audit, canonical_json, configuration_key, verify_selected
from model import Instance, NOTEBOOK_WEIGHTS, evaluate, load_data, make_instance, solve_scip
from qubo import best_slack_assignment, energy as qubo_energy

DATA = Path(__file__).resolve().parents[3] / "problems/water_quality/data/LDB_centroids_clean.geojson"
DATA_SHA = hashlib.sha256(DATA.read_bytes()).hexdigest()


def small_case():
    return Instance(
        coords=np.array([[1., 2.], [3., 4.], [5., 6.], [7., 8.]]),
        free_indices=np.array([10, 11, 12]),
        fixed_indices=np.array([20]), utility=np.array([.1, .2, .3, .4]),
        linear=np.array([-1.8, -1.6, -.3]),
        quadratic=((0, 1, .4), (1, 2, .2)),
        neighbors=((1,), (0, 2), (1,)),
        fixed_neighbors=np.array([1, 0, 0]), budget=2, d_max=9000.,
    )


def test_every_small_binary_decision_matches_exported_objective_and_constraints():
    inst = small_case()
    audit, qubo = build_audit(inst, dataset_sha256=DATA_SHA, settings={"K": 2})
    assert audit["original_miqp"]["variable_count"] == 3
    assert audit["scip_solver_milp"]["auxiliary_pair_binary_count"] == 2
    assert len(audit["scip_solver_milp"]["product_variables"]) == 2
    assert audit["original_miqp"]["local_one_hop_connectivity"][0]["free_neighbor_indices"] == [1]
    assert len(audit["encoded_qubo"]["auxiliary_binary_slacks"]) == 3

    raw_copy = dict(audit)
    digest = raw_copy.pop("model_fingerprint_sha256")
    assert hashlib.sha256(canonical_json(raw_copy).encode()).hexdigest() == digest

    for x in product((0, 1), repeat=3):
        arr = np.asarray(x)
        exported = verify_selected(inst, qubo, audit, arr)
        actual = evaluate(inst, arr)
        direct_energy = sum(float(inst.linear[i]) * x[i] for i in range(3)) + (
            .4 * x[0] * x[1] + .2 * x[1] * x[2]
        )
        assert exported["original_objective"] == pytest.approx(direct_energy)
        assert exported["original_objective"] == pytest.approx(actual["energy"])
        assert exported["original_feasible"] == actual["feasible"]
        assert exported["budget_residual"] == sum(x) - 2
        assert exported["qubo_energy_with_minimized_slacks"] == pytest.approx(
            qubo_energy(qubo, best_slack_assignment(inst, qubo, list(x)))
        )
        # Exact SCIP pair-product linearization: all 3 inequalities force z=x_i*x_j.
        for term in audit["scip_solver_milp"]["product_variables"]:
            i, j = term["i"], term["j"]
            valid = [
                z for z in (0, 1)
                if z >= x[i] + x[j] - 1 and z <= x[i] and z <= x[j]
            ]
            assert valid == [x[i] * x[j]]


def test_actual_qubo_export_exactly_matches_solver_compatible_q_and_aux_bits():
    inst = small_case()
    audit, qubo = build_audit(inst, dataset_sha256=DATA_SHA, settings={"K": 2},
                             budget_penalty=3.25, connectivity_penalty=7.5)
    q = audit["encoded_qubo"]
    assert q["budget_penalty"]["value"] == 3.25
    assert q["connectivity_penalty"]["value"] == 7.5
    assert q["offset"]["value"] == qubo.offset
    assert len(q["nonzero_upper_triangular_terms"]) == len(qubo.coefficients)
    recovered = {(t["i"], t["j"]): float.fromhex(t["coefficient"]["float64_hex"])
                 for t in q["nonzero_upper_triangular_terms"]}
    assert recovered == qubo.as_index_qubo()
    assert all(i <= j < qubo.n_variables for i, j in recovered)
    assert q["binary_variable_count"] == qubo.n_variables
    assert q["original_x_indices"] == [0, 1, 2]
    assert [
        (tuple(group["bit_indices"]), tuple(group["bit_weights"]))
        for group in q["auxiliary_binary_slacks"]
    ] == list(zip(qubo.slack_variables, qubo.slack_weights))


def test_model_fingerprint_changes_for_every_scientific_input_dimension():
    inst = small_case()
    first, _ = build_audit(inst, dataset_sha256=DATA_SHA, settings={"K": 2})
    repeat, _ = build_audit(inst, dataset_sha256=DATA_SHA, settings={"K": 2})
    assert first == repeat
    changed_linear = replace(inst, linear=inst.linear.copy())
    changed_linear.linear[0] = np.nextafter(changed_linear.linear[0], np.inf)
    changed, _ = build_audit(changed_linear, dataset_sha256=DATA_SHA, settings={"K": 2})
    assert changed["model_fingerprint_sha256"] != first["model_fingerprint_sha256"]
    changed_graph = replace(inst, fixed_neighbors=np.array([0, 0, 0]))
    changed, _ = build_audit(changed_graph, dataset_sha256=DATA_SHA, settings={"K": 2})
    assert changed["model_fingerprint_sha256"] != first["model_fingerprint_sha256"]
    changed, _ = build_audit(inst, dataset_sha256=DATA_SHA, settings={"K": 2},
                             budget_penalty=3., connectivity_penalty=3.)
    assert changed["model_fingerprint_sha256"] != first["model_fingerprint_sha256"]
    changed, _ = build_audit(inst, dataset_sha256=DATA_SHA, settings={"K": 2, "beta": 1.5})
    assert changed["model_fingerprint_sha256"] != first["model_fingerprint_sha256"]
    assert configuration_key({"K": 2}, DATA_SHA) != configuration_key({"K": 3}, DATA_SHA)
    with pytest.raises(ValueError, match="SHA-256"):
        build_audit(inst, dataset_sha256="bad", settings={})


def test_real_n20_miqp_qubo_and_scip_solution_match_exported_audit():
    data = load_data(DATA)
    inst, simulated = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    assert not simulated
    audit, qubo = build_audit(
        inst, dataset_sha256=DATA_SHA,
        settings={"K": 5, "weights": NOTEBOOK_WEIGHTS.tolist()}
    )
    assert audit["source"]["dataset_sha256"] == DATA_SHA
    assert len(audit["source"]["fixed_master_feature_positions"]) == 15
    assert audit["original_miqp"]["variable_count"] == 20
    assert len(audit["original_miqp"]["quadratic_terms"]) == 12
    assert audit["scip_solver_milp"]["auxiliary_pair_binary_count"] == 12
    x, result = solve_scip(inst, time_limit=90.)
    assert result["status"] == "optimal"
    checks = verify_selected(inst, qubo, audit, x)
    assert checks["original_feasible"]
    assert checks["original_objective"] == pytest.approx(result["energy"], abs=1e-8)
    assert checks["original_objective"] == pytest.approx(-3.3012934918564643, abs=1e-8)
    assert checks["qubo_energy_with_minimized_slacks"] == pytest.approx(
        checks["original_objective"], abs=1e-7
    )
    assert checks["selected_local_indices"] == [0, 1, 3, 6, 7]
    assert checks["model_fingerprint_sha256"] == audit["model_fingerprint_sha256"]
