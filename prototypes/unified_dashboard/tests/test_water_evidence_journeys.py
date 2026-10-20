"""End-to-end *unified routed page* scientific evidence release regressions.

Unlike standalone water-page tests, these start from the ONE unified Streamlit
entrypoint and follow the same page/router users will launch in preview.
They inspect literal evidence bytes, not a merely successful button click.
"""
from __future__ import annotations

import csv
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
from zipfile import ZipFile

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
LOCAL_LABEL = "Local clusters · original"
GLOBAL_LABEL = "Global connectivity · all stations"
LOCAL_SITES = [0, 1, 3, 6, 7]
ALL_FIXED_GLOBAL_K5_FEASIBLE = 860
ALL_FIXED_GLOBAL_K5_FEASIBLE_SHA = (
    "3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40"
)


def start():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception, app.exception
    assert any("Water-quality sensor placement" in t.value for t in app.title)
    assert "mvp_result" not in app.session_state
    return app


def assert_exact_archive(raw_zip: bytes, expected_payloads: set[str]) -> dict:
    """Check *every actual downloaded member*, including byte hashes."""
    assert type(raw_zip) is bytes and 0 < len(raw_zip) <= 2_000_000
    with ZipFile(BytesIO(raw_zip), "r") as archive:
        members = archive.infolist()
        assert len(members) == len(expected_payloads) + 1
        assert {m.filename for m in members} == expected_payloads | {"SHA256SUMS.json"}
        assert all(m.file_size <= 1_000_000 for m in members)
        assert sum(m.file_size for m in members) <= 2_000_000
        manifest = json.loads(archive.read("SHA256SUMS.json"))
        assert set(manifest["files_sha256"]) == expected_payloads
        for name, expected_sha in manifest["files_sha256"].items():
            assert sha256(archive.read(name)).hexdigest() == expected_sha, name
        return {name: archive.read(name) for name in expected_payloads}


def test_unified_entrypoint_original_scip_actual_lp_csv_and_archive_match_display():
    app = start()
    assert next(r for r in app.radio if r.label == "Wireless connectivity").value == LOCAL_LABEL
    assert not [b for b in app.button if b.key == "mvp_download"]
    app.button(key="mvp_run").click().run()
    assert not app.exception, app.exception

    current = app.session_state["mvp_result"]
    assert current["metrics"]["status"] == "optimal"
    assert current["independent"]["selected_local_positions"] == LOCAL_SITES
    assert current["attestation"]["strictly_bound_to_compiled_current_run"] is True
    assert current["attestation"]["parsed_original_scip_lp_formulation"][
        "budget_equal_K_verified"
    ] is True
    assert current["attestation"]["parsed_original_scip_lp_formulation"][
        "each_original_local_one_hop_verified"
    ] is True
    assert any(m.label == "SCIP status" and m.value == "optimal" for m in app.metric)
    # AppTest does not enumerate st.download_button in app.button; validate
    # active evidence bytes plus the visible, truthful source description.
    assert any("Evidence contains formulation coefficients" in str(c.proto)
               for c in app.caption)

    files = assert_exact_archive(current["zip"], {
        "model.json", "result.json", "selected_sites.csv", "actual_scip_model.lp",
    })
    model, result = json.loads(files["model.json"]), json.loads(files["result.json"])
    assert model["model_fingerprint_sha256"] == current["fingerprint"]
    assert result["model_fingerprint_sha256"] == current["fingerprint"]
    assert result["scip_status"] == "optimal"
    assert result["scip_optimal_proven"] is True
    assert result["independent_audit"] == current["independent"]
    assert "Minimize" in files["actual_scip_model.lp"].decode("ascii")
    assert "Subject to" in files["actual_scip_model.lp"].decode("ascii")
    rows = list(csv.DictReader(StringIO(files["selected_sites.csv"].decode("utf-8"))))
    assert [int(row["local_position"]) for row in rows] == LOCAL_SITES
    assert [int(row["master_feature_position"]) for row in rows] == [
        model["mapping"]["free_master_feature_positions"][i] for i in LOCAL_SITES
    ]
    # No second process service or paper/field certification gets installed
    # merely by rendering a source-level, mathematical verification result.
    assert any("No quantum solver" in str(w.proto) for w in app.warning)


