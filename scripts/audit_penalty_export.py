"""Read-only, dependency-free audit of historical CELL 7/8 penalty exports.

Inputs must be researcher-provided local JSON/CSV. Never execute the original
notebook, fetch a cloud object, or publish raw experiment output to GitHub.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import sys

MAX_BYTES = 8_000_000
MAX_POINTS = 10_000
ABS_TOL = Decimal("1e-9")
REL_TOL = Decimal("1e-12")


class ExportAuditError(ValueError):
    """Invalid or mismatched historical output; no scientific claim accepted."""


def _unique(items):
    data = {}
    for key, value in items:
        if key in data:
            raise ExportAuditError("Duplicate JSON key")
        data[key] = value
    return data


def _json(path):
    if (path.is_symlink() or not path.is_file()
            or not 0 < path.stat().st_size <= MAX_BYTES):
        raise ExportAuditError("Missing, symlinked or oversized export")
    raw = path.read_bytes()
    try:
        data = json.loads(
            raw, parse_float=Decimal, parse_int=int,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ExportAuditError("Nonfinite JSON constant")
            ), object_pairs_hook=_unique,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExportAuditError("Invalid JSON") from exc
    return data, sha256(raw).hexdigest()


def _number(value, key):
    if value is None or isinstance(value, (bool, list, dict)):
        raise ExportAuditError("Missing or invalid numeric " + key)
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ExportAuditError("Malformed numeric " + key) from exc
    if not result.is_finite():
        raise ExportAuditError("Nonfinite numeric " + key)
    return result


def _close(a, b):
    return abs(a-b) <= max(ABS_TOL, REL_TOL * max(abs(a), abs(b)))


def _point(row):
    if not isinstance(row, dict):
        raise ExportAuditError("Grid point is not a record")
    lb = _number(row.get("lambda_budget"), "lambda_budget")
    lc = _number(row.get("lambda_conn"), "lambda_conn")
    total = _number(row.get("penalty_sum"), "penalty_sum")
    rate = _number(row.get("feas_rate_mean"), "feas_rate_mean")
    if lb < 0 or lc < 0 or not 0 <= rate <= 1:
        raise ExportAuditError("Penalty or feasibility outside allowed range")
    if not _close(total, lb + lc):
        raise ExportAuditError("Grid penalty_sum inconsistent with components")
    return (lb, lc, total, rate)


def audit_exports(grid_path, winners_path, summary_path=None):
    """Verify internal arithmetic and winner selection only, not an experiment."""
    grid, grid_sha = _json(Path(grid_path))
    winners, winners_sha = _json(Path(winners_path))
    if (not isinstance(grid, dict) or type(grid.get("N")) is not int
            or grid["N"] < 1):
        raise ExportAuditError("Missing integer N tier")
    tier = grid["N"]
    if not isinstance(winners, dict) or str(tier) not in winners:
        raise ExportAuditError("Missing raw winner for specified N tier")
    config = grid.get("config")
    if not isinstance(config, dict):
        raise ExportAuditError("Missing grid configuration")
    threshold = _number(config.get("FEAS_THRESHOLD"), "FEAS_THRESHOLD")
    if not 0 <= threshold <= 1:
        raise ExportAuditError("Invalid feasibility threshold")
    points = grid.get("grid_points")
    if not isinstance(points, list) or not 1 <= len(points) <= MAX_POINTS:
        raise ExportAuditError("Missing or unbounded grid points")
    decoded = [_point(row) for row in points]
    eligible = [i for i, row in enumerate(decoded) if row[3] >= threshold]
    # The original summary code uses idxmin / idxmax, which keep the
    # first eligible row on a tie. Preserve that instead of re-ranking.
    chosen_index = (min(eligible, key=lambda i: decoded[i][2]) if eligible
                    else max(range(len(decoded)), key=lambda i: decoded[i][3]))
    chosen = decoded[chosen_index]
    winner = winners[str(tier)]
    if not isinstance(winner, dict):
        raise ExportAuditError("Malformed winner record")
    reported = (
        _number(winner.get("λ_budget"), "winner budget"),
        _number(winner.get("λ_conn"), "winner connectivity"),
        _number(winner.get("Penalty Sum"), "winner penalty sum"),
        _number(winner.get("Feasibility (%)"), "winner feasibility") / 100,
    )
    if not _close(reported[2], reported[0] + reported[1]):
        raise ExportAuditError("Winner sum inconsistent with components")
    if not all(_close(a, b) for a, b in zip(chosen, reported)):
        raise ExportAuditError("Winner mismatches original grid selection")
    summary_sha = None
    if summary_path is not None:
        path = Path(summary_path)
        if (path.is_symlink() or not path.is_file()
                or not 0 < path.stat().st_size <= MAX_BYTES):
            raise ExportAuditError("Missing or unsafe CSV summary")
        raw = path.read_bytes()
        summary_sha = sha256(raw).hexdigest()
        try:
            rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
        except UnicodeDecodeError as exc:
            raise ExportAuditError("Bad CSV encoding") from exc
        matches = [row for row in rows if row.get("N") == str(tier)]
        if len(matches) != 1:
            raise ExportAuditError("Expected exactly one CSV row for this tier")
        row = matches[0]
        csv_result = (
            _number(row.get("Winner λ_budget"), "CSV budget"),
            _number(row.get("Winner λ_conn"), "CSV connectivity"),
            _number(row.get("Winner Penalty Sum"), "CSV penalty sum"),
        )
        if not all(_close(a, b) for a, b in zip(csv_result, chosen[:3])):
            raise ExportAuditError("CSV summary differs from selected raw winner")
    return {
        "schema": "qopt-historical-penalty-export-review-v1",
        "tier_n": tier, "raw_grid_points_checked": len(decoded),
        "selected_grid_position": chosen_index,
        "selection_rule": ("lowest_penalty_sum_above_feasibility_threshold"
                           if eligible else "fallback_highest_feasibility"),
        "grid_sha256": grid_sha, "winners_sha256": winners_sha,
        "summary_sha256": summary_sha,
        "internal_arithmetic_and_winner_consistent": True,
        "original_manuscript_table_verified": False,
        "scientific_optimality_proven": False,
        "source_data_provenance_verified": False,
        "cloud_write_authorized": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid", type=Path, required=True)
    parser.add_argument("--winners", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    try:
        report = audit_exports(args.grid, args.winners, args.summary)
    except ExportAuditError as exc:
        print("Penalty export audit FAILED: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
