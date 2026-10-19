"""Read-only N20 spatial/AHP provenance gate; NO alternate-parameter sweep.

Protocol-first docs/research_protocols/N20_S4_PARAMETER_PROVENANCE_GATES_2026_10_19.md.
Original manuscript table numbers are labeled documentary transcriptions, not
inputs secretly substituted for the historical solver's source weights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy as np
import scipy
import shapely

from scripts.n20_independent_geometry_audit import (
    EXPECTED_DATA_SHA, EXPECTED_FREE, EXPECTED_FIXED,
    EXPECTED_FEASIBLE, SOURCE, certify_geometry,
)
from scripts.run_n20_reference_notebook import verify_result

ROOT = Path(__file__).resolve().parents[2]
ARCHIVED_NOTEBOOK = ROOT / "problems/water_quality/notebooks/experiment9 grid search copy.ipynb"
EXPECTED_ARCHIVE_SHA = "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"
MANUSCRIPT_LOCAL_DOCX_SHA = "f667995bc2bbf1bee191b5294fc26f366767bc72b78478e547419689b6eaf2be"
FACTOR_NAMES = [
    "a1_river_proximity", "a2_runoff_proximity", "b1_fishpen_density",
    "b2_hypoxic_proximity", "c1_bathymetric_depressions",
    "c2_outlet_proximity", "d1_boatramp_proximity", "d2_road_proximity",
]
ORIGINAL_WEIGHTS = (.3671, .1224, .2508, .0502, .1278, .0183, .0476, .0159)
# User manuscript, printed Table III; exact rational pairwise comparisons.
TABLE_III = [
    [1, 4, 6, 8],
    [1 / 4, 1, 3, 5],
    [1 / 6, 1 / 3, 1, 3],
    [1 / 8, 1 / 5, 1 / 3, 1],
]
# Owner-provided manuscript printed Table IV global weights, NOT historical source input.
PRINTED_TABLE_IV = (
    .276095907, .276095907, .17922015, .089610075,
    .087188181, .043594091, .024097845, .024097845,
)
EXPECTED_LOCAL_SHA = "2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a"


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def main_ahp_priority(table):
    """Source transcribed printed matrix: principal right eigenvector, NOT printed weights."""
    a = np.asarray(table, dtype=float)
    if (a.shape != (4, 4) or not np.isfinite(a).all()
            or np.any(a <= 0) or not np.allclose(a * a.T, 1.0, atol=1e-12)):
        raise ValueError("4x4 reciprocal positive complete AHP matrix required")
    eigenvalues, eigenvectors = np.linalg.eig(a)
    n = int(np.argmax(np.real(eigenvalues)))
    if abs(float(np.imag(eigenvalues[n]))) > 1e-10:
        raise ValueError("AHP dominant eigenvalue is not real")
    v = np.asarray(np.real(eigenvectors[:, n]), dtype=float)
    if np.all(v < 0):
        v *= -1
    if not np.all(v > 0):
        raise ValueError("AHP principal vector must be strictly positive")
    p = v / np.sum(v)
    lam = float(np.real(eigenvalues[n]))
    return {
        "principal_right_eigenvector": [float(x) for x in p],
        "lambda_max": lam,
        "consistency_index": (lam - 4) / 3,
        "consistency_ratio_RI4_0_90": (lam - 4) / (3 * 0.9),
    }


def factor_utility(factors, weights):
    """Exactly source notebook's nan-aware available-weight normalization."""
    f = np.asarray(factors, dtype=float)
    w = np.asarray(weights, dtype=float)
    if f.ndim != 2 or f.shape[1] != 8 or w.shape != (8,):
        raise ValueError("Eight criteria in original fixed order required")
    if not np.isfinite(w).all() or np.any(w < 0):
        raise ValueError("Invalid source factor weights")
    if np.isinf(f).any():
        raise ValueError("Infinite input factors are not accepted")
    active = ~np.isnan(f)
    numerator = np.nansum(f * w, axis=1)
    denominator = np.nansum(active * w, axis=1)
    util = np.clip(numerator / np.where(denominator == 0, 1, denominator), 0, 1)
    return numerator, denominator, util


def parent_weight_sums(weights):
    if len(weights) != 8:
        raise ValueError("Need source-ordered eight subcriteria weights")
    return [float(sum(weights[i:i + 2])) for i in (0, 2, 4, 6)]


