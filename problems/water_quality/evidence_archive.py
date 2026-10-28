"""Operator-only private staging and restore-drill of completed science evidence.

NO network upload, public archive, automatic backup schedule or queue restore.
A separate approved off-VM transport must preserve confidentiality and retention.
Only completed original source-verified jobs are exportable. Stage is append-only,
never overwrites an existing archive or sidecar. A crash can leave an incomplete
pair; verification rejects the pair and requires an operator to investigate.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import stat
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from problems.water_quality.experiment_jobs import (
    JOB_PATTERN, JobError, MAX_JOB_ZIP_BYTES, SCHEMA, SOURCE_SHA256,
    canonical, export_bundle, utc_now,
)
from problems.water_quality.remote_queue import PrivateQueue

BUNDLE_SCHEMA = "private-original-source-science-evidence-stage-v1"
REQUIRED = frozenset({"config.json", "model.json", "result.json", "manifest.json"})
ALLOWED = REQUIRED | {"samples.csv", "emitted_scip_model.lp"}


class EvidenceError(JobError):
    """Archive incomplete, unexpectedly modified, unsafe or not completed."""


def _id(value: str) -> str:
    if not isinstance(value, str) or JOB_PATTERN.fullmatch(value) is None:
        raise EvidenceError("Invalid scientific job ID")
    return value


def _destination(value: Path) -> Path:
    path = Path(value).expanduser().resolve()
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not path.is_dir() or path.stat().st_mode & 0o077:
        raise EvidenceError("Evidence destination must be private (mode 0700)")
    return path


def _read_regular(path: Path, *, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise EvidenceError("Archive or manifest missing or not a regular file")
    st = path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o077:
        raise EvidenceError("Archive or manifest is not private (mode 0600)")
    if st.st_size > limit:
        raise EvidenceError("Oversized staged evidence")
    return path.read_bytes()


def inspect_bundle(raw: bytes, *, job_id: str) -> dict:
    """Independently verify ZIP members and inner original-science digests."""
    _id(job_id)
    if not isinstance(raw, bytes) or len(raw) > MAX_JOB_ZIP_BYTES:
        raise EvidenceError("Original research ZIP exceeds export size limit")
    try:
        with ZipFile(io.BytesIO(raw)) as zip_file:
            infos = zip_file.infolist()
            names = [item.filename for item in infos]
            if (len(names) != len(set(names))
                    or not REQUIRED.issubset(names)
                    or not set(names).issubset(ALLOWED)
                    or len(names) > len(ALLOWED)):
                raise EvidenceError("Missing, duplicate or unexpected ZIP paths")
            if sum(item.file_size for item in infos) > 6 * MAX_JOB_ZIP_BYTES:
                raise EvidenceError("Archive declares excessive uncompressed size")
            for info in infos:
                kind = (info.external_attr >> 16) & 0o170000
                if (info.is_dir() or kind not in (0, stat.S_IFREG)
                        or info.file_size > MAX_JOB_ZIP_BYTES):
                    raise EvidenceError("Unsupported ZIP entry type or size")
            members = {name: zip_file.read(name) for name in names}
    except EvidenceError:
        # Preserve specific security/structure validation failures.
        raise
    except (BadZipFile, EOFError, OSError, ValueError, RuntimeError) as exc:
        raise EvidenceError("Unreadable scientific evidence ZIP") from exc
    try:
        manifest = json.loads(members["manifest.json"])
        config = json.loads(members["config.json"])
        model = json.loads(members["model.json"])
        result = json.loads(members["result.json"])
        checksums = manifest["sha256"]
        if (not isinstance(checksums, dict)
                or set(checksums) != set(names) - {"manifest.json"}):
            raise EvidenceError("Manifest missing or extra checksum entries")
        for name, expected in checksums.items():
            if (not isinstance(expected, str) or len(expected) != 64
                    or sha256(members[name]).hexdigest() != expected):
                raise EvidenceError("Original scientific artifact checksum mismatch")
        if (manifest["schema"] != SCHEMA
                or config["schema"] != SCHEMA
                or result["schema"] != SCHEMA
                or config["job_id"] != job_id
                or result["job_id"] != job_id
                or manifest["source_sha256"] != SOURCE_SHA256
                or config["source_sha256"] != SOURCE_SHA256
                or model["source_sha256"] != SOURCE_SHA256
                or result["source_sha256"] != SOURCE_SHA256
                or result["model_sha256"] != sha256(members["model.json"]).hexdigest()
                or config["configuration"] != result["configuration"]):
            raise EvidenceError("Original model identity, inputs or source mismatch")
    except (ValueError, TypeError, KeyError, UnicodeDecodeError) as exc:
        if isinstance(exc, EvidenceError):
            raise
        raise EvidenceError("Malformed original evidence metadata") from exc
    return {
        "source_sha256": SOURCE_SHA256,
        "model_sha256": sha256(members["model.json"]).hexdigest(),
        "member_sha256": {name: sha256(members[name]).hexdigest()
                          for name in sorted(members)},
    }


def _write_once(path: Path, raw: bytes):
    """O_EXCL prevents silent overwrite; 0600 even with caller umask 0022."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def stage_completed(queue: PrivateQueue, *, job_id: str, destination: Path) -> dict:
    """Create one immutable evidence ZIP + SHA-256 sidecar after queue completion."""
    job_id = _id(job_id)
    with queue._connection() as db:
        row = db.execute(
            "SELECT status, source_sha256 FROM research_jobs WHERE job_id=?",
            (job_id,),
        ).fetchone()
    if row is None or row["status"] != "completed":
        raise EvidenceError("Only completed queue jobs can be staged")
    if row["source_sha256"] != SOURCE_SHA256:
        raise EvidenceError("Queue source identity differs from original dataset")
    raw = export_bundle(job_id, root=queue.root)
    scientific = inspect_bundle(raw, job_id=job_id)
    dest = _destination(destination)
    if dest == queue.root or dest.is_relative_to(queue.root):
        raise EvidenceError("Use a separate private evidence staging directory")
    archive = dest / (job_id + ".zip")
    sidecar = dest / (job_id + ".sha256.json")
    if archive.exists() or sidecar.exists():
        raise EvidenceError("Evidence already exists; never overwrite snapshots")
    index = {
        "schema": BUNDLE_SCHEMA,
        "job_id": job_id,
        "source_sha256": SOURCE_SHA256,
        "model_sha256": scientific["model_sha256"],
        "archive_sha256": sha256(raw).hexdigest(),
        "archive_size": len(raw),
        "created_at": utc_now(),
        "confidential_research_evidence": True,
        "not_off_vm_until_transferred_and_verified": True,
    }
    _write_once(archive, raw)
    # On a crash here, the incomplete pair is rejected, not silently recovered.
    _write_once(sidecar, canonical(index))
    return verify_staged(destination=dest, job_id=job_id)


