"""Fail-closed artifacts and scientific claim boundaries for M3 report."""
from __future__ import annotations

import io
import json
from zipfile import ZipFile

import pytest

from problems.water_quality.offline_resolution_report import (
    _check_receipt, extract_verified_rows,
)


def _zip(files):
    stream = io.BytesIO()
    with ZipFile(stream, "w") as out:
        for name, payload in files.items():
            out.writestr(name, payload)
    return stream.getvalue()


def _receipt():
    return {
        "schema": "independent-source-lp-highs-v1",
        "N_free": 50, "K": 5, "source_sha256": "pinned",
        "model_sha256": "model-hash", "actual_exported_LP_sha256": "lp-hash",
        "scip_status": "optimal", "highs_status": 0,
        "independent_computational_optimality_corroboration": True,
        "formal_proof_certificate": False, "paper_input_parity_claimed": False,
        "scip_objective": -3.0, "highs_primal_objective": -3.0,
        "highs_dual_bound": -3.0, "highs_relative_gap": 0.0,
    }


def test_precise_receipt_and_numerical_tolerance():
    receipt = _receipt()
    _check_receipt(receipt, receipt)
    rounded = dict(receipt, highs_dual_bound=-3.00000001)
    _check_receipt(rounded, receipt)


@pytest.mark.parametrize("key,changed", [
    ("source_sha256", "different-dataset"),
    ("model_sha256", "forged"),
    ("actual_exported_LP_sha256", "different-lp"),
    ("highs_status", 1),
    ("formal_proof_certificate", True),
    ("paper_input_parity_claimed", True),
    ("scip_status", "timelimit"),
    ("highs_dual_bound", -6.0),
])
def test_rejects_forged_identity_or_unsupported_claim(key, changed):
    validated = _receipt()
    forged = dict(validated, **{key: changed})
    with pytest.raises(ValueError):
        _check_receipt(forged, validated)


def test_rejects_empty_or_duplicated_workflow_zip():
    for raw in (b"", b"bad"):
        with pytest.raises((ValueError, OSError)):
            extract_verified_rows(raw)
    with pytest.raises(ValueError):
        extract_verified_rows(_zip({"unrelated.txt": b"nothing"}))


def test_rejects_incorrect_second_solver_scope_before_processing():
    artifact = _zip({
        "source-execution.zip": b"not-an-archive",
        "highs-bound-receipt.json": json.dumps({
            "schema": "untrusted-third-party", "runs": []
        }).encode(),
    })
    with pytest.raises(ValueError, match="unexpected second-solver proof scope"):
        extract_verified_rows(artifact)
