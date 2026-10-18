"""Headless executable tests for end-user CSV/GeoJSON model switching.

The UI is a separate synthetic-only prototype, not the deployed dashboard.
These tests genuinely run SCIP and independently audited source bundles.
"""
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def fresh():
    app = AppTest.from_file(str(APP), default_timeout=90).run()
    assert not app.exception
    return app


def select(app, label, value):
    options = [item for item in app.selectbox if item.label == label]
    assert len(options) == 1
    return options[0].set_value(value).run()


def edit(app, label, value):
    options = [item for item in app.text_area if item.label == label]
    assert len(options) == 1
    return options[0].set_value(value).run()


def button(app, label):
    found = [item for item in app.button if item.label == label]
    assert len(found) == 1
    return found[0].click().run()


def test_csv_user_edits_change_solution_and_preserve_exact_uploaded_format():
    at = fresh()
    select(at, "Example problem", "Generic binary scores — synthetic CSV")
    assert not at.exception
    assert any("Dataset CSV — editable" == field.label for field in at.text_area)
    button(at, "Validate and preview formulation")
    assert not at.exception
    button(at, "Run this validated synthetic model with SCIP")
    assert not at.exception
    first = at.session_state["completed_run"]
    assert first["report"]["scip"]["selected_variables"] == ["alpha"]
    assert first["report"]["scip"]["objective"] == -4
    with ZipFile(BytesIO(first["archive"])) as evidence:
        assert {"input-source.csv", "input-bundle.json", "run.json",
                "actual-scip-binary-milp.lp", "manifest.json"} <= set(evidence.namelist())
        spec = json.loads(evidence.read("input-bundle.json"))
        assert spec["dataset"]["path"] == "source.csv"
        assert b"variable,linear_coefficient" in evidence.read("input-source.csv")
        assert b"x_alpha" in evidence.read("actual-scip-binary-milp.lp")

    edit(at, "Dataset CSV — editable",
         "variable,linear_coefficient\nalpha,-2\nbeta,-11\ngamma,-1\n")
    assert not at.exception
    assert not [h for h in at.subheader if "SCIP result" in h.value]
    button(at, "Validate and preview formulation")
    button(at, "Run this validated synthetic model with SCIP")
    assert not at.exception
    changed = at.session_state["completed_run"]
    assert changed["fingerprint"] != first["fingerprint"]
    assert changed["report"]["scip"]["selected_variables"] == ["beta"]
    assert changed["report"]["scip"]["objective"] == -11


def test_projected_geojson_water_ui_preserves_infeasibility_and_budget_zero():
    at = fresh()
    select(at, "Example problem", "Water quality — synthetic GeoJSON")
    assert not at.exception
    assert any(t.label == "Dataset GeoJSON — editable" for t in at.text_area)
    button(at, "Validate and preview formulation")
    assert not at.exception
    button(at, "Run this validated synthetic model with SCIP")
    assert not at.exception
    first = at.session_state["completed_run"]
    out = first["report"]
    assert out["scip_status"] == "infeasible"
    assert out["original_feasible"] is False
    assert out["selected_local_positions"] == []
    assert out["independent_enumeration"]["status"] == "infeasible"
    with ZipFile(BytesIO(first["archive"])) as archive:
        assert {"input-source.geojson", "input-bundle.json", "run.json",
                "actual-water-scip-milp.lp"} <= set(archive.namelist())
        assert b"connect_0" in archive.read("actual-water-scip-milp.lp")
        assert json.loads(archive.read("input-bundle.json"))["dataset"]["path"] == "source.geojson"

    initial_params = next(t for t in at.text_area
                          if t.label == "Formulation parameters JSON — editable")
    updated = json.loads(initial_params.value)
    updated["budget"] = 0
    edit(at, "Formulation parameters JSON — editable", json.dumps(updated))
    assert not at.exception
    assert not [h for h in at.subheader if "SCIP result" in h.value]
    button(at, "Validate and preview formulation")
    button(at, "Run this validated synthetic model with SCIP")
    assert not at.exception
    new = at.session_state["completed_run"]
    assert new["fingerprint"] != first["fingerprint"]
    assert new["report"]["scip_status"] == "optimal"
    assert new["report"]["original_feasible"] is True
    assert new["report"]["original_objective"] == 0
    assert new["report"]["selected_local_positions"] == []


def test_invalid_projected_geojson_is_a_preflight_error_not_silent_reprojection():
    at = fresh()
    select(at, "Example problem", "Water quality — synthetic GeoJSON")
    edit(at, "Dataset GeoJSON — editable",
         json.dumps({"type": "FeatureCollection", "features": [],
                     "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}}))
    assert not at.exception
    assert any("Data / model preflight failed" in str(x.proto) for x in at.error)
    assert not any("Run this validated synthetic model" in x.label for x in at.button)


def test_csv_spreadsheet_formula_injection_rejected_before_scip():
    at = fresh()
    select(at, "Example problem", "Generic binary scores — synthetic CSV")
    edit(at, "Dataset CSV — editable",
         "variable,linear_coefficient\n=HYPERLINK(1),-12\n")
    assert not at.exception
    assert any("Data / model preflight failed" in str(x.proto) for x in at.error)
    assert not any("Run this validated synthetic model" in x.label for x in at.button)
