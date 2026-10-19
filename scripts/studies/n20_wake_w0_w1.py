"""Historical W0 vs posthoc-motivated wake-off W1 sensitivity.

Protocol committed before this code in DRAFT PR #81. Historical source is
not edited. No claim of real downstream hydrodynamics or blind discovery.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import platform

import numpy as np
import scipy
import shapely
from shapely import concave_hull
from shapely.geometry import MultiPoint, Point, LineString

from scripts.n20_independent_geometry_audit import (
    EXPECTED_DATA_SHA, EXPECTED_FREE, EXPECTED_FIXED,
    EXPECTED_FEASIBLE, source_coordinates, original_fixed_spacing,
    feasible_subsets,
)

N_FREE, N_FIXED, K_NEW = 20, 15, 5
L_C, L_W, BETA, CONE = 7500.0, 1000.0, 1.0, .7071
EXPECTED_SOURCE_SHA = "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048"
EXPECTED_MEMBERSHIP = "2956ba5ace10cd6334fab0165f09f66628f231d9c5e63c934061b7879e21979a"
EXPECTED_BEST = [0, 1, 3, 6, 7]
EXPECTED_BEST_E = -3.3012934918564643
ARCHIVE = Path(__file__).resolve().parents[2] / "problems/water_quality/notebooks/experiment9 grid search copy.ipynb"


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def source_wake_pair(cosine: float, distance: float) -> float:
    """Exact archived signed-branch expression; no abs simplification here."""
    if not math.isfinite(cosine) or not math.isfinite(distance) or distance <= 0:
        raise ValueError("Wake requires nonzero finite distance and cosine")
    cosine = float(np.clip(cosine, -1.0, 1.0))
    forward = np.exp(-distance / L_W) * cosine if cosine > CONE else 0.0
    backward = -np.exp(-distance / L_W) * cosine if -cosine > CONE else 0.0
    return float(forward + backward)


def source_case(model: dict, raw_coords, hull, *, delta: float) -> dict:
    """Recompute original all-35-pair loop and linearization from first principles."""
    if delta not in (0.0, 1.0):
        raise ValueError("Only frozen W0 delta=1 or W1 delta=0 registered")
    positions = np.asarray([
        [float.fromhex(v) for v in row]
        for row in model["site_coords_epsg32651_float64_hex"]
    ], dtype=float)
    expected = np.asarray(raw_coords, dtype=float)[EXPECTED_FREE + EXPECTED_FIXED]
    if positions.shape != (35, 2) or not np.array_equal(positions, expected):
        raise AssertionError("Frozen source station coordinates / ordering changed")
    orig_utility = [float.fromhex(s) for s in model["utility_free_float64_hex"]]
    if len(orig_utility) != 20:
        raise AssertionError("Original factor utility size changed")
    linear = -np.asarray(orig_utility, dtype=float).copy()
    quad = []
    neighbors = [set() for _ in range(20)]
    fixed = [0] * 20
    wake_free_free = []
    wake_free_fixed = []
    geo_pairs = 0
    for i, j in combinations(range(35), 2):
        p, q = positions[i], positions[j]
        if not (hull.contains(Point(p)) and hull.contains(Point(q))
                and hull.contains(LineString([p, q]))):
            continue
        displacement = q - p
        d = float(np.linalg.norm(displacement))
        if d == 0:
            continue
        geo_pairs += 1
        if d <= float.fromhex(model["d_max_m_float64_hex"]):
            if i < 20 and j < 20:
                neighbors[i].add(j)
                neighbors[j].add(i)
            elif i < 20:
                fixed[i] = 1
            elif j < 20:
                fixed[j] = 1
        if d > 2 * L_C:
            continue
        redundancy = max(0.0, 1.0 - d / L_C)
        cosine = float(np.clip(displacement[0] / d, -1.0, 1.0))
        wake = source_wake_pair(cosine, d)
        if wake < -1e-14:
            raise AssertionError("Source pair wake unexpectedly negative")
        if wake > 0:
            if i < 20 and j < 20:
                wake_free_free.append([i, j, float(wake).hex()])
            elif i < 20 and j >= 20:
                wake_free_fixed.append([i, j - 20, float(wake).hex()])
        coefficient = float(BETA * redundancy + delta * wake)
        if abs(coefficient) <= 1e-12:
            continue
        if i < 20 and j < 20:
            quad.append((i, j, coefficient))
        elif i < 20:
            linear[i] += coefficient
        elif j < 20:
            linear[j] += coefficient
    case = {
        "delta": delta,
        "linear_float64_hex": [float(a).hex() for a in linear],
        "quadratic_ij_float64_hex": [[i, j, float(q).hex()] for i, j, q in quad],
        "neighbors": [sorted(n) for n in neighbors],
        "fixed_flags": fixed,
        "geometry_eligible_nonzero_length_all_site_pairs": geo_pairs,
        "positive_wake_free_free_pairs": wake_free_free,
        "positive_wake_free_fixed_pairs": wake_free_fixed,
    }
    case["coefficient_manifest_sha256"] = digest({
        "delta": case["delta"], "linear": case["linear_float64_hex"],
        "quadratic": case["quadratic_ij_float64_hex"]
    })
    return case


def score(case, ids: tuple[int, ...]) -> float:
    linear = [float.fromhex(s) for s in case["linear_float64_hex"]]
    selected = set(ids)
    return float(sum(linear[i] for i in ids) +
                 sum(float.fromhex(q) for i, j, q in case["quadratic_ij_float64_hex"]
                     if i in selected and j in selected))


def evaluate_case(case):
    nbs, fixed = case["neighbors"], case["fixed_flags"]
    rank = []
    feasible_sha = hashlib.sha256()
    count = 0
    for ids in combinations(range(20), K_NEW):
        s = set(ids)
        if any(not fixed[i] and not any(j in s for j in nbs[i]) for i in ids):
            continue
        count += 1
        feasible_sha.update((",".join(map(str, ids)) + "\n").encode("ascii"))
        rank.append((score(case, ids), ids))
    rank.sort(key=lambda pair: (pair[0], pair[1]))
    if not rank:
        raise AssertionError("Original source local one-hop K5 unexpectedly empty")
    best = rank[0][0]
    grouped = [list(ids) for e, ids in rank if abs(e - best) <= 1e-9]
    return {
        "all_K5_subsets_examined": math.comb(20, 5),
        "feasible_count": count,
        "feasible_site_membership_sha256": feasible_sha.hexdigest(),
        "winner_local_positions": grouped,
        "best_energy_under_own_objective": best,
        "top_10": [
            {"local_positions": list(ids), "energy_under_own_objective": e}
            for e, ids in rank[:10]
        ],
        "runner_up_energy": rank[1][0] if len(rank) > 1 else None,
    }


def source_validation(reference, model, w0, out):
    if (reference.get("dataset_sha256") != EXPECTED_DATA_SHA
            or reference.get("archived_notebook_sha256") != EXPECTED_SOURCE_SHA
            or reference.get("scip_status") != "optimal"
            or reference.get("feasible_combinations") != EXPECTED_FEASIBLE
            or reference.get("selected_local_positions") != EXPECTED_BEST
            or reference.get("feasible_site_sets_sha256") != EXPECTED_MEMBERSHIP
            or model.get("candidate_master_feature_positions") != EXPECTED_FREE
            or model.get("fixed_master_feature_positions") != EXPECTED_FIXED
            or digest(model) != reference.get("model_input_sha256")):
        raise AssertionError("Fresh historical source notebook certificate mismatch")
    if (w0["neighbors"] != model["free_neighbor_indices"]
            or w0["fixed_flags"] != model["fixed_neighbor_flags"]
            or out["feasible_count"] != EXPECTED_FEASIBLE
            or out["feasible_site_membership_sha256"] != EXPECTED_MEMBERSHIP
            or out["winner_local_positions"] != [EXPECTED_BEST]
            or abs(out["best_energy_under_own_objective"] - EXPECTED_BEST_E) > 1e-7):
        raise AssertionError("Rebuilt historical W0 graph/exact optimum mismatch")
    coeff_l = [float.fromhex(s) for s in model["linear_float64_hex"]]
    coeff_q = [(i, j, float.fromhex(q)) for i, j, q in
               model["quadratic_ij_float64_hex"]]
    computed_q = [(i, j, float.fromhex(q)) for i, j, q in
                  w0["quadratic_ij_float64_hex"]]
    if (len(coeff_l) != 20 or
            max(abs(a - b) for a, b in zip(
                coeff_l,
                [float.fromhex(s) for s in w0["linear_float64_hex"]]
            )) > 1e-7 or
            len(coeff_q) != len(computed_q) or
            any((i, j) != (a, b) or abs(v - q) > 1e-7
                for (i, j, v), (a, b, q) in zip(coeff_q, computed_q))):
        raise AssertionError("W0 original coefficient numerical/source identity mismatch")


def study(reference):
    source_coords, marked_fixed = source_coordinates()
    if marked_fixed != EXPECTED_FIXED:
        raise AssertionError("Original marked fixed-site identities differ")
    if hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() != EXPECTED_SOURCE_SHA:
        raise AssertionError("Archived historical source notebook SHA changed")
    hull = concave_hull(MultiPoint(source_coords), ratio=.05, allow_holes=True)
    model = reference["model_input"]
    dmax = original_fixed_spacing([source_coords[i] for i in marked_fixed])
    if abs(float.fromhex(model["d_max_m_float64_hex"]) - dmax) > 1e-7:
        raise AssertionError("Dmax no longer matches original fixed station spacing")
    cases = {
        "W0_original": source_case(model, source_coords, hull, delta=1.0),
        "W1_wake_off": source_case(model, source_coords, hull, delta=0.0),
    }
    a = evaluate_case(cases["W0_original"])
    source_validation(reference, model, cases["W0_original"], a)
    b = evaluate_case(cases["W1_wake_off"])
    if a["feasible_site_membership_sha256"] != b["feasible_site_membership_sha256"]:
        raise AssertionError("Changing only wake coefficient altered frozen feasible sets")
    orig = tuple(EXPECTED_BEST)
    alt = tuple(b["winner_local_positions"][0])
    same_site = tuple(a["winner_local_positions"][0]) == alt
    pairs = {
        "original_choice_W0_energy": score(cases["W0_original"], orig),
        "original_choice_W1_energy": score(cases["W1_wake_off"], orig),
        "wake_off_choice_W0_energy": score(cases["W0_original"], alt),
        "wake_off_choice_W1_energy": score(cases["W1_wake_off"], alt),
    }
    if pairs["original_choice_W1_energy"] > pairs["original_choice_W0_energy"] + 1e-10:
        raise AssertionError("Removing nonnegative wake raised original chosen energy")
    report = {
        "schema_version": 1,
        "scope": "openly_posthoc_motivated_n20_W0_vs_W1_delta_only_wake_sensitivity",
        "protocol": "docs/research_protocols/N20_W0_W1_WAKE_ALGEBRA_PREREG_2026_10_19.md",
        "previously_known_wake_off_same_winner": True,
        "not_blind_confirmation": True,
        "model_input_sha256_original_source": reference["model_input_sha256"],
        "original_source_geojson_sha256": EXPECTED_DATA_SHA,
        "archived_original_notebook_sha256": EXPECTED_SOURCE_SHA,
        "cases": {
            k: {**v, "exact_K5": a if k == "W0_original" else b}
            for k, v in cases.items()
        },
        "comparison": {
            **pairs,
            "same_optimal_station_set": same_site,
            "optimal_station_set_Jaccard": len(
                set(a["winner_local_positions"][0]) & set(alt)
            ) / len(set(a["winner_local_positions"][0]) | set(alt)),
            "top_10_overlap_count": len(
                {tuple(x["local_positions"]) for x in a["top_10"]} &
                {tuple(x["local_positions"]) for x in b["top_10"]}
            ),
            "wake_penalty_on_original_winner": (
                pairs["original_choice_W0_energy"] -
                pairs["original_choice_W1_energy"]
            ),
            "wake_free_fixed_positive_pair_count": len(
                cases["W0_original"]["positive_wake_free_fixed_pairs"]
            ),
            "wake_free_free_positive_pair_count": len(
                cases["W0_original"]["positive_wake_free_free_pairs"]
            ),
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "shapely": shapely.__version__,
        },
        "interpretation": (
            "W0 reproduces original signed forward/backward pair terms. "
            "This formula is invariant to east-west reversal as an absolute "
            "alignment threshold; no real hydrodynamic directional W2 was run. "
            "W1 is a previously observed exploratory counterfactual and "
            "does not certify measured lake currents or site quality."
        ),
    }
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite research evidence")
    ref = json.loads(args.reference.read_text(encoding="utf-8"))
    data = study(ref)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(data))
    print("N20_WAKE_W0_W1_CONTROLLED_REPLAY " + json.dumps({
        "W0_K5_feasible": data["cases"]["W0_original"]["exact_K5"]["feasible_count"],
        "W1_K5_feasible": data["cases"]["W1_wake_off"]["exact_K5"]["feasible_count"],
        "W0_optima": data["cases"]["W0_original"]["exact_K5"]["winner_local_positions"],
        "W1_optima": data["cases"]["W1_wake_off"]["exact_K5"]["winner_local_positions"],
        "W0_best": data["cases"]["W0_original"]["exact_K5"]["best_energy_under_own_objective"],
        "W1_best": data["cases"]["W1_wake_off"]["exact_K5"]["best_energy_under_own_objective"],
        "wake_original_winner": data["comparison"]["wake_penalty_on_original_winner"],
        "positive_free_fixed": data["comparison"]["wake_free_fixed_positive_pair_count"],
        "positive_free_free": data["comparison"]["wake_free_free_positive_pair_count"],
        "top10_overlap": data["comparison"]["top_10_overlap_count"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