def test_unified_global_modeswitch_invalidates_local_and_exports_no_fake_scip_lp():
    app = start()
    app.button(key="mvp_run").click().run()
    assert not app.exception, app.exception
    local = app.session_state["mvp_result"]
    local_sha = sha256(local["zip"]).hexdigest()
    local_fingerprint = local["fingerprint"]

    chooser = next(r for r in app.radio if r.label == "Wireless connectivity")
    chooser.set_value(GLOBAL_LABEL).run()
    assert not app.exception, app.exception
    assert "mvp_result" not in app.session_state
    assert not [b for b in app.button if b.key == "mvp_download"]
    assert not [m for m in app.metric if m.label == "Original objective (min.)"]
    assert any("Inputs changed" in str(x.proto) for x in app.info)

    app.button(key="mvp_run").click().run()
    assert not app.exception, app.exception
    current = app.session_state["mvp_result"]
    assert current["metrics"]["status"] == "optimal_exhaustive"
    assert current["metrics"]["optimal"] is True
    assert current["chosen"] is not None
    assert current["fingerprint"] != local_fingerprint
    assert sha256(current["zip"]).hexdigest() != local_sha
    assert current["attestation"]["strictly_bound_to_compiled_current_run"] is True
    assert any(m.label == "Exact search status" for m in app.metric)
    assert not [m for m in app.metric if m.label == "SCIP status"]
    # Actual downloaded ZIP bytes are checked below; Streamlit AppTest
    # cannot directly click st.download_button in its ordinary button list.
    assert any("Global evidence contains formulation" in str(c.proto)
               for c in app.caption)

    files = assert_exact_archive(current["zip"], {
        "model.json", "result.json", "selected_sites.csv", "wireless_graph.json",
    })
    model, result, graph = (json.loads(files[p]) for p in (
        "model.json", "result.json", "wireless_graph.json"
    ))
    assert model["settings"]["connectivity_mode"] == "all_stations_connected"
    assert model["constraints"]["global_path_connectivity"] is True
    assert model["model_fingerprint_sha256"] == result["model_fingerprint_sha256"]
    assert model["model_fingerprint_sha256"] == current["fingerprint"]
    assert result["optimal_proven"] is True
    assert result["search"] == current["metrics"]
    assert graph["fixed_count"] == 15
    assert graph["free_count"] == 20
    assert result["graph_fingerprint_sha256"] == current[
        "attestation"
    ]["active_graph_sha256"]
    assert current["metrics"]["feasible_combinations"] == ALL_FIXED_GLOBAL_K5_FEASIBLE
    assert "actual_scip_model.lp" not in files
    assert current["attestation"]["parsed_original_scip_lp_formulation"] is None

    # Switch BACK without solving: it is a different mathematical scenario.
    chooser = next(r for r in app.radio if r.label == "Wireless connectivity")
    chooser.set_value(LOCAL_LABEL).run()
    assert not app.exception, app.exception
    assert "mvp_result" not in app.session_state
    assert not [b for b in app.button if b.key == "mvp_download"]
    assert not [m for m in app.metric if m.label == "Original objective (min.)"]


def test_two_unified_browser_sessions_do_not_share_source_or_global_result():
    local = start()
    other = start()
    local.button(key="mvp_run").click().run()
    assert not local.exception, local.exception
    assert "mvp_result" not in other.session_state
    local_record = local.session_state["mvp_result"]
    original_local_zip_sha = sha256(local_record["zip"]).hexdigest()

    next(r for r in other.radio if r.label == "Wireless connectivity").set_value(
        GLOBAL_LABEL
    ).run()
    other.button(key="mvp_run").click().run()
    assert not other.exception, other.exception
    assert other.session_state["mvp_result"]["metrics"]["status"] == "optimal_exhaustive"
    assert sha256(other.session_state["mvp_result"]["zip"]).hexdigest() != original_local_zip_sha
    # A separate browser session's mode/solution may not change the original.
    local.run()
    assert not local.exception, local.exception
    assert local.session_state["mvp_result"]["metrics"]["status"] == "optimal"
    assert sha256(local.session_state["mvp_result"]["zip"]).hexdigest() == original_local_zip_sha
