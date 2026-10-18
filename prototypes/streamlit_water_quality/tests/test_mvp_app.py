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
    assert any("Review the mathematical problem" in x.value for x in at.subheader)
    assert "mvp_result" not in at.session_state
    assert any(b.label == "Run SCIP placement" for b in at.button)
    assert len(at.metric) >= 3
    assert any("Opening the dashboard does not run a solver" in str(x.proto)
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
