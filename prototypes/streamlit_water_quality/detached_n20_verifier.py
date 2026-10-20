"""Offline detached N20 verification verdict, without a signer or deployed service.

No imports from the UX app's model compiler, Streamlit, GeoJSON loader or SCIP.
Input source-model commitment AND random run challenge must come from an
independently governed verifier caller, NOT from this same submitted envelope.

This creates no remote trust: any host able to replace both executable and
challenge could forge the result. A SHA digest is not a signature.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace
import sys

# In Python -I, the script directory is deliberately absent from sys.path.
# Permit exactly this checked-out, adjacent *pure* structural LP parser, but
# do not import the app, original notebook, or PySCIPOpt into the verifier.
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from scip_lp_structure import certify_emitted_scip_lp

SCHEMA = 1
MAX_JSON_BYTES = 150_000
MAX_LP_BYTES = 100_000
SOURCE_SCHEMA = {
    "dataset_sha256", "criterion_semantics", "n_free", "n_fixed", "budget",
    "free_master_feature_positions", "fixed_master_feature_positions",
    "linear_float64_hex", "quadratic_terms", "fixed_neighbor_flags",
    "free_neighbors",
}
ENVELOPE_SCHEMA = {
    "schema_version", "scope", "challenge_nonce", "source", "source_sha256",
    "lp_sha256", "upstream", "child",
}
_UPSTREAM = {
    "status", "optimal", "gap", "feasible", "budget_ok", "connectivity_ok",
    "isolated", "num_selected", "energy", "binary20",
}
CHILD_SCOPE = "fresh_separate_python_process_reads_actual_exported_binary_MILP"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
NONCE = re.compile(r"[0-9a-f]{32,64}\Z")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(value: object) -> str:
    return sha256(canonical(value)).hexdigest()


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise ValueError("Detached N20 review verdict: " + msg)


def _real(value, name: str) -> float:
    require(type(value) in (float, int) and math.isfinite(value),
            "nonfinite or nonnumeric " + name)
    return float(value)


def _binary20(raw, k: int, name: str) -> tuple[int, ...]:
    require(type(raw) is list and len(raw) == 20
            and all(type(bit) is int and bit in (0, 1) for bit in raw)
            and sum(raw) == k, "nonbinary or wrong-budget " + name)
    return tuple(raw)


def _source(source: dict):
    require(type(source) is dict and set(source) == SOURCE_SCHEMA,
            "incomplete, extra or unrecognized source model fields")
    require(type(source["dataset_sha256"]) is str
            and HEX64.fullmatch(source["dataset_sha256"]) is not None
            and source["criterion_semantics"] ==
                "historical_8_factor_original_D2_road_proximity_not_WorldPop",
            "original dataset or criterion source not explicitly identified")
    n = source["n_free"]
    k = source["budget"]
    require(type(n) is int and n == 20
            and type(source["n_fixed"]) is int and source["n_fixed"] == 15
            and type(k) is int and k == 5,
            "detached verdict restricted to original N20/K5/15-existing source")
    free = source["free_master_feature_positions"]
    fixed = source["fixed_master_feature_positions"]
    require(type(free) is list and type(fixed) is list
            and len(free) == 20 and len(fixed) == 15
            and all(type(x) is int and 0 <= x < 5417 for x in free + fixed)
            and len(set(free + fixed)) == 35,
            "original ordered master-site identity or fixed sites malformed")
    linear_raw = source["linear_float64_hex"]
    require(type(linear_raw) is list and len(linear_raw) == 20,
            "wrong original objective linear dimension")
    def number(hexstr: str) -> float:
        require(type(hexstr) is str and len(hexstr) <= 32
                and re.fullmatch(r"-?0x[0-9a-f]+(?:\.[0-9a-f]+)?p[+-]?[0-9]+", hexstr)
                is not None, "invalid original binary64 coefficient encoding")
        v = float.fromhex(hexstr)
        require(math.isfinite(v) and float.hex(v) == hexstr,
                "noncanonical/nonfinite original binary64 coefficient")
        return v
    linear = [number(x) for x in linear_raw]
    pairs = []
    old = (-1, -1)
    pair_raw = source["quadratic_terms"]
    require(type(pair_raw) is list and len(pair_raw) <= 190,
            "malformed quadratic source terms")
    for pair in pair_raw:
        require(type(pair) is dict and set(pair) == {"i", "j", "q_float64_hex"},
                "unexpected source quadratic term")
        i, j = pair["i"], pair["j"]
        q = number(pair["q_float64_hex"])
        require(type(i) is int and type(j) is int and 0 <= i < j < 20
                and (i, j) > old and q > 0, "unsorted/duplicated/invalid pair penalty")
        old = (i, j)
        pairs.append((i, j, q))
    fixed_neighbors = source["fixed_neighbor_flags"]
    neighbors = source["free_neighbors"]
    require(type(fixed_neighbors) is list and len(fixed_neighbors) == 20
            and all(type(f) is int and f in (0, 1) for f in fixed_neighbors),
            "invalid original source fixed-neighbor flags")
    require(type(neighbors) is list and len(neighbors) == 20, "wrong adjacency size")
    adjacent = []
    for i, ns in enumerate(neighbors):
        require(type(ns) is list
                and all(type(j) is int and 0 <= j < 20 and j != i for j in ns)
                and ns == sorted(set(ns)), "invalid original one-hop neighbor list")
        adjacent.append(tuple(ns))
    for i in range(20):
        for j in adjacent[i]:
            require(i in adjacent[j], "asymmetric original local graph")
    return SimpleNamespace(
        free_indices=tuple(free), fixed_indices=tuple(fixed),
        linear=tuple(linear), quadratic=tuple(pairs),
        fixed_neighbors=tuple(fixed_neighbors), neighbors=tuple(adjacent),
        budget=k,
    )


def _feasible(bits: tuple[int, ...], model) -> bool:
    return sum(bits) == model.budget and all(
        not bits[i] or model.fixed_neighbors[i]
        or any(bits[j] for j in model.neighbors[i])
        for i in range(20)
    )


def _exact_oracle(model):
    values = [Fraction.from_float(x) for x in model.linear]
    pairs = [(i, j, Fraction.from_float(q)) for i, j, q in model.quadratic]
    denominator = max([v.denominator for v in values] +
                      [q.denominator for _, _, q in pairs] + [1])
    linear = [int(v * denominator) for v in values]
    quadratic = [(i, j, int(v * denominator)) for i, j, v in pairs]
    count = 0
    membership = sha256()
    winner, best = None, None
    for subset in combinations(range(20), model.budget):
        bits = tuple(int(i in subset) for i in range(20))
        if not _feasible(bits, model):
            continue
        count += 1
        membership.update((",".join(map(str, subset)) + "\n").encode("ascii"))
        score = sum(linear[i] for i in subset)
        score += sum(q for i, j, q in quadratic if bits[i] and bits[j])
        if best is None or score < best:
            winner, best = list(subset), score
    require(winner is not None and count > 0, "original source graph has no valid K5")
    return Fraction(best, denominator), winner, count, membership.hexdigest()


def _score(bits: tuple[int, ...], model) -> Fraction:
    chosen = {i for i in range(20) if bits[i]}
    return (sum((Fraction.from_float(model.linear[i]) for i in chosen),
                Fraction(0)) +
            sum((Fraction.from_float(q) for i, j, q in model.quadratic
                 if i in chosen and j in chosen), Fraction(0)))


def verify(envelope: dict, lp: bytes, *, expected_nonce: str,
           expected_source_sha256: str, expected_dataset_sha256: str) -> dict:
    """Offline verdict. Three expected values MUST come from outside envelope."""
    require(type(envelope) is dict and set(envelope) == ENVELOPE_SCHEMA
            and envelope["schema_version"] == 1
            and envelope["scope"] == "N20_original_source_local_unsigned_process_review",
            "unknown/extra/unrecognized research submission")
    require(type(expected_nonce) is str and NONCE.fullmatch(expected_nonce) is not None
            and envelope["challenge_nonce"] == expected_nonce,
            "unrecognized, stale or mismatched run challenge")
    require(type(expected_source_sha256) is str
            and HEX64.fullmatch(expected_source_sha256) is not None
            and envelope["source_sha256"] == expected_source_sha256
            and digest(envelope["source"]) == expected_source_sha256,
            "source model not bound to independently supplied reference commitment")
    require(type(expected_dataset_sha256) is str
            and HEX64.fullmatch(expected_dataset_sha256) is not None
            and envelope["source"]["dataset_sha256"] == expected_dataset_sha256,
            "dataset digest not anchored to separately supplied source reference")
    require(type(lp) is bytes and 0 < len(lp) <= MAX_LP_BYTES
            and envelope["lp_sha256"] == sha256(lp).hexdigest(),
            "provided emitted SCIP LP does not match submitted bytes")
    source = _source(envelope["source"])
    lp_proof = certify_emitted_scip_lp(source, lp)
    best, witness, feasible, membership = _exact_oracle(source)

    upstream = envelope["upstream"]
    require(type(upstream) is dict and set(upstream) == _UPSTREAM
            and upstream["status"] == "optimal"
            and upstream["optimal"] is True and upstream["feasible"] is True
            and upstream["budget_ok"] is True and upstream["connectivity_ok"] is True
            and upstream["isolated"] == []
            and type(upstream["num_selected"]) is int
            and upstream["num_selected"] == source.budget,
            "first SCIP reported metadata incompatible with claimed optimum")
    require(0 <= _real(upstream["gap"], "upstream gap") <= 1e-6,
            "first SCIP reported invalid or nonconverged gap")
    first = _binary20(upstream["binary20"], source.budget, "first SCIP sites")
    require(_feasible(first, source) and _score(first, source) == best,
            "first SCIP selection violates original graph or exact optimum")
    require(math.isclose(_real(upstream["energy"], "first energy"),
                         float(best), abs_tol=1e-7, rel_tol=0),
            "first SCIP objective report differs from exact source model")

    child = envelope["child"]
    require(type(child) is dict
            and child.get("receipt_schema") == 1
            and child.get("scope") ==
                "fresh_separate_python_process_reads_actual_exported_binary_MILP"
            and child.get("solver_did_read_and_optimize_lp_in_this_process") is True
            and child.get("this_is_an_untrusted_local_process_receipt_not_signed_attestation") is True
            and child.get("original_upstream_scip_execution_authenticated") is False
            and child.get("published_manuscript_or_physical_lake_quality_validated") is False
            and child.get("input_lp_sha256") == envelope["lp_sha256"]
            and child.get("input_lp_bytes") == len(lp)
            and child.get("original_binary_variable_count") ==
                lp_proof["binary_variable_count"]
            and child.get("status") == "optimal"
            and type(child.get("best_solution_count")) is int
            and child["best_solution_count"] >= 1
            and type(child.get("solver_time_limit_seconds")) is int
            and child["solver_time_limit_seconds"] == 30,
            "child process receipt lacks honest original LP/status/provenance")
    second = _binary20(child.get("original_binary20"), source.budget,
                       "second SCIP sites")
    require(_feasible(second, source) and _score(second, source) == best,
            "second SCIP selection violates original graph or exact optimum")
    objective = _real(child.get("objective_lp_decimal_approx"), "child LP objective")
    primal = _real(child.get("primal_bound_lp_decimal"), "child primal")
    dual = _real(child.get("dual_bound_lp_decimal"), "child dual")
    gap = _real(child.get("reported_relative_gap"), "child gap")
    require(0 <= gap <= 1e-6 and dual <= primal + 1e-7
            and abs(primal - dual) <= 1e-6
            and abs(objective - primal) <= 1e-7
            and math.isclose(objective, float(best), abs_tol=1e-7, rel_tol=0),
            "second SCIP reported nonconvergent or forged LP bounds")

    return {
        "schema_version": SCHEMA,
        "scope": "offline_challenge_bound_original_N20_mathematical_review_ONLY",
        "verdict": "source_local_mathematically_verified",
        "challenge_nonce": expected_nonce,
        "untrusted_submission_sha256": digest(envelope),
        "independently_expected_source_sha256": expected_source_sha256,
        "independently_expected_dataset_sha256": expected_dataset_sha256,
        "emitted_original_scip_lp_sha256": sha256(lp).hexdigest(),
        "structural_lp_constraint_count": lp_proof["structurally_verified_constraint_count"],
        "feasible_n20_k5_count": feasible,
        "feasible_membership_sha256": membership,
        "exact_optimum_witness": witness,
        "first_selected": [i for i in range(20) if first[i]],
        "second_selected": [i for i in range(20) if second[i]],
        "exact_binary64_optimum_numerator": str(best.numerator),
        "exact_binary64_optimum_denominator": str(best.denominator),
        "separate_process_receipt_is_self_reported": True,
        "first_solver_process_externally_authenticated": False,
        "signed_by_separately_governed_key": False,
        "nonce_replay_consumption_enforced_by_service": False,
        "published_manuscript_reconstructed": False,
        "physical_RF_DO_coverage_validated": False,
    }


def _read_json(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink()
            and 0 < path.stat().st_size <= MAX_JSON_BYTES,
            "missing or oversized detached JSON envelope")
    def pairs_hook(pairs):
        keys = [key for key, _ in pairs]
        require(len(keys) == len(set(keys)), "duplicate JSON keys in untrusted envelope")
        return dict(pairs)
    def reject_constant(value):
        raise ValueError("Detached N20 review verdict: invalid JSON constant " + value)
    return json.loads(path.read_text("utf-8"), object_pairs_hook=pairs_hook,
                      parse_constant=reject_constant)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--envelope", required=True, type=Path)
    p.add_argument("--lp", required=True, type=Path)
    p.add_argument("--expected-nonce", required=True)
    p.add_argument("--expected-source-sha256", required=True)
    p.add_argument("--expected-dataset-sha256", required=True)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    require(not a.output.exists(), "refuse to replace earlier reviewer verdict")
    require(a.lp.is_file() and not a.lp.is_symlink()
            and 0 < a.lp.stat().st_size <= MAX_LP_BYTES,
            "missing/oversized original SCIP LP")
    result = verify(_read_json(a.envelope), a.lp.read_bytes(),
                    expected_nonce=a.expected_nonce,
                    expected_source_sha256=a.expected_source_sha256,
                    expected_dataset_sha256=a.expected_dataset_sha256)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(canonical(result))
    print("N20_DETACHED_UNSIGNED_VERDICT " + json.dumps({
        "verdict": result["verdict"],
        "feasible": result["feasible_n20_k5_count"],
        "witness": result["exact_optimum_witness"],
        "signature": False,
        "replay_service": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
