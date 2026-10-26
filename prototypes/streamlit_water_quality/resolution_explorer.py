"""Read-only water-quality multi-resolution source-candidate exploration.

This page renders source geometry and deterministic cohort provenance only.
It does not change the validated N20 solver/ZIP workflow, run SCIP/SA,
or treat candidate availability as optimized sensor deployments.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from pyproj import Transformer

from problems.water_quality.nested_resolution import (
    REFERENCE_GEOJSON,
    NestedStudy,
    TierInstance,
    build_nested_instances,
)


@st.cache_data(show_spinner="Building source-backed N20/50/100 cohorts…", max_entries=1)
def get_nested_study(source_sha256: str) -> NestedStudy:
    """Cache only source-identity-keyed deterministic geometry; no solver work."""
    study = build_nested_instances(REFERENCE_GEOJSON)
    if study.source_sha256 != source_sha256:
        raise ValueError("Nested candidate source digest does not match the pinned dataset")
    if len(study.fixed_master_positions) != 15 or study.fixed_simulated:
        raise ValueError("Nested candidate study requires 15 marked existing stations")
    return study


def candidate_table(row: TierInstance) -> pd.DataFrame:
    """Exact source row/feature mapping; no solution or inferred deployment."""
    n = row.n_free
    return pd.DataFrame({
        "local_candidate_position": range(n),
        "source_feature_position": row.candidate_master_positions,
        "source_property_id": row.candidate_feature_ids,
        "easting_m": row.instance.coords[:n, 0],
        "northing_m": row.instance.coords[:n, 1],
        "utility_notebook_weights": row.instance.utility[:n],
    })


def fixed_station_table(study: NestedStudy, row: TierInstance) -> pd.DataFrame:
    n = row.n_free
    return pd.DataFrame({
        "source_feature_position": study.fixed_master_positions,
        "source_property_id": study.fixed_feature_ids,
        "easting_m": row.instance.coords[n:, 0],
        "northing_m": row.instance.coords[n:, 1],
    })


def _deck(row: TierInstance, study: NestedStudy) -> pdk.Deck:
    n = row.n_free
    m = len(study.fixed_master_positions)
    coordinates = row.instance.coords
    lon, lat = Transformer.from_crs(
        "EPSG:32651", "EPSG:4326", always_xy=True
    ).transform(coordinates[:, 0], coordinates[:, 1])
    points = pd.DataFrame({
        "lon": lon,
        "lat": lat,
        "site_type": ["Unselected candidate"] * n + ["Existing station"] * m,
        "source_position": list(row.candidate_master_positions) + list(study.fixed_master_positions),
        "source_id": list(row.candidate_feature_ids) + list(study.fixed_feature_ids),
        "color": [[130, 145, 165, 160]] * n + [[221, 68, 54, 230]] * m,
    })
    return pdk.Deck(
        layers=[pdk.Layer(
            "ScatterplotLayer", data=points, get_position="[lon, lat]",
            get_fill_color="color", get_radius=1000, pickable=True,
        )],
        initial_view_state=pdk.ViewState(
            latitude=float(np.mean(lat)), longitude=float(np.mean(lon)), zoom=9
        ),
        tooltip={"text": "{site_type}: source feature position {source_position}, property ID {source_id}"},
    )


def cohort_comparison(study: NestedStudy) -> pd.DataFrame:
    rows = []
    for entry in study.tier_instances:
        rows.append({
            "Free decisions (N)": entry.n_free,
            "Existing fixed stations": len(entry.instance.fixed_indices),
            "New-site budget (K)": entry.instance.budget,
            "Pairwise free coefficients": len(entry.instance.quadratic),
            "Local free-free graph edges": sum(map(len, entry.instance.neighbors)) // 2,
            "Solver evidence": "not run in candidate explorer",
        })
    return pd.DataFrame(rows)


def render_nested_candidate_explorer(n_free: int, source_sha256: str) -> None:
    if n_free not in (50, 100):
        raise ValueError("Read-only N50/N100 explorer must not receive the live N20 path")
    study = get_nested_study(source_sha256)
    matches = [t for t in study.tier_instances if t.n_free == n_free]
    if len(matches) != 1:
        raise AssertionError("Missing unique source-backed resolution cohort")
    row = matches[0]
    st.subheader("Nested source candidates — candidate-only research")
    st.warning(
        "N=50/100 are deterministic candidate cohorts, NOT solved deployments. "
        "No SCIP, greedy, QUBO tuning or simulated annealing has run for this view; "
        "there are no new-N optimality, feasibility, objective-gap or runtime claims."
    )
    st.caption(
        "Notebook Cell 2 / corrected second Cell 3 candidate construction: "
        "10,000-point hexagonal bounding-box pool, lake-hull containment, "
        "nearest original source features, deduplication, then FPS seeded by "
        "15 existing stations. Uses historic notebook AHP weights and road-based D2."
    )
    a, b, c = st.columns(3)
    a.metric("Free candidates (N)", n_free)
    b.metric("Fixed existing stations", len(study.fixed_master_positions))
    c.metric("New-station budget (K)", row.instance.budget)
    st.caption(
        f"Source: {study.source_feature_count:,} GeoJSON features · "
        f"EPSG:32651 · SHA-256: `{study.source_sha256}`"
    )
    st.subheader("Cross-resolution source comparison")
    st.dataframe(cohort_comparison(study), hide_index=True, use_container_width=True)
    st.caption(
        "N20 ⊂ N50 ⊂ N100 by original source feature *positions*. "
        "All tiers share the same 15 fixed stations. No cross-N solver timings "
        "or objective values are compared because none were measured here."
    )
    st.subheader(f"Candidate geometry — N={n_free}")
    st.pydeck_chart(_deck(row, study), use_container_width=True)
    st.caption(
        "Gray points: unselected candidate sites; red points: existing stations. "
        "No blue deployment sites or invented radio-network routes are shown."
    )
    st.dataframe(candidate_table(row), hide_index=True, use_container_width=True)
    with st.expander("Inspect fixed-station identities and source provenance"):
        st.dataframe(fixed_station_table(study, row), hide_index=True, use_container_width=True)
        st.caption(
            "Local candidate position, original GeoJSON array position and its "
            "property ID are distinct quantities. The GeoJSON is unchanged."
        )
    st.download_button(
        "Download candidate positions and weights (CSV)",
        data=candidate_table(row).to_csv(index=False).encode("utf-8"),
        file_name=f"laguna-source-candidates-n{n_free}-{source_sha256[:12]}.csv",
        mime="text/csv",
        use_container_width=True,
        key="nested_candidates_csv",
    )
    st.download_button(
        "Download full nested source manifest (JSON)",
        data=json.dumps(study.manifest(), sort_keys=True, indent=2).encode("utf-8"),
        file_name=f"laguna-nested-cohorts-{source_sha256[:12]}.json",
        mime="application/json",
        use_container_width=True,
        key="nested_manifest_json",
    )
    st.info(
        "To run the existing independently attested local N20 SCIP experiment, "
        "select N=20. N50/N100 optimization and a cross-N result dashboard "
        "require separately reviewed solver and artifact protocols."
    )
