"""Guided editor contracts: atomic edits to the same scientific typed IR."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "framework" / "python"))
sys.path.insert(0, str(ROOT / "prototypes" / "streamlit_configurable"))

from guided_math import apply_guided_edit, parse_components
from qopt.core.math_ir import validate_ir, render_original

EXAMPLES = ROOT / "problems" / "evacuation_centers" / "examples"


def fixture(name="synthetic-typed-mixed.json"):
    return json.loads((EXAMPLES / name).read_text())


def test_guided_objective_edits_change_exact_equation_and_copy_not_source():
    original = fixture()
    source = deepcopy(original)
    changed = apply_guided_edit(source, {}, "linear_set",
                                name="people", coefficient=8.0)
    assert source == original
    assert changed["objective"]["linear"]["people"] == 8
    assert "+8*people" in render_original(validate_ir(changed, {}))
    changed = apply_guided_edit(changed, {}, "objective_update",
                                sense="minimize", constant=7)
    assert "minimize E = +7" in render_original(validate_ir(changed, {}))


def test_guided_constraint_edits_are_precise_and_respect_rhs_override():
    model = fixture()
    altered = apply_guided_edit(model, {}, "constraint_update",
                                name="limit_served", sense=">=", rhs=2)
    assert altered["constraints"][-1]["sense"] == ">="
    assert "limit_served: +1*people >= 2" in render_original(validate_ir(altered, {}))
    with pytest.raises(ValueError, match="RHS override"):
        apply_guided_edit(model, {"rhs_overrides": {"limit_served": 2}},
                          "constraint_update", name="limit_served",
                          sense="<=", rhs=3)
    assert model == fixture()


def test_add_remove_row_changes_exact_qubo_eligibility():
    data = fixture("synthetic-typed-binary-qubo.json")
    changed = apply_guided_edit(data, {}, "constraint_add",
                                name="no_b", sense="==", rhs=0)
    assert len(changed["constraints"]) == 1
    changed = apply_guided_edit(changed, {}, "constraint_coefficient",
                                name="no_b", variable="b", coefficient=1)
    assert changed["constraints"][0]["linear"]["b"] == 1
    changed = apply_guided_edit(changed, {}, "constraint_coefficient_remove",
                                name="no_b", variable="b")
    assert changed["constraints"][0]["linear"] == {}
    removed = apply_guided_edit(changed, {}, "constraint_remove", name="no_b")
    assert removed["constraints"] == []
    assert data["constraints"] == []


def test_reference_guard_blocks_unsafe_deletion_and_invalid_domain():
    data = fixture()
    with pytest.raises(ValueError, match="referenced"):
        apply_guided_edit(data, {}, "variable_remove", name="open")
    with pytest.raises(ValueError, match="only for distinct binary"):
        apply_guided_edit(
            fixture("synthetic-typed-binary-qubo.json"), {},
            "variable_update", name="a", domain="continuous", lower=0, upper=1
        )
    with pytest.raises(ValueError, match="Duplicate"):
        apply_guided_edit(data, {}, "variable_add", name="open",
                          domain="binary", lower=0, upper=1)
    with pytest.raises(ValueError, match="Unsupported guided"):
        apply_guided_edit(data, {}, "eval", python="1+1")
    assert data == fixture()


def test_added_variable_can_be_removed_if_unreferenced_and_duplicates_fail():
    data = fixture("synthetic-typed-binary-qubo.json")
    changed = apply_guided_edit(data, {}, "variable_add",
                                name="new_one", domain="binary", lower=0, upper=1)
    assert len(changed["variables"]) == 3
    removed = apply_guided_edit(changed, {}, "variable_remove", name="new_one")
    assert removed == data


def test_term_deletion_prevents_silent_dropping_referenced_variables():
    data = fixture("synthetic-typed-binary-qubo.json")
    with pytest.raises(ValueError, match="referenced"):
        apply_guided_edit(data, {}, "variable_remove", name="a")
    edited = apply_guided_edit(data, {}, "linear_remove", name="a")
    edited = apply_guided_edit(edited, {}, "quadratic_remove", first="a", second="b")
    final = apply_guided_edit(edited, {}, "variable_remove", name="a")
    assert [v["name"] for v in final["variables"]] == ["b"]


def test_exact_json_components_parser_preserves_structure():
    data = fixture()
    parsed = parse_components(
        json.dumps(data["variables"]), json.dumps(data["objective"]),
        json.dumps(data["constraints"]),
    )
    assert parsed == data
