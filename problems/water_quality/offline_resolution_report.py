"""Make read-only, source-bound N50/N100 scientific comparison outputs.

No Streamlit, solver on UI reruns, paper-reproduction claim, runtime
scaling inference, or 5,417-site master-objective extrapolation.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
import math
from pathlib import Path
from zipfile import ZipFile, is_zipfile

from problems.water_quality.independent_lp_bounds import inspect_archive
from problems.water_quality.offline_scip_batch import (
    EXPECTED_SOURCE_SHA, canonical, verify_bundle, verify_cross_tier_embedding,
)

FIELDS = (
    "N_free", "K", "native_original_objective", "original_linear_component",
    "original_quadratic_component", "SCIP_status", "SCIP_relative_gap",
    "HiGHS_dual_bound", "HiGHS_relative_gap",
    "SCIP_call_seconds_including_LP_export", "child_process_wall_seconds",
    "source_model_rebuild_seconds", "selected_source_positions",
    "model_sha256", "emitted_LP_sha256", "source_geojson_sha256",
)
MAX_WORKFLOW_ARTIFACT_BYTES = 20_000_000


def fail(message):
    raise ValueError("Provenance-verified M3 report: " + message)


def _check_receipt(saved, fresh):
    if type(saved) is not dict:
        fail("missing second-solver record")
    for key in (
        "schema", "N_free", "K", "source_sha256", "model_sha256",
        "actual_exported_LP_sha256", "scip_status", "highs_status",
        "independent_computational_optimality_corroboration",
        "formal_proof_certificate", "paper_input_parity_claimed",
    ):
        if saved.get(key) != fresh[key]:
            fail("HiGHS receipt identity or claim changed: " + key)
    for key in ("scip_objective", "highs_primal_objective",
                "highs_dual_bound", "highs_relative_gap"):
        old, new = saved.get(key), fresh.get(key)
        if (type(old) not in (int, float) or not math.isfinite(old)
                or not math.isclose(old, new, rel_tol=1e-8, abs_tol=1e-6)):
            fail("HiGHS bound/certificate changed: " + key)


def extract_verified_rows(artifact: bytes, *, independent_seconds: int = 20) -> tuple[list[dict], dict]:
    """Revalidate uploaded CI evidence against fresh independent MILP bounds."""
    if not isinstance(artifact, bytes) or not 0 < len(artifact) <= MAX_WORKFLOW_ARTIFACT_BYTES:
        fail("workflow evidence ZIP missing or too large")
    if not is_zipfile(io.BytesIO(artifact)):
        fail("invalid workflow source ZIP")
    with ZipFile(io.BytesIO(artifact)) as outer:
        entries = outer.namelist()
        if len(set(entries)) != len(entries):
            fail("duplicate workflow artifact members")
        if not {"source-execution.zip", "highs-bound-receipt.json"}.issubset(entries):
            fail("requires paired source execution and independent bound receipt")
        source_zip = outer.read("source-execution.zip")
        claimed = json.loads(outer.read("highs-bound-receipt.json"))
        if claimed.get("schema") != "independent-source-lp-highs-bounds-v1":
            fail("unexpected second-solver proof scope")
        reverified = inspect_archive(io.BytesIO(source_zip), seconds=independent_seconds)
        saved = claimed.get("runs")
        if not isinstance(saved, list) or len(saved) != 2:
            fail("exactly two source-pinned second-solver receipts required")
        for a, b in zip(saved, reverified):
            _check_receipt(a, b)
    with ZipFile(io.BytesIO(source_zip)) as sources:
        index = json.loads(sources.read("index.json"))
        if index["source_sha256"] != EXPECTED_SOURCE_SHA:
            fail("historical source hash changed")
        tiers = {}
        for entry in index["tiers"]:
            raw = sources.read(entry["archive"])
            if sha256(raw).hexdigest() != entry["archive_sha256"]:
                fail("per-tier source archive hash changed")
            verified = verify_bundle(raw)
            if verified["classification"] != "optimal" or verified["independent_audit"] is None:
                fail("non-optimal/unchecked tier cannot enter this figure")
            with ZipFile(io.BytesIO(raw)) as nested:
                model = json.loads(nested.read("model.json"))
            if model["source_sha256"] != EXPECTED_SOURCE_SHA:
                fail("different source model")
            tiers[entry["N_free"]] = (model, verified)
        if set(tiers) != {50, 100}:
            fail("expected exactly N50 and N100")
        comparison = verify_cross_tier_embedding(
            tiers[50][0], tiers[50][1], tiers[100][0], tiers[100][1]
        )
        if not (comparison["small_solution_feasible_in_large_tier"]
                and comparison["both_scip_runs_reported_optimal"]):
            fail("nested mathematical embedding was not proven")
        rows = []
        for fresh in reverified:
            n = fresh["N_free"]
            model, result = tiers[n]
            witness = result["independent_audit"]
            if fresh["model_sha256"] != sha256(canonical(model)).hexdigest():
                fail("verified LP / recorded model is not the current tier")
            if not math.isclose(
                fresh["highs_dual_bound"], witness["original_objective"],
                rel_tol=1e-8, abs_tol=1e-6
            ):
                fail("second-solver global bound does not match native objective")
            rows.append({
                "N_free": n, "K": model["K"],
                "native_original_objective": witness["original_objective"],
                "original_linear_component": witness["linear_component"],
                "original_quadratic_component": witness["quadratic_component"],
                "SCIP_status": result["solver_status"],
                "SCIP_relative_gap": result["solver_gap"],
                "HiGHS_dual_bound": fresh["highs_dual_bound"],
                "HiGHS_relative_gap": fresh["highs_relative_gap"],
                "SCIP_call_seconds_including_LP_export": result["solve_call_seconds"],
                "child_process_wall_seconds": result["worker_wall_seconds"],
                "source_model_rebuild_seconds": result["model_build_seconds"],
                "selected_source_positions": json.dumps(
                    witness["selected_master_positions"], separators=(",", ":")
                ),
                "model_sha256": fresh["model_sha256"],
                "emitted_LP_sha256": fresh["actual_exported_LP_sha256"],
                "source_geojson_sha256": EXPECTED_SOURCE_SHA,
            })
        if [row["N_free"] for row in rows] != [50, 100]:
            fail("missing ordered nested tiers")
        report = {
            "schema": "source-audited-two-resolution-observations-v1",
            "source_sha256": EXPECTED_SOURCE_SHA,
            "workflow_artifact_zip_sha256": sha256(artifact).hexdigest(),
            "SCIP_and_HiGHS_independently_optimal_for_exported_models": True,
            "cross_tier_embedding": comparison,
            "single_source_science_CI_execution": True,
            "paper_data_parity_proven": False,
            "physical_sensor_placement_validated": False,
            "formal_signed_optimality_certificate": False,
            "runtime_scaling_inference_permitted": False,
            "full_5417_site_master_objective_evaluated": False,
            "chart_note": (
                "Single CI run, native per-N source objective; cross-N source "
                "coefficients and feasible smaller-in-larger embedding checked. "
                "SCIP and independent HiGHS optima agree, not a paper reproduction."
            ),
            "observations": rows,
        }
        return rows, report


def write_outputs(raw: bytes, output: Path, *, independent_seconds: int = 20):
    rows, report = extract_verified_rows(raw, independent_seconds=independent_seconds)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "original_objective_by_resolution.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (output / "verified_comparison.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    # Matplotlib only in the offline report builder, NEVER a Streamlit rerun.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.3, 4.8))
    ns = [row["N_free"] for row in rows]
    objective = [row["native_original_objective"] for row in rows]
    ax.scatter(ns, objective, s=65)
    ax.set_ylim(min(objective) - 0.035, max(objective) + 0.045)
    ax.set_xlim(min(ns) - 10, max(ns) + 10)
    ax.set_xticks(ns, [f"N={n}" for n in ns])
    ax.set_ylabel("Original local-model objective (minimize)")
    ax.set_xlabel("Free candidate decisions (N)")
    ax.set_title("Source-pinned N50/N100 • one CI execution")
    ax.grid(True, axis="y", alpha=0.3)
    for n, score in zip(ns, objective):
        ax.annotate(f"{score:.7f}", (n, score), xytext=(0, 9),
                    textcoords="offset points", ha="center")
    fig.text(
        0.5, 0.015,
        "K=5 • historical notebook weights • SCIP + HiGHS verified • "
        "no paper parity or runtime-scaling claim",
        ha="center", va="bottom", fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(output / "original_objective_by_resolution.png", dpi=160)
    plt.close(fig)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow_artifact", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=20)
    args = parser.parse_args()
    report = write_outputs(args.workflow_artifact.read_bytes(), args.output,
                           independent_seconds=args.seconds)
    print(json.dumps({
        "schema": report["schema"],
        "source_sha256": report["source_sha256"],
        "values": [
            [row["N_free"], row["native_original_objective"]]
            for row in report["observations"]
        ],
        "runtime_scaling_claimed": report["runtime_scaling_inference_permitted"],
    }, indent=2))


if __name__ == "__main__":
    main()
