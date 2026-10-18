"""Replay a committed byte-for-byte archived B QUBO across fresh OpenJij processes.

Absolutely no source model, geometric terms, QUBO expansion, penalty or
child seeds are generated on sampler hosts. Original MIQP and encoded energies
are checked independently for every returned 46-bit state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
from importlib.metadata import version as package_version

import numpy as np

from evidence import canonical_bytes
from model import Instance
from qubo import Qubo, best_slack_assignment, energy as qubo_energy
from sa_benchmark import decode_records

FROZEN_FILE = (
    Path(__file__).parent / "fixtures" / "frozen_B_row_sum_qubo.json"
)
# SHA of the reviewed CI candidate, checked before committing its exact bytes.
FROZEN_SHA256 = "51d47e9a6ad320784019f02110e6543abee60da92453bc26e5c39b91e52398cb"
FROZEN_QUBO_SHA256 = "d4bd390b6ff8af6aa5fbaf38ec5a2515b3661d6f5bf728da0134f07d29e91746"
ARCHIVED_SOURCE_B_SHA256 = "0718156034e83d46223fa3e4e086bc9997c16f7252e3c348ca8ac70cf19d5532"
EXPECTED_PENALTY_HEX = "0x1.190ab5b15d1b3p+0"
SCIP_REFERENCE = -3.3012934918564643
SELECTED_REFERENCE = (0, 1, 3, 6, 7)
EXPECTED_READS = 1024


def read_frozen(path: Path = FROZEN_FILE) -> tuple[dict, Instance, Qubo]:
    """Read and independently inspect source and fully expanded fixed QUBO."""
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_SHA256:
        raise ValueError("Frozen B-mode file SHA-256 mismatch: stop before sampling")
    data = json.loads(raw)
    if raw != canonical_bytes(data):
        raise ValueError("Frozen fixture must use canonical original JSON bytes")
    if data.get("schema_version") != 1 or data.get("historical_archive_mode") != "B":
        raise ValueError("Unexpected frozen QUBO scenario/schema")
    if data["archived_original_instance_json_sha256"] != ARCHIVED_SOURCE_B_SHA256:
        raise ValueError("Unrecognized archived B source provenance")
    model = data["source_model"]
    encoded = data["qubo"]
    protocol = data["seed_protocol"]
    if hashlib.sha256(canonical_bytes(encoded)).hexdigest() != FROZEN_QUBO_SHA256:
        raise ValueError("Frozen QUBO coefficient/offset SHA-256 mismatch")
    if data["qubo_canonical_sha256"] != FROZEN_QUBO_SHA256:
        raise ValueError("Frozen input's claimed QUBO digest is invalid")
    if encoded["budget_penalty_float64_hex"] != EXPECTED_PENALTY_HEX or (
        encoded["connectivity_penalty_float64_hex"] != EXPECTED_PENALTY_HEX
    ):
        raise ValueError("Frozen historical row-sum penalty changed")
    if (model["n_free"], model["new_station_budget"], encoded["n_free"],
            encoded["n_variables"]) != (20, 5, 20, 46):
        raise ValueError("Expected original 20/5 model with 46 QUBO bits")
    if protocol["openjij_version"] != "0.12.2" or (
        protocol["sweeps_per_read"], protocol["reads_per_parent"],
        protocol["num_reads_per_call"], protocol["expected_total_reads"]
    ) != (300, 32, 1, 1024):
        raise ValueError("Historical sampler schedule was changed")
    parents = list(range(270010001, 270010033))
    seeds = protocol["child_seeds_uint32"]
    if protocol["parent_seeds"] != parents or len(seeds) != 32 or any(
        len(row) != 32 or len(set(row)) != 32 or any(
            not isinstance(k, int) or not 0 <= k <= 2**32 - 1 for k in row
        ) for row in seeds
    ):
        raise ValueError("Parent/child seed schedule differs from issue #22")
    if len({seed for row in seeds for seed in row}) != EXPECTED_READS:
        raise ValueError("Child seed collision across frozen experiment")
    # Verify frozen NumPy SeedSequence manifest once; DO NOT derive and use
    # new seeds for sampling. Sampler uses the reviewed manifest bytes only.
    for parent, expected in zip(parents, seeds):
        generated = [
            int(child.generate_state(1, dtype=np.uint32)[0])
            for child in np.random.SeedSequence(parent).spawn(32)
        ]
        if generated != expected:
            raise ValueError("Original frozen child-seed derivation differs")
    n = model["n_free"]
    linear = np.asarray(
        [float.fromhex(x) for x in model["linear_float64_hex"]], dtype=float
    )
    quadratic = tuple(
        (int(i), int(j), float.fromhex(q))
        for i, j, q in model["quadratic_float64_hex"]
    )
    neighbors = tuple(tuple(int(j) for j in group) for group in model["neighbors"])
    fixed = np.asarray(model["fixed_neighbor"], dtype=int)
    if (len(linear) != n or len(quadratic) != 12 or len(neighbors) != n
            or len(fixed) != n or len(model["existing_master_positions"]) != 15):
        raise ValueError("Original model/constraint data shape changed")
    for i, group in enumerate(neighbors):
        if (i in group or len(group) != len(set(group))
                or any(j < 0 or j >= n or i not in neighbors[j] for j in group)):
            raise ValueError("Frozen original one-hop graph invalid")
    if any(v not in (0, 1) for v in fixed):
        raise ValueError("Frozen fixed-station flags invalid")
    source = Instance(
        coords=np.zeros((35, 2), dtype=float),  # Geometry is NEVER recomputed.
        free_indices=np.asarray(model["free_master_positions"]),
        fixed_indices=np.asarray(model["existing_master_positions"]),
        utility=np.zeros(35, dtype=float),  # No utility-generation/fit in this study.
        linear=linear, quadratic=quadratic, neighbors=neighbors,
        fixed_neighbors=fixed, budget=5, d_max=0.0,
    )
    terms = [
        (int(i), int(j), float.fromhex(val))
        for i, j, val in encoded["coefficient_terms_float64_hex"]
    ]
    pairs = [(i, j) for i, j, _ in terms]
    if (len(terms) != 323 or len(set(pairs)) != 323
            or any(i < 0 or j < i or j >= 46 for i, j in pairs)):
        raise ValueError("Frozen QUBO term indexing malformed")
    qubo = Qubo(
        n_free=20,
        n_variables=46,
        coefficients={(i, j): v for i, j, v in terms},
        offset=float.fromhex(encoded["offset_float64_hex"]),
        budget_penalty=float.fromhex(encoded["budget_penalty_float64_hex"]),
        connectivity_penalty=float.fromhex(encoded["connectivity_penalty_float64_hex"]),
        slack_variables=tuple(tuple(group) for group in encoded["slack_variables"]),
        slack_weights=tuple(tuple(group) for group in encoded["slack_weights"]),
    )
    # The optimal binary x is not itself necessarily the correct slack assignment.
    chosen = [int(i in SELECTED_REFERENCE) for i in range(n)]
    optimal_bits = best_slack_assignment(source, qubo, chosen)
    if abs(qubo_energy(qubo, optimal_bits) - SCIP_REFERENCE) > 1e-7:
        raise AssertionError("Frozen QUBO optimum source energy changed")
    # Exhaustively verify original x-only budget+local-one-hop feasibility.
    from itertools import combinations
    feasible = 0
    minimum = float("inf")
    selected_argmin: tuple[int, ...] | None = None
    for subset in combinations(range(n), 5):
        selected = set(subset)
        if any(not (fixed[i] or any(j in selected for j in neighbors[i]))
               for i in selected):
            continue
        feasible += 1
        e = sum(float(linear[i]) for i in subset) + sum(
            float(q) for i, j, q in quadratic if i in selected and j in selected
        )
        if e < minimum - 1e-9:
            minimum, selected_argmin = e, subset
    if feasible != 1077 or selected_argmin != SELECTED_REFERENCE or (
        abs(minimum - SCIP_REFERENCE) > 1e-7
    ):
        raise AssertionError("Frozen original-source N20 feasibility/optimum changed")
    return data, source, qubo


def restricted_environment() -> dict:
    model_name = None
    p = Path("/proc/cpuinfo")
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                model_name = line.partition(":")[2].strip()
                break
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "openjij": package_version("openjij"),
        "cpu_model": model_name,
        "platform": platform.platform(),
        "workflow_commit": os.environ.get("GITHUB_SHA"),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "thread_env": {
            key: os.environ.get(key)
            for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }


def run_replay(replica: str) -> dict:
    fixture, instance, qubo = read_frozen()
    import openjij as oj
    if package_version("openjij") != "0.12.2":
        raise RuntimeError("Unexpected OpenJij binary; pins must be exact")
    # Historical code includes otherwise-zero QUBO diagonal indices to
    # ensure the sampler returns all 46 original and auxiliary variables.
    matrix = qubo.as_index_qubo()
    matrix.update({
        (i, i): matrix.get((i, i), 0.0) for i in range(qubo.n_variables)
    })
    all_samples = []
    for parent, child_seeds in zip(
        fixture["seed_protocol"]["parent_seeds"],
        fixture["seed_protocol"]["child_seeds_uint32"],
    ):
        # Preserve historical sampler instantiation scope: once per parent.
        sampler = oj.SASampler()
        for read_index, sample_seed in enumerate(child_seeds):
            response = sampler.sample_qubo(
                matrix, num_reads=1, num_sweeps=300,
                seed=int(sample_seed), sparse=True,
            )
            decoded = decode_records(
                response, qubo, instance, seed=int(parent),
                penalty_name="frozen_historical_B_row_sum",
                sample_seed=int(sample_seed), read_index=read_index,
            )
            if len(decoded) != 1 or decoded[0]["occurrences"] != 1:
                raise AssertionError("One read must yield one complete 46-bit sample")
            record = decoded[0]
            if len(record["full_bits"]) != 46:
                raise AssertionError("Incomplete returned QUBO state")
            record["optimum_hit"] = bool(
                record["feasible"]
                and abs(record["raw_objective"] - SCIP_REFERENCE) <= 1e-7
            )
            all_samples.append(record)
    if len(all_samples) != EXPECTED_READS:
        raise AssertionError("Wrong number of frozen child-seeded SA samples")
    feasible = sum(bool(row["feasible"]) for row in all_samples)
    hits = sum(bool(row["optimum_hit"]) for row in all_samples)
    bitstrings = [
        {"parent_seed": int(s["seed"]), "read_index": int(s["read_index"]),
         "child_seed": int(s["sample_seed"]), "full_bits": s["full_bits"]}
        for s in all_samples
    ]
    return {
        "schema_version": 1,
        "design": "issue58_frozen_historical_B_qubo_crosshost_classical_sa",
        "replica": replica,
        "frozen_fixture_file_sha256": FROZEN_SHA256,
        "frozen_qubo_canonical_sha256": FROZEN_QUBO_SHA256,
        "source_archived_B_sha256": ARCHIVED_SOURCE_B_SHA256,
        "environment": restricted_environment(),
        "n_samples": len(all_samples),
        "feasible_count": feasible,
        "optimum_hit_count": hits,
        "ordered_full_state_sha256": hashlib.sha256(canonical_bytes(bitstrings)).hexdigest(),
        "full_samples_sha256": hashlib.sha256(canonical_bytes(all_samples)).hexdigest(),
        "full_samples": all_samples,
        "interpretation": (
            "Classical OpenJij 0.12.2 on a frozen exact B-mode QUBO: "
            "observed process sample, not universal deterministic guarantee"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replica", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run_replay(args.replica)
    if args.output.exists():
        raise FileExistsError("Refusing to replace historical replay results")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(result))
    print("FROZEN_QUBO_OPENJIJ_REPLAY " + json.dumps({
        "replica": args.replica,
        "frozen_Q_sha256": result["frozen_qubo_canonical_sha256"],
        "state_sha256": result["ordered_full_state_sha256"],
        "feasible": result["feasible_count"],
        "optimum_hits": result["optimum_hit_count"],
        "total_reads": result["n_samples"],
        "cpu": result["environment"]["cpu_model"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
