"""Issue #108: opt-in actual routed original SCIP worker, no source rewrite.

Linux-only test controls. The true source SCIP compiler and mathematical
attestation remain independently pinned and unmodified. Opt-in is OFF by
default; local CI does not turn this on for production Cloud deployments.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from model import NOTEBOOK_WEIGHTS, load_data, make_instance, solve_scip
from prototypes.isolated_water_scip import (
    _admit, _bounded_command, _unpack, _validated_payload,
    solve_scip_bounded,
)

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
UNIFIED = ROOT / "prototypes/unified_dashboard/app.py"
EXPECTED = [0, 1, 3, 6, 7]

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux") or shutil.which("prlimit") is None,
    reason="Review-only original SCIP child requires Linux prlimit",
)


@pytest.fixture(scope="module")
def source_instance():
    data = load_data(DATA)
    instance, simulated = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    assert not simulated
    return instance


def test_original_model_float64_json_round_trip_without_pickle(source_instance):
    p = _validated_payload(source_instance)
    copy = _unpack(json.loads(json.dumps(p, sort_keys=True)))
    assert _validated_payload(copy) == p
    assert copy.budget == 5 and len(copy.fixed_indices) == 15
    assert np.array_equal(copy.coords, source_instance.coords)
    assert np.array_equal(copy.linear, source_instance.linear)
    assert np.array_equal(copy.fixed_neighbors, source_instance.fixed_neighbors)
    assert copy.quadratic == source_instance.quadratic


def test_admission_rejects_third_simultaneous_request_without_queuing():
    with _admit():
        with _admit():
            with pytest.raises(RuntimeError, match="two SCIP workers already active"):
                with _admit():
                    raise AssertionError("unsupported third concurrent solve")


def test_original_source_solver_actual_bounded_child_lp_and_evidence(tmp_path, source_instance):
    from scip_lp_structure import certify_emitted_scip_lp
    target = tmp_path / "actual-original-child.lp"
    selected, metrics = solve_scip_bounded(
        source_instance, time_limit=30.0, export_lp_path=target
    )
    assert metrics["status"] == "optimal"
    assert metrics["optimal"] is True and metrics["gap"] <= 1e-6
    assert np.flatnonzero(selected).tolist() == EXPECTED
    lp = target.read_bytes()
    assert 0 < len(lp) <= 100000
    certificate = certify_emitted_scip_lp(source_instance, lp)
    assert certificate["original_scip_lp_sha256"] == sha256(lp).hexdigest()
    assert certificate["each_original_local_one_hop_verified"] is True


def test_bad_child_request_digest_refused_without_running_scip(tmp_path):
    model_request = tmp_path / "request.json"
    output_lp = tmp_path / "should-not-exist.lp"
    response_file = tmp_path / "should-not-exist.json"
    model_request.write_bytes(b'{"schema":1,"bad":"input"}\n')
    command = _bounded_command(
        model_request, "0" * 64, output_lp, response_file, "a" * 32
    )
    result = subprocess.run(
        command, cwd=tmp_path, capture_output=True, text=True, timeout=25,
    )
    assert result.returncode != 0
    assert not output_lp.exists()
    assert not response_file.exists()
    assert "digest mismatch" in result.stderr


def test_two_independent_thread_sessions_both_use_child_boundary(source_instance):
    """Actual two results; gate-overlap and kernel limits are separately proven in #119."""
    with ThreadPoolExecutor(max_workers=2) as workers:
        futures = [workers.submit(solve_scip_bounded, source_instance,
                                  time_limit=30.0) for _ in range(2)]
        answers = [x.result(timeout=95) for x in futures]
    assert all(np.flatnonzero(chosen).tolist() == EXPECTED
               and metrics["status"] == "optimal" for chosen, metrics in answers)
    assert answers[0][0] is not answers[1][0]


def test_opted_in_unified_streamlit_scip_runs_out_of_process_and_retains_archive(
    monkeypatch,
):
    from io import BytesIO
    from zipfile import ZipFile

    monkeypatch.setenv("QOPT_REVIEW_BOUNDED_SCIP", "1")
    app = AppTest.from_file(str(UNIFIED), default_timeout=120).run()
    assert not app.exception, app.exception
    assert "mvp_result" not in app.session_state
    app.button(key="mvp_run").click().run()
    assert not app.exception, app.exception
    result = app.session_state["mvp_result"]
    assert result["metrics"]["status"] == "optimal"
    assert result["independent"]["selected_local_positions"] == EXPECTED
    assert result["attestation"]["strictly_bound_to_compiled_current_run"] is True
    assert result["attestation"]["parsed_original_scip_lp_formulation"][
        "budget_equal_K_verified"
    ] is True
    with ZipFile(BytesIO(result["zip"])) as archive:
        assert "actual_scip_model.lp" in archive.namelist()
        model = json.loads(archive.read("model.json"))
        assert model["model_fingerprint_sha256"] == result["fingerprint"]
