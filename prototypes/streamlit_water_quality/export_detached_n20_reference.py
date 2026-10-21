"""Export source-compiled N20 LP + *unsigned* evidence for detached review.

Challenge MUST be issued outside this exporter. The bundled source digest is
only a proposed commitment, NOT an independently endorsed source reference.
A reviewer must compare it to their independently controlled commitment.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import re

from detached_n20_verifier import canonical, digest
from model import NOTEBOOK_WEIGHTS, load_data, make_instance, solve_scip
from mvp_audit import source_sha
from scip_lp_reexecution import reexecute_emitted_lp_in_child

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"


def build_envelope(instance, lp: bytes, first, metrics: dict,
                   report: dict, dataset_sha256: str, nonce: str) -> dict:
    if re.fullmatch(r"[0-9a-f]{32,64}", nonce) is None:
        raise ValueError("Reviewer-issued challenge nonce must be hexadecimal and bounded")
    source = {
        "dataset_sha256": dataset_sha256,
        "criterion_semantics": "historical_8_factor_original_D2_road_proximity_not_WorldPop",
        "n_free": 20,
        "n_fixed": 15,
        "budget": int(instance.budget),
        "free_master_feature_positions": [int(i) for i in instance.free_indices],
        "fixed_master_feature_positions": [int(i) for i in instance.fixed_indices],
        "linear_float64_hex": [float(x).hex() for x in instance.linear],
        "quadratic_terms": [
            {"i": int(i), "j": int(j), "q_float64_hex": float(q).hex()}
            for i, j, q in instance.quadratic
        ],
        "fixed_neighbor_flags": [int(i) for i in instance.fixed_neighbors],
        "free_neighbors": [list(map(int, ns)) for ns in instance.neighbors],
    }
    upstream = {
        "status": metrics["status"],
        "optimal": metrics["optimal"],
        "gap": float(metrics["gap"]),
        "feasible": metrics["feasible"],
        "budget_ok": metrics["budget_ok"],
        "connectivity_ok": metrics["connectivity_ok"],
        "isolated": metrics["isolated"],
        "num_selected": int(metrics["num_selected"]),
        "energy": float(metrics["energy"]),
        "binary20": [int(v) for v in first],
    }
    return {
        "schema_version": 1,
        "scope": "N20_original_source_local_unsigned_process_review",
        "challenge_nonce": nonce,
        "source": source,
        "source_sha256": digest(source),
        "lp_sha256": sha256(lp).hexdigest(),
        "upstream": upstream,
        "child": report["observed_child_receipt"],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--challenge", required=True, type=Path)
    p.add_argument("--envelope-output", required=True, type=Path)
    p.add_argument("--lp-output", required=True, type=Path)
    p.add_argument("--commitment-output", required=True, type=Path)
    args = p.parse_args()
    destinations = (args.envelope_output, args.lp_output, args.commitment_output)
    if len({v.resolve() for v in destinations}) != len(destinations):
        raise ValueError("Research envelope, LP and source commitment paths must differ")
    if any(v.exists() for v in destinations):
        raise FileExistsError("Refuse to overwrite prior detached review evidence")
    challenge = json.loads(args.challenge.read_text("utf-8"))
    if type(challenge) is not dict or set(challenge) != {"nonce"}:
        raise ValueError("Expect a separately prepared nonce-only challenge")
    dataset_sha = source_sha(DATA)
    data = load_data(DATA)
    instance, fallback = make_instance(data, NOTEBOOK_WEIGHTS, 20, 5)
    if fallback:
        raise ValueError("Original fixed stations unexpectedly substituted")
    with TemporaryDirectory(prefix="n20_detached_export_") as tmp:
        original_lp_file = Path(tmp) / "source_original.lp"
        first, metrics = solve_scip(instance, time_limit=30,
                                    export_lp_path=original_lp_file)
        lp = original_lp_file.read_bytes()
        child = reexecute_emitted_lp_in_child(instance, lp, first, metrics)
    envelope = build_envelope(instance, lp, first, metrics, child,
                              dataset_sha, challenge["nonce"])
    for v in destinations:
        v.parent.mkdir(parents=True, exist_ok=True)
    args.lp_output.write_bytes(lp)
    args.envelope_output.write_bytes(canonical(envelope))
    # This file is *co-produced*, not an independently authoritative reference.
    args.commitment_output.write_bytes(canonical({
        "source_sha256": envelope["source_sha256"],
        "dataset_sha256": envelope["source"]["dataset_sha256"],
        "source_origin": "UNTRUSTED_same_runner_demonstration_requires_owner_anchor",
        "independently_authorized": False,
    }))
    print("N20_UNSIGNED_DETACHED_EXPORT " + json.dumps({
        "lp_sha256": envelope["lp_sha256"],
        "source_sha256": envelope["source_sha256"],
        "nonce_bound": True,
        "commitment_independently_authorized": False,
        "signed": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
