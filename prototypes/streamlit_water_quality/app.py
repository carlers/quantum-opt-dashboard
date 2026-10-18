"""Mobile-friendly Streamlit scientific feasibility pilot; not paper-validated."""
from __future__ import annotations

from pathlib import Path
import hashlib
from tempfile import TemporaryDirectory

from formulation_audit import (
    build_audit, canonical_json, configuration_key, verify_selected,
)
from qubo import objective_bound, safe_penalty

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
    inspect = st.button("Inspect mathematical formulation", use_container_width=True,
                        help="Preview original MIQP, SCIP MILP and encoded QUBO without running a solver.")
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

# A rendered formula is a VIEW of these exact coefficient objects, never
# a second implementation of the mathematical model.
dataset_sha = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
settings = {
    "N": int(n_free), "K": int(budget), "weight_source": source,
    "weights": weights.tolist(), "beta": float(beta), "delta": float(delta),
    "scip_time_limit_seconds": int(max_seconds),
}
input_key = configuration_key(settings, dataset_sha)

if inspect or run:
    st.session_state["show_formulation"] = True

current_instance = None
audit = None
compiled_qubo = None
if st.session_state.get("show_formulation", False):
    with st.spinner("Compiling formulation from the selected inputs (no solver run)…"):
        try:
            # Run and inspect on this rerun both use exactly this SAME Instance.
            current_instance, _ = make_instance(
                data, weights, int(n_free), int(budget),
                beta=float(beta), delta=float(delta),
            )
        except Exception as exc:
            st.error(f"Could not construct the mathematical instance: {type(exc).__name__}: {exc}")
            st.stop()

    st.subheader("Mathematical formulation inspector")
    st.caption(
        "Read-only scientific audit. Changing the sidebar settings recompiles this preview; "
        "it never starts SCIP or OpenJij. The numeric coefficient tables and export "
        "are built from the same model.Instance used for SCIP."
    )
    custom_penalty = st.checkbox(
        "Customize QUBO penalties for inspection only",
        value=False, help="Does not change what the Run SCIP button solves.",
    )
    conservative = safe_penalty(current_instance)
    if custom_penalty:
        p_budget = st.number_input(
            "QUBO budget squared penalty", min_value=1e-9,
            value=float(conservative), format="%.12f",
        )
        p_local = st.number_input(
            "QUBO local connectivity squared penalty", min_value=1e-9,
            value=float(conservative), format="%.12f",
        )
    else:
        p_budget = p_local = None

    try:
        audit, compiled_qubo = build_audit(
            current_instance, dataset_sha256=dataset_sha, settings=settings,
            budget_penalty=p_budget, connectivity_penalty=p_local,
        )
    except Exception as exc:
        st.error(f"Cannot compile the QUBO audit: {type(exc).__name__}: {exc}")
        st.stop()

    original = audit["original_miqp"]
    milp = audit["scip_solver_milp"]
    qspec = audit["encoded_qubo"]
    st.caption(
        f"Model fingerprint (SHA-256): \`{audit['model_fingerprint_sha256']}\`"
    )
    st.write(
        f"**{int(n_free)} binary free-site decisions** · **{len(current_instance.fixed_indices)} "
        f"existing fixed sites** · **{len(original['quadratic_terms'])} original pair terms** · "
        f"**{compiled_qubo.n_variables} QUBO bits (including slack)**"
    )
    tabs = st.tabs(["Original MIQP", "SCIP MILP (solver code)", "Encoded QUBO", "Inspect / export"])

    with tabs[0]:
        st.latex(
            r"\min_{\mathbf{x}\in\{0,1\}^{N}}\ "
            r"\sum_{i=0}^{N-1}a_ix_i+\sum_{i<j}q_{ij}x_ix_j"
        )
        st.latex(r"\sum_{i=0}^{N-1}x_i = " + str(int(budget)))
        st.latex(
            r"x_i \le f_i+\sum_{j\in\mathcal{N}(i)} x_j"
            r"\quad\forall i\in\{0,\ldots,N-1\}"
        )
        st.warning(
            "Connectivity means local one-hop adjacency to another selected station or an "
            "existing station. It does NOT guarantee a route/path to an existing station."
        )
        st.caption(
            "All fixed-station interactions have already been folded into the linear "
            "coefficients a_i. This is the actual original binary quadratic objective."
        )
        st.dataframe([
            {"local_i": t["i"],
             "master_site": int(current_instance.free_indices[t["i"]]),
             "linear_a_i": t["a"]["value"],
             "exact_float64": t["a"]["float64_hex"]}
            for t in original["linear_terms"]
        ], hide_index=True, use_container_width=True)
        with st.expander("All free-free objective interactions"):
            st.dataframe([
                {"i": t["i"], "j": t["j"], "q_ij": t["q"]["value"],
                 "exact_float64": t["q"]["float64_hex"]}
                for t in original["quadratic_terms"]
            ], hide_index=True, use_container_width=True)
        with st.expander("Exact local constraint coefficients for every site"):
            st.dataframe([
                {"i": t["i"], "f_i": t["fixed_neighbor_indicator"],
                 "neighbor_local_indices": str(t["free_neighbor_indices"])}
                for t in original["local_one_hop_connectivity"]
            ], hide_index=True, use_container_width=True)

    with tabs[1]:
        st.info(
            "The SCIP button solves an **exact MILP linearization** of the binary "
            "quadratic objective; it does not submit a native MIQP and does not run a QUBO."
        )
        st.latex(
            r"\min_{\mathbf{x},\mathbf{p}}\ "
            r"\sum_i a_i x_i+\sum_{i<j} q_{ij} p_{ij}"
        )
        st.latex(
            r"p_{ij}\ge x_i+x_j-1,\quad p_{ij}\le x_i,\quad "
            r"p_{ij}\le x_j,\quad x_i,p_{ij}\in\{0,1\}"
        )
        st.caption("This equation is reconstructed from the exact SCIP solver implementation. After a run, download the actual .lp file exported from the same PySCIPOpt model to verify the solver input. SCIP additionally enforces the same budget and one-hop constraints.")
        st.dataframe([
            {"variable": t["name"], "x_i": t["i"], "x_j": t["j"],
             "coefficient": t["coefficient"]["value"],
             "pair_product_constraints": " ; ".join(t["constraints"])}
            for t in milp["product_variables"]
        ], hide_index=True, use_container_width=True)

    with tabs[2]:
        st.info(
            "This QUBO is compiled from the **exact binary-slack encoder** for research "
            "inspection. The live SCIP button does NOT run OpenJij. "
            "It is not the historical notebook's JijModeling-to-QUBO conversion."
        )
        st.latex(
            r"E_Q(\mathbf{b})=c+\sum_{i\le j}Q_{ij}b_ib_j"
        )
        st.latex(
            r"E_Q=E(\mathbf{x}) + P_b(\sum_i x_i-K)^2"
            r"+P_c\sum_i(f_i+\sum_{j\in\mathcal N(i)}x_j-x_i-s_i)^2"
        )
        st.write(
            f"**Penalty budget:** {compiled_qubo.budget_penalty:.12g} · "
            f"**Penalty connectivity:** {compiled_qubo.connectivity_penalty:.12g} · "
            f"**QUBO offset:** {compiled_qubo.offset:.12g}"
        )
        st.caption(
            f"{len(compiled_qubo.coefficients)} nonzero upper-triangular QUBO entries; "
            f"{compiled_qubo.n_variables - int(n_free)} auxiliary slack bits. "
            "The full exact values are downloadable."
        )
        bound = 2.0 * objective_bound(current_instance)
        if compiled_qubo.budget_penalty <= bound or compiled_qubo.connectivity_penalty <= bound:
            st.warning(
                "At least one penalty is not above the sufficient global-feasibility bound "
                "2B. This setting is exploratory and does not have that sufficient guarantee."
            )
        else:
            st.success(
                "Both penalties exceed 2B, a sufficient bound for the QUBO's global "
                "minimum to be originally feasible **if an original feasible solution exists**. "
                "This does not guarantee finite-time annealing success."
            )
        with st.expander("Exact nonzero QUBO coefficients"):
            st.dataframe([
                {"bit_i": t["i"], "bit_j": t["j"],
                 "Q_ij": t["coefficient"]["value"],
                 "exact_float64": t["coefficient"]["float64_hex"]}
                for t in qspec["nonzero_upper_triangular_terms"]
            ], hide_index=True, use_container_width=True)
        with st.expander("Binary slack variable mapping"):
            st.dataframe([
                {"site_i": t["site_i"], "bit_indices": str(t["bit_indices"]),
                 "bit_weights": str(t["bit_weights"])}
                for t in qspec["auxiliary_binary_slacks"]
            ], hide_index=True, use_container_width=True)

    with tabs[3]:
        st.write("Full model definition, input provenance, exact IEEE-754 coefficients, "
                 "SCIP linearization, QUBO matrix and auxiliary mappings.")
        st.code(
            "Dataset SHA-256: " + dataset_sha + "\n" +
            "Model SHA-256: " + audit["model_fingerprint_sha256"],
            language="text",
        )
        st.download_button(
            "Download mathematical audit (JSON)",
            data=canonical_json(audit).encode("utf-8"),
            file_name=f"water-formulation-{audit['model_fingerprint_sha256'][:12]}.json",
            mime="application/json",
            use_container_width=True,
        )
        st.caption(
            "A model fingerprint reflects the data/config/numeric coefficients in this "
            "preview. Different floating-point builds can yield different exact hashes; "
            "the hash is not proof of historical-paper equivalence."
        )

