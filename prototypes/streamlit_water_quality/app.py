"""Mobile-friendly Streamlit scientific feasibility pilot; not paper-validated."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from pyproj import Transformer

from model import (FACTOR_NAMES, NOTEBOOK_WEIGHTS, PAPER_WEIGHTS,
                   existing_stations, load_data, make_instance, site_utility, solve_scip)

st.set_page_config(page_title="Water-quality optimization pilot", page_icon="🧪", layout="centered")
st.title("Water-quality placement · feasibility pilot")
st.caption("Experimental interface for the original Python notebook—not a validated reproduction.")
st.warning(
    "Notebook AHP weights differ from the previous paper's Table IV. "
    "Fixed-station inputs may also differ. Do not treat prototype output as a paper match."
)
DATA_PATH = Path(__file__).resolve().parents[2] / "problems/water_quality/data/LDB_centroids_clean.geojson"


@st.cache_data(show_spinner="Loading candidate-site data…")
def get_data():
    return load_data(DATA_PATH)


@st.cache_resource
def converter():
    return Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True)


try:
    data = get_data()
except Exception as exc:
    st.error(f"Could not read committed GeoJSON: {exc}")
    st.stop()

with st.sidebar:
    st.header("Experiment configuration")
    n_free = st.selectbox("Candidate free sites (N)", [20, 50], index=0,
                          help="N excludes existing fixed stations, matching the notebook")
    budget = st.number_input("New sensors (K)", min_value=0, max_value=int(n_free), value=5, step=1)
    source = st.radio("AHP factor weights", ["Notebook code", "Previous paper"], index=0)
    weights = NOTEBOOK_WEIGHTS.copy() if source == "Notebook code" else PAPER_WEIGHTS.copy()
    st.caption("Weights from different sources are not automatically interchangeable.")
    with st.expander("Adjust eight factor weights"):
        if st.checkbox("Customize weights", value=False):
            weights = np.array([
                st.number_input(name, min_value=0.0, max_value=1.0,
                                value=float(w), step=.01, format="%.4f")
                for name, w in zip(FACTOR_NAMES, weights)
            ])
    beta = st.number_input("Redundancy multiplier (β)", min_value=0.0, value=1.0, step=.25)
    delta = st.number_input("Wake multiplier (δ)", min_value=0.0, value=1.0, step=.25)
    max_seconds = st.slider("SCIP time limit (seconds)", 5, 120, 30)
    run = st.button("Run SCIP experiment", type="primary", use_container_width=True)

st.write(f"**Dataset:** {len(data.ids):,} geospatial candidate points · EPSG:32651 projected inputs")
if weights.sum() <= 0:
    st.error("Weight total must be positive")
    st.stop()
utility = site_utility(data.factors, weights)
fixed, simulated = existing_stations(data, utility)
st.info(
    f"Existing stations: {len(fixed)} (" +
    ("simulated three-station notebook fallback" if simulated else "marked in GeoJSON") +
    "). This is not necessarily the paper's 15-station case."
)

if run:
    with st.spinner("Building notebook-style candidate model and solving with SCIP…"):
        try:
            instance, _ = make_instance(data, weights, int(n_free), int(budget),
                                        beta=float(beta), delta=float(delta))
            solution, result = solve_scip(instance, time_limit=float(max_seconds))
            st.session_state["result"] = (instance, solution, result)
            st.session_state["settings"] = {"N": int(n_free), "K": int(budget),
                                             "weight_source": source, "weights": weights.tolist(),
                                             "beta": float(beta), "delta": float(delta)}
        except Exception as exc:
            st.session_state.pop("result", None)
            st.error(f"Experiment did not complete: {type(exc).__name__}: {exc}")

if "result" not in st.session_state:
    st.caption("Press **Run SCIP experiment**. No solver runs just from opening the app.")
    st.stop()

instance, solution, result = st.session_state["result"]
st.subheader("Last completed experiment")
st.caption(f"Configuration: {st.session_state['settings']}")
if not result["optimal"]:
    st.warning("SCIP returned a feasible incumbent without proving optimality.")
col1, col2, col3 = st.columns(3)
col1.metric("Energy (min)", f"{result['energy']:.6f}")
col2.metric("New sites", result["num_selected"])
col3.metric("SCIP status", result["status"])
st.write(
    f"Feasible: **{result['feasible']}** · Budget OK: **{result['budget_ok']}** · "
    f"Connectivity OK: **{result['connectivity_ok']}** · D_max: **{instance.d_max:.1f} m**"
)

coord = instance.coords
k = len(instance.free_indices)
labels = np.array(
    ["New sensor" if solution[i] else "Candidate" for i in range(k)] +
    ["Existing" for _ in range(len(instance.fixed_indices))]
)
longitude, latitude = converter().transform(coord[:, 0], coord[:, 1])
palette = {"New sensor": [15, 121, 208, 230], "Existing": [221, 68, 54, 220],
           "Candidate": [140, 149, 159, 110]}
map_data = pd.DataFrame({
    "lon": longitude, "lat": latitude, "type": labels,
    "color": [palette[label] for label in labels]
})
layer = pdk.Layer("ScatterplotLayer", data=map_data, get_position="[lon, lat]",
                  get_fill_color="color", get_radius=1200, pickable=True)
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=pdk.ViewState(latitude=float(np.mean(latitude)),
                                     longitude=float(np.mean(longitude)), zoom=9),
    tooltip={"text": "{type}"}
))
st.caption(
    "Blue: new sensor · Red: existing station · Gray: unselected candidate. "
    "Map coordinates converted to WGS84 for display."
)
st.dataframe(pd.DataFrame({
    "master_site_index": instance.free_indices[solution.astype(bool)],
    "Easting": coord[:k][solution.astype(bool), 0],
    "Northing": coord[:k][solution.astype(bool), 1]
}), hide_index=True, use_container_width=True)
st.warning(
    "The previous paper reports N=20 SCIP energy −3.301319, but its AHP weights "
    "and fixed-station setup do not match the committed notebook defaults. "
    "Match inputs and validate results before comparing energies."
)
