"""Issue #108: read-only inventory of import edges and global import-path hazards.

AST-only: never imports project packages, executes Streamlit, or reads source GIS
datasets. An inventory is NOT proof of cross-thread/session import isolation.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (
    "prototypes",
    "problems",
    "framework/python/qopt",
    "scripts",
)
PATH_METHODS = {"insert", "append", "extend", "remove", "pop", "clear"}


def _python_files(root: Path) -> list[Path]:
    result = []
    for subtree in SCAN_ROOTS:
        base = root / subtree
        if not base.is_dir():
            raise ValueError(f"Missing audited source directory: {subtree}")
        for path in base.rglob("*.py"):
            if not any(part.startswith(".") or part == "__pycache__"
                       for part in path.relative_to(root).parts):
                result.append(path)
    return sorted(result)


def _sys_path(node: ast.AST) -> bool:
    return (isinstance(node, ast.Attribute) and node.attr == "path"
            and isinstance(node.value, ast.Name) and node.value.id == "sys")


def _import_edge(node: ast.AST, module_index: dict[str, list[str]]):
    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        target = node.module
    elif isinstance(node, ast.Import):
        # Each unqualified import is recorded independently below.
        return [(alias.name, alias.name in module_index)
                for alias in node.names if "." not in alias.name]
    else:
        return []
    return [(target, "." not in target and target in module_index)]


def inventory(root: Path = ROOT) -> dict:
    """Return a deterministic JSON-serializable review artifact; execute no modules."""
    files = _python_files(root)
    module_index = defaultdict(list)
    for path in files:
        if path.stem != "__init__":
            module_index[path.stem].append(path.relative_to(root).as_posix())
    module_index = {name: sorted(paths) for name, paths in sorted(module_index.items())}

    entries = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        parsed = ast.parse(data, filename=relative)
        imports = []
        mutations = []
        dynamic = []
        for node in ast.walk(parsed):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for target, ambiguous in _import_edge(node, module_index):
                    if ambiguous:
                        imports.append({
                            "line": node.lineno, "module": target,
                            "candidate_files": module_index[target],
                        })
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                fn = node.func
                if _sys_path(fn.value) and fn.attr in PATH_METHODS:
                    mutations.append({"line": node.lineno, "method": fn.attr})
                if (isinstance(fn.value, ast.Name) and fn.value.id == "runpy"
                        and fn.attr == "run_path"):
                    dynamic.append({"line": node.lineno, "kind": "runpy.run_path"})
                if (isinstance(fn.value, ast.Name)
                        and fn.value.id == "importlib"
                        and fn.attr == "import_module"):
                    dynamic.append({"line": node.lineno, "kind": "importlib.import_module"})
            if (isinstance(node, (ast.Assign, ast.AugAssign))
                    and any(_sys_path(x) for x in (
                        node.targets if isinstance(node, ast.Assign)
                        else [node.target]))):
                mutations.append({"line": node.lineno, "method": "assignment"})
        if imports or mutations or dynamic:
            entries.append({
                "file": relative, "sha256": sha256(data).hexdigest(),
                "unqualified_local_name_edges": sorted(imports, key=lambda x: (x["line"], x["module"])),
                "sys_path_mutations": sorted(mutations, key=lambda x: x["line"]),
                "dynamic_execution": sorted(dynamic, key=lambda x: (x["line"], x["kind"])),
            })
    return {
        "schema_version": 1,
        "kind": "READ_ONLY_IMPORT_SURFACE_AUDIT_NOT_ISOLATION_ATTESTATION",
        "scan_roots": list(SCAN_ROOTS),
        "python_source_file_count": len(files),
        "files_with_observed_edges_or_hazards": entries,
        "counts": {
            "unqualified_local_name_edges": sum(
                len(x["unqualified_local_name_edges"]) for x in entries),
            "sys_path_mutations": sum(len(x["sys_path_mutations"]) for x in entries),
            "dynamic_execution": sum(len(x["dynamic_execution"]) for x in entries),
        },
        "limitations": [
            "AST does not resolve all conditional, string-based, plugin or lazy imports.",
            "A local filename is a candidate, not proof of runtime module origin.",
            "Import paths and sys.modules are process-global; no concurrent session isolation is certified.",
            "Standalone scripts, scientific numerical identity and live browser behavior are not exercised.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
