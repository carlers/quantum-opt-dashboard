"""Research-side scientific claim contract for the historical lake N20 reference.

A proved SCIP optimum is a computational claim, NOT proof of historic
manuscript-input parity, scientifically elicited criteria, radio links or
physical lake coverage. No new measurements, alternate weights or sweeps.

Future dashboard consumers MAY display this certificate but MUST NOT use a
user-provided boolean as authority to upgrade the scientific claim level.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.n20_independent_geometry_audit import (
    EXPECTED_DATA_SHA, EXPECTED_FIXED, EXPECTED_FREE, SOURCE,
    EXPECTED_FEASIBLE, certify_geometry,
)
from scripts.run_n20_reference_notebook import verify_result
from scripts.studies.n20_s4_parameter_provenance import (
    ARCHIVED_NOTEBOOK, EXPECTED_ARCHIVE_SHA, FACTOR_NAMES, ORIGINAL_WEIGHTS,
    PRINTED_TABLE_IV,
)

SCHEMA = 1
ORIGINAL_FEASIBLE_SHA = (
    "2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a"
)
ALLOWED_DISPLAY_CLAIM = "verified_notebook_derived_N20_computation"
HIGHER_CLAIMS = (
    "replicated_manuscript_inputs_and_results",
    "physically_validated_monitoring_network",
    "field_verified_radio_coverage",
    "scientifically_validated_pollutant_transport",
    "proved_quantum_hardware_advantage",
)


def canonical(obj: object) -> bytes:
    return (
        json.dumps(obj, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")


def full_manifest_digest(obj: object) -> str:
    return sha256(canonical(obj)).hexdigest()


def objective_manifest(model: dict) -> dict:
    """The actual scored binary function over the same ordered master sites.

    The score is comparable as the *same function* only with matching site
    meaning, original eight criteria, linear and quadratic coefficients.
    The radio graph/constraints are deliberately NOT included: the same
    objective can be tested on different feasible sets, but this does not
    prove one scenario's physical utility is greater.
    """
    required = (
        "candidate_master_feature_positions",
        "fixed_master_feature_positions",
        "factor_column_names",
        "factor_weights_float64_hex",
        "linear_float64_hex",
        "quadratic_ij_float64_hex",
        "site_coords_epsg32651_float64_hex",
        "budget_exact",
        "dataset_sha256",
    )
    if not isinstance(model, dict) or any(key not in model for key in required):
        raise ValueError("Incomplete source numerical objective manifest")
    n = len(model["candidate_master_feature_positions"])
    if n < 1 or len(model["linear_float64_hex"]) != n:
        raise ValueError("Objective dimension and station-site meaning inconsistent")
    sites = model["candidate_master_feature_positions"]
    fixed = model["fixed_master_feature_positions"]
    if (not all(type(i) is int and i >= 0 for i in sites + fixed)
            or len(set(sites + fixed)) != len(sites) + len(fixed)):
        raise ValueError("Station identities must be distinct, ordered source feature positions")
    if len(model["factor_column_names"]) != len(model["factor_weights_float64_hex"]):
        raise ValueError("Criterion identity and weight dimensions differ")
    if len(model["site_coords_epsg32651_float64_hex"]) != n + len(fixed):
        raise ValueError("Numerical objective site-coordinate identities incomplete")
    if type(model["budget_exact"]) is not int or not 0 <= model["budget_exact"] <= n:
        raise ValueError("Invalid original binary station budget")
    for key in ("linear_float64_hex", "factor_weights_float64_hex"):
        for value in model[key]:
            try:
                x = float.fromhex(value)
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValueError("Source objective requires exact float.hex numeric fields") from exc
            if not math.isfinite(x):
                raise ValueError("Nonfinite source objective coefficient")
    edges = model["quadratic_ij_float64_hex"]
    seen = set()
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 3:
            raise ValueError("Malformed quadratic term")
        i, j, hex_q = edge
        if (type(i) is not int or type(j) is not int or not 0 <= i < j < n
                or (i, j) in seen):
            raise ValueError("Quadratic pairs must be distinct ordered local indices")
        seen.add((i, j))
        try:
            q = float.fromhex(hex_q)
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError("Invalid quadratic float.hex value") from exc
        if not math.isfinite(q):
            raise ValueError("Nonfinite quadratic coefficient")
    for row in model["site_coords_epsg32651_float64_hex"]:
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError("Invalid EPSG:32651 source coordinate")
        for v in row:
            try:
                x = float.fromhex(v)
            except (TypeError, ValueError, AttributeError) as exc:
                raise ValueError("Invalid coordinate float.hex") from exc
            if not math.isfinite(x):
                raise ValueError("Nonfinite site coordinate")
    if model["dataset_sha256"] != EXPECTED_DATA_SHA:
        raise ValueError("Objective belongs to another source dataset")

    return {key: model[key] for key in required} | {
        "objective_form": "binary_sum_a_i_x_i_plus_sum_q_ij_x_i_x_j",
        "constant_offset": 0.0,
        "source_available_weight_normalization": True,
    }


def objective_fingerprint(model: dict) -> str:
    return full_manifest_digest(objective_manifest(model))


def compare_raw_energies(model_a: dict, model_b: dict) -> dict:
    """State whether numeric energies are values of the EXACT same function.

    Even a true result means "same mathematical score", NEVER "higher real
    water-quality coverage" or absolute superiority of a network topology.
    """
    a = objective_fingerprint(model_a)
    b = objective_fingerprint(model_b)
    same = a == b
    return {
        "same_exact_objective_over_identical_ordered_sites": same,
        "first_objective_sha256": a,
        "second_objective_sha256": b,
        "comparison_status": (
            "same_mathematical_objective_raw_energy_comparison_permitted"
            if same else
            "different_site_or_scoring_definition_raw_energy_quality_claim_prohibited"
        ),
        "physical_monitoring_quality_comparison_established": False,
        "note": (
            "Equal coefficient identity permits a mathematical energy "
            "comparison only; feasible constraints/topology and physical "
            "environment still require independent interpretation."
        ),
    }


def _assert_source_bytes() -> None:
    if sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED_DATA_SHA:
        raise AssertionError("Claim gate refuses altered original GeoJSON")
    if sha256(ARCHIVED_NOTEBOOK.read_bytes()).hexdigest() != EXPECTED_ARCHIVE_SHA:
        raise AssertionError("Claim gate refuses altered original archived notebook")


def validate_evidence(original: dict, s4: dict) -> dict:
    """Source check is a real gate, not arbitrary client-provided status flags."""
    _assert_source_bytes()
    verify_result(original)
    geometry = certify_geometry(original)
    model = original["model_input"]
    if not isinstance(s4, dict) or s4.get("schema_version") != 1:
        raise AssertionError("S4 original provenance report required")
    if s4.get("scope") != (
        "read_only_N20_S4_parameter_and_AHP_provenance_no_sensitivity_sweep"
    ):
        raise AssertionError("S4 is not the frozen source-only audit")
    if (s4.get("original_source_model_sha256") != original["model_input_sha256"]
            or s4.get("original_source_geojson_sha256") != EXPECTED_DATA_SHA
            or s4.get("archived_original_notebook_sha256") != EXPECTED_ARCHIVE_SHA):
        raise AssertionError("S4 and original source model identity differ")

    reference = s4["reference"]
    if (reference["N"], reference["K"], reference["original_fixed_count"]) != (20, 5, 15):
        raise AssertionError("S4 did not audit the actual N20 K5 15-fixed scenario")
    if (reference["original_best_local_indices"] != [0, 1, 3, 6, 7]
            or reference["original_feasible_subsets"] != EXPECTED_FEASIBLE
            or reference["original_feasible_set_sha256"] != ORIGINAL_FEASIBLE_SHA
            or abs(float(reference["original_energy"]) - original["original_energy"]) > 1e-7):
        raise AssertionError("S4 optimum or exact feasible set does not match original")
    original_criteria = s4["original_factor_data"]
    if (original_criteria["original_eight_names"] != FACTOR_NAMES
            or original_criteria["all_source_points"] != 5417
            or original_criteria["all_source_features_with_any_missing"] != 0
            or original_criteria["selected_20_with_any_missing"] != 0):
        raise AssertionError("Unverified GIS factor identity/completeness")
    original_weights = tuple(float.fromhex(h) for h in
                             original_criteria["original_weights_float64_hex"])
    if (original_weights != ORIGINAL_WEIGHTS
            or model["factor_column_names"] != FACTOR_NAMES
            or model["factor_weights_float64_hex"] !=
            original_criteria["original_weights_float64_hex"]
            or abs(float(original_criteria["original_weights_sum"]) - 1.0001) > 1e-10):
        raise AssertionError("Changed original weights or factor semantics")
    s4_geom = s4["original_spatial_inputs"]
    if (s4_geom["source_hull_geometry_graph_sha256"] !=
            geometry["spatial_graph_sha256"]
            or s4_geom["source_490_candidate_related_pair_checks"] != 490
            or s4_geom["original_direct_free_free_edges"] != 11
            or s4_geom["original_direct_free_fixed_edges"] != 34
            or s4_geom["original_Dmax_m_float64_hex"] !=
            model["d_max_m_float64_hex"]):
        raise AssertionError("S4 original lake wireless geometry was altered")
    missing = s4["sensitivity_status"]
    if missing.get("new_parameter_values_tested") != []:
        raise AssertionError("S4 source-only provenance may not be relabeled a sweep")
    if not all(
        isinstance(value, str) and value.startswith("BLOCKED_")
        for key, value in missing.items()
        if key != "new_parameter_values_tested"
    ):
        raise AssertionError("Physical evidence blockers cannot be silently removed")

    manuscript = s4["manuscript_transcription_not_original_solver_input"]
    if (manuscript.get("source_D2_field") != "d2_road_proximity"
            or "WorldPop" not in manuscript.get("manuscript_D2_label", "")
            or manuscript.get("table_IV_printed_global_eight_weights") !=
            list(PRINTED_TABLE_IV)):
        raise AssertionError("Original road vs manuscript population criterion mismatch hidden")
    # No boolean or string in a user-selected UI input can satisfy the need
    # for raw expert judgments, original GIS recipe or measured RF evidence.
    objective_sha = objective_fingerprint(model)
    return {
        "schema_version": SCHEMA,
        "certification_scope": "source_notebook_N20_K5_mathematical_parity_only",
        "source_dataset_sha256": EXPECTED_DATA_SHA,
        "archived_notebook_sha256": EXPECTED_ARCHIVE_SHA,
        "source_model_input_sha256": original["model_input_sha256"],
        "source_objective_fingerprint_sha256": objective_sha,
        "independent_geometry_sha256": geometry["spatial_graph_sha256"],
        "baseline": {
            "N": 20, "K": 5, "existing": 15,
            "selected_local": [0, 1, 3, 6, 7],
            "original_energy": float(original["original_energy"]),
            "feasible_K5": EXPECTED_FEASIBLE,
            "feasible_K5_sha256": ORIGINAL_FEASIBLE_SHA,
        },
        "claim_gates": {
            "computational_source_replay": {
                "status": "verified",
                "display_claim": ALLOWED_DISPLAY_CLAIM,
                "evidence": "source SHA + model digest + SCIP + exhaustive K5 + raw GeoJSON graph + S4",
            },
            "historical_manuscript_parity": {
                "status": "blocked_no_authoritative_inputs",
                "blockers": [
                    "original_expert_pairwise_aggregation_and_AHP_revision",
                    "manuscript_D2_WorldPop_vs_GeoJSON_d2_road_proximity",
                    "paper_N20_SCIP_original_coefficient_and_environment_trace",
                ],
            },
            "physical_scientific_validation": {
                "status": "blocked_no_field_calibration",
                "blockers": [
                    "verified_shoreline_island_geometry",
                    "measured_radio_range_antenna_propagation_and_existing_backhaul",
                    "original_lake_hydrology_spatial_DO_and_current_data",
                    "independently_validated_factor_provenance_and_monitoring_outcomes",
                ],
            },
        },
        "forbidden_implied_claims": list(HIGHER_CLAIMS),
        "source_only_model_selection_status": "not_authorized_to_replace_baseline",
        "new_sensitivity_parameters_tested": [],
        "physical_quality_guarantee": False,
        "quantum_hardware_experiment": False,
        "main_preview_or_production_change_authorized": False,
        "interpretation": (
            "This verifies a specified mathematical instance. It does not "
            "establish that selected sites are physically deployable, that "
            "published paper input coefficients match, or that another "
            "mathematical objective has superior monitoring value."
        ),
    }


def require_display_claim(certificate: dict, requested_claim: str) -> str:
    """Fail closed. This research-only contract does not mint paper/RF approval."""
    if requested_claim != ALLOWED_DISPLAY_CLAIM:
        raise PermissionError("Scientific claim not established by N20 source-only evidence")
    gates = certificate.get("claim_gates", {})
    verified = gates.get("computational_source_replay", {})
    if (certificate.get("certification_scope") != "source_notebook_N20_K5_mathematical_parity_only"
            or certificate.get("schema_version") != SCHEMA
            or verified.get("status") != "verified"
            or verified.get("display_claim") != ALLOWED_DISPLAY_CLAIM
            or certificate.get("claim_gates", {}).get("historical_manuscript_parity", {}).get("status")
            != "blocked_no_authoritative_inputs"
            or certificate.get("claim_gates", {}).get("physical_scientific_validation", {}).get("status")
            != "blocked_no_field_calibration"):
        raise PermissionError("Incomplete or incorrectly upgraded scientific claim certificate")
    return "Verified notebook-derived N=20/K=5 computational result; manuscript and physical validation pending."


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference", required=True, type=Path)
    p.add_argument("--provenance", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite a prior scientific claim certificate")
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    s4 = json.loads(args.provenance.read_text(encoding="utf-8"))
    cert = validate_evidence(reference, s4)
    # Emit only once the exact intended display wording is authorized.
    require_display_claim(cert, ALLOWED_DISPLAY_CLAIM)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(cert))
    print("N20_SCIENTIFIC_CLAIM_GATE " + json.dumps({
        "source_only": cert["claim_gates"]["computational_source_replay"]["status"],
        "manuscript": cert["claim_gates"]["historical_manuscript_parity"]["status"],
        "physical": cert["claim_gates"]["physical_scientific_validation"]["status"],
        "objective_sha256": cert["source_objective_fingerprint_sha256"],
        "source_N20_K5_feasible": cert["baseline"]["feasible_K5"],
        "new_sensitivity_values_tested": cert["new_sensitivity_parameters_tested"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
