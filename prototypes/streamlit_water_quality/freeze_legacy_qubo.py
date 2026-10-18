"""One-time fixture generator: archive the existing issue #26 B/B QUBO bytes.

Never run this generator inside repeated SA host jobs. After a scientist reviews
the exact original B numerical model, commit its output and pin the file hash.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from evidence import canonical_bytes
from sa_paired_replication import PARENT_SEEDS, READS_PER_PARENT, SWEEPS
from sa_ulp_replay import (
    B_LINEAR_REFERENCE_HEX, PENALTY_HEX, SOURCE_ARCHIVE_SHA,
    build_arms, bits_digest,
)

FIXTURE_NAME = "historical_B_linear_B_penalty_n20_k5"
ARCHIVED_FEASIBLE_COUNT = 665
ARCHIVED_OPTIMUM_COUNT = 13


def generate_frozen_fixture() -> dict:
    arms = build_arms()
    name, original, qubo, provenance = next(
        item for item in arms if item[0] == "B-linear_B-penalty"
    )
    assert name == "B-linear_B-penalty"
    assert provenance["archive_source_instance_sha256"] == SOURCE_ARCHIVE_SHA["B"]
    assert qubo.budget_penalty.hex() == PENALTY_HEX["B"]
    assert qubo.connectivity_penalty.hex() == PENALTY_HEX["B"]
    assert len(qubo.coefficients) == 323 and qubo.n_variables == 46
    assert len(PARENT_SEEDS) == 32 and READS_PER_PARENT == 32 and SWEEPS == 300
    for index, exact in B_LINEAR_REFERENCE_HEX.items():
        assert float(original.linear[index]).hex() == exact
    child_seeds = []
    for parent in PARENT_SEEDS:
        children = np.random.SeedSequence(int(parent)).spawn(READS_PER_PARENT)
        seq = [int(child.generate_state(1, dtype=np.uint32)[0])
               for child in children]
        if len(set(seq)) != READS_PER_PARENT:
            raise ValueError(f"Non-unique read seeds for parent {parent}")
        child_seeds.append(seq)
    qubo_exact = {
        "n_free": int(qubo.n_free),
        "n_variables": int(qubo.n_variables),
        "offset_float64_hex": float(qubo.offset).hex(),
        "budget_penalty_float64_hex": float(qubo.budget_penalty).hex(),
        "connectivity_penalty_float64_hex": float(qubo.connectivity_penalty).hex(),
        "coefficient_terms_float64_hex": [
            [int(i), int(j), float(value).hex()]
            for (i, j), value in sorted(qubo.coefficients.items())
        ],
        "slack_variables": [list(g) for g in qubo.slack_variables],
        "slack_weights": [list(g) for g in qubo.slack_weights],
    }
    source_exact = {
        "n_free": len(original.linear),
        "new_station_budget": int(original.budget),
        "linear_float64_hex": [float(v).hex() for v in original.linear],
        "quadratic_float64_hex": [
            [int(i), int(j), float(v).hex()]
            for i, j, v in original.quadratic
        ],
        "neighbors": [list(group) for group in original.neighbors],
        "fixed_neighbor": [int(x) for x in original.fixed_neighbors],
        "free_master_positions": original.free_indices.astype(int).tolist(),
        "existing_master_positions": original.fixed_indices.astype(int).tolist(),
        "certified_original_scip_energy": -3.3012934918564643,
        "certified_selected_local_indices": [0, 1, 3, 6, 7],
    }
    assert bits_digest(qubo) == provenance["qubo_sha256"]
    return {
        "schema_version": 1,
        "label": FIXTURE_NAME,
        "historical_archive_mode": "B",
        "archived_original_instance_json_sha256": SOURCE_ARCHIVE_SHA["B"],
        "historical_source_note": (
            "Historical source-derived B/B coefficients and encoded row-sum QUBO "
            "from issue #26, NOT the paper's JijModeling compiler."
        ),
        "source_model": source_exact,
        "qubo": qubo_exact,
        "qubo_canonical_sha256": hashlib.sha256(canonical_bytes(qubo_exact)).hexdigest(),
        "seed_protocol": {
            "source_issue": 22,
            "sampler": "openjij.SASampler (classical simulated annealing)",
            "openjij_version": "0.12.2",
            "numpy_seedsequence_version": "2.5.4",
            "sweeps_per_read": SWEEPS,
            "reads_per_parent": READS_PER_PARENT,
            "num_reads_per_call": 1,
            "parent_seeds": list(PARENT_SEEDS),
            "child_seeds_uint32": child_seeds,
            "sparse": True,
            "expected_total_reads": len(PARENT_SEEDS) * READS_PER_PARENT,
            "seed_derivation": (
                "numpy.random.SeedSequence(parent).spawn(32); "
                "child.generate_state(1, dtype=np.uint32)[0]"
            ),
        },
        "historical_observation_only": {
            "feasible": ARCHIVED_FEASIBLE_COUNT,
            "optimum_hits": ARCHIVED_OPTIMUM_COUNT,
            "denominator": 1024,
            "not_a_required_new_cross_host_outcome": True,
        },
        "scientific_limit": (
            "Original B source-derived slack QUBO only; not a QPU or the "
            "historical paper's unverified JijModeling conversion."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    fixture = generate_frozen_fixture()
    if args.output.exists():
        raise FileExistsError(f"Will not overwrite existing fixture: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(fixture)
    args.output.write_bytes(payload)
    print("FROZEN_QUBO_CANDIDATE " + json.dumps({
        "file_sha256": hashlib.sha256(payload).hexdigest(),
        "qubo_sha256": fixture["qubo_canonical_sha256"],
        "coefficients": len(fixture["qubo"]["coefficient_terms_float64_hex"]),
        "variables": fixture["qubo"]["n_variables"],
        "reads": fixture["seed_protocol"]["expected_total_reads"],
        "bytes": len(payload),
        "note": "Review candidate; commit exact bytes before cross-run sampling",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
