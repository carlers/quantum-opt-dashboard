"""Headless Streamlit MVP flow: idle -> numeric preview -> SCIP -> stale protection."""
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def fresh():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not at.exception
    return at


def test_first_page_has_true_reference_preview_without_executing_scip():
    at = fresh()
    assert any("Water-quality sensor placement" in x.value for x in at.title)
    assert any("Understand the current model" in x.value for x in at.subheader)
    assert "mvp_result" not in at.session_state
    assert any(b.label == "Find monitoring locations (SCIP)" for b in at.button)
    assert len(at.metric) >= 3
    assert any("Nothing is solved until you run it" in str(x.proto)
               for x in at.info)


def test_run_downloads_original_model_verified_evidence_and_selection():
    at = fresh()
    at.button(key="mvp_run").click().run()
    assert not at.exception
    recorded = at.session_state["mvp_result"]
    assert recorded["metrics"]["status"] == "optimal"
    assert recorded["independent"]["original_feasible"]
    assert recorded["independent"]["selected_local_positions"] == [0, 1, 3, 6, 7]
    with ZipFile(BytesIO(recorded["zip"])) as evidence:
        names = set(evidence.namelist())
        assert {"model.json", "result.json", "selected_sites.csv",
                "actual_scip_model.lp", "SHA256SUMS.json"} == names
        model = json.loads(evidence.read("model.json"))
        outcome = json.loads(evidence.read("result.json"))
        assert model["constraints"]["budget_rhs"] == 5
        assert model["settings"]["candidate_sites_n"] == 20
        assert outcome["scip_optimal_proven"]
        assert outcome["independent_audit"]["selected_local_positions"] == [0, 1, 3, 6, 7]
        assert b"budget" in evidence.read("actual_scip_model.lp")
        assert len(evidence.read("selected_sites.csv").splitlines()) == 6


def test_changing_budget_removes_old_result_and_updates_preview_key():
    at = fresh()
    at.button(key="mvp_run").click().run()
    assert not at.exception
    previous = at.session_state["mvp_result"]["fingerprint"]
    field = next(x for x in at.number_input if x.label == "New sensors to place (K)")
    field.set_value(0).run()
    assert not at.exception
    assert not [x for x in at.metric if x.label == "Original objective (min.)"]
    assert any("Inputs changed" in str(x.proto) for x in at.info)
    assert "mvp_result" not in at.session_state
    assert "mvp_run" in [b.key for b in at.button]
    # No old result can be relabeled to current K. The new scenario must be run.


def test_paper_weights_counterfactual_is_explicit_before_solver():
    at = fresh()
    source = next(r for r in at.radio if r.label == "Criterion weights")
    source.set_value("Paper weights · comparison only").run()
    assert not at.exception
    assert "mvp_result" not in at.session_state
    assert any("Exploratory parameter comparison" in str(x.proto) for x in at.info)
    assert any("paper's published numerical inputs" in str(x.proto).lower()
               or "paper" in str(x.proto).lower() for x in at.warning)


def test_weight_source_switch_invalidates_a_previously_solved_result():
    at = fresh()
    at.button(key="mvp_run").click().run()
    assert not at.exception
    before = at.session_state["mvp_result"]["fingerprint"]
    switch = next(r for r in at.radio if r.label == "Criterion weights")
    switch.set_value("Paper weights · comparison only").run()
    assert not at.exception
    assert "mvp_result" not in at.session_state
    assert any("Inputs changed" in str(x.proto) for x in at.info)
    assert any("Exploratory parameter comparison" in str(x.proto) for x in at.info)
    assert not [x for x in at.metric if x.label == "Original objective (min.)"]


def test_cloud_warm_reload_with_legacy_preview_helper_still_renders_and_runs(monkeypatch):
    """Regression for 2026-10-18 Cloud traceback at app.py:157.

    Streamlit can rerun the updated page while the earlier imported audit
    module remains cached in sys.modules with the old five-argument preview
    signature. This test deliberately gives the app that legacy call boundary
    rather than running only in a clean Python process.
    """
    import hashlib
    import sys

    sys.path.insert(0, str(APP.parent))
    import mvp_audit

    modern = mvp_audit.preview

    def old_cached_preview(instance, *, dataset_sha256, weights,
                           weight_source, time_limit_seconds):
        return modern(instance, dataset_sha256=dataset_sha256,
                      weights=weights, weight_source=weight_source,
                      time_limit_seconds=time_limit_seconds)

    with monkeypatch.context() as patch:
        patch.setattr(mvp_audit, "preview", old_cached_preview)
        at = fresh()
        beta = next(x for x in at.number_input
                    if x.label == "Redundancy strength (β)")
        beta.set_value(2.).run()
        assert not at.exception
        assert any("redundancy 2" in str(x.proto) for x in at.caption)
        at.button(key="mvp_run").click().run()
        assert not at.exception
        result = at.session_state["mvp_result"]
        assert result["independent"]["original_feasible"]
        with ZipFile(BytesIO(result["zip"])) as archive:
            model = json.loads(archive.read("model.json"))
            assert model["settings"]["beta"] == 2.
            assert model["settings"]["delta"] == 1.
            saved = model.pop("model_fingerprint_sha256")
            assert saved == hashlib.sha256(mvp_audit.canonical(model)).hexdigest()
            assert saved == result["fingerprint"]
