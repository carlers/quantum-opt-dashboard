"""Review-only Linux resource-bounded concurrency proof for the ORIGINAL N20 LP.

Two simultaneously released new Python processes read and optimize the same
actual source-emitted SCIP LP using the UNCHANGED independent LP worker.
This script is NOT invoked by any live Streamlit solver route, and its
OS bounds do not certify production per-user resource isolation.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "prototypes/streamlit_water_quality/scip_lp_reexecution_worker.py"
DATA = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
CPU_SOFT = 55
CPU_HARD = 60
AS_BYTES = 4 * 1024**3
FSIZE_BYTES = 1024**2
NOFILE = 256
SCIP_TIME_LIMIT = 30
WALL_SECONDS = 75
LP_LIMIT = 100_000
LIMITS = {
    "cpu": [CPU_SOFT, CPU_HARD],
    "as": [AS_BYTES, AS_BYTES],
    "fsize": [FSIZE_BYTES, FSIZE_BYTES],
    "nofile": [NOFILE, NOFILE],
}


def _require(ok: bool, why: str) -> None:
    if not ok:
        raise RuntimeError("Issue108 Linux isolated worker: " + why)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _entry(gate: Path, ready: Path, limits_file: Path, lp: Path, digest: str) -> None:
    """The prlimit child inherits limits BEFORE executing any PySCIPOpt code."""
    observed = {
        "cpu": list(resource.getrlimit(resource.RLIMIT_CPU)),
        "as": list(resource.getrlimit(resource.RLIMIT_AS)),
        "fsize": list(resource.getrlimit(resource.RLIMIT_FSIZE)),
        "nofile": list(resource.getrlimit(resource.RLIMIT_NOFILE)),
    }
    _require(observed == LIMITS, "OS enforced limits differ from declared bounds")
    limits_file.write_text(json.dumps(observed, sort_keys=True) + "\n", encoding="utf-8")
    ready.write_text(str(os.getpid()) + "\n", encoding="utf-8")
    deadline = time.monotonic() + 20
    while not gate.is_file():
        _require(time.monotonic() < deadline, "parent never released overlap gate")
        time.sleep(0.02)
    # execv replaces this process image; CPU, AS, file and descriptor limits
    # survive exec. Never use a shell, dynamic worker path or sys.modules alias.
    os.execv(sys.executable, [
        sys.executable, "-I", str(WORKER),
        "--lp", str(lp), "--expect-sha256", digest,
        "--time-limit-seconds", str(SCIP_TIME_LIMIT),
    ])


def _bounded_command(gate: Path, ready: Path, limits_file: Path, lp: Path,
                     digest: str) -> list[str]:
    program = shutil.which("prlimit")
    _require(program is not None and sys.platform.startswith("linux"),
             "Linux util-linux prlimit is mandatory, no unbounded fallback")
    return [
        program,
        f"--cpu={CPU_SOFT}:{CPU_HARD}",
        f"--as={AS_BYTES}:{AS_BYTES}",
        f"--fsize={FSIZE_BYTES}:{FSIZE_BYTES}",
        f"--nofile={NOFILE}:{NOFILE}",
        "--",
        sys.executable, "-I", str(Path(__file__).resolve()),
        "--child-gate", "--gate", str(gate), "--ready", str(ready),
        "--limits-file", str(limits_file), "--lp", str(lp), "--digest", digest,
    ]


def _kill_group(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        # An unkillable process is an infrastructure failure, not success.
        raise RuntimeError("unable to reap bounded process after SIGKILL")


def _run_two(lp: Path, digest: str, instance, chosen, metrics, folder: Path) -> list[dict]:
    from scip_lp_reexecution import check_independent_process_receipt

    gate = folder / "start-gate"
    spawned = []
    try:
        for slot in range(2):
            prefix = folder / f"worker-{slot}"
            ready, limits_file = Path(str(prefix) + ".ready"), Path(str(prefix) + ".limits.json")
            stdout, stderr = Path(str(prefix) + ".stdout"), Path(str(prefix) + ".stderr")
            out = stdout.open("wb")
            err = stderr.open("wb")
            try:
                proc = subprocess.Popen(
                    _bounded_command(gate, ready, limits_file, lp, digest),
                    stdout=out, stderr=err, cwd=folder, start_new_session=True,
                    close_fds=True,
                    env={
                        **os.environ,
                        "OPENBLAS_NUM_THREADS": "1",
                        "OMP_NUM_THREADS": "1",
                        "MKL_NUM_THREADS": "1",
                    },
                )
            finally:
                out.close()
                err.close()
            spawned.append((proc, ready, limits_file, stdout, stderr))
        deadline = time.monotonic() + 25
        while not all(ready.is_file() for _, ready, _, _, _ in spawned):
            _require(time.monotonic() < deadline, "worker did not reach shared gate")
            _require(all(p.poll() is None for p, _, _, _, _ in spawned),
                     "a worker exited before both were ready")
            time.sleep(0.02)
        _require(len({p.pid for p, _, _, _, _ in spawned}) == 2,
                 "two distinct OS process IDs not observed")
        _require(all(p.poll() is None for p, _, _, _, _ in spawned),
                 "workers did not overlap while blocked on same gate")
        # Ensure actual OS limits were observed from within BOTH children.
        for _, _, limits_file, _, _ in spawned:
            _require(_json(limits_file) == LIMITS,
                     "child's actual kernel resource limits differ")
        released_at = time.monotonic()
        gate.write_text("release-both\n", encoding="utf-8")
        observations = []
        for slot, (proc, ready, limits_file, out, err) in enumerate(spawned):
            remaining = WALL_SECONDS - (time.monotonic() - released_at)
            _require(remaining > 0, "shared wall-clock deadline exhausted")
            try:
                proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("bounded SCIP child exceeded OS wall time") from exc
            _require(proc.returncode == 0, f"bounded SCIP process {slot} failed: {err.read_text(encoding='utf-8', errors='replace')[:1500]}")
            _require(0 < out.stat().st_size <= 24_000, "worker stdout missing or excessive")
            _require(err.stat().st_size <= FSIZE_BYTES, "worker stderr exceeds bounded output")
            recorded = _json(out)
            checked = check_independent_process_receipt(
                instance, lp.read_bytes(), recorded, chosen, metrics
            )
            observations.append({
                "slot": slot,
                "pid": proc.pid,
                "returncode": proc.returncode,
                "observed_rlimits": _json(limits_file),
                "stdout_sha256": sha256(out.read_bytes()).hexdigest(),
                "stderr_sha256": sha256(err.read_bytes()).hexdigest(),
                "child_status": recorded["status"],
                "child_selected_indices": checked["independent_child_selected_indices"],
                "original_local_feasible": checked["second_process_selected_original_graph_feasible"],
                "independent_optimum_exactly_checked": checked["replay_status_source_math_crosschecked"],
                "original_execution_authenticated": False,
            })
        return observations
    finally:
        # Even if worker 0 fails before wait on worker 1, kill *both* process
        # groups and reap them. A SCIP time limit is not process cleanup.
        for proc, _, _, _, _ in spawned:
            _kill_group(proc)


def _run(output: Path) -> None:
    from model import NOTEBOOK_WEIGHTS, load_data, make_instance, solve_scip
    from scip_lp_structure import certify_emitted_scip_lp

    _require(sys.platform.startswith("linux") and shutil.which("prlimit") is not None,
             "test requires Linux util-linux prlimit")
    _require(not output.exists(), "refuse overwriting previous observed evidence")
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="qopt_issue108_scip_", dir=str(output.parent)) as dirname:
        folder = Path(dirname)
        data = load_data(DATA)
        instance, simulated = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
        _require(not simulated, "original source N20 scenario was simulated")
        lp = folder / "actual-original-scip.lp"
        first_selected, first_metrics = solve_scip(
            instance, time_limit=SCIP_TIME_LIMIT, export_lp_path=lp
        )
        _require(first_metrics.get("status") == "optimal"
                 and first_metrics.get("feasible") is True,
                 "upstream source SCIP did not prove local model optimum")
        raw_lp = lp.read_bytes()
        _require(0 < len(raw_lp) <= LP_LIMIT, "source emitted LP outside bounded worker size")
        evidence = certify_emitted_scip_lp(instance, raw_lp)
        expected_digest = sha256(raw_lp).hexdigest()
        _require(evidence["original_scip_lp_sha256"] == expected_digest,
                 "original LP structural certificate does not match source bytes")
        results = _run_two(lp, expected_digest, instance,
                           first_selected, first_metrics, folder)
        import subprocess as _subprocess
        sha = _subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        report = {
            "schema_version": 1,
            "kind": "REVIEW_ONLY_LINUX_TWO_BOUND_SCIP_LP_WORKERS",
            "actual_git_checkout_sha": sha,
            "source_pr_head_sha": os.getenv("PR_HEAD_SHA"),
            "original_lp_sha256": expected_digest,
            "source_lp_bytes": len(raw_lp),
            "original_model": "N20 K5 local one-hop, NOT global all-stations model",
            "original_scip_status": first_metrics["status"],
            "two_distinct_processes_simultaneously_waited_at_gate": True,
            "linux_limits_from_inside_children": LIMITS,
            "wall_clock_seconds_max": WALL_SECONDS,
            "workers": results,
            "unverified": [
                "No Streamlit production routing or per-user worker pool integration",
                "No measured enforcement of memory exhaustion under attack",
                "No protected qualified-namespace isolation, remote attestation or signature",
                "No portable Windows/macOS resource isolation or native wheel lock",
                "No source paper AHP/D2 parity, field RF/backhaul/DO/current or quantum advantage",
            ],
        }
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--child-gate", action="store_true")
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--ready", type=Path)
    parser.add_argument("--limits-file", type=Path)
    parser.add_argument("--lp", type=Path)
    parser.add_argument("--digest")
    args = parser.parse_args()
    if args.child_gate:
        _require(all((args.gate, args.ready, args.limits_file, args.lp, args.digest)),
                 "missing child worker arguments")
        _entry(args.gate, args.ready, args.limits_file, args.lp, args.digest)
    else:
        _require(args.output is not None, "--output required")
        _run(args.output)


if __name__ == "__main__":
    main()
