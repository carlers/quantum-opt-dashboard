"""Execute and validate the curated lake N20 notebook in a clean Jupyter kernel.

This is deliberately separate from the source-hash-only legacy inventory.
It performs a bounded N20 exact reconstruction and actual SCIP solve.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "problems/water_quality/notebooks/water_quality_n20_reproducible.ipynb"
EXPECTED_SELECTED = [0, 1, 3, 6, 7]
EXPECTED_MASTER = [5253, 2394, 1557, 47, 5409]
EXPECTED_DATA_SHA = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
EXPECTED_NOTEBOOK_SHA = "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"
EXPECTED_ENERGY = -3.3012934918564643
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


def verify_result(record: dict) -> None:
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
