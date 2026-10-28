# Private OIDC experiment API and cgroup design — review only

**Status:** DRAFT, NOT DEPLOYED. Stacked on [#155](https://github.com/carlers/quantum-opt-dashboard/pull/155), which is stacked on #154/#150. No running network service, no Oracle or Mosaic changes, no Streamlit public flag, and no owner authorization to publish experimental archives.

The owner already validated real SCIP, HiGHS, OpenJij and the N20 reference model on their independent Oracle Ubuntu 24.04 ARM64 A1 research VM, with 1 OCPU, 6 GB RAM, 50 GB disk. This PR does not claim to have remotely installed anything there.

## Authentication boundary

`problems.water_quality.private_api.IdentityVerifier` requires three explicit operator-provided values (NONE committed or defaulted):

- `QOPT_OIDC_ISSUER`: exact HTTPS issuer string, e.g. `https://your-tenant.example/auth/v1` (no trailing slash).
- `QOPT_OIDC_AUDIENCE`: exact access-token audience, **not** a redirect URL or a public API secret.
- `QOPT_OIDC_JWKS_URL`: HTTPS JWKS URL on the *same hostname* as the issuer. No token-supplied JWKS URL or JKU accepted.

The API validates an **RS256 signature** using the pinned JWKS client, and validates `iss`, `aud`, `sub`, `iat`, `exp`. Maximum lifetime is 3600 seconds, with 15-second allowed clock skew and 8 KiB token cap. An opaque owner ID is SHA256 of exact issuer + delimiter + verified OIDC `sub`. The request never accepts a client-supplied owner ID or executable command.

There are currently no login screens, token refresh flows, configured identity providers, user/group permissions or Streamlit Cloud integration. **Do not paste bearer tokens, private keys, or signing keys into GitHub/issues/this chat.** Never commit `/etc/quantum-opt/private-api.env`. JWKS origin and private ingress need owner review before activation.

## Bound API contract (loopback only)

Default CLI host is `127.0.0.1`; binding to `0.0.0.0` or an arbitrary interface is rejected. OpenAPI/docs and CORS are disabled, and no reverse proxy/tunnel is deployed. Authentication required on all endpoints except `GET /healthz`.

| Endpoint | Function |
|---|---|
| `POST /v1/jobs` | Enqueue one exact `Spec` config with mandatory 32-hex `Idempotency-Key` header; 16 KiB JSON maximum; no subprocess launches |
| `GET /v1/jobs` | List the authenticated subject's jobs only |
| `GET /v1/jobs/{id}` | Owner-scoped queue status and current worker progress |
| `POST /v1/jobs/{id}/cancel` | Owner-scoped cooperative cancellation |
| `GET /v1/jobs/{id}/result` | Only completed result; re-verifies original evidence hashes |
| `GET /v1/jobs/{id}/bundle` | Completed source ZIP, checksum-verified and returned without browser caching |

Missing and cross-owner jobs return the same 404. A repeated idempotency key and byte-equivalent normalized `Spec` returns the original job ID; using the same key with another configuration is a conflict. Per-owner/global queued+running job caps still apply to new submissions. No `owner`, shell, arbitrary input file or unbounded scientific N-tier can be submitted.

Example **JSON body for a future authenticated client** (not a live endpoint):

```json
{
  "configuration": {
    "solver": "scip",
    "n_free": 20,
    "k_new": 5,
    "time_limit_seconds": 15,
    "reads": 4,
    "sweeps": 300,
    "parent_seed": 20261026,
    "lambda_budget": 12.9,
    "lambda_connectivity": 12.9
  }
}
```

## Operator-only bounded subprocess and systemd templates

The code stays in a **separate pinned install** under `/opt/quantum-opt/repo`, venv in `/opt/quantum-opt/venv`, owned by a privileged maintainer, readable but not writable by `qopt`; writable SQLite WAL and jobs in `/var/lib/quantum-opt` must be `qopt`-owned and mode 0700. The current development checkout under `/home/ubuntu` cannot simply be used by the `qopt` service.

Uninstalled files:

- `deploy/systemd/quantum-opt-private-api.service` — runs API as `qopt`, loopback-only, 512 MB service cgroup.
- `deploy/systemd/quantum-opt-private-worker.service` — one sequential `run-once` dispatch as `qopt`, private network, `MemoryMax=2G`, `MemorySwapMax=0`, `TasksMax=64`, `CPUQuota=100%`, 100-second start/wall control, cgroup kill, read/write paths restricted.
- `deploy/systemd/quantum-opt-private-worker.timer.example` — optional future scheduler, **not** installed or activated.

These units were **statically inspected in CI only**. A live Ubuntu 24.04 systemd/cgroup v2 smoke test must prove real native solver execution, enforced out-of-memory/process cleanup, unexpected worker kill/reboot behavior and no wider VCN exposure. Worker `run_once` uses `RLIMIT_CPU` and a 90-second Python wall limit as an additional guard. The systemd cgroup is the *planned hard memory boundary*; the Python limits alone do not provide it.

**No automatic lease reclaim or retry**: an expired running claim blocks further dispatch until an authorized operator verifies the old native process is dead, inspects source/evidence, and reconciles the job. This is deliberate to avoid silent duplicate physical computations. Verified off-VM artifact backup and recovery/runbooks are still blockers.

## Local CI / test-only commands (no background job service)

```bash
python -m pip install -r requirements-private-api.txt
python -m pip install "pytest>=8,<10"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest -q \
  prototypes/unified_dashboard/tests/test_private_api.py \
  prototypes/unified_dashboard/tests/test_remote_queue_foundation.py
```

The JWT tests sign actual fixture RS256 tokens, including wrong issuer/audience, expired/future/oversized, wrong key and cross-owner read/cancel/export rejection. Real N20 SCIP process dispatch and SHA256 evidence export are exercised. **CI tests are not an independent published sensor-placement study.**

## Still required for hosting (issue #151)

Provider-backed OIDC login/refresh and trusted proxy/HTTPS access from Streamlit; provider JWKS rotation/revocation tests; secure API-to-UI token flow and CSRF policy; production idempotency and rate-limit proof; resilient stale-job recovery and audited operator reconciliation; off-machine backup and restore exercises; login/logout and two-session browser tests; hard-cgroup validation on the owner's VM; alerts and costs; manual approval before modifying any live networking or production branch.

The lake model still uses the original source's road-proximity D2 and notebook weights, not a validated historical WorldPop manuscript reconstruction. N20/N50/N100 restrict to source-derived candidates, and OpenJij runs **classical** simulated annealing.
