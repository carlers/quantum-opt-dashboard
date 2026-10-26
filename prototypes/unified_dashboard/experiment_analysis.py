"""Read-only analysis of researcher-triggered experiment artifacts.

Only completed, checksum-verified jobs are analyzed. Comparisons demand
bitwise-identical ORIGINAL source models (not merely N/K or matching seeds).
No solver is invoked by this module and no statistical significance is claimed.
"""
from __future__ import annotations

import csv
from hashlib import sha256
import io
import json
import math
from pathlib import Path

from problems.water_quality.experiment_jobs import (
    JobError, SOURCE_SHA256, job_dir, job_root, read_job,
)


def _validated_payload(job_id: str, *, root=None):
    record = read_job(job_id, root=root)
    if record["status"] != "completed" or record["result"] is None:
        raise JobError("Only completed experiments may be analyzed")
    folder = job_dir(Path(root) if root is not None else job_root(), job_id)
    try:
        manifest = json.loads((folder / "manifest.json").read_bytes())
        digests = manifest["sha256"]
        required = {"config.json", "model.json", "result.json"}
        if not required.issubset(digests) or set(digests) - (
            required | {"samples.csv", "emitted_scip_model.lp"}
        ):
            raise JobError("Missing or unexpected research evidence files")
        files = {}
        for name, expected in digests.items():
            raw = (folder / name).read_bytes()
            if sha256(raw).hexdigest() != expected:
                raise JobError("Stored " + name + " failed source checksum validation")
            files[name] = raw
        model = json.loads(files["model.json"])
        result = json.loads(files["result.json"])
        spec = record["spec"]
        if (model.get("source_sha256") != SOURCE_SHA256
                or model.get("N_free") != spec.n_free or model.get("K") != spec.k_new
                or result.get("model_sha256") != sha256(files["model.json"]).hexdigest()
                or result.get("job_id") != job_id
                or result.get("configuration") != spec.manifest()
                or result.get("source_sha256") != SOURCE_SHA256
                or model.get("paper_data_parity_proven") is not False):
            raise JobError("Research source and immutable run configuration disagree")
        if spec.solver == "classical_sa" and "samples.csv" not in files:
            raise JobError("Completed classical run is missing every-sample evidence")
        if spec.solver == "scip" and "emitted_scip_model.lp" not in files:
            raise JobError("Completed SCIP run is missing its exported linearized model")
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        if isinstance(exc, JobError):
            raise
        raise JobError("Experiment evidence is missing or corrupted") from exc
    return record, model, result, files


def load_verified_samples(job_id: str, *, root=None) -> list[dict]:
    """Re-evaluate each sampled source x using archived exact binary64 model."""
    job, model, result, files = _validated_payload(job_id, root=root)
    if job["spec"].solver != "classical_sa":
        return []
    n = job["spec"].n_free
    k = job["spec"].k_new
    try:
        raw = files["samples.csv"].decode("utf-8")
        reader = csv.DictReader(io.StringIO(raw))
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise JobError("Invalid sampled-column identities")
        rows = list(reader)
        linear = [float.fromhex(s) for s in model["linear_ieee754_hex"]]
        quadratic = [(int(i), int(j), float.fromhex(q))
                     for i, j, q in model["quadratic_ieee754_hex"]]
        neighbors = model["free_neighbors"]
        fixed = model["fixed_neighbors"]
        master = model["source_master_free_positions"]
        if not (len(linear) == len(neighbors) == len(fixed) == len(master) == n
                and len(rows) == job["spec"].reads
                and len(rows) == result["result"]["total_samples"]):
            raise JobError("Missing source weights, adjacency, or sampled states")
        seen_indices, seen_seeds = set(), set()
        audited = []
        for record in rows:
            index, seed = int(record["read_index"]), int(record["child_seed"])
            bits = record["original_decisions"]
            full = record["full_original_and_auxiliary_bits"]
            if (not 0 <= index < job["spec"].reads
                    or index in seen_indices or seed in seen_seeds
                    or len(bits) != n or any(s not in "01" for s in bits)
                    or not full.startswith(bits) or
                    any(s not in "01" for s in full)):
                raise JobError("Duplicated or malformed original/auxiliary bitstring")
            seen_indices.add(index)
            seen_seeds.add(seed)
            x = [int(s) for s in bits]
            chosen = [i for i, v in enumerate(x) if v]
            connected = all(
                fixed[i] or any(x[j] for j in neighbors[i])
                for i in chosen
            )
            feasible = (len(chosen) == k and connected)
            score = (sum(x[i] * linear[i] for i in range(n))
                     + sum(q * x[i] * x[j] for i, j, q in quadratic))
            recorded_positions = json.loads(record["selected_local_positions"])
            source_positions = json.loads(record["selected_source_master_positions"])
            if (recorded_positions != chosen
                    or source_positions != [master[i] for i in chosen]
                    or record["original_feasible"] != str(feasible)
                    or record["original_budget_ok"] != str(len(chosen) == k)
                    or record["original_connectivity_ok"] != str(connected)
                    or int(record["original_selected_count"]) != len(chosen)
                    or not math.isclose(
                        float(record["original_objective"]), score,
                        rel_tol=1e-10, abs_tol=1e-7
                    )):
                raise JobError("Sample fails independent archived-original-model evaluation")
            audited.append({
                "Read": index,
                "Child seed": seed,
                "Feasible": feasible,
                "Selected count": len(chosen),
                "Budget met": len(chosen) == k,
                "Local one-hop met": connected,
                "Original objective": score,
                "Augmented QUBO energy": float(record["expanded_qubo_augmented_energy"]),
                "Selected source positions": source_positions,
                "Selected local positions": chosen,
            })
        if seen_indices != set(range(job["spec"].reads)):
            raise JobError("One or more samples were omitted")
        summary = result["result"]
        feasible = [s for s in audited if s["Feasible"]]
        if (len(feasible) != summary["feasible_count"]
                or not math.isclose(summary["feasible_fraction"],
                                    len(feasible) / len(audited), abs_tol=1e-12)):
            raise JobError("Stored feasibility summary disagrees with full samples")
        return sorted(audited, key=lambda row: row["Read"])
    except (OSError, ValueError, KeyError, TypeError, IndexError, OverflowError) as exc:
        if isinstance(exc, JobError):
            raise
        raise JobError("Invalid archived sampled-state record") from exc


