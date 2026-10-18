"""Experimental Streamlit UI for versioned, replaceable synthetic model bundles.

NOT the deployed water-quality pilot. Upload/paste local JSON, choose a
validated formulation, inspect the resolved source model, run SCIP on demand
and download the original input + EXACT SCIP LP + independent result audit.

No arbitrary Python/LaTeX execution; no real shelter/hazard data supported.
"""
from __future__ import annotations

from io import BytesIO
import json
from math import comb
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "problems" / "evacuation_centers" / "examples"
WATER_EXAMPLES = ROOT / "problems" / "water_quality" / "examples"
sys.path.insert(0, str(ROOT / "problems" / "water_quality"))
sys.path.insert(0, str(ROOT / "framework" / "python"))
sys.path.insert(0, str(ROOT / "problems" / "evacuation_centers"))

from qopt.core.experiment_bundle import canonical, load_bundle
from qopt.core.binary_quadratic import validate_binary_problem
from qopt.core.math_ir import validate_ir, render_original
from bundle_runner import _synthetic_evacuation, execute
from water_bundle_adapter import _parameters as _water_parameters, _validate_geojson
from notebook_reference_model import make_instance, load_data


PRESETS = {
    "Evacuation — capacitated allocation": "evac-capacitated.json",
    "Evacuation — maximum potential coverage": "evac-covering.json",
    "Evacuation — alternate artificial dataset": "evac-alternate-data.json",
    "Generic binary quadratic": "generic-binary-quadratic.json",
    "Structured math — binary, integer and continuous": "synthetic-typed-mixed.bundle.json",
    "Structured math — unconstrained binary QUBO": "synthetic-typed-binary-qubo.bundle.json",
    "Generic binary scores — synthetic CSV": "generic-csv-linear-bundle.json",
    "Water quality — synthetic GeoJSON": WATER_EXAMPLES / "fake-water-n5.bundle.json",
    "Water quality — alternate synthetic GeoJSON": WATER_EXAMPLES / "fake-water-alternate.bundle.json",
}


def _bundle_spec(preset: str) -> tuple[dict, str, str]:
    bundle_path = PRESETS[preset]
    if not isinstance(bundle_path, Path):
        bundle_path = EXAMPLES / bundle_path
    manifest = json.loads(bundle_path.read_text(encoding="utf-8"))
    file_path = bundle_path.parent / manifest["dataset"]["path"]
    extension = file_path.suffix
    if extension not in (".json", ".geojson", ".csv"):
        raise ValueError("Unsupported sample input format")
    source = file_path.read_text(encoding="utf-8")
    if extension != ".csv":
        source = json.dumps(json.loads(source), indent=2)
    return manifest, source, extension


def _prepare(manifest: dict, data_bytes: bytes, directory: Path, extension: str = ".json"):
    if manifest.get("classification") != "SYNTHETIC":
        raise ValueError("This experimental UI accepts synthetic data only, not historical or real-site uploads")
    if extension not in (".json", ".geojson", ".csv"):
        raise ValueError("Unsupported dataset extension")
    if len(data_bytes) > 1_000_000:
        raise ValueError("Prototype only supports at most 1 MB of synthetic data")
    source_name = "source" + extension
    (directory / source_name).write_bytes(data_bytes)
    config = dict(manifest)
    config["dataset"] = {"path": source_name}
    (directory / "bundle.json").write_bytes(canonical(config))
    b = load_bundle(directory / "bundle.json")
    # A preview is a validated data/model configuration, not a SCIP run.
    if b.problem_id == "evacuation.synthetic":
        if b.formulation_id not in ("maximal_coverage", "capacitated_lexicographic"):
            raise ValueError("Unsupported mathematical formulation")
        _synthetic_evacuation(b.data, b.parameters)
    elif b.problem_id == "binary_quadratic.synthetic":
        if b.formulation_id != "binary_quadratic":
            raise ValueError("Unsupported binary quadratic formulation")
        validate_binary_problem(b.data, b.parameters)
    elif b.problem_id == "structured.synthetic":
        if b.formulation_id != "typed_milp" or extension != ".json":
            raise ValueError("Typed structured editor requires its bounded typed_milp JSON formulation")
        validate_ir(b.data, b.parameters)
    elif b.problem_id == "water_quality.reference":
        if b.formulation_id != "notebook_one_hop_milp" or extension != ".geojson":
            raise ValueError("Water-quality reference requires its original one-hop formulation and projected GeoJSON")
        _validate_geojson(b)
        settings = _water_parameters(b.parameters)
        # Keep interactive preview and exact subset proof bounded on shared UI.
        if settings["n_free"] > 12 or settings["time_limit"] > 30:
            raise ValueError("UI water-quality experiment is capped at N=12 and time_limit=30 seconds")
        if len(b.data["features"]) > 200:
            raise ValueError("UI synthetic water GeoJSON is capped at 200 features")
        if comb(settings["n_free"], settings["budget"]) > 200000:
            raise ValueError("UI experiment exceeds the exhaustive verification budget")
    else:
        raise ValueError("Unsupported scientific problem adapter")
    return b


