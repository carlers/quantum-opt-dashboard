"""Experimental opt-in Linux subprocess boundary for the original water SCIP solver.

No pickle, untrusted code paths, in-process fallback or science source rewrite.
Only N20/15-fixed original-source Instance with explicit hex-float JSON may
cross the boundary. Stage 11 proved Linux prlimit on separate LP re-solvers;
this stage actually runs the ORIGINAL model.solve_scip in a bounded child.
Not an arbitrary-Python security sandbox, cgroup RAM cap or trusted signer.
"""
from __future__ import annotations

from contextlib import contextmanager
import argparse
import fcntl
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory, gettempdir
from typing import Iterator

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WORKER = Path(__file__).resolve()
CPU_SOFT = 55
CPU_HARD = 60
AS_BYTES = 4 * 1024**3
FSIZE_BYTES = 1024**2
NOFILE = 256
WALL_SECONDS = 75
REQUEST_LIMIT = 160_000
LP_LIMIT = 100_000
RESPONSE_LIMIT = 24_000
SLOTS = 2
SCHEMA = 1


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError("Bounded water SCIP (review only): " + message)


def _hex(value) -> str:
    x = float(value)
    _require(math.isfinite(x), "nonfinite source scientific value")
    return x.hex()


def _float(value) -> float:
    _require(type(value) is str and len(value) <= 32, "not a finite source hex-float")
    try:
        x = float.fromhex(value)
    except ValueError as exc:
        raise RuntimeError("malformed source float") from exc
    _require(math.isfinite(x) and x.hex() == value, "noncanonical source float")
    return x


def _integers(source, count: int, bound: int) -> list[int]:
    _require(type(source) is list and len(source) == count, "invalid source integer vector")
    _require(all(type(v) is int and 0 <= v < bound for v in source),
             "source integer out of bounds")
    return source


def _validated_payload(instance) -> dict:
    from model import Instance
    _require(type(instance) is Instance, "requires the exact original model.Instance class")
    n, m = len(instance.free_indices), len(instance.fixed_indices)
    _require(n == 20 and m == 15 and type(instance.budget) is int
             and 0 <= instance.budget <= n, "only actual original N20/15-fixed instances")
    _require(np.asarray(instance.coords).shape == (n + m, 2)
             and np.asarray(instance.utility).shape == (n + m,)
             and np.asarray(instance.linear).shape == (n,)
             and np.asarray(instance.fixed_neighbors).shape == (n,),
             "source model array shapes changed")
    free = [int(x) for x in instance.free_indices]
    fixed = [int(x) for x in instance.fixed_indices]
    _require(all(x >= 0 for x in free + fixed)
             and len(set(free + fixed)) == n + m, "duplicate/invalid source site ids")
    _require(len(instance.neighbors) == n and len(instance.quadratic) <= n * (n - 1) // 2,
             "source local graph dimensions changed")
    adjacency = []
    for i, row in enumerate(instance.neighbors):
        values = [int(j) for j in row]
        _require(all(0 <= j < n and j != i for j in values)
                 and values == sorted(set(values)), "invalid source neighbor list")
        adjacency.append(values)
    fixed_neighbors = [int(x) for x in instance.fixed_neighbors]
    _require(all(x in (0, 1) for x in fixed_neighbors),
             "invalid source fixed-station links")
    quadratic = []
    for i, j, q in instance.quadratic:
        _require(type(i) is int and type(j) is int and 0 <= i < j < n,
                 "invalid original source pair index")
        quadratic.append([i, j, _hex(q)])
    _require(len({(i, j) for i, j, _ in quadratic}) == len(quadratic),
             "duplicate source quadratic pair")
    return {
        "coords": [[_hex(v) for v in row] for row in instance.coords],
        "free_indices": free, "fixed_indices": fixed,
        "utility": [_hex(v) for v in instance.utility],
        "linear": [_hex(v) for v in instance.linear],
        "quadratic": quadratic, "neighbors": adjacency,
        "fixed_neighbors": fixed_neighbors,
        "budget": instance.budget, "d_max": _hex(instance.d_max),
    }


