"""Create an original-source N20/K5 read-only independent SCIP process receipt.

Produces no application changes, no manuscript revisions, no field-science
claims, and never overwrites a prior research record. The emitted LP is solved
once by the existing prototype SCIP compiler and *again*, freshly, by a
separate Python+SCIP process reading exactly those original LP bytes.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from model import NOTEBOOK_WEIGHTS, load_data, make_instance, solve_scip
from mvp_audit import (
    EXPECTED_GEOJSON_SHA256, NOTEBOOK_N20_K5_LOCAL_INDICES,
    canonical, preview, source_sha,
)
from scip_lp_reexecution import reexecute_emitted_lp_in_child

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL_GEOJSON = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"


def run_original_n20_process_replay() -> dict:
    source_digest = source_sha(ORIGINAL_GEOJSON)
    data = load_data(ORIGINAL_GEOJSON)
    instance, substituted_fixed = make_instance(
        data, NOTEBOOK_WEIGHTS, n_free=20, budget=5,
        beta=1.0, delta=1.0,
    )
    if substituted_fixed:
        raise ValueError("Original N20 source fixed stations were substituted")
    model = preview(
        instance, dataset_sha256=source_digest,
        weights=NOTEBOOK_WEIGHTS.tolist(),
        weight_source="Notebook source original factor weights",
        time_limit_seconds=30,
        beta=1., delta=1.,
    )
    with TemporaryDirectory(prefix="n20_first_scip_") as temp:
        lp_path = Path(temp) / "original_scip_untransformed.lp"
        first_solution, original_metrics = solve_scip(
            instance, time_limit=30.0, export_lp_path=lp_path,
        )
        raw_lp = lp_path.read_bytes()
        independent = reexecute_emitted_lp_in_child(
            instance, raw_lp, first_solution, original_metrics,
        )

    selected = [i for i, flag in enumerate(first_solution) if flag]
    if selected != list(NOTEBOOK_N20_K5_LOCAL_INDICES):
        raise ValueError("Actual original local SCIP selected source sites changed")
    original_sha = sha256(raw_lp).hexdigest()
    if independent["source_original_scip_lp_sha256"] != original_sha:
        raise ValueError("Fresh independent process solved a different LP")

    return {
        "schema_version": 1,
        "scope": "original_N20_K5_one_hop_local_actual_LP_fresh_Scip_process_report",
        "dataset_sha256": source_digest,
        "dataset_matches_original_source": source_digest == EXPECTED_GEOJSON_SHA256,
        "current_original_n20_model_manifest_sha256": model["model_fingerprint_sha256"],
        "original_scip_lp_sha256": original_sha,
        "original_scip_selected_sites": selected,
        "original_upstream_scip_status": original_metrics["status"],
        "original_upstream_scip_optimal_claimed": original_metrics["optimal"],
        "original_upstream_scip_energy_float64_hex": float(
            original_metrics["energy"]
        ).hex(),
        "independent_second_process": independent,
        "previous_upstream_scip_binary_execution_log_authenticated": False,
        "report_cryptographically_signed_by_trusted_service": False,
        "global_all_original_fixed_graph_scip_proven": False,
        "paper_AHP_D2_parity_or_physical_RF_DO_validity": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError("Refuse to replace earlier observed independent SCIP evidence")
    record = run_original_n20_process_replay()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(record))
    print("N20_SCIENTIFIC_SECOND_SCIP_PROCESS " + json.dumps({
        "original_status": record["original_upstream_scip_status"],
        "second_status": record["independent_second_process"]["independent_child_status"],
        "matching_lp_sha": record["original_scip_lp_sha256"] ==
        record["independent_second_process"]["source_original_scip_lp_sha256"],
        "replayed_source_selected": record["independent_second_process"][
            "independent_child_selected_indices"
        ],
        "primal_dual_gap": record["independent_second_process"][
            "independent_lp_relative_gap"
        ],
        "upstream_scip_process_authenticated": False,
        "paper_or_field_claim": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
