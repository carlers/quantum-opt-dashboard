"""Experimental Streamlit UI for versioned, replaceable synthetic model bundles.

NOT the deployed water-quality pilot. Upload/paste local JSON, choose a
validated formulation, inspect the resolved source model, run SCIP on demand
and download the original input + EXACT SCIP LP + independent result audit.

No arbitrary Python/LaTeX execution; no real shelter/hazard data supported.
"""
from __future__ import annotations

from io import BytesIO
import json
import threading
from math import comb
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
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
from guided_math_ui import show_guided_controls


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


def _set_quick_budget(preset: str, parameter_name: str) -> None:
    """Apply a simple GUI setting to the SAME parameter editor/source bytes."""
    key = "parameters-" + preset
    params = json.loads(st.session_state[key])
    params[parameter_name] = int(st.session_state["quick-budget-" + preset])
    st.session_state[key] = json.dumps(params, indent=2)


def _set_quick_demand(preset: str, zone_index: int, widget_key: str) -> None:
    """One source-of-truth edit; source fingerprint still guards all old output."""
    key = "input-data-" + preset
    source = json.loads(st.session_state[key])
    source["demands"][zone_index] = int(st.session_state[widget_key])
    st.session_state[key] = json.dumps(source, indent=2)


def _quick_model_controls(preset: str, domain: str, suggested: dict,
                          sample_text: str) -> None:
    """First-run controls for users who should never need to open a JSON editor."""
    if domain not in ("evacuation.synthetic", "binary_quadratic.synthetic"):
        return
    st.subheader("2 · Adjust the example")
    st.caption("You can change these settings using normal controls. "
               "The advanced input editor below is optional.")
    params_key = "parameters-" + preset
    raw_params = json.loads(st.session_state.get(
        params_key, json.dumps(suggested["parameters"])
    ))
    if domain == "evacuation.synthetic":
        source = json.loads(st.session_state.get("input-data-" + preset, sample_text))
        count = len(source["site_ids"])
        current = int(raw_params.get("max_open", source["max_open"]))
        budget_key = "quick-budget-" + preset
        source_key = "quick-budget-source-" + preset
        if st.session_state.get(source_key) != current:
            st.session_state[budget_key] = current
            st.session_state[source_key] = current
        st.number_input(
            "Maximum evacuation centers to open", min_value=0, max_value=count,
            step=1, key=budget_key, on_change=_set_quick_budget,
            args=(preset, "max_open"),
            help="A limit on how many of these fictional shelters can open. "
                 "Try changing it and compare the number of people served.",
        )
        zone = st.selectbox("Demand zone to adjust", source["zone_ids"],
                            key="quick-zone-" + preset)
        idx = source["zone_ids"].index(zone)
        demand_key = f"quick-demand-{preset}-{idx}"
        sync_key = f"quick-demand-source-{preset}-{idx}"
        current_demand = int(source["demands"][idx])
        if st.session_state.get(sync_key) != current_demand:
            st.session_state[demand_key] = current_demand
            st.session_state[sync_key] = current_demand
        st.number_input(
            "People needing shelter in selected zone (fictional)",
            min_value=0, max_value=100, step=1,
            key=demand_key, on_change=_set_quick_demand,
            args=(preset, idx, demand_key),
            help="Changes synthetic demand for the selected zone. No real people "
                 "or emergency facility information is used.",
        )
    else:
        # The tiny binary model and synthetic CSV both expose the budget
        # through their existing named RHS parameter override.
        rows = raw_params.get("rhs_overrides", {})
        current = int(rows.get("budget", 1))
        budget_key = "quick-budget-" + preset
        source_key = "quick-budget-source-" + preset
        if st.session_state.get(source_key) != current:
            st.session_state[budget_key] = current
            st.session_state[source_key] = current
        st.number_input(
            "Maximum choices to select", min_value=0, max_value=16,
            step=1, key=budget_key,
            on_change=_set_quick_rhs_budget, args=(preset,),
            help="Changes the named budget constraint used by SCIP. "
                 "Your changes can be inspected in the model evidence.",
        )


def _set_quick_rhs_budget(preset: str) -> None:
    key = "parameters-" + preset
    params = json.loads(st.session_state[key])
    overrides = dict(params.get("rhs_overrides", {}))
    overrides["budget"] = int(st.session_state["quick-budget-" + preset])
    params["rhs_overrides"] = overrides
    st.session_state[key] = json.dumps(params, indent=2)


