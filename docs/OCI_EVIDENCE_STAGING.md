# Original-science evidence staging and restore drill (review-only)

**Not a live backup or public release.** Stacked on draft #156 and #155. This draft introduces an **operator-only** local staging tool for immutable research ZIP evidence, before a separate approved transfer mechanism can deposit the files off the VM. No network calls, provider credentials, new storage bucket, automatic schedules, service enablement or dashboard changes.

## Purpose and scope

Original scientist-triggered experiments may record native SCIP, classical OpenJij samples and their own source/model checksums. `problems.water_quality.evidence_archive` stages **only queue-completed jobs**, verifies the original SHA-256 chain, and writes two private append-only files per job:

- `<job-id>.zip` — the original ZIP, containing `config.json`, `model.json`, `result.json`, the original `manifest.json` and solver-specific LP or `samples.csv` when present.
- `<job-id>.sha256.json` — archive SHA-256, original source/model hashes and size, plus a warning that the artifact is not off-VM until moved and independently reverified.

Both files must remain confidential (directory 0700, files 0600). The operator CLI never overwrites an existing copy; an interrupted stage can leave an incomplete pair which verification rejects. A manual operator must investigate before removing files. No queue-record restoration or job retry is provided.

Validation checks every ZIP member name, duplicate, type and size, the original science-file manifest SHA-256 values, original source hash, model hash and job ID. It refuses an archive whose inner science data has changed even if someone updates the outer sidecar checksum. The restore drill extracts only after verification into a **new private folder**, never overwrites an existing location, and does not recreate job status or ownership.

## Development commands (do NOT run against the real private queue without separate approval)

```bash
python -m pytest -q prototypes/unified_dashboard/tests/test_evidence_archive.py
```

Examples for an already-approved operator-maintained *completed* job, in a private isolated environment:

```bash
python -m problems.water_quality.evidence_archive stage \
  --database /private/state/queue.sqlite3 \
  --root /private/state/experiments \
  --job 0123456789abcdef0123456789abcdef \
  --destination /private/staging/research-evidence

# Execute on the destination machine AFTER transferring both files:
python -m problems.water_quality.evidence_archive verify \
  --job 0123456789abcdef0123456789abcdef \
  --destination /private/staging/research-evidence

# Independent read-only evidence inspection (not queue restore):
python -m problems.water_quality.evidence_archive restore-drill \
  --job 0123456789abcdef0123456789abcdef \
  --destination /private/staging/research-evidence \
  --restore-into /private/rehearsal/recovered-job
```

The job ID above is illustrative. This PR does **not** implement transferring files to OCI Object Storage, encrypting archives with tenant-managed keys, backup lifecycle policy, identity and authorization for archived data, DB/WAL recovery, a scheduled backup, verified retention, or queue restoration. Those remain release blockers for issue #151.

## Off-VM acceptance plan (future distinct authorization)

1. Agree on storage region, compartment, bucket visibility (strict private), cost/retention policy, disaster recovery needs, institution research-data policy and IAM instance principals or workload identity. Do not use a public bucket or a pre-authenticated public URL.
2. Pin a supported transfer client with read/write IAM narrowly scoped to one research bucket/prefix. Transfer **both** archive and sidecar and compare SHA-256 checksums after fetching them *on another machine*.
3. Prove complete restoration from an inaccessible/destroyed local cache. Record the object version IDs, manifests, transfer attempts and a restore rehearsal in a protected operator log; do not disclose researcher data.
4. Add queue metadata/database snapshot strategy (SQLite online backup, schema and ownership checks, WAL recovery, idempotency ledger) and audited manual terminal reconciliation of abandoned claims. **Do not auto-retry native solvers after restart.**
5. Verify private storage permissions and quotas for both upload identity and researcher download identity. Only then enable any automated backup.

Scientific caution: restricted original-source N20 reference, not a WorldPop D2 manuscript parity claim, field validation or quantum hardware run.
