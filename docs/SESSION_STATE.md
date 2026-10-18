# Current scoped milestone — preregistered paired-seed SA replication (2026-10-18)

- Scope: [issue #22](https://github.com/carlers/quantum-opt-dashboard/issues/22) preregistered **before results**, on isolated `science-sa-paired-replication` stacked above unmerged PR #21. New draft PR targets `science-openjij-sa-benchmark`, not the live Streamlit branch.
- Registered design: **32 NEW parent seeds `270010001..270010032`**, 32 independently child-seeded single reads per parent × 3 **unchanged** QUBO penalty configurations, **300 sweeps/read**, total **3,072 samples** from OpenJij 0.12.2 classical SA.
- Primary outcome: *original-feasible AND exact SCIP-optimum hit* (1e-7), denominator all samples including infeasible. Secondary: original feasibility. Report two paired differences against row-sum penalty, each with descriptive **10,000-resample parent-seed-block percentile bootstrap** intervals, fixed bootstrap PRNG seed 734021; no significance or generalization claim.
- Implementation: `sa_paired_replication.py`, `tests/test_sa_paired_replication.py`, `SA_PAIRED_REPLICATION.md` and scoped GitHub Actions artifact `n20-sa-paired-replication`.
- Independent SCIP 20-choose-5 certification and historical source checksums retained. No original notebook, GeoJSON, deployed app, model, or paper modification. Unresolved paper provenance issue #16.
- **Validation gate:** New branch CI compiles, passes existing tests plus synthetic paired bootstrap tests, executes the immutable 3,072-read protocol and uploads JSON/CSV/SHA manifest. Record exact run, sample counts, bootstrap results after actual verification. No live merge/deploy without user approval.

---

# Active scientific checkpoint — seeded OpenJij N20 benchmark (2026-10-18)

- Scope: [issue #20](https://github.com/carlers/quantum-opt-dashboard/issues/20), draft PR #21 on non-live `science-openjij-sa-benchmark` stacked above PR #19 (exact QUBO).
- **Verified first fully independent-read CI:** [run 39096176060](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096176060), SHA `c173d34e0afd814b0e9f568ee40d12dca1de06ee`. All **26** Python tests passed, 3×3×32-read OpenJij SA CLI completed, prior SCIP evidence workflow completed, and both evidence archives uploaded.
- Packages: OpenJij classical SASampler pinned to **0.12.2**; other runtime versions in benchmark `summary.json`.
- Crucial methodological fix: a prior `num_reads=32` call reusing one seed appeared to repeat original placement patterns; superseded this with **32 separate num_reads=1 calls with 32 distinct logged child seeds** derived via NumPy SeedSequence from each parent seed. All final reported benchmark counts use the corrected scheme.
- N20=20 free, K5, 15 real fixed stations, notebook weights. SCIP proven energy −3.3012934918564643 and selected local indices [0,1,3,6,7]; independent enumeration agrees. All 3 penalty settings report 96 classical SA draws each:
  - Notebook row-sum P=1.0978196676270329: **67/96 feasible**, best feasible −3.3012934918564643 (6 exact hits).
  - Midpoint P=12.92646186401367: **80/96 feasible**, best feasible −3.1020113800145808 (0 exact hits).
  - Sufficient global P=24.755104060400306: **81/96 feasible**, best feasible −2.7834182199112294 (0 exact hits).
- Verified machine-readable [SA artifact](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096176060/artifacts/12125230062) contains summary/trial/sample detail and checksum manifest; [SCIP artifact](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096176060/artifacts/12125260030) retains reference provenance.
- Results are **exploratory** due to 3 parent seeds and 96 draws per point. QUBO is our explicit slack encoder, not the paper's unverified JijModeling converter. No quantum advantage, no publication parity or rigorous stochastic superiority claim.
- Historical AHP and paper-input provenance remain under #16; next research step is preplanned larger/more diversified stochastic trials, solver formulation review, or conceptual evacuation-center model work, after appropriate scoped issue.
- **Deployment safety:** live `plugin-water-streamlit-pilot` branch and default `main` remain untouched. No merges/deployment without explicit user permission.

---

## Earlier scoped scientific checkpoints

# Active scientific-validation checkpoint (2026-10-18)

- **Current task:** issue #18 — exact auxiliary-slack QUBO encoding, after headless N=20 SCIP evidence PR #17. Branch `science-qubo-exact-encoding`, stacked on `science-headless-evidence-export` (draft PR #17; non-live).
- **Changes:** `prototypes/streamlit_water_quality/qubo.py`, `tests/test_qubo.py`, `QUBO_ENCODING.md`. Correctness-first independent quadratic encoding of budget and per-site local connectivity constraints, with sufficient global penalties and exhaustive tiny-instance bit enumeration. No stochastic SA claims yet.
- **Verification gate:** scoped GitHub Actions Python syntax and all pilot tests, including QUBO; review outcome and failures before claiming validated.
- **Known verified SCIP baseline:** notebook-weight N=20/K=5 = −3.3012934918564643, selected local indices [0,1,3,6,7], 15 existing real stations; full evidence JSON/CSV from PR #17. Paper mathematical/provenance disagreements tracked in issue #16.
- **Safety:** live deployment branch `plugin-water-streamlit-pilot` at `e383d1f887eded3e808dd4dec909dc6283b01a5e`; no merge or deployment without explicit user approval. Original notebook, GeoJSON, paper, and existing SCIP model remain intact.
- **After review:** seeded, repeated OpenJij SA evaluation with explicit penalty sweeps and independently checked feasibility, as a separate follow-up task.

---

## Historical scientific checkpoint from preceding PR

# Active checkpoint: headless N20 evidence export (2026-10-18)

## Current task
Draft PR [#17](https://github.com/carlers/quantum-opt-dashboard/pull/17), branch `science-headless-evidence-export`, stacked on `science-n20-scip-parity` (draft PR #15). Add automated, archived, reproducible N=20 SCIP JSON/CSV evidence to remove dependency on manual Streamlit interaction. No changes to live `plugin-water-streamlit-pilot`; user approval required before any merge that can update the deployed app.

### Scoped changes
- `prototypes/streamlit_water_quality/evidence.py`: headless 3-scenario N20 (K=5) SCIP runner, exact enumeration, explicit objective decomposition and independent feasibility checks; export config, numerical instance, results and candidate sites to JSON/CSV with SHA-256 provenance manifest.
- `prototypes/streamlit_water_quality/tests/test_evidence_export.py`: scenario IDs, all 15,504 combinations, zero-feasible-case rejection, complete export schema and checksums, golden energies, tamper detection.
- `.github/workflows/streamlit-pilot.yml`: automatically generate and upload artifact `n20-scip-evidence` (14-day retention) on scoped PR CI.
- `prototypes/streamlit_water_quality/HEADLESS_EVIDENCE.md`: run instructions, schemas, epistemic boundaries.

### N20 scientific reference retained
- 5,417 GeoJSON records; 15 actually flagged fixed stations.
- Original notebook AHP weights: SCIP optimum **−3.3012934918564643**, selected local indices **[0,1,3,6,7]**.
- Published Table IV AHP weights on same data: **−3.473640036773477**.
- Hypothetical Table III principal-eigenvector priorities: **−3.629863700075275**.
- The published paper's SCIP result −3.301319 is not proven to arise from the committed input files. Historical AHP and solver uncertainties tracked at issue #16.

### Review gates
- [x] Current branch CI passed: https://github.com/carlers/quantum-opt-dashboard/actions/runs/39072903613 — **17 tests passed**, CLI ran all three scenarios, archive upload succeeded (artifact ID 12115499202). Archive: https://github.com/carlers/quantum-opt-dashboard/actions/runs/39072903613/artifacts/12115499202. Evidence coefficients and settings validated by CI; hosted Streamlit app itself was not tested.
- [ ] Record final head SHA and CI verification in PR #17 and issue #12 after final documentation commit.
- [ ] Do not deploy or merge to `plugin-water-streamlit-pilot` without explicit user approval.
- [ ] Original Streamlit app's real N20 output and historical paper-era solver inputs remain unverified; neither blocks the automated cold-build evidence generation.

---

## Previous N20 scientific validation checkpoint

# Active scientific-validation checkpoint (2026-10-18)

- Active priority: N=20 water-quality original-notebook → pilot SCIP scientific parity; see roadmap #2, issue #12 and #6.
- Live deployment branch: `plugin-water-streamlit-pilot` (do not update or merge without user approval).
- Earlier draft PR #13 targets `main`; PR #14 targets live branch but remains unmerged.
- Current scoped work: `science-n20-scip-parity` is stacked on PR #14's unmerged head; new PR targets `plugin-water-scip-regression`, which is **not** live.
- **Verified CI:** https://github.com/carlers/quantum-opt-dashboard/actions/runs/39071712498 — 14 tests passed, including N20 reconstruction and independent exhaustive enumeration against real SCIP for three AHP scenarios, plus reconstructed paper AHP-matrix arithmetic.
- Baseline (notebook weights): SCIP optimal −3.3012934918564643 at local indices [0,1,3,6,7], 15 *actual* flagged stations; paper reports −3.301319 with identical selections; numeric delta +0.0000255081435356. Paper-weight sensitivity: −3.473640036773477, same selections. Do not claim exact paper reproduction.
- Adds independent source-formula/geometry reconstruction, exhaustive 20-choose-5 reference and real SCIP regression tests; scientific evidence document: `prototypes/streamlit_water_quality/N20_VALIDATION.md`.
- This branch makes no solver/UI/data/notebook changes. No claims of paper parity until exact paper inputs and notebook cache provenance can be verified.
- User-confirmed working Streamlit URL: https://v3wzqpbn8w6nmdgkxh5kum.streamlit.app/.
- Paper AHP numerical audit: Table III principal eigenvalue 4.147126421479674 (CR 0.0544912672) versus paper-reported 4.2207 (CR 0.0817). Reported values arise from applying mean((A*w)/w) to the **Table IV** pillar weights, which are not Table III's principal eigenvector. New counterfactual N20 optimum using Table III-derived priorities: **−3.629863700075275**, same local selected indices [0,1,3,6,7]; not a historical result. See `tests/test_paper_ahp_consistency.py` and N20_VALIDATION.md; preserve published figures as evidence rather than silently overwriting them.
- Next: investigate missing paper AHP elicitation/provenance and historical original SCIP config behind energy delta; capture live app N20 settings/output. Approval required before any merge to live Streamlit.

---

## Historical scaffold checkpoint (2026-09-30; superseded by issue #2 / #12)

Updated: 2026-09-30
Current task: Scaffold committed. Next: FC1 (Problem protocol + schemas).
Status: Repo pushed to GitHub. Source data and reference notebook committed.
No feature branches open yet.

## Completed
- Monorepo scaffold (framework/, problems/, apps/, contracts/, docs/).
- Source geojson at `problems/water_quality/data/`.
- Reference notebook at `problems/water_quality/notebooks/`.
- CI workflows: framework.yml, water-quality.yml, frontend.yml, worker-image.yml.

## Next tasks (in order)
- `framework-problem-protocol` — Problem, StageSpec, contexts, Tracker.
- `framework-plugin-registry` — Entry-point discovery.
- `framework-cache-keys` — Cache-key derivation from StageSpec.
- `framework-cache-storage` — Disk + R2 tiered cache.
- `framework-stage-executor` — Runs one stage-unit. Pivotal task.

Each task is one branch, one PR, one ChatGPT conversation. Branch name matches
the task name above.

## Constraints (durable)
- Framework must not import plugins.
- Every stage declares config_deps and inputs; cache keys derive from these.
- code_version, env_version, seed frozen per job at creation.
- No plt.show() in library code; artifacts return bytes.
- At least two plugins must run before v0.1 ships.
- This is a control center: pause, resume, fork, sweep are hard requirements.

## Files in active work
- (none — no branch open)

## Blockers
- None.

## Workflow
- Feature branch per task. PR to `main`. CI green before merge.
- Branch naming: `<phase><number>-<slug>` (e.g. `fc1-interfaces`).
- Every PR updates this file.
