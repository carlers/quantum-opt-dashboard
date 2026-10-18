"""Guard against accidental loss or accidental PR-wide reruns of science (#34).

Uses YAML BaseLoader so the YAML 1.1 implicit-boolean "on" pitfall cannot
incorrectly parse the GitHub Actions event specification as True.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".github" / "workflows"


def _workflow(path):
    raw = (WORKFLOWS / path).read_text(encoding="utf-8")
    contents = yaml.load(raw, Loader=yaml.BaseLoader)
    assert isinstance(contents, dict)
    return contents, raw


def _runs(step_list):
    return "\n".join(str(s.get("run", "")) for s in step_list)


def test_fast_gate_runs_every_real_unit_and_streamlit_smoke_test():
    fast, raw = _workflow("streamlit-pilot.yml")
    assert set(fast["on"]) == {"pull_request", "push"}
    assert "prototypes/streamlit_water_quality/**" in fast["on"]["pull_request"]["paths"]
    assert ".github/workflows/streamlit-pilot.yml" in fast["on"]["pull_request"]["paths"]
    assert ".github/workflows/streamlit-research-evidence.yml" in fast["on"]["pull_request"]["paths"]
    assert fast["on"]["push"]["branches"] == ["plugin-water-streamlit-pilot"]
    job = fast["jobs"]["model-tests"]
    steps = job["steps"]
    executed = _runs(steps)
    assert "python -m pytest prototypes/streamlit_water_quality/tests -q -s" in executed
    assert "python -m compileall" in executed
    assert "test_inspector_app_smoke" not in executed  # no exclusions
    assert "requirements.txt" in executed
    assert "openjij==0.12.2" in executed
    assert job["timeout-minutes"] == "15"
    # A UI-only edit must never trigger all 3072+4096 stochastic draws.
    for command in ("sa_paired_replication.py", "sa_ulp_replay.py",
                    "sa_benchmark.py", "evidence.py", "precision_probe.py"):
        assert command not in executed
    assert "uses: actions/upload-artifact" not in raw


def test_research_gate_retains_every_frozen_protocol_and_auditable_archive():
    workflow, raw = _workflow("streamlit-research-evidence.yml")
    assert set(workflow["on"]) == {"pull_request", "workflow_dispatch"}
    paths = workflow["on"]["pull_request"]["paths"]
    for dependency in (
        "prototypes/streamlit_water_quality/model.py",
        "prototypes/streamlit_water_quality/qubo.py",
        "prototypes/streamlit_water_quality/formulation_audit.py",
        "prototypes/streamlit_water_quality/evidence.py",
        "prototypes/streamlit_water_quality/sa_benchmark.py",
        "prototypes/streamlit_water_quality/sa_paired_replication.py",
        "prototypes/streamlit_water_quality/sa_ulp_replay.py",
        "prototypes/streamlit_water_quality/precision_probe.py",
        "prototypes/streamlit_water_quality/compare_archived_sa.py",
        "prototypes/streamlit_water_quality/requirements.txt",
        "problems/water_quality/data/**",
        "problems/water_quality/notebooks/**",
        ".github/workflows/streamlit-research-evidence.yml",
    ):
        assert dependency in paths
    # No broad prototype/** match: UI styling should not rerun frozen research.
    assert "prototypes/streamlit_water_quality/**" not in paths
    assert "prototypes/streamlit_water_quality/app.py" not in paths
    job = workflow["jobs"]["frozen-research-evidence"]
    assert job["timeout-minutes"] == "30"
    steps = job["steps"]
    executed = _runs(steps)
    for source in (
        "evidence.py", "sa_benchmark.py", "sa_paired_replication.py",
        "precision_probe.py", "sa_ulp_replay.py",
    ):
        assert source in executed
    assert "openjij==0.12.2" in executed
    assert "python -m pytest" in executed
    artifacts = [
        step["with"] for step in steps
        if step.get("uses", "").startswith("actions/upload-artifact@")
    ]
    assert len(artifacts) == 5
    assert {a["name"] for a in artifacts} == {
        "n20-scip-evidence", "n20-openjij-sa-benchmark",
        "n20-sa-paired-replication", "n20-precision-probe",
        "n20-ulp-controlled-replay",
    }
    assert all(a["if-no-files-found"] == "error" for a in artifacts)
    assert all(a["retention-days"] == "14" for a in artifacts)
    assert "github.event.pull_request.head.sha || github.sha" in raw


def test_research_workflow_is_bounded_and_cannot_write_to_live_branch():
    fast, _ = _workflow("streamlit-pilot.yml")
    science, _ = _workflow("streamlit-research-evidence.yml")
    assert fast["permissions"] == {"contents": "read"}
    assert science["permissions"] == {"contents": "read"}
    assert science["concurrency"]["cancel-in-progress"] == "true"
    assert "push" not in science["on"]
    for _, workflow in (("fast", fast), ("science", science)):
        for job in workflow["jobs"].values():
            steps = _runs(job["steps"])
            assert "git push" not in steps
            assert "streamlit deploy" not in steps
            assert "gh release create" not in steps
