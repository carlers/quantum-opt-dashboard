"""Independent objective, graph, archive tamper and source semantics gates."""
from __future__ import annotations

from hashlib import sha256
import io
import json
from zipfile import ZipFile

import pytest

from problems.water_quality.offline_scip_batch import (
    SCHEMA, archive_bundle, canonical, independent_witness, verify_bundle,
)


@pytest.fixture
def tiny_model():
    return {
        "schema": SCHEMA, "source_sha256": "synthetic-only",
        "N_free": 4, "K": 2, "graph": "historical local one-hop",
        "free_master_positions": [5, 11, 12, 13],
        "fixed_master_positions": [100],
        "linear_float64_hex": [float(v).hex() for v in (-1., -2., -3., -4.)],
        "quadratic_float64_hex": [[1, 3, (0.5).hex()]],
        "free_neighbors": [[1], [0, 3], [3], [1, 2]],
        "fixed_neighbors": [0, 1, 0, 0],
    }


def complete(tiny_model):
    result = {
        "schema": SCHEMA, "model_sha256": sha256(canonical(tiny_model)).hexdigest(),
        "classification": "optimal", "solver_status": "optimal",
        "binary_solution": [0, 1, 0, 1],
        "solver_objective": -5.5,
    }
    result["independent_audit"] = independent_witness(
        tiny_model, result["binary_solution"], result["solver_objective"]
    )
    return result


def test_original_energy_and_one_hop_independently_checked(tiny_model):
    result = complete(tiny_model)
    assert result["independent_audit"]["selected_local_positions"] == [1, 3]
    assert result["independent_audit"]["selected_master_positions"] == [11, 13]
    assert result["independent_audit"]["original_objective"] == -5.5
    assert result["independent_audit"]["budget_residual"] == 0
    with pytest.raises(ValueError):
        independent_witness(tiny_model, [0, 1, 0, 1], -5.0)
    with pytest.raises(ValueError):
        independent_witness(tiny_model, [0, 0, 0, 1], -4.0)
    with pytest.raises(ValueError):
        independent_witness(tiny_model, [1, 0, 0, 1], -5.0)
    with pytest.raises(ValueError):
        independent_witness(tiny_model, [0, True, 0, 1], -5.5)


def test_immutable_bundle_checksums_and_forged_optimality(tiny_model):
    result = complete(tiny_model)
    bundle = archive_bundle(tiny_model, result, b"\\ SCIP synthetic LP fixture\n")
    assert verify_bundle(bundle)["classification"] == "optimal"
    forged = dict(result, solver_status="timelimit")
    with pytest.raises(ValueError):
        verify_bundle(archive_bundle(tiny_model, forged, None))
    forged = dict(result, solver_objective=-5.6)
    with pytest.raises(ValueError):
        verify_bundle(archive_bundle(tiny_model, forged, None))
    corrupted = io.BytesIO()
    with ZipFile(corrupted, "w") as archive:
        with ZipFile(io.BytesIO(bundle)) as original:
            for name in original.namelist():
                raw = original.read(name)
                if name == "model.json":
                    raw += b" "
                archive.writestr(name, raw)
    with pytest.raises(ValueError):
        verify_bundle(corrupted.getvalue())


@pytest.mark.parametrize("classification", [
    "wall_timeout", "worker_exit_error", "no_incumbent", "solver_error",
])
def test_uncertified_runs_have_no_invented_witness(tiny_model, classification):
    result = {
        "schema": SCHEMA, "model_sha256": sha256(canonical(tiny_model)).hexdigest(),
        "classification": classification, "solver_status": None,
        "binary_solution": None, "solver_objective": None, "independent_audit": None,
    }
    assert verify_bundle(archive_bundle(tiny_model, result, None))["classification"] == classification
    result["binary_solution"] = [0, 1, 0, 1]
    with pytest.raises(ValueError):
        verify_bundle(archive_bundle(tiny_model, result, None))


def test_input_coefficients_are_hex_not_rounded(tiny_model):
    assert float.fromhex(tiny_model["linear_float64_hex"][0]) == -1.
    assert canonical(tiny_model) == canonical(json.loads(canonical(tiny_model)))
