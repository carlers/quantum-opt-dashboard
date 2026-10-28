"""Private SQLite queue contract: ownership, fencing, cancellation and real SCIP."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from problems.water_quality.experiment_jobs import (
    JobError, Spec, execute_job, export_bundle, job_dir, read_job,
)
from problems.water_quality.remote_queue import (
    MAX_PER_OWNER_ACTIVE, PrivateQueue, QueueError, Claim,
)


@pytest.fixture
def queue(tmp_path):
    return PrivateQueue(
        database=tmp_path / "private" / "queue.sqlite3",
        root=tmp_path / "experiments",
    )


def test_owner_scope_and_reject_unverified_principals(queue):
    job_id = queue.submit("researcher-A", Spec())
    assert queue.get("researcher-A", job_id)["status"] == "queued"
    assert queue.get("researcher-B", job_id) is None
    assert queue.list_for_owner("researcher-B") == []
    assert [row["job_id"] for row in queue.list_for_owner("researcher-A")] == [job_id]
    with pytest.raises(QueueError, match="principal"):
        queue.submit("../forged", Spec())
    with pytest.raises(QueueError, match="not found"):
        queue.request_cancellation("researcher-B", job_id)
    with pytest.raises(QueueError, match="Invalid experiment"):
        queue.get("researcher-A", "../../etc/passwd")
    assert queue.database.stat().st_mode & 0o077 == 0
    assert queue.root.stat().st_mode & 0o077 == 0


def test_single_claim_survives_new_process_handle_and_fences_tokens(queue):
    first = queue.submit("a", Spec())
    second = queue.submit("b", Spec(solver="classical_sa", reads=1, sweeps=10))
    claimed = queue.claim_next()
    assert claimed.job_id == first
    assert len(claimed.token) == 64
    second_handle = PrivateQueue(database=queue.database, root=queue.root)
    assert second_handle.claim_next() is None  # No concurrent second worker.
    with pytest.raises(QueueError, match="lease"):
        queue.heartbeat(Claim(first, "0" * 64))
    queue.heartbeat(claimed)
    result = execute_job(first, root=queue.root)
    assert result["status"] == "completed"
    assert second_handle.finish(claimed) == "completed"
    assert queue.get("a", first)["status"] == "completed"
    assert queue.claim_next().job_id == second


def test_queued_cancel_never_runs_and_owner_cannot_cancel_other_queue(queue):
    first = queue.submit("alice", Spec())
    assert queue.request_cancellation("alice", first)
    assert queue.get("alice", first)["status"] == "cancelled"
    assert read_job(first, root=queue.root)["status"] == "cancelled"
    assert queue.claim_next() is None
    assert not queue.request_cancellation("alice", first)
    with pytest.raises(QueueError):
        queue.request_cancellation("bob", first)


def test_active_cancel_propagates_to_real_worker(queue):
    job_id = queue.submit("alice", Spec(solver="classical_sa", reads=2, sweeps=10))
    claim = queue.claim_next()
    assert claim.job_id == job_id
    assert queue.request_cancellation("alice", job_id)
    assert (job_dir(queue.root, job_id) / "cancel.request").is_file()
    state = execute_job(job_id, root=queue.root)
    assert state["status"] == "cancelled"
    assert queue.finish(claim) == "cancelled"
    assert queue.get("alice", job_id)["cancel_requested"] == 1


def test_lost_lease_never_reclaims_or_duplicates_job(queue):
    first = queue.submit("alice", Spec())
    queue.submit("bob", Spec())
    claim = queue.claim_next()
    assert claim.job_id == first
    with sqlite3.connect(queue.database) as conn:
        conn.execute(
            "UPDATE research_jobs SET lease_until=0 WHERE job_id=?", (first,)
        )
    assert queue.claim_next() is None  # Fail closed until human intervention.
    audit = queue.audit_stalled()
    assert len(audit) == 1
    assert audit[0]["job_id"] == first
    assert audit[0]["manual_review_required"] is True
    assert audit[0]["worker_state"] == "queued"
    with pytest.raises(QueueError, match="lease"):
        queue.heartbeat(claim)
    execute_job(first, root=queue.root)
    with pytest.raises(QueueError, match="lease"):
        queue.finish(claim)
    assert queue.claim_next() is None


def test_bounded_per_owner_submission(queue):
    for _ in range(MAX_PER_OWNER_ACTIVE):
        queue.submit("alice", Spec())
    with pytest.raises(QueueError, match="capacity"):
        queue.submit("alice", Spec())
    # Another independent principal is still allowed within the global bound.
    queue.submit("bob", Spec())
    with pytest.raises(JobError, match="source-validated"):
        queue.submit("bob", Spec(n_free=2000))


def test_completion_requires_original_sha256_evidence(queue):
    job_id = queue.submit("alice", Spec())
    claim = queue.claim_next()
    assert execute_job(job_id, root=queue.root)["status"] == "completed"
    (job_dir(queue.root, job_id) / "result.json").write_text("{}")
    with pytest.raises(JobError, match="changed"):
        queue.finish(claim)
    assert queue.get("alice", job_id)["status"] == "running"


def test_real_explicit_subprocess_dispatch_and_persistent_evidence(queue):
    job_id = queue.submit("alice", Spec())
    outcome = queue.run_once(wall_seconds=60)
    assert outcome == (job_id, "completed")
    assert queue.get("alice", job_id)["status"] == "completed"
    assert read_job(job_id, root=queue.root)["result"] is not None
    assert len(export_bundle(job_id, root=queue.root)) > 1000
    assert queue.run_once() is None


def test_fail_closed_on_existing_public_sqlite_database(tmp_path):
    path = tmp_path / "queue.sqlite3"
    path.write_bytes(b"")
    path.chmod(0o644)
    with pytest.raises(QueueError, match="unsafe permissions"):
        PrivateQueue(database=path, root=tmp_path / "jobs")
