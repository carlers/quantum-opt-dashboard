"""M2 report rejects missing/forged experimental data before drawing heatmaps."""
from __future__ import annotations

from copy import deepcopy
import io
import json
from zipfile import ZipFile

import pytest

from problems.water_quality.penalty_grid_report import inspect_archive
from problems.water_quality.independent_penalty_grid import SCHEMA, SOURCE_SHA256


def zipped(files):
    out = io.BytesIO()
    with ZipFile(out, "w") as bundle:
        for name, value in files.items():
            bundle.writestr(name, value)
    return out.getvalue()


def test_missing_or_invalid_archive_is_not_faked_as_success():
    for raw in (b"", b"bad", b"no complete source samples"):
        with pytest.raises(ValueError):
            inspect_archive(raw)
    with pytest.raises(ValueError, match="incomplete"):
        inspect_archive(zipped({"summary.json": b"{}"}))


def test_bad_source_schema_is_rejected_before_looking_up_sample_rows():
    evidence = zipped({
        "summary.json": b"{}",
        "trials.csv": b"grid_index\n",
        "samples.csv": b"grid_index\n",
        "compiled_source_model.json": b"{}",
        "SHA256SUMS.json": json.dumps({
            "schema": SCHEMA, "source_sha256": "NOT-the-original-source",
            "file_sha256": {},
        }),
    })
    with pytest.raises(ValueError, match="checksum/source"):
        inspect_archive(evidence)


def test_changed_archive_member_fails_sha256_chain():
    content = {
        "summary.json": b'{"source_sha256":"historical"}\n',
        "trials.csv": b"grid_index\n",
        "samples.csv": b"grid_index\n",
        "compiled_source_model.json": b"{}",
    }
    hashes = {name: __import__("hashlib").sha256(raw).hexdigest()
              for name, raw in content.items()}
    checks = {"schema": SCHEMA, "source_sha256": SOURCE_SHA256, "file_sha256": hashes}
    changed = deepcopy(content)
    changed["samples.csv"] = b"grid_index\nFORGED\n"
    changed["SHA256SUMS.json"] = json.dumps(checks).encode()
    with pytest.raises(ValueError, match="checksum mismatch"):
        inspect_archive(zipped(changed))
