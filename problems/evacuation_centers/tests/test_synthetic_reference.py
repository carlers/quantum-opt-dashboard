"""Independent synthetic-only formulation and source-provenance acceptance #32."""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from synthetic_reference import (
    FIXTURE_PATH, SyntheticProblem, check_assignment,
    independent_enumeration, maximal_coverage_reference,
    run_cli, scip_lexicographic, validate_parity,
)


def toy():
    return SyntheticProblem.from_fixture(FIXTURE_PATH)


def test_predeclared_two_zone_two_shelter_exact_and_independent():
    model = toy()
    result = validate_parity(model)
    coverage = result["mclp_potential_only"]
    scip = result["capacitated_scip"]
    reference = result["independent_enumeration_highs"]

    assert result["kind"] == "SYNTHETIC"
    assert result["actual_shelters_used"] is False
    assert coverage["max_potential_coverage_persons"] == 7
    assert coverage["capacity_constraints"] == "NOT_MODELED"
    assert scip["status"] == "optimal"
    assert scip["phase1_status"] == scip["phase2_status"] == "optimal"
    assert scip["selected_sites_zero_based"] == [0]
    assert scip["unserved_persons"] == pytest.approx(2, abs=1e-6)
    assert scip["served_persons"] == pytest.approx(5, abs=1e-6)
    assert scip["total_travel_person_minutes"] == pytest.approx(6, abs=1e-6)
    assert scip["site_load_persons"] == pytest.approx([5, 0], abs=1e-6)
    assert scip["unserved_by_zone_persons"] == pytest.approx([0, 2], abs=1e-6)
    observed = {
        (t["zone_index"], t["site_index"]): t["persons"]
        for t in scip["allocations"]
    }
    assert observed == pytest.approx({(0, 0): 4, (1, 0): 1}, abs=1e-6)
    assert reference["opening_subsets_checked"] == 3
    assert reference["selected_sites_zero_based"] == [0]
    assert reference["min_unserved_persons"] == pytest.approx(2)
    assert reference["min_travel_person_minutes"] == pytest.approx(6)


def test_covering_is_potential_not_evacuees_served():
    p = toy()
    mclp = maximal_coverage_reference(p)
    capacitated = scip_lexicographic(p)
    assert mclp["max_potential_coverage_persons"] == sum(p.demands) == 7
    assert capacitated["served_persons"] == pytest.approx(5, abs=1e-6)
    assert capacitated["unserved_persons"] == pytest.approx(2, abs=1e-6)
    assert mclp["max_potential_coverage_persons"] > capacitated["served_persons"]


def test_all_served_is_impossible_with_one_capacity_five_center():
    p = toy()
    outcome = scip_lexicographic(p, require_all_served=True)
    assert outcome["status"] == "infeasible"
    assert outcome["phase"] == 1


def test_budget_zero_all_unserved_and_two_sites_can_serve_all():
    model = toy()
    none = validate_parity(replace(model, max_open=0))
    assert none["capacitated_scip"]["unserved_persons"] == pytest.approx(7, abs=1e-6)
    assert none["capacitated_scip"]["selected_sites_zero_based"] == []
    both = validate_parity(replace(model, max_open=2))
    assert both["capacitated_scip"]["unserved_persons"] == pytest.approx(0, abs=1e-6)
    assert both["independent_enumeration_highs"]["min_unserved_persons"] == pytest.approx(0)


def test_unreachable_zone_and_unsafe_shelter_excluded_from_assignments():
    p = toy()
    first_zone_disconnected = replace(p, travel_minutes=((None, None), (2, 4)))
    result = validate_parity(first_zone_disconnected)
    assert result["capacitated_scip"]["unserved_by_zone_persons"][0] == pytest.approx(4)
    assert result["mclp_potential_only"]["max_potential_coverage_persons"] == pytest.approx(3)

    no_safe_sites = replace(p, eligible=(False, False))
    result = validate_parity(no_safe_sites)
    assert result["capacitated_scip"]["selected_sites_zero_based"] == []
    assert result["capacitated_scip"]["unserved_persons"] == pytest.approx(7)
    assert result["mclp_potential_only"]["max_potential_coverage_persons"] == 0