if run:
    with st.spinner("Solving the SAME inspected model instance with SCIP…"):
        try:
            if current_instance is None:
                raise RuntimeError("Cannot run without a successfully compiled model")
            # Export the exact original MILP from the SAME SCIP model object
            # that is optimized, rather than exporting a separate mock model.
            with TemporaryDirectory(prefix="water-scip-audit-") as directory:
                lp_file = Path(directory) / "water-quality-scip-model.lp"
                solution, result = solve_scip(
                    current_instance, time_limit=float(max_seconds),
                    export_lp_path=lp_file,
                )
                lp_export_bytes = lp_file.read_bytes()
            st.session_state["scip_lp_export"] = lp_export_bytes
            st.session_state["result"] = (current_instance, solution, result)
            st.session_state["settings"] = settings
            st.session_state["result_input_key"] = input_key
        except Exception as exc:
            st.session_state.pop("result", None)
            st.session_state.pop("scip_lp_export", None)
            st.session_state.pop("result_input_key", None)
            st.error(f"Experiment did not complete: {type(exc).__name__}: {exc}")

if "result" not in st.session_state:
    st.caption("Inspect the equations first, or press **Run SCIP experiment**.")
    st.stop()

if st.session_state.get("result_input_key") != input_key:
    st.warning(
        "Your experiment settings changed since the last SCIP run. "
        "The previous result is hidden to prevent a misleading equation/solution match. "
        "Press Run SCIP experiment again."
    )
    st.stop()

