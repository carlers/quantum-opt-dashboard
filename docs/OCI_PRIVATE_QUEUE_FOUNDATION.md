# Oracle private experiment-queue foundation (review-only)

**Not deployed. No HTTP listener. No automatic job runner. Not safe to expose to external users.**
This implements the first internally testable portion of [issue #151](https://github.com/carlers/quantum-opt-dashboard/issues/151) on top of the local experiments in draft PRs #150 and #154. It does not change the Streamlit preview or the Mosaic VM.

## Verified operator environment (2026-10-28)

The owner confirmed the isolated OCI `QuantumOpt` compartment, Singapore A1 ARM64 Ubuntu 24.04 worker with 1 OCPU / 6 GiB RAM / 50 GB boot volume, plus a dedicated non-login `qopt` account and private `/var/lib/quantum-opt/experiments` storage. Original source SHA-256, real N20/K5 SCIP optimum `-3.3012934918564647` and source selections `[5253,2394,1557,47,5409]`, two SCIP/SA evidence tests and two four-cell sweep tests all passed on ARM64. These are real **restricted original-source model** validations, not manuscript replication, unrestricted N5,417 proof or quantum hardware.

## In this foundation

- `PrivateQueue` persists researcher job ownership and state in **private SQLite WAL**, with transactional FIFO submission, one active claim, 32-byte unpredictable lease fencing token, heartbeats, explicit cancellation and no lease-based automatic retry.
- Every submitted job delegates to the **existing** `Spec.validate` and `create_job`: only bounded SCIP N20/N50/N100 and **classical** OpenJij N20 experiments, with the original source SHA-256 and full independently checked model evidence.
- Owner-scoped `get`, `list_for_owner` and cancellation accept a **trusted server-side owner identity**. An eventual API must obtain that identity from verified authentication claims, not a request body. The current module exposes no network interface.
- The operator-only `run-once` command runs a single original Python worker child (no shell string), with 1-thread BLAS/OMP, CPU/file-size limits, a bounded wall deadline and original output SHA-256 verification. No daemon, scheduled task, user API or public port is installed.
- **Fail closed**: abandoned or expired `running` records remain locked; no new work is claimed until a trusted operator investigates and manually reconciles process and artifact state. Not yet sufficient for a hosted multiuser queue.
- `_sweeps` remains local-only and is **not** accepted by the remote queue yet. Scientific experiment results are not silently synthesized.

### Development-only usage (trusted Linux operator, not a deployment guide)

From a clean checkout of this PR, with root scientific dependencies installed:

```bash
python -m problems.water_quality.remote_queue init \
  --database /path/to/private-state/queue.sqlite3 \
  --root /path/to/private-state/experiments
python -m pytest -q prototypes/unified_dashboard/tests/test_remote_queue_foundation.py
```

Initialization opens a private SQLite database; it does not launch jobs or bind any port. An operator can call `PrivateQueue.submit(trusted_owner, Spec(...))` in a private Python shell during development; `run-once` dispatches **one** queued job. Do not use untrusted arbitrary owner strings or untrusted file paths. No public Streamlit deployment should set `QOPT_LOCAL_EXPERIMENTS=1`.

**Important service-account distinction:** The owner's current repo clone and `.venv` are under `/home/ubuntu`; creating `qopt` and an experiment directory does **not** grant it a readable, reproducible code install or a working systemd unit. Build a pinned dedicated deployment artifact under a restricted, service-readable location before attempting a real `qopt` service. Do not run the prospective service as `ubuntu` or root.

## Blocking work before any remote/public use

1. **Authentication and HTTPS ingress:** choose and verify user identities (e.g. OIDC JWT audience/issuer/JWKS), derive immutable owner IDs server-side, require authorization per operation, strict size-limited request parsing, proper responses and auditing. A shared API token alone is not multi-user authentication.
2. **Independent hard sandboxing:** systemd transient scopes or another mechanism imposing per-job `MemoryMax`, `CPUQuota`, wall limit and process-count quotas. The present Python `RLIMIT_CPU` + wall kill do **not** establish reliable memory isolation.
3. **Durable queue recovery:** supervisor-owned worker PID/process group and heartbeat, atomic reconciler for power loss, audited operator-only stale-job intervention, and fencing against stale workers. Never silently retry native solvers while the old process may still run.
4. **Ownership-safe artifact endpoints and durable backup:** per-job original-model/source hashes, verified ZIP download, persistent off-VM backup or signed object store, restore drills, quotas, disk alerts and retention policy. The 50 GB boot disk is not a resilient archive.
5. **Research UI and end-to-end tests:** authenticated Streamlit-to-backend submit/status/cancel/export, multi-session concurrency, negative authorization tests, interruption and reboot, no-cost controls, request rate limits and abuse handling, all behind a private/HTTPS boundary first.
6. **Scientific scope controls:** preserve original notebook road-based D2 / AHP and 15 fixed stations; explicitly differentiate explored restricted candidate tiers from the paper's WorldPop D2, physical RF connectivity or field validation. Classical OpenJij `SASampler` is not quantum hardware.

Do not merge, deploy, set a public listener, create an external tunnel, enable a service, change the OCI NSG/security-list rules, publish generated archives, or initiate the 9,216-draw confirmatory study without distinct owner approval.
