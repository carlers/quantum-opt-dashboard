"""Read-only AST extraction of historical notebook Cell 2 factor metadata.

Does not execute the original notebook or import NumPy. The archived notebook
bytes are independently pinned by the source-custody gate.
"""
from __future__ import annotations

import ast
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path

from scripts.verify_research_sources import ANCHORS, NOTEBOOK, ROOT

SOURCE_CELL_INDEX = 3  # zero-based notebook JSON index for historical CELL 2
MAX_CELL_CHARS = 25_000


class HistoricalFactorError(ValueError):
    """Unknown or changed original source structure; no results are returned."""


def _literal_decimal(expr: ast.expr, source: str) -> Decimal:
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, (ast.UAdd, ast.USub)):
        value = _literal_decimal(expr.operand, source)
        return -value if isinstance(expr.op, ast.USub) else value
    if not isinstance(expr, ast.Constant) or type(expr.value) not in (int, float):
        raise HistoricalFactorError("Historical factor weight must be a numeric literal")
    raw = ast.get_source_segment(source, expr)
    if not isinstance(raw, str):
        raise HistoricalFactorError("Historical numeric token unavailable")
    try:
        value = Decimal(raw.replace("_", ""))
    except InvalidOperation as exc:
        raise HistoricalFactorError("Invalid historical numeric token") from exc
    if not value.is_finite() or value < 0:
        raise HistoricalFactorError("Historical factor weights must be finite and nonnegative")
    return value


def extract_from_cell(source: str) -> tuple[tuple[str, ...], tuple[Decimal, ...]]:
    """Parse only top-level literal FACTOR_NAMES and WEIGHTS=np.array([...])."""
    if not isinstance(source, str) or not 0 < len(source) <= MAX_CELL_CHARS:
        raise HistoricalFactorError("Expected bounded historical CELL 2 Python source")
    try:
        syntax = ast.parse(source)
    except SyntaxError as exc:
        raise HistoricalFactorError("Historical CELL 2 is not parseable Python") from exc
    assignments = {}
    for statement in syntax.body:
        if not isinstance(statement, ast.Assign):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id in ("WEIGHTS", "FACTOR_NAMES"):
                if target.id in assignments:
                    raise HistoricalFactorError("Ambiguous repeated factor input assignment")
                assignments[target.id] = statement.value
    if set(assignments) != {"WEIGHTS", "FACTOR_NAMES"}:
        raise HistoricalFactorError("Historical factor weights or labels missing")
    weights_expr = assignments["WEIGHTS"]
    if (not isinstance(weights_expr, ast.Call)
            or not isinstance(weights_expr.func, ast.Attribute)
            or not isinstance(weights_expr.func.value, ast.Name)
            or weights_expr.func.value.id != "np"
            or weights_expr.func.attr != "array"
            or len(weights_expr.args) != 1
            or len(weights_expr.keywords) != 1
            or weights_expr.keywords[0].arg != "dtype"
            or not isinstance(weights_expr.keywords[0].value, ast.Attribute)
            or not isinstance(weights_expr.keywords[0].value.value, ast.Name)
            or weights_expr.keywords[0].value.value.id != "np"
            or weights_expr.keywords[0].value.attr != "float64"):
        raise HistoricalFactorError("Expected historical np.array([...], dtype=np.float64)")
    numeric = weights_expr.args[0]
    if not isinstance(numeric, (ast.List, ast.Tuple)) or len(numeric.elts) != 8:
        raise HistoricalFactorError("Historical study must use exactly eight factor weights")
    weights = tuple(_literal_decimal(node, source) for node in numeric.elts)
    factor_expr = assignments["FACTOR_NAMES"]
    if not isinstance(factor_expr, (ast.List, ast.Tuple)):
        raise HistoricalFactorError("Historical factor names must be a literal list")
    if not all(isinstance(n, ast.Constant) and isinstance(n.value, str)
               for n in factor_expr.elts):
        raise HistoricalFactorError("Factor names are not static string literals")
    names = tuple(n.value for n in factor_expr.elts)
    if len(names) != 8 or len(set(names)) != 8:
        raise HistoricalFactorError("Historical factor names are incomplete or repeated")
    if names[-1] != "d2_road_proximity":
        raise HistoricalFactorError("Historical D2 factor is not road proximity")
    if not sum(weights):
        raise HistoricalFactorError("Historical factor weights sum to zero")
    return names, weights


def extract_original_weights(notebook_path: Path | None = None):
    """Read immutable original notebook, verify its bytes, parse without execution."""
    path = ROOT / NOTEBOOK if notebook_path is None else Path(notebook_path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 500_000:
        raise HistoricalFactorError("Original notebook not a bounded regular file")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != ANCHORS[NOTEBOOK]:
        raise HistoricalFactorError("Original notebook bytes differ from frozen source")
    try:
        notebook = json.loads(raw)
        cells = notebook["cells"]
        cell = cells[SOURCE_CELL_INDEX]
        source = cell["source"]
        source = "".join(source) if isinstance(source, list) else source
    except (KeyError, TypeError, IndexError, json.JSONDecodeError) as exc:
        raise HistoricalFactorError("Historical notebook cells malformed") from exc
    return extract_from_cell(source)
