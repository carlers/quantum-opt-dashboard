"""Actual second-PROCESS PySCIPOpt solve and adversarial source-receipt controls.

Mathematical scope is original source N20 local SCIP only, no fabricated
SCIP global-network solver and no field or manuscript validity claims.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from model import NOTEBOOK_WEIGHTS, load_data, make_instance, solve_scip
from scip_lp_reexecution import (
    check_independent_process_receipt, reexecute_emitted_lp_in_child,
)
from scip_lp_structure import certify_emitted_scip_lp
from runtime_attestation import exact_bounded_oracle, exact_selection_objective

DATA = Path(__file__).resolve().parents[3] / "problems/water_quality/data/LDB_centroids_clean.geojson"


@pytest.fixture(scope="module")
def original_verified_child():
    data = load_data(DATA)
    instance, simulated = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    assert not simulated
    with TemporaryDirectory(prefix="n20_actual_first_scip_") as temp:
        lp_file = Path(temp) / "actual_local_scip.lp"
        chosen, source_metrics = solve_scip(
            instance, time_limit=30., export_lp_path=lp_file,
        )
        assert source_metrics["status"] == "optimal"
        original_lp = lp_file.read_bytes()
        report = reexecute_emitted_lp_in_child(
            instance, original_lp, chosen, source_metrics,
        )
    return instance, original_lp, chosen, source_metrics, report


def test_second_independent_process_genuinely_reads_original_lp_and_proves_bounds(original_verified_child):
    inst, lp, first, metric, report = original_verified_child
    assert report["source_original_scip_lp_sha256"] == certify_emitted_scip_lp(
        inst, lp
    )["original_scip_lp_sha256"]
    assert report["original_selected_indices"] == [0, 1, 3, 6, 7]
    assert report["independent_child_selected_indices"] == [0, 1, 3, 6, 7]
    assert report["original_upstream_status"] == "optimal"
    assert report["independent_child_status"] == "optimal"
    assert report["independent_lp_relative_gap"] <= 1e-6
    assert report["independent_lp_dual_bound"] <= report["independent_lp_primal_bound"] + 1e-7
    assert report["independent_feasible_original_local_count"] == 1077
    assert report["replay_status_source_math_crosschecked"] is True
    assert report["original_upstream_process_externally_authenticated"] is False
    assert report["session_is_cryptographically_signed"] is False
    assert report["physical_RF_DO_or_manuscript_validated"] is False


def test_forged_worker_lp_sha_rejected(original_verified_child):
    inst, lp, bits, metrics, report = original_verified_child
    receipt = deepcopy(report["observed_child_receipt"])
    receipt["input_lp_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="different emitted LP"):
        check_independent_process_receipt(inst, lp, receipt, bits, metrics)


def test_forged_upstream_or_worker_status_rejected(original_verified_child):
    inst, lp, bits, metrics, report = original_verified_child
    receipt = deepcopy(report["observed_child_receipt"])
    receipt["status"] = "timelimit"
    with pytest.raises(ValueError, match="actually optimal"):
        check_independent_process_receipt(inst, lp, receipt, bits, metrics)
    changed_upstream = deepcopy(metrics)
    changed_upstream["optimal"] = False
    with pytest.raises(ValueError, match="actually optimal"):
        check_independent_process_receipt(
            inst, lp, report["observed_child_receipt"], bits, changed_upstream
        )


def test_omitted_wrong_K_binary_and_nonoptimal_solution_rejected(original_verified_child):
    inst, lp, bits, metrics, report = original_verified_child
    receipt = deepcopy(report["observed_child_receipt"])
    for fake in ([1] * 20, [0] * 20, ["1"] + [0] * 19, [2] + [0] * 19):
        receipt["original_binary20"] = fake
        with pytest.raises(ValueError, match="binary K-budget"):
            check_independent_process_receipt(inst, lp, receipt, bits, metrics)
    receipt = deepcopy(report["observed_child_receipt"])
    receipt["original_binary20"] = [0] * 20
    for index in (0, 2, 4, 6, 8):
        receipt["original_binary20"][index] = 1
    with pytest.raises(ValueError, match="selection|graph|optimum"):
        check_independent_process_receipt(inst, lp, receipt, bits, metrics)


def test_false_zero_gap_or_reversed_dual_bound_rejected(original_verified_child):
    inst, lp, bits, metrics, report = original_verified_child
    for key, value in (
        ("reported_relative_gap", .2),
        ("dual_bound_lp_decimal", report["independent_lp_primal_bound"] + .01),
        ("primal_bound_lp_decimal", 99.9),
        ("objective_lp_decimal_approx", -999.),
    ):
        receipt = deepcopy(report["observed_child_receipt"])
        receipt[key] = value
        with pytest.raises(ValueError, match="bounds|objective"):
            check_independent_process_receipt(inst, lp, receipt, bits, metrics)


def test_forged_process_trust_upgrade_rejected(original_verified_child):
    inst, lp, bits, metrics, report = original_verified_child
    receipt = deepcopy(report["observed_child_receipt"])
    receipt["original_upstream_scip_execution_authenticated"] = True
    with pytest.raises(ValueError, match="escalated"):
        check_independent_process_receipt(inst, lp, receipt, bits, metrics)


def test_original_lp_mutated_without_updating_digest_fails_before_worker(original_verified_child):
    inst, lp, bits, metrics, report = original_verified_child
    bad = lp.replace(b" = +5\n", b" = +4\n", 1)
    assert bad != lp
    with pytest.raises(ValueError, match="constraint budget"):
        reexecute_emitted_lp_in_child(inst, bad, bits, metrics)


def test_change_original_compiled_source_neighbors_fails_before_second_solve(original_verified_child):
    inst, lp, bits, metrics, report = original_verified_child
    fixed = np.array(inst.fixed_neighbors, copy=True)
    fixed[0] = 1 - fixed[0]
    changed = replace(inst, fixed_neighbors=fixed)
    with pytest.raises(ValueError, match="connect_0"):
        reexecute_emitted_lp_in_child(changed, lp, bits, metrics)


def test_actual_flat_exact_ties_may_select_different_equal_optimum(original_verified_child):
    inst, _, _, _, _ = original_verified_child
    flat = replace(inst, linear=np.zeros(20), quadratic=tuple())
    with TemporaryDirectory(prefix="n20_flat_real_scip_") as tmp:
        file = Path(tmp) / "flat_original_source_geometry.lp"
        chosen, metrics = solve_scip(flat, time_limit=30., export_lp_path=file)
        report = reexecute_emitted_lp_in_child(
            flat, file.read_bytes(), chosen, metrics,
        )
    assert report["best_exact_binary64_score_numerator"] == "0"
    assert report["independent_feasible_original_local_count"] == 1077
    assert report["independent_child_status"] == "optimal"
    assert report["independent_lp_relative_gap"] <= 1e-6
    assert report["original_upstream_process_externally_authenticated"] is False


def test_reported_process_cannot_be_reinterpreted_as_original_global_scip(original_verified_child):
    inst, lp, bits, metrics, report = original_verified_child
    assert report["scope"] == (
        "review_only_second_child_Scip_readProblem_optimize_and_exact_N20_crosscheck"
    )
    assert report["structural_lp_certificate"]["scope"] == (
        "bounded_ASCII_CPLEX_LP_structural_formulation_only"
    )
    assert report["physical_RF_DO_or_manuscript_validated"] is False
