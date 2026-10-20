"""Isolated (separate Python process) read-only SCIP re-solve of supplied N20 LP.

This worker does not import Streamlit, the historical source notebook, or
the UI model compiler. Its sole mathematical input is the *actual emitted*
CPLEX LP file; it independently invokes SCIP.readProblem() then optimize().
It produces an observed process-level solver receipt, NOT a signature,
remote trusted attestation or replay of the original SCIP solver process.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sys

MAX_LP_SIZE = 100_000
SOURCE_N = 20


def _require(ok: bool, text: str) -> None:
    if not ok:
        raise RuntimeError("Independent SCIP LP process: " + text)


def solve_exported_lp(path: Path, expected_sha256: str, max_seconds: int) -> dict:
    from pyscipopt import Model
    import pyscipopt

    _require(1 <= max_seconds <= 60, "time limit outside audited bounded interval")
    _require(re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is not None,
             "invalid expected LP digest")
    _require(path.is_file() and not path.is_symlink(),
             "missing or symbolic-link input")
    lp = path.read_bytes()
    _require(0 < len(lp) <= MAX_LP_SIZE and sha256(lp).hexdigest() == expected_sha256,
             "supplied original LP bytes changed or exceeded the bound")
    _require(path.suffix == ".lp", "refuse non-LP file formats")

    # This is a completely new, separately initialized SCIP instance.
    model = Model("independent_lp_replay")
    model.hideOutput()
    model.readProblem(str(path))
    original_names = [v.name for v in model.getVars(transformed=False)]
    _require(len(original_names) == len(set(original_names))
             and len(original_names) <= 300
             and all(re.fullmatch(r"(?:x\\d+|p\\d+_\\d+)", name)
                     for name in original_names),
             "unexpected independent loaded LP variable namespace")
    _require({f"x{i}" for i in range(SOURCE_N)}.issubset(set(original_names)),
             "original 20 site choices not present in the loaded LP")
    _require(model.getObjectiveSense() == "minimize", "original LP sense is not minimization")
    model.setRealParam("limits/time", float(max_seconds))
    model.optimize()

    status = str(model.getStatus())
    number_of_solutions = int(model.getNSols())
    _require(number_of_solutions >= 0, "invalid solver solution count")
    chosen = None
    obj = None
    primal = None
    dual = None
    gap = None
    if number_of_solutions:
        solution = model.getBestSol()
        names = {v.name: v for v in model.getVars(transformed=False)}
        bits = []
        for i in range(SOURCE_N):
            value = float(model.getSolVal(solution, names[f"x{i}"]))
            _require(math.isfinite(value)
                     and min(abs(value), abs(1 - value)) <= 1e-6,
                     "nonbinary independent primal x solution")
            bits.append(int(value > .5))
        for name, variable in names.items():
            if name.startswith("p"):
                match = re.fullmatch(r"p(\\d+)_(\\d+)", name)
                _require(match is not None, "unknown pair name")
                i, j = int(match.group(1)), int(match.group(2))
                _require(0 <= i < j < SOURCE_N, "invalid pair index")
                val = float(model.getSolVal(solution, variable))
                _require(math.isfinite(val)
                         and abs(val - bits[i] * bits[j]) <= 1e-6,
                         "independent LP pair-product integrality violated")
        chosen = bits
        obj = float(model.getObjVal())
        primal = float(model.getPrimalbound())
        dual = float(model.getDualbound())
        gap = float(model.getGap())
        _require(all(math.isfinite(x) for x in (obj, primal, dual, gap)),
                 "nonfinite independent SCIP numerical bound")
    result = {
        "receipt_schema": 1,
        "scope": "fresh_separate_python_process_reads_actual_exported_binary_MILP",
        "input_lp_sha256": sha256(lp).hexdigest(),
        "input_lp_bytes": len(lp),
        "python_version": sys.version.split()[0],
        "pyscipopt_version": getattr(pyscipopt, "__version__", "unavailable"),
        "status": status,
        "best_solution_count": number_of_solutions,
        "original_binary_variable_count": len(original_names),
        "original_binary20": chosen,
        "objective_lp_decimal_approx": obj,
        "primal_bound_lp_decimal": primal,
        "dual_bound_lp_decimal": dual,
        "reported_relative_gap": gap,
        "solver_time_limit_seconds": max_seconds,
        "solver_did_read_and_optimize_lp_in_this_process": True,
        "this_is_an_untrusted_local_process_receipt_not_signed_attestation": True,
        "original_upstream_scip_execution_authenticated": False,
        "published_manuscript_or_physical_lake_quality_validated": False,
    }
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lp", type=Path, required=True)
    ap.add_argument("--expect-sha256", required=True)
    ap.add_argument("--time-limit-seconds", type=int, default=30)
    args = ap.parse_args()
    result = solve_exported_lp(args.lp, args.expect_sha256,
                               args.time_limit_seconds)
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
