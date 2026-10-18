"""Controlled four-arm, paired-seed ULP sensitivity replay of archived SCIP inputs.

See issue #26. This is a retrospective controlled *replay* of preexisting
seeds, not a fresh preregistered Monte Carlo sample or historical paper
reproduction. All archived A/B changes are frozen before inspecting outputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from importlib.metadata import version as package_version
from itertools import combinations
from pathlib import Path
import platform

import numpy as np

from evidence import canonical_bytes
from model import Instance
from qubo import make_qubo
from sa_benchmark import decode_records, notebook_row_sum_bound
from sa_paired_replication import PARENT_SEEDS, READS_PER_PARENT, SWEEPS

# Original exact source SHA-256 hashes of the notebook/instance.json content,
# recovered from archived GitHub Actions SCIP evidence, *not* from new runs.
SOURCE_ARCHIVE_SHA = {
    "A": "22c6bdfce2df49c47263341e0a4fa6f1ab8e8dba60cd552a1e9a8b0b7ac60822",
    "B": "0718156034e83d46223fa3e4e086bc9997c16f7252e3c348ca8ac70cf19d5532",
}
B_LINEAR = (
    -0.6521506468697543, -0.7787324333193801, -0.6913654952575794,
    -0.6252770020057188, -0.6747138282298528, -0.697526425333438,
    -0.6799627668825393, -0.654750015044013, -0.6811293255576854,
    -0.1869955107174101, -0.04162833783001657, -0.6782343722300318,
    -0.3428584661450556, 0.6995053988383269, -0.3635730008569015,
    -0.15789400583666008, -0.6872738125202991, 0.7891748701592056,
    -0.7042270333694934, 0.004568708971249169,
)
A_LINEAR_OVERRIDES_HEX = {
    9: "-0x1.7ef780983da1ap-3", 10: "-0x1.5504f3b222e88p-5",
    17: "0x1.940eba845152ep-1", 19: "0x1.2b6a379dd0180p-8",
}
B_LINEAR_REFERENCE_HEX = {
    9: "-0x1.7ef780983da1ep-3", 10: "-0x1.5504f3b222e78p-5",
    17: "0x1.940eba845152cp-1", 19: "0x1.2b6a379dd0200p-8",
}
B_QUADRATIC = (
    (0, 7, 0.08957937226494117), (0, 14, 0.31627763002306475),
    (1, 9, 0.16081160925214388), (1, 13, 0.0002699584704684191),
    (3, 9, 0.21012032173405853), (6, 17, 0.00020932561815228956),
    (6, 19, 2.5779420797209138e-06), (7, 14, 0.0002838380939718353),
    (10, 15, 2.0468976986411935e-05), (10, 17, 1.0195113296079744e-05),
    (13, 17, 0.05702598126989811), (17, 19, 0.25139929546648077),
)
FREE_NEIGHBORS = (
    (7, 14), (9, 13), (), (9,), (), (), (17,), (0, 14), (),
    (1, 3), (12, 19), (), (10,), (1, 17), (0, 7), (),
    (), (6, 13, 19), (), (10, 17),
)
FIXED_NEIGHBORS = (1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1)
FREE_MASTER = (5253, 2394, 1894, 1557, 3225, 4623, 47, 5409, 3922, 2408,
               2694, 4136, 2567, 1164, 4973, 4537, 2726, 968, 16, 1762)
FIXED_MASTER = (417, 454, 725, 1055, 1076, 1709, 2771, 3402, 3520,
                3529, 3732, 3886, 4613, 4868, 5038)
PENALTY_HEX = {
    "A": "0x1.190ab5b15d1b4p+0", "B": "0x1.190ab5b15d1b3p+0"
}
ARMS = (
    ("B-linear_B-penalty", "B", "B"),
    ("A-linear_B-penalty", "A", "B"),
    ("B-linear_A-penalty", "B", "A"),
    ("A-linear_A-penalty", "A", "A"),
)
SCIP_REFERENCE = -3.3012934918564643


def fixture_instance(variant: str) -> Instance:
    """Use immutable archived numeric inputs, never re-run floating geometry."""
    if variant not in ("A", "B"):
        raise ValueError("Unknown archived source mode")
    linear = list(B_LINEAR)
    if variant == "A":
        for i, value in A_LINEAR_OVERRIDES_HEX.items():
            linear[i] = float.fromhex(value)
    if any(float(B_LINEAR[i]).hex() != hexval
           for i, hexval in B_LINEAR_REFERENCE_HEX.items()):
        raise AssertionError("Archived B reference coefficient bits changed")
    return Instance(
        coords=np.zeros((35, 2), dtype=float),  # Not used by encoded objective.
        free_indices=np.asarray(FREE_MASTER), fixed_indices=np.asarray(FIXED_MASTER),
        utility=np.zeros(35, dtype=float), linear=np.asarray(linear, dtype=float),
        quadratic=B_QUADRATIC, neighbors=FREE_NEIGHBORS,
        fixed_neighbors=np.asarray(FIXED_NEIGHBORS, dtype=int),
        budget=5, d_max=9873.27073466548,
    )


def _direct_energy(inst: Instance, chosen: tuple[int, ...]) -> float:
    x = set(chosen)
    return float(
        sum(float(inst.linear[i]) for i in chosen)
        + sum(float(q) for i, j, q in inst.quadratic if i in x and j in x)
    )


def verify_archived_reference(inst: Instance) -> dict:
    """Independent exhaustive N20/K5 exact objective and adjacency checks."""
    best = float("inf")
    argmins = []
    feasible = 0
    for subset in combinations(range(20), 5):
        chosen = set(subset)
        if any(not (int(inst.fixed_neighbors[i]) or
                    any(j in chosen for j in inst.neighbors[i])) for i in chosen):
            continue
        feasible += 1
        e = _direct_energy(inst, subset)
        if e < best - 1e-9:
            best, argmins = e, [list(subset)]
        elif abs(e - best) <= 1e-9:
            argmins.append(list(subset))
    if feasible != 1077 or argmins != [[0, 1, 3, 6, 7]]:
        raise AssertionError("Archived frozen N20 feasibility/optimum changed")
    if abs(best - SCIP_REFERENCE) > 1e-7:
        raise AssertionError("Archived SCIP certified objective differs from fixture")
    return {"enumerated_subsets": 15504, "feasible_subsets": feasible,
            "optimal_local_indices": [0, 1, 3, 6, 7], "energy": best}


def bits_digest(qubo) -> str:
    q = {
        "offset": qubo.offset.hex(),
        "budget_penalty": qubo.budget_penalty.hex(),
        "connectivity_penalty": qubo.connectivity_penalty.hex(),
        "terms": [[i, j, float(v).hex()]
                  for (i, j), v in sorted(qubo.coefficients.items())],
        "n_variables": qubo.n_variables,
        "slack_indices": [list(x) for x in qubo.slack_variables],
        "slack_weights": [list(x) for x in qubo.slack_weights],
    }
    return hashlib.sha256(canonical_bytes(q)).hexdigest()


def build_arms() -> list[tuple[str, Instance, object, dict]]:
    result = []
    for name, linear_mode, penalty_mode in ARMS:
        instance = fixture_instance(linear_mode)
        ref = verify_archived_reference(instance)
        penalty = float.fromhex(PENALTY_HEX[penalty_mode])
        expected = notebook_row_sum_bound(instance)
        if expected.hex() != PENALTY_HEX[linear_mode]:
            raise AssertionError("Original archived row-sum penalty not exactly reconstructed")
        q = make_qubo(instance, budget_penalty=penalty, connectivity_penalty=penalty)
        if q.n_variables != 46:
            raise AssertionError("Unexpected QUBO encoding size")
        result.append((name, instance, q, {
            "name": name, "linear_source": linear_mode, "penalty_source": penalty_mode,
            "penalty_hex": penalty.hex(),
            "qubo_sha256": bits_digest(q),
            "archive_source_instance_sha256": SOURCE_ARCHIVE_SHA[linear_mode],
            "independent_reference": ref,
        }))
    return result


def run_experiment() -> tuple[dict, list[dict], list[dict]]:
    import openjij as oj
    if package_version("openjij") != "0.12.2":
        raise RuntimeError("OpenJij version mismatch")
    result, sample_rows, trial_rows = {}, [], []
    for name, instance, qubo, cfg in build_arms():
        matrix = qubo.as_index_qubo()
        matrix.update({(i, i): matrix.get((i, i), 0.0)
                       for i in range(qubo.n_variables)})
        total_feasible = total_optimal = 0
        for parent in PARENT_SEEDS:
            seeds = [
                int(child.generate_state(1, dtype=np.uint32)[0])
                for child in np.random.SeedSequence(parent).spawn(READS_PER_PARENT)
            ]
            if len(set(seeds)) != READS_PER_PARENT:
                raise AssertionError("Child random seed collision")
            sampler = oj.SASampler()
            feasible = hits = 0
            for read_index, child_seed in enumerate(seeds):
                response = sampler.sample_qubo(
                    matrix, num_reads=1, num_sweeps=SWEEPS,
                    seed=child_seed, sparse=True,
                )
                from sa_benchmark import decode_records
                records = decode_records(
                    response, qubo, instance, seed=parent,
                    penalty_name=name, sample_seed=child_seed,
                    read_index=read_index,
                )
                if len(records) != 1 or records[0]["occurrences"] != 1:
                    raise AssertionError("Each independently seeded read must yield one sample")
                rec = records[0]
                if rec["feasible"]:
                    feasible += 1
                    if abs(rec["raw_objective"] - SCIP_REFERENCE) <= 1e-7:
                        hits += 1
                sample_rows.append(rec)
            total_feasible += feasible
            total_optimal += hits
            trial_rows.append({"arm": name, "parent_seed": parent,
                               "reads": READS_PER_PARENT,
                               "feasible": feasible, "optimum_hits": hits})
        result[name] = {
            **cfg, "total_reads": len(PARENT_SEEDS) * READS_PER_PARENT,
            "feasible": total_feasible, "optimum_hits": total_optimal,
            "feasibility_percent": 100 * total_feasible / (len(PARENT_SEEDS)*READS_PER_PARENT),
        }
        print("N20_ULP_REPLAY " + json.dumps(result[name], sort_keys=True, allow_nan=False))
    base = result[ARMS[0][0]]["feasible"]
    result["comparisons_vs_BB"] = {
        name: {
            "delta_feasible_count": result[name]["feasible"] - base,
            "delta_feasible_percentage_points": (
                result[name]["feasibility_percent"] -
                result[ARMS[0][0]]["feasibility_percent"]
            ),
        } for name, _, _ in ARMS[1:]
    }
    summary = {
        "schema_version": 1,
        "scientific_warning": "Retrospective paired-seed perturbation experiment, not a new independent preregistered SA replication",
        "source_archive_A": SOURCE_ARCHIVE_SHA["A"],
        "source_archive_B": SOURCE_ARCHIVE_SHA["B"],
        "source_scientific_scenario": "notebook-weight N20 K5 Laguna de Bay",
        "seed_parent_list": list(PARENT_SEEDS), "reads_per_parent": READS_PER_PARENT,
        "sweeps_per_read": SWEEPS, "sampler": "classical openjij 0.12.2 SASampler",
        "baseline_Scip_optimum": SCIP_REFERENCE,
        "runtime": {"python": platform.python_version(),
                    "numpy": np.__version__, "openjij": package_version("openjij"),
                    "cpu": platform.processor()},
        "arms": result,
    }
    return summary, trial_rows, sample_rows


def write_bundle(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary, trials, samples = run_experiment()
    assert len(trials) == 4 * len(PARENT_SEEDS)
    assert len(samples) == 4 * len(PARENT_SEEDS) * READS_PER_PARENT == 4096
    hashes = {}
    path = output_dir / "summary.json"
    path.write_bytes(canonical_bytes(summary))
    hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name, rows in (("trials.csv", trials), ("samples.csv", samples)):
        path = output_dir / name
        with path.open("w", newline="", encoding="utf-8") as handle:
            w = csv.DictWriter(handle, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output_dir / "manifest.json").write_bytes(canonical_bytes(
        {"schema_version": 1, "archive_shas": SOURCE_ARCHIVE_SHA,
         "file_sha256": hashes, "total_read_rows": len(samples)}
    ))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    write_bundle(args.output_dir)


if __name__ == "__main__":
    main()
