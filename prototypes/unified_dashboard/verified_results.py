"""Read-only independently reviewed, source-pinned offline SCIP/HiGHS results.

This UI never invokes a solver, never trusts session-state optimizers or
relabels a N20 ZIP as an N50/N100 result. A frozen reviewed snapshot names
the original short-retention CI artifact; it is not a signed certificate.
"""
from __future__ import annotations

from hashlib import sha1, sha256
import json
import math
from pathlib import Path
import re

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from pyproj import Transformer

from problems.water_quality.nested_resolution import (
    REFERENCE_GEOJSON, build_nested_instances,
)

SNAPSHOT = Path(__file__).resolve().parent / "data/reviewed_n50_n100_2026_10_26.json"
SNAPSHOT_GIT_BLOB_SHA = "cd13f1032a4cfab5cf4dc69105429bfd0d0bbeef"
SOURCE_SHA256 = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
EXPECTED_EVIDENCE_SHA256 = "c0fff39780dc21a42e1de14c126cde7adda16e28ca37d25a38b156497800deb2"
APPROVED_RUN_ID = 40305459517


class ReviewedSourceError(ValueError):
    """Evidence cannot be honestly shown for the active original source."""


def read_reviewed_snapshot(path: Path = SNAPSHOT) -> dict:
    raw = Path(path).read_bytes()
    # Git's content-addressed blob SHA-1, pinned to this exact reviewed snapshot.
    # This is source file integrity, NOT remote authentic signing.
    git_blob = sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if git_blob != SNAPSHOT_GIT_BLOB_SHA:
        raise ReviewedSourceError("Reviewed observation snapshot bytes changed")
    return json.loads(raw)


def validate_reviewed_observations(snapshot: dict, study) -> list[dict]:
    """Recompute both original objectives from source instances; no solver runs."""
    if (snapshot.get("schema") != "reviewed-n50-n100-one-ci-execution-v1"
            or snapshot.get("source_geojson_sha256") != SOURCE_SHA256
            or study.source_sha256 != SOURCE_SHA256
            or snapshot.get("original_artifact_zip_sha256") != EXPECTED_EVIDENCE_SHA256
            or snapshot.get("source_workflow_run_id") != APPROVED_RUN_ID
            or snapshot.get("archived_data_retention_days") != 14):
        raise ReviewedSourceError("Snapshot does not reference the reviewed source execution")
    if (len(study.fixed_master_positions) != 15 or study.fixed_simulated
            or len(study.tier_instances) != 3
            or tuple(t.n_free for t in study.tier_instances) != (20, 50, 100)):
        raise ReviewedSourceError("Fixed stations or nested source cohorts changed")
    limitations = snapshot["scientific_limitations"]
    if (any(value is not False for key, value in limitations.items()
            if key != "independent_statistical_repetitions")
            or limitations["independent_statistical_repetitions"] != 0):
        raise ReviewedSourceError("Snapshot contains unsupported scientific claims")
    rows = snapshot["observations"]
    if len(rows) != 2 or [x["n_free"] for x in rows] != [50, 100]:
        raise ReviewedSourceError("Only the two reviewed N50/N100 observations are available")
    validated = []
    for obs, tier in zip(rows, study.tier_instances[1:]):
        n = tier.n_free
        if (type(obs["n_free"]) is not int or obs["n_free"] != n
                or obs["new_sensor_budget"] != tier.instance.budget
                or obs["new_sensor_budget"] != 5
                or obs["scip_status"] != "optimal"
                or obs["highs_status"] != 0
                or obs["scip_gap"] != 0
                or obs["highs_gap"] != 0):
            raise ReviewedSourceError("SCIP/HiGHS status or original K changed")
        for name in ("model_sha256", "emitted_lp_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", obs[name]):
                raise ReviewedSourceError("Model or LP digest is not a SHA-256")
        selected = obs["selected_local_positions"]
        if (not isinstance(selected, list) or len(selected) != 5
                or any(type(i) is not int or i < 0 or i >= n for i in selected)
                or selected != sorted(set(selected))):
            raise ReviewedSourceError("Invalid selected local site positions")
        mapped = [int(tier.instance.free_indices[i]) for i in selected]
        if mapped != obs["selected_source_master_positions"]:
            raise ReviewedSourceError("Source GeoJSON master positions no longer match")
        flags = np.zeros(n, dtype=np.int64)
        flags[selected] = 1
        violations = [
            i for i in selected
            if not int(tier.instance.fixed_neighbors[i])
            and not any(flags[j] for j in tier.instance.neighbors[i])
        ]
        if violations:
            raise ReviewedSourceError("Selected station violates original local one-hop")
        linear = sum(float(tier.instance.linear[i]) for i in selected)
        quadratic = sum(
            float(q) for i, j, q in tier.instance.quadratic
            if flags[i] and flags[j]
        )
        value = linear + quadratic
        for key, expected in (
            ("original_objective", value),
            ("highs_dual_bound", value),
            ("linear_component", linear),
            ("quadratic_component", quadratic),
        ):
            recorded = obs[key]
            if (type(recorded) not in (int, float) or not math.isfinite(recorded)
                    or not math.isclose(recorded, expected, abs_tol=1e-7, rel_tol=1e-10)):
                raise ReviewedSourceError("Original source objective or HiGHS bound changed: " + key)
        for field in (
            "model_rebuild_seconds", "scip_call_including_lp_export_seconds",
            "child_wall_seconds",
        ):
            measured = obs[field]
            if type(measured) not in (int, float) or not 0 < measured < 180:
                raise ReviewedSourceError("Missing or impossible observed timing")
        validated.append(obs)
    lower = study.tier_instances[1].instance
    upper = study.tier_instances[2].instance
    if (list(lower.free_indices) != list(upper.free_indices[:50])
            or list(lower.fixed_indices) != list(upper.fixed_indices)
            or not np.array_equal(lower.linear, upper.linear[:50])):
        raise ReviewedSourceError("Nested candidate identity or objective coefficients changed")
    if snapshot["verified_cross_tier_small_embeds_unchanged_in_large"] is not True:
        raise ReviewedSourceError("Missing cross-tier source-model verification")
    return validated


