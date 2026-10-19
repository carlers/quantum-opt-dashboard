"""Observe exact original N20 objective fingerprints across fresh source replays.

Research diagnostic only. Does not adjust source notebook, mathematical scores,
feasible rules, thresholds, weights or claim field-scientific validity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts import science_claim_gate as gate
from scripts.compare_n20_replays import compare, safe_runtime_metadata, walk_diff
from scripts.n20_independent_geometry_audit import certify_geometry
from scripts.run_n20_reference_notebook import verify_result

SCHEMA = 1
PRIOR_OBSERVED_OBJECTIVE_SHAS = (
    "2b238848f43d1763fe093b38360941677e2fa46f1a6c01d05b5b359a62dc5809",
    "8536a3db295bd4f4e0faa8ad599bfbb3c01a0c4391c04ecc145701f83adc3a56",
)
FLOAT_KEYS = ("linear_float64_hex", "quadratic_ij_float64_hex",
              "factor_weights_float64_hex", "site_coords_epsg32651_float64_hex")


def audit_one(record: dict) -> tuple[dict, str]:
    """Revalidate genuine cold source and geometric model before comparing it."""
    gate._assert_source_bytes()
    verify_result(record)
    geometry = certify_geometry(record)
    model = record["model_input"]
    if model["factor_column_names"] != list(gate.FACTOR_NAMES):
        raise AssertionError("Original eight source criterion identities changed")
    if ([float.fromhex(w) for w in model["factor_weights_float64_hex"]]
            != list(gate.ORIGINAL_WEIGHTS)):
        raise AssertionError("Original source AHP numerical weight inputs changed")
    if gate.full_manifest_digest(model) != record["model_input_sha256"]:
        raise AssertionError("Source raw model checksum invalid")
    return geometry, gate.objective_fingerprint(model)


def summarize(records: list[tuple[str, dict]]) -> dict:
    """Exact objective/schema comparison; verification not inferred from hashes.

    Each fresh record is independently source-checked, not trusted because
    it shares a recorded SHA or selects the known optimum.
    """
    if len(records) < 2:
        raise ValueError("Need at least two independently sourced cold records")
    paths = [name for name, _ in records]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate input record paths")
    records = sorted(records)
    identity = {}
    for name, record in records:
        geom, objective_sha = audit_one(record)
        identity[name] = {
            "source_model_sha256": record["model_input_sha256"],
            "objective_sha256": objective_sha,
            "geometry_sha256": geom["spatial_graph_sha256"],
        }
    earlier = compare(records)
    baseline_name, baseline = records[0]
    baseline_manifest = gate.objective_manifest(baseline["model_input"])
    outcomes = []
    variants = {}
    for name, record in records:
        objective_sha = identity[name]["objective_sha256"]
        differences = walk_diff(
            baseline_manifest, gate.objective_manifest(record["model_input"])
        )
        nonnumeric = [d for d in differences if d["kind"] != "float_hex"]
        outside = [d for d in differences if d["kind"] == "float_hex"
                   and not d["within_declared_tolerance"]]
        variants.setdefault(objective_sha, []).append(name)
        outcomes.append({
            "record": name,
            "original_model_sha256": identity[name]["source_model_sha256"],
            "objective_sha256": objective_sha,
            "geometry_sha256": identity[name]["geometry_sha256"],
            "matches_first_objective_exactly": objective_sha == identity[baseline_name]["objective_sha256"],
            "matches_prior_2026_10_19_observed_objective": objective_sha in PRIOR_OBSERVED_OBJECTIVE_SHAS,
            "objective_leaf_differences_from_first": differences,
            "objective_structural_differences": nonnumeric,
            "objective_numeric_outside_declared_diagnostic_tolerance": outside,
            "selected": record["selected_local_positions"],
            "source_energy": record["original_energy"],
            "core_versions": record.get("scientific_environment"),
        })
    return {
        "schema_version": SCHEMA,
        "scope": "historical N20/K5 source computational objective only, observational cross-run experiment",
        "source_file_bytes_checked_and_original_N20_reverified": True,
        "individual_raw_geometry_independently_checked": True,
        "records": len(records),
        "baseline_record": baseline_name,
        "objective_sha_variants_to_records": variants,
        "observed_exact_objective_stability": len(variants) == 1,
        "historical_2026_10_19_objective_sha_observations_not_replayed_here": list(PRIOR_OBSERVED_OBJECTIVE_SHAS),
        "comparisons": outcomes,
        "original_model_comparison": earlier,
        "diagnostic_semantic_equivalence_only": (
            earlier["semantic_pass_with_tolerance"]
            and all(not r["objective_structural_differences"]
                    and not r["objective_numeric_outside_declared_diagnostic_tolerance"]
                    for r in outcomes)
        ),
        "bit_exact_objectives_claimed_identical": len(variants) == 1,
        "source_calculation_not_manuscript_or_physical_validation": True,
        "cautions": [
            "A matching SHA across sampled hosts is not universal cross-platform determinism",
            "An objective SHA difference does not by itself identify changed physical science",
            "This new experiment cannot retrospectively recover older CI raw model coefficients",
            "ULP estimates do not identify a CPU instruction, dispatch library or cause",
            "Source model SHA and scored objective SHA are different hash namespaces",
            "Different exact coefficient fingerprints remain different cache identities",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--min-results", type=int, default=6)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError("Refusing to overwrite prior scientific cross-run result")
    if args.min_results < 2:
        raise ValueError("Require at least two independent processes")
    paths = sorted(args.inputs_root.rglob("replicate-*.json"))
    if len(paths) < args.min_results:
        raise ValueError(f"Expected {args.min_results} independent samples, got {len(paths)}")
    records = [(str(p.relative_to(args.inputs_root)),
                json.loads(p.read_text(encoding="utf-8"))) for p in paths]
    result = summarize(records)
    metapaths = sorted(args.inputs_root.rglob("runtime.json"))
    result["runtime_records"] = [{
        "record": str(p.relative_to(args.inputs_root)),
        "environment": json.loads(p.read_text(encoding="utf-8")),
    } for p in metapaths]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(gate.canonical(result))
    print("N20_OBJECTIVE_CROSS_RUN " + json.dumps({
        "process_records": result["records"],
        "distinct_exact_objective_fingerprints": len(result["objective_sha_variants_to_records"]),
        "fingerprints": sorted(result["objective_sha_variants_to_records"]),
        "diagnostic_semantic_equivalence": result["diagnostic_semantic_equivalence_only"],
        "environment_records": len(metapaths),
    }, sort_keys=True))
    if not result["diagnostic_semantic_equivalence_only"]:
        raise AssertionError("Changed original structural semantics or beyond-tolerance numeric inputs")


if __name__ == "__main__":
    main()
