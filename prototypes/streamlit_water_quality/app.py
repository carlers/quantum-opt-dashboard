"""A focused, source-pinned Streamlit MVP for one auditable water-quality study.

One built-in Laguna de Bay reference, notebook-derived N=20 candidates, K
and AHP preset selection, exact original math preview, one SCIP run, map,
independent original feasibility/objective audit and self-contained evidence.
Neither quantum hardware nor previous-paper numerical replication is claimed.
"""
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from pyproj import Transformer

from model import (
    FACTOR_NAMES, NOTEBOOK_WEIGHTS, PAPER_WEIGHTS, existing_stations, load_data,
    make_instance, site_utility, solve_scip,
)
from mvp_audit import (
    NOTEBOOK_N20_K5_LOCAL_INDICES, NOTEBOOK_N20_K5_OPTIMUM,
    canonical, check_selected, evidence_zip, preview, selected_csv, source_sha,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
N_FREE = 20
SCIP_TIME_LIMIT = 30

FACTOR_LABELS = (
    "River proximity",
    "Runoff proximity",
    "Fishpen density",
    "Low-oxygen proximity",
    "Bathymetric depressions",
    "Outlet proximity",
    "Boat ramp proximity",
    "Road proximity",
)

if not getattr(threading.current_thread(), "_qopt_unified_page", False):
    st.set_page_config(
        page_title="Water-quality Placement · Research MVP",
        page_icon="🧪", layout="wide",
    )
st.title("Water-quality sensor placement")
st.caption("Research MVP · Laguna de Bay · source-pinned notebook-derived model")
st.warning(
    "This reproduces a **committed notebook-derived scenario**, not the earlier "
    "paper's published numerical inputs. Paper AHP/Table IV, criterion D2, "
    "and historical SCIP energy provenance remain unresolved. No quantum solver is run."
)


@st.cache_data(show_spinner="Loading committed reference dataset…")
def get_data():
    return load_data(DATA_PATH)


@st.cache_resource
def converter():
    return Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True)


try:
    dataset_sha = source_sha(DATA_PATH)
    data = get_data()
    if len(data.ids) != 5417:
        raise ValueError("Pinned source must contain exactly 5,417 sites.")
except (ValueError, OSError, KeyError) as exc:
    st.error("Could not verify the original source dataset: " + str(exc))
    st.stop()

with st.sidebar:
    st.header("1 · Configure")
    st.caption("Single source dataset · exactly 20 candidate free sites")
    k = st.number_input(
        "New sensors to place (K)", min_value=0, max_value=N_FREE,
        value=5, step=1,
        help="Exact cardinality; the original committed notebook reference uses K=5.",
    )
    source = st.radio(
        "Criterion weights",
        ["Notebook weights · reference", "Paper weights · comparison only",
         "Custom weights · exploratory"],
        help="Each of the eight environmental factors contributes to the site suitability "
             "score. Notebook and paper profiles differ; custom weights define a new experiment.",
    )
    weights = (NOTEBOOK_WEIGHTS.copy() if source.startswith("Notebook")
               else PAPER_WEIGHTS.copy() if source.startswith("Paper")
               else None)
    with st.expander("Eight factors and their importance", expanded=True):
        st.caption(
            "These are the eight measured criteria in the committed dataset. "
            "Higher relative weight gives a criterion more influence on site suitability. "
            "Missing criteria are renormalized per site."
        )
        if weights is None:
            weights = np.array([
                st.number_input(
                    label + " weight", min_value=0.0, max_value=5.0,
                    value=float(NOTEBOOK_WEIGHTS[i]), step=0.01, format="%.4f",
                    key=f"water-custom-weight-{i}",
                    help=f"Criterion {FACTOR_NAMES[i]}. Set zero to exclude it from the "
                         "weighted site suitability score; at least one weight must be positive.",
                )
                for i, label in enumerate(FACTOR_LABELS)
            ], dtype=float)
        else:
            st.dataframe(pd.DataFrame({
                "Environmental factor": FACTOR_LABELS,
                "Relative weight": [round(float(w), 6) for w in weights],
            }), hide_index=True, use_container_width=True)
            st.caption("Choose Custom weights above to edit each of these eight values.")
        st.caption("Criterion values themselves come from the source GeoJSON; "
                   "this reference page changes their importance, not the measured data.")
    with st.expander("Advanced: interaction strengths", expanded=False):
        st.caption("These model parameters change penalties for placing sensors close "
                   "together. They do not change the one-hop connectivity requirement.")
        beta = st.number_input(
            "Redundancy strength (β)", min_value=0.0, max_value=10.0,
            value=1.0, step=0.1,
            help="Strength of the penalty for nearby stations that may duplicate "
                 "each other's spatial coverage. Zero removes this interaction penalty.",
        )
        delta = st.number_input(
            "Wake strength (δ)", min_value=0.0, max_value=10.0,
            value=1.0, step=0.1,
            help="Strength of the distance-and-current-direction wake overlap penalty. "
                 "Zero removes this interaction penalty.",
        )
    if np.sum(weights) <= 0:
        st.error("At least one environmental factor must have a positive weight.")
        st.stop()
    st.caption("20 possible new sites · SCIP time limit 30 seconds")
    run = st.button(
        "Find monitoring locations (SCIP)", key="mvp_run",
        type="primary", use_container_width=True,
        help="Solve the currently selected budget, eight factor weights and interaction strengths.",
    )

