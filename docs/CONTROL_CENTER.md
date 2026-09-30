# Control center semantics

## Job lifecycle
queued -> running -> succeeded
                \-> pause_requested -> paused -> queued (resume)
                \-> cancelled
                \-> failed

## Pause
- soft: framework stops at next unit boundary.
- hard: framework sends interrupt signal; plugin checkpoints; unit marked paused.
- none: pause request is deferred; only cancel is honored.

Stage declares its pause support in StageSpec.supports_pause.

## Resume
- Reads job_stage_units; skips done; resumes from first non-done.
- resumed_count++.
- Config edits between pause and resume invalidate cache keys for
  affected stages (framework recomputes keys).

## Edit
- queued: full edit; config_revision++.
- paused: allowed only for fields affecting not-yet-run stages.
  UI shows which stages will be invalidated.
- running/succeeded/failed: disabled. Use Fork.

## Fork
- New job, fork_parent_id set, config_overrides applied.
- Cache reuse for unchanged stages is automatic (content-addressed keys).
- fork_from_stage: only re-run this stage and downstream. Upstream stages
  become dependencies on the parent job's units.

## Sweep (DAG expansion)
- Config field path is swept over N values.
- Framework computes invalidated stages from `config_deps` closure.
- Shared prefix is one job.
- N variant jobs depend on the prefix; each runs invalidated stages.
- Comparison job depends on all variants.
- Scheduler respects job_dependencies.

## Rate limiting
Per-user daily job cap. Configurable via env. 429 on exceed.
