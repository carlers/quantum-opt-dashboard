"""Streamlit actual UI must hide tampered current map/site export before rerender.

Unlike pure unit tests, these alter the real session's result after a genuine
SCIP/exact enumeration solve and then rerun the actual app code.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_local_current_scip_zip_mutation_hides_current_result_and_download():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not at.exception, at.exception
    at.button(key="mvp_run").click().run()
    assert not at.exception, at.exception
    current = at.session_state["mvp_result"]
    assert current["attestation"]["strictly_bound_to_compiled_current_run"] is True
    current["zip"] = current["zip"] + b"post-solver-corruption"
    at.session_state["mvp_result"] = current
    at.run()
    assert not at.exception, at.exception
    assert "mvp_result" not in at.session_state
    assert not [x for x in at.metric if x.label == "Original objective (min.)"]
    assert not [x for x in at.button if x.key == "mvp_download"]
    assert any("Inputs changed" in str(x.proto) for x in at.info)


def test_global_current_optimality_status_mutation_hides_map_and_download():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not at.exception, at.exception
    next(x for x in at.radio if x.label == "Wireless connectivity").set_value(
        "Global connectivity · all stations"
    ).run()
    assert not at.exception, at.exception
    at.button(key="mvp_run").click().run()
    assert not at.exception, at.exception
    current = at.session_state["mvp_result"]
    assert current["metrics"]["status"] == "optimal_exhaustive"
    current["metrics"]["status"] = "time_limit_no_certified_optimum"
    at.session_state["mvp_result"] = current
    at.run()
    assert not at.exception, at.exception
    assert "mvp_result" not in at.session_state
    assert not [x for x in at.metric if x.label == "Original objective (min.)"]
    assert not [x for x in at.button if x.key == "mvp_download"]
    assert any("Inputs changed" in str(x.proto) for x in at.info)


def test_mutated_independent_score_and_selected_table_are_not_rendered():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not at.exception, at.exception
    at.button(key="mvp_run").click().run()
    assert not at.exception, at.exception
    current = at.session_state["mvp_result"]
    assert current["independent"]["selected_local_positions"] == [0, 1, 3, 6, 7]
    current["independent"]["independent_original_objective"] -= 1000.
    current["independent"]["selected_master_feature_positions"][0] = 999999
    at.session_state["mvp_result"] = current
    at.run()
    assert not at.exception, at.exception
    assert "mvp_result" not in at.session_state
    assert not [x for x in at.metric if x.label == "Original objective (min.)"]
    assert any("Inputs changed" in str(x.proto) for x in at.info)
