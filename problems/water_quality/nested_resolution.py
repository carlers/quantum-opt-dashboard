"""Auditable, offline N20/50/100 source-backed nested water-quality cohorts.

This is an additive research entry point, not a Streamlit selector, batch
scheduler, solver benchmark, or claim of manuscript numerical replication.
The frozen N20 model and its historical source files are not modified.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import numpy as np

from prototypes.streamlit_water_quality.model import (
    Instance,
    NOTEBOOK_WEIGHTS,
    existing_stations,
    load_data,
    make_instance,
    select_sites,
    site_utility,
)

REFERENCE_GEOJSON = (
    Path(__file__).resolve().parents[2]
    / "problems/water_quality/data/LDB_centroids_clean.geojson"
)
INITIAL_TIERS = (20, 50, 100)
SAMPLING_METHOD = "hex-bbox-10000 -> water hull -> nearest master -> unique -> fixed-seeded FPS"


@dataclass(frozen=True)
class TierInstance:
    n_free: int
    instance: Instance
    # Position in the original GeoJSON features array, NOT local candidate
    # position and NOT properties["id"].
    candidate_master_positions: tuple[int, ...]
    candidate_feature_ids: tuple[int, ...]


@dataclass(frozen=True)
class NestedStudy:
    source_sha256: str
    source_feature_count: int
    fixed_master_positions: tuple[int, ...]
    fixed_feature_ids: tuple[int, ...]
    fixed_simulated: bool
    tier_instances: tuple[TierInstance, ...]

    def manifest(self) -> dict:
        """JSON-compatible provenance, deliberately excluding solver claims."""
        return {
            "schema_version": "nested-source-cohorts-v1",
            "source_sha256": self.source_sha256,
            "source_feature_count": self.source_feature_count,
            "sampling_method": SAMPLING_METHOD,
            "model_profile": "committed-notebook-weights / historical local one-hop",
            "weights": [float(w) for w in NOTEBOOK_WEIGHTS],
            "new_station_budget": 5,
            "fixed_master_positions": list(self.fixed_master_positions),
            "fixed_feature_ids": list(self.fixed_feature_ids),
            "fixed_simulated": self.fixed_simulated,
            "tiers": [
                {
                    "n_free": row.n_free,
                    "candidate_master_positions": list(row.candidate_master_positions),
                    "candidate_feature_ids": list(row.candidate_feature_ids),
                    "total_graph_vertices": len(row.instance.coords),
                    "pairwise_free_terms": len(row.instance.quadratic),
                    "d_max_m": float(row.instance.d_max),
                }
                for row in self.tier_instances
            ],
            "solver_executed": False,
            "paper_parity_claimed": False,
        }


def _validate_tiers(tiers: tuple[int, ...]) -> None:
    if not tiers or any(type(n) is not int for n in tiers):
        raise ValueError("Select a nonempty tuple of integer candidate counts")
    if tuple(sorted(set(tiers))) != tiers:
        raise ValueError("Tiers must be ascending and unique")
    if not set(tiers).issubset(INITIAL_TIERS):
        raise ValueError("Initial offline gate supports only N=20,50,100")


def build_nested_instances(
    source: str | Path = REFERENCE_GEOJSON,
    *,
    tiers: tuple[int, ...] = INITIAL_TIERS,
) -> NestedStudy:
    """Build instances without solving them; preserve exact GeoJSON identity.

    Each tier invokes the existing frozen make_instance path independently.
    A separate maximum-N FPS pass verifies that every emitted tier is a
    strict prefix of one common deterministic master-candidate ordering.
    Repeated geometric construction is intentional in this correctness-first
    gate; optimize only after a reproducible numerical baseline is archived.
    """
    _validate_tiers(tiers)
    source = Path(source)
    source_sha256 = sha256(source.read_bytes()).hexdigest()
    data = load_data(source)
    utility = site_utility(data.factors, NOTEBOOK_WEIGHTS)
    fixed, simulated = existing_stations(data, utility)
    max_free, _ = select_sites(data, fixed, max(tiers))
    fixed_positions = tuple(int(i) for i in fixed)
    rows: list[TierInstance] = []
    for n in tiers:
        instance, instance_simulated = make_instance(
            data, NOTEBOOK_WEIGHTS, n_free=n, budget=5
        )
        expected = max_free[:n]
        if not np.array_equal(instance.free_indices, expected):
            raise AssertionError(f"N={n} candidate order differs from shared FPS prefix")
        if not np.array_equal(instance.fixed_indices, fixed):
            raise AssertionError(f"N={n} fixed stations differ from source reference")
        if instance_simulated != simulated:
            raise AssertionError(f"N={n} fixed-station provenance changed")
        if len(set(int(i) for i in instance.free_indices)) != n:
            raise AssertionError(f"N={n} duplicate source candidates")
        if np.intersect1d(instance.free_indices, fixed).size:
            raise AssertionError(f"N={n} free candidates overlap existing stations")
        positions = tuple(int(i) for i in instance.free_indices)
        rows.append(TierInstance(
            n_free=n,
            instance=instance,
            candidate_master_positions=positions,
            candidate_feature_ids=tuple(int(data.ids[i]) for i in positions),
        ))
    return NestedStudy(
        source_sha256=source_sha256,
        source_feature_count=len(data.coords),
        fixed_master_positions=fixed_positions,
        fixed_feature_ids=tuple(int(data.ids[i]) for i in fixed_positions),
        fixed_simulated=simulated,
        tier_instances=tuple(rows),
    )
