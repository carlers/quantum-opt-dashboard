"""Execute and validate the curated lake N20 notebook in a clean Jupyter kernel.

This is deliberately separate from the source-hash-only legacy inventory.
It performs a bounded N20 exact reconstruction and actual SCIP solve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from itertools import combinations
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "problems/water_quality/notebooks/water_quality_n20_reproducible.ipynb"
EXPECTED_SELECTED = [0, 1, 3, 6, 7]
EXPECTED_FREE_MASTER = [
    5253, 2394, 1894, 1557, 3225, 4623, 47, 5409, 3922, 2408,
    2694, 4136, 2567, 1164, 4973, 4537, 2726, 968, 16, 1762,
]
EXPECTED_FIXED_MASTER = [
    417, 454, 725, 1055, 1076, 1709, 2771, 3402, 3520, 3529,
    3732, 3886, 4613, 4868, 5038,
]
EXPECTED_MASTER = [5253, 2394, 1557, 47, 5409]
EXPECTED_DATA_SHA = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
EXPECTED_NOTEBOOK_SHA = "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"
EXPECTED_ENERGY = -3.3012934918564643
EXPECTED_FEASIBLE = 1077  # Historical source-derived x-only exhaustive canary
OUTPUT_MARKER = "N20_CLEAN_RESULT "


def read_unexecuted(path: Path = NOTEBOOK):
    original = nbformat.read(path, as_version=4)
    nbformat.validate(original)
    if len(original.cells) != 23:
        raise ValueError("Expected a compact notebook with 11 code and 12 Markdown cells")
    if sum(cell.cell_type == "code" for cell in original.cells) != 11:
        raise ValueError("Unexpected cleaned notebook code cell count")
    if sum(cell.cell_type == "markdown" for cell in original.cells) != 12:
        raise ValueError("Unexpected cleaned notebook documentation count")
    if any(cell.get("outputs") or cell.get("execution_count") is not None
           for cell in original.cells if cell.cell_type == "code"):
        raise ValueError("Cleaned notebook must be committed with no saved execution outputs")
    return original


def verify_exact_model(record: dict) -> None:
    """Audit source-derived N20 coefficients, not only selected-score canaries."""
    model = record["model_input"]
    canonical = (json.dumps(model, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    if digest != record["model_input_sha256"]:
        raise AssertionError("Exact numerical model SHA-256 does not match model payload")
    if record["model_input_hash_scope"] != (
        "IEEE754 exact model; compare tolerance-based parity separately"
    ):
        raise AssertionError("Numerical digest must retain precision warning")
    if model["model_family"] != "notebook_derived_laguna_N20_local_one_hop":
        raise AssertionError("Expected the notebook-derived one-hop model")
    if model["dataset_sha256"] != EXPECTED_DATA_SHA:
        raise AssertionError("Model has unexpected source data SHA")
    if model["archived_notebook_sha256"] != EXPECTED_NOTEBOOK_SHA:
        raise AssertionError("Model has unexpected original notebook SHA")
    if model["candidate_master_feature_positions"] != EXPECTED_FREE_MASTER:
        raise AssertionError("Candidate cohort or ordering differs from the N20 canary")
    if model["fixed_master_feature_positions"] != EXPECTED_FIXED_MASTER:
        raise AssertionError("Existing station cohort differs from the source fixture")
    if model["budget_exact"] != 5:
        raise AssertionError("The original N20 reference budget changed")
    linear = [float.fromhex(s) for s in model["linear_float64_hex"]]
    edges = [(int(i), int(j), float.fromhex(q))
             for i, j, q in model["quadratic_ij_float64_hex"]]
    fixed = model["fixed_neighbor_flags"]
    neighbors = model["free_neighbor_indices"]
    coordinates = model["site_coords_epsg32651_float64_hex"]
    weights = [float.fromhex(s) for s in model["factor_weights_float64_hex"]]
    if len(linear) != 20 or len(edges) != 12 or len(neighbors) != 20 or len(fixed) != 20:
        raise AssertionError("N20 objective or one-hop model shape changed")
    if len(coordinates) != 35 or any(len(row) != 2 for row in coordinates):
        raise AssertionError("Expected 20 free and 15 fixed projected coordinates")
    if len(weights) != 8 or not all(w >= 0 and math.isfinite(w) for w in weights):
        raise AssertionError("Invalid environmental factor weights")
    if not all(math.isfinite(a) for a in linear):
        raise AssertionError("Nonfinite original linear coefficient")
    if not all(0 <= i < j < 20 and q >= 0 and math.isfinite(q)
               for i, j, q in edges):
        raise AssertionError("Invalid binary quadratic interaction term")
    if not all(value in (0, 1) for value in fixed):
        raise AssertionError("Invalid fixed-station adjacency flag")
    if any(j == i or j < 0 or j >= 20 or i not in neighbors[j]
           for i, members in enumerate(neighbors) for j in members):
        raise AssertionError("One-hop free adjacency is not symmetric")
    if not all(math.isfinite(float.fromhex(s)) for row in coordinates for s in row):
        raise AssertionError("Nonfinite projected candidate coordinate")
    selected_raw = record["selected_local_positions"]
    selected = set(selected_raw)
    if (len(selected_raw) != 5 or len(selected) != 5
            or any(not isinstance(i, int) or not 0 <= i < 20 for i in selected_raw)):
        raise AssertionError("Selected site indices must be five distinct local N20 positions")
    if any(not fixed[i] and not selected.intersection(neighbors[i]) for i in selected):
        raise AssertionError("Selected stations violate the reported one-hop rules")
    reconstructed_energy = sum(linear[i] for i in selected) + sum(
        q for i, j, q in edges if i in selected and j in selected
    )
    if abs(reconstructed_energy - record["original_energy"]) >= 1e-7:
        raise AssertionError("Decoded complete coefficient model differs from claimed score")


def feasible_space_certificate(model: dict) -> tuple[int, str]:
    """Independently enumerate reported one-hop adjacency, not notebook outputs."""
    fixed = model["fixed_neighbor_flags"]
    adjacent = [set(group) for group in model["free_neighbor_indices"]]
    digest = hashlib.sha256()
    feasible_count = 0
    for subset in combinations(range(20), 5):
        chosen = set(subset)
        if all(fixed[i] or chosen.intersection(adjacent[i]) for i in subset):
            feasible_count += 1
            digest.update((",".join(map(str, subset)) + "\n").encode("ascii"))
    return feasible_count, digest.hexdigest()


def verify_feasible_space(record: dict) -> None:
    actual_count, actual_sha = feasible_space_certificate(record["model_input"])
    if record.get("feasible_combinations") != actual_count:
        raise AssertionError("Feasible K5 subset count differs from independent one-hop audit")
    if record.get("feasible_site_sets_sha256") != actual_sha:
        raise AssertionError("Feasible K5 subset SHA-256 differs from independent adjacency audit")


def verify_result(record: dict) -> None:
    if record["schema_version"] != 2:
        raise AssertionError("N20 report schema has changed")
    verify_exact_model(record)
    verify_feasible_space(record)
    if record["feasible_combinations"] != EXPECTED_FEASIBLE:
        raise AssertionError("Source-derived N20 feasible-set size differs from reviewed 1077")
    if record["dataset_sha256"] != EXPECTED_DATA_SHA:
        raise AssertionError("The source GeoJSON digest does not match the pinned baseline")
    if record["archived_notebook_sha256"] != EXPECTED_NOTEBOOK_SHA:
        raise AssertionError("The source notebook digest does not match the pinned baseline")
    if record["scip_status"] != "optimal":
        raise AssertionError("The source-derived SCIP problem was not certified optimal")
    if record["selected_local_positions"] != EXPECTED_SELECTED:
        raise AssertionError("The notebook changed the original N20 local site selection")
    if record["selected_master_feature_positions"] != EXPECTED_MASTER:
        raise AssertionError("The notebook changed the original GeoJSON feature positions")
    if record["candidate_count"] != 20 or record["new_station_budget"] != 5:
        raise AssertionError("Unexpected N or exact budget")
    if record["marked_existing_stations"] != 15 or record["enumerated_combinations"] != 15504:
        raise AssertionError("Missing fixed-station or exhaustive-enumeration evidence")
    if record["local_one_hop_not_global_connectivity"] is not True:
        raise AssertionError("Local adjacency must not be described as global connectivity")
    for field in ("original_energy", "enumeration_energy"):
        if abs(float(record[field]) - EXPECTED_ENERGY) >= 1e-7:
            raise AssertionError(f"The source-derived {field} changed: {record[field]}")
    if abs(record["original_energy"] - record["enumeration_energy"]) >= 1e-7:
        raise AssertionError("SCIP and independent enumeration disagree")
    if record["status"] != "notebook_derived_N20_replay_not_paper_parity":
        raise AssertionError("The result must distinguish source parity from published-paper parity")


def execute_notebook():
    notebook = read_unexecuted()
    client = NotebookClient(
        notebook, timeout=180, kernel_name="python3", allow_errors=False,
        resources={"metadata": {"path": str(ROOT)}},
    )
    executed = client.execute()
    found = []
    for cell in executed.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") == "stream":
                value = output.get("text", "")
                for line in value.splitlines():
                    if line.startswith(OUTPUT_MARKER):
                        found.append(json.loads(line[len(OUTPUT_MARKER):]))
    if len(found) != 1:
        raise AssertionError(f"Expected exactly one machine-readable result, got {len(found)}")
    verify_result(found[0])
    return found[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, help="Output validated result JSON")
    args = parser.parse_args()
    record = execute_notebook()
    output = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        with args.result.open("x", encoding="utf-8") as stream:
            stream.write(output)
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
