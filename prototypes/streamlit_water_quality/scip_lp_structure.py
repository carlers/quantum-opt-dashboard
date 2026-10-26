"""Fail-closed *structural* review of SCIP's untransformed N20 CPLEX LP export.

Parses a deliberately small supported subset of SCIP 6.x's text LP format.
Reconstructs every binary variable, pair-product AND linearization row,
exact-budget equation, original local-one-hop row and serialized objective.
Anything outside this grammar fails closed. Objective DECIMALS are compared
at SCIP's observed 15-significant-digit serialization, NOT mistaken for the
exact IEEE754 binary64 coefficients (which are independently checked against
the compiled Instance by runtime_attestation.py).

This is an independently readable emitted-LP formulation witness, not an
authenticated SCIP executable/process log, a solver optimality certificate,
or a formal proof of source paper / real-world lake-network efficacy.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from hashlib import sha256
import math
import re

_NUM = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_VAR = r"(?:x\d+|p\d+_\d+)"
_TERM = re.compile(rf"\s*({_NUM})\s+({_VAR})(?=\s|$)")
_RHS = re.compile(rf"\s*(<=|>=|=)\s*({_NUM})\s*$")
_BOUND = re.compile(rf"\s*0\s*<=\s*({_VAR})\s*<=\s*1\s*$")
_LABEL = re.compile(r"\s*([A-Za-z][A-Za-z0-9_]*):\s*(.*)$")
_MAX_LP_BYTES = 100_000


def _fail(message: str):
    raise ValueError("Original N20 SCIP LP structural audit: " + message)


def _decimal(raw: str) -> Decimal:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError("Invalid numeric SCIP LP coefficient") from exc
    if not value.is_finite():
        _fail("Nonfinite SCIP LP numeric token")
    return value


def _parse_linear(raw: str) -> dict[str, Decimal]:
    remaining = raw.strip()
    terms: dict[str, Decimal] = {}
    if remaining in ("0", "+0", "-0"):
        return terms
    while remaining:
        matched = _TERM.match(remaining)
        if matched is None:
            _fail("Unexpected LP expression, nonlinear or unrecognized token: " + remaining[:60])
        number, variable = matched.groups()
        if variable in terms:
            _fail("Repeated variable coefficient: " + variable)
        terms[variable] = _decimal(number)
        remaining = remaining[matched.end():].strip()
    return terms


def _lp_sections(lp: bytes) -> tuple[str, dict[str, tuple[dict[str, Decimal], str, Decimal]], dict[str, tuple[Decimal, Decimal]], set[str]]:
    if not isinstance(lp, bytes) or not lp or len(lp) > _MAX_LP_BYTES:
        _fail("LP must be an original bounded N20 model and at most 100 KB")
    try:
        source = lp.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("Original SCIP LP must use ASCII text") from exc
    if "\x00" in source:
        _fail("NUL character in SCIP LP")
    lines = [ln.strip() for ln in source.splitlines()
             if ln.strip() and not ln.lstrip().startswith("\\")]
    sections: dict[str, list[str]] = {
        "Minimize": [], "Subject to": [], "Bounds": [], "Binaries": [],
    }
    expected = ("Minimize", "Subject to", "Bounds", "Binaries", "End")
    stage = -1
    for line in lines:
        if line in expected:
            target = expected.index(line)
            if target != stage + 1:
                _fail("LP section omitted, repeated, reordered or duplicated")
            stage = target
            continue
        if stage < 0 or stage >= 4:
            _fail("Unexpected LP content outside mandatory four sections")
        sections[expected[stage]].append(line)
    if stage != 4:
        _fail("LP missing terminating End or required variable section")

    obj_lines = sections["Minimize"]
    if not obj_lines or not obj_lines[0].startswith("Obj:"):
        _fail("LP must provide exactly one named Obj expression")
    if any(":" in x for x in obj_lines[1:]):
        _fail("Unexpected second objective")
    objective_raw = obj_lines[0][len("Obj:"):].strip()
    objective_raw += (" " + " ".join(obj_lines[1:])) if len(obj_lines) > 1 else ""
    objective = _parse_linear(objective_raw)

    named_rows: dict[str, tuple[dict[str, Decimal], str, Decimal]] = {}
    current_name = None
    current_text = []
    for line in sections["Subject to"] + ["FINISH__:" ]:
        header = _LABEL.fullmatch(line)
        if header:
            if current_name is not None:
                rhs_match = _RHS.search(" ".join(current_text))
                if rhs_match is None:
                    _fail("Missing LP row sense or RHS for " + current_name)
                body = " ".join(current_text)[:rhs_match.start()]
                named_rows[current_name] = (
                    _parse_linear(body), rhs_match.group(1), _decimal(rhs_match.group(2))
                )
            current_name = header.group(1)
            if current_name in named_rows:
                _fail("Repeated LP constraint name " + current_name)
            current_text = [header.group(2)]
        else:
            if current_name is None:
                _fail("Unnamed LP constraint")
            current_text.append(line)
    named_rows.pop("FINISH__", None)

    bounds = {}
    for line in sections["Bounds"]:
        match = _BOUND.fullmatch(line)
        if match is None:
            _fail("LP contains unrecognized or nonbinary variable bounds")
        v = match.group(1)
        if v in bounds:
            _fail("LP contains repeated variable bounds")
        bounds[v] = (Decimal(0), Decimal(1))
    binary_list = " ".join(sections["Binaries"]).split()
    binaries = set(binary_list)
    if len(binary_list) != len(binaries):
        _fail("LP has duplicated binary variable declarations")
    if any(re.fullmatch(_VAR, v) is None for v in binaries):
        _fail("Unrecognized binary variable name")
    return objective, named_rows, bounds, binaries


def _assert_row(rows, name: str, expected: dict[str, int], sense: str, rhs: int) -> None:
    if name not in rows:
        _fail("Missing required SCIP LP constraint " + name)
    coeffs, actual_sense, actual_rhs = rows[name]
    expected_terms = {k: Decimal(v) for k, v in expected.items() if v}
    if coeffs != expected_terms or actual_sense != sense or actual_rhs != rhs:
        _fail("Changed or fabricated SCIP LP constraint " + name)


def _expected_lp_decimal(number: float) -> Decimal:
    if not math.isfinite(number):
        _fail("Nonfinite original compiled model coefficient")
    # SCIP's writeProblem(trans=False) emits rounded text. 15 significant
    # digits are intentionally the LP FORMAT, not the real binary64 objective.
    return Decimal(format(float(number), ".15g"))


def certify_emitted_scip_lp(instance, raw_lp: bytes) -> dict:
    """Parse LP independently of SCIP and compare ALL compiled N20 MILP rows."""
    n = len(instance.free_indices)
    if n != 20 or not 0 <= instance.budget <= n:
        _fail("This reviewer is limited to original N20 K in 0..20")
    pairs = list(instance.quadratic)
    if any(type(i) is not int or type(j) is not int
           or not 0 <= i < j < n or not math.isfinite(float(q)) or q < 0
           for i, j, q in pairs):
        _fail("Invalid original nonnegative pair-product model")
    pairnames = [f"p{i}_{j}" for i, j, _ in pairs]
    if len(pairnames) != len(set(pairnames)):
        _fail("Original model contains duplicated quadratic pair")
    expected_variables = {f"x{i}" for i in range(n)} | set(pairnames)
    objective, rows, bounds, binaries = _lp_sections(raw_lp)
    if binaries != expected_variables or set(bounds) != expected_variables:
        _fail("Missing/extra original binary decision or pair-product variables")
    if len(rows) != 1 + 3 * len(pairs) + n:
        _fail("Incorrect number of source SCIP MILP constraints")

    expected_obj = {
        f"x{i}": dec
        for i in range(n)
        if (dec := _expected_lp_decimal(float(instance.linear[i]))) != 0
    }
    for i, j, q in pairs:
        dec = _expected_lp_decimal(float(q))
        if dec:
            expected_obj[f"p{i}_{j}"] = dec
    if objective != expected_obj:
        _fail("Actual serialized SCIP LP objective differs from compiled coefficients")

    _assert_row(rows, "budget", {f"x{i}": 1 for i in range(n)},
                "=", int(instance.budget))
    expected_labels = {"budget"}
    for i in range(n):
        ns = tuple(instance.neighbors[i])
        if len(ns) != len(set(ns)) or any(
            type(j) is not int or j == i or j < 0 or j >= n for j in ns
        ):
            _fail("Invalid original source one-hop neighbor index")
        site_terms = {f"x{i}": 1, **{f"x{j}": -1 for j in ns}}
        _assert_row(rows, f"connect_{i}", site_terms, "<=",
                    int(instance.fixed_neighbors[i]))
        expected_labels.add(f"connect_{i}")

    for pair_index, (i, j, _) in enumerate(pairs):
        pair = f"p{i}_{j}"
        triple = [
            ({pair: 1, f"x{i}": -1, f"x{j}": -1}, ">=", -1),
            ({pair: 1, f"x{i}": -1}, "<=", 0),
            ({pair: 1, f"x{j}": -1}, "<=", 0),
        ]
        for off, (coeffs, sense, rhs) in enumerate(triple):
            name = f"c{3*pair_index + off + 1}"
            _assert_row(rows, name, coeffs, sense, rhs)
            expected_labels.add(name)
    if set(rows) != expected_labels:
        _fail("Unexpected/replaced source MILP constraint identifiers")
    return {
        "schema_version": 1,
        "scope": "bounded_ASCII_CPLEX_LP_structural_formulation_only",
        "original_scip_lp_sha256": sha256(raw_lp).hexdigest(),
        "original_scip_binary_x_count": n,
        "linearized_binary_pair_count": len(pairs),
        "binary_variable_count": len(expected_variables),
        "structurally_verified_constraint_count": len(rows),
        "objective_compared_as_scip_15_digit_decimal_serialization": True,
        "active_model_binary64_objective_verified_elsewhere": True,
        "budget_equal_K_verified": True,
        "each_original_local_one_hop_verified": True,
        "each_pair_product_3row_exact_binary_linearization_verified": True,
        "variable_domains_verified": True,
        "independent_scip_process_execution_or_optimality_authenticated": False,
        "physical_monitoring_or_paper_parity": False,
    }
