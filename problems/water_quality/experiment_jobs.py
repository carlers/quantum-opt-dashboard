"""Opt-in LOCAL user-controlled source-science experiments, never CI studies.

Workers are independent bounded processes. Job inputs are immutable, all
results are scoped to a UUID folder, and page rerenders never invoke solvers.
This is single-operator local filesystem persistence, NOT a multiuser/cloud
task queue, remote service, unattended scheduler or guaranteed hard sandbox.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from dataclasses import dataclass, replace
from hashlib import sha256
import io
from importlib.metadata import PackageNotFoundError, version
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import traceback
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA256 = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
SCHEMA = "user-controlled-water-quality-local-job-v1"
JOB_PATTERN = re.compile(r"[0-9a-f]{32}\Z")
ALLOWED_STATUS = {"queued", "running", "completed", "failed", "cancelled"}
FILES = ("config.json", "state.json", "model.json", "result.json", "samples.csv",
         "manifest.json", "worker.log")
MAX_JOBS = 50
MAX_JOB_ZIP_BYTES = 5_000_000
SCIP_SECONDS_LIMIT = 30


class JobError(ValueError):
    """Invalid config, unsafe job identity or missing verified source."""


class Cancelled(Exception):
    """Local worker cancellation request after a safe solver checkpoint."""


@dataclass(frozen=True)
class Spec:
    solver: str = "scip"
    n_free: int = 20
    k_new: int = 5
    time_limit_seconds: int = 15
    reads: int = 4
    sweeps: int = 300
    parent_seed: int = 20261026
    lambda_budget: float = 12.9
    lambda_connectivity: float = 12.9

    def validate(self):
        if self.solver not in ("scip", "classical_sa"):
            raise JobError("Only SCIP and classical OpenJij SA are supported")
        if type(self.n_free) is not int or self.n_free not in (20, 50, 100):
            raise JobError("N must be one of the source-validated 20, 50, 100 tiers")
        if type(self.k_new) is not int or not 1 <= self.k_new <= min(self.n_free, 10):
            raise JobError("K must be between 1 and 10")
        if type(self.time_limit_seconds) is not int or not 1 <= self.time_limit_seconds <= SCIP_SECONDS_LIMIT:
            raise JobError("SCIP budget must be 1–30 seconds")
        if type(self.reads) is not int or not 1 <= self.reads <= 32:
            raise JobError("Classical SA samples must be 1–32")
        if type(self.sweeps) is not int or not 10 <= self.sweeps <= 500:
            raise JobError("Classical SA sweeps must be 10–500")
        if type(self.parent_seed) is not int or not 0 <= self.parent_seed < 2**32:
            raise JobError("Parent seed must be an unsigned 32-bit integer")
        for name in ("lambda_budget", "lambda_connectivity"):
            v = getattr(self, name)
            if type(v) not in (int, float) or not math.isfinite(v) or not 0.01 <= v <= 1000:
                raise JobError(f"{name} must be finite within 0.01–1000")
        if self.solver == "classical_sa" and self.n_free != 20:
            raise JobError("Classical SA is currently source-validated only for N20")
        return self

    @classmethod
    def from_dict(cls, raw):
        if not isinstance(raw, dict) or set(raw) != set(cls.__dataclass_fields__):
            raise JobError("Unknown/missing experiment setting (not an executable script)")
        try:
            return cls(**raw).validate()
        except TypeError as exc:
            raise JobError("Invalid configuration structure") from exc

    def manifest(self):
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def local_opt_in():
    return os.environ.get("QOPT_LOCAL_EXPERIMENTS") == "1"


def job_root():
    override = os.environ.get("QOPT_EXPERIMENT_STORE")
    return (Path(override).expanduser().resolve() if override else
            (ROOT / ".qopt_experiments").resolve())


def job_dir(root, job_id):
    if not isinstance(job_id, str) or JOB_PATTERN.fullmatch(job_id) is None:
        raise JobError("Invalid local experiment identifier")
    return Path(root) / job_id


def atomic_write(path, raw):
    temp = path.parent / ("." + path.name + "." + uuid4().hex + ".tmp")
    try:
        with temp.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def write_json(path, data):
    atomic_write(path, canonical(data))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def package_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def load_json(path):
    return json.loads(path.read_bytes())


def create_job(spec: Spec, *, root=None):
    """Prepare a persistent immutable job, without launching a subprocess."""
    spec.validate()
    root = Path(root) if root is not None else job_root()
    root.mkdir(parents=True, exist_ok=True)
    if len(list(root.glob("[0-9a-f]" * 32))) >= MAX_JOBS:
        raise JobError("Local history at capacity; archive/remove old jobs manually")
    identifier = uuid4().hex
    folder = job_dir(root, identifier)
    folder.mkdir(mode=0o700, exist_ok=False)
    write_json(folder / "config.json", {
        "schema": SCHEMA, "job_id": identifier,
        "created_at": utc_now(), "source_sha256": SOURCE_SHA256,
        "configuration": spec.manifest(),
        "not_manuscript_or_field_reproduction": True,
    })
    write_json(folder / "state.json", {
        "schema": SCHEMA, "job_id": identifier, "status": "queued",
        "completed_reads": 0, "total_reads": spec.reads if spec.solver == "classical_sa" else 1,
        "updated_at": utc_now(), "error": None,
    })
    return identifier


def launch_job(spec: Spec, *, root=None):
    """Run only after an explicit click and local operator opt-in.

    No arbitrary worker executable, path or shell from user-controlled input.
    """
    if not local_opt_in():
        raise JobError("Local experiments disabled: set QOPT_LOCAL_EXPERIMENTS=1 on a trusted, private machine")
    root = Path(root).resolve() if root is not None else job_root()
    # Serialize check-and-launch among Streamlit sessions on POSIX machines.
    import fcntl
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".launch.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            jobs = list_jobs(root=root)
            if any(j["status"] in ("queued", "running") for j in jobs):
                raise JobError("A local research job is already running or queued")
            job_id = create_job(spec, root=root)
            folder = job_dir(root, job_id)
            env = os.environ.copy()
            for var in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
                env[var] = "1"
            try:
                with (folder / "worker.log").open("ab", buffering=0) as log:
                    subprocess.Popen(
                        [sys.executable, "-m", "problems.water_quality.experiment_jobs",
                         "worker", "--job", job_id, "--root", str(root)],
                        cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                        stdout=log, stderr=subprocess.STDOUT,
                        close_fds=True, start_new_session=True,
                    )
            except OSError as exc:
                update_state(folder, "failed", error="Local Python worker could not launch")
                raise JobError("Could not start local worker") from exc
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return job_id


def update_state(folder, status, **extra):
    if status not in ALLOWED_STATUS:
        raise JobError("Unrecognized worker status")
    old = load_json(folder / "state.json")
    old.update(status=status, updated_at=utc_now(), **extra)
    write_json(folder / "state.json", old)


def read_job(job_id, *, root=None):
    folder = job_dir(Path(root) if root is not None else job_root(), job_id)
    info = load_json(folder / "config.json")
    state = load_json(folder / "state.json")
    if info.get("job_id") != job_id or state.get("job_id") != job_id:
        raise JobError("Corrupt job identifiers")
    if state.get("status") not in ALLOWED_STATUS or info.get("schema") != SCHEMA:
        raise JobError("Invalid persistent job record")
    # Every read verifies the settings remain safe (and allows no unknown keys).
    spec = Spec.from_dict(info["configuration"])
    return {"job_id": job_id, "status": state["status"],
            "state": state, "config": info, "spec": spec,
            "result": load_json(folder / "result.json") if
                state["status"] == "completed" and (folder / "result.json").is_file()
                else None}


def list_jobs(*, root=None):
    root = Path(root) if root is not None else job_root()
    if not root.is_dir():
        return []
    records = []
    for path in root.iterdir():
        if path.is_dir() and JOB_PATTERN.fullmatch(path.name):
            try:
                records.append(read_job(path.name, root=root))
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue
    return sorted(records, key=lambda j: j["config"]["created_at"], reverse=True)[:MAX_JOBS]


def request_cancel(job_id, *, root=None):
    job = read_job(job_id, root=root)
    if job["status"] not in ("queued", "running"):
        return False
    folder = job_dir(Path(root) if root is not None else job_root(), job_id)
    atomic_write(folder / "cancel.request", b"operator_requested\n")
    return True


def check_cancel(folder):
    if (folder / "cancel.request").is_file():
        raise Cancelled("Operator requested cancellation")


def _source_instance(spec, folder):
    from dataclasses import replace
    from hashlib import sha256
    from problems.water_quality.nested_resolution import REFERENCE_GEOJSON, build_nested_instances
    digest = sha256(REFERENCE_GEOJSON.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise JobError("Historical lake GeoJSON source bytes changed")
    study = build_nested_instances(tiers=(spec.n_free,))
    if study.source_sha256 != SOURCE_SHA256 or study.fixed_simulated or len(study.fixed_master_positions) != 15:
        raise JobError("Original real marked stations or source changed")
    instance = replace(study.tier_instances[0].instance, budget=spec.k_new)
    model = {
        "schema": "original-notebook-local-onehop-hex-float-v1",
        "source_sha256": digest, "N_free": spec.n_free, "K": spec.k_new,
        "source_master_free_positions": [int(v) for v in instance.free_indices],
        "source_master_fixed_positions": [int(v) for v in instance.fixed_indices],
        "linear_ieee754_hex": [float(v).hex() for v in instance.linear],
        "quadratic_ieee754_hex": [[int(i), int(j), float(q).hex()]
                                 for i, j, q in instance.quadratic],
        "free_neighbors": [list(map(int, x)) for x in instance.neighbors],
        "fixed_neighbors": [int(v) for v in instance.fixed_neighbors],
        "factors": "historical notebook weights / road-based D2 / local one-hop",
        "paper_data_parity_proven": False,
    }
    write_json(folder / "model.json", model)
    return instance, model


def _original_audit(instance, selected):
    from prototypes.streamlit_water_quality.model import evaluate
    import numpy as np
    x = np.zeros(len(instance.free_indices), dtype=np.int64)
    x[selected] = 1
    result = evaluate(instance, x)
    result["selected_local_positions"] = selected
    result["selected_source_master_positions"] = [int(instance.free_indices[i]) for i in selected]
    return result


def _run_scip(instance, spec, folder):
    from prototypes.streamlit_water_quality.model import solve_scip
    check_cancel(folder)
    begin = time.perf_counter()
    values, solver = solve_scip(
        instance, time_limit=float(spec.time_limit_seconds),
        export_lp_path=folder / "emitted_scip_model.lp"
    )
    check_cancel(folder)
    selected = [int(i) for i, bit in enumerate(values) if bit]
    audit = _original_audit(instance, selected)
    if not audit["feasible"] or not math.isclose(audit["energy"], solver["energy"], abs_tol=1e-7):
        raise JobError("Independent SCIP source objective / feasibility check failed")
    update_state(folder, "running", completed_reads=1)
    return {
        "solver": "SCIP exact MILP for original nonnegative interaction model",
        "scip_status": solver["status"], "scip_gap": solver["gap"],
        "scip_proven_optimal": bool(solver["optimal"]),
        "source_selection": audit, "solve_call_including_lp_export_seconds": time.perf_counter() - begin,
        "formal_signed_optimality_certificate": False,
    }, []


def _run_sa(instance, spec, folder):
    import numpy as np
    import openjij as oj
    from prototypes.streamlit_water_quality.qubo import make_qubo, energy, decoded_penalty_energy
    q = make_qubo(instance, budget_penalty=spec.lambda_budget,
                  connectivity_penalty=spec.lambda_connectivity)
    coeff = q.as_index_qubo()
    coeff.update({(i, i): coeff.get((i, i), 0.0) for i in range(q.n_variables)})
    children = np.random.SeedSequence(spec.parent_seed).spawn(spec.reads)
    seeds = [int(c.generate_state(1, dtype=np.uint32)[0]) for c in children]
    if len(set(seeds)) != len(seeds):
        raise JobError("Child seed collision")
    sampler = oj.SASampler()
    samples = []
    begin = time.perf_counter()
    for index, seed in enumerate(seeds):
        check_cancel(folder)
        reply = sampler.sample_qubo(
            coeff, num_reads=1, num_sweeps=spec.sweeps, seed=seed, sparse=True,
        )
        indices = [int(v) for v in reply.indices]
        if len(indices) != q.n_variables or set(indices) != set(range(q.n_variables)):
            raise JobError("OpenJij did not report all original and auxiliary variables")
        records = reply.record
        if (len(records.sample) != 1 or int(records.num_occurrences[0]) != 1
                or len(records.energy) != 1):
            raise JobError("One-read sample returned unknown multiplicity")
        bits = [0] * q.n_variables
        for col, raw in zip(indices, records.sample[0]):
            if float(raw) not in (0., 1.):
                raise JobError("OpenJij returned nonbinary spins")
            bits[col] = int(raw)
        score = energy(q, bits)
        if not math.isclose(score - q.offset, float(records.energy[0]),
                            abs_tol=1e-6, rel_tol=1e-9):
            raise JobError("Classical sampler/expanded QUBO energy mismatch")
        selected = [i for i, v in enumerate(bits[:q.n_free]) if v]
        audit = _original_audit(instance, selected)
        minimum_slack = decoded_penalty_energy(instance, q, bits[:q.n_free])
        if score < minimum_slack - 1e-6:
            raise JobError("Sampled auxiliary energy below minimized slack penalty")
        samples.append({
            "read_index": index, "child_seed": seed,
            "original_decisions": "".join(map(str, bits[:q.n_free])),
            "full_original_and_auxiliary_bits": "".join(map(str, bits)),
            "original_feasible": bool(audit["feasible"]),
            "original_budget_ok": bool(audit["budget_ok"]),
            "original_connectivity_ok": bool(audit["connectivity_ok"]),
            "original_selected_count": audit["num_selected"],
            "selected_local_positions": audit["selected_local_positions"],
            "selected_source_master_positions": audit["selected_source_master_positions"],
            "original_objective": audit["energy"],
            "expanded_qubo_augmented_energy": float(score),
            "qubo_energy_without_offset": float(records.energy[0]),
            "same_original_x_best_slack_energy": float(minimum_slack),
        })
        update_state(folder, "running", completed_reads=index + 1)
    check_cancel(folder)
    feasible = [s for s in samples if s["original_feasible"]]
    reference = -3.3012934918564643 if spec.n_free == 20 and spec.k_new == 5 else None
    if reference is not None and any(s["original_objective"] < reference - 1e-7 for s in feasible):
        raise JobError("Feasible SA state beat independently verified N20 optimum")
    return {
        "solver": "classical OpenJij SASampler (NOT quantum hardware)",
        "total_samples": len(samples),
        "feasible_count": len(feasible),
        "feasible_fraction": len(feasible) / len(samples),
        "best_feasible_original_objective": (
            min(s["original_objective"] for s in feasible) if feasible else None
        ),
        "exact_N20_reference_objective_if_applicable": reference,
        "sample_wall_seconds": time.perf_counter() - begin,
        "penalties": {"budget": spec.lambda_budget, "connectivity": spec.lambda_connectivity},
        "n_qubo_variables": q.n_variables,
        "qubo_coefficient_sha256": sha256(canonical({
            "offset_hex": float(q.offset).hex(),
            "coefficients_hex": [[int(i), int(j), float(v).hex()]
                                 for (i, j), v in sorted(q.coefficients.items())]
        })).hexdigest(),
        "scientific_scope": "single-user N20 bounded exploratory sample, no inference",
    }, samples


def _write_samples_csv(folder, records):
    if not records:
        return
    # Preserve serialized array-valued fields as JSON, never Python repr.
    buffer = io.StringIO()
    columns = list(records[0])
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for record in records:
        writer.writerow({key: json.dumps(value, separators=(",", ":"))
                         if isinstance(value, (dict, list)) else value
                         for key, value in record.items()})
    atomic_write(folder / "samples.csv", buffer.getvalue().encode())


def _finalize_bundle(folder):
    present = [name for name in ("config.json", "model.json", "result.json", "samples.csv",
                                  "emitted_scip_model.lp") if (folder / name).is_file()]
    digests = {name: sha256((folder / name).read_bytes()).hexdigest() for name in present}
    write_json(folder / "manifest.json", {
        "schema": SCHEMA, "sha256": digests,
        "source_sha256": SOURCE_SHA256,
        "immutable_inputs_and_outputs_checksums_only": True,
        "log_and_mutable_job_state_not_included_in_checksum_set": True,
    })


def execute_job(job_id, *, root=None):
    """Execute only a previously created, validated job; no shell from config."""
    root = Path(root) if root is not None else job_root()
    folder = job_dir(root, job_id)
    record = read_job(job_id, root=root)
    if record["status"] != "queued":
        raise JobError("Worker cannot run a nonqueued experiment")
    spec = record["spec"]
    # Check original submitted bytes once before any expensive work.
    submitted = record["config"]
    if submitted.get("source_sha256") != SOURCE_SHA256:
        raise JobError("Submitted research dataset changed")
    update_state(folder, "running", started_at=utc_now())
    start = time.perf_counter()
    try:
        check_cancel(folder)
        instance, model = _source_instance(spec, folder)
        check_cancel(folder)
        if spec.solver == "scip":
            solver_record, samples = _run_scip(instance, spec, folder)
        else:
            solver_record, samples = _run_sa(instance, spec, folder)
        check_cancel(folder)
        output = {
            "schema": SCHEMA, "job_id": job_id,
            "source_sha256": SOURCE_SHA256,
            "model_sha256": sha256((folder / "model.json").read_bytes()).hexdigest(),
            "configuration": spec.manifest(),
            "result": solver_record,
            "total_worker_wall_seconds": time.perf_counter() - start,
            "python_version": sys.version.split()[0],
            "software_versions": {
                package: package_version(package) for package in (
                    "numpy", "scipy", "shapely", "pyscipopt", "openjij", "streamlit",
                )
            },
            "numerical_thread_environment": {
                var: os.environ.get(var) for var in (
                    "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"
                )
            },
            "not_manuscript_parity_or_field_validated": True,
            "not_general_experimental_inference": True,
        }
        write_json(folder / "result.json", output)
        _write_samples_csv(folder, samples)
        _finalize_bundle(folder)
        update_state(folder, "completed", finished_at=utc_now(),
                     completed_reads=spec.reads if spec.solver == "classical_sa" else 1)
    except Cancelled:
        update_state(folder, "cancelled", finished_at=utc_now(),
                     error="Cancelled on operator request at bounded worker checkpoint")
    except Exception as exc:
        print("Research worker error:", repr(exc), file=sys.stderr, flush=True)
        traceback.print_exc()
        update_state(folder, "failed", finished_at=utc_now(),
                     error=f"{type(exc).__name__}: {str(exc)[:250]}")
    return load_json(folder / "state.json")


def export_bundle(job_id, *, root=None):
    record = read_job(job_id, root=root)
    if record["status"] != "completed":
        raise JobError("Only complete experiments have exportable original artifacts")
    folder = job_dir(Path(root) if root is not None else job_root(), job_id)
    manifest = load_json(folder / "manifest.json")
    for name, hexdigest in manifest["sha256"].items():
        if name not in FILES and name != "emitted_scip_model.lp":
            raise JobError("Unknown file listed in immutable experiment manifest")
        raw = (folder / name).read_bytes()
        if sha256(raw).hexdigest() != hexdigest:
            raise JobError("Stored scientific output has changed since completion")
    output = io.BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name in ("config.json", "model.json", "result.json", "samples.csv",
                     "emitted_scip_model.lp", "manifest.json"):
            path = folder / name
            if path.is_file():
                archive.write(path, name)
    if len(output.getvalue()) > MAX_JOB_ZIP_BYTES:
        raise JobError("Research evidence export exceeds bounded MVP limit")
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("worker",))
    parser.add_argument("--job", required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "worker":
        result = execute_job(args.job, root=args.root)
        print(json.dumps({"job_id": args.job, "status": result["status"]}))
        if result["status"] == "failed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
