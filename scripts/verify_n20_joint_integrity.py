"""Issue #6: compare immutable N20 geometry across six independent source kernels.

Original coefficient float.hex hashes may vary at ~1 ULP across runtime
environments. That is NOT equivalent to a changed site/geometry/feasible set.
This validator requires source and spatial science invariants to be identical
without incorrectly imposing bit-exact equality on arithmetic coefficients.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ORIGINAL_GEOJSON_SHA = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
ORIGINAL_NOTEBOOK_SHA = "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"
SOURCE_GEOJSON_FEASIBLE_SHA = "2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a"
EXPECTED_SELECTION = [0, 1, 3, 6, 7]
EXPECTED_FEASIBLE = 1077
EXPECTED_ENERGY = -3.3012934918564643
EXPECTED_NAMES = {f"replicate-r{h}-{p}" for h in (1, 2, 3) for p in ("a", "b")}


def canonical(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def validate(record: dict) -> str:
    if record.get("schema_version") != 2 or record.get("status") != (
        "notebook_derived_N20_replay_not_paper_parity"
    ):
        raise ValueError("Not an original source-derived N20/K5 notebook output")
    if (record.get("dataset_sha256") != ORIGINAL_GEOJSON_SHA
            or record.get("archived_notebook_sha256") != ORIGINAL_NOTEBOOK_SHA):
        raise ValueError("Source historical data/notebook SHA changed")
    if (record.get("candidate_count") != 20
            or record.get("new_station_budget") != 5
            or record.get("marked_existing_stations") != 15
            or record.get("enumerated_combinations") != 15504
            or record.get("feasible_combinations") != EXPECTED_FEASIBLE
            or record.get("feasible_site_sets_sha256") != SOURCE_GEOJSON_FEASIBLE_SHA):
        raise ValueError("Original complete source feasible region changed")
    if record.get("selected_local_positions") != EXPECTED_SELECTION:
        raise ValueError("Original source optimal site selection changed")
    if record.get("scip_status") != "optimal":
        raise ValueError("Independent source SCIP no longer optimal")
    if record.get("local_one_hop_not_global_connectivity") is not True:
        raise ValueError("Original graph must retain local one-hop semantics")
    energy = record.get("original_energy")
    if (not isinstance(energy, (int, float)) or not math.isfinite(energy)
            or abs(energy - EXPECTED_ENERGY) >= 1e-7):
        raise ValueError("Original source-derived N20 objective changed")
    model = record["model_input"]
    if hashlib.sha256(canonical(model)).hexdigest() != record.get("model_input_sha256"):
        raise ValueError("Exact source model manifest checksum changed without payload")
    if (model.get("dataset_sha256") != ORIGINAL_GEOJSON_SHA
            or model.get("archived_notebook_sha256") != ORIGINAL_NOTEBOOK_SHA):
        raise ValueError("Source model used different archived inputs")
    if (len(model.get("candidate_master_feature_positions", [])) != 20
            or len(model.get("fixed_master_feature_positions", [])) != 15
            or len(model.get("fixed_neighbor_flags", [])) != 20
            or len(model.get("free_neighbor_indices", [])) != 20):
        raise ValueError("Original source adjacency/cohort dimensions changed")
    if len(model.get("free_fixed_pair_trace", [])) != 300:
        raise ValueError("Original source 300 free/fixed precision trace was dropped")
    return record["model_input_sha256"]


def geometry_contract(record: dict) -> dict:
    model = record["model_input"]
    return {
        "candidate_master_feature_positions": model["candidate_master_feature_positions"],
        "fixed_master_feature_positions": model["fixed_master_feature_positions"],
        "fixed_neighbor_flags": model["fixed_neighbor_flags"],
        "free_neighbor_indices": model["free_neighbor_indices"],
    }


def compare(records: list[tuple[str, dict]]) -> dict:
    if len(records) != len(EXPECTED_NAMES):
        raise ValueError("Exactly six original source independent process results required")
    names = [name for name, _ in records]
    if len(set(names)) != len(names) or set(names) != EXPECTED_NAMES:
        raise ValueError("Missing, duplicate or unexpected source replica ID")
    model_shas: set[str] = set()
    first_geometry = None
    for name, record in sorted(records):
        model_shas.add(validate(record))
        current = geometry_contract(record)
        if first_geometry is None:
            first_geometry = current
        elif current != first_geometry:
            raise ValueError(
                f"{name}: source one-hop graph differs between independent kernels"
            )
    fingerprint = hashlib.sha256(canonical(first_geometry)).hexdigest()
    return {
        "schema_version": 1,
        "study": "combined_N20_source_precision_spatial_crosshost_invariants",
        "independent_processes": len(records),
        "original_source_geojson_sha256": ORIGINAL_GEOJSON_SHA,
        "feasible_combinations": EXPECTED_FEASIBLE,
        "feasible_site_sets_sha256": SOURCE_GEOJSON_FEASIBLE_SHA,
        "identical_original_one_hop_graph_across_hosts": True,
        "one_hop_graph_sha256": fingerprint,
        "source_original_exact_coefficient_sha_modes": sorted(model_shas),
        "num_source_numeric_modes_in_observed_sample": len(model_shas),
        "interpretation": (
            "Exact numerical input coefficients may exhibit 1-ULP runtime "
            "differences: require original archived sources, chosen sites, exact "
            "adjacency and full feasible-region membership; do not confuse this "
            "with manuscript parity or universal float64 bitwise reproducibility."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    source_files = sorted(args.inputs_root.rglob("replicate-r*-*.json"))
    if len(source_files) != 6:
        raise ValueError(f"Need six complete source kernel records, got {len(source_files)}")
    rows = [(f.stem, json.loads(f.read_text(encoding="utf-8"))) for f in source_files]
    report = compare(rows)
    if args.report.exists():
        raise FileExistsError("Refuse to replace original combined source audit")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(canonical(report))
    print("N20_JOINT_SPATIAL_NUMERIC_INVARIANTS " + json.dumps({
        "independent_processes": report["independent_processes"],
        "numeric_modes": report["num_source_numeric_modes_in_observed_sample"],
        "feasible_combinations": report["feasible_combinations"],
        "spatial_hash": report["one_hop_graph_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