instance, solution, result = st.session_state["result"]
st.subheader("Last completed experiment")
if st.session_state.get("scip_lp_export"):
    st.download_button(
        "Download the actual SCIP model submitted for this run (.lp)",
        data=st.session_state["scip_lp_export"],
        file_name="water-quality-scip-model.lp",
        mime="text/plain",
        use_container_width=True,
        help="Exported by PySCIPOpt from the same solver model just before optimize().",
    )
st.caption(f"Configuration used: {st.session_state['settings']}")
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

# Independent check: decode the SCIP selection AGAINST the exported MIQP
# and the exact compiled QUBO, not just the solver-returned energy.
if audit is not None and compiled_qubo is not None:
    solution_audit = verify_selected(instance, compiled_qubo, audit, solution)
    if not np.isclose(solution_audit["original_objective"], result["energy"],
                      rtol=0, atol=1e-7) or not solution_audit["original_feasible"]:
        st.error("Independent mathematical audit disagrees with SCIP; inspect this run.")
        st.stop()
    with st.expander("Verify the returned solution against the equations", expanded=True):
        st.write(
            f"Original objective: **{solution_audit['original_objective']:.9f}** "
            f"(linear {solution_audit['linear_objective']:.9f} + "
            f"quadratic {solution_audit['quadratic_objective']:.9f})"
        )
        st.write(
            f"Budget residual: **{solution_audit['budget_residual']}** · "
            f"Local constraint violations: "
            f"**{len(solution_audit['violated_one_hop_sites'])}** · "
            f"Minimized-slack QUBO witness: "
            f"**{solution_audit['qubo_energy_with_minimized_slacks']:.9f}**"
        )
        st.caption("The original SCIP result is checked against the exact displayed model.")
        st.download_button(
            "Download selected-solution mathematical verification (JSON)",
            data=canonical_json(solution_audit).encode("utf-8"),
            file_name=f"water-solution-audit-{audit['model_fingerprint_sha256'][:12]}.json",
            mime="application/json",
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
