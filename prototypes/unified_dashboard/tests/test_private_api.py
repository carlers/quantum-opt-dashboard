"""Authenticated private API regression: genuine RS256 JWTs and SCIP evidence.

These tests never start a web listener, require Oracle credentials or make a
network call. A dedicated test JWK provider returns the fixture's signing key.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from zipfile import ZipFile

import pytest
# Optional API-only packages are installed by the dedicated authenticated-API
# workflow; existing Streamlit/water CI may collect this test without them.
jwt = pytest.importorskip("jwt")
pytest.importorskip("fastapi")
pytest.importorskip("cryptography")
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from problems.water_quality.experiment_jobs import Spec
from problems.water_quality.private_api import IdentityVerifier, create_app
from problems.water_quality.remote_queue import PrivateQueue

ISSUER = "https://identity.example.test/auth/v1"
JWKS = ISSUER + "/.well-known/jwks.json"
AUDIENCE = "researchers"


@pytest.fixture
def harness(tmp_path):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    class FixtureJWKS:
        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key=private.public_key())

    verifier = IdentityVerifier(
        issuer=ISSUER, audience=AUDIENCE, jwks_url=JWKS,
        jwks_client=FixtureJWKS(),
    )
    queue = PrivateQueue(
        database=tmp_path / "private" / "queue.sqlite3",
        root=tmp_path / "experiments",
    )
    client = TestClient(create_app(queue=queue, verifier=verifier))
    now = int(datetime.now(timezone.utc).timestamp())

    def token(subject, *, issuer=ISSUER, audience=AUDIENCE,
              exp_offset=900, iat_offset=0, algorithm="RS256", key=None):
        claims = {
            "iss": issuer, "aud": audience, "sub": subject,
            "iat": now + iat_offset, "exp": now + exp_offset,
        }
        return jwt.encode(
            claims, key if key is not None else private,
            algorithm=algorithm,
            headers={"kid": "test-kid"},
        )

    def headers(subject, *, idem=None):
        return {"Authorization": "Bearer " + token(subject),
                "Idempotency-Key": idem or uuid4().hex}

    return client, queue, token, headers


def test_issuer_jwks_must_be_https_and_same_origin():
    for options in (
        {"issuer": "http://identity.example.test/auth/v1", "jwks_url": JWKS},
        {"issuer": ISSUER, "jwks_url": "http://identity.example.test/jwks"},
        {"issuer": ISSUER, "jwks_url": "https://attacker.test/jwks"},
        {"issuer": ISSUER + "/", "jwks_url": JWKS},
    ):
        with pytest.raises(ValueError, match="HTTPS"):
            IdentityVerifier(audience=AUDIENCE, **options)


def test_api_requires_valid_signed_identity_and_expected_claims(harness):
    client, _, token, _ = harness
    assert client.get("/healthz").status_code == 200
    assert client.get("/v1/jobs").status_code == 401
    invalid = [
        token("alice", issuer="https://wrong.example.test"),
        token("alice", audience="other-audience"),
        token("alice", exp_offset=-10_000),
        token("alice", iat_offset=3600, exp_offset=3700),
        token("alice", exp_offset=7200),
        token(""),
        token("alice", key=rsa.generate_private_key(
            public_exponent=65537, key_size=2048,
        )),
    ]
    for value in invalid:
        assert client.get("/v1/jobs", headers={
            "Authorization": "Bearer " + value
        }).status_code == 401
    assert client.get("/v1/jobs", headers={
        "Authorization": "Bearer " + "a" * 9000
    }).status_code == 401


def test_owner_scoping_across_list_detail_cancel_result_and_bundle(harness):
    client, queue, _, headers = harness
    sent = client.post("/v1/jobs", json={"configuration": Spec().manifest()},
                       headers=headers("alice"))
    assert sent.status_code == 201, sent.text
    job_id = sent.json()["job_id"]
    assert client.get("/v1/jobs", headers=headers("alice")) .json()["jobs"][0]["job_id"] == job_id
    assert client.get("/v1/jobs", headers=headers("bob")).json()["jobs"] == []
    for url in (f"/v1/jobs/{job_id}", f"/v1/jobs/{job_id}/result",
                f"/v1/jobs/{job_id}/bundle"):
        assert client.get(url, headers=headers("bob")).status_code == 404
    assert client.post(f"/v1/jobs/{job_id}/cancel",
                       headers=headers("bob")).status_code == 404
    assert client.get(f"/v1/jobs/{job_id}", headers=headers("alice")).status_code == 200
    assert client.get(f"/v1/jobs/{job_id}/result",
                      headers=headers("alice")).status_code == 409
    assert client.get(f"/v1/jobs/{job_id}/bundle",
                      headers=headers("alice")).status_code == 409
    assert queue.list_for_owner("bob") == []


def test_idempotency_and_same_key_other_owner_are_independent(harness):
    client, queue, _, headers = harness
    key = uuid4().hex
    data = {"configuration": Spec().manifest()}
    first = client.post("/v1/jobs", json=data, headers=headers("alice", idem=key))
    second = client.post("/v1/jobs", json=data, headers=headers("alice", idem=key))
    assert first.status_code == second.status_code == 201
    assert first.json()["job_id"] == second.json()["job_id"]
    different = {"configuration": Spec(k_new=4).manifest()}
    conflict = client.post("/v1/jobs", json=different,
                           headers=headers("alice", idem=key))
    assert conflict.status_code == 409
    another = client.post("/v1/jobs", json=data, headers=headers("bob", idem=key))
    assert another.status_code == 201
    assert another.json()["job_id"] != first.json()["job_id"]


def test_schema_body_budget_and_content_type_reject_untrusted_config(harness):
    client, _, _, headers = harness
    for payload in (
        {"owner": "bob", "configuration": Spec().manifest()},
        {"configuration": {**Spec().manifest(), "command": "rm -rf /"}},
        {"configuration": {**Spec().manifest(), "n_free": 1000}},
        {"configuration": {**Spec().manifest(), "lambda_budget": -1}},
        {"configuration": {"solver": "scip"}},
    ):
        reply = client.post("/v1/jobs", json=payload, headers=headers("alice"))
        assert reply.status_code == 422, reply.text
    assert client.post("/v1/jobs", json={"configuration": Spec().manifest()},
                       headers={"Authorization": headers("alice")["Authorization"]}
                       ).status_code == 400
    assert client.post("/v1/jobs", content=b"x" * 16385, headers={
        **headers("alice"), "Content-Type": "application/json"
    }).status_code == 413
    assert client.post("/v1/jobs", content=b"{}", headers={
        **headers("alice"), "Content-Type": "text/plain"
    }).status_code == 415


def test_real_scip_run_returns_original_model_evidence_and_verified_zip(harness):
    client, queue, _, headers = harness
    job = client.post("/v1/jobs", json={"configuration": Spec().manifest()},
                      headers=headers("researcher-1"))
    assert job.status_code == 201
    job_id = job.json()["job_id"]
    assert client.get(f"/v1/jobs/{job_id}", headers=headers("researcher-1")).json()[
        "worker_status"] == "queued"
    # The API never dispatches work. A trusted operator explicitly runs one.
    assert queue.run_once(wall_seconds=60) == (job_id, "completed")
    url = f"/v1/jobs/{job_id}"
    assert client.get(url, headers=headers("researcher-1")).json()[
        "status"] == "completed"
    result = client.get(url + "/result", headers=headers("researcher-1"))
    assert result.status_code == 200
    assert result.json()["result"]["source_selection"][
        "selected_source_master_positions"] == [5253, 2394, 1557, 47, 5409]
    bundle = client.get(url + "/bundle", headers=headers("researcher-1"))
    assert bundle.status_code == 200
    assert bundle.headers["content-type"] == "application/zip"
    assert bundle.headers["cache-control"] == "no-store"
    with ZipFile(io.BytesIO(bundle.content)) as archive:
        record = json.loads(archive.read("manifest.json"))
        for name, expected in record["sha256"].items():
            assert sha256(archive.read(name)).hexdigest() == expected
    assert client.post(url + "/cancel",
                       headers=headers("researcher-1")).json()[
        "cancellation_requested"] is False


def test_queued_cancel_persists_without_worker_execution(harness):
    client, queue, _, headers = harness
    job = client.post("/v1/jobs", json={"configuration": Spec().manifest()},
                      headers=headers("researcher-2"))
    job_id = job.json()["job_id"]
    assert client.post(f"/v1/jobs/{job_id}/cancel",
                       headers=headers("researcher-2")).json()[
        "cancellation_requested"] is True
    assert queue.run_once() is None
    assert client.get(f"/v1/jobs/{job_id}", headers=headers("researcher-2")).json()[
        "status"] == "cancelled"
