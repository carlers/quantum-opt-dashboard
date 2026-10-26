"""Two dashboard modes: real exact network solver, source SCIP unchanged."""
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def page():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not at.exception, at.exception
    return at


def test_two_modes_only_and_original_selected_by_default():
    at = page()
    chooser = next(r for r in at.radio if r.label == "Wireless connectivity")
    assert chooser.options == [
        "Local clusters · original", "Global connectivity · all stations"
    ]
    assert chooser.value == "Local clusters · original"
    assert any(b.label == "Find monitoring locations (SCIP)" for b in at.button)


def test_switching_to_global_fingerprints_graph_and_invalidates_source_result():
    at = page()
    at.button(key="mvp_run").click().run()
    assert not at.exception
    old_hash = at.session_state["mvp_result"]["fingerprint"]
    topology = next(r for r in at.radio if r.label == "Wireless connectivity")
    topology.set_value("Global connectivity · all stations").run()
    assert not at.exception, at.exception
    assert "mvp_result" not in at.session_state
    assert any("Inputs changed" in str(x.proto) for x in at.info)
    assert any(b.label == "Find fully connected stations (exact search)" for b in at.button)
    assert any("Global connectivity" in str(x.proto) for x in at.caption)
    # Validates new mode has different model even with identical coefficients.
    assert at.session_state.get("mvp_result") is None


def test_global_run_does_not_fake_optimum_or_scip_lp_if_infeasible():
    at = page()
    topology = next(r for r in at.radio if r.label == "Wireless connectivity")
    topology.set_value("Global connectivity · all stations").run()
    assert not at.exception, at.exception
    at.button(key="mvp_run").click().run()
    assert not at.exception, at.exception
    result = at.session_state["mvp_result"]
    assert result["fingerprint"]
    with ZipFile(BytesIO(result["zip"])) as evidence:
        names = set(evidence.namelist())
        assert "wireless_graph.json" in names
        assert "actual_scip_model.lp" not in names
        assert "SHA256SUMS.json" in names
        model = json.loads(evidence.read("model.json"))
        out = json.loads(evidence.read("result.json"))
        graph = json.loads(evidence.read("wireless_graph.json"))
        assert model["settings"]["connectivity_mode"] == "all_stations_connected"
        assert model["constraints"]["global_path_connectivity"]
        assert graph["fixed_count"] == 15 and graph["free_count"] == 20
        assert out["solver"] if "solver" in out else out["algorithm"]
        assert out["model_fingerprint_sha256"] == result["fingerprint"]
        if result["chosen"] is None:
            assert out["optimal_proven"] is False
            assert result["metrics"]["status"].startswith(("infeasible_", "time_limit_"))
            assert any("No certified globally connected placement" in
                       str(x.proto) for x in at.error)
        else:
            assert out["optimal_proven"] is True
            assert result["metrics"]["status"] == "optimal_exhaustive"
            assert result["independent"]["original_feasible"]


def test_changing_back_to_local_never_reuses_global_graph_result():
    at = page()
    topology = next(r for r in at.radio if r.label == "Wireless connectivity")
    topology.set_value("Global connectivity · all stations").run()
    at.button(key="mvp_run").click().run()
    assert not at.exception
    graph_fingerprint = at.session_state["mvp_result"]["fingerprint"]
    topology = next(r for r in at.radio if r.label == "Wireless connectivity")
    topology.set_value("Local clusters · original").run()
    assert not at.exception
    assert "mvp_result" not in at.session_state
    at.button(key="mvp_run").click().run()
    assert not at.exception
    local = at.session_state["mvp_result"]
    assert local["fingerprint"] != graph_fingerprint
    assert local["independent"]["selected_local_positions"] == [0, 1, 3, 6, 7]