def compare_completed_jobs(ids: list[str], *, root=None) -> dict:
    """Only compare feasible-source outcomes if source model bytes match exactly."""
    if len(ids) < 2 or len(ids) > 12 or len(set(ids)) != len(ids):
        raise JobError("Select 2–12 distinct saved experiment jobs")
    evidence = [_validated_payload(job_id, root=root) for job_id in ids]
    model_hashes = {
        sha256(files["model.json"]).hexdigest() for _, _, _, files in evidence
    }
    if len(model_hashes) != 1:
        raise JobError(
            "Cannot directly compare different models: candidate identities, "
            "N/K, or exact floating-point source coefficients differ. "
            "Use separately labeled descriptive views instead."
        )
    rows = []
    for job, model, result, files in evidence:
        spec, outcome = job["spec"], result["result"]
        if spec.solver == "classical_sa":
            samples = load_verified_samples(job["job_id"], root=root)
            feasible = [sample for sample in samples if sample["Feasible"]]
            fraction = len(feasible) / len(samples)
            best = min((sample["Original objective"] for sample in feasible), default=None)
            count = len(feasible)
            total = len(samples)
            status = "completed classical sample"
        else:
            if not outcome["source_selection"]["feasible"]:
                raise JobError("Archived SCIP solution is not original-source feasible")
            fraction = 1.0
            best = outcome["source_selection"]["energy"]
            count = total = 1
            status = outcome["scip_status"]
        rows.append({
            "Job ID": job["job_id"], "Solver": spec.solver,
            "N": spec.n_free, "K": spec.k_new,
            "λ budget": spec.lambda_budget if spec.solver == "classical_sa" else None,
            "λ connectivity": spec.lambda_connectivity if spec.solver == "classical_sa" else None,
            "Reads": total, "Original-feasible count": count,
            "Original-feasible fraction": fraction,
            "Best feasible original objective": best,
            "Solver status": status,
            "SCIP proven optimal": (
                bool(outcome["scip_proven_optimal"]) if spec.solver == "scip" else False
            ),
        })
    return {
        "model_sha256": next(iter(model_hashes)),
        "source_sha256": SOURCE_SHA256,
        "same_original_model_verified": True,
        "observations": rows,
        "statistical_inference_or_optimal_penalty_claimed": False,
        "scope": (
            "User-requested descriptive comparisons of identical original source "
            "models. Feasible fractions include all draws, SCIP is one solver "
            "incumbent not an SA sampling frequency, and distinct QUBO penalties "
            "must not be compared using augmented QUBO energies."
        ),
    }