def _model_text(b) -> str:
    if b.problem_id == "structured.synthetic":
        ir = validate_ir(b.data, b.parameters)
        exact_qubo = not ir["constraints"] and all(
            v["domain"] == "binary" for v in ir["variables"]
        )
        return (render_original(ir) + "\n" +
                ("Direct unconstrained QUBO: exact, with maximization negated for minimizer"
                 if exact_qubo else
                 "Direct QUBO: REFUSED (constraints or non-binary variables need separately proven encoding)") +
                "\nSCIP: exact MILP pair-product compiler; verified against discrete enumeration + continuous HiGHS LP.")
    if b.problem_id == "water_quality.reference":
        settings = _water_parameters(b.parameters)
        source = load_data(b.dataset_path)
        instance, simulated = make_instance(
            source, settings["weights"], settings["n_free"], settings["budget"],
            beta=settings["beta"], delta=settings["delta"]
        )
        if simulated:
            raise ValueError("Synthetic lake scenario must supply explicit fixed station markers")
        terms = [
            "minimize E(x) = sum_i a_i*x_i + sum_(i<j) q_ij*x_i*x_j",
            "x_i binary; exact budget: sum_i x_i = " + str(instance.budget),
            "local one-hop: x_i <= fixed_neighbor_i + sum_(j neighbor of i) x_j",
            "IMPORTANT: local one-hop is NOT global backbone connectivity",
            "N=" + str(len(instance.free_indices)) + "; fixed sites=" + str(len(instance.fixed_indices)),
            "factor weights: " + str(settings["weights"].tolist()),
            "selected candidate positions (zero-based source feature indices): " +
            str(instance.free_indices.astype(int).tolist()),
            "a_i linear coefficients: " + str(instance.linear.astype(float).tolist()),
            "q_ij upper quadratic terms: " + str([[int(i),int(j),float(q)] for i,j,q in instance.quadratic]),
            "fixed_neighbor_i: " + str(instance.fixed_neighbors.astype(int).tolist()),
            "neighbors_i: " + str([list(group) for group in instance.neighbors]),
            "Actual SCIP MILP (including pair-product constraints) exported only after Run.",
            "Original manuscript replication is UNRESOLVED, these are fake GeoJSON sites.",
        ]
        return "\n".join(terms)
    if b.problem_id == "evacuation.synthetic":
        p = _synthetic_evacuation(b.data, b.parameters)
        first = ("maximize sum(d_i * covered_i); z_i <= sum(reachable open_j)"
                 if b.formulation_id == "maximal_coverage"
                 else "stage 1: minimize sum(unserved_i)\nstage 2: minimize sum(travel_minutes_ij * assigned_persons_ij)")
        return "\n".join([
            first,
            "budget: sum(open_j) <= " + str(p.max_open),
            "eligible sites: " + str(list(p.eligible)),
            "zone demand (persons): " + str(list(p.demands)),
            "site capacities (persons): " + str(list(p.capacities)) +
            (" [NOT ENFORCED IN COVERING MODEL]" if b.formulation_id == "maximal_coverage" else ""),
            "travel times (minutes, null = unreachable): " + str([list(row) for row in p.travel_minutes]),
            "important: these are fake people/shelters; no real emergency advice",
        ])
    p = validate_binary_problem(b.data, b.parameters)
    obj = p["objective"]
    parts = [f"{value:+g}*{name}" for name,value in obj["linear"].items()]
    parts += [f"{t['coefficient']:+g}*{t['first']}*{t['second']}"
              for t in obj["quadratic"]]
    if obj.get("constant"):
        parts.append(f"{obj['constant']:+g}")
    rows = [
        f"{obj['sense']} " + (" ".join(parts) if parts else "0"),
        "binary variables: " + ", ".join(p["variables"]),
    ]
    rows += [
        str(" ".join(f"{coeff:+g}*{name}" for name,coeff in row["linear"].items()) or "0")
        + " " + row["sense"] + " " + str(row["rhs"]) + "  [" + row["id"] + "]"
        for row in p["constraints"]
    ]
    return "\n".join(rows)


