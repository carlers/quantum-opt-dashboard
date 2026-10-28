"""Private, explicit operator-dispatched SQLite queue for source-verified experiments.

FOUNDATION ONLY: no HTTP routes, user authentication, public listener, remote
submission or daemon. The owner argument is a *trusted authenticated principal*
to be supplied by a future verified API, NEVER a client-provided owner field.

No auto-retry: a dead/expired worker stays 'running' and blocks subsequent
claims until an operator investigates the process and artifacts. This prevents
accidental duplicate native solver execution after lease expiry.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from contextlib import contextmanager
from dataclasses import dataclass
import os
from pathlib import Path
import re
import resource
import secrets
import signal
import sqlite3
import subprocess
import sys
import time

from problems.water_quality.experiment_jobs import (
    JOB_PATTERN, ROOT, SOURCE_SHA256, JobError, Spec, create_job, export_bundle,
    job_dir, read_job, request_cancel, update_state, utc_now, canonical,
)

OWNER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
TERMINAL = frozenset({"completed", "failed", "cancelled"})
MAX_PER_OWNER_ACTIVE = 4
MAX_GLOBAL_ACTIVE = 20
LEASE_SECONDS = 30
MAX_OPERATOR_WALL_SECONDS = 90


class QueueError(JobError):
    """Reject untrusted identity, exhausted capacity, or invalid worker lease."""


@dataclass(frozen=True)
class Claim:
    job_id: str
    token: str  # INTERNAL fencing capability; must never be returned from an API.


def _owner(value: str) -> str:
    if not isinstance(value, str) or OWNER_RE.fullmatch(value) is None:
        raise QueueError("Owner must be a verified, bounded server-side principal")
    return value


def _job_id(value: str) -> str:
    if not isinstance(value, str) or JOB_PATTERN.fullmatch(value) is None:
        raise QueueError("Invalid experiment identifier")
    return value


class PrivateQueue:
    """Transactional FIFO dispatcher with owner scoping and fail-closed leases.

    The database and experiment root must be on a persistent local disk owned
    by the unprivileged service account; do not use a Git checkout or /tmp.
    """

    def __init__(self, *, database: Path, root: Path):
        self.database = Path(database).expanduser().resolve()
        self.root = Path(root).expanduser().resolve()
        if self.database.is_relative_to(self.root):
            raise QueueError("Queue database must live outside the job root")
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.database.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.root.stat().st_mode & 0o077:
            raise QueueError("Experiment store must not be group/world accessible")
        if self.database.exists():
            if not self.database.is_file() or self.database.stat().st_mode & 0o077:
                raise QueueError("Existing queue database has unsafe permissions")
        else:
            # Do not let sqlite's default umask (often 022) create a 0644 DB.
            try:
                fd = os.open(self.database, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
            except FileExistsError as exc:
                raise QueueError("Queue database was created concurrently") from exc
        self._initialize()

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(str(self.database), timeout=10, isolation_level=None)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            yield connection
        finally:
            connection.close()

    @contextmanager
    def _transaction(self):
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.execute("COMMIT")
            except BaseException:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise

    def _initialize(self):
        with self._connection() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS research_jobs (
                  job_id TEXT PRIMARY KEY,
                  owner TEXT NOT NULL,
                  status TEXT NOT NULL CHECK(
                    status IN ('queued','running','completed','failed','cancelled')
                  ),
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  source_sha256 TEXT NOT NULL,
                  cancel_requested INTEGER NOT NULL DEFAULT 0,
                  lease_token TEXT,
                  lease_until REAL,
                  attempts INTEGER NOT NULL DEFAULT 0,
                  idempotency_key TEXT,
                  config_sha256 TEXT
                )
            """)
            # Non-destructive migration for an earlier private foundation DB.
            columns = {r[1] for r in db.execute("PRAGMA table_info(research_jobs)")}
            for col in ("idempotency_key", "config_sha256"):
                if col not in columns:
                    db.execute("ALTER TABLE research_jobs ADD COLUMN " + col + " TEXT")
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS research_owner_idempotency "
                "ON research_jobs(owner, idempotency_key) "
                "WHERE idempotency_key IS NOT NULL"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS research_owner_jobs "
                "ON research_jobs(owner, created_at)"
            )
        if self.database.stat().st_mode & 0o077:
            raise QueueError("Queue database must not be group/world readable")

    def submit(self, owner: str, spec: Spec, *,
               idempotency_key: str | None = None) -> str:
        """Return the first matching job on authenticated, equal-config retries."""
        owner = _owner(owner)
        spec.validate()
        if idempotency_key is not None and (
            type(idempotency_key) is not str
            or re.fullmatch(r"[0-9a-f]{32}", idempotency_key) is None
        ):
            raise QueueError("Invalid Idempotency-Key")
        config_sha256 = sha256(canonical(spec.manifest())).hexdigest()
        with self._transaction() as db:
            if idempotency_key is not None:
                found = db.execute(
                    "SELECT job_id,config_sha256 FROM research_jobs "
                    "WHERE owner=? AND idempotency_key=?",
                    (owner, idempotency_key),
                ).fetchone()
                if found is not None:
                    if found["config_sha256"] != config_sha256:
                        raise QueueError("Idempotency-Key conflicts with existing configuration")
                    return found["job_id"]
            active = db.execute(
                "SELECT COUNT(*) FROM research_jobs WHERE status IN ('queued','running')"
            ).fetchone()[0]
            per_owner = db.execute(
                "SELECT COUNT(*) FROM research_jobs "
                "WHERE owner=? AND status IN ('queued','running')", (owner,)
            ).fetchone()[0]
            if active >= MAX_GLOBAL_ACTIVE or per_owner >= MAX_PER_OWNER_ACTIVE:
                raise QueueError("Private research queue is at capacity")
            # Source-fingerprinted immutable config and job folder are created
            # by the existing independently validated scientific implementation.
            job_id = create_job(spec, root=self.root)
            now = utc_now()
            db.execute(
                "INSERT INTO research_jobs(job_id,owner,status,created_at,updated_at,"
                "source_sha256,idempotency_key,config_sha256) VALUES(?,?,?,?,?,?,?,?)",
                (job_id, owner, "queued", now, now, SOURCE_SHA256,
                 idempotency_key, config_sha256),
            )
        return job_id

    def get(self, owner: str, job_id: str):
        owner, job_id = _owner(owner), _job_id(job_id)
        with self._connection() as db:
            row = db.execute(
                "SELECT job_id,status,created_at,updated_at,cancel_requested,"
                "source_sha256 FROM research_jobs WHERE job_id=? AND owner=?",
                (job_id, owner),
            ).fetchone()
            return dict(row) if row else None

    def list_for_owner(self, owner: str, *, limit: int = 20):
        owner = _owner(owner)
        if type(limit) is not int or not 1 <= limit <= 50:
            raise QueueError("Invalid listing limit")
        with self._connection() as db:
            rows = db.execute(
                "SELECT job_id,status,created_at,updated_at,cancel_requested,"
                "source_sha256 FROM research_jobs WHERE owner=? "
                "ORDER BY created_at DESC, rowid DESC LIMIT ?",
                (owner, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def request_cancellation(self, owner: str, job_id: str) -> bool:
        owner, job_id = _owner(owner), _job_id(job_id)
        with self._transaction() as db:
            row = db.execute(
                "SELECT status FROM research_jobs WHERE owner=? AND job_id=?",
                (owner, job_id),
            ).fetchone()
            if row is None:
                # Same response for missing jobs and another owner's jobs.
                raise QueueError("Experiment not found")
            if row["status"] in TERMINAL:
                return False
            if row["status"] == "queued":
                db.execute(
                    "UPDATE research_jobs SET status='cancelled', "
                    "cancel_requested=1, updated_at=? WHERE job_id=?",
                    (utc_now(), job_id),
                )
                queued = True
            else:
                db.execute(
                    "UPDATE research_jobs SET cancel_requested=1, updated_at=? "
                    "WHERE job_id=?", (utc_now(), job_id),
                )
                queued = False
        if queued:
            update_state(job_dir(self.root, job_id), "cancelled",
                         finished_at=utc_now(), error="Owner cancelled before dispatch")
        else:
            request_cancel(job_id, root=self.root)
        return True

    def claim_next(self) -> Claim | None:
        """Exactly one active worker; expired leases are NOT automatically reused."""
        with self._transaction() as db:
            if db.execute(
                "SELECT 1 FROM research_jobs WHERE status='running' LIMIT 1"
            ).fetchone():
                return None
            row = db.execute(
                "SELECT job_id FROM research_jobs WHERE status='queued' "
                "ORDER BY created_at ASC, rowid ASC LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            job_id = row["job_id"]
            token = secrets.token_hex(32)
            changed = db.execute(
                "UPDATE research_jobs SET status='running', lease_token=?, "
                "lease_until=?, attempts=attempts+1, updated_at=? "
                "WHERE job_id=? AND status='queued'",
                (token, time.time() + LEASE_SECONDS, utc_now(), job_id),
            ).rowcount
            if changed != 1:
                raise QueueError("Queue claim conflict")
        return Claim(job_id, token)

    def heartbeat(self, claim: Claim):
        with self._transaction() as db:
            changed = db.execute(
                "UPDATE research_jobs SET lease_until=?, updated_at=? "
                "WHERE job_id=? AND lease_token=? AND status='running' "
                "AND lease_until>=?",
                (time.time() + LEASE_SECONDS, utc_now(),
                 _job_id(claim.job_id), claim.token, time.time()),
            ).rowcount
            if changed != 1:
                raise QueueError("Worker lease expired or was replaced")

    def finish(self, claim: Claim) -> str:
        record = read_job(_job_id(claim.job_id), root=self.root)
        status = record["status"]
        if status not in TERMINAL:
            raise QueueError("Cannot finalize an active or incomplete experiment")
        if status == "completed":
            # Verify the original source/LP/samples SHA256 chain, not just
            # SQLite metadata, before recording a successful completion.
            export_bundle(claim.job_id, root=self.root)
        with self._transaction() as db:
            updated = db.execute(
                "UPDATE research_jobs SET status=?, lease_token=NULL,"
                "lease_until=NULL, updated_at=? "
                "WHERE job_id=? AND lease_token=? AND status='running' "
                "AND lease_until>=?",
                (status, utc_now(), claim.job_id, claim.token, time.time()),
            ).rowcount
            if updated != 1:
                raise QueueError("Cannot finish without a valid active lease")
        return status

    def run_once(self, *, wall_seconds: int = MAX_OPERATOR_WALL_SECONDS):
        """Explicit CLI dispatch only, no daemon, no HTTP listener, no auto-retry.

        The child is given CPU and file-size rlimits and a hard wall deadline,
        but NOT a cgroup memory limit. Do not deploy for untrusted users until
        systemd/cgroup memory limits, audited auth, and recovery are complete.
        """
        if type(wall_seconds) is not int or not 10 <= wall_seconds <= 90:
            raise QueueError("Operator wall timeout must be 10–90 seconds")
        claim = self.claim_next()
        if claim is None:
            return None
        folder = job_dir(self.root, claim.job_id)
        env = os.environ.copy()
        for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
            env[name] = "1"

        def limits():
            resource.setrlimit(resource.RLIMIT_CPU, (80, 85))
            resource.setrlimit(resource.RLIMIT_FSIZE, (10_000_000, 10_000_000))

        proc = None
        start = time.monotonic()
        try:
            with (folder / "worker.log").open("ab", buffering=0) as log:
                proc = subprocess.Popen(
                    [sys.executable, "-m", "problems.water_quality.experiment_jobs",
                     "worker", "--job", claim.job_id, "--root", str(self.root)],
                    cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                    close_fds=True, preexec_fn=limits,
                )
                while True:
                    if time.monotonic() - start > wall_seconds:
                        raise TimeoutError("Scientific job exceeded operator wall budget")
                    try:
                        proc.wait(timeout=2)
                        break
                    except subprocess.TimeoutExpired:
                        self.heartbeat(claim)
            record = read_job(claim.job_id, root=self.root)
            if record["status"] not in TERMINAL:
                update_state(folder, "failed", finished_at=utc_now(),
                             error="Worker exited without a terminal research state")
            return claim.job_id, self.finish(claim)
        except Exception:
            if proc is not None and proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                    proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                except ProcessLookupError:
                    pass
            # A lease failure is deliberately NOT auto-recovered. Do not
            # pretend the solver was safely stopped or retry its work.
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init", "run-once"))
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    queue = PrivateQueue(database=args.database, root=args.root)
    if args.action == "init":
        print("Private queue initialized; no server or worker started")
    else:
        result = queue.run_once()
        print("No queued experiments" if result is None else
              f"Scientific worker finished: {result[0]} status={result[1]}")


if __name__ == "__main__":
    main()
