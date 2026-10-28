"""Read-only provenance audit of the archived water-quality research notebook.

The original paper, GeoJSON, numerical model, and notebook are not edited.
A *mechanical* working copy is optional and does NOT claim numerical parity.
No notebook cell is executed by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_RELATIVE = "problems/water_quality/notebooks/experiment9 grid search copy.ipynb"
NOTEBOOK = ROOT / NOTEBOOK_RELATIVE
ORIGINAL_SHA256 = "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"
ORIGINAL_CELLS = 25

# Indices refer to the immutable 25-cell notebook, NOT the derived working copy.
# The first three pairs look repetitive but contain substantive differences.
REPEATED_SECTIONS = {
    "CELL 3 nested resolution scaling": (4, 5),
    "CELL 5 SCIP solver": (7, 8),
    "CELL 5b SCIP deployment plots": (9, 10),
    "CELL 7 penalty grid search": (13, 14),
    "CELL 10 comparison table": (21, 22),
}
IDENTICAL_SECOND_CELLS = (14, 22)


def cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", [])
    if isinstance(source, str):
        return source
    if isinstance(source, list) and all(isinstance(line, str) for line in source):
        return "".join(source)
    raise ValueError("Invalid notebook cell source")


def load_archived_notebook(path: Path = NOTEBOOK) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ORIGINAL_SHA256:
        raise ValueError(
            "Archived notebook bytes differ from the declared immutable SHA-256: " + digest
        )
    notebook = json.loads(raw)
    cells = notebook.get("cells")
    if notebook.get("nbformat") != 4 or not isinstance(cells, list):
        raise ValueError("Expected a Jupyter nbformat=4 notebook")
    if len(cells) != ORIGINAL_CELLS:
        raise ValueError(f"Expected {ORIGINAL_CELLS} archived cells; received {len(cells)}")
    if any(cell.get("cell_type") != "code" for cell in cells):
        raise ValueError("The pinned source inventory expects 25 code cells")
    if any(cell.get("outputs") or cell.get("execution_count") is not None for cell in cells):
        raise ValueError("Archived source now has execution records; do not silently trust it")
    return notebook, digest


def inspect_notebook(notebook: dict[str, Any], digest: str) -> dict[str, Any]:
    cells = notebook["cells"]
    groups: list[dict[str, Any]] = []
    for name, (first, second) in REPEATED_SECTIONS.items():
        a, b = cell_source(cells[first]), cell_source(cells[second])
        lines_a, lines_b = a.splitlines(), b.splitlines()
        differing_line = next(
            (i + 1 for i in range(max(len(lines_a), len(lines_b)))
             if i >= len(lines_a) or i >= len(lines_b) or lines_a[i] != lines_b[i]),
            None,
        )
        identical = a == b
        if identical != (second in IDENTICAL_SECOND_CELLS):
            raise ValueError(f"Repeated source section changed unexpectedly: {name}")
        groups.append({
            "section": name,
            "cell_indices": [first, second],
            "cell_ids": [cells[first].get("id"), cells[second].get("id")],
            "source_identical": identical,
            "first_differing_line": differing_line,
        })
    return {
        "schema_version": 1,
        "original_path": NOTEBOOK_RELATIVE,
        "original_sha256": digest,
        "original_cells": len(cells),
        "code_cells": sum(cell.get("cell_type") == "code" for cell in cells),
        "recorded_executions": sum(
            cell.get("execution_count") is not None for cell in cells
        ),
        "cells_with_outputs": sum(bool(cell.get("outputs")) for cell in cells),
        "repeated_sections": groups,
        "mechanically_excludable_second_cell_indices": list(IDENTICAL_SECOND_CELLS),
        "limits": [
            "Static structural inventory; notebook cells are not executed",
            "Duplicate execution may have side effects; parity is not established",
            "Similar but different variants cannot be silently collapsed",
        ],
    }


def write_mechanical_copy(notebook: dict[str, Any], destination: Path) -> None:
    if destination.resolve() == NOTEBOOK.resolve():
        raise ValueError("Refusing to overwrite the archived notebook")
    copy = deepcopy(notebook)
    for index in sorted(IDENTICAL_SECOND_CELLS, reverse=True):
        copy["cells"].pop(index)
    # Verify remaining source cell content and order, rather than guessing equivalence.
    expected = [
        cell_source(cell) for i, cell in enumerate(notebook["cells"])
        if i not in IDENTICAL_SECOND_CELLS
    ]
    if [cell_source(cell) for cell in copy["cells"]] != expected:
        raise AssertionError("A retained cell changed during mechanical derivation")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(copy, stream, ensure_ascii=False, indent=1)
        stream.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="Write JSON report instead of stdout")
    parser.add_argument(
        "--working-copy", type=Path,
        help="Optional new notebook: remove only identical repeated source cells; never execute",
    )
    args = parser.parse_args()
    source, digest = load_archived_notebook()
    report = inspect_notebook(source, digest)
    if args.working_copy:
        write_mechanical_copy(source, args.working_copy)
        report["working_copy_excludes"] = list(IDENTICAL_SECOND_CELLS)
        report["working_copy_execution_equivalence_verified"] = False
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