def _human_result(domain: str, report: dict) -> None:
    """Translate verified numerical results to readable outcomes, not raw JSON."""
    st.subheader("Your optimization result")
    if domain == "evacuation.synthetic":
        result = report["result"]
        if "capacitated_scip" in result:
            solved = result["capacitated_scip"]
            sites = report["scenario"]["sites"]
            selected = [sites[i] for i in solved["selected_sites_zero_based"]]
            a, b, c = st.columns(3)
            a.metric("People served (fictional)", f'{solved["served_persons"]:g}')
            b.metric("People not served", f'{solved["unserved_persons"]:g}')
            c.metric("Open facilities", len(selected))
            st.write("**Selected sites:**", ", ".join(selected) if selected else "None")
            st.caption("Capacity is enforced. SCIP and an independent small-instance "
                       "reference checked the result.")
        else:
            sites = report["scenario"]["sites"]
            selected = [sites[i] for i in result["selected_site_indices"]]
            st.metric("Potentially reachable people (not people served)",
                      f'{result["potentially_reachable_persons_NOT_served"]:g}')
            st.write("**Selected sites:**", ", ".join(selected) if selected else "None")
            st.warning("This covering formulation does not enforce facility capacity. "
                       "It must not be read as a count of people actually served.")
    elif domain in ("structured.synthetic", "binary_quadratic.synthetic"):
        solved = report["scip"]
        st.write("**SCIP solver status:**", solved["status"])
        if solved["status"] == "optimal":
            st.metric("Objective value", f'{solved["objective"]:.6g}')
            if "selected_variables" in solved:
                st.write("**Chosen variables:**",
                         ", ".join(solved["selected_variables"]) or "None")
            elif "assignment" in solved:
                st.write("**Decision values:**", {
                    k: round(float(v), 5) for k, v in solved["assignment"].items()
                })
        st.caption("The result is verified against the supported original model "
                   "and independent reference before it is exported.")
    else:
        st.caption("See the independent model verification and source below.")


def main() -> None:
    if not getattr(threading.current_thread(), "_qopt_unified_page", False):
        st.set_page_config(page_title="QOpt Configurable Problem Workbench (Synthetic)", layout="wide")
    st.title("Configurable Optimization Workbench")
    st.info(
        "Safe practice problems with fictional data. You can change a setting, "
        "solve it, and learn what the results mean. This is not real emergency guidance."
    )
    st.caption(
        "Upload or edit a supported synthetic JSON, CSV, or projected GeoJSON dataset, "
        "choose a compatible formulation, review exact numeric terms, "
        "run SCIP, and export the audit."
    )

    st.subheader("1 · Choose a problem to explore")
    preset = st.selectbox("Example problem", list(PRESETS),
                          help="Start with the first fictional shelter example, or try "
                               "the structured mathematical model for variable-level editing.")
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
        st.subheader("2 · Adjust the example")
        st.caption("Use the tabs below to edit variable bounds, numerical scores "
                   "and constraints. Advanced JSON is optional.")
        vars_key, obj_key, cons_key = (
            "typed-vars-" + preset,
            "typed-objective-" + preset,
            "typed-constraints-" + preset,
        )
        vars_text = st.session_state.get(
            vars_key, json.dumps(sample_object["variables"], indent=2)
        )
        obj_text = st.session_state.get(
            obj_key, json.dumps(sample_object["objective"], indent=2)
        )
        cons_text = st.session_state.get(
            cons_key, json.dumps(sample_object["constraints"], indent=2)
        )
        params_for_controls = st.session_state.get(
            "parameters-" + preset, json.dumps(suggested["parameters"], indent=2)
        )
        if st.session_state.get("dataset-upload-" + preset) is None:
            show_guided_controls(
                preset, vars_text, obj_text, cons_text, params_for_controls
            )
        else:
            st.info("An uploaded model takes precedence; remove it to use guided controls.")
        with st.expander("Advanced: edit underlying model JSON", expanded=False):
            vars_text = st.text_area(
                "Variables — JSON list of names, domains and bounds",
                value=json.dumps(sample_object["variables"], indent=2),
                height=175, key=vars_key,
            )
            obj_text = st.text_area(
                "Objective — JSON sense, constant, linear and binary-pair terms",
                value=json.dumps(sample_object["objective"], indent=2),
                height=175, key=obj_key,
            )
            cons_text = st.text_area(
                "Constraints — JSON linear rows with named RHS",
                value=json.dumps(sample_object["constraints"], indent=2),
                height=175, key=cons_key,
            )
        editable = None
    else:
        _quick_model_controls(preset, domain, suggested, sample_text)
        with st.expander("Advanced: edit or upload raw data", expanded=False):
            editable = st.text_area(
                "Dataset " + suffix_label + " — editable", value=sample_text,
                height=210, key="input-data-" + preset,
                help="You can modify fictional dataset values. "
                     "The quick controls above update this same input.",
            )
    with st.expander("Advanced: input files and parameters", expanded=False):
        uploaded = st.file_uploader(
            "Replace dataset with " + suffix_label + " (takes precedence over editor)",
            type=[extension.lstrip(".")], key="dataset-upload-" + preset,
        )
        params = st.text_area(
            "Formulation parameters JSON — editable",
            value=json.dumps(suggested["parameters"], indent=2),
            height=86, key="parameters-" + preset,
            help="This is the exact configuration sent to SCIP, "
                 "including any changes from quick controls.",
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

    st.subheader("3 · Preview and solve")
    st.caption("A validated preview is generated without running the solver. "
               "You can inspect the math before choosing to run SCIP.")
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
        _human_result(domain, run["report"])
        with st.expander("Advanced: verified numerical report and provenance", expanded=False):
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
