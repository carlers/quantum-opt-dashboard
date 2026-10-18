"""Read-only compiled mathematical audit for the exact water-quality Instance.

The single source of numerical truth is model.make_instance's Instance:
the SCIP MILP's product variables match solve_scip() in model.py, and the
QUBO coefficient/slack table comes from qubo.make_qubo() directly.

This module does NOT parse LaTeX, execute arbitrary formulas, run OpenJij,
or change the original scientific formulation.
"""
from __future__ import annotations

import hashlib
import json
from math import isclose
from typing import Any, Mapping

import numpy as np

from model import Instance
from qubo import Qubo, best_slack_assignment, energy as qubo_energy, make_qubo, safe_penalty

SCHEMA_VERSION = 1


def canonical_json(data: dict) -> str:
    """Fixed byte serialization, capturing all float64 bits as explicit hex fields."""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False)


def _number(value: float) -> dict[str, float | str]:
    val = float(value)
    if not np.isfinite(val):
        raise ValueError("An audit cannot contain nonfinite coefficients")
    return {"value": val, "float64_hex": val.hex()}


def configuration_key(settings: Mapping[str, Any], dataset_sha256: str) -> str:
    """Detect a config change before displaying a stale SCIP solution."""
    return hashlib.sha256(canonical_json({
        "settings": dict(settings), "dataset_sha256": dataset_sha256,
    }).encode("utf-8")).hexdigest()


def build_audit(
    instance: Instance, *,
    dataset_sha256: str, settings: Mapping[str, Any],
    budget_penalty: float | None = None, connectivity_penalty: float | None = None,
) -> tuple[dict, Qubo]:
    """Export original MIQP, SCIP pair-product MILP and *actual* encoded QUBO.

    A QUBO is built only for inspection. It is NOT the formulation solved by
    the current Streamlit SCIP button.
    """
    n = len(instance.free_indices)
    if n == 0 or n != len(instance.linear) or len(instance.neighbors) != n:
        raise ValueError("Malformed original model")
    if not isinstance(dataset_sha256, str) or len(dataset_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in dataset_sha256
    ):
        raise ValueError("Expected lowercase SHA-256 of original GeoJSON bytes")
    compiled = make_qubo(instance, budget_penalty=budget_penalty,
                         connectivity_penalty=connectivity_penalty)
    pair_terms = [
        {"i": int(i), "j": int(j), "q": _number(q), "z_name": f"z_{i}_{j}"}
        for i, j, q in instance.quadratic
    ]
    original = {
        "variable_type": "binary",
        "variable_count": n,
        "objective_sense": "minimize",
        "linear_terms": [
            {"i": i, "a": _number(v)} for i, v in enumerate(instance.linear)
        ],
        "quadratic_terms": pair_terms,
        "budget_equality": {
            "rhs": int(instance.budget), "variable_indices": list(range(n))
        },
        "local_one_hop_connectivity": [
            {
                "i": i,
                "fixed_neighbor_indicator": int(instance.fixed_neighbors[i]),
                "free_neighbor_indices": [int(j) for j in instance.neighbors[i]],
                "inequality": "x_i <= fixed_neighbor_indicator + sum(x_j for neighbor j)",
            }
            for i in range(n)
        ],
        "connectivity_semantics": (
            "Each selected free site has >=1 selected free neighbor or an "
            "existing fixed neighbor; this does NOT enforce a graph path "
            "from every selected free site to a fixed station."
        ),
        "fixed_station_terms": (
            "Interactions with existing fixed stations are already folded "
            "into the linear coefficients a_i."
        ),
    }
    # These are the *actual* x_i*x_j -> z_ij inequalities used by solve_scip:
    # z>=xi+xj-1, z<=xi, z<=xj (binary z).
    milp = {
        "solver": "PySCIPOpt/SCIP",
        "implemented_representation": "exact binary pair-product MILP, not native MIQP",
        "decision_binary_count": n,
        "auxiliary_pair_binary_count": len(pair_terms),
        "objective_linear_terms": original["linear_terms"],
        "product_variables": [
            {"name": term["z_name"], "i": term["i"], "j": term["j"],
             "coefficient": term["q"],
             "constraints": [
                 f"{term['z_name']} >= x_{term['i']} + x_{term['j']} - 1",
                 f"{term['z_name']} <= x_{term['i']}",
                 f"{term['z_name']} <= x_{term['j']}",
             ]}
            for term in pair_terms
        ],
        "original_budget_and_connectivity": "identical to original section",
    }
    qterms = [
        {"i": int(i), "j": int(j), "coefficient": _number(value)}
        for (i, j), value in sorted(compiled.coefficients.items())
    ]
    qubo = {
        "role": "inspection-only, NOT executed by current Streamlit SCIP action",
        "encoder": "explicit binary auxiliary slack from qubo.make_qubo",
        "not_historical_converter": "not the notebook's JijModeling/OMMX to_qubo()",
        "binary_variable_count": compiled.n_variables,
        "original_x_count": compiled.n_free,
        "original_x_indices": list(range(n)),
        "budget_penalty": _number(compiled.budget_penalty),
        "connectivity_penalty": _number(compiled.connectivity_penalty),
        "sufficient_global_penalty_threshold_example": _number(safe_penalty(instance)),
        "offset": _number(compiled.offset),
        "nonzero_upper_triangular_terms": qterms,
        "auxiliary_binary_slacks": [
            {"site_i": i, "bit_indices": list(group), "bit_weights": list(weights),
             "s_i": "sum(bit_weight * binary_aux_bit)"}
            for i, (group, weights) in enumerate(zip(
                compiled.slack_variables, compiled.slack_weights
            ))
        ],
        "energy_convention": "offset + sum_{i<=j} Q_ij b_i b_j",
        "penalty_interpretation": (
            "A penalty greater than 2 times the absolute objective bound is "
            "sufficient for globally optimal feasible solutions IF the "
            "original problem is feasible. It is NOT a guarantee that SA "
            "sampling finds a feasible solution."
        ),
    }
    source = {
        "dataset_sha256": dataset_sha256,
        "settings": dict(settings),
        "free_master_feature_positions": [int(x) for x in instance.free_indices],
        "fixed_master_feature_positions": [int(x) for x in instance.fixed_indices],
        "utility_float64": [_number(v) for v in instance.utility],
        "coordinate_epsg32651_float64": [
            [_number(x), _number(y)] for x, y in instance.coords
        ],
        "d_max_m": _number(instance.d_max),
    }
    document = {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "original_miqp": original,
        "scip_solver_milp": milp,
        "encoded_qubo": qubo,
    }
    digest = hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()
    document["model_fingerprint_sha256"] = digest
    return document, compiled


