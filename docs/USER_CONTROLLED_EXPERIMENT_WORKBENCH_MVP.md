# User-controlled local experiment runner MVP (review-only)

## What changed

The project's primary workflow is **researcher configures → explicitly runs → inspects → downloads/reproduces**. The original research scripts and CI-science artifacts remain essential *verification fixtures*, not a permanent replacement for a user-run research platform. This feature uses **the existing SCIP original-model solver** and **actual classical OpenJij SA/QUBO implementation**, not mock numerical curves. Both run in a separate Python worker rather than inside Streamlit rerenders.

This is a **draft feature stacked on #143** (read-only source-verified UI) and its source cohort lineage; it is **not deployed** or merged. Original notebooks, water-quality GeoJSON, original N20 page, standalone classical-SA research inspector and CI-science PR #131–#148 are left untouched.

## Local-only operator setup

From a trusted **private** Linux/macOS developer machine:

```sh
python -m pip install -r requirements.txt
export QOPT_LOCAL_EXPERIMENTS=1
# Optional local persistent storage path, separate from git:
export QOPT_EXPERIMENT_STORE="$HOME/.local/share/quantum-opt-dashboard/experiments"
streamlit run prototypes/unified_dashboard/app.py
```

Without the explicit environment flag, **the new page cannot launch workers**. Do not set this flag on publicly accessible Streamlit Community Cloud. It has no login, authorization, quota per tenant, process sandbox, central queue, durable network filesystem, data isolation, institution-hosted compute billing, or robust recovery for crashed hosts. The local default is `.qopt_experiments/` in the repo, which is added to `.gitignore`; host filesystem lifetime determines persistence. Do not treat it as backup or a public research archive.

The sidebar exposes **Run experiments (local)**; on launch, the selected configuration is frozen to a dedicated, locally generated UUID directory. The Streamlit server starts a separate Python process with exactly the checked-in worker module (no shell or user-supplied command), working in the repository root and with BLAS/OMP environment thread limits set to one. **Navigation, refresh and download never invoke a solver.**

## Current bounded controls

- **Exact SCIP**: N20, N50 or N100 original source nested free-candidate tiers; K=1..10; local original one-hop graph; notebook AHP weights and road-proximity D2; optional solver time budget 1..30 seconds. Only `status=="optimal"` means SCIP-proven optimum. A feasible time-limited incumbent remains **feasible, not proven**; no incumbent is a failed bounded run, not a fabricated answer.
- **Classical OpenJij SA**: N20 only, K=1..10, independent numerical `λ_budget` and `λ_connectivity` in 0.01..1000, 1..32 individually seeded one-read OpenJij calls per job, 10..500 sweeps and 32-bit parent seed. All original and auxiliary bits, each child seed, original K/one-hop feasibility, original source objective and augmented energy/offset agreement are retained. Only N20/K5 has the existing pinned exhaustive/SCIP objective comparator.
- **No unbounded N2000 or 9,216-sample confirmatory studies.** Batch sweeps, general arbitrary custom uploads, QAOA hardware, SQA execution, network API, asynchronous cloud jobs and multi-user project sharing are separate future acceptance gates.

## Persistent evidence and honest cancellation

Each local job has `config.json`, `state.json` (queued/running/completed/failed/cancelled), `model.json` (the exact compiled binary64-hex original source model, source candidate feature *array positions*, graph and fixed-site identities), `worker.log`, `result.json`, optional `samples.csv` for OpenJij, optional actual `emitted_scip_model.lp`, and `manifest.json` with SHA-256 digests of immutable scientific outputs. The worker writes staged outputs and only marks a job completed once all required evidence exists. The UI verifies file checksums before exporting a ZIP. Mutable progress/log records are deliberately distinguished from immutable checksum inputs. There is no automatic historical-record deletion or eviction; the MVP bounds local history to 50 jobs to prevent unlimited growth.

**Cancellation is cooperative:** it writes an operator request marker read before and after source reconstruction and after each individual OpenJij sample. SCIP can take up to its user-selected **30-second internal time limit** before cancellation is acknowledged; cancellation does **not** guarantee instant termination of a native solver. A full hard process/cgroup quota, supervisor heartbeat, stale-job recovery, orphan detection and worker reattachment are future reliability gates. This process is not appropriate for shared untrusted hosting.

## Scientific interpretation

A given N20/50/100 run optimizes a **restricted source candidate cohort**, not the entire 5,417-site master problem. The source model uses road-based D2 and notebook weights, which do not exactly match the manuscript's WorldPop D2/AHP description. Model adjacency is not in-situ physical sensor/network feasibility; OpenJij is classical, not quantum; one short job is an exploratory observation, not a statistically preregistered comparison.

**Practical local acceptance:** launch an N20/K5 SCIP run and verify source-selected positions `[5253,2394,1557,47,5409]`, original objective about `−3.3012934918564643`; then launch an N20/K5 classical OpenJij run with two *separate* λ values and two samples. Refresh after worker completion, verify the independent child seeds, full sample rows, feasibility/energy fields and export ZIP manifest. Cancellation and tamper tests must pass in CI; no auto-launch when the page is re-rendered.

## Next product milestones

1. Add **live progress polling, resumable durable job leasing, hard time/memory isolation and authentication** for safe multi-user / remotely deployed research compute; do not enable current local-only flag in hosted preview.
2. Build a **saved-experiment comparison** page and user-requested parameter-sweep batch grid; no automated large study launches. Compare original feasible objective and success metrics *conditional/unconditional as labeled*, never different-λ augmented energies as original objective.
3. Support N50/N100 classical-SA with appropriate coefficient-size/hardware benchmarks and separate scientifically validated scheduling thresholds, then configurable source/formulation problem instances and actual supported quantum solvers (not placeholders).
4. Once provenance/redistribution and institutionally authorized archive are decided, offer durable versioned research-object export without invented DOI or license.

No merges, changes to `preview`/`main`, cloud environment enabling, or production deployment are authorized by this PR.
