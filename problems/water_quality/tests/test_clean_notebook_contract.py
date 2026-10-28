"""Fast notebook/source invariants for the legacy water-quality CI test gate.

The slow PySCIPOpt execution belongs to notebook-n20-replay.yml, not this test.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "problems/water_quality/notebooks/experiment9 grid search copy.ipynb"
CLEAN = ROOT / "problems/water_quality/notebooks/water_quality_n20_reproducible.ipynb"
GEOJSON = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"

EXPECTED_SOURCE_SHA = "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"
EXPECTED_DATA_SHA = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"


def test_historical_source_and_geojson_are_still_immutable():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SOURCE_SHA
    assert hashlib.sha256(GEOJSON.read_bytes()).hexdigest() == EXPECTED_DATA_SHA


def test_clean_reference_is_documented_unexecuted_notebook():
    notebook = json.loads(CLEAN.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    cells = notebook["cells"]
    assert len(cells) == 23
    assert sum(c["cell_type"] == "markdown" for c in cells) == 12
    assert sum(c["cell_type"] == "code" for c in cells) == 11
    for cell in cells:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None
            assert cell["outputs"] == []
    markdown = "\n".join(
        "".join(c["source"]) for c in cells if c["cell_type"] == "markdown"
    )
    for required in [
        "reproducible N=20 reference", "local one-hop",
        "published Table IV", "15 explicitly marked existing", "SCIP",
    ]:
        assert required.lower() in markdown.lower(), required


def test_replay_avoids_legacy_external_cache_and_stochastic_execution():
    notebook = json.loads(CLEAN.read_text(encoding="utf-8"))
    code = "\n".join(
        "".join(cell["source"]) for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    assert "pickle.load(" not in code
    assert "drive.mount(" not in code
    assert "openjij" not in code.lower()
    assert "scip.optimize()" in code
    assert "tested == 15504" in code
    assert "N20_CLEAN_RESULT " in code
