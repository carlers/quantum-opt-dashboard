"""Private-loopback, OIDC-authenticated REST interface for bounded research jobs.

SECURITY BOUNDARY: identity is derived only from a signature-verified external
OIDC JWT (issuer + audience + expiry + iat + sub). Never trust an owner field
from the request, request headers, or an unverified JWT claim. This module
cannot bind to public interfaces; no public deployment is authorized.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import PyJWKClient, PyJWKClientError

from problems.water_quality.experiment_jobs import (
    JobError, Spec, export_bundle, read_job,
)
from problems.water_quality.remote_queue import PrivateQueue, QueueError

MAX_BODY_BYTES = 16_384
MAX_TOKEN_LENGTH = 8192
MAX_TOKEN_AGE_SECONDS = 3600
IDEMPOTENCY_RE = re.compile(r"[0-9a-f]{32}\Z")


class IdentityVerifier:
    """Single pinned issuer/JWKS endpoint; asymmetric RS256 signatures only."""

    def __init__(self, *, issuer: str, audience: str, jwks_url: str,
                 jwks_client=None):
        issuer_parts = urlsplit(issuer)
        jwks_parts = urlsplit(jwks_url)
        if (issuer_parts.scheme != "https"
                or jwks_parts.scheme != "https"
                or not issuer_parts.hostname or not jwks_parts.hostname
                or issuer_parts.hostname != jwks_parts.hostname
                or issuer_parts.username or issuer_parts.password
                or jwks_parts.username or jwks_parts.password
                or issuer_parts.query or issuer_parts.fragment
                or jwks_parts.query or jwks_parts.fragment
                or not audience or not audience.strip()
                or issuer != issuer.rstrip("/")):
            raise ValueError("Explicit HTTPS issuer and same-host HTTPS JWKS required")
        self.issuer = issuer
        self.audience = audience
        self.jwks_url = jwks_url
        self.client = (jwks_client if jwks_client is not None else
                       PyJWKClient(jwks_url, cache_keys=False,
                                   cache_jwk_set=True, lifespan=120,
                                   timeout=3))

    def principal(self, token: str) -> str:
        if not isinstance(token, str) or not token or len(token) > MAX_TOKEN_LENGTH:
            raise ValueError("Missing or oversized access token")
        try:
            # Key discovery must not grant authority: decode only with RS256,
            # independently require issuer/audience, and reject missing claims.
            key = self.client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token, key, algorithms=["RS256"], issuer=self.issuer,
                audience=self.audience, leeway=15,
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
        except (jwt.PyJWTError, PyJWKClientError, ValueError, TypeError) as exc:
            raise ValueError("Invalid access token") from exc

        subject = claims.get("sub")
        issued_at, expires_at = claims.get("iat"), claims.get("exp")
        if (not isinstance(subject, str) or not 1 <= len(subject) <= 256
                or not isinstance(issued_at, int) or isinstance(issued_at, bool)
                or not isinstance(expires_at, int) or isinstance(expires_at, bool)
                or expires_at <= issued_at
                or expires_at - issued_at > MAX_TOKEN_AGE_SECONDS):
            raise ValueError("Invalid identity or access-token lifetime")
        # Fixed-length opaque identifier avoids exposing emails and supports
        # OIDC subjects containing '|', '/', colons, etc.
        return "oidc-" + sha256(
            (self.issuer + "\x00" + subject).encode("utf-8")
        ).hexdigest()

    @classmethod
    def from_environment(cls):
        env = ("QOPT_OIDC_ISSUER", "QOPT_OIDC_AUDIENCE", "QOPT_OIDC_JWKS_URL")
        if any(not os.environ.get(name) for name in env):
            raise RuntimeError("OIDC issuer/audience/JWKS must be configured explicitly")
        return cls(issuer=os.environ[env[0]], audience=os.environ[env[1]],
                   jwks_url=os.environ[env[2]])


def create_app(*, queue: PrivateQueue, verifier: IdentityVerifier) -> FastAPI:
    """Construct a PRIVATE API: no docs or CORS; caller controls safe bind."""
    app = FastAPI(
        title="Private quantum optimization jobs",
        docs_url=None, redoc_url=None, openapi_url=None,
    )
    security = HTTPBearer(auto_error=False)

    def owner(credentials: HTTPAuthorizationCredentials | None =
              Depends(security)) -> str:
        if (credentials is None or credentials.scheme.lower() != "bearer"):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                                "Valid bearer token required")
        try:
            return verifier.principal(credentials.credentials)
        except ValueError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                                "Invalid access token") from None

    def existing_job(user: str, job_id: str):
        try:
            row = queue.get(user, job_id)
        except QueueError:
            row = None
        if row is None:
            # Exactly the same result whether missing or another user's job.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiment not found")
        return row

    @app.get("/healthz")
    def health():
        return {"status": "ok", "service": "private-queue-api"}

    @app.post("/v1/jobs", status_code=201)
    async def submit(
        request: Request,
        user: str = Depends(owner),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ):
        if idempotency_key is None or not IDEMPOTENCY_RE.fullmatch(idempotency_key):
            raise HTTPException(400, "Idempotency-Key must be 32 lowercase hex digits")
        if request.headers.get("content-type", "").split(";")[0].lower().strip() != "application/json":
            raise HTTPException(415, "Expected application/json")
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > MAX_BODY_BYTES:
                    raise HTTPException(413, "Experiment request exceeds size limit")
            except ValueError:
                raise HTTPException(400, "Invalid Content-Length") from None
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > MAX_BODY_BYTES:
                raise HTTPException(413, "Experiment request exceeds size limit")
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict) or set(payload) != {"configuration"}:
                raise ValueError("Invalid experiment envelope")
            spec = Spec.from_dict(payload["configuration"])
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            raise HTTPException(422, "Invalid bounded experiment configuration") from None
        try:
            job_id = queue.submit(user, spec, idempotency_key=idempotency_key)
        except QueueError as exc:
            message = str(exc)
            if "Idempotency" in message:
                raise HTTPException(409, "Idempotency-Key was reused with different configuration") from None
            if "capacity" in message:
                raise HTTPException(429, "Per-user or global bounded queue at capacity") from None
            raise HTTPException(503, "Private queue could not accept experiment") from None
        return {"job_id": job_id, "status": queue.get(user, job_id)["status"]}

    @app.get("/v1/jobs")
    def list_jobs(user: str = Depends(owner)):
        return {"jobs": queue.list_for_owner(user)}

    @app.get("/v1/jobs/{job_id}")
    def detail(job_id: str, user: str = Depends(owner)):
        row = existing_job(user, job_id)
        try:
            state = read_job(job_id, root=queue.root)["state"]
        except (OSError, ValueError, KeyError):
            # The queue record still exists; don't falsely claim completion.
            raise HTTPException(503, "Experiment state unavailable") from None
        return {
            **row,
            "progress": {"completed_reads": state.get("completed_reads"),
                         "total_reads": state.get("total_reads")},
            "worker_status": state.get("status"),
        }

    @app.post("/v1/jobs/{job_id}/cancel")
    def cancel(job_id: str, user: str = Depends(owner)):
        existing_job(user, job_id)
        try:
            accepted = queue.request_cancellation(user, job_id)
        except (QueueError, OSError):
            raise HTTPException(503, "Cancellation could not be persisted") from None
        return {"job_id": job_id, "cancellation_requested": accepted}

    @app.get("/v1/jobs/{job_id}/result")
    def result(job_id: str, user: str = Depends(owner)):
        row = existing_job(user, job_id)
        if row["status"] != "completed":
            raise HTTPException(409, "Experiment has no completed result")
        try:
            # Always verify source-model and output SHA256 evidence before use.
            export_bundle(job_id, root=queue.root)
            return read_job(job_id, root=queue.root)["result"]
        except (JobError, OSError, ValueError, KeyError):
            raise HTTPException(503, "Verified experiment result unavailable") from None

    @app.get("/v1/jobs/{job_id}/bundle")
    def bundle(job_id: str, user: str = Depends(owner)):
        row = existing_job(user, job_id)
        if row["status"] != "completed":
            raise HTTPException(409, "Only completed experiments can be exported")
        try:
            archive = export_bundle(job_id, root=queue.root)
        except (JobError, OSError, ValueError, KeyError):
            raise HTTPException(503, "Verified experiment evidence unavailable") from None
        return Response(
            content=archive, media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="research-{job_id}.zip"',
                "Cache-Control": "no-store",
            },
        )

    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8876, type=int)
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "::1", "localhost"):
        parser.error("Only explicit loopback binds are permitted in this foundation")
    if not 1024 <= args.port <= 65535:
        parser.error("Invalid unprivileged TCP port")
    import uvicorn
    queue = PrivateQueue(database=args.database, root=args.root)
    app = create_app(queue=queue, verifier=IdentityVerifier.from_environment())
    uvicorn.run(app, host=args.host, port=args.port, access_log=False)


if __name__ == "__main__":
    main()
