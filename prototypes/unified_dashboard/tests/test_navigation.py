"""Single-entrypoint MVP: navigation reaches all three real research experiences."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def startup():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception
    return app


def test_unified_opens_source_pinned_water_problem_and_preserves_scip_run():
    app = startup()
    assert any("Water-quality sensor placement" in item.value for item in app.title)
    assert any("Understand the current model" in item.value for item in app.subheader)
    assert not app.session_state.get("mvp_result")
    app.button(key="mvp_run").click().run()
    assert not app.exception
    outcome = app.session_state["mvp_result"]
    assert outcome["metrics"]["status"] == "optimal"
    assert outcome["independent"]["selected_local_positions"] == [0, 1, 3, 6, 7]
    assert outcome["zip"]


def test_unified_custom_models_page_renders_existing_configurable_workbench():
    app = startup().switch_page("pages/custom.py").run()
    assert not app.exception
    assert any("Configurable Optimization Workbench" in item.value for item in app.title)
    assert any(s.label == "Example problem" for s in app.selectbox)
    assert any(s.label == "Mathematical formulation" for s in app.selectbox)
    # No cross-page automatic solver execution.
    assert not app.session_state.get("completed_run")


def test_unified_research_inspector_is_safe_before_manual_classical_run():
    app = startup().switch_page("pages/research.py").run()
    assert not app.exception
    assert any("QUBO and classical annealing" in item.value for item in app.title)
    assert any(item.label == "Original binary variables" for item in app.metric)
    assert any("Classical" in item.label or "classical" in item.label
               for item in app.button)
    assert not app.session_state.get("unified_sa_run")
    assert any("QUBO inspection is available now" in str(item.proto)
               for item in app.info)


def test_unified_about_preserves_scientific_limitations():
    app = startup().switch_page("pages/about.py").run()
    assert not app.exception
    assert any("About the scientific workbench" in item.value for item in app.title)
    assert not app.exception


def test_bounded_classical_sampler_reports_seeded_original_feasibility():
    app = startup().switch_page("pages/research.py").run()
    assert not app.exception
    samples = next(item for item in app.slider
                   if item.label == "Independent samples per run")
    samples.set_value(2).run()
    button = next(item for item in app.button
                  if item.label == "Run bounded classical simulated annealing")
    button.click().run()
    assert not app.exception
    record = app.session_state["unified_sa_run"]["result"]
    assert record["algorithm"] == "OpenJij SASampler, not quantum hardware"
    assert record["num_reads"] == 2
    assert len(record["child_seeds"]) == 2
    assert record["summary"]["sample_count"] == 2
    assert record["summary"]["feasible_sample_count"] <= 2
