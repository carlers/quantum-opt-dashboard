"""Real original SCIP exported LP and adversarial structural-forgery cases.

The parser is tested against a freshly *emitted* PySCIPOpt LP with original
source 20 free/15 fixed graph. No source notebook or data alteration.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import replace
import re

import numpy as np
import pytest

from model import NOTEBOOK_WEIGHTS, load_data, make_instance, solve_scip
from scip_lp_structure import certify_emitted_scip_lp

DATA = Path(__file__).resolve().parents[3] / "problems/water_quality/data/LDB_centroids_clean.geojson"


@pytest.fixture(scope="module")
def actual_emitted_lp():
    data = load_data(DATA)
    instance, simulated = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    assert not simulated
    with TemporaryDirectory() as directory:
        target = Path(directory) / "actual_scip_model.lp"
        chosen, result = solve_scip(instance, time_limit=30, export_lp_path=target)
        assert result["optimal"] is True
        return instance, target.read_bytes()


def _corrupt(lp: bytes, before: str, after: str) -> bytes:
    text = lp.decode("ascii")
    if before not in text:
        raise AssertionError("Expected original SCIP LP pattern missing: " + before)
    return text.replace(before, after, 1).encode("ascii")


def test_real_scip_emitted_objective_and_all_budget_connectivity_pair_rows(actual_emitted_lp):
    instance, lp = actual_emitted_lp
    proof = certify_emitted_scip_lp(instance, lp)
    assert proof["original_scip_binary_x_count"] == 20
    assert proof["linearized_binary_pair_count"] == len(instance.quadratic)
    assert proof["binary_variable_count"] == 20 + len(instance.quadratic)
    assert proof["structurally_verified_constraint_count"] == 21 + 3 * len(instance.quadratic)
    assert proof["each_pair_product_3row_exact_binary_linearization_verified"] is True
    assert proof["budget_equal_K_verified"] is True
    assert proof["objective_compared_as_scip_15_digit_decimal_serialization"] is True
    assert proof["independent_scip_process_execution_or_optimality_authenticated"] is False


def test_changed_budget_denied(actual_emitted_lp):
    inst, lp = actual_emitted_lp
    mutant = _corrupt(lp, " = +5\n", " = +4\n")
    with pytest.raises(ValueError, match="budget"):
        certify_emitted_scip_lp(inst, mutant)


def test_forged_connectivity_neighbor_denied(actual_emitted_lp):
    inst, lp = actual_emitted_lp
    mutant = _corrupt(lp, "connect_7: +1 x7 -1 x0 -1 x14 <= +0",
                      "connect_7: +1 x7 -1 x0 <= +0")
    with pytest.raises(ValueError, match="connect_7"):
        certify_emitted_scip_lp(inst, mutant)


def test_forged_pair_product_lower_bound_denied(actual_emitted_lp):
    inst, lp = actual_emitted_lp
    mutant = _corrupt(lp, " c1: +1 p0_7 -1 x0 -1 x7 >= -1",
                      " c1: +1 p0_7 -1 x0 -1 x7 >= +0")
    with pytest.raises(ValueError, match="c1"):
        certify_emitted_scip_lp(inst, mutant)


def test_forged_pair_product_upper_bound_denied(actual_emitted_lp):
    inst, lp = actual_emitted_lp
    mutant = _corrupt(lp, " c2: +1 p0_7 -1 x0 <= +0",
                      " c2: +1 p0_7 -1 x0 <= +1")
    with pytest.raises(ValueError, match="c2"):
        certify_emitted_scip_lp(inst, mutant)


def test_forged_objective_decimal_denied(actual_emitted_lp):
    inst, lp = actual_emitted_lp
    match = re.search(rb"(?m)(Obj: )([-+]?[0-9.]+)( x0)", lp)
    assert match
    forged = lp[:match.start(2)] + b"-99.5" + lp[match.end(2):]
    with pytest.raises(ValueError, match="objective"):
        certify_emitted_scip_lp(inst, forged)


def test_forged_variable_domain_or_missing_binary_denied(actual_emitted_lp):
    inst, lp = actual_emitted_lp
    with pytest.raises(ValueError, match="bounds"):
        certify_emitted_scip_lp(inst, _corrupt(lp, " 0 <= x0 <= 1", " 0 <= x0 <= 2"))
    with pytest.raises(ValueError, match="Missing/extra"):
        certify_emitted_scip_lp(inst, _corrupt(lp, "\n x0 x1", "\n x1"))


def test_unexpected_row_or_extra_var_denied(actual_emitted_lp):
    inst, lp = actual_emitted_lp
    extra = _corrupt(lp, "\nBounds\n", "\n ghost: +1 x0 <= +1\nBounds\n")
    with pytest.raises(ValueError, match="number"):
        certify_emitted_scip_lp(inst, extra)


def test_repeated_or_nonstandard_sections_denied(actual_emitted_lp):
    inst, lp = actual_emitted_lp
    for forged in (
        lp + b"\nMinimize\n Obj: +1 x0\n",
        _corrupt(lp, "\nBinaries\n", "\nGenerals\n"),
    ):
        with pytest.raises(ValueError, match="LP"):
            certify_emitted_scip_lp(inst, forged)


def test_actual_compiled_graph_mutation_denied_even_if_lp_unchanged(actual_emitted_lp):
    inst, lp = actual_emitted_lp
    neighbor = list(inst.neighbors)
    neighbor[7] = tuple(x for x in neighbor[7] if x != 0)
    changed = replace(inst, neighbors=tuple(neighbor))
    with pytest.raises(ValueError, match="connect_7"):
        certify_emitted_scip_lp(changed, lp)


def test_zero_objective_real_scip_serialization_remains_structurally_reviewable(actual_emitted_lp):
    inst, _ = actual_emitted_lp
    zero = replace(inst, linear=np.zeros(20), quadratic=tuple())
    with TemporaryDirectory() as tmp:
        p = Path(tmp) / "flat.lp"
        _, result = solve_scip(zero, time_limit=30, export_lp_path=p)
        assert result["optimal"] is True
        record = certify_emitted_scip_lp(zero, p.read_bytes())
    assert record["binary_variable_count"] == 20
    assert record["structurally_verified_constraint_count"] == 21