@st.cache_data(show_spinner="Checking immutable archived observations against original geometry…", max_entries=1)
def reviewed_source_data():
    if sha256(REFERENCE_GEOJSON.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ReviewedSourceError("Committed historical lake GeoJSON SHA-256 changed")
    study = build_nested_instances()
    snapshot = read_reviewed_snapshot()
    validated = validate_reviewed_observations(snapshot, study)
    return snapshot, study, validated


def selected_site_map(study, row: dict) -> pdk.Deck:
    tier = next(x for x in study.tier_instances if x.n_free == row["n_free"])
    n = tier.n_free
    coords = tier.instance.coords
    lon, lat = Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True).transform(
        coords[:, 0], coords[:, 1]
    )
    selected = set(row["selected_local_positions"])
    types = ["Selected in archived SCIP/HiGHS run" if i in selected
             else "Available unselected candidate" for i in range(n)] + [
                 "Original existing station" for _ in study.fixed_master_positions
             ]
    palette = {
        "Selected in archived SCIP/HiGHS run": [15, 121, 208, 235],
        "Available unselected candidate": [140, 149, 159, 95],
        "Original existing station": [221, 68, 54, 225],
    }
    frame = pd.DataFrame({
        "lon": lon, "lat": lat, "status": types,
        "source_feature_position": list(tier.candidate_master_positions)
        + list(study.fixed_master_positions),
        "color": [palette[k] for k in types],
    })
    return pdk.Deck(
        layers=[pdk.Layer(
            "ScatterplotLayer", data=frame, get_position="[lon, lat]",
            get_fill_color="color", get_radius=1100, pickable=True,
        )],
        initial_view_state=pdk.ViewState(
            latitude=float(np.mean(lat)), longitude=float(np.mean(lon)), zoom=9,
        ),
        tooltip={"text": "{status} • source position {source_feature_position}"},
    )


