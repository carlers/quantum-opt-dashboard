"""Evidence-staging contract: no overwrite, private ZIPs, independent restore."""
from __future__ import annotations

from hashlib import sha256
import io
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import pytest

from problems.water_quality.evidence_archive import (
    EvidenceError, inspect_bundle, restore_drill, stage_completed, verify_staged,
)
from problems.water_quality.experiment_jobs import Spec, canonical, export_bundle
from problems.water_quality.remote_queue import PrivateQueue


@pytest.fixture
def queue(tmp_path):
    return PrivateQueue(
        database=tmp_path / "db" / "queue.sqlite3",
        root=tmp_path / "jobs",
    )


@pytest.fixture
def completed(queue):
    job_id = queue.submit("trusted-researcher", Spec())
    assert queue.run_once(wall_seconds=60) == (job_id, "completed")
    return job_id


def test_verified_stage_and_offline_restore_drill(queue, completed, tmp_path):
    destination = tmp_path / "archive-stage"
    staged = stage_completed(queue, job_id=completed, destination=destination)
    assert staged["verified"] is True
    assert staged["source_sha256"].startswith("e303cce3")
    assert 0 < staged["archive_size"] < 5_000_000
    assert (destination.stat().st_mode & 0o077) == 0

    zip_path = destination / (completed + ".zip")
    index_path = destination / (completed + ".sha256.json")
    assert (zip_path.stat().st_mode & 0o077) == 0
    assert (index_path.stat().st_mode & 0o077) == 0
    assert zip_path.read_bytes() == export_bundle(completed, root=queue.root)
    assert verify_staged(destination=destination, job_id=completed) == staged

    restored = tmp_path / "standalone-restore"
    names = restore_drill(destination=destination, job_id=completed, into=restored)
    assert {"config.json", "model.json", "result.json", "manifest.json"}.issubset(names)
    assert (restored.stat().st_mode & 0o077) == 0
    assert all((restored / name).stat().st_mode & 0o077 == 0 for name in names)
    result = json.loads((restored / "result.json").read_text())
    assert result["result"]["source_selection"]["selected_source_master_positions"] == [
        5253, 2394, 1557, 47, 5409
    ]
    with pytest.raises(EvidenceError, match="already exists"):
        restore_drill(destination=destination, job_id=completed, into=restored)


def test_stage_never_overwrites_existing_evidence(queue, completed, tmp_path):
    destination = tmp_path / "private-stage"
    first = stage_completed(queue, job_id=completed, destination=destination)
    with pytest.raises(EvidenceError, match="never overwrite"):
        stage_completed(queue, job_id=completed, destination=destination)
    assert verify_staged(destination=destination, job_id=completed) == first


def test_staging_refuses_queued_or_invalid_job(queue, tmp_path):
    pending = queue.submit("alice", Spec())
    with pytest.raises(EvidenceError, match="Only completed"):
        stage_completed(queue, job_id=pending, destination=tmp_path / "staged")
    with pytest.raises(EvidenceError, match="Invalid scientific"):
        verify_staged(destination=tmp_path / "staged", job_id="../other")


def test_modified_zip_is_detected(queue, completed, tmp_path):
    destination = tmp_path / "staged"
    stage_completed(queue, job_id=completed, destination=destination)
    archive = destination / (completed + ".zip")
    raw = archive.read_bytes()
    archive.write_bytes(raw[:-3] + b"bad")
    with pytest.raises(EvidenceError):
        verify_staged(destination=destination, job_id=completed)


def test_modified_sidecar_is_detected(queue, completed, tmp_path):
    destination = tmp_path / "staged"
    stage_completed(queue, job_id=completed, destination=destination)
    path = destination / (completed + ".sha256.json")
    index = json.loads(path.read_text())
    index["archive_sha256"] = "0" * 64
    path.write_bytes(canonical(index))
    with pytest.raises(EvidenceError, match="sidecar"):
        verify_staged(destination=destination, job_id=completed)


def test_inner_manifest_mismatch_is_detected_even_with_updated_outer_checksum(
    queue, completed, tmp_path
):
    destination = tmp_path / "staged"
    stage_completed(queue, job_id=completed, destination=destination)
    path = destination / (completed + ".zip")
    sidecar = destination / (completed + ".sha256.json")
    with ZipFile(io.BytesIO(path.read_bytes())) as source:
        members = {name: source.read(name) for name in source.namelist()}
    members["result.json"] += b" "
    output = io.BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as target:
        for name, raw in members.items():
            target.writestr(name, raw)
    path.write_bytes(output.getvalue())
    index = json.loads(sidecar.read_text())
    index["archive_sha256"] = sha256(output.getvalue()).hexdigest()
    index["archive_size"] = len(output.getvalue())
    sidecar.write_bytes(canonical(index))
    with pytest.raises(EvidenceError, match="checksum"):
        verify_staged(destination=destination, job_id=completed)


def test_zip_traversal_and_duplicate_paths_refused(completed, queue):
    original = export_bundle(completed, root=queue.root)
    with ZipFile(io.BytesIO(original)) as src:
        members = {name: src.read(name) for name in src.namelist()}
    for extra in ("../escape", "result.json"):
        out = io.BytesIO()
        with ZipFile(out, "w", ZIP_DEFLATED) as archive:
            for name, value in members.items():
                archive.writestr(name, value)
            archive.writestr(extra, b"bad")
        with pytest.raises(EvidenceError, match="ZIP paths"):
            inspect_bundle(out.getvalue(), job_id=completed)


def test_world_accessible_destination_rejected(queue, completed, tmp_path):
    destination = tmp_path / "public"
    destination.mkdir(mode=0o755)
    destination.chmod(0o755)
    with pytest.raises(EvidenceError, match="private"):
        stage_completed(queue, job_id=completed, destination=destination)
