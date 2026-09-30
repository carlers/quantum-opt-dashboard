# Cache design

Content-addressed, hierarchical.

## Key formula

    stage_key = sha256_json({
      problem,        problem_name
      problem_ver,    problem_version
      stage,          stage.name
      config_slice,   {f: cfg[f] for f in stage.config_deps}
      inputs,         {name: parent_stage_key for name in stage.inputs}
      seed,           job.seed
      code,           job.code_version  (frozen at creation)
      env,            job.env_version   (frozen at creation)
    })

## Layering
- Disk (hot): LRU, bounded bytes.
- R2 (cold): durable.
- Read: disk → R2 → compute.
- Write: compute → disk + R2.

## GC
- Disk eviction: automatic, LRU.
- R2 GC: nightly cron removes blobs whose stage_key isn't
  referenced by a `job_stage_units` row for a job in the last N days.

## Why frozen code/env per job
A mid-job deploy or dependency bump must not silently change cache hits.
Freezing at job creation makes cache hits correct, not coincidental.
