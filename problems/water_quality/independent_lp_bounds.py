"""Review-only N50/N100 SCIP CPLEX LP byte auditing and independent HiGHS bounds.

Reconstruct every emitted row against exact source hex coefficients, then
solve the parsed LP using an entirely different MILP engine, SciPy HiGHS.
This corroborates computational optimality, not a formal signed certificate.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import re
from zipfile import ZipFile

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_array

from problems.water_quality.offline_scip_batch import (
    MAX_ARCHIVE_BYTES, canonical, verify_bundle,
)

NUM = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
VAR = r"(?:x\d+|p\d+_\d+)"
TERM = re.compile(rf"\s*({NUM})\s+({VAR})(?=\s|$)")
RHS = re.compile(rf"\s*(<=|>=|=)\s*({NUM})\s*$")
ROW = re.compile(r"([A-Za-z][A-Za-z0-9_]*):\s*(.*)")
BOUND = re.compile(rf"0\s*<=\s*({VAR})\s*<=\s*1")


def fail(message):
    raise ValueError("Independent LP/HiGHS audit: " + message)


def expression(raw):
    remaining = raw.strip()
    if remaining in ("0", "+0", "-0"):
        return {}
    terms = {}
    while remaining:
        match = TERM.match(remaining)
        if not match:
            fail("unrecognized/changed LP expression " + remaining[:60])
        number, name = match.groups()
        if name in terms:
            fail("duplicated LP coefficient")
        value = Decimal(number)
        if not value.is_finite():
            fail("nonfinite LP coefficient")
        terms[name] = value
        remaining = remaining[match.end():].strip()
    return terms


def parse_lp(lp):
    if not isinstance(lp, bytes) or not 0 < len(lp) <= 2_000_000:
        fail("missing or overlarge LP")
    try:
        text = lp.decode("ascii")
    except UnicodeDecodeError:
        fail("LP must be ASCII")
    if "\x00" in text:
        fail("NUL token in LP")
    sections = ("Minimize", "Subject to", "Bounds", "Binaries", "End")
    chunks = {section: [] for section in sections[:-1]}
    stage = -1
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("\\"):
            continue
        if line in sections:
            if sections.index(line) != stage + 1:
                fail("omitted/duplicated/reordered LP section")
            stage += 1
        else:
            if not 0 <= stage < 4:
                fail("LP content outside supported sections")
            chunks[sections[stage]].append(line)
    if stage != 4:
        fail("missing LP End")
    lines = chunks["Minimize"]
    if not lines or not lines[0].startswith("Obj:") or any(":" in x for x in lines[1:]):
        fail("unexpected LP objective")
    objective = expression(lines[0][4:] + " " + " ".join(lines[1:]))
    rows = {}
    current, tokens = None, []
    for line in chunks["Subject to"] + ["FINISH__:"]:
        head = ROW.fullmatch(line)
        if head is None:
            if current is None:
                fail("unlabeled LP row")
            tokens.append(line)
            continue
        if current is not None:
            joined = " ".join(tokens)
            rhs = RHS.search(joined)
            if rhs is None or current in rows:
                fail("invalid / duplicate LP row")
            rows[current] = (expression(joined[:rhs.start()]), rhs.group(1), Decimal(rhs.group(2)))
        current, tokens = head.group(1), [head.group(2)]
    rows.pop("FINISH__", None)
    bounds = set()
    for line in chunks["Bounds"]:
        matched = BOUND.fullmatch(line)
        if matched is None or matched.group(1) in bounds:
            fail("unrecognized/repeated LP bound")
        bounds.add(matched.group(1))
    listed = " ".join(chunks["Binaries"]).split()
    binaries = set(listed)
    if len(listed) != len(binaries) or any(re.fullmatch(VAR, x) is None for x in binaries):
        fail("unexpected/duplicated binary declaration")
    return objective, rows, bounds, binaries


def audit_structure(source, lp):
    n, k = source["N_free"], source["K"]
    if type(n) is not int or n not in (50, 100) or type(k) is not int or k != 5:
        fail("only nested N50/N100 K5 source models")
    if (len(source["linear_float64_hex"]) != n or len(source["free_neighbors"]) != n
            or len(source["fixed_neighbors"]) != n):
        fail("wrong source model dimension")
    pairs = source["quadratic_float64_hex"]
    if len({(i, j) for i, j, _ in pairs}) != len(pairs):
        fail("duplicate pair")
    for i, j, hex_q in pairs:
        if (type(i) is not int or type(j) is not int or not 0 <= i < j < n
                or not math.isfinite(float.fromhex(hex_q)) or float.fromhex(hex_q) < 0):
            fail("invalid source pair")
    objective, rows, bounds, binary = parse_lp(lp)
    expected_vars = {f"x{i}" for i in range(n)} | {f"p{i}_{j}" for i, j, _ in pairs}
    if bounds != expected_vars or binary != expected_vars:
        fail("LP variables/bounds inconsistent with source")
    if len(rows) != 3 * len(pairs) + 1 + n:
        fail("LP has wrong number of constraints")
    expected_obj = {}
    for i, h in enumerate(source["linear_float64_hex"]):
        d = Decimal(format(float.fromhex(h), ".15g"))
        if d:
            expected_obj[f"x{i}"] = d
    for i, j, h in pairs:
        d = Decimal(format(float.fromhex(h), ".15g"))
        if d:
            expected_obj[f"p{i}_{j}"] = d
    if objective != expected_obj:
        fail("emitted LP decimal coefficients differ from binary64 source")
    def check(name, coefficients, sense, rhs):
        expected = {x: Decimal(c) for x, c in coefficients.items() if c}
        if rows.get(name) != (expected, sense, Decimal(rhs)):
            fail("missing or altered constraint: " + name)
    row_no = 0
    for i, j, _ in pairs:
        p = f"p{i}_{j}"
        for coeff, sense, rhs in (
            ({p: 1, f"x{i}": -1, f"x{j}": -1}, ">=", -1),
            ({p: 1, f"x{i}": -1}, "<=", 0),
            ({p: 1, f"x{j}": -1}, "<=", 0),
        ):
            row_no += 1
            check("c" + str(row_no), coeff, sense, rhs)
    check("budget", {f"x{i}": 1 for i in range(n)}, "=", k)
    for i, neighbors in enumerate(source["free_neighbors"]):
        if (len(neighbors) != len(set(neighbors)) or
                any(type(j) is not int or not 0 <= j < n or j == i for j in neighbors)):
            fail("invalid source one-hop index")
        if source["fixed_neighbors"][i] not in (0, 1):
            fail("invalid fixed neighbor")
        check(f"connect_{i}", {f"x{i}": 1, **{f"x{j}": -1 for j in neighbors}},
              "<=", source["fixed_neighbors"][i])
    expected_rows = {"budget"} | {f"connect_{i}" for i in range(n)} | {
        f"c{i}" for i in range(1, row_no + 1)
    }
    if set(rows) != expected_rows:
        fail("unexpected named source row")
    return objective, rows


def check_highs_bound(source, lp, result, *, seconds=20):
    """HiGHS solves independently from the parsed LP, not original SCIP builder."""
    if type(seconds) is not int or not 1 <= seconds <= 60:
        fail("HiGHS wall seconds must be in 1..60")
    objective, rows = audit_structure(source, lp)
    if result.get("solver_status") != "optimal" or result.get("classification") != "optimal":
        fail("SCIP did not claim a proven optimal result")
    n = source["N_free"]
    names = [f"x{i}" for i in range(n)] + [
        f"p{i}_{j}" for i, j, _ in source["quadratic_float64_hex"]
    ]
    column = {v: i for i, v in enumerate(names)}
    c = np.array([float(objective.get(v, 0)) for v in names], dtype=float)
    i_idx, j_idx, vals, low, high = [], [], [], [], []
    for r, (coefficients, sense, rhs) in enumerate(rows.values()):
        for v, q in coefficients.items():
            i_idx.append(r)
            j_idx.append(column[v])
            vals.append(float(q))
        low.append(float(rhs) if sense in ("=", ">=") else -np.inf)
        high.append(float(rhs) if sense in ("=", "<=") else np.inf)
    matrix = coo_array(
        (np.array(vals, dtype=float),
         (np.array(i_idx, dtype=np.int32), np.array(j_idx, dtype=np.int32))),
        shape=(len(rows), len(names)),
    ).tocsr()
    run = milp(
        c, integrality=np.ones(len(names), dtype=np.int32), bounds=Bounds(0, 1),
        constraints=LinearConstraint(matrix, np.asarray(low), np.asarray(high)),
        options={"time_limit": seconds, "mip_rel_gap": 0.0},
    )
    if (run.status != 0 or run.x is None or run.fun is None
            or run.mip_dual_bound is None):
        fail("second solver did not certify optimality")
    if not all(math.isfinite(float(v)) for v in (run.fun, run.mip_dual_bound, run.mip_gap)):
        fail("nonfinite HiGHS bound")
    if not math.isclose(run.fun, run.mip_dual_bound, abs_tol=1e-6, rel_tol=1e-8):
        fail("HiGHS primal-dual gap remains")
    if not math.isclose(run.fun, result["solver_objective"], abs_tol=1e-6, rel_tol=1e-8):
        fail("SCIP and HiGHS objective differ")
    bits = [int(round(v)) for v in run.x[:n]]
    if any(abs(v - b) > 1e-5 for v, b in zip(run.x[:n], bits)):
        fail("fractional HiGHS selection")
    if sum(bits) != source["K"]:
        fail("second-solver invalid K")
    for i, b in enumerate(bits):
        if b and not source["fixed_neighbors"][i] and not any(
            bits[j] for j in source["free_neighbors"][i]
        ):
            fail("second-solver isolated selected source station")
    for offset, (i, j, _) in enumerate(source["quadratic_float64_hex"], n):
        if abs(run.x[offset] - bits[i] * bits[j]) > 1e-5:
            fail("second-solver invalid binary product")
    original_objective = sum(
        float.fromhex(h) for i, h in enumerate(source["linear_float64_hex"]) if bits[i]
    ) + sum(
        float.fromhex(h) for i, j, h in source["quadratic_float64_hex"]
        if bits[i] and bits[j]
    )
    if not math.isclose(original_objective, run.fun, abs_tol=1e-6, rel_tol=1e-8):
        fail("source-hex objective disagrees with second solver")
    return {
        "schema": "independent-source-lp-highs-v1", "N_free": n, "K": source["K"],
        "source_sha256": source["source_sha256"],
        "model_sha256": sha256(canonical(source)).hexdigest(),
        "actual_exported_LP_sha256": sha256(lp).hexdigest(),
        "scip_status": result["solver_status"],
        "scip_objective": result["solver_objective"],
        "highs_status": int(run.status),
        "highs_primal_objective": float(run.fun),
        "highs_dual_bound": float(run.mip_dual_bound),
        "highs_relative_gap": float(run.mip_gap),
        "highs_selected_master_positions": [
            source["free_master_positions"][i] for i, bit in enumerate(bits) if bit
        ],
        "LP_decimal_rounded_15_significant_digits": True,
        "independent_computational_optimality_corroboration": True,
        "formal_proof_certificate": False,
        "paper_input_parity_claimed": False,
    }


def inspect_archive(path, *, seconds=20):
    with ZipFile(path) as archive:
        ledger = json.loads(archive.read("index.json"))
        receipts = []
        for tier in ledger["tiers"]:
            nested = archive.read(tier["archive"])
            if len(nested) > MAX_ARCHIVE_BYTES or sha256(nested).hexdigest() != tier["archive_sha256"]:
                fail("outer artifact integrity violation")
            result = verify_bundle(nested)
            with ZipFile(io.BytesIO(nested)) as contents:
                model = json.loads(contents.read("model.json"))
                lp = contents.read("emitted_scip_model.lp")
            if model["source_sha256"] != ledger["source_sha256"]:
                fail("dataset identity mismatch")
            if sha256(canonical(model)).hexdigest() != tier["model_sha256"]:
                fail("binary64 source model identity mismatch")
            receipts.append(check_highs_bound(model, lp, result, seconds=seconds))
        if [r["N_free"] for r in receipts] != [50, 100]:
            fail("must contain N50 then N100")
        return receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outer_zip", type=Path)
    parser.add_argument("--seconds", type=int, default=20)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    record = {"schema": "independent-source-lp-highs-bounds-v1",
              "runs": inspect_archive(args.outer_zip, seconds=args.seconds)}
    result = json.dumps(record, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        args.output.write_text(result, encoding="utf-8")
    print(result)


if __name__ == "__main__":
    main()