def _artifact_zip(directory: Path) -> bytes:
    buff = BytesIO()
    with ZipFile(buff, "w", ZIP_DEFLATED) as archive:
        for file in sorted(directory.glob("*.json")) + sorted(directory.glob("*.lp")):
            archive.write(file, file.name)
    return buff.getvalue()


def main() -> None:
    st.set_page_config(page_title="QOpt Configurable Problem Workbench (Synthetic)", layout="wide")
    st.title("Configurable Optimization Workbench")
    st.warning(
        "Experimental research prototype using synthetic inputs ONLY. "
        "Not the deployed Laguna de Bay dashboard, a live shelter finder, "
        "or a quantum-computing benchmark."
    )
    st.caption(
        "Upload or edit a supported synthetic JSON, CSV, or projected GeoJSON dataset, "
        "choose a compatible formulation, review exact numeric terms, "
        "run SCIP, and export the audit."
    )

    preset = st.selectbox("Example problem", list(PRESETS))
    suggested, sample_text, extension = _bundle_spec(preset)
    domain = suggested["problem_id"]
    choices = (["maximal_coverage", "capacitated_lexicographic"]
               if domain == "evacuation.synthetic"
               else ["notebook_one_hop_milp"] if domain == "water_quality.reference"
               else ["typed_milp"] if domain == "structured.synthetic"
               else ["binary_quadratic"])
    formulation = st.selectbox(
        "Mathematical formulation", choices,
        index=choices.index(suggested["formulation_id"]),
        key="formula-" + preset,
    )
    suffix_label = {".json": "JSON", ".geojson": "GeoJSON", ".csv": "CSV"}[extension]
    st.caption(
        "Input format: " + suffix_label +
        (" | Explicit EPSG:32651 projected meters, eight named factor columns and fixed-station flags"
         if extension == ".geojson" else
         " | Columns: variable,linear_coefficient; at most 16 binary variables"
         if extension == ".csv" else " | Schema and units checked by the selected model adapter")
    )
    structured = domain == "structured.synthetic"
    if structured:
        sample_object = json.loads(sample_text)
        st.caption("Structured term editor: edit variable types/bounds, coefficient terms, "
                   "and named constraints independently. LaTeX is never executed.")
        vars_text = st.text_area(
            "Variables — JSON list of names, domains and bounds",
            value=json.dumps(sample_object["variables"], indent=2),
            height=175, key="typed-vars-" + preset,
        )
        obj_text = st.text_area(
            "Objective — JSON sense, constant, linear and binary-pair terms",
            value=json.dumps(sample_object["objective"], indent=2),
            height=175, key="typed-objective-" + preset,
        )
        cons_text = st.text_area(
            "Constraints — JSON linear rows with named RHS",
            value=json.dumps(sample_object["constraints"], indent=2),
            height=175, key="typed-constraints-" + preset,
        )
        editable = None
    else:
        editable = st.text_area(
            "Dataset " + suffix_label + " — editable", value=sample_text,
            height=210, key="input-data-" + preset,
            help="Modify artificial values or upload a replacement with the SAME supported format.",
        )
    uploaded = st.file_uploader(
        "Replace dataset with " + suffix_label + " (takes precedence over editor)",
        type=[extension.lstrip(".")], key="dataset-upload-" + preset,
    )
    params = st.text_area(
        "Formulation parameters JSON — editable",
        value=json.dumps(suggested["parameters"], indent=2),
        height=86, key="parameters-" + preset,
        help="For example: max_open or named binary constraint rhs_overrides.",
    )

    valid = False
    validation_error = ""
    try:
        parameters = json.loads(params)
        if uploaded is not None:
            source_bytes = uploaded.getvalue()
        elif structured:
            source_bytes = canonical({
                "classification": "SYNTHETIC_TYPED_OPTIMIZATION",
                "variables": json.loads(vars_text),
                "objective": json.loads(obj_text),
                "constraints": json.loads(cons_text),
            })
        else:
            source_bytes = editable.encode("utf-8")
        with TemporaryDirectory(prefix="qopt-synthetic-preview-") as folder:
            manifest = dict(suggested)
            manifest["formulation_id"] = formulation
            manifest["parameters"] = parameters
            bundle = _prepare(manifest, source_bytes, Path(folder), extension)
            fingerprint = bundle.fingerprint
            desc = _model_text(bundle)
            validated_input = bundle.audit()
        valid = True
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, OSError) as exc:
        validation_error = str(exc)
    if not valid:
        st.error("Data / model preflight failed: " + validation_error)
        st.session_state.pop("preview_fingerprint", None)
        st.session_state.pop("completed_run", None)
        st.stop()

    st.caption("Resolved source/model fingerprint: " + fingerprint)
    st.button("Validate and preview formulation", key="preview_btn",
              on_click=lambda: st.session_state.update(preview_fingerprint=fingerprint))
    if st.session_state.get("preview_fingerprint") != fingerprint:
        st.info("Changed inputs require a new formulation preview before solving.")
        st.session_state.pop("completed_run", None)
        return

    st.subheader("Verified original formulation (from selected inputs)")
    st.code(desc, language="text")
    with st.expander("Resolved exact configuration and source input"):
        st.json(validated_input)

    if st.button("Run this validated synthetic model with SCIP", key="run_btn"):
        try:
            with TemporaryDirectory(prefix="qopt-synthetic-run-") as folder:
                manifest = dict(suggested)
                manifest["formulation_id"] = formulation
                manifest["parameters"] = parameters
                root = Path(folder)
                checked = _prepare(manifest, source_bytes, root, extension)
                output = root / "evidence"
                result = execute(root / "bundle.json", output)
                if checked.fingerprint != fingerprint:
                    raise AssertionError("Preview model fingerprint changed before SCIP run")
                artifacts = _artifact_zip(output)
                # Include the precise data/model submitted, not only results.
                src_zip = BytesIO(artifacts)
                final_zip = BytesIO()
                with ZipFile(final_zip, "w", ZIP_DEFLATED) as dest:
                    with ZipFile(src_zip, "r") as original:
                        for item in original.infolist():
                            dest.writestr(item, original.read(item.filename))
                    dest.writestr("input-source" + extension, source_bytes)
                    dest.writestr("input-bundle.json", (root / "bundle.json").read_bytes())
                st.session_state["completed_run"] = {
                    "fingerprint": fingerprint,
                    "report": result["result"],
                    "archive": final_zip.getvalue(),
                }
        except (ValueError, KeyError, TypeError, AssertionError, OSError, RuntimeError) as exc:
            st.error("Solver or post-solve audit failed: " + str(exc))
            st.session_state.pop("completed_run", None)

    run = st.session_state.get("completed_run")
    if run is not None and run["fingerprint"] == fingerprint:
        st.subheader("SCIP result and independent original-model audit")
        st.json(run["report"])
        st.download_button(
            "Download input, actual SCIP LP, source hashes and verified result (.zip)",
            data=run["archive"], file_name="qopt-synthetic-audit.zip",
            mime="application/zip", key="download_bundle",
        )
    else:
        st.caption("No SCIP result for these settings yet. Preview first, then run.")


if __name__ == "__main__":
    main()
