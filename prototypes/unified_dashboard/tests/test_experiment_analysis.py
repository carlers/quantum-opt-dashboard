"""Source-grounded analysis and comparisons of user-launched local experiments."""
from __future__ import annotations

from hashlib import sha256
import io
import json
from pathlib import Path
import time
from zipfile import ZipFile

import pytest

from problems.water_quality.experiment_jobs import (
    JobError, Spec, create_job, execute_job, launch_job, read_job,
)
from prototypes.unified_dashboard.experiment_analysis import (
    compare_completed_jobs, load_verified_samples,
)


@pytest.fixture
def root(tmp_path):
    return tmp_path / "source-research-history"


def run(root, **settings):
    job_id = create_job(Spec(**settings), root=root)
    state = execute_job(job_id, root=root)
    assert state["status"] == "completed", state
    return job_id


def test_read_only_analysis_checks_every_original_sample_and_compares_same_model(root):
    first = run(root, solver="classical_sa", reads=2, sweeps=40,
                lambda_budget=2.0, lambda_connectivity=12.0)
    second = run(root, solver="classical_sa", reads=2, sweeps=40,
                 lambda_budget=12.0, lambda_connectivity=2.0)
    a = load_verified_samples(first, root=root)
    b = load_verified_samples(second, root=root)
    assert len(a) == len(b) == 2
    assert [x["Read"] for x in a] == [0, 1]
    assert len({x["Child seed"] for x in a}) == 2
    assert all(x["Selected count"] >= 0 for x in a + b)
    compared = compare_completed_jobs([first, second], root=root)
    assert compared["same_original_model_verified"] is True
    assert compared["statistical_inference_or_optimal_penalty_claimed"] is False
    assert len(compared["observations"]) == 2
    assert compared["observations"][0]["λ budget"] == 2.0
    assert compared["observations"][1]["λ connectivity"] == 2.0
    for item in compared["observations"]:
        assert 0 <= item["Original-feasible count"] <= item["Reads"] == 2
        assert 0 <= item["Original-feasible fraction"] <= 1
        assert not item["SCIP proven optimal"]


def test_reject_incomparable_N_K_even_though_same_geojson(root):
    a = run(root, solver="scip", n_free=20, k_new=5)
    b = run(root, solver="scip", n_free=20, k_new=4)
    with pytest.raises(JobError, match="different models"):
        compare_completed_jobs([a, b], root=root)
    with pytest.raises(JobError, match="2"):
        compare_completed_jobs([a], root=root)
    with pytest.raises(JobError, match="distinct"):
        compare_completed_jobs([a, a], root=root)


def test_semantically_fake_sample_energy_rejected_even_if_attacker_rehashes_manifest(root):
    job_id = run(root, solver="classical_sa", reads=2, sweeps=40)
    assert len(load_verified_samples(job_id, root=root)) == 2
    folder = root / job_id
    file = folder / "samples.csv"
    original = file.read_text()
    # Original source objective tampered with while retaining CSV integrity.
    import csv
    rows = list(csv.DictReader(io.StringIO(original)))
    rows[0]["original_objective"] = "123456.0"
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    file.write_text(output.getvalue())
    manifest_file = folder / "manifest.json"
    manifest = json.loads(manifest_file.read_text())
    manifest["sha256"]["samples.csv"] = sha256(file.read_bytes()).hexdigest()
    manifest_file.write_text(json.dumps(manifest))
    with pytest.raises(JobError, match="independent archived-original-model"):
        load_verified_samples(job_id, root=root)


def test_missing_or_corrupted_model_is_not_accepted_for_comparison(root):
    a = run(root, solver="scip")
    b = run(root, solver="scip")
    assert compare_completed_jobs([a, b], root=root)["same_original_model_verified"]
    (root / a / "model.json").write_text("{}")
    with pytest.raises(JobError, match="checksum"):
        compare_completed_jobs([a, b], root=root)


def test_actual_detached_subprocess_completes_a_locally_requested_small_job(
    monkeypatch, root
):
    monkeypatch.setenv("QOPT_LOCAL_EXPERIMENTS", "1")
    # Uses the real subprocess API, not a monkeypatched fake worker.
    ident = launch_job(Spec(solver="classical_sa", reads=1, sweeps=10), root=root)
    deadline = time.monotonic() + 30
    status = "queued"
    while time.monotonic() < deadline:
        status = read_job(ident, root=root)["status"]
        if status in ("completed", "failed", "cancelled"):
            break
        time.sleep(.2)
    assert status == "completed", (status, (root / ident / "worker.log").read_text())
    rows = load_verified_samples(ident, root=root)
    assert len(rows) == 1
