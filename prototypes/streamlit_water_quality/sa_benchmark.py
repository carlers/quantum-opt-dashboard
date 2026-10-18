"""Bounded seeded *classical* OpenJij SA benchmark vs certified N=20 SCIP.

Runs only the existing committed notebook-weight experiment; the explicit
auxiliary-slack QUBO is NOT claimed identical to historic JijModeling to_qubo.
Records every returned state including infeasible samples and multiplicities.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
from statistics import mean
from time import perf_counter

import numpy as np

from evidence import (
    BUDGET, GEOJSON, N_FREE, NOTEBOOK, PAPER_REPORTED_SCIP_ENERGY,
    canonical_bytes, enumerated_optimum,
)
from model import NOTEBOOK_WEIGHTS, load_data, make_instance, solve_scip
from qubo import energy as expanded_qubo_energy, make_qubo, safe_penalty


def notebook_row_sum_bound(instance) -> float:
    """Notebook Cell 6 single-flip coefficient bound; NOT a global guarantee."""
    rows = np.abs(instance.linear.astype(float)).copy()
    for i, j, v in instance.quadratic:
        rows[i] += abs(float(v))
        rows[j] += abs(float(v))
    return float(np.max(rows))


def benchmark_penalties(instance) -> dict[str, float]:
    lower = notebook_row_sum_bound(instance)
    upper = safe_penalty(instance)
    if not (0 < lower < upper):
        raise ValueError("Expected a positive notebook heuristic below the global bound")
    return {
        "notebook-local-row-sum": lower,
        "midpoint-exploratory": (lower + upper) / 2.0,
        "global-feasibility-bound": upper,
    }


def independent_augmented_energy(instance, qubo, bits: list[int]) -> float:
    """Evaluate the *unexpanded* squared expressions, independent of Q dict."""
    x = bits[:qubo.n_free]
    raw = sum(float(a) * x[i] for i, a in enumerate(instance.linear))
    raw += sum(float(q) * x[i] * x[j] for i, j, q in instance.quadratic)
    budget_pen = qubo.budget_penalty * (sum(x) - instance.budget) ** 2
    connection_pen = 0.0
    for i, (group, weights) in enumerate(zip(qubo.slack_variables, qubo.slack_weights)):
        slack = sum(int(bits[j]) * mag for j, mag in zip(group, weights))
        residual = int(instance.fixed_neighbors[i]) + sum(x[j] for j in instance.neighbors[i]) - x[i] - slack
        connection_pen += qubo.connectivity_penalty * residual * residual
    return float(raw + budget_pen + connection_pen)


def decode_records(response, qubo, instance, *, seed: int, penalty_name: str) -> list[dict]:
    """Respect response variable labels, frequencies, and QUBO-offset conventions.

    Dimod/OpenJij energies do NOT include our manually retained QUBO offset.
    Every full auxiliary state is preserved as a binary string for audit.
    """
    indices = [int(v) for v in response.indices]
    if len(indices) != qubo.n_variables or set(indices) != set(range(qubo.n_variables)):
        raise RuntimeError("Sampler did not return every original and auxiliary variable")
    record = response.record
    matrix = np.asarray(record.sample)
    frequencies = np.asarray(record.num_occurrences)
    reported = np.asarray(record.energy)
    if matrix.ndim != 2 or matrix.shape[1] != len(indices):
        raise RuntimeError("OpenJij sample columns and response.indices disagree")
    if len(frequencies) != len(reported) or len(frequencies) != len(matrix):
        raise RuntimeError("OpenJij sample/energy/multiplicity row counts differ")

    samples = []
    for row, (state, occ, qenergy) in enumerate(zip(matrix, frequencies, reported)):
        bits = [0] * qubo.n_variables
        for label, value in zip(indices, state):
            number = int(value)
            if number not in (0, 1) or number != float(value):
                raise ValueError("Expected QUBO binary values (not Ising spins)")
            bits[label] = number
        count = int(occ)
        if count < 1 or count != float(occ):
            raise ValueError("Occurrence counts must be positive integers")
        calculated = expanded_qubo_energy(qubo, bits)
        unexpanded = independent_augmented_energy(instance, qubo, bits)
        if not math.isclose(calculated, unexpanded, rel_tol=1e-9, abs_tol=1e-6):
            raise AssertionError("Expanded QUBO differs from independently evaluated squared penalties")
        if not math.isclose(calculated - qubo.offset, float(qenergy), rel_tol=1e-9, abs_tol=1e-6):
            raise AssertionError("Sampler returned QUBO energy disagrees with canonical Q and offset")

        x = bits[:qubo.n_free]
        selected = [i for i, v in enumerate(x) if v]
        isolated = [i for i in selected if not (
            instance.fixed_neighbors[i] or any(x[j] for j in instance.neighbors[i])
        )]
        raw = sum(float(a) * x[i] for i, a in enumerate(instance.linear))
        raw += sum(float(q) * x[i] * x[j] for i, j, q in instance.quadratic)
        budget_ok = len(selected) == instance.budget
        samples.append({
            "penalty": penalty_name, "seed": seed, "record_row": row,
            "occurrences": count, "full_bits": "".join(map(str, bits)),
            "selected_local_indices": json.dumps(selected, separators=(",", ":")),
            "selected_count": len(selected),
            "isolated_selected_count": len(isolated),
            "budget_ok": budget_ok, "connectivity_ok": len(isolated) == 0,
            "feasible": bool(budget_ok and not isolated),
            "raw_objective": float(raw), "qubo_augmented_energy": float(calculated),
            "qubo_energy_without_offset": float(qenergy),
        })
    return samples


def seed_summary(rows: list[dict], *, expected_reads: int, optimum: float) -> dict:
    """All counts weighted by sampler num_occurrences, not compressed row count."""
    total = sum(int(r["occurrences"]) for r in rows)
    if total != expected_reads:
        raise AssertionError(f"SA returned {total} samples instead of {expected_reads}")
    feasible_rows = [r for r in rows if r["feasible"]]
    count = sum(int(r["occurrences"]) for r in feasible_rows)
    best = min((r["raw_objective"] for r in feasible_rows), default=None)
    average = (sum(r["raw_objective"] * r["occurrences"] for r in feasible_rows) / count
               if count else None)
    if best is not None and best < optimum - 1e-6:
        raise AssertionError("Stochastic feasible objective appears to beat proven SCIP optimum")
    return {
        "sample_count": total,
        "distinct_record_rows": len(rows),
        "feasible_sample_count": count,
        "infeasible_sample_count": total - count,
        "feasible_fraction": count / total,
        "best_feasible_raw_objective": best,
        "mean_feasible_raw_objective": average,
        "best_feasible_gap_vs_scip": best - optimum if best is not None else None,
        "exact_optimum_hits": sum(r["occurrences"] for r in feasible_rows
                                  if abs(r["raw_objective"] - optimum) <= 1e-7),
    }


def run_benchmark(*, seeds: tuple[int, ...], reads: int, sweeps: int) -> tuple[dict, list[dict], list[dict]]:
    if not (1 <= len(seeds) <= 10 and len(set(seeds)) == len(seeds) and
            all(isinstance(s, int) and 0 <= s < 2**32 for s in seeds)):
        raise ValueError("Supply 1..10 distinct unsigned 32-bit seed values")
    if not (1 <= reads <= 128 and 10 <= sweeps <= 2000):
        raise ValueError("Bounded CI benchmark requires 1..128 reads and 10..2000 sweeps")

    import openjij as oj

    data = load_data(GEOJSON)
    instance, simulated = make_instance(data, NOTEBOOK_WEIGHTS, N_FREE, BUDGET)
    if simulated or len(instance.fixed_indices) != 15:
        raise AssertionError("Expected 15 real flagged existing stations")
    reference = enumerated_optimum(instance)
    solution, scip = solve_scip(instance, time_limit=120.)
    if not (scip["status"] == "optimal" and scip["feasible"]):
        raise RuntimeError("SCIP has not certified the deterministic comparator optimum")
    if abs(scip["energy"] - reference["minimum_energy"]) > 1e-7:
        raise AssertionError("SCIP and independent 15,504-subset enumeration disagree")
    chosen = np.flatnonzero(solution).tolist()
    if chosen not in reference["optimal_local_index_sets"]:
        raise AssertionError("SCIP selected a non-enumerated optimum")

    penalty_points = benchmark_penalties(instance)
    trial_rows = []
    sample_rows = []
    for penalty_name, penalty in penalty_points.items():
        qubo = make_qubo(instance, budget_penalty=penalty, connectivity_penalty=penalty)
        Q = qubo.as_index_qubo()
        # Binary slack bits and original decision bits must all be represented
        # in the sampler response, even if an exact zero diagonal was omitted.
        Q.update({(i, i): Q.get((i, i), 0.0) for i in range(qubo.n_variables)})
        for seed in seeds:
            start = perf_counter()
            response = oj.SASampler().sample_qubo(
                Q, num_reads=reads, num_sweeps=sweeps, seed=seed, sparse=True,
            )
            wall = perf_counter() - start
            decoded = decode_records(
                response, qubo, instance, seed=seed, penalty_name=penalty_name
            )
            result = seed_summary(decoded, expected_reads=reads, optimum=float(scip["energy"]))
            trial = {
                "penalty": penalty_name, "penalty_value": penalty, "seed": seed,
                "reads": reads, "sweeps": sweeps, "qubo_variables": qubo.n_variables,
                "qubo_nonzero_coefficients": len(qubo.coefficients),
                "qubo_offset": qubo.offset, "elapsed_wall_s": float(wall),
                **result,
            }
            trial_rows.append(trial)
            sample_rows.extend(decoded)
            print("N20_SA_TRIAL " + json.dumps(trial, sort_keys=True, allow_nan=False))

    aggregate = {}
    for name, penalty in penalty_points.items():
        trials = [r for r in trial_rows if r["penalty"] == name]
        all_count = sum(t["sample_count"] for t in trials)
        all_feasible = sum(t["feasible_sample_count"] for t in trials)
        observed_feasible = [s for s in sample_rows if s["penalty"] == name and s["feasible"]]
        best = min((s["raw_objective"] for s in observed_feasible), default=None)
        agg = {
            "penalty_value": penalty, "repeat_count": len(seeds),
            "total_samples": all_count, "feasible_samples": all_feasible,
            "feasible_fraction": all_feasible / all_count,
            "mean_per_seed_feasible_fraction": mean(t["feasible_fraction"] for t in trials),
            "best_feasible_raw_objective": best,
            "mean_feasible_raw_objective": (
                sum(s["raw_objective"] * s["occurrences"] for s in observed_feasible) /
                all_feasible if all_feasible else None
            ),
            "gap_to_proven_scip": best - scip["energy"] if best is not None else None,
            "exact_optimum_hits": sum(t["exact_optimum_hits"] for t in trials),
            "total_wall_s": sum(t["elapsed_wall_s"] for t in trials),
        }
        aggregate[name] = agg
        print("N20_SA_AGGREGATE " + json.dumps({"penalty": name, **agg}, sort_keys=True))

    source = {
        "dataset_sha256": hashlib.sha256(GEOJSON.read_bytes()).hexdigest(),
        "notebook_sha256": hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
        "free_master_feature_positions": instance.free_indices.tolist(),
        "fixed_master_feature_positions": instance.fixed_indices.tolist(),
    }
    output = {
        "schema_version": 1, "experiment": "water_quality_n20_classical_sa_benchmark",
        "scientific_warning": "Explicit slack QUBO is not the paper's historical JijModeling conversion; OpenJij SASampler is classical, stochastic, and not a quantum advantage test.",
        "scenario": "notebook", "N_free": N_FREE, "K_new": BUDGET,
        "seeds": list(seeds), "reads_per_seed": reads, "sweeps_per_read": sweeps,
        "penalty_definition": "same positive P for both squared budget and squared local-connectivity residuals",
        "notebook_local_row_sum_is_only_a_heuristic": True,
        "global_sufficient_penalty_if_feasible": safe_penalty(instance),
        "penalty_points": penalty_points,
        "scip": {"status": scip["status"], "proven_optimal": scip["optimal"],
                 "energy": scip["energy"], "selected_local_indices": chosen},
        "enumeration": reference, "sources": source, "aggregate": aggregate,
        "runtime": {"python": platform.python_version(), "OS": platform.platform(),
                    "numpy": np.__version__, "scipy": __import__("scipy").__version__,
                    "shapely": __import__("shapely").__version__,
                    "pyscipopt": __import__("pyscipopt").__version__,
                    "openjij": oj.__version__,
                    "git_commit": os.environ.get("GITHUB_HEAD_SHA") or os.environ.get("GITHUB_SHA")},
        "manuscript_comparison_is_not_input_parity": {"paper_n20_scip_energy": PAPER_REPORTED_SCIP_ENERGY},
    }
    return output, trial_rows, sample_rows


def write_bundle(output_dir: Path, *, seeds: tuple[int, ...], reads: int, sweeps: int) -> dict:
    """Machine readable statistics, every compressed sample row, SHA manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary, trials, samples = run_benchmark(seeds=seeds, reads=reads, sweeps=sweeps)
    paths = {}
    for filename, contents in [("summary.json", canonical_bytes(summary))]:
        file = output_dir / filename
        file.write_bytes(contents)
        paths[filename] = hashlib.sha256(contents).hexdigest()
    for filename, rows in [("trials.csv", trials), ("samples.csv", samples)]:
        file = output_dir / filename
        with file.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        paths[filename] = hashlib.sha256(file.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "file_sha256": paths,
        "meaning": "One row in samples.csv per OpenJij response record, weighted by occurrences",
    }
    (output_dir / "manifest.json").write_bytes(canonical_bytes(manifest))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seeds", default="20261018,20261019,20261020")
    parser.add_argument("--reads", type=int, default=32)
    parser.add_argument("--sweeps", type=int, default=300)
    args = parser.parse_args()
    seeds = tuple(int(x) for x in args.seeds.split(","))
    write_bundle(args.output_dir, seeds=seeds, reads=args.reads, sweeps=args.sweeps)


if __name__ == "__main__":
    main()
