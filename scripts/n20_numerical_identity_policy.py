"""Source-only diagnostic classification of observed N20 binary64 drift.

NEVER normalize historical coefficients, equate distinct objective hashes,
reuse cached solver results, or claim historical manuscript/physical validation.
This is NOT a general floating-point equivalence relation and its post-hoc
envelope MUST NOT be used to accept new model inputs or solver outputs.
"""
from __future__ import annotations

import math
import struct

from scripts import science_claim_gate as gate
from scripts.run_n20_reference_notebook import (
    EXPECTED_DATA_SHA, EXPECTED_FIXED_MASTER, EXPECTED_FREE_MASTER,
    EXPECTED_NOTEBOOK_SHA,
)

SCHEMA = 1
# Bounds taken from the observed 2026-10-19 r1/r2/r3 coefficients, not proposed
# permissible scientific perturbations. Never export these as new default weights.
OBSERVED_LINEAR_ULP_ENVELOPE = {9: 4, 10: 16, 17: 2, 19: 128}
_ALLOWED_CHANGE_KEYS = frozenset(("linear_float64_hex", "free_fixed_pair_trace"))
_FLOAT64_SIGN_BIT = 1 << 63
_FLOAT64_MASK = (1 << 64) - 1


def _ordered_float_bits(value: float) -> int:
    """A monotone IEEE-754 key, to count ULPs across positive/negative numbers."""
    bits = struct.unpack(">Q", struct.pack(">d", value))[0]
    return (~bits & _FLOAT64_MASK) if bits & _FLOAT64_SIGN_BIT else bits | _FLOAT64_SIGN_BIT


def _ulp_separation(a_hex: str, b_hex: str) -> int:
    a, b = float.fromhex(a_hex), float.fromhex(b_hex)
    if not math.isfinite(a) or not math.isfinite(b):
        raise ValueError("Nonfinite float64 input not diagnostic evidence")
    return abs(_ordered_float_bits(a) - _ordered_float_bits(b))


def _source_like_model(model: dict) -> None:
    """Require immutable original cohort/criteria, but DO NOT certify source replay.

    Full source verification needs the independent notebook, GIS and S4 gates.
    """
    gate.objective_manifest(model)
    if (model.get("dataset_sha256") != EXPECTED_DATA_SHA
            or model.get("archived_notebook_sha256") != EXPECTED_NOTEBOOK_SHA
            or model.get("model_family") != "notebook_derived_laguna_N20_local_one_hop"
            or model["candidate_master_feature_positions"] != EXPECTED_FREE_MASTER
            or model["fixed_master_feature_positions"] != EXPECTED_FIXED_MASTER
            or model.get("budget_exact") != 5
            or model["factor_column_names"] != list(gate.FACTOR_NAMES)
            or model["factor_weights_float64_hex"] != [
                float(w).hex() for w in gate.ORIGINAL_WEIGHTS
            ]):
        raise ValueError("Numerical diagnosis is limited to source-like N20/K5 inputs")


def diagnose_original_n20_objective_pair(model_a: dict, model_b: dict) -> dict:
    """Classify *observed* N20 precision modes, without any approval semantics."""
    _source_like_model(model_a)
    _source_like_model(model_b)
    objective_a = gate.objective_fingerprint(model_a)
    objective_b = gate.objective_fingerprint(model_b)
    full_a = gate.full_manifest_digest(model_a)
    full_b = gate.full_manifest_digest(model_b)
    strict_other_fields = (
        set(model_a) == set(model_b)
        and all(model_a[key] == model_b[key]
                for key in model_a if key not in _ALLOWED_CHANGE_KEYS)
    )
    linear_a = model_a["linear_float64_hex"]
    linear_b = model_b["linear_float64_hex"]
    changed = []
    allowed_observed_numeric = True
    for index, (aa, bb) in enumerate(zip(linear_a, linear_b)):
        if aa == bb:
            continue
        n_ulp = _ulp_separation(aa, bb)
        a_num, b_num = float.fromhex(aa), float.fromhex(bb)
        max_ulp = OBSERVED_LINEAR_ULP_ENVELOPE.get(index, 0)
        in_envelope = (
            n_ulp <= max_ulp
            and abs(a_num - b_num) <= 2.220446049250313e-16
        )
        if not in_envelope:
            allowed_observed_numeric = False
        changed.append({
            "index": index,
            "first_hex": aa,
            "second_hex": bb,
            "ulp_distance_exact_integer": n_ulp,
            "absolute_difference": abs(a_num - b_num),
            "within_observed_posthoc_envelope": in_envelope,
        })
    diagnostics_match_known_low_bit_pattern = (
        strict_other_fields and allowed_observed_numeric
        and (full_a == full_b or bool(changed))
    )
    same_exact_objective = objective_a == objective_b
    return {
        "schema_version": SCHEMA,
        "scope": "source-like original N20/K5 observed coefficient precision only",
        "first_full_model_sha256": full_a,
        "second_full_model_sha256": full_b,
        "first_exact_objective_sha256": objective_a,
        "second_exact_objective_sha256": objective_b,
        "same_exact_objective": same_exact_objective,
        "same_complete_model_input": full_a == full_b,
        "same_nontraced_nonscore_original_metadata": strict_other_fields,
        "changed_linear_coefficients": changed,
        "observed_posthoc_numerical_envelope_only": diagnostics_match_known_low_bit_pattern,
        "raw_energy_as_same_exact_mathematical_function_permitted": same_exact_objective,
        "tolerance_used_for_cache_or_solver_result_approval": False,
        "cached_solver_result_reuse_permitted_by_this_diagnostic": False,
        "independent_source_gis_s4_validation_done_here": False,
        "solver_optimality_authenticated_here": False,
        "manuscript_input_parity_established": False,
        "field_radio_or_water_quality_validated": False,
        "warning": (
            "This is an observational source-like input diagnostic, not model identity. "
            "Different exact objective or full model SHAs are distinct and can never be "
            "substituted in scenario hashes or solver exports. Partial source/graph "
            "input checks here are not cold notebook/GIS/SCIP/S4 certification."
        ),
    }