def _unpack(payload: dict):
    from model import Instance
    _require(type(payload) is dict, "invalid source instance payload")
    _require(set(payload) == {
        "coords", "free_indices", "fixed_indices", "utility", "linear",
        "quadratic", "neighbors", "fixed_neighbors", "budget", "d_max",
    }, "unexpected source instance fields")
    _require(type(payload["coords"]) is list and len(payload["coords"]) == 35
             and all(type(row) is list and len(row) == 2 for row in payload["coords"]),
             "invalid source coordinate rows")
    _require(type(payload["utility"]) is list and len(payload["utility"]) == 35
             and type(payload["linear"]) is list and len(payload["linear"]) == 20,
             "invalid objective array sizes")
    free = _integers(payload["free_indices"], 20, 100000)
    fixed = _integers(payload["fixed_indices"], 15, 100000)
    _require(len(set(free + fixed)) == 35, "duplicate source site ids")
    _require(type(payload["quadratic"]) is list and len(payload["quadratic"]) <= 190,
             "invalid source pair count")
    _require(type(payload["neighbors"]) is list and len(payload["neighbors"]) == 20,
             "invalid source neighbor count")
    quadratic = []
    for row in payload["quadratic"]:
        _require(type(row) is list and len(row) == 3
                 and type(row[0]) is int and type(row[1]) is int
                 and 0 <= row[0] < row[1] < 20, "malformed source pair")
        quadratic.append((row[0], row[1], _float(row[2])))
    neighbors = []
    for i, row in enumerate(payload["neighbors"]):
        _require(type(row) is list and len(row) <= 19
                 and all(type(v) is int and 0 <= v < 20 and v != i for v in row)
                 and row == sorted(set(row)), "malformed source local neighbor set")
        neighbors.append(tuple(row))
    fixed_neighbors = _integers(payload["fixed_neighbors"], 20, 2)
    _require(type(payload["budget"]) is int and 0 <= payload["budget"] <= 20,
             "invalid source budget")
    instance = Instance(
        np.asarray([[_float(x) for x in row] for row in payload["coords"]], dtype=np.float64),
        np.asarray(free, dtype=np.int64), np.asarray(fixed, dtype=np.int64),
        np.asarray([_float(x) for x in payload["utility"]], dtype=np.float64),
        np.asarray([_float(x) for x in payload["linear"]], dtype=np.float64),
        tuple(quadratic), tuple(neighbors), np.asarray(fixed_neighbors, dtype=np.int64),
        payload["budget"], _float(payload["d_max"]),
    )
    _require(_validated_payload(instance) == payload, "source payload failed exact roundtrip")
    return instance


@contextmanager
def _admit() -> Iterator[int]:
    """At most two bounded children on this Linux user host; no queue or fairness."""
    _require(sys.platform.startswith("linux"), "Linux only, no unsafe platform fallback")
    chosen = None
    for slot in range(SLOTS):
        name = Path(gettempdir()) / ("qopt_issue108_bounded_scip_uid"
                                     + str(os.getuid()) + "_slot_" + str(slot) + ".lock")
        flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(name, flags, 0o600)
        try:
            record = os.fstat(fd)
            _require(record.st_uid == os.getuid() and record.st_mode & 0o777 == 0o600,
                     "insecure admission-control lock file owner or permissions")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                os.close(fd)
                continue
            chosen = fd
            break
        except BaseException:
            if chosen != fd:
                try:
                    os.close(fd)
                except OSError:
                    pass
            raise
    _require(chosen is not None, "two SCIP workers already active; retry after completion")
    try:
        yield chosen
    finally:
        fcntl.flock(chosen, fcntl.LOCK_UN)
        os.close(chosen)


def _bounded_command(input_path: Path, digest: str, lp_path: Path,
                     response_path: Path, nonce: str) -> list[str]:
    binary = shutil.which("prlimit")
    _require(binary is not None and sys.platform.startswith("linux"),
             "Linux util-linux prlimit required; never run unbounded")
    return [
        binary, f"--cpu={CPU_SOFT}:{CPU_HARD}",
        f"--as={AS_BYTES}:{AS_BYTES}", f"--fsize={FSIZE_BYTES}:{FSIZE_BYTES}",
        f"--nofile={NOFILE}:{NOFILE}", "--",
        sys.executable, "-I", str(WORKER), "--child",
        "--input", str(input_path), "--digest", digest,
        "--lp", str(lp_path), "--response", str(response_path), "--nonce", nonce,
    ]