def render_verified_results() -> None:
    st.title("Verified offline water-quality results")
    st.warning(
        "Archived SOURCE-MODEL results, not a live optimization, previous-manuscript "
        "reproduction, physical deployment validation, quantum run, or runtime benchmark."
    )
    try:
        snapshot, study, rows = reviewed_source_data()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        st.error("Archived source evidence was not verified: " + str(exc))
        st.stop()

    st.caption(
        "One CI execution on 26 Oct 2026 • source SHA-256 "
        f"{snapshot['source_geojson_sha256']} • 15 fixed stations • notebook "
        "weights / road-based D2 / historical local one-hop • K=5."
    )
    st.markdown(
        "[Open original independently verified workflow artifact]"
        f"({snapshot['source_artifact_url']})"
    )
    st.caption(
        f"Original uploaded workflow ZIP SHA-256: {snapshot['original_artifact_zip_sha256']}. "
        "GitHub's original archive retention is 14 days; this committed snapshot "
        "alone cannot replace the original LP/solver bytes or a durable science archive."
    )
    st.subheader("Two measured resolutions — original source objective")
    table = pd.DataFrame({
        "Free candidates (N)": [x["n_free"] for x in rows],
        "K": [x["new_sensor_budget"] for x in rows],
        "SCIP status": [x["scip_status"] for x in rows],
        "Original objective (min.)": [x["original_objective"] for x in rows],
        "Independent HiGHS dual bound": [x["highs_dual_bound"] for x in rows],
        "One observed SCIP-call time (s)": [
            x["scip_call_including_lp_export_seconds"] for x in rows
        ],
    })
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.scatter_chart(
        table.rename(columns={
            "Free candidates (N)": "N",
            "Original objective (min.)": "Objective",
        }), x="N", y="Objective", height=280,
    )
    st.caption(
        "Exactly TWO observations from ONE CI run. Neither timing trend, "
        "uncertainty estimate, stochastic replication, nor larger-N extrapolation "
        "can be inferred. N50 embeds feasibly and objective-conservingly into N100; "
        "these are native source-tier objectives, not a 5,417-site master objective."
    )
    st.info(
        "Historical N20 K5 has a separate pinned reference and independent exact "
        "oracle in the Water-quality placement page. It is not silently pooled "
        "into this one-run N50/N100 measurement series."
    )
    chosen_n = st.selectbox(
        "Archived experiment resolution (N)", (50, 100),
        index=0, key="reviewed_result_n",
    )
    chosen = next(x for x in rows if x["n_free"] == chosen_n)
    st.subheader(f"Archived selected sites • N={chosen_n}")
    a, b, c = st.columns(3)
    a.metric("New monitoring positions (K)", chosen["new_sensor_budget"])
    b.metric("Original objective", f"{chosen['original_objective']:.8f}")
    c.metric("SCIP / independent HiGHS", "Both optimal")
    st.pydeck_chart(selected_site_map(study, chosen), use_container_width=True)
    st.caption(
        "Blue: archive-selected source features · Red: 15 original existing "
        "stations · Gray: other available candidates. No live sensor placement "
        "or radio propagation is asserted."
    )
    st.dataframe(pd.DataFrame({
        "local_position": chosen["selected_local_positions"],
        "original_GeoJSON_feature_position": chosen["selected_source_master_positions"],
    }), hide_index=True, use_container_width=True)
    with st.expander("Inspect exact model/LP references and measured time scopes"):
        st.json({
            "source_dataset_sha256": snapshot["source_geojson_sha256"],
            "compiled_model_sha256": chosen["model_sha256"],
            "actual_exported_scip_lp_sha256": chosen["emitted_lp_sha256"],
            "worker_cold_source_rebuild_seconds": chosen["model_rebuild_seconds"],
            "SCIP_call_including_LP_export_seconds": chosen[
                "scip_call_including_lp_export_seconds"
            ],
            "child_process_total_wall_seconds": chosen["child_wall_seconds"],
            "observations": 1,
            "solver_source": "SCIP then independent SciPy HiGHS",
            "paper_data_and_field_validation": False,
        })
    st.download_button(
        "Download reviewed, source-bound observation snapshot (.json)",
        data=json.dumps(snapshot, indent=2, sort_keys=True).encode("utf-8"),
        file_name="laguna-reviewed-n50-n100-source-ci-snapshot.json",
        mime="application/json", key="reviewed_source_download",
    )
