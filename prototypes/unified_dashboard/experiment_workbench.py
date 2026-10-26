"""Local user-controlled experiment run configuration, history and evidence.

Only starts workers after an explicit button click on a trusted, private
operator's local host. No auto-solve on rerender. Not an authenticated
multiuser cloud queue and not a published manuscript reproduction.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from problems.water_quality.experiment_jobs import (
    JobError, Spec, export_bundle, job_root, launch_job,
    list_jobs, local_opt_in, read_job, request_cancel,
)


def render_experiment_page():
    st.title("Experiment workbench")
    st.caption("Explicit user-run computational research · source-pinned Laguna de Bay")
    st.warning(
        "Trusted local single-operator MVP ONLY. No user authentication or tenant "
        "isolation: never expose this enabled worker on a public Streamlit deployment. "
        "SCIP is classical exact MILP; OpenJij is classical simulated annealing, "
        "NOT QAOA or quantum hardware. Historical source notebook weights, road D2 "
        "and local one-hop do not reproduce all manuscript inputs."
    )
    if not local_opt_in():
        st.info(
            "Execution is disabled by default. On a private machine only, "
            "set QOPT_LOCAL_EXPERIMENTS=1 before starting Streamlit. "
            "The existing hosted preview should remain read-only."
        )
        return

    st.caption(
        f"Local evidence directory: {job_root()} — persistent on this machine "
        "only. Do not use a shared/public instance without authentication, "
        "quotas and a durable isolated worker backend."
    )
    st.subheader("1 · Configure your experiment")
    with st.form("local_research_job_config", clear_on_submit=False):
        method = st.selectbox(
            "Solver", ["SCIP — classical exact MILP", "OpenJij — classical SA"],
            help="SCIP reports optimality/gap. Classical SA does not prove optimality.",
        )
        solver = "scip" if method.startswith("SCIP") else "classical_sa"
        n = st.selectbox(
            "Free candidate sites (N)", [20, 50, 100] if solver == "scip" else [20],
            help="Source-validated nested tiers. SA beyond N20 needs another gate.",
        )
        k = st.number_input(
            "New sensors (K)", min_value=1, max_value=10, value=5, step=1,
            help="K affects the constraint model. N20/K5 alone has a pinned exact enumeration.",
        )
        if solver == "scip":
            seconds = st.slider("SCIP time limit (seconds)", 1, 30, 15, 1)
            reads, sweeps, seed, pb, pc = 4, 300, 20261026, 12.9, 12.9
        else:
            seconds = 15
            left, right = st.columns(2)
            with left:
                pb = st.number_input(
                    "Budget penalty (λb)", min_value=0.01,
                    max_value=1000.0, value=12.9, step=0.1,
                )
                reads = st.slider("Individually seeded samples", 1, 32, 4)
            with right:
                pc = st.number_input(
                    "Connectivity penalty (λc)", min_value=0.01,
                    max_value=1000.0, value=12.9, step=0.1,
                )
                sweeps = st.slider("Sweeps per sample", 10, 500, 300, 10)
            seed = st.number_input(
                "Parent seed", min_value=0, max_value=4294967295,
                value=20261026, step=1,
            )
            st.caption(
                "Each sample is separately seeded, in one OpenJij call. "
                "Changing λ changes the augmented QUBO, not the original objective. "
                "Infeasible states are always retained."
            )
        submitted = st.form_submit_button(
            "Launch bounded experiment", type="primary",
        )
    if submitted:
        try:
            spec = Spec(
                solver=solver, n_free=int(n), k_new=int(k),
                time_limit_seconds=int(seconds), reads=int(reads),
                sweeps=int(sweeps), parent_seed=int(seed),
                lambda_budget=float(pb), lambda_connectivity=float(pc),
            )
            job_id = launch_job(spec)
            st.session_state["local_selected_experiment"] = job_id
            st.success("Local worker launched: " + job_id[:12] + ". Refresh below to inspect.")
        except (JobError, OSError, ValueError) as exc:
            st.error("Experiment not launched: " + str(exc))

    st.subheader("2 · Saved experiment history")
    st.caption(
        "Persistent disk records are independent of Streamlit session state. "
        "Refresh manually; page navigation never schedules another experiment."
    )
    st.button("Refresh job statuses", key="local_job_refresh")
    jobs = list_jobs()
    if not jobs:
        st.info("No saved experiments yet. Submit a configuration explicitly above.")
        return
    records = []
    for job in jobs:
        spec = job["spec"]
        state = job["state"]
        records.append({
            "Job": job["job_id"][:12],
            "Created (UTC)": job["config"]["created_at"],
            "Method": "SCIP" if spec.solver == "scip" else "Classical SA",
            "N": spec.n_free, "K": spec.k_new, "Status": job["status"],
            "Progress": f"{state['completed_reads']}/{state['total_reads']}",
        })
    st.dataframe(pd.DataFrame(records), hide_index=True, use_container_width=True)
    ids = [j["job_id"] for j in jobs]
    previous = st.session_state.get("local_selected_experiment")
    index = ids.index(previous) if previous in ids else 0
    chosen = st.selectbox(
        "Inspect saved experiment", ids, index=index,
        format_func=lambda job_id: job_id[:12],
        key="local_experiment_viewer",
    )
    st.session_state["local_selected_experiment"] = chosen
    job = read_job(chosen)
    state = job["state"]
    spec = job["spec"]
    st.caption(f"Full experiment ID: {chosen}")
    st.progress(min(1.0, max(0.0, state["completed_reads"] / max(1, state["total_reads"]))))
    st.write(f"**Status:** {job['status']} · last updated: {state.get('updated_at', 'unknown')}")
    if job["status"] in ("queued", "running"):
        if st.button("Request cancellation", key="local_job_cancel"):
            if request_cancel(chosen):
                st.warning(
                    "Cancellation requested. SA stops after the current single-read call. "
                    "SCIP may finish its at-most-30-second solver call first."
                )
    if job["status"] in ("failed", "cancelled"):
        st.error(state.get("error") or "Worker ended without complete results.")
    with st.expander("Original submitted configuration and limitations"):
        st.json(job["config"])
    if job["result"]:
        result = job["result"]
        st.subheader("3 · Analyze original-source results")
        st.caption(
            "Original constrained objective, not arbitrary augmented QUBO energy. "
            "No manuscript input parity, physical field validation, or inferential claim."
        )
        record = result["result"]
        if spec.solver == "scip":
            sites = record["source_selection"]
            a, b, c = st.columns(3)
            a.metric("Original objective", f"{sites['energy']:.8f}")
            b.metric("Selected sensors", str(sites["num_selected"]))
            c.metric("SCIP status", record["scip_status"])
            st.caption(f"Reported SCIP gap: {record['scip_gap']:.6g}; "
                       "only explicit optimal status counts as solver-proven optimal.")
            st.dataframe(pd.DataFrame({
                "Local candidate position": sites["selected_local_positions"],
                "Original GeoJSON feature position": sites["selected_source_master_positions"],
            }), hide_index=True, use_container_width=True)
        else:
            a, b, c = st.columns(3)
            a.metric("Original-feasible draws",
                     f"{record['feasible_count']}/{record['total_samples']}")
            b.metric("Feasibility rate", f"{record['feasible_fraction']:.1%}")
            best = record["best_feasible_original_objective"]
            c.metric("Best feasible original objective",
                     f"{best:.7f}" if best is not None else "None")
            st.caption(
                "The N20/K5 original SCIP optimum is −3.3012934918564643. "
                "Only one submitted parent seed is used; this exploratory run "
                "is not a confirmatory statistical study."
            )
            st.json(record)
        st.caption(
            f"Source/model SHA-256: {result['source_sha256']} / "
            f"{result['model_sha256']} · worker elapsed: "
            f"{result['total_worker_wall_seconds']:.2f} seconds."
        )
        try:
            payload = export_bundle(chosen)
            st.download_button(
                "Download immutable model, configuration, samples and evidence ZIP",
                payload, file_name=f"lake-research-run-{chosen[:12]}.zip",
                mime="application/zip", key="local_job_export",
            )
        except (JobError, OSError) as exc:
            st.error("Evidence failed immutable checksum verification: " + str(exc))
    else:
        st.info("Results will appear here after this local worker finishes.")