def verify_selected(
    instance: Instance, qubo: Qubo, document: dict, selected: np.ndarray,
) -> dict:
    """Independent original objective/constraint audit against EXPORTED terms.

    Uses the exported numeric terms, rather than PySCIPOpt's returned energy
    or a handwritten symbolic UI equation. The QUBO witness fills in slacks.
    """
    x = np.asarray(selected)
    n = len(instance.free_indices)
    if x.shape != (n,) or not np.isin(x, (0, 1)).all():
        raise ValueError("Must supply a binary selection for every free site")
    chosen = [int(i) for i in np.flatnonzero(x)]
    terms = document["original_miqp"]
    linear = sum(row["a"]["value"] * int(x[row["i"]])
                 for row in terms["linear_terms"])
    quadratic = sum(row["q"]["value"] * int(x[row["i"]]) * int(x[row["j"]])
                    for row in terms["quadratic_terms"])
    residuals = [
        int(x[row["i"]]) - row["fixed_neighbor_indicator"] -
        sum(int(x[j]) for j in row["free_neighbor_indices"])
        for row in terms["local_one_hop_connectivity"]
    ]
    budget_residual = len(chosen) - terms["budget_equality"]["rhs"]
    feasible = budget_residual == 0 and all(r <= 0 for r in residuals)
    expanded = qubo_energy(qubo, best_slack_assignment(instance, qubo, x.astype(int).tolist()))
    objective = float(linear + quadratic)
    if feasible and not isclose(expanded, objective, rel_tol=1e-10, abs_tol=1e-7):
        raise AssertionError("A feasible original solution must have zero minimized QUBO penalty")
    return {
        "selected_local_indices": chosen,
        "selected_master_feature_positions": [
            int(instance.free_indices[i]) for i in chosen
        ],
        "linear_objective": float(linear),
        "quadratic_objective": float(quadratic),
        "original_objective": objective,
        "budget_residual": budget_residual,
        "local_connectivity_residuals": residuals,
        "violated_one_hop_sites": [i for i, r in enumerate(residuals) if r > 0],
        "original_feasible": bool(feasible),
        "qubo_energy_with_minimized_slacks": float(expanded),
        "compiled_qubo_offset": float(qubo.offset),
        "model_fingerprint_sha256": document["model_fingerprint_sha256"],
    }