def check_model_snapshot(record, spatial):
    verify_result(record)  # full source fingerprint, exact N20/SCIP/feasible SHA gates
    model = record["model_input"]
    if (model.get("factor_column_names") != FACTOR_NAMES
            or model.get("candidate_master_feature_positions") != EXPECTED_FREE
            or model.get("fixed_master_feature_positions") != EXPECTED_FIXED):
        raise AssertionError("Original factor names and site indices differ")
    if (record["feasible_combinations"] != EXPECTED_FEASIBLE
            or record["feasible_site_sets_sha256"] != EXPECTED_LOCAL_SHA):
        raise AssertionError("Original source one-hop feasible membership changed")
    expected_constants = {
        "hull_ratio_float64_hex": 0.05,
        "fixed_spacing_buffer_float64_hex": 1.15,
        "redundancy_length_m_float64_hex": 7500.0,
        "wake_length_m_float64_hex": 1000.0,
        "redundancy_beta_float64_hex": 1.0,
        "wake_delta_float64_hex": 1.0,
    }
    for name, expected in expected_constants.items():
        if float.fromhex(model[name]) != expected:
            raise AssertionError(f"Historical source parameter changed: {name}")
    declared = tuple(float.fromhex(v) for v in model["factor_weights_float64_hex"])
    if declared != ORIGINAL_WEIGHTS:
        raise AssertionError("Historical source AHP weight vector changed")
    if (spatial["model_input_sha256"] != record["model_input_sha256"]
            or spatial["source_data_sha256"] != EXPECTED_DATA_SHA
            or spatial["spatial_graph"]["feasible_site_sets_sha256"] != EXPECTED_LOCAL_SHA):
        raise AssertionError("Independent source geometry/model identity differs")


