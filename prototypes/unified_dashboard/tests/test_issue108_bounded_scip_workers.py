"""Issue #108: actual Linux OS constraints and cleanup on an UNRELEASED child.

This negative test never runs SCIP and cannot certify live Streamlit routing.
The separate dedicated workflow runs two real concurrent SCIP LP workers.
"""
from __future__ import annotations

from importlib import util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/issue108_bounded_scip_concurrency.py"

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux") or shutil.which("prlimit") is None,
    reason="Review-only Linux util-linux prlimit OS resource test",
)


def _probe():
    spec = util.spec_from_file_location("issue108_bounded_worker", SCRIPT)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_os_limits_are_applied_before_exec_and_parent_kills_child_group(tmp_path):
    """Gated bounded worker must be live, limited and reaped when cancelled."""
    module = _probe()
    gate = tmp_path / "never-opened"
    ready = tmp_path / "ready"
    limits_file = tmp_path / "limits.json"
    lp = tmp_path / "not-even-created.lp"
    out, err = tmp_path / "stdout.txt", tmp_path / "stderr.txt"
    with out.open("wb") as stdout, err.open("wb") as stderr:
        process = subprocess.Popen(
            module._bounded_command(gate, ready, limits_file, lp, "0" * 64),
            cwd=tmp_path, stdout=stdout, stderr=stderr,
            start_new_session=True, close_fds=True,
        )
    try:
        deadline = time.monotonic() + 12
        while not ready.is_file():
            assert time.monotonic() < deadline, err.read_text(errors="replace")
            assert process.poll() is None, err.read_text(errors="replace")
            time.sleep(.025)
        assert process.poll() is None
        assert int(ready.read_text().strip()) == process.pid
        observed = json.loads(limits_file.read_text())
        assert observed == module.LIMITS
        assert "cpu" in observed and "as" in observed
        assert "nofile" in observed and "fsize" in observed
        assert not gate.exists()
        # The child's only route to SCIP is the unopened gate; this is a
        # deliberate timeout/cancellation control rather than solver proof.
    finally:
        module._kill_group(process)
    assert process.poll() is not None
    assert process.returncode != 0
    assert not lp.exists()


def test_worker_source_path_and_runtime_limits_are_fixed():
    module = _probe()
    assert module.WORKER == (
        ROOT / "prototypes/streamlit_water_quality/scip_lp_reexecution_worker.py"
    )
    assert module.LP_LIMIT == 100_000
    assert module.WALL_SECONDS < 120
    assert module.CPU_SOFT < module.CPU_HARD
    assert module.AS_BYTES > 0
    assert module.NOFILE <= 256
    assert module.FSIZE_BYTES <= 1_048_576
    assert module.SCIP_TIME_LIMIT == 30
