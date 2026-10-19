"""Inspect actual pinned Streamlit AppTest-produced local/global evidence ZIPs.

A test harness is NOT an authenticated live user's session. No UX source files
are edited or merged; this imports only the separately checked-out app at its
fixed reviewed git SHA and treats its own exported ZIP as untrusted evidence.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from io import BytesIO, StringIO
import json
import math
from pathlib import Path
from zipfile import ZipFile

from streamlit.testing.v1 import AppTest

EXPECTED_SOURCE_SHA = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
EXPECTED_GLOBAL_FEASIBLE_SHA = "3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40"
UX_COMMIT = "8752d17372d9d4dd544acbbfd686b4bb45e33f40"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def inspect_ui_zip(session_result: dict, mode: str) -> dict:
    """Validate current displayed session fingerprint and EACH ZIP content SHA."""
    _require(mode in ("source_local", "all_stations_connected"), "Unsupported UI mode")
    _require(isinstance(session_result, dict)
             and isinstance(session_result.get("fingerprint"), str)
             and isinstance(session_result.get("zip"), bytes),
             "Active UI result and evidence bytes required")
    chosen = session_result.get("chosen")
    _require(isinstance(chosen, list) and len(chosen) == 20
             and all(type(v) is int and v in (0, 1) for v in chosen)
             and sum(chosen) == 5,
             "Displayed solution must contain exactly five selected original source sites")
    _require(session_result.get("metrics", {}).get("optimal") is True,
             "UI cannot export a claimed optimal result without solver proof")

    archive_sha = sha256(session_result["zip"]).hexdigest()
    with ZipFile(BytesIO(session_result["zip"])) as archive:
        members = archive.namelist()
        _require(len(set(members)) == len(members), "Duplicate ZIP file names")
        expected = {"model.json", "result.json", "selected_sites.csv", "SHA256SUMS.json"}
        _require(set(members) == expected | (
            {"actual_scip_model.lp"} if mode == "source_local"
            else {"wireless_graph.json"}
        ), "Unexpected, missing or invented global SCIP LP/evidence ZIP files")
        manifest = json.loads(archive.read("SHA256SUMS.json"))
        checksums = manifest["files_sha256"]
        _require(set(checksums) == set(members) - {"SHA256SUMS.json"},
                 "Unexpected or missing evidence content checksum")
        for name in checksums:
            _require(sha256(archive.read(name)).hexdigest() == checksums[name],
                     "ZIP content/checksum mismatch: " + name)
        model = json.loads(archive.read("model.json"))
        result = json.loads(archive.read("result.json"))
        csv_source = archive.read("selected_sites.csv").decode("utf-8")
        rows = list(csv.DictReader(StringIO(csv_source)))
        if mode == "source_local":
            _require(bool(archive.read("actual_scip_model.lp").strip()),
                     "Original local SCIP LP is missing or empty")
        else:
            graph = json.loads(archive.read("wireless_graph.json"))
            _require(graph == model["wireless_graph"],
                     "UI global model and exported graph differ")

    active_fingerprint = model["model_fingerprint_sha256"]
    model_without_hash = dict(model)
    model_without_hash.pop("model_fingerprint_sha256")
    _require(sha256(canonical(model_without_hash)).hexdigest() == active_fingerprint
             and active_fingerprint == session_result["fingerprint"]
             and result["model_fingerprint_sha256"] == active_fingerprint,
             "Displayed current model and UX ZIP fingerprint do not match")
    _require(model["dataset_sha256"] == EXPECTED_SOURCE_SHA,
             "Actual UI source bytes do not match original source")
    _require(model["settings"]["connectivity_mode"] == mode,
             "Current UI mode and compiled model disagree")
    _require(model["mapping"]["fixed_master_feature_positions"]
             and len(model["mapping"]["fixed_master_feature_positions"]) == 15
             and len(model["mapping"]["free_master_feature_positions"]) == 20,
             "Original fixed/new ordered station identity incomplete")
    _require([int(r["local_position"]) for r in rows]
             == [i for i, flag in enumerate(chosen) if flag],
             "Selected sites in CSV do not match displayed binary solution")
    _require([int(r["master_feature_position"]) for r in rows] ==
             [model["mapping"]["free_master_feature_positions"][i]
              for i, flag in enumerate(chosen) if flag],
             "Selected source site master IDs in CSV differ from active result")
    _require(session_result["independent"]["selected_local_positions"]
             == [i for i, flag in enumerate(chosen) if flag],
             "UI current independent result does not agree with displayed selected sites")
    if mode == "source_local":
        _require(result["scip_status"] == "optimal"
                 and result["scip_optimal_proven"] is True
                 and model["constraints"]["global_path_connectivity"] is False
                 and "actual_scip_model.lp" in checksums,
                 "Local UI is not an actual original SCIP mathematically optimal export")
    else:
        search = result["search"]
        _require(result["connectivity_mode"] == mode
                 and result["optimal_proven"] is True
                 and search["status"] == "optimal_exhaustive"
                 and search["solver"] == "exact_exhaustive_enumeration"
                 and search["feasible_combinations"] == 860
                 and search["combinations_examined"] == 15504
                 and search["selected_local_positions"]
                 == [i for i, flag in enumerate(chosen) if flag],
                 "Global UI ZIP makes unproved or misbound exact result claim")
        _require(
            model["constraints"]["global_path_connectivity"] is not False
            and graph["free_count"] == 20 and graph["fixed_count"] == 15,
            "Missing required full-global 15 mandatory original fixed stations"
        )

    return {
        "mode": mode,
        "source_dataset_sha256": model["dataset_sha256"],
        "active_model_fingerprint_sha256": active_fingerprint,
        "zip_sha256": archive_sha,
        "selected_local_positions": [i for i, flag in enumerate(chosen) if flag],
        "selected_master_feature_positions": [
            model["mapping"]["free_master_feature_positions"][i]
            for i, flag in enumerate(chosen) if flag
        ],
        "all_15_original_fixed_master_positions": model["mapping"]["fixed_master_feature_positions"],
        "original_model_linear_float64_hex": model["objective"]["linear_float64_hex"],
        "original_model_quadratic_ij_float64_hex": [
            [row["i"], row["j"], row["q_float64_hex"]]
            for row in model["objective"]["quadratic_terms"]
        ],
        "source_dmax_float64_hex": model["d_max_m_float64_hex"],
        "global_graph_edges": graph["undirected_edges"] if mode != "source_local" else None,
        "global_graph_fingerprint": graph["fingerprint_sha256"] if mode != "source_local" else None,
        "reported_backend_status": session_result["metrics"]["status"],
        "scip_lp_in_zip": mode == "source_local",
        "all_evidence_file_checksums_verified": True,
        "not_independently_authenticated_live_user_session": True,
        "not_field_or_manuscript_validation": True,
    }


def record_ux_apptest(app: Path, source: dict, science: dict, ux: dict) -> dict:
    """Execute both actual app modes; enforce state invalidation before global."""
    if not app.is_file():
        raise ValueError("Pinned UX Streamlit app file missing")
    at = AppTest.from_file(str(app), default_timeout=120).run()
    if at.exception:
        raise AssertionError(f"Pinned UI initial render failed: {at.exception}")
    _require(next(x for x in at.radio if x.label == "Wireless connectivity").value
             == "Local clusters · original", "Source local must be UX default")
    at.button(key="mvp_run").click().run()
    if at.exception:
        raise AssertionError(f"Original local SCIP AppTest failed: {at.exception}")
    local = inspect_ui_zip(dict(at.session_state["mvp_result"]), "source_local")

    at.radio(key=next(x.key for x in at.radio if x.label == "Wireless connectivity")).set_value(
        "Global connectivity · all stations"
    ).run()
    if at.exception:
        raise AssertionError(f"Global-mode switch failed: {at.exception}")
    _require("mvp_result" not in at.session_state,
             "Old local result/ZIP survived a change in active graph topology")
    at.button(key="mvp_run").click().run()
    if at.exception:
        raise AssertionError(f"Global exact-search Streamlit AppTest failed: {at.exception}")
    global_session = inspect_ui_zip(dict(at.session_state["mvp_result"]),
                                    "all_stations_connected")

    _require(local["active_model_fingerprint_sha256"]
             != global_session["active_model_fingerprint_sha256"],
             "Original local and exploratory global same fingerprint")
    _require(local["selected_local_positions"] == source["selected_local_positions"]
             and global_session["selected_local_positions"]
             == science["global_exact_union_find_oracle"]["independently_optimal_indices"],
             "AppTest actual UI selected sites differ from certified source/global solution")
    _require(global_session["global_graph_edges"]
             == science["full_global_graph"]["undirected_edges"]
             == ux["modeled_geometry_graph"]["undirected_edges"],
             "Actual UI zipped source model graph differs from independent science/UX exporter")
    _require(global_session["global_graph_fingerprint"]
             == ux["modeled_geometry_graph"]["fingerprint_sha256"],
             "Actual UI graph fingerprint does not match UX's separately run backend graph")
    _require(global_session["source_dmax_float64_hex"]
             == ux["source_dmax_float64_hex"],
             "Actual UI range/Dmax differs from UX backend model")
    _require(global_session["all_15_original_fixed_master_positions"]
             == ux["source_fixed_master_feature_positions"],
             "Actual UI does not preserve all original fixed site identities")
    _require(
        global_session["original_model_linear_float64_hex"]
        == ux["original_objective_linear_float64_hex"]
        and global_session["original_model_quadratic_ij_float64_hex"]
        == ux["original_objective_quadratic_ij_float64_hex"],
        "UX AppTest current compiled score differs from independently executed UX backend"
    )
    return {
        "schema_version": 1,
        "scope": "actual_ux_Streamlit_AppTest_local_and_global_read_only_snapshot",
        "ux_pinned_commit_sha": UX_COMMIT,
        "mode_change_actually_invalidated_previous_result": True,
        "local_actual_scip_archive": local,
        "global_actual_exact_enumeration_archive": global_session,
        "full_current_app_and_exporter_edges_cohere": True,
        "global_current_app_and_exporter_coefficients_exactly_match": True,
        "zip_checksums_fully_reverified": True,
        "simulated_AppTest_not_signed_real_user_session": True,
        "not_proof_of_physical_water_quality_or_RFI": True,
        "not_manuscript_AHP_D2_parity": True,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app", type=Path, required=True)
    p.add_argument("--source-reference", type=Path, required=True)
    p.add_argument("--science-global", type=Path, required=True)
    p.add_argument("--ux-global", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError("Refuse to overwrite earlier UX AppTest snapshot")
    records = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in (args.source_reference, args.science_global, args.ux_global)
    ]
    result = record_ux_apptest(args.app, *records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(result))
    print("N20_CURRENT_UX_APPTEST_EVIDENCE " + json.dumps({
        "local_scip_lp": result["local_actual_scip_archive"]["scip_lp_in_zip"],
        "global_no_fake_lp": not result["global_actual_exact_enumeration_archive"]["scip_lp_in_zip"],
        "ui_exported_edge_list_match": result["full_current_app_and_exporter_edges_cohere"],
        "source_selected_sites": result["local_actual_scip_archive"]["selected_local_positions"],
        "global_selected_sites": result["global_actual_exact_enumeration_archive"]["selected_local_positions"],
        "user_live_session_authenticated": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
