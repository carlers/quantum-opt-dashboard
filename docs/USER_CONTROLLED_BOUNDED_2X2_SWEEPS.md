# User-initiated 2×2 penalty sweeps — bounded local research workbench

**Draft product feature** stacked on PR #150, tracked in issue #153. No source notebook, original GeoJSON, production branch, existing user research model or deployment settings changed. This is a feature for *users to conduct experiments*, not a study run by ChatGPT.

## What researchers can do

On a trusted local Streamlit instance with `QOPT_LOCAL_EXPERIMENTS=1`, open **Run experiments (local)** and expand **Optional · Run a bounded 2×2 QUBO penalty sweep**.

Select independent `λ_budget = [first, second]` and `λ_connectivity = [first, second]`. The user explicitly launches the **full Cartesian product** of four classical SA settings, in deterministic fixed order. Adjust K (1–10), parent seed, individually seeded single-read calls per cell (1–8) and sweeps per read (10–100). These intentionally small hard protocol caps yield at most **4 × 8 × 100 = 3,200 nominal simulated-annealing sweeps**, not the proposed 9,216-draw confirmatory study. There is no automatic launch, rerender/background scheduler, or multiuser job endpoint.

Each grid cell becomes a separate, original-source-verified `Spec(solver="classical_sa", N_free=20, K=...)` job in the existing local worker engine. Parent seeds are deterministically derived using `SeedSequence([parent_seed, cell_index]).generate_state(1)`; within each cell the original OpenJij code derives distinct child seeds using `SeedSequence(cell_parent).spawn(reads)` and makes **one independent sampler call per read**. All original and auxiliary bits, original raw energy, original exact-K/local-one-hop feasibility and actual returned energies are preserved. The four cell original-model SHA-256 digests **must match bit-for-bit** before the sweep is completed.

The sweep is its **own detached Python worker process**. Its state in `.qopt_experiments/_sweeps/<uuid>/` includes immutable `config.json`, mutable `state.json`, and `worker.log`. Progress reports 0–4 completed cells and the active child job; the user can request cancellation (propagated to the current child at individual-read checkpoints). Completed experiments produce `result.json`, `cells.csv`, four per-cell original-job ZIPs and a SHA-256 `manifest.json`. A sweep export ZIP contains each one-read state and child model/evidence. Child jobs also appear individually in the original single-experiment history so the user can analyze and compare each one with the existing original-model-hash guard. No experimental results appear on a blank dashboard, and no optimizer is called during visualization.

The same local `.launch.lock` synchronizes standalone job launches and sweep job launches. A queued/running standalone job prevents a sweep from launching, and a queued/running sweep prevents a standalone job from launching. The sweep runner creates child research records directly inside its own single worker rather than launching four competing subprocesses.

## Honest interpretation and limits

The results table shows **observed original-feasible / total sampled draws**, per-cell original feasible fraction and best original feasible objective. The 2×2 matrix is descriptive only and never selects a winning λ from four tiny cell samples. Never compare different λ *augmented* QUBO energies as if they were original feasible objective values. No confidence interval, preregistered study, independent parent-block inference, quantum hardware execution, QAOA or physical/field water-quality validation is claimed.

The source model remains historical notebook AHP weights, road-based D2, 15 originally marked existing lake stations and the original local one-hop condition. It is not fully reconciled with the published paper's population/WorldPop D2 input or original OMMX/JijModeling compiler.

**Local-only security scope:** no login, quota-per-user, hard memory/wall sandbox, server job recovery, durable cloud storage, billing guard, user tenant isolation or remote compute permission. Never set the enabling environment variable on publicly accessible Streamlit Community Cloud. Workers execute only fixed checked-in Python entrypoints, never user-supplied commands. Full archives and logs are stored in the local ignored directory; this is **not** a durable public DOI/academic archive. Canceled/interrupted sweeps retain their child job directories and state, but only a successfully verified completed sweep has a final ZIP export. Abrupt machine shutdown requires manual operator recovery; no false automatic success.

## Acceptance and next milestones

CI tests one **genuine** four-cell OpenJij sweep (1 read × 10 sweeps each) and another real detached worker execution. It verifies four independent derived parent seeds, all four complete source-validated child job ZIPs, identical source model hashes, SHA-256 output chain, tamper rejection, queued job/sweep lock exclusion, safe cancellation and inherited existing bounded job source regressions.

Next milestones are multiuser authentication, durable queue leases/heartbeat and crash recovery, safe remote workers/resource quotas, persistent object storage, flexible grid experiments with user-configured bounds, and statistical analyses that label inferential vs descriptive data clearly. The much larger proposed study in #146 still needs scientific and resource approval.

**Nothing here authorizes merging, enabling public execution or deploying production compute.**
