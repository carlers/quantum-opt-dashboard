# Exact-seed frozen-profile replay: two successful CI artifact comparison (2026-10-26)

**Question answered:** Did two separate CI workflows produce the same bitwise source model, QUBO coefficients, sampler child seeds and original-plus-auxiliary samples after freezing N20 source coefficients and pinning BLAS/OMP thread counts? **Yes, for these two executions.** This is a reproducibility *engineering gate*, not an independent statistical replication.

**Source runs** (retrieved and compared as original artifact ZIP bytes):
- Classical 3×3 runner: [GitHub Actions run 40314225342](https://github.com/carlers/quantum-opt-dashboard/actions/runs/40314225342), artifact `12646151272`, outer ZIP SHA-256 `73185f13d396475b058232624b2e343c162038872591f10f4b1a0de432c9fd8d`.
- Independent sample-auditing heatmap pipeline: [GitHub Actions run 40314233600](https://github.com/carlers/quantum-opt-dashboard/actions/runs/40314233600), artifact `12645548837`, outer ZIP SHA-256 `70a8607982ee05bab44e5d9450ee37d3998206eb2fecee4b81e04ba89778f792`.

**Exact comparable inner bytes:** each carries `compiled_source_model.json` with SHA-256 `add84856f0f933eecd4a82b615c239430a85e524d7f00d796c4753f7b4ba4101`, and `samples.csv` with SHA-256 `2a446a313224e1dd...` (the latter is shown here as a prefix; retrieve its full value from the original checksum manifests). Both copies of **each file are byte-identical**, not just numerically close. The `samples.csv` equality covers **all 72** parent×grid×read rows, individual child seeds, all original and auxiliary bits, complete raw QUBO energies and original objectives, penalties, constraint statuses, and complete QUBO coefficient hashes. All nine grid-specific QUBO hashes and all 72 child seeds match exactly. All original source models have N20, K5, 15 flagged stations, historical notebook weights and road-proximity D2.

**Verified feasible counts** per cell, each denominator **8** (budget λb rows × connection λc columns, both: row-sum heuristic, midpoint, conservative global):
```
6/8   2/8   0/8
2/8   6/8   4/8
0/8   2/8   5/8
```
No optimum-hitting sample was seen. **Do not infer an optimal penalty or statistical effect from these 72 draws.** A mathematical sufficient penalty is not a finite-sweep SA success guarantee.

**Expected differences:** `summary.json` differs in the `software.github_sha` field (different CI commit being tested); `trials.csv` differs in measured `sampler_wall_seconds`. Thus ZIP bytes, summary metadata/checksums and parent-trial timing bytes differ **correctly**. It would be unsound to assert the complete archives are identical or to treat two deterministic replays as 144 independent stochastic outcomes.

**Earlier numerical drift remains documented:** before freezing the numeric profile, different runner environments produced one-ULP differences in derived source coefficients and in row-sum λ heuristic. Fix: the **explicit, version-controlled** `problems/water_quality/data/n20_frozen_classical_penalty_profile_v1.json` with SHA-256 `add84856f0f933eecd4a82b615c239430a85e524d7f00d796c4753f7b4ba4101` is checked against regenerated original source identity, topology and coefficient differences within 1e-12. The original standalone N20 SCIP/model/GeoJSON and manuscript files are unchanged. `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS` are all set to `1`. A frozen numerical comparator is **not** a bitwise identity claim about every possible original source regeneration.

**Remaining gates:** automate this comparison across two fresh executions; preserve both artifacts long-term under an approved license/archive; obtain explicit approval for the pilot-informed, prospectively frozen larger-study design in issue #146 before any 9,216-read batch. GitHub artifact retention is 14 days, and these two replays are *not* independent parent blocks beyond the original two seeds.