try:
    utility = site_utility(data.factors, weights)
    fixed, simulated = existing_stations(data, utility)
    if simulated or len(fixed) != 15:
        raise ValueError("The immutable reference requires 15 explicitly marked existing stations.")
    instance, simulated_instance = make_instance(
        data, weights, N_FREE, int(k), beta=float(beta), delta=float(delta)
    )
    if simulated_instance:
        raise ValueError("Reference fallback stations are forbidden in the MVP.")
    # Streamlit may hot-reload this page while retaining an older imported
    # mvp_audit.preview from a previous Cloud deployment. The legacy function
    # accepts the original five inputs, but not beta/delta. Pass the stable
    # interface, then explicitly bind all current model parameters and rebuild
    # the source-derived fingerprint from the *actual* compiled instance.
    # This preserves numerical provenance AND survives a warm Cloud reload.
    model = preview(
        instance, dataset_sha256=dataset_sha, weights=weights.tolist(),
        weight_source=source, time_limit_seconds=SCIP_TIME_LIMIT,
    )
    model["settings"]["beta"] = float(beta)
    model["settings"]["delta"] = float(delta)
    model.pop("model_fingerprint_sha256", None)
    model["model_fingerprint_sha256"] = hashlib.sha256(canonical(model)).hexdigest()
except (ValueError, RuntimeError, IndexError) as exc:
    st.error("Could not construct this mathematical scenario: " + str(exc))
    st.stop()

fingerprint = model["model_fingerprint_sha256"]
old = st.session_state.get("mvp_result")
if old is not None and old["fingerprint"] != fingerprint:
    st.session_state.pop("mvp_result", None)
    st.info("Inputs changed. The previous result is hidden; rerun SCIP to solve this model.")

is_reference = (k == 5 and source.startswith("Notebook")
                and beta == 1.0 and delta == 1.0)

st.subheader("2 · Understand the current model")
st.caption("Your choices: " + str(int(k)) + " new monitoring sites · " + source +
           f" · redundancy {beta:g} · wake {delta:g}. "
           "Changing any setting requires a new solution.")
a, b, c = st.columns(3)
a.metric("Original sites", f"{len(data.ids):,}")
b.metric("Existing stations", str(len(instance.fixed_indices)))
c.metric("New-site budget", str(int(k)))
st.caption(
    "CRS: EPSG:32651 (meters) · N=20 free candidate decisions · "
    f"Dataset SHA-256: `{dataset_sha[:16]}…`"
)
if is_reference:
    st.success(
        "Committed notebook-reference scenario: N=20, K=5, notebook weights, "
        "15 explicitly marked existing stations."
    )
else:
    st.info(
        "Exploratory parameter comparison: this is not the pinned N20/K5 "
        "notebook default and must not be labeled a publication reproduction."
    )

with st.expander("Scientific equation and model constraints", expanded=False):
    st.latex(
        r"\min_{\mathbf{x}\in\{0,1\}^{20}}\ "
        r"\sum_i a_i x_i+\sum_{i<j}q_{ij}x_ix_j"
    )
    st.latex(r"\sum_i x_i=" + str(int(k)))
    st.latex(r"x_i\leq f_i+\sum_{j\in\mathcal{N}(i)}x_j")
st.caption(
    "The coefficients aᵢ and qᵢⱼ below are generated from the actual current "
    "instance. The local one-hop rule does NOT establish global path connectivity. "
    "SCIP solves an exact binary-product MILP equivalent to this original objective."
)
with st.expander("Inspect actual coefficients, sites, adjacency and source fingerprint"):
    st.write(f"**Model fingerprint:** `{fingerprint}`")
    st.dataframe(pd.DataFrame({
        "local_i": list(range(N_FREE)),
        "master_feature_position": instance.free_indices.astype(int),
        "a_i": instance.linear.astype(float),
        "a_i_float64_hex": [float(x).hex() for x in instance.linear],
        "fixed_neighbor": instance.fixed_neighbors.astype(int),
        "free_neighbor_indices": [str(v) for v in instance.neighbors],
    }), hide_index=True, use_container_width=True)
    st.caption(
        f"{len(instance.quadratic)} free-free quadratic interactions; "
        "fixed-station effects have been folded into linear terms."
    )
    with st.expander("Show every numerical quadratic interaction qᵢⱼ"):
        st.dataframe(pd.DataFrame([
            {
                "local_i": int(i),
                "local_j": int(j),
                "q_ij": float(q),
                "q_ij_float64_hex": float(q).hex(),
            }
            for i, j, q in instance.quadratic
        ]), hide_index=True, use_container_width=True)
    st.download_button(
        "Download current formulation JSON",
        data=json.dumps(model, sort_keys=True, indent=2),
        file_name=f"water-formulation-{fingerprint[:12]}.json",
        mime="application/json",
        use_container_width=True,
    )

