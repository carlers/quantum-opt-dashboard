"""Offline-only M2 3x3 feasibility counts, from verified classical OpenJij samples.

No scorer/optimizer in Streamlit; no posthoc winning penalty claim. The exact
original+auxiliary bits, child-seed accounting, source-QUBO coefficient digest,
and all 72 expanded/unexpanded energy checks are reconstructed from archive.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
import math
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile, is_zipfile

import numpy as np

from problems.water_quality.nested_resolution import build_nested_instances
from problems.water_quality.independent_penalty_grid import (
    SCHEMA, SOURCE_SHA256, FROZEN_N20_OPTIMUM, canonical, child_seeds,
    grid, inspect_one_read, model_record, qubo_digest, frozen_source_instance,
)
from prototypes.streamlit_water_quality.qubo import make_qubo

FIELDS = (
    "grid_index", "lambda_budget_label", "lambda_budget",
    "lambda_connectivity_label", "lambda_connectivity",
    "observed_feasible_count", "total_draws", "observed_feasible_fraction",
    "observed_exact_N20_optimum_hits", "descriptive_only",
)


def fail(message):
    raise ValueError("M2 artifact-gated descriptive grid: " + message)


def _read_csv(raw):
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))


def inspect_archive(raw: bytes):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= 3_000_000:
        fail("research evidence is missing or exceeds review size bound")
    if not is_zipfile(io.BytesIO(raw)):
        fail("not a valid source research ZIP")
    with ZipFile(io.BytesIO(raw)) as archive:
        expected = {"summary.json", "trials.csv", "samples.csv", "compiled_source_model.json", "SHA256SUMS.json"}
        if set(archive.namelist()) != expected or len(archive.namelist()) != 5:
            fail("unexpected/incomplete source research evidence files")
        checksums = json.loads(archive.read("SHA256SUMS.json"))
        if checksums.get("schema") != SCHEMA or checksums.get("source_sha256") != SOURCE_SHA256:
            fail("changed checksum/source schema")
        computed = {name: sha256(archive.read(name)).hexdigest()
                    for name in expected - {"SHA256SUMS.json"}}
        if computed != checksums.get("file_sha256"):
            fail("original source samples and trials checksum mismatch")
        compiled = json.loads(archive.read("compiled_source_model.json"))
        summary = json.loads(archive.read("summary.json"))
        trials = _read_csv(archive.read("trials.csv"))
        samples = _read_csv(archive.read("samples.csv"))

    if (summary.get("schema") != SCHEMA
            or summary.get("source_sha256") != SOURCE_SHA256
            or summary.get("algorithm") != "classical OpenJij SASampler one independent child-seeded read per call"
            or summary.get("grid_shape") != [3, 3]
            or summary.get("nonquantum_classical_only") is not True
            or summary.get("inference_or_optimal_penalty_grid_claimed") is not False
            or summary.get("manuscript_input_or_QUBO_equivalence_claimed") is not False):
        fail("unsupported classical, source, QUBO or inference claim")
    parents = summary["parent_seeds"]
    reads = summary["reads_per_parent_per_cell"]
    if (not isinstance(parents, list) or not (1 <= len(parents) <= 8)
            or len(set(parents)) != len(parents) or type(reads) is not int
            or not 1 <= reads <= 32):
        fail("incorrect parent-seed block design")
    number = 9 * len(parents) * reads
    if (len(samples) != number
            or len(trials) != 9 * len(parents)
            or summary["sampled_source_states"] != number):
        fail("dropped or duplicated source samples")
    study, instance = frozen_source_instance()
    if study.source_sha256 != SOURCE_SHA256 or len(study.fixed_master_positions) != 15:
        fail("historical lake source identity differs")
    recomputed = model_record(instance)
    if (compiled != recomputed
            or sha256(canonical(compiled)).hexdigest() != summary["original_model_sha256"]
            or summary.get("numerical_profile_sha256") != summary["original_model_sha256"]):
        fail("archived IEEE-754 source model differs from the current source or its digest")
    points = grid(instance)
    if summary["grid_points"] != list(points):
        fail("grid point geometry/penalty levels did not reproduce")

    cells = {(g, p): [] for g in range(9) for p in parents}
    expected_seeds = {}
    for point in points:
        for parent in parents:
            for j, seed in enumerate(child_seeds(parent, point["grid_index"], reads)):
                expected_seeds[(point["grid_index"], parent, j)] = seed
    if len(set(expected_seeds.values())) != number:
        fail("derived unique seed streams unexpectedly collide")

    qubos = {}
    for point in points:
        q = make_qubo(
            instance,
            budget_penalty=point["lambda_budget"],
            connectivity_penalty=point["lambda_connectivity"],
        )
        qubos[point["grid_index"]] = (q, qubo_digest(q))

    observed_keys = set()
    for record in samples:
        try:
            g, parent, index, seed = (
                int(record["grid_index"]), int(record["parent_seed"]),
                int(record["read_index"]), int(record["child_seed"])
            )
            point = points[g]
            q, digest = qubos[g]
            key = (g, parent, index)
            if (key not in expected_seeds or key in observed_keys
                    or expected_seeds[key] != seed
                    or record["qubo_coefficient_sha256"] != digest
                    or not math.isclose(float(record["lambda_budget"]), point["lambda_budget"], abs_tol=1e-9)
                    or not math.isclose(float(record["lambda_connectivity"]), point["lambda_connectivity"], abs_tol=1e-9)):
                fail("duplicated or forged child-seeded QUBO sample")
            bits = record["full_slack_quo_bits"]
            if len(bits) != q.n_variables or any(b not in "01" for b in bits):
                fail("malformed original/auxiliary bitstring")
            state = np.asarray([int(v) for v in bits], dtype=np.int64)
            response = SimpleNamespace(
                indices=list(range(q.n_variables)),
                record=SimpleNamespace(
                    sample=state.reshape(1, -1),
                    num_occurrences=np.asarray([1]),
                    energy=np.asarray([float(record["qubo_energy_without_offset"])]),
                ),
            )
            verified = inspect_one_read(
                response, q, instance, parent_seed=parent,
                child_seed=seed, grid_index=g, read_index=index
            )
            for field in (
                "original_raw_objective", "qubo_energy_full",
                "min_slack_energy_same_original_x", "sampled_slack_excess_energy",
                "budget_penalty_component", "connectivity_penalty_component",
            ):
                if not math.isclose(
                    float(record[field]), float(verified[field]), rel_tol=1e-9, abs_tol=1e-6
                ):
                    fail("archived QUBO/source numerical observation changed: " + field)
            for field in (
                "original_decisions", "full_slack_quo_bits",
                "selected_source_feature_positions",
            ):
                if record[field] != str(verified[field]):
                    fail("source selections/auxiliary decisions no longer match")
            if record["original_feasible"] != str(verified["original_feasible"]):
                fail("feasibility flag changed")
            observed_keys.add(key)
            cells[(g, parent)].append(verified)
        except (IndexError, KeyError, TypeError, OverflowError) as exc:
            fail("invalid source sample schema: " + str(exc))
    if observed_keys != set(expected_seeds):
        fail("missing parent/cell/read from preserved sample archive")

    trial_keys = set()
    for trial in trials:
        g, parent = int(trial["grid_index"]), int(trial["parent_seed"])
        key = (g, parent)
        if key not in cells or key in trial_keys:
            fail("repeated or unknown parent-cell trial")
        trial_keys.add(key)
        draws = cells[key]
        count = sum(s["original_feasible"] for s in draws)
        hits = sum(s["original_feasible"] and
                   abs(s["original_raw_objective"] - FROZEN_N20_OPTIMUM) <= 1e-7
                   for s in draws)
        if (len(draws) != reads or int(trial["reads"]) != reads
                or int(trial["feasible_reads"]) != count
                or int(trial["infeasible_reads"]) != reads - count
                or int(trial["scip_optimum_hits"]) != hits
                or trial["qubo_coefficient_sha256"] != qubos[g][1]):
            fail("parent-cell summary inconsistent with exact original samples")
    if trial_keys != set(cells):
        fail("parent-cell trial records are incomplete")
    output = []
    for point in points:
        draws = [s for p in parents for s in cells[(point["grid_index"], p)]]
        feasible = sum(s["original_feasible"] for s in draws)
        hits = sum(s["original_feasible"] and
                   abs(s["original_raw_objective"] - FROZEN_N20_OPTIMUM) <= 1e-7
                   for s in draws)
        output.append({
            **point,
            "observed_feasible_count": int(feasible),
            "total_draws": len(draws),
            "observed_feasible_fraction": float(feasible / len(draws)),
            "observed_exact_N20_optimum_hits": int(hits),
            "descriptive_only": True,
        })
    return {
        "schema": "M2-frozen-source-pilot-descriptive-3x3-v1",
        "source_archive_sha256": sha256(raw).hexdigest(),
        "source_geojson_sha256": SOURCE_SHA256,
        "N_free": 20, "K": 5, "parent_blocks": parents,
        "reads_per_cell_parent": reads,
        "one_read_sampler_calls": number,
        "panel_counts": output,
        "confidence_intervals_computed": False,
        "best_penalty_or_statistical_ranking_claimed": False,
        "quantum_hardware_used": False,
        "manuscript_input_parity_proven": False,
        "limitation": "Only exploratory parent-block classical SA smoke counts; not an inferential penalty comparison.",
    }


def write_figure_report(raw: bytes, out: Path):
    report = inspect_archive(raw)
    out.mkdir(parents=True, exist_ok=True)
    (out / "verified_penalty_grid.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    with (out / "verified_feasibility_counts.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["panel_counts"])

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    matrix = np.array([
        [report["panel_counts"][3 * i + j]["observed_feasible_count"]
         for j in range(3)] for i in range(3)
    ])
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    im = ax.imshow(matrix)
    ax.set_xticks(range(3), ["row sum", "midpoint", "global P"])
    ax.set_yticks(range(3), ["row sum", "midpoint", "global P"])
    ax.set_xlabel("Connectivity penalty λc")
    ax.set_ylabel("Budget penalty λb")
    ax.set_title("Source N20 • exploratory feasible samples / 8 draws per cell")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{matrix[i, j]}/8", ha="center", va="center")
    fig.colorbar(im, ax=ax, label="Observed feasible draws (out of 8)")
    fig.text(.5, .015, "Classical OpenJij, one small CI execution; not a penalty ranking",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, 1))
    fig.savefig(out / "descriptive_feasible_counts.png", dpi=150)
    plt.close(fig)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_grid_artifact", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summary = write_figure_report(args.original_grid_artifact.read_bytes(), args.out)
    print(json.dumps({
        "source_archive_sha256": summary["source_archive_sha256"],
        "observed_feasible_count_by_grid": [
            x["observed_feasible_count"] for x in summary["panel_counts"]
        ], "statistical_ranking_claimed": summary["best_penalty_or_statistical_ranking_claimed"]
    }, sort_keys=True))


if __name__ == "__main__":
    main()