def verify_staged(*, destination: Path, job_id: str) -> dict:
    """Offline verification; must run again AFTER transferring archive off VM."""
    job_id = _id(job_id)
    dest = _destination(destination)
    raw = _read_regular(dest / (job_id + ".zip"), limit=MAX_JOB_ZIP_BYTES)
    sidecar = _read_regular(dest / (job_id + ".sha256.json"), limit=16_384)
    try:
        index = json.loads(sidecar)
        scientific = inspect_bundle(raw, job_id=job_id)
        if (index["schema"] != BUNDLE_SCHEMA
                or index["job_id"] != job_id
                or index["source_sha256"] != SOURCE_SHA256
                or index["model_sha256"] != scientific["model_sha256"]
                or index["archive_size"] != len(raw)
                or index["archive_sha256"] != sha256(raw).hexdigest()):
            raise EvidenceError("Stage sidecar does not match research ZIP")
    except (ValueError, TypeError, KeyError, UnicodeDecodeError) as exc:
        if isinstance(exc, EvidenceError):
            raise
        raise EvidenceError("Malformed evidence sidecar") from exc
    return {"job_id": job_id, "verified": True,
            "archive_sha256": index["archive_sha256"],
            "archive_size": len(raw),
            "source_sha256": SOURCE_SHA256,
            "model_sha256": scientific["model_sha256"]}


def restore_drill(*, destination: Path, job_id: str, into: Path) -> list[str]:
    """Extract only the verified original research files to a NEW private folder.

    This is a standalone evidence inspection, NOT a database/queue restoration.
    """
    verify_staged(destination=destination, job_id=job_id)
    raw = _read_regular(
        _destination(destination) / (_id(job_id) + ".zip"),
        limit=MAX_JOB_ZIP_BYTES,
    )
    target = Path(into).expanduser().resolve()
    if target.exists():
        raise EvidenceError("Restore-drill destination already exists")
    target.mkdir(parents=True, mode=0o700, exist_ok=False)
    if target.stat().st_mode & 0o077:
        raise EvidenceError("Restore-drill destination must be private")
    names = []
    with ZipFile(io.BytesIO(raw)) as zip_file:
        for name in zip_file.namelist():
            # inspect_bundle checked fixed names, duplicates and traversal.
            _write_once(target / name, zip_file.read(name))
            names.append(name)
    return sorted(names)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "verify", "restore-drill"))
    parser.add_argument("--job", required=True)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--restore-into", type=Path)
    args = parser.parse_args()
    if args.action == "stage":
        if args.database is None or args.root is None:
            parser.error("stage requires --database and --root")
        queue = PrivateQueue(database=args.database, root=args.root)
        output = stage_completed(queue, job_id=args.job,
                                 destination=args.destination)
    elif args.action == "verify":
        output = verify_staged(destination=args.destination, job_id=args.job)
    else:
        if args.restore_into is None:
            parser.error("restore-drill requires --restore-into")
        output = {"members": restore_drill(
            destination=args.destination, job_id=args.job,
            into=args.restore_into,
        )}
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