st.subheader("3 · Placement results")
if run:
    with st.spinner("Solving the exact selected formulation with SCIP…"):
        try:
            with TemporaryDirectory(prefix="qopt-water-mvp-") as folder:
                lp_path = Path(folder) / "actual_scip_model.lp"
                chosen, metrics = solve_scip(
                    instance, time_limit=SCIP_TIME_LIMIT, export_lp_path=lp_path
                )
                audit = check_selected(instance, chosen, metrics, model)
                if is_reference and metrics["optimal"]:
                    if (abs(audit["independent_original_objective"] -
                            NOTEBOOK_N20_K5_OPTIMUM) > 1e-7 or
                            tuple(audit["selected_local_positions"]) != NOTEBOOK_N20_K5_LOCAL_INDICES):
                        raise AssertionError("Certified notebook N20 benchmark unexpectedly changed")
                csv_bytes = selected_csv(instance, chosen)
                lp_bytes = lp_path.read_bytes()
                archive = evidence_zip(model, audit, metrics, csv_bytes, lp_bytes)
            st.session_state["mvp_result"] = {
                "fingerprint": fingerprint,
                "chosen": chosen.tolist(),
                "metrics": metrics,
                "independent": audit,
                "zip": archive,
            }
        except (ValueError, OSError, RuntimeError, AssertionError) as exc:
            st.session_state.pop("mvp_result", None)
            st.error("SCIP could not produce a verified result for these settings: " + str(exc))

current = st.session_state.get("mvp_result")
if current is None or current["fingerprint"] != fingerprint:
    st.info("Choose settings in the sidebar, then select **Find monitoring locations (SCIP)**. Nothing is solved until you run it.")
    st.stop()

selected = np.asarray(current["chosen"], dtype=int)
metrics = current["metrics"]
independent = current["independent"]
if not metrics["optimal"]:
    st.warning("SCIP has a feasible incumbent, but optimality is NOT certified at the 30-second time limit.")
else:
    st.success("SCIP certified an optimal solution for the currently displayed model.")

c1, c2, c3 = st.columns(3)
c1.metric("Original objective (min.)", f"{independent['independent_original_objective']:.6f}")
c2.metric("Selected new sites", len(independent["selected_local_positions"]))
c3.metric("SCIP status", metrics["status"])
st.caption(
    f"Independent original feasible: {independent['original_feasible']} · "
    f"Exact K residual: {independent['budget_residual']} · "
    f"One-hop violations: {len(independent['violated_local_one_hop_sites'])} · "
    f"Model: `{fingerprint[:16]}…`"
)

coordinates = instance.coords
labels = np.array(
    ["New sensor" if selected[i] else "Candidate" for i in range(N_FREE)] +
    ["Existing" for _ in instance.fixed_indices]
)
longitude, latitude = converter().transform(coordinates[:, 0], coordinates[:, 1])
palette = {
    "New sensor": [15, 121, 208, 235],
    "Existing": [221, 68, 54, 220],
    "Candidate": [140, 149, 159, 110],
}
frame = pd.DataFrame({
    "lon": longitude, "lat": latitude, "type": labels,
    "color": [palette[label] for label in labels],
})
st.pydeck_chart(pdk.Deck(
    layers=[pdk.Layer(
        "ScatterplotLayer", data=frame, get_position="[lon, lat]",
        get_fill_color="color", get_radius=1200, pickable=True,
    )],
    initial_view_state=pdk.ViewState(
        latitude=float(np.mean(latitude)),
        longitude=float(np.mean(longitude)), zoom=9,
    ),
    tooltip={"text": "{type}"},
))
st.caption("Blue: new · Red: existing · Gray: unselected. Converted EPSG:32651 → WGS84 for display.")
st.dataframe(pd.DataFrame({
    "master_feature_position": independent["selected_master_feature_positions"],
    "easting_m": coordinates[:N_FREE][selected.astype(bool), 0],
    "northing_m": coordinates[:N_FREE][selected.astype(bool), 1],
}), hide_index=True, use_container_width=True)
st.download_button(
    "Download experiment, verified result and actual SCIP LP (.zip)",
    data=current["zip"],
    file_name=f"water-mvp-{fingerprint[:12]}.zip",
    mime="application/zip",
    use_container_width=True, key="mvp_download",
)
st.caption(
    "Evidence contains formulation coefficients, source hash, independently "
    "checked objective/constraints, original SCIP LP, selected-site CSV and file checksums. "
    "Previous-paper energy ≈−3.301319 is NOT a matching-input validation target."
)