def analyze(record):
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED_DATA_SHA:
        raise AssertionError("Source GeoJSON content differs")
    if hashlib.sha256(ARCHIVED_NOTEBOOK.read_bytes()).hexdigest() != EXPECTED_ARCHIVE_SHA:
        raise AssertionError("Original archived notebook differs")
    spatial = certify_geometry(record)  # independent reconstruction from original raw GeoJSON
    check_model_snapshot(record, spatial)
    model = record["model_input"]
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    features = raw["features"]
    if len(features) != 5417:
        raise AssertionError("Original source feature count differs")
    vals = np.asarray([
        [np.nan if row["properties"].get(name) is None
         else float(row["properties"][name]) for name in FACTOR_NAMES]
        for row in features
    ], dtype=float)
    if np.isinf(vals).any():
        raise AssertionError("Source factor contains an infinite value")
    weights = np.asarray(ORIGINAL_WEIGHTS)
    numerator, denominator, utility = factor_utility(vals, weights)
    candidates = EXPECTED_FREE
    # Compare source emitted numerators, denominators and site utility.
    for key, derived in [
        ("utility_numerator_free_float64_hex", numerator[candidates]),
        ("utility_denominator_free_float64_hex", denominator[candidates]),
        ("utility_free_float64_hex", utility[candidates]),
    ]:
        reported = np.asarray([float.fromhex(v) for v in model[key]], dtype=float)
        if len(reported) != 20 or not np.allclose(reported, derived, rtol=0, atol=1e-10):
            raise AssertionError(f"Original emitted {key} differs from raw factor values")
    # Original 20 candidates are source complete: any field missing remains
    # a measured finding, not an excuse to substitute WorldPop.
    criterion_completeness = []
    for j, label in enumerate(FACTOR_NAMES):
        col = vals[:, j]
        valid = col[np.isfinite(col)]
        criterion_completeness.append({
            "source_field": label,
            "all_5417_nonmissing": int(len(valid)),
            "all_5417_missing": int(np.isnan(col).sum()),
            "selected_20_nonmissing": int(np.isfinite(col[candidates]).sum()),
            "selected_20_missing": int(np.isnan(col[candidates]).sum()),
            "source_min": float(np.min(valid)) if len(valid) else None,
            "source_max": float(np.max(valid)) if len(valid) else None,
            "outside_unit_interval_count": int(((valid < 0) | (valid > 1)).sum()),
        })
    ahp = main_ahp_priority(TABLE_III)
    table4 = parent_weight_sums(PRINTED_TABLE_IV)
    original_parent = parent_weight_sums(ORIGINAL_WEIGHTS)
    geom = spatial["spatial_graph"]
    return {
        "schema_version": 1,
        "scope": "read_only_N20_S4_parameter_and_AHP_provenance_no_sensitivity_sweep",
        "protocol": "docs/research_protocols/N20_S4_PARAMETER_PROVENANCE_GATES_2026_10_19.md",
        "original_source_geojson_sha256": EXPECTED_DATA_SHA,
        "archived_original_notebook_sha256": EXPECTED_ARCHIVE_SHA,
        "locally_inspected_owner_manuscript_sha256_not_ci_input": MANUSCRIPT_LOCAL_DOCX_SHA,
        "original_source_model_sha256": record["model_input_sha256"],
        "reference": {
            "N": 20,
            "K": 5,
            "original_fixed_count": 15,
            "original_feasible_subsets": 1077,
            "original_feasible_set_sha256": EXPECTED_LOCAL_SHA,
            "original_best_local_indices": record["selected_local_positions"],
            "original_energy": record["original_energy"],
        },
        "original_spatial_inputs": {
            "hull_ratio": .05,
            "fixed_spacing_buffer": 1.15,
            "original_Dmax_m_float64_hex": model["d_max_m_float64_hex"],
            "Lc_m": 7500.,
            "Lw_m": 1000.,
            "beta": 1.,
            "delta": 1.,
            "source_hull_geometry_graph_sha256": spatial["spatial_graph_sha256"],
            "source_geometry_nearest_edge_threshold_margin_m_hex":
                geom["nearest_distance_threshold_margin_m_hex"],
            "source_490_candidate_related_pair_checks": geom["tested_pairs"],
            "source_interior_candidate_related_pairs": geom["interior_pairs"],
            "original_direct_free_free_edges": geom["free_free_edges"],
            "original_direct_free_fixed_edges": geom["free_fixed_edges"],
        },
        "original_factor_data": {
            "original_eight_names": FACTOR_NAMES,
            "original_weights_float64_hex": model["factor_weights_float64_hex"],
            "original_weights_sum": float(np.sum(weights)),
            "original_weights_parent_subtotals": original_parent,
            "all_source_points": len(features),
            "all_source_features_with_any_missing": int(np.isnan(vals).any(axis=1).sum()),
            "all_source_features_with_all_eight_missing": int(np.isnan(vals).all(axis=1).sum()),
            "selected_20_with_any_missing": int(np.isnan(vals[candidates]).any(axis=1).sum()),
            "selected_20_available_weight_denominator_min": float(
                np.min(denominator[candidates])
            ),
            "selected_20_available_weight_denominator_max": float(
                np.max(denominator[candidates])
            ),
            "site_utilities_normalized_from_available_weights_not_plain_weight_sum": True,
            "criterion_completeness": criterion_completeness,
        },
        "manuscript_transcription_not_original_solver_input": {
            "table_III_four_by_four_main_pairwise": TABLE_III,
            "derived_table_III_principal_eigenvector": ahp,
            "table_IV_printed_global_eight_weights": list(PRINTED_TABLE_IV),
            "table_IV_parent_weights_by_A_B_C_D": table4,
            "manuscript_reports_lambda_max": 4.2207,
            "manuscript_reports_consistency_ratio": .0817,
            "manuscript_D2_label": "stakeholder/population exposure — WorldPop",
            "source_D2_field": FACTOR_NAMES[-1],
            "warning": (
                "Printed table weights, recalculated Table III eigenvector, and "
                "source notebook weights are distinct; original expert elicitation "
                "and D2 processing provenance not available."
            ),
        },
        "sensitivity_status": {
            "new_parameter_values_tested": [],
            "hull_ratio_range_sweep": "BLOCKED_need_verified_shoreline_and_predeclared_values",
            "Dmax_radio_range_sweep": "BLOCKED_need_measured_radio_link_budget",
            "Lc_Lw_variation": "BLOCKED_need_spatial_covariance_and_hydrodynamic_evidence",
            "AHP_expert_weight_sweep": "BLOCKED_need_original_judgments_aggregation_and_D2_identity",
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "shapely": shapely.__version__,
        },
        "limitations": [
            "No alternate weights, ratios, radio ranges, current fields or candidate pools were tested",
            "Owner DOCX manuscript table values transcribed locally; CI only checks original source data and published transcribed arithmetic",
            "Shapely/GEOS same hull definition is computational parity, not independent shoreline accuracy",
            "Original notebook model is not validated physical wireless coverage or published table replication",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    opts = parser.parse_args()
    if opts.output.exists():
        raise FileExistsError("Never overwrite existing historical provenance evidence")
    source = json.loads(opts.reference.read_text(encoding="utf-8"))
    report = analyze(source)
    opts.output.parent.mkdir(parents=True, exist_ok=True)
    opts.output.write_bytes(canonical(report))
    print("N20_S4_SOURCE_PARAMETER_PROVENANCE " + json.dumps({
        "source_weights_sum": report["original_factor_data"]["original_weights_sum"],
        "selected_20_missing_any": report["original_factor_data"]["selected_20_with_any_missing"],
        "all_source_features_missing_any": report["original_factor_data"]["all_source_features_with_any_missing"],
        "source_Dmax_hex": report["original_spatial_inputs"]["original_Dmax_m_float64_hex"],
        "original_edges": [report["original_spatial_inputs"]["original_direct_free_free_edges"],
                           report["original_spatial_inputs"]["original_direct_free_fixed_edges"]],
        "paper_printed_parent": report["manuscript_transcription_not_original_solver_input"][
            "table_IV_parent_weights_by_A_B_C_D"
        ],
        "table_III_derived_eigenvector": report["manuscript_transcription_not_original_solver_input"][
            "derived_table_III_principal_eigenvector"
        ]["principal_right_eigenvector"],
        "sweeps_run": report["sensitivity_status"]["new_parameter_values_tested"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
