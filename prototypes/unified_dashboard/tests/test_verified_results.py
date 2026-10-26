"""Source-bound frozen N50/N100 receipts and unified navigation acceptance."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from problems.water_quality.nested_resolution import build_nested_instances
from prototypes.unified_dashboard.verified_results import (
    APPROVED_RUN_ID, EXPECTED_EVIDENCE_SHA256, ReviewedSourceError,
    read_reviewed_snapshot, validate_reviewed_observations,
)

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(scope="module")
def reviewed():
    snapshot = read_reviewed_snapshot()
    study = build_nested_instances()
    verified = validate_reviewed_observations(snapshot, study)
    return snapshot, study, verified


def test_pinned_ci_receipt_recomputes_both_real_source_solutions(reviewed):
    snapshot, study, observations = reviewed
    assert snapshot["source_workflow_run_id"] == APPROVED_RUN_ID
    assert snapshot["original_artifact_zip_sha256"] == EXPECTED_EVIDENCE_SHA256
    assert [r["n_free"] for r in observations] == [50, 100]
    assert [r["original_objective"] for r in observations] == pytest.approx(
        [-3.3012934918564643, -3.4910546048016684], abs=1e-10
    )
    assert observations[0]["selected_source_master_positions"] == [
        5253, 2394, 1557, 47, 5409
    ]
    assert observations[1]["selected_source_master_positions"] == [
        5253, 1557, 47, 5328, 2530
    ]
    assert tuple(t.n_free for t in study.tier_instances) == (20, 50, 100)


@pytest.mark.parametrize("field,forged", [
    ("original_objective", -99.),
    ("highs_dual_bound", -99.),
    ("linear_component", -99.),
    ("emitted_lp_sha256", "unsigned and mutable"),
    ("scip_status", "timelimit"),
])
def test_altered_computational_claims_fail_closed(reviewed, field, forged):
    snapshot, study, _ = reviewed
    attack = deepcopy(snapshot)
    attack["observations"][0][field] = forged
    with pytest.raises(ReviewedSourceError):
        validate_reviewed_observations(attack, study)


def test_altered_source_identity_and_paper_claims_fail_closed(reviewed):
    snapshot, study, _ = reviewed
    for key, forged in (
        ("source_geojson_sha256", "different-source"),
        ("original_artifact_zip_sha256", "wrong-artifact"),
        ("verified_cross_tier_small_embeds_unchanged_in_large", False),
    ):
        attack = deepcopy(snapshot)
        attack[key] = forged
        with pytest.raises(ReviewedSourceError):
            validate_reviewed_observations(attack, study)
    attack = deepcopy(snapshot)
    attack["scientific_limitations"]["paper_data_and_field_validation"] = True
    with pytest.raises(ReviewedSourceError):
        validate_reviewed_observations(attack, study)


def test_snapshot_file_tampering_rejected_even_when_json_parses(tmp_path):
    orig = read_reviewed_snapshot()
    path = tmp_path / "snapshot.json"
    path.write_text(__import__("json").dumps(orig), encoding="utf-8")
    with pytest.raises(ReviewedSourceError, match="bytes changed"):
        read_reviewed_snapshot(path)


def test_unified_results_page_is_read_only_and_scientifically_labeled():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception, app.exception
    app.switch_page("pages/verified_results.py").run()
    assert not app.exception, app.exception
    assert any("Verified offline water-quality results" in x.value for x in app.title)
    assert any("Archived SOURCE-MODEL results" in str(x.proto) for x in app.warning)
    assert any("Two measured resolutions" in x.value for x in app.subheader)
    assert any("Exactly TWO observations" in str(x.proto) for x in app.caption)
    assert not any(b.key == "mvp_run" for b in app.button)
    assert "mvp_result" not in app.session_state
    assert any(s.label == "Archived experiment resolution (N)" for s in app.selectbox)
    select = next(s for s in app.selectbox
                  if s.label == "Archived experiment resolution (N)")
    select.set_value(100).run()
    assert not app.exception, app.exception
    assert any("Archived selected sites" in x.value for x in app.subheader)
    assert "mvp_result" not in app.session_state
    assert not any(b.key == "mvp_run" for b in app.button)