def _kill(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    proc.wait(timeout=5)


def solve_scip_bounded(instance, *, time_limit: float = 30.0,
                       export_lp_path: str | Path | None = None):
    """Same (selected np.ndarray, original metrics) return contract as source SCIP."""
    from model import evaluate
    from scip_lp_structure import certify_emitted_scip_lp
    from prototypes.water_import_guard import require_water_import_origins
    require_water_import_origins()
    _require(type(time_limit) in (int, float) and time_limit == 30.0,
             "only the existing original 30-second SCIP time bound is supported")
    payload = _validated_payload(instance)
    from model import __file__ as model_file
    model_sha = sha256(Path(model_file).read_bytes()).hexdigest()
    from secrets import token_hex
    nonce = token_hex(16)
    envelope = {
        "schema": SCHEMA, "kind": "ORIGINAL_N20_HEX_FLOAT_INSTANCE",
        "model_source_sha256": model_sha,
        "nonce": nonce, "instance": payload,
    }
    raw = (json.dumps(envelope, sort_keys=True, separators=(",", ":"), allow_nan=False)
           + "\n").encode("utf-8")
    _require(0 < len(raw) <= REQUEST_LIMIT, "source model request exceeds bound")
    request_sha = sha256(raw).hexdigest()
    with _admit():
        with TemporaryDirectory(prefix="qopt_issue108_live_scip_") as location:
            directory = Path(location)
            request_file, lp_file = directory / "request.json", directory / "original.lp"
            response_file = directory / "response.json"
            output, error = directory / "child.stdout", directory / "child.stderr"
            request_file.write_bytes(raw)
            with output.open("wb") as out, error.open("wb") as err:
                proc = subprocess.Popen(
                    _bounded_command(request_file, request_sha, lp_file, response_file, nonce),
                    cwd=ROOT, stdout=out, stderr=err, start_new_session=True,
                    close_fds=True,
                    env={**os.environ, "OPENBLAS_NUM_THREADS": "1",
                         "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"},
                )
            try:
                try:
                    proc.wait(timeout=WALL_SECONDS)
                except subprocess.TimeoutExpired as exc:
                    raise RuntimeError("SCIP child exceeded 75-second wall deadline") from exc
                _require(proc.returncode == 0, "SCIP child failed under Linux resource limits"
                         + ": " + error.read_text(encoding="utf-8", errors="replace")[:500])
                # SCIP/PySCIPOpt may print C-level diagnostics to stdout
                # despite hideOutput(); stdout is NEVER the JSON protocol.
                _require(output.stat().st_size <= FSIZE_BYTES
                         and error.stat().st_size <= FSIZE_BYTES,
                         "SCIP child diagnostic log exceeds bound")
                _require(response_file.is_file() and not response_file.is_symlink()
                         and 0 < response_file.stat().st_size <= RESPONSE_LIMIT,
                         "dedicated bounded child JSON receipt is missing or excessive")
                response = json.loads(response_file.read_text(encoding="utf-8"))
                _require(type(response) is dict and response.get("schema") == SCHEMA
                         and response.get("kind") == "ORIGINAL_N20_LOCAL_SCIP_BOUNDED_CHILD"
                         and response.get("input_sha256") == request_sha
                         and response.get("nonce") == nonce
                         and response.get("model_source_sha256") == model_sha
                         and response.get("original_solver_called") is True
                         and response.get("remote_authenticated") is False
                         and response.get("observed_linux_rlimits") == {
                             "cpu": [CPU_SOFT, CPU_HARD],
                             "as": [AS_BYTES, AS_BYTES],
                             "fsize": [FSIZE_BYTES, FSIZE_BYTES],
                             "nofile": [NOFILE, NOFILE],
                         },
                         "child response does not bind exact source input and process scope")
                bits = response.get("selected")
                _require(type(bits) is list and len(bits) == 20
                         and all(type(x) is int and x in (0, 1) for x in bits),
                         "child did not return 20 original binary decisions")
                chosen = np.asarray(bits, dtype=int)
                metrics = response.get("metrics")
                source_checks = evaluate(instance, chosen)
                _require(type(metrics) is dict
                         and all(metrics.get(k) == source_checks[k] for k in (
                             "num_selected", "budget_ok", "connectivity_ok",
                             "isolated", "feasible"))
                         and type(metrics.get("energy")) in (int, float)
                         and math.isclose(float(metrics["energy"]), source_checks["energy"],
                                          rel_tol=0, abs_tol=1e-7)
                         and metrics.get("feasible") is True
                         and type(metrics.get("status")) is str
                         and metrics.get("optimal") == (metrics["status"] == "optimal")
                         and type(metrics.get("gap")) in (float, int)
                         and math.isfinite(metrics["gap"])
                         and metrics["gap"] >= 0,
                         "child original SCIP output failed parent source feasibility check")
                _require(lp_file.is_file() and not lp_file.is_symlink()
                         and 0 < lp_file.stat().st_size <= LP_LIMIT,
                         "original child SCIP LP missing or excessive")
                lp = lp_file.read_bytes()
                _require(response.get("lp_sha256") == sha256(lp).hexdigest(),
                         "source LP digest mismatch across child boundary")
                certificate = certify_emitted_scip_lp(instance, lp)
                _require(certificate["original_scip_lp_sha256"] == response["lp_sha256"],
                         "actual child emitted SCIP LP differs from parent source model")
                if export_lp_path is not None:
                    destination = Path(export_lp_path)
                    _require(destination.suffix == ".lp" and not destination.is_symlink(),
                             "refuse unsafe result LP destination")
                    destination.write_bytes(lp)
                return chosen, metrics
            finally:
                _kill(proc)


def _child(input_file: Path, digest: str, lp_file: Path,
           response_file: Path, nonce: str) -> None:
    import resource
    from prototypes.water_import_guard import require_water_import_origins
    require_water_import_origins()
    from model import Instance, solve_scip, __file__ as model_file
    limits = {
        "cpu": list(resource.getrlimit(resource.RLIMIT_CPU)),
        "as": list(resource.getrlimit(resource.RLIMIT_AS)),
        "fsize": list(resource.getrlimit(resource.RLIMIT_FSIZE)),
        "nofile": list(resource.getrlimit(resource.RLIMIT_NOFILE)),
    }
    expected = {
        "cpu": [CPU_SOFT, CPU_HARD], "as": [AS_BYTES, AS_BYTES],
        "fsize": [FSIZE_BYTES, FSIZE_BYTES], "nofile": [NOFILE, NOFILE],
    }
    _require(limits == expected, "kernel process resource limits missing")
    _require(input_file.is_file() and not input_file.is_symlink()
             and 0 < input_file.stat().st_size <= REQUEST_LIMIT,
             "invalid bounded source input")
    raw = input_file.read_bytes()
    _require(sha256(raw).hexdigest() == digest, "source request digest mismatch")
    data = json.loads(raw)
    _require(type(data) is dict and set(data) == {
        "schema", "kind", "model_source_sha256", "nonce", "instance"
    } and data["schema"] == SCHEMA
             and data["kind"] == "ORIGINAL_N20_HEX_FLOAT_INSTANCE"
             and data["nonce"] == nonce
             and data["model_source_sha256"] == sha256(Path(model_file).read_bytes()).hexdigest(),
             "source model identity or session nonce did not match")
    instance = _unpack(data["instance"])
    chosen, metrics = solve_scip(instance, time_limit=30.0, export_lp_path=lp_file)
    _require(lp_file.is_file() and lp_file.stat().st_size <= LP_LIMIT,
             "original emitted LP exceeds bound")
    response = {
        "schema": SCHEMA, "kind": "ORIGINAL_N20_LOCAL_SCIP_BOUNDED_CHILD",
        "input_sha256": digest, "nonce": nonce,
        "model_source_sha256": data["model_source_sha256"],
        "selected": [int(v) for v in chosen], "metrics": metrics,
        "lp_sha256": sha256(lp_file.read_bytes()).hexdigest(),
        "observed_linux_rlimits": limits,
        "original_solver_called": True, "remote_authenticated": False,
    }
    # Separate JSON protocol from any native solver stdout diagnostics.
    _require(not response_file.exists() and response_file.parent == lp_file.parent,
             "child receipt path must be unused and next to original LP")
    encoded = (json.dumps(response, sort_keys=True, separators=(",", ":"),
                          allow_nan=False) + "\n").encode("utf-8")
    _require(len(encoded) <= RESPONSE_LIMIT, "child JSON receipt exceeds bound")
    response_file.write_bytes(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--digest")
    parser.add_argument("--lp", type=Path)
    parser.add_argument("--response", type=Path)
    parser.add_argument("--nonce")
    args = parser.parse_args()
    _require(args.child and args.input is not None and args.lp is not None
             and args.response is not None
             and type(args.digest) is str and len(args.digest) == 64
             and type(args.nonce) is str and len(args.nonce) == 32,
             "no standalone UI invocation allowed for this internal child")
    _child(args.input, args.digest, args.lp, args.response, args.nonce)


if __name__ == "__main__":
    main()
