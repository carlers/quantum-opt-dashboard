"""Researcher-controlled local job runner: real SCIP/SA, fail-closed stores and UI."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile
import io

import pytest
from streamlit.testing.v1 import AppTest

from problems.water_quality.experiment_jobs import (
    SOURCE_SHA256, Cancelled, JobError, Spec, check_cancel, create_job,
    execute_job, export_bundle, job_dir, launch_job, list_jobs, local_opt_in,
    read_job, request_cancel,
)

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def store(tmp_path):
    return tmp_path / "research-store"


def test_disabled_by_default_and_schemas_fail_closed(monkeypatch, store):
    monkeypatch.delenv("QOPT_LOCAL_EXPERIMENTS", raising=False)
    assert local_opt_in() is False
    with pytest.raises(JobError, match="disabled"):
        launch_job(Spec(), root=store)
    for overrides in (
        {"solver": "__shell__"}, {"n_free": 1000}, {"k_new": 0},
        {"time_limit_seconds": 10000}, {"reads": 512},
        {"sweeps": 1000000}, {"parent_seed": -1},
        {"lambda_budget": float("nan")},
        {"lambda_connectivity": -2},
        {"solver": "classical_sa", "n_free": 100},
    ):
        with pytest.raises(JobError):
            replace(Spec(), **overrides).validate()
    with pytest.raises(JobError):
        Spec.from_dict({**Spec().manifest(), "command": "rm -rf /"})
    for malicious in ("../other", "0" * 31, "a" * 32 + "/secret"):
        with pytest.raises(JobError, match="identifier"):
            job_dir(store, malicious)


def test_job_creation_persists_immutable_user_config_without_running_solver(store):
    ident = create_job(Spec(), root=store)
    job = read_job(ident, root=store)
    assert job["status"] == "queued"
    assert job["config"]["source_sha256"] == SOURCE_SHA256
    assert job["config"]["configuration"] == Spec().manifest()
    assert job["state"]["total_reads"] == 1
    assert not (store / ident / "result.json").exists()
    assert [j["job_id"] for j in list_jobs(root=store)] == [ident]


def test_operator_cancellation_does_not_fake_success(store):
    ident = create_job(Spec(solver="classical_sa", reads=3), root=store)
    assert request_cancel(ident, root=store)
    with pytest.raises(Cancelled):
        check_cancel(store / ident)
    final = execute_job(ident, root=store)
    assert final["status"] == "cancelled"
    assert final["completed_reads"] == 0
    assert read_job(ident, root=store)["result"] is None
    with pytest.raises(JobError, match="Only complete"):
        export_bundle(ident, root=store)
    assert request_cancel(ident, root=store) is False


def test_real_original_source_n20_scip_worker_and_hash_checked_zip(store):
    ident = create_job(Spec(), root=store)
    final = execute_job(ident, root=store)
    assert final["status"] == "completed", final
    job = read_job(ident, root=store)
    assert job["status"] == "completed"
    solver = job["result"]["result"]
    assert solver["solver"].startswith("SCIP")
    assert solver["scip_status"] == "optimal"
    assert solver["scip_proven_optimal"] is True
    assert solver["source_selection"]["selected_local_positions"] == [0, 1, 3, 6, 7]
    assert solver["source_selection"]["selected_source_master_positions"] == [
        5253, 2394, 1557, 47, 5409
    ]
    assert solver["source_selection"]["energy"] == pytest.approx(-3.3012934918564643, abs=1e-7)
    zipped = export_bundle(ident, root=store)
    with ZipFile(io.BytesIO(zipped)) as bundle:
        expected = {"config.json", "model.json", "result.json", "emitted_scip_model.lp", "manifest.json"}
        assert set(bundle.namelist()) == expected
        manifest = json.loads(bundle.read("manifest.json"))
        for name, digest in manifest["sha256"].items():
            assert sha256(bundle.read(name)).hexdigest() == digest
        exported_lp = bundle.read("emitted_scip_model.lp")
        assert len(exported_lp) > 1000
        assert b"Minimize" in exported_lp
        assert b"Subject to" in exported_lp
        assert b"Binaries" in exported_lp
        assert b"budget:" in exported_lp
    path = store / ident / "result.json"
    path.write_text(path.read_text() + "changed")
    with pytest.raises(JobError, match="changed"):
        export_bundle(ident, root=store)


def test_real_two_read_classical_sa_retains_feasible_and_infeasible_states(store):
    ident = create_job(Spec(solver="classical_sa", reads=2, sweeps=50,
                            parent_seed=20261026,
                            lambda_budget=12.9, lambda_connectivity=15.2), root=store)
    done = execute_job(ident, root=store)
    assert done["status"] == "completed", done
    job = read_job(ident, root=store)
    result = job["result"]["result"]
    assert result["solver"].startswith("classical OpenJij")
    assert result["total_samples"] == 2
    assert 0 <= result["feasible_count"] <= 2
    assert 0 <= result["feasible_fraction"] <= 1
    assert result["penalties"] == {"budget": 12.9, "connectivity": 15.2}
    assert result["exact_N20_reference_objective_if_applicable"] == pytest.approx(
        -3.3012934918564643
    )
    with ZipFile(io.BytesIO(export_bundle(ident, root=store))) as bundle:
        rows = bundle.read("samples.csv").decode("utf-8").splitlines()
        assert len(rows) == 3
        assert "full_original_and_auxiliary_bits" in rows[0]
        manifest = json.loads(bundle.read("manifest.json"))
        assert sha256(bundle.read("samples.csv")).hexdigest() == manifest["sha256"]["samples.csv"]
        source = json.loads(bundle.read("model.json"))
        assert source["source_sha256"] == SOURCE_SHA256


def test_unsafe_multi_job_launch_and_no_shell(monkeypatch, store):
    monkeypatch.setenv("QOPT_LOCAL_EXPERIMENTS", "1")
    spawned = []
    class FakeProc:
        def __init__(self, args, **kw):
            spawned.append((args, kw))
    monkeypatch.setattr("problems.water_quality.experiment_jobs.subprocess.Popen", FakeProc)
    ident = launch_job(Spec(), root=store)
    assert len(spawned) == 1
    args, kw = spawned[0]
    assert args[:3] == [__import__("sys").executable, "-m",
                       "problems.water_quality.experiment_jobs"]
    assert args[-2:] == ["--root", str(store.resolve())]
    assert kw["start_new_session"] is True
    assert kw["env"]["OPENBLAS_NUM_THREADS"] == "1"
    with pytest.raises(JobError, match="already running"):
        launch_job(Spec(), root=store)
    assert read_job(ident, root=store)["status"] == "queued"


def test_page_disabled_by_default_never_starts_unbounded_background_worker(monkeypatch):
    monkeypatch.delenv("QOPT_LOCAL_EXPERIMENTS", raising=False)
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception, app.exception
    app.switch_page("pages/experiments.py").run()
    assert not app.exception, app.exception
    assert any("Experiment workbench" in x.value for x in app.title)
    assert any("disabled by default" in str(i.proto) for i in app.info)
    assert not any("Launch bounded experiment" in x.label for x in app.button)
    assert "local_selected_experiment" not in app.session_state
