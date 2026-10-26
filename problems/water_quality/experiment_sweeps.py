"""Explicit, LOCAL-ONLY four-cell classical-SA parameter sweeps.

A sweep is one detached worker that executes four *ordinary* source-verified
experiment jobs in a fixed 2x2 Cartesian order. This is an engineering-scale
exploratory run, never a confirmatory statistical study or quantum execution.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from hashlib import sha256
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import traceback
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np

from problems.water_quality.experiment_jobs import (
    Cancelled, JobError, JOB_PATTERN, SOURCE_SHA256, Spec, atomic_write,
    canonical, create_job, execute_job, export_bundle, job_root, list_jobs,
    load_json, local_opt_in, request_cancel, utc_now, write_json,
)
from prototypes.unified_dashboard.experiment_analysis import load_verified_samples

SCHEMA = "local-user-triggered-2x2-classical-penalty-sweep-v1"
MAX_ARCHIVE_BYTES = 6_000_000
SWEEP_SUBDIR = "_sweeps"
OUTPUTS = ("config.json", "result.json", "cells.csv", "manifest.json")


@dataclass(frozen=True)
class SweepSpec:
    k_new: int = 5
    budget_levels: tuple[float, float] = (2.0, 12.0)
    connectivity_levels: tuple[float, float] = (2.0, 12.0)
    reads_per_cell: int = 2
    sweeps_per_read: int = 40
    parent_seed: int = 20261026

    def validate(self):
        if type(self.k_new) is not int or not 1 <= self.k_new <= 10:
            raise JobError("Sweep K must be 1–10")
        if type(self.reads_per_cell) is not int or not 1 <= self.reads_per_cell <= 8:
            raise JobError("Sweep limit: 1–8 classical samples per cell")
        if type(self.sweeps_per_read) is not int or not 10 <= self.sweeps_per_read <= 100:
            raise JobError("Sweep limit: 10–100 sweeps per sample")
        if type(self.parent_seed) is not int or not 0 <= self.parent_seed < 2**32:
            raise JobError("Sweep parent seed must be an unsigned 32-bit number")
        for name in ("budget_levels", "connectivity_levels"):
            levels = getattr(self, name)
            if not isinstance(levels, (list, tuple)) or len(levels) != 2:
                raise JobError(name + ": exactly two distinct λ values required")
            if any(
                type(v) not in (int, float) or not math.isfinite(v)
                or not 0.01 <= v <= 1000 for v in levels
            ):
                raise JobError(name + ": finite positive values within 0.01–1000")
            if float(levels[0]) == float(levels[1]):
                raise JobError(name + ": duplicate penalty values")
        return self

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or set(value) != set(cls.__dataclass_fields__):
            raise JobError("Sweep spec contains missing/unknown configuration keys")
        obj = cls(
            k_new=value["k_new"], budget_levels=tuple(value["budget_levels"]),
            connectivity_levels=tuple(value["connectivity_levels"]),
            reads_per_cell=value["reads_per_cell"],
            sweeps_per_read=value["sweeps_per_read"],
            parent_seed=value["parent_seed"],
        )
        return obj.validate()

    def as_dict(self):
        self.validate()
        return {
            "k_new": self.k_new,
            "budget_levels": list(self.budget_levels),
            "connectivity_levels": list(self.connectivity_levels),
            "reads_per_cell": self.reads_per_cell,
            "sweeps_per_read": self.sweeps_per_read,
            "parent_seed": self.parent_seed,
        }

    def cells(self):
        """Four full Cartesian combinations, with cell-distinct parent seeds."""
        self.validate()
        records = []
        for i, b in enumerate(self.budget_levels):
            for j, c in enumerate(self.connectivity_levels):
                index = i * 2 + j
                child_parent = int(np.random.SeedSequence(
                    [self.parent_seed, index]
                ).generate_state(1, dtype=np.uint32)[0])
                records.append({
                    "cell_index": index,
                    "budget_penalty": float(b),
                    "connectivity_penalty": float(c),
                    "derived_parent_seed": child_parent,
                })
        if len({p["derived_parent_seed"] for p in records}) != 4:
            raise JobError("Collision of parent seeds across 2D penalty cells")
        return records


def sweep_folder(root, sweep_id):
    if not isinstance(sweep_id, str) or JOB_PATTERN.fullmatch(sweep_id) is None:
        raise JobError("Invalid 2x2 sweep identifier")
    return Path(root) / SWEEP_SUBDIR / sweep_id


def create_sweep(spec: SweepSpec, *, root=None):
    spec.validate()
    root = Path(root) if root is not None else job_root()
    folder = root / SWEEP_SUBDIR
    folder.mkdir(parents=True, exist_ok=True)
    if len(list(folder.glob("[0-9a-f]" * 32))) >= 25:
        raise JobError("Local sweep history full; archive old results")
    sweep_id = uuid4().hex
    target = sweep_folder(root, sweep_id)
    target.mkdir(mode=0o700, exist_ok=False)
    write_json(target / "config.json", {
        "schema": SCHEMA, "sweep_id": sweep_id, "created_at": utc_now(),
        "source_sha256": SOURCE_SHA256,
        "configuration": spec.as_dict(),
        "not_confirmatory_or_quantum": True,
    })
    write_json(target / "state.json", {
        "schema": SCHEMA, "sweep_id": sweep_id, "status": "queued",
        "completed_cells": 0, "total_cells": 4, "active_job_id": None,
        "child_job_ids": [], "updated_at": utc_now(), "error": None,
    })
    return sweep_id


def read_sweep(sweep_id, *, root=None):
    root = Path(root) if root is not None else job_root()
    folder = sweep_folder(root, sweep_id)
    try:
        config = load_json(folder / "config.json")
        state = load_json(folder / "state.json")
        if (config.get("schema") != SCHEMA or state.get("schema") != SCHEMA
                or config.get("sweep_id") != sweep_id
                or state.get("sweep_id") != sweep_id
                or state.get("status") not in
                ("queued", "running", "completed", "failed", "cancelled")):
            raise JobError("Corrupt sweep identity or status")
        spec = SweepSpec.from_dict(config["configuration"])
        if config.get("source_sha256") != SOURCE_SHA256:
            raise JobError("Historical source checksum changed")
        result = (load_json(folder / "result.json")
                  if state["status"] == "completed" else None)
        return {"sweep_id": sweep_id, "config": config,
                "state": state, "spec": spec, "result": result}
    except (OSError, TypeError, ValueError, KeyError) as exc:
        if isinstance(exc, JobError):
            raise
        raise JobError("Sweep history file missing or invalid") from exc


def list_sweeps(*, root=None):
    root = Path(root) if root is not None else job_root()
    parent = root / SWEEP_SUBDIR
    if not parent.is_dir():
        return []
    found = []
    for path in parent.iterdir():
        if path.is_dir() and JOB_PATTERN.fullmatch(path.name):
            try:
                found.append(read_sweep(path.name, root=root))
            except (OSError, ValueError):
                continue
    return sorted(found, key=lambda row: row["config"]["created_at"], reverse=True)


def active_sweep_exists(*, root=None):
    return any(s["state"]["status"] in ("queued", "running")
               for s in list_sweeps(root=root))


def _state(folder, status, **kwargs):
    state = load_json(folder / "state.json")
    state.update(status=status, updated_at=utc_now(), **kwargs)
    write_json(folder / "state.json", state)


def launch_sweep(spec: SweepSpec, *, root=None):
    if not local_opt_in():
        raise JobError("Local-only sweep disabled until trusted operator opt-in")
    import fcntl
    root = Path(root).resolve() if root is not None else job_root()
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".launch.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            if active_sweep_exists(root=root) or any(
                x["status"] in ("queued", "running") for x in list_jobs(root=root)
            ):
                raise JobError("A standalone or sweep experiment is already active")
            sweep_id = create_sweep(spec, root=root)
            folder = sweep_folder(root, sweep_id)
            env = os.environ.copy()
            for key in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
                env[key] = "1"
            try:
                with (folder / "worker.log").open("ab", buffering=0) as log:
                    subprocess.Popen(
                        [sys.executable, "-m",
                         "problems.water_quality.experiment_sweeps",
                         "worker", "--sweep", sweep_id, "--root", str(root)],
                        cwd=str(Path(__file__).resolve().parents[2]), env=env,
                        stdin=subprocess.DEVNULL, stdout=log,
                        stderr=subprocess.STDOUT, close_fds=True,
                        start_new_session=True,
                    )
            except OSError as exc:
                _state(folder, "failed", error="Unable to launch local sweep worker")
                raise JobError("Unable to launch local sweep") from exc
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return sweep_id


def cancel_sweep(sweep_id, *, root=None):
    root = Path(root) if root is not None else job_root()
    record = read_sweep(sweep_id, root=root)
    if record["state"]["status"] not in ("queued", "running"):
        return False
    folder = sweep_folder(root, sweep_id)
    atomic_write(folder / "cancel.request", b"operator_requested\n")
    active = record["state"].get("active_job_id")
    if active:
        request_cancel(active, root=root)
    return True


def _check_cancel(folder):
    if (folder / "cancel.request").is_file():
        raise Cancelled("Operator cancelled bounded 2x2 classical grid")


def _make_csv(rows):
    buffer = io.StringIO()
    fields = list(rows[0])
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode()


def execute_sweep(sweep_id, *, root=None):
    """Sequentially run and checkpoint actual source-validated child experiments."""
    root = Path(root) if root is not None else job_root()
    original = read_sweep(sweep_id, root=root)
    if original["state"]["status"] != "queued":
        raise JobError("Sweep must be queued to start")
    folder = sweep_folder(root, sweep_id)
    _state(folder, "running", started_at=utc_now())
    spec = original["spec"]
    records = []
    try:
        for point in spec.cells():
            _check_cancel(folder)
            sub_spec = Spec(
                solver="classical_sa", n_free=20, k_new=spec.k_new,
                reads=spec.reads_per_cell, sweeps=spec.sweeps_per_read,
                parent_seed=point["derived_parent_seed"],
                lambda_budget=point["budget_penalty"],
                lambda_connectivity=point["connectivity_penalty"],
            )
            child_id = create_job(sub_spec, root=root)
            current = load_json(folder / "state.json")
            _state(folder, "running", active_job_id=child_id,
                   child_job_ids=current["child_job_ids"] + [child_id])
            child_result = execute_job(child_id, root=root)
            if child_result["status"] == "cancelled":
                raise Cancelled("Current cell cancelled by operator")
            if child_result["status"] != "completed":
                raise JobError("Child cell solver failed: " + str(child_result.get("error")))
            # Parse independent exact-original source semantics again, after
            # verifying all child model/sample file digests and full samples.
            rows = load_verified_samples(child_id, root=root)
            child_zip = export_bundle(child_id, root=root)
            filename = f"cell-{point['cell_index']}-{child_id}.zip"
            atomic_write(folder / filename, child_zip)
            feasible = [row for row in rows if row["Feasible"]]
            state = load_json(folder / "state.json")
            records.append({
                **point, "child_job_id": child_id,
                "child_evidence_sha256": sha256(child_zip).hexdigest(),
                "sample_count": len(rows), "feasible_count": len(feasible),
                "observed_feasible_fraction": len(feasible) / len(rows),
                "best_feasible_original_objective": (
                    min(r["Original objective"] for r in feasible) if feasible else None
                ),
                "exact_model_sha256": read_sweep_child_model_sha(child_id, root),
            })
            _state(folder, "running",
                   completed_cells=len(records), active_job_id=None)
        _check_cancel(folder)
        if len({row["exact_model_sha256"] for row in records}) != 1:
            raise JobError("Numeric original-model fingerprint changed across 2x2 cells")
        output = {
            "schema": SCHEMA, "sweep_id": sweep_id,
            "source_sha256": SOURCE_SHA256,
            "configuration": spec.as_dict(),
            "original_model_sha256": records[0]["exact_model_sha256"],
            "observations": records,
            "total_sampled_states": sum(row["sample_count"] for row in records),
            "statistical_significance_or_optimal_penalty_claimed": False,
            "quantum_executed": False,
            "scientific_interpretation": (
                "Only four exploratory classical-SA source-model configurations. "
                "All infeasible reads kept, not a preregistered/repeated study."
            ),
        }
        write_json(folder / "result.json", output)
        atomic_write(folder / "cells.csv", _make_csv(records))
        names = ["config.json", "result.json", "cells.csv"] + [
            f"cell-{record['cell_index']}-{record['child_job_id']}.zip"
            for record in records
        ]
        write_json(folder / "manifest.json", {
            "schema": SCHEMA,
            "source_sha256": SOURCE_SHA256,
            "file_sha256": {
                name: sha256((folder / name).read_bytes()).hexdigest()
                for name in names
            },
        })
        _state(folder, "completed", finished_at=utc_now(), active_job_id=None)
    except Cancelled:
        _state(folder, "cancelled", finished_at=utc_now(),
               active_job_id=None, error="Operator requested cancellation")
    except Exception as exc:
        print("Sweep worker failed:", repr(exc), file=sys.stderr, flush=True)
        traceback.print_exc()
        _state(folder, "failed", finished_at=utc_now(),
               active_job_id=None, error=f"{type(exc).__name__}: {str(exc)[:250]}")
    return load_json(folder / "state.json")


def read_sweep_child_model_sha(job_id, root):
    item = read_job_for_sweep(job_id, root)
    return item["model_sha256"]


def read_job_for_sweep(job_id, root):
    from problems.water_quality.experiment_jobs import read_job
    record = read_job(job_id, root=root)
    if record["status"] != "completed" or record["result"] is None:
        raise JobError("Sweep cell did not complete successfully")
    return record["result"]


def export_sweep(sweep_id, *, root=None):
    root = Path(root) if root is not None else job_root()
    record = read_sweep(sweep_id, root=root)
    if record["state"]["status"] != "completed":
        raise JobError("Only a completed sweep has a final exportable 2x2 package")
    folder = sweep_folder(root, sweep_id)
    try:
        manifest = load_json(folder / "manifest.json")
        expected = {"config.json", "result.json", "cells.csv"} | {
            f"cell-{row['cell_index']}-{row['child_job_id']}.zip"
            for row in record["result"]["observations"]
        }
        if (manifest.get("schema") != SCHEMA or set(manifest["file_sha256"]) != expected
                or record["result"]["configuration"] != record["spec"].as_dict()
                or len(record["result"]["observations"]) != 4):
            raise JobError("Incomplete/mismatched 2x2 scientific archive")
        data = {}
        for name, expected_hash in manifest["file_sha256"].items():
            raw = (folder / name).read_bytes()
            if sha256(raw).hexdigest() != expected_hash:
                raise JobError("Recomputed scientific SHA256 differs for " + name)
            data[name] = raw
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if isinstance(exc, JobError):
            raise
        raise JobError("Sweep archive is corrupted or incomplete") from exc
    archive = io.BytesIO()
    with ZipFile(archive, "w", ZIP_DEFLATED) as out:
        for name, raw in data.items():
            out.writestr(name, raw)
        out.writestr("manifest.json", canonical(manifest))
    if len(archive.getvalue()) > MAX_ARCHIVE_BYTES:
        raise JobError("Local bounded sweep ZIP exceeds research size cap")
    return archive.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("worker",))
    parser.add_argument("--sweep", required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "worker":
        state = execute_sweep(args.sweep, root=args.root)
        print(json.dumps({"sweep_id": args.sweep, "status": state["status"]}))
        if state["status"] == "failed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
