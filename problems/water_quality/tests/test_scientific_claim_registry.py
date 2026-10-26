"""M0 scientific claim ledger: source evidence and non-claims are enforceable."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from problems.water_quality.nested_resolution import (
    REFERENCE_GEOJSON, build_nested_instances,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "scientific_claim_registry.json"
SOURCE_SHA = "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"


@pytest.fixture(scope="module")
def claims():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert registry["schema"] == "water-quality-source-claim-registry-v1"
    return registry


def test_preserved_source_hash_and_original_notebook_provenance(claims):
    data = claims["original_inputs"]["geojson"]
    assert data["path"].endswith("LDB_centroids_clean.geojson")
    assert data["sha256"] == SOURCE_SHA
    assert sha256(REFERENCE_GEOJSON.read_bytes()).hexdigest() == SOURCE_SHA
    assert data["feature_count"] == 5417
    assert data["flagged_fixed_stations"] == 15
    assert data["d2_factor_in_committed_source"] == "road_proximity"
    notebook = claims["original_inputs"]["notebook"]
    assert notebook["preserve_original"] is True
    assert notebook["code_cell_count"] == 25
    assert notebook["git_blob_sha1"] == "a554f4f37957e924c0ed417e53af2dab04e45ffa"


def test_claims_are_tied_to_actual_original_local_model_not_paper_inputs(claims):
    study = build_nested_instances(tiers=(20, 50, 100))
    assert study.source_sha256 == SOURCE_SHA
    assert study.source_feature_count == 5417
    assert len(study.fixed_master_positions) == 15
    assert study.fixed_simulated is False
    assert [x.n_free for x in study.tier_instances] == [20, 50, 100]
    assert tuple(study.tier_instances[0].candidate_master_positions) == tuple(
        study.tier_instances[2].candidate_master_positions[:20]
    )
    assert tuple(study.tier_instances[1].candidate_master_positions) == tuple(
        study.tier_instances[2].candidate_master_positions[:50]
    )
    n20 = study.tier_instances[0].instance
    witness = np.zeros(20, dtype=np.int64)
    witness[[0, 1, 3, 6, 7]] = 1
    assert int(witness.sum()) == 5
    assert all(not witness[i] or int(n20.fixed_neighbors[i])
               or any(witness[j] for j in n20.neighbors[i])
               for i in range(20))
    direct = sum(float(n20.linear[i]) for i in np.flatnonzero(witness))
    direct += sum(float(v) for i, j, v in n20.quadratic
                  if witness[i] and witness[j])
    declared = claims["model_scope"]["small_scale_exact_reference"]
    assert declared["tier_n"] == 20
    assert declared["selected_local_positions"] == [0, 1, 3, 6, 7]
    assert direct == pytest.approx(declared["source_objective"], abs=1e-7)
    assert declared["feasible_local_one_hop_subsets"] == 1077
    global_only = claims["model_scope"]["distinct_global_counterfactual"]
    assert global_only["feasible_subsets"] == 860
    assert global_only["do_not_pool_with_local"] is True


def test_each_positive_claim_is_bounded_to_source_only_and_has_review_pointer(claims):
    expected = {
        "E-N20-L", "E-M1-COHORTS",
        "E-N50-SCIP-HIGHS", "E-N100-SCIP-HIGHS", "E-M2-PILOT",
    }
    records = claims["evidence_claims"]
    assert len(records) == len(expected)
    assert {x["id"] for x in records} == expected
    assert all(x["status"] in (
        "source-computational-verified", "reviewed-single-ci-execution",
        "pilot-engineering-observation-not-inferential"
    ) for x in records)
    assert all(x["not_physical_deployment"] is True for x in records)
    assert all(x["source_url"].startswith(
        "https://github.com/carlers/quantum-opt-dashboard/pull/"
    ) for x in records)


def test_prohibited_claims_are_explicit_false_and_cannot_be_misread_as_validation(claims):
    banned = {x["id"]: x for x in claims["prohibited_claims"]}
    assert set(banned) == {
        "PAPER-PARITY", "WIRELESS-FIELD", "QUANTUM-SPEEDUP",
        "STAT-SCALING", "MASTER-OPT",
    }
    assert all(x["allowed"] is False and len(x["reason"]) > 25
               for x in banned.values())
    assert claims["original_inputs"]["uploaded_manuscript"][
        "source_data_parity_proven"
    ] is False
    assert claims["model_scope"]["paper_input_reproduced"] is False
    assert claims["original_inputs"]["geojson"]["d2_factor_in_committed_source"] != (
        "population_exposure_WorldPop_reported_by_manuscript"
    )


def test_unsettled_license_publication_and_doi_are_not_assumed(claims):
    fields = claims["experiment_boundary"]
    assert len(fields["experiment_manifest_required"]) >= 14
    assert fields["data_license_checked"] is False
    assert fields["public_distribution_approved"] is False
    assert fields["durable_repository_selected"] is False
    assert fields["doi_assigned"] is False
    assert claims["status"].startswith("draft-")
