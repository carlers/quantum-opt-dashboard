"""Guard that fast integrated MVP regression and full research runs are distinct.

The heavy N20 SA/ULP protocols remain available for manual scientific runs
but cannot unintentionally execute on a broad integration PR.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".github" / "workflows"


def workflow(name):
    return yaml.load((WORKFLOWS / name).read_text(), Loader=yaml.BaseLoader)


def commands(job):
    return "\n".join(str(x.get("run", "")) for x in job["steps"])


def test_integrated_fast_gate_runs_scip_ui_qubo_and_app_tests_without_long_sampling():
    fast = workflow("streamlit-pilot.yml")
    assert "pull_request" in fast["on"]
    paths = fast["on"]["pull_request"]["paths"]
    assert "prototypes/streamlit_water_quality/**" in paths
    assert "prototypes/unified_dashboard/**" in paths
    assert ".github/workflows/streamlit-research-evidence.yml" in paths
    job = fast["jobs"]["model-tests"]
    assert job["timeout-minutes"] == "15"
    cmd = commands(job)
    assert "python -m pytest prototypes/streamlit_water_quality/tests prototypes/unified_dashboard/tests -q -s" in cmd
    assert "python -m pip install -r requirements.txt" in cmd
    assert "compileall" in cmd
    for forbidden in ("sa_paired_replication.py", "sa_ulp_replay.py",
                      "sa_benchmark.py --output", "precision_probe.py --output"):
        assert forbidden not in cmd
    assert fast["permissions"] == {"contents": "read"}


def test_heavy_research_still_available_explicitly_with_same_frozen_protocols():
    research = workflow("streamlit-research-evidence.yml")
    assert set(research["on"]) == {"workflow_dispatch"}
    assert research["permissions"] == {"contents": "read"}
    job = research["jobs"]["frozen-research-evidence"]
    assert job["timeout-minutes"] == "30"
    cmd = commands(job)
    for script in ("evidence.py", "sa_benchmark.py", "sa_paired_replication.py",
                   "precision_probe.py", "sa_ulp_replay.py"):
        assert script in cmd
    assert "openjij==0.12.2" in cmd
    uploads = [x["with"] for x in job["steps"] if
               x.get("uses", "").startswith("actions/upload-artifact@")]
    assert len(uploads) == 5
    assert all(x["retention-days"] == "14" for x in uploads)
    assert all(x["if-no-files-found"] == "error" for x in uploads)
    assert "push" not in research["on"]


def test_neither_workflow_can_modify_production_or_deploy():
    for filename in ("streamlit-pilot.yml", "streamlit-research-evidence.yml"):
        workflow_data = workflow(filename)
        assert workflow_data["permissions"]["contents"] == "read"
        for job in workflow_data["jobs"].values():
            cmd = commands(job)
            for forbidden in ("git push", "streamlit deploy", "gh release create"):
                assert forbidden not in cmd
