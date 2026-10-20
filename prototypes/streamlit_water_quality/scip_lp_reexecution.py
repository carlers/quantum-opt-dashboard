"""Re-execute a verified original N20 LP via a genuinely separate SCIP process.

The launched worker reads the *actual* byte-identical emitted LP, reconstructs
SCIP's internal model using readProblem(), optimizes it anew and reports primal,
dual, gap and selected stations. The parent cross-checks original compilation
and mathematical source-site feasibility independently.

This is strictly a PROCESS OBSERVATION/REPLICATION receipt, NOT an externally
signed/remote hardware attestation of the previous solver execution.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np

from scip_lp_structure import certify_emitted_scip_lp
from runtime_attestation import exact_bounded_oracle, exact_selection_objective

_TIMEOUT_SECONDS = 60
_TIME_LIMIT_SECONDS = 30
_WORKER = Path(__file__).with_name("scip_lp_reexecution_worker.py")


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError("Separate SCIP execution witness: " + message)


def _source_local_feasible(instance, chosen: list[int]) -> bool:
    """Recalculate one-hop feasibility for EVERY selected station, not just K.

    A binary64-exact optimum score by itself is NOT an admissibility proof:
    an infeasible selection can have the same objective as a feasible optimum,
    especially for exact-tie or flat-objective experimental settings.
    """
    if len(chosen) != 20 or sum(chosen) != instance.budget:
        return False
    for i, selected in enumerate(chosen):
        if selected and not (
            bool(instance.fixed_neighbors[i])
            or any(chosen[j] for j in instance.neighbors[i])
        ):
            return False
    return True


def check_independent_process_receipt(
    instance, lp_bytes: bytes, recorded: dict, original_selection,
    original_metrics: dict,
) -> dict:
    """Fail closed on mismatched/forged process observation or objective bound."""
    certificate = certify_emitted_scip_lp(instance, lp_bytes)
    _require(type(recorded) is dict
             and recorded.get("receipt_schema") == 1
             and recorded.get("scope")
             == "fresh_separate_python_process_reads_actual_exported_binary_MILP"
             and recorded.get("solver_did_read_and_optimize_lp_in_this_process") is True
             and recorded.get("this_is_an_untrusted_local_process_receipt_not_signed_attestation") is True
             and recorded.get("original_upstream_scip_execution_authenticated") is False
             and recorded.get("published_manuscript_or_physical_lake_quality_validated") is False,
             "missing or escalated process receipt claims")
    _require(recorded.get("input_lp_sha256") == certificate["original_scip_lp_sha256"]
             and recorded.get("input_lp_bytes") == len(lp_bytes)
             and recorded.get("original_binary_variable_count")
             == certificate["binary_variable_count"]
             and type(recorded.get("solver_time_limit_seconds")) is int
             and recorded["solver_time_limit_seconds"] == _TIME_LIMIT_SECONDS,
             "replay receipt is for a different emitted LP/variable set")
    _require(original_metrics.get("status") == "optimal"
             and original_metrics.get("optimal") is True
             and recorded.get("status") == "optimal"
             and type(recorded.get("best_solution_count")) is int
             and recorded["best_solution_count"] >= 1,
             "only two actually optimal SCIP runs may be equated")
    chosen = recorded.get("original_binary20")
    _require(type(chosen) is list and len(chosen) == 20
             and all(type(bit) is int and bit in (0, 1) for bit in chosen)
             and sum(chosen) == instance.budget,
             "replayed original 20 site vector is not binary K-budget feasible")
    n = len(instance.free_indices)
    _require(n == 20, "only original N20 source is permitted")
    source_bits = np.asarray(original_selection)
    _require(source_bits.shape == (20,) and np.isin(source_bits, (0, 1)).all()
             and int(source_bits.sum()) == instance.budget,
             "upstream source selection changed or malformed")
    source_vector = [int(x) for x in source_bits]
    _require(_source_local_feasible(instance, source_vector),
             "upstream original SCIP selection violates source local graph")
    _require(_source_local_feasible(instance, chosen),
             "independent replayed SCIP selection violates source local graph")
    oracle = exact_bounded_oracle(instance, "source_local", None)
    _require(oracle["feasible_count"] > 0,
             "replay claims feasible selection for a mathematically infeasible model")
    best = exact_selection_objective(instance, oracle["exact_selected_indices"])
    orig_ids = np.flatnonzero(source_bits).tolist()
    new_ids = [i for i, bit in enumerate(chosen) if bit]
    _require(exact_selection_objective(instance, orig_ids) == best
             and exact_selection_objective(instance, new_ids) == best,
             "independent second SCIP source selection is not a mathematically exact optimum")

    values = [
        recorded.get("objective_lp_decimal_approx"),
        recorded.get("primal_bound_lp_decimal"),
        recorded.get("dual_bound_lp_decimal"),
        recorded.get("reported_relative_gap"),
        original_metrics.get("energy"),
    ]
    _require(all(type(x) in (int, float) and math.isfinite(x) for x in values),
             "nonfinite SCIP gap/objective/bounds")
    objective, primal, dual, gap, upstream_obj = map(float, values)
    _require(gap >= 0 and gap <= 1e-6
             and dual <= primal + 1e-7
             and abs(primal - dual) <= 1e-6
             and abs(objective - primal) <= 1e-7,
             "independent SCIP primal/dual bounds do not prove numerical convergence")
    _require(math.isclose(objective, float(best), rel_tol=0, abs_tol=1e-7)
             and math.isclose(upstream_obj, float(best), rel_tol=0, abs_tol=1e-7),
             "independent parsed LP objective and source binary64 model differ")
    normalized = {
        "schema_version": 1,
        "scope": "review_only_second_child_Scip_readProblem_optimize_and_exact_N20_crosscheck",
        "source_original_scip_lp_sha256": certificate["original_scip_lp_sha256"],
        "structural_lp_certificate": certificate,
        "original_upstream_status": original_metrics["status"],
        "independent_child_status": recorded["status"],
        "original_selected_indices": orig_ids,
        "independent_child_selected_indices": new_ids,
        "different_equally_exact_optimal_sites_permitted": orig_ids != new_ids,
        "best_exact_binary64_score_numerator": str(best.numerator),
        "best_exact_binary64_score_denominator": str(best.denominator),
        "independent_lp_objective_approx": objective,
        "independent_lp_primal_bound": primal,
        "independent_lp_dual_bound": dual,
        "independent_lp_relative_gap": gap,
        "independent_feasible_original_local_count": oracle["feasible_count"],
        "upstream_selected_original_graph_feasible": True,
        "second_process_selected_original_graph_feasible": True,
        "replay_status_source_math_crosschecked": True,
        "independent_lp_reader_reoptimized_in_separate_process_as_reported": True,
        "original_upstream_process_externally_authenticated": False,
        "session_is_cryptographically_signed": False,
        "physical_RF_DO_or_manuscript_validated": False,
    }
    return normalized


def reexecute_emitted_lp_in_child(
    instance, lp_bytes: bytes, original_selection, original_metrics: dict,
    *, worker_path: Path | None = None,
) -> dict:
    """Bounded separate Python+SCIP process; do not rely on shell or cached LP.

    Does NOT mutate the original Streamlit app or its actual solver. Separate
    recorded process output is verified by an in-process mathematical oracle.
    """
    initial = certify_emitted_scip_lp(instance, lp_bytes)
    executable = (worker_path if worker_path is not None else _WORKER).resolve(strict=True)
    _require(executable.is_file() and executable.suffix == ".py",
             "separate solver worker module missing")
    with TemporaryDirectory(prefix="n20_source_lp_replay_") as tmp:
        lp_file = Path(tmp) / "source_original_emitted.lp"
        lp_file.write_bytes(lp_bytes)
        cmd = [
            sys.executable, "-I", str(executable),
            "--lp", str(lp_file),
            "--expect-sha256", initial["original_scip_lp_sha256"],
            "--time-limit-seconds", str(_TIME_LIMIT_SECONDS),
        ]
        try:
            # No shell, network, executable sourced from an uncontrolled result
            # or inherited arbitrary UI file paths. The child only reads LP.
            res = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=_TIMEOUT_SECONDS + 15, check=False)
        except subprocess.TimeoutExpired as exc:
            raise ValueError("Separate SCIP execution witness: fresh worker timed out") from exc
        _require(res.returncode == 0 and len(res.stdout) <= 24_000,
                 "fresh SCIP solver process failed or emitted too much output")
        try:
            observation = json.loads(res.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("Separate SCIP execution witness: invalid process JSON") from exc
        report = check_independent_process_receipt(
            instance, lp_bytes, observation, original_selection, original_metrics,
        )
        # Store the observed child receipt separately from the analytical
        # verification. A single local machine may forge BOTH: no signing claim.
        report["observed_child_receipt"] = observation
        report["observed_stdout_sha256"] = sha256(res.stdout.encode()).hexdigest()
        report["observed_stderr_sha256"] = sha256(res.stderr.encode()).hexdigest()
        report["child_stderr_empty"] = not res.stderr.strip()
        return report
