"""Actual user-triggered, bounded classical 2x2 sweep execution and safety."""
from __future__ import annotations

from hashlib import sha256
import io
import json
import time
from zipfile import ZipFile

import pytest

from problems.water_quality.experiment_jobs import (
    JobError, Spec, create_job, launch_job, read_job,
)
from problems.water_quality.experiment_sweeps import (
    SCHEMA, SweepSpec, active_sweep_exists, cancel_sweep,
    create_sweep, execute_sweep, export_sweep,
    launch_sweep, list_sweeps, read_sweep, sweep_folder,
)
from prototypes.unified_dashboard.experiment_analysis import (
    load_verified_samples,
)


@pytest.fixture
def store(tmp_path):
    return tmp_path / "operator-store"


def test_sweep_validation_and_independent_two_axes():
    case = SweepSpec()
    cells = case.cells()
    assert len(cells) == 4
    assert [(c["budget_penalty"], c["connectivity_penalty"]) for c in cells] == [
        (2.0, 2.0), (2.0, 12.0), (12.0, 2.0), (12.0, 12.0),
    ]
    assert len({v["derived_parent_seed"] for v in cells}) == 4
    assert cells == SweepSpec.from_dict(case.as_dict()).cells()
    for data in (
        {"reads_per_cell": 256}, {"sweeps_per_read": 100000},
        {"budget_levels": (2.0, 2.0)},
        {"connectivity_levels": (12.0, float("nan"))},
        {"parent_seed": -1}, {"k_new": 0},
        {"budget_levels": (1.0,)},
    ):
        with pytest.raises(JobError):
            SweepSpec(**{**case.as_dict(), **data}).validate()
    with pytest.raises(JobError):
        SweepSpec.from_dict({**case.as_dict(), "worker_command": "/bin/sh"})


def test_cancel_before_first_cell_produces_no_false_results(store):
    ident = create_sweep(SweepSpec(), root=store)
    assert active_sweep_exists(root=store)
    assert cancel_sweep(ident, root=store)
    state = execute_sweep(ident, root=store)
    assert state["status"] == "cancelled"
    assert state["completed_cells"] == 0
    assert list_sweeps(root=store)[0]["state"]["status"] == "cancelled"
    assert not active_sweep_exists(root=store)
    with pytest.raises(JobError, match="Only a completed"):
        export_sweep(ident, root=store)


def test_genuine_four_cell_experiment_keeps_every_state_and_full_child_zip(store):
    ident = create_sweep(SweepSpec(
        k_new=5, reads_per_cell=1, sweeps_per_read=10,
        budget_levels=(2.0, 12.0), connectivity_levels=(3.0, 17.0),
        parent_seed=232323,
    ), root=store)
    outcome = execute_sweep(ident, root=store)
    assert outcome["status"] == "completed", outcome
    record = read_sweep(ident, root=store)
    results = record["result"]
    assert results["schema"] == SCHEMA
    assert results["total_sampled_states"] == 4
    assert not results["statistical_significance_or_optimal_penalty_claimed"]
    assert not results["quantum_executed"]
    assert len(results["observations"]) == 4
    assert len({r["derived_parent_seed"] for r in results["observations"]}) == 4
    assert len({r["exact_model_sha256"] for r in results["observations"]}) == 1
    assert [r["cell_index"] for r in results["observations"]] == [0, 1, 2, 3]
    for result in results["observations"]:
        child = result["child_job_id"]
        assert read_job(child, root=store)["status"] == "completed"
        assert result["sample_count"] == 1
        assert len(load_verified_samples(child, root=store)) == 1
        assert 0 <= result["feasible_count"] <= result["sample_count"]
    packed = export_sweep(ident, root=store)
    with ZipFile(io.BytesIO(packed)) as zipped:
        names = zipped.namelist()
        assert {"config.json", "result.json", "cells.csv", "manifest.json"} <= set(names)
        assert sum(name.startswith("cell-") and name.endswith(".zip") for name in names) == 4
        manifest = json.loads(zipped.read("manifest.json"))
        for filename, digest in manifest["file_sha256"].items():
            assert sha256(zipped.read(filename)).hexdigest() == digest
        assert len(zipped.read("cells.csv").splitlines()) == 5
    # Even changed raw ZIP bytes must not survive the sweep manifest check.
    first = results["observations"][0]
    original = sweep_folder(store, ident) / (
        f"cell-{first['cell_index']}-{first['child_job_id']}.zip"
    )
    original.write_bytes(original.read_bytes() + b"MODIFIED")
    with pytest.raises(JobError, match="SHA256"):
        export_sweep(ident, root=store)


def test_one_local_lock_blocks_standalone_job_while_sweep_is_active(monkeypatch, store):
    monkeypatch.setenv("QOPT_LOCAL_EXPERIMENTS", "1")
    queued = create_sweep(SweepSpec(), root=store)
    with pytest.raises(JobError, match="already active"):
        launch_job(Spec(), root=store)
    assert cancel_sweep(queued, root=store)
    assert execute_sweep(queued, root=store)["status"] == "cancelled"
    create_job(Spec(), root=store)
    with pytest.raises(JobError, match="already active"):
        launch_sweep(SweepSpec(), root=store)


def test_actual_local_detached_sweep_worker_completes_all_four_cells(monkeypatch, store):
    monkeypatch.setenv("QOPT_LOCAL_EXPERIMENTS", "1")
    sweep_id = launch_sweep(SweepSpec(
        reads_per_cell=1, sweeps_per_read=10, parent_seed=2266001
    ), root=store)
    deadline = time.monotonic() + 45
    status = "queued"
    while time.monotonic() < deadline:
        record = read_sweep(sweep_id, root=store)
        status = record["state"]["status"]
        if status in ("completed", "failed", "cancelled"):
            break
        time.sleep(.2)
    assert status == "completed", (
        status, (sweep_folder(store, sweep_id) / "worker.log").read_text()
    )
    assert read_sweep(sweep_id, root=store)["result"]["total_sampled_states"] == 4
    assert len(export_sweep(sweep_id, root=store)) > 1000
