"""Bounded source-pinned N20 two-axis classical SA penalty-grid research smoke.

The independent budget and local-one-hop penalties are lambda_b and lambda_c.
Uses the explicit auxiliary-slack QUBO already reviewed in the water pilot,
NOT an asserted reproduction of JijModeling/OMMX internal to_qubo encoding.
The grid is deliberately exploratory: no adaptive winner claim, QAOA, SQA,
quantum hardware, statistical scaling or manuscript parity.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import json
import math
import os
from pathlib import Path
import platform
from time import perf_counter

import numpy as np

from problems.water_quality.nested_resolution import (
    REFERENCE_GEOJSON, build_nested_instances,
)
from prototypes.streamlit_water_quality.qubo import (
    make_qubo, safe_penalty, best_slack_assignment,
    decoded_penalty_energy, energy as expanded_energy,
)

SOURCE_SHA256 = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
FROZEN_N20_OPTIMUM = -3.3012934918564643
SCHEMA = "two-independent-penalty-N20-classical-SA-smoke-v1"
PARENT_SEEDS = (270010001, 270010002)
LEVEL_NAMES = ("notebook_single_flip_heuristic", "exploratory_midpoint", "global_feasibility_sufficient")
MAX_READS_PER_CELL_PARENT = 32
MAX_PARENT_BLOCKS = 8
MAX_SWEEPS = 500


def canonical(x):
    return (json.dumps(x, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def _require(condition, message):
    if not condition:
        raise ValueError("N20 independent-penalty research gate: " + message)


def notebook_single_flip_bound(instance) -> float:
    """Cell 6 row-absolute-sum heuristic; never imply a global guarantee."""
    scores = np.abs(np.asarray(instance.linear, dtype=float)).copy()
    for i, j, q in instance.quadratic:
        scores[i] += abs(float(q))
        scores[j] += abs(float(q))
    return float(np.max(scores))


def penalty_levels(instance) -> tuple[tuple[str, float], ...]:
    lower = notebook_single_flip_bound(instance)
    upper = safe_penalty(instance)
    _require(0 < lower < upper, "expected row-sum heuristic below sufficient global bound")
    middle = (lower + upper) / 2
    return tuple(zip(LEVEL_NAMES, (lower, middle, upper)))


def grid(instance) -> tuple[dict, ...]:
    """Predeclared 3 by 3 separate-budget/separate-connectivity points."""
    levels = penalty_levels(instance)
    return tuple({
        "grid_index": i * 3 + j,
        "lambda_budget_label": label_b, "lambda_budget": value_b,
        "lambda_connectivity_label": label_c, "lambda_connectivity": value_c,
    } for i, (label_b, value_b) in enumerate(levels)
      for j, (label_c, value_c) in enumerate(levels))


def child_seeds(parent: int, index: int, reads: int) -> list[int]:
    """A parent block has separately generated one-read streams per cell."""
    _require(type(parent) is int and 0 <= parent < 2**32, "invalid parent seed")
    _require(type(index) is int and 0 <= index < 9, "invalid grid coordinate")
    _require(type(reads) is int and 1 <= reads <= MAX_READS_PER_CELL_PARENT,
             "invalid reads per cell")
    children = np.random.SeedSequence([parent, index]).spawn(reads)
    derived = [int(c.generate_state(1, dtype=np.uint32)[0]) for c in children]
    _require(len(set(derived)) == reads, "child-seed collision in one parent/cell")
    return derived


def model_record(instance) -> dict:
    n = len(instance.free_indices)
    return {
        "N_free": n, "K": instance.budget,
        "free_master_feature_positions": [int(v) for v in instance.free_indices],
        "fixed_master_feature_positions": [int(v) for v in instance.fixed_indices],
        "source": SOURCE_SHA256,
        "linear_hex": [float(v).hex() for v in instance.linear],
        "quadratic_hex": [[int(i), int(j), float(q).hex()]
                          for i, j, q in instance.quadratic],
        "fixed_neighbors": [int(v) for v in instance.fixed_neighbors],
        "free_neighbors": [list(map(int, row)) for row in instance.neighbors],
    }


def qubo_digest(qubo) -> str:
    """Keep all float64 coefficients/offset/slack identities in the digest."""
    return sha256(canonical({
        "N_variables": qubo.n_variables,
        "N_free": qubo.n_free,
        "offset_hex": float(qubo.offset).hex(),
        "lambda_budget_hex": float(qubo.budget_penalty).hex(),
        "lambda_connectivity_hex": float(qubo.connectivity_penalty).hex(),
        "coefficients_hex": [
            [int(i), int(j), float(q).hex()]
            for (i, j), q in sorted(qubo.coefficients.items())
        ],
        "slack_indices": [list(s) for s in qubo.slack_variables],
        "slack_weights": [list(w) for w in qubo.slack_weights],
    })).hexdigest()


def inspect_one_read(response, qubo, instance, *, parent_seed: int,
                     child_seed: int, grid_index: int, read_index: int):
    """Independent source/penalty energy check incl. response labels and offset."""
    labels = [int(x) for x in response.indices]
    _require(len(labels) == qubo.n_variables
             and set(labels) == set(range(qubo.n_variables)),
             "sampler returned missing or unexpected auxiliary variables")
    samples = np.asarray(response.record.sample)
    counts = np.asarray(response.record.num_occurrences)
    reported = np.asarray(response.record.energy)
    _require(samples.ndim == 2 and samples.shape[1] == qubo.n_variables
             and len(samples) == len(counts) == len(reported),
             "sampler response shape or energy count changed")
    _require(len(samples) == 1 and len(counts) == 1 and counts[0] == 1,
             "each independent one-read call must yield exactly one state")
    bits = [0] * qubo.n_variables
    for label, value in zip(labels, samples[0]):
        _require(float(value) in (0.0, 1.0),
                 "sampler returned nonbinary state (possible Ising-spin confusion)")
        bits[label] = int(value)
    augmented = expanded_energy(qubo, bits)
    _require(math.isclose(augmented - qubo.offset, float(reported[0]),
                         abs_tol=1e-6, rel_tol=1e-9),
             "OpenJij energy or coefficient offset changed")
    x = bits[:qubo.n_free]
    selected = [i for i, v in enumerate(x) if v]
    isolated = [i for i in selected if not (
        int(instance.fixed_neighbors[i])
        or any(x[j] for j in instance.neighbors[i])
    )]
    raw = sum(float(v) * x[i] for i, v in enumerate(instance.linear))
    raw += sum(float(q) * x[i] * x[j] for i, j, q in instance.quadratic)
    residual_squares = []
    for i, (indices, magnitudes) in enumerate(zip(
        qubo.slack_variables, qubo.slack_weights
    )):
        s = sum(bits[index] * mag for index, mag in zip(indices, magnitudes))
        residual = (int(instance.fixed_neighbors[i])
                    + sum(x[j] for j in instance.neighbors[i]) - x[i] - s)
        residual_squares.append(int(residual * residual))
    budget_cost = qubo.budget_penalty * (len(selected) - instance.budget) ** 2
    connection_cost = qubo.connectivity_penalty * sum(residual_squares)
    direct = raw + budget_cost + connection_cost
    _require(math.isclose(direct, augmented, abs_tol=1e-6, rel_tol=1e-9),
             "expanded QUBO differs from unexpanded original plus squared slack penalties")
    optimally_slacked = decoded_penalty_energy(instance, qubo, x)
    canonical_slack = expanded_energy(qubo, best_slack_assignment(instance, qubo, x))
    _require(math.isclose(optimally_slacked, canonical_slack, abs_tol=1e-6, rel_tol=1e-9),
             "binary slack encoding fails minimized-auxiliary comparison")
    _require(augmented + 1e-6 >= optimally_slacked,
             "sampled auxiliary bits beat optimal same-x slack assignment")
    feasible = (len(selected) == instance.budget and not isolated)
    if feasible:
        _require(raw >= FROZEN_N20_OPTIMUM - 1e-7,
                 "feasible source solution beats independently proven N20 optimum")
    return {
        "parent_seed": parent_seed, "grid_index": grid_index,
        "read_index": read_index, "child_seed": child_seed,
        "selected_source_feature_positions": json.dumps(
            [int(instance.free_indices[i]) for i in selected], separators=(",", ":")
        ),
        "original_decisions": "".join(map(str, x)),
        "full_slack_quo_bits": "".join(map(str, bits)),
        "selected_count": len(selected), "budget_residual": len(selected) - instance.budget,
        "isolated_selected_count": len(isolated),
        "original_feasible": bool(feasible),
        "original_raw_objective": float(raw),
        "qubo_energy_full": float(augmented),
        "qubo_energy_without_offset": float(reported[0]),
        "min_slack_energy_same_original_x": float(optimally_slacked),
        "sampled_slack_excess_energy": float(max(0., augmented - optimally_slacked)),
        "budget_penalty_component": float(budget_cost),
        "connectivity_penalty_component": float(connection_cost),
    }


def _version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def run_grid(*, parents: tuple[int, ...] = PARENT_SEEDS, reads: int = 4,
             sweeps: int = 40) -> tuple[dict, list[dict], list[dict]]:
    """One bounded exploratory protocol; 9 cells x parent blocks x child reads."""
    _require(1 <= len(parents) <= MAX_PARENT_BLOCKS
             and len(set(parents)) == len(parents)
             and all(type(x) is int and 0 <= x < 2**32 for x in parents),
             "invalid distinct parent blocks")
    _require(type(reads) is int and 1 <= reads <= MAX_READS_PER_CELL_PARENT,
             "invalid total per-parent cell read budget")
    _require(type(sweeps) is int and 10 <= sweeps <= MAX_SWEEPS,
             "invalid number of classical SA sweeps")
    import openjij as oj
    study = build_nested_instances(tiers=(20,))
    if (study.source_sha256 != SOURCE_SHA256 or study.fixed_simulated
            or len(study.fixed_master_positions) != 15):
        raise AssertionError("N20 pinned historical source/fixed stations changed")
    instance = study.tier_instances[0].instance
    if instance.budget != 5:
        raise AssertionError("N20 exact budget changed")
    checksum = sha256(canonical(model_record(instance))).hexdigest()
    points = grid(instance)
    samples = []
    trials = []
    used_children = set()
    for point in points:
        qubo = make_qubo(
            instance, budget_penalty=point["lambda_budget"],
            connectivity_penalty=point["lambda_connectivity"],
        )
        qhash = qubo_digest(qubo)
        indexed_qubo = qubo.as_index_qubo()
        # Ensure the sampler returns all auxiliary columns even when Q_ii=0.
        indexed_qubo.update({
            (i, i): indexed_qubo.get((i, i), 0.0)
            for i in range(qubo.n_variables)
        })
        for parent in parents:
            children = child_seeds(parent, point["grid_index"], reads)
            if set(children) & used_children:
                raise RuntimeError("Read-level seed collision across the 2D grid")
            used_children.update(children)
            sampler = oj.SASampler()
            rows = []
            start = perf_counter()
            for read_index, child in enumerate(children):
                response = sampler.sample_qubo(
                    indexed_qubo, num_reads=1, num_sweeps=sweeps,
                    seed=child, sparse=True,
                )
                obs = inspect_one_read(
                    response, qubo, instance, parent_seed=parent,
                    child_seed=child, grid_index=point["grid_index"],
                    read_index=read_index,
                )
                obs.update({
                    "lambda_budget": point["lambda_budget"],
                    "lambda_connectivity": point["lambda_connectivity"],
                    "qubo_coefficient_sha256": qhash,
                })
                rows.append(obs)
            seconds = perf_counter() - start
            _require(len(rows) == reads, "missing independently sampled child read")
            feasible = [row for row in rows if row["original_feasible"]]
            trials.append({
                **point,
                "parent_seed": parent,
                "reads": reads, "sweeps": sweeps,
                "qubo_variables": qubo.n_variables,
                "qubo_nonzero_terms": len(qubo.coefficients),
                "qubo_coefficient_sha256": qhash,
                "sampler_wall_seconds": seconds,
                "feasible_reads": len(feasible),
                "infeasible_reads": reads - len(feasible),
                "feasible_fraction": len(feasible) / reads,
                "best_feasible_original_raw": (
                    min(row["original_raw_objective"] for row in feasible)
                    if feasible else None
                ),
                "scip_optimum_hits": sum(
                    abs(row["original_raw_objective"] - FROZEN_N20_OPTIMUM) <= 1e-7
                    for row in feasible
                ),
                "no_inference_from_ci_smoke": True,
            })
            samples.extend(rows)
    _require(len(samples) == len(points) * len(parents) * reads,
             "grid is incomplete")
    summary = {
        "schema": SCHEMA, "source_sha256": study.source_sha256,
        "N_free": 20, "K": 5, "fixed_station_count": 15,
        "original_model_sha256": checksum,
        "original_N20_proven_scip_optimum": FROZEN_N20_OPTIMUM,
        "source_model": "historical notebook weights, road D2 and local one-hop",
        "algorithm": "classical OpenJij SASampler one independent child-seeded read per call",
        "qubo_encoding": "explicit nonnegative binary slack squares (not manuscript JijModeling QUBO parity)",
        "grid_shape": [3, 3], "grid_points": list(points),
        "levels": [{"name": n, "value": v} for n, v in penalty_levels(instance)],
        "independent_axes": ["lambda_budget", "lambda_connectivity"],
        "parent_seeds": list(parents), "reads_per_parent_per_cell": reads,
        "sweeps_per_read": sweeps,
        "sampling_seed_protocol": "numpy SeedSequence([parent_seed, grid_index]).spawn(reads), one OpenJij call each",
        "sampled_source_states": len(samples),
        "parent_cell_trials": len(trials),
        "predeclared_exploratory_CI_smoke_not_preregistered_population_study": True,
        "inference_or_optimal_penalty_grid_claimed": False,
        "nonquantum_classical_only": True,
        "manuscript_input_or_QUBO_equivalence_claimed": False,
        "software": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "openjij": _version("openjij"),
            "scipy": _version("scipy"),
            "shapely": _version("shapely"),
            "github_sha": os.environ.get("GITHUB_SHA"),
        },
    }
    return summary, trials, samples


def write_bundle(out: Path, *, parents: tuple[int, ...] = PARENT_SEEDS,
                 reads: int = 4, sweeps: int = 40) -> dict:
    summary, trials, samples = run_grid(parents=parents, reads=reads, sweeps=sweeps)
    out.mkdir(parents=True, exist_ok=True)
    files = {"summary.json": canonical(summary)}
    for name, rows in (("trials.csv", trials), ("samples.csv", samples)):
        memory = __import__("io").StringIO()
        writer = csv.DictWriter(memory, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        files[name] = memory.getvalue().encode("utf-8")
    digests = {name: sha256(content).hexdigest() for name, content in files.items()}
    files["SHA256SUMS.json"] = canonical({
        "schema": SCHEMA,
        "source_sha256": SOURCE_SHA256,
        "file_sha256": digests,
        "not_an_independent_publication_study": True,
    })
    for name, raw in files.items():
        (out / name).write_bytes(raw)
    return {"summary": summary, "files_sha256": digests}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--parents", default=",".join(map(str, PARENT_SEEDS)))
    parser.add_argument("--reads", type=int, default=4)
    parser.add_argument("--sweeps", type=int, default=40)
    args = parser.parse_args()
    parents = tuple(int(x) for x in args.parents.split(","))
    receipt = write_bundle(args.out, parents=parents,
                           reads=args.reads, sweeps=args.sweeps)
    print(json.dumps({
        "model_sha256": receipt["summary"]["original_model_sha256"],
        "sampled_source_states": receipt["summary"]["sampled_source_states"],
        "grid_shape": receipt["summary"]["grid_shape"],
        "output_directory": str(args.out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
