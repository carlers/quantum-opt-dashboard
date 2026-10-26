"""Small explicit user-run 2x2 classical penalty sweeps; local host only."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from problems.water_quality.experiment_jobs import JobError, local_opt_in
from problems.water_quality.experiment_sweeps import (
    SweepSpec, cancel_sweep, export_sweep, launch_sweep,
    list_sweeps, read_sweep,
)


def render_sweep_section():
    if not local_opt_in():
        return

    with st.expander("Optional · Run a bounded 2×2 QUBO penalty sweep"):
        st.warning(
            "Exactly four N20 classical OpenJij configurations. This is a "
            "small user-controlled exploratory run, not the 9,216-sample "
            "confirmatory study, quantum hardware, or an optimal-penalty claim."
        )
        with st.form("bounded_classical_2x2_penalty_sweep"):
            k = st.number_input(
                "Sweep new sensors (K)", min_value=1, max_value=10,
                value=5, step=1, key="sweep_k",
            )
            first, second = st.columns(2)
            with first:
                bl = st.number_input(
                    "Budget penalty λb — first value",
                    min_value=0.01, max_value=1000.0,
                    value=2.0, key="sweep_b_low",
                )
                bh = st.number_input(
                    "Budget penalty λb — second value",
                    min_value=0.01, max_value=1000.0,
                    value=12.0, key="sweep_b_high",
                )
                reads = st.slider(
                    "Individually seeded samples per cell", 1, 8, 2,
                    key="sweep_reads",
                )
            with second:
                cl = st.number_input(
                    "Connectivity penalty λc — first value",
                    min_value=0.01, max_value=1000.0,
                    value=2.0, key="sweep_c_low",
                )
                ch = st.number_input(
                    "Connectivity penalty λc — second value",
                    min_value=0.01, max_value=1000.0,
                    value=12.0, key="sweep_c_high",
                )
                sweeps = st.slider(
                    "Annealing sweeps per read", 10, 100, 40,
                    step=10, key="sweep_sweeps",
                )
            seed = st.number_input(
                "Sweep parent seed", min_value=0, max_value=4294967295,
                value=20261026, step=1, key="sweep_parent",
            )
            st.caption(
                "Each of the four cells has its own deterministic child-parent "
                "seed, then independently seeded one-read calls. All feasible and "
                "infeasible results are preserved with the exact original model."
            )
            submit = st.form_submit_button(
                "Launch four bounded classical experiments", type="primary",
            )
        if submit:
            try:
                spec = SweepSpec(
                    k_new=int(k), budget_levels=(float(bl), float(bh)),
                    connectivity_levels=(float(cl), float(ch)),
                    reads_per_cell=int(reads),
                    sweeps_per_read=int(sweeps), parent_seed=int(seed),
                )
                sweep_id = launch_sweep(spec)
                st.session_state["local_selected_sweep"] = sweep_id
                st.success(
                    "Four-cell sequential local worker launched: " + sweep_id[:12]
                )
            except (JobError, ValueError, OSError) as exc:
                st.error("2×2 research sweep not launched: " + str(exc))

    archived = list_sweeps()
    if not archived:
        return
    st.subheader("Saved 2×2 experimental sweeps")
    st.caption(
        "Refresh manually after launch; each cell is an independently stored "
        "research job. The CSV/chart summarize only original-source feasible "
        "draws, never augmented QUBO energies across different penalties."
    )
    st.button("Refresh sweep statuses", key="local_sweep_refresh")
    st.dataframe(pd.DataFrame([{
        "Sweep": x["sweep_id"][:12],
        "Created (UTC)": x["config"]["created_at"],
        "Status": x["state"]["status"],
        "Completed cells": f"{x['state']['completed_cells']}/4",
    } for x in archived]), hide_index=True, width="stretch")
    ids = [s["sweep_id"] for s in archived]
    previously = st.session_state.get("local_selected_sweep")
    active = st.selectbox(
        "Inspect saved 2×2 sweep", ids,
        index=ids.index(previously) if previously in ids else 0,
        format_func=lambda x: x[:12], key="local_sweep_viewer",
    )
    st.session_state["local_selected_sweep"] = active
    row = read_sweep(active)
    state = row["state"]
    st.progress(state["completed_cells"] / 4)
    st.caption(
        f"Sweep {active} · {state['status']} · "
        f"{state['completed_cells']}/4 complete cells."
    )
    if state["status"] in ("queued", "running"):
        if st.button("Request sweep cancellation", key="local_sweep_cancel"):
            if cancel_sweep(active):
                st.warning(
                    "Cancellation requested. The current small OpenJij cell "
                    "stops at the next per-read checkpoint; remaining cells "
                    "will not start."
                )
    if state["status"] in ("failed", "cancelled"):
        st.error(state.get("error") or "The batch did not complete.")
    with st.expander("Inspect immutable sweep configuration"):
        st.json(row["config"])

    if state["status"] != "completed" or row["result"] is None:
        return
    try:
        zipped = export_sweep(active)
    except (JobError, OSError, ValueError) as exc:
        st.error("The saved sweep did not pass checksum verification: " + str(exc))
        return
    st.subheader("2×2 observed classical feasibility")
    observations = row["result"]["observations"]
    dataframe = pd.DataFrame(observations)
    st.dataframe(dataframe[[
        "budget_penalty", "connectivity_penalty",
        "sample_count", "feasible_count",
        "observed_feasible_fraction",
        "best_feasible_original_objective",
        "child_job_id",
    ]], hide_index=True, width="stretch")
    st.caption(
        "One original model and K across all four cells. These are descriptive "
        "counts from one small user-run sweep, NOT an uncertainty estimate, "
        "best λ selection or quantum computation."
    )
    matrix = dataframe.pivot(
        index="budget_penalty", columns="connectivity_penalty",
        values="observed_feasible_fraction",
    )
    st.dataframe(matrix, width="stretch")
    st.download_button(
        "Download full 2×2 scientific evidence (all four original jobs)",
        data=zipped, file_name=f"lake-2x2-sweep-{active[:12]}.zip",
        mime="application/zip", key="local_sweep_export",
    )