def test_zero_capacity_and_zero_demand_are_explicit_not_imputed():
    p = toy()
    zero_capacity = validate_parity(replace(p, capacities=(0, 0)))
    assert zero_capacity["capacitated_scip"]["served_persons"] == pytest.approx(0)
    assert zero_capacity["capacitated_scip"]["unserved_persons"] == pytest.approx(7)
    zero_demand = validate_parity(replace(p, demands=(0, 0)))
    assert zero_demand["capacitated_scip"]["unserved_persons"] == pytest.approx(0)
    assert zero_demand["capacitated_scip"]["mean_travel_minutes_per_served_person"] is None


@pytest.mark.parametrize("changes,reason", [
    ({"capacities": (None, 5)}, "Unknown"),
    ({"demands": (-1, 3)}, "Unknown"),
    ({"capacities": (float("nan"), 5)}, "Unknown"),
    ({"travel_minutes": ((1, -1), (2, 4))}, "Travel"),
    ({"travel_minutes": ((1, None), (2,))}, "rectangular"),
    ({"eligible": (True, None)}, "Eligibility"),
    ({"eligible": (True,)}, "dimensions"),
    ({"max_open": 3}, "budget"),
    ({"zone_ids": ("a", "a")}, "Duplicate"),
    ({"label": "OFFICIAL SHELTER ADVICE"}, "synthetic"),
])
def test_inputs_reject_unlicensed_reality_disguised_as_synthetic(changes, reason):
    with pytest.raises(ValueError, match=reason):
        replace(toy(), **changes)


def test_independent_feasibility_audit_catches_budget_capacity_and_road_errors():
    p = toy()
    with pytest.raises(AssertionError, match="Capacity"):
        check_assignment(p, (0,), {(0, 0): 4., (1, 0): 3.}, [0., 0.])
    with pytest.raises(AssertionError, match="Demand balance"):
        check_assignment(p, (0,), {(0, 0): 4., (1, 0): 1.}, [0., 0.])
    with pytest.raises(AssertionError, match="Invalid open"):
        check_assignment(p, (0, 1), {}, [4., 3.])
    with pytest.raises(AssertionError, match="unreachable"):
        check_assignment(replace(p, travel_minutes=((None, 9), (2, 4))),
                         (0,), {(0, 0): 4.}, [0., 3.])


def test_exported_real_scip_lp_and_checksums_are_both_verified(tmp_path):
    result = run_cli(tmp_path)
    first = (tmp_path / "synthetic-stage1-unserved.lp").read_text()
    second = (tmp_path / "synthetic-stage2-travel.lp").read_text()
    for token in ("open_0", "open_1", "unserved_0", "unserved_1", "capacity_0"):
        assert token in first and token in second
    assert "fix_optimal_unserved" in second
    assert "fix_optimal_unserved" not in first
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    for name, digest in manifest["files_sha256"].items():
        assert sha256((tmp_path / name).read_bytes()).hexdigest() == digest
    assert (tmp_path / "fixture.json").read_bytes() == FIXTURE_PATH.read_bytes()
    assert result["provenance"]["fixture_sha256"] == sha256(FIXTURE_PATH.read_bytes()).hexdigest()
    assert result["capacitated_scip"]["phase1_optimal_unserved_persons"] == pytest.approx(2)
    assert json.loads((tmp_path / "summary.json").read_text())["kind"] == "SYNTHETIC"


def test_independent_reference_and_scip_agree_across_deterministic_small_variants():
    model = toy()
    cases = [
        replace(model, capacities=(3, 4)),
        replace(model, demands=(2, 1)),
        replace(model, travel_minutes=((8, 1), (1, 8))),
        replace(model, eligible=(False, True)),
        replace(model, travel_minutes=((1, None), (None, 4))),
        replace(model, capacities=(10, 0)),
    ]
    for problem in cases:
        comparison = validate_parity(problem)
        assert comparison["capacitated_scip"]["status"] == "optimal"
        assert comparison["capacitated_scip"]["original_constraints_ok"]
