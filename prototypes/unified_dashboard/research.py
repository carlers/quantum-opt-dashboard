"""User-facing bounded N20 QUBO inspection and classical SA experiment.

This page consumes the same independently checked research modules/coef source
as the historical N20 CI. OpenJij SASampler is CLASSICAL simulated annealing,
NOT quantum hardware. This is a small exploratory sampler, never a claim of
historical paper reproduction or universal quantum speedup.
"""
from __future__ import annotations

import csv
import io
import json
import platform

from prototypes.water_import_guard import require_water_import_origins
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import pandas as pd
import streamlit as st

require_water_import_origins()

from model import NOTEBOOK_WEIGHTS, load_data, make_instance
from mvp_audit import EXPECTED_GEOJSON_SHA256, NOTEBOOK_N20_K5_OPTIMUM, source_sha
from qubo import make_qubo
from sa_benchmark import benchmark_penalties, decode_records, seed_summary
from formulation_audit import build_audit

SOURCE = Path(__file__).resolve().parents[2] / "problems/water_quality/data/LDB_centroids_clean.geojson"

def render_research_page() -> None:
    st.title("QUBO and classical annealing")
    st.caption("Frozen N=20, K=5 notebook-derived reference · explicit slack-encoded QUBO")
    st.warning(
        "The OpenJij SASampler here is **classical simulated annealing**, not a quantum "
        "processor. The historical paper's JijModeling/OMMX QUBO conversion is not "
        "established as equivalent to this explicit slack encoding. Small changes "
        "to float64 coefficients or penalties can substantially change sampled states."
    )


    @st.cache_data(show_spinner="Preparing source-pinned research model…")
    def get_reference():
        digest = source_sha(SOURCE)
        source = load_data(SOURCE)
        instance, simulated = make_instance(
            source, NOTEBOOK_WEIGHTS, 20, 5, beta=1., delta=1.
        )
        if simulated or len(instance.fixed_indices) != 15:
            raise ValueError("Expected original 15 marked existing stations")
        return digest, instance


    try:
        data_digest, instance = get_reference()
    except (OSError, ValueError, RuntimeError) as exc:
        st.error("The committed reference dataset could not be verified: " + str(exc))
        st.stop()

    st.subheader("Experiment: can classical annealing find valid monitoring sites?")
    st.write(
        "The exact SCIP result is our reference. Classical simulated annealing "
        "tries to find good bitstrings, but some samples can violate the station "
        "budget or local connection rule. You can compare how different constraint "
        "penalties affect those samples."
    )
    st.caption("Start with the notebook heuristic. You do not need to tune the "
               "penalty to run the example.")
    penalties = benchmark_penalties(instance)
    penalty_names = {
        "notebook-local-row-sum": "Notebook heuristic (good starting point)",
        "midpoint-exploratory": "Midpoint (exploratory comparison)",
        "global-feasibility-bound": "Global feasibility bound (conservative)",
    }
    penalty_explanations = {
        "notebook-local-row-sum": (
            "Based on the notebook's local coefficient row-sum heuristic. "
            "This is an experimental starting value, not a guarantee that every "
            "returned sample obeys the original constraints."
        ),
        "midpoint-exploratory": (
            "A middle value between the notebook heuristic and the global bound. "
            "Useful for comparing how penalty strength changes sampled outcomes."
        ),
        "global-feasibility-bound": (
            "Mathematically sufficient to favor feasible global optima when a "
            "feasible original assignment exists. It does NOT guarantee the "
            "classical stochastic sampler will find a feasible solution."
        ),
    }
    with st.expander("Advanced: choose a QUBO constraint penalty", expanded=False):
        st.caption(
            "**What is a penalty?** The QUBO adds an extra energy cost when a "
            "sample chooses the wrong number of sensors or breaks local adjacency. "
            "Changing the penalty changes the sampling landscape, not the original "
            "water-quality optimization problem."
        )
        label = st.selectbox(
            "QUBO penalty (equal budget and connectivity penalties)",
            list(penalties),
            format_func=lambda choice: penalty_names[choice],
            help="Larger penalties punish constraint violations more strongly, "
                 "but can also make the landscape harder to sample. "
                 "The notebook heuristic is an exploratory default; the global "
                 "bound does not guarantee a feasible sampled result.",
        )
        st.info(penalty_explanations[label])
    chosen_penalty = penalties[label]
    st.caption("Using: " + penalty_names[label] +
               f" · numerical penalty {chosen_penalty:.6g}. "
               "Open Advanced to compare other values.")
    settings = {
        "free_sites_n": 20, "new_sites_k": 5, "weight_profile": "notebook",
        "dataset_sha256": data_digest, "beta": 1.0, "delta": 1.0,
        "penalty_name": label, "penalty_value_float64_hex": chosen_penalty.hex(),
    }
    audit, qubo = build_audit(
        instance, dataset_sha256=data_digest, settings=settings,
        budget_penalty=chosen_penalty, connectivity_penalty=chosen_penalty,
    )
    fingerprint = audit["model_fingerprint_sha256"]
    previous = st.session_state.get("unified_sa_run")
    if previous is not None and previous["fingerprint"] != fingerprint:
        st.session_state.pop("unified_sa_run", None)
        st.info("Penalty changed; old SA samples are hidden for this different QUBO.")

    a,b,c = st.columns(3)
    a.metric("Original binary variables", qubo.n_free)
    b.metric("Total QUBO binary variables", qubo.n_variables)
    c.metric("Nonzero QUBO terms", len(qubo.coefficients))
    st.latex(r"E_{Q}=E_{original}(x)+P_b(\sum_i x_i-K)^2"
             r"+P_c\sum_i(f_i+\sum_{j\in N(i)}x_j-x_i-s_i)^2")
    st.caption(
        "Source is SHA-pinned and the displayed QUBO is produced by the actual "
        "encoding implementation. Slack variables encode local one-hop constraints; "
        "they do **not** enforce global connected paths. SCIP is the exact reference."
    )
    with st.expander("Inspect original, SCIP MILP and actual QUBO coefficients"):
        original_tab, milp_tab, qubo_tab = st.tabs(
            ["Original objective", "SCIP exact MILP", "Encoded QUBO"]
        )
        with original_tab:
            st.json(audit["original_miqp"])
        with milp_tab:
            st.json(audit["scip_solver_milp"])
        with qubo_tab:
            st.write(f"**Budget/connectivity penalty:** {chosen_penalty:.16g}")
            st.write(f"**QUBO offset:** {qubo.offset:.16g}")
            st.dataframe(pd.DataFrame([
                {"i": i, "j": j, "coefficient": coefficient,
                 "float64_hex": float(coefficient).hex()}
                for (i,j), coefficient in sorted(qubo.coefficients.items())
            ]), hide_index=True, use_container_width=True)

    st.download_button(
        "Download compiled original/MILP/QUBO inspection JSON",
        data=json.dumps(audit, sort_keys=True, indent=2, allow_nan=False),
        file_name=f"qubo-inspection-{fingerprint[:12]}.json",
        mime="application/json",
        key="unified_qubo_download",
    )

    st.subheader("Optional small classical SA experiment")
    reads = st.slider("Independent samples per run", min_value=1, max_value=16, value=4, step=1)
    sweeps = st.slider("Annealing sweeps", min_value=50, max_value=500, value=300, step=50)
    seed = st.number_input(
        "Parent RNG seed", min_value=0, max_value=4294967295,
        value=20261018, step=1,
    )
    st.caption(
        "Each sample is a separately seeded single-read OpenJij call. This is only "
        "an exploratory demonstration; the larger preregistered CI studies remain "
        "available in the repository and must not be read as proof of quantum advantage."
    )
    settings_key = sha256(json.dumps({
        "model": fingerprint, "reads": int(reads), "sweeps": int(sweeps),
        "seed": int(seed),
    }, sort_keys=True).encode()).hexdigest()
    if st.session_state.get("unified_sa_run", {}).get("settings_key") != settings_key:
        st.session_state.pop("unified_sa_run", None)

    if st.button("Run bounded classical simulated annealing", type="primary"):
        try:
            import openjij as oj

            q = qubo.as_index_qubo()
            q.update({(i, i): q.get((i, i), 0.) for i in range(qubo.n_variables)})
            children = np.random.SeedSequence(int(seed)).spawn(int(reads))
            seeds = [int(child.generate_state(1, dtype=np.uint32)[0]) for child in children]
            if len(set(seeds)) != len(seeds):
                raise AssertionError("Child sample RNG seeds collided")
            sampler = oj.SASampler()
            samples: list[dict] = []
            start = perf_counter()
            with st.spinner("Classical OpenJij sampling (bounded)…"):
                for index, child_seed in enumerate(seeds):
                    response = sampler.sample_qubo(
                        q, num_reads=1, num_sweeps=int(sweeps),
                        seed=child_seed, sparse=True,
                    )
                    samples.extend(decode_records(
                        response, qubo, instance, seed=int(seed), penalty_name=label,
                        sample_seed=child_seed, read_index=index,
                    ))
            summary = seed_summary(
                samples, expected_reads=int(reads), optimum=NOTEBOOK_N20_K5_OPTIMUM
            )
            result = {
                "research_scope": "bounded classical simulated annealing ONLY",
                "algorithm": "OpenJij SASampler, not quantum hardware",
                "not_historical_converter": True,
                "data_sha256": data_digest,
                "model_fingerprint_sha256": fingerprint,
                "penalty_name": label,
                "penalty_exact_hex": chosen_penalty.hex(),
                "parent_seed": int(seed), "child_seeds": seeds,
                "sweeps": int(sweeps), "num_reads": int(reads),
                "baseline_notebook_scip_optimum": NOTEBOOK_N20_K5_OPTIMUM,
                "numerical_caveat": "Last-bit coefficient drift can change returned sample states.",
                "summary": summary, "sample_records": samples,
                "versions": {
                    "python": platform.python_version(), "openjij": version("openjij"),
                },
                "elapsed_wall_seconds": perf_counter() - start,
            }
            st.session_state["unified_sa_run"] = {
                "settings_key": settings_key, "fingerprint": fingerprint,
                "result": result,
            }
        except (ImportError, ValueError, AssertionError, RuntimeError) as exc:
            st.session_state.pop("unified_sa_run", None)
            st.error("Bounded OpenJij experiment could not be validated: " + str(exc))

    result = st.session_state.get("unified_sa_run")
    if result and result["settings_key"] == settings_key:
        summary = result["result"]["summary"]
        st.metric("Original-feasible samples", f"{summary['feasible_sample_count']}/{int(reads)}")
        st.metric("Best feasible original objective",
                  "None" if summary["best_feasible_raw_objective"] is None
                  else f"{summary['best_feasible_raw_objective']:.6f}")
        st.caption(
            "Exact SCIP/independent baseline: "
            f"{NOTEBOOK_N20_K5_OPTIMUM:.9f}. No feasible SA solution is a "
            "legitimate result, not a solver failure."
        )
        st.json(summary)
        st.download_button(
            "Download full seeded SA sample audit JSON",
            data=json.dumps(result["result"], indent=2, sort_keys=True, allow_nan=False),
            file_name=f"classical-sa-{settings_key[:12]}.json",
            mime="application/json",
        )
    else:
        st.info("QUBO inspection is available now. Sampling runs only when you press Run.")

