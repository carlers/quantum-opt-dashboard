# Exact-head evidence checkpoint — Issue #58 (2026-10-18 UTC)

**Latest tested scientific code head** `100c3d2a4c710bc45e687e8e02e04b5c10f7710b`, [draft PR #59](https://github.com/carlers/quantum-opt-dashboard/pull/59), based on archived actual QUBO encoder branch PR #27. Full six-process 6,144-state frozen exact B/B sampler experiment passed at [CI #39176442679](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39176442679): one ordered 46-bit sample SHA across Intel Xeon 8370C and AMD EPYC 7763; **665/1024 original-feasible, 13/1024 exact optimum in every process; 12/12 dedicated adversarial tests passed.** Preexisting Streamlit historical science CI [#39176442608](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39176442608) **47/47 tests passed** and historical four-arm replay produced **[665,665,698,698]** at 1024 samples each. Pinning candidate SHA independently reproduced at [#39176442675](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39176442675). Independent original B archive vs all six new process ZIPs: **zero mismatches in 12 full-sample fields across all 6144 audited reads**. Details + archival repro commands `docs/FROZEN_QUBO_CROSSHOST_RESULTS.md`; full-original/modern N20 mathematical parity limited to notebook-derived model. Draft unmerged, all live branches/data untouched.

---

# Issue #58 — observed fixed-QUBO sampler cross-host bitwise parity (2026-10-18 UTC)

**New draft stacked PR [#59](https://github.com/carlers/quantum-opt-dashboard/pull/59), base the actual historical QUBO work in PR #27**. Exact committed B/B fixture \`prototypes/streamlit_water_quality/fixtures/frozen_B_row_sum_qubo.json\` **raw SHA \`51d47e9a...\`**, binary 46-site+slack-variable QUBO, 323 terms, 1024 original predeclared child seeds and B row-sum P \`0x1.190ab5b15d1b3p+0\`. Every frozen sampler subprocess reads this fixture and verifies its SHA, **no regenerated source model/coefficients/penalty/seed values on hosts**. 3 different GitHub runner jobs × 2 fresh Python/OpenJij 0.12.2 SA processes each = **6,144** read-level states. [Crosshost run #39176026760](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39176026760) **SUCCESS**, original objective/feasibility and QUBO/offset separately checked for every result: all six processes produced **identical full-state digest \`99b76336...\`**, original feasible **665/1024** and exact optimum hits **13/1024** per process. Samples include AMD EPYC 7763 and 9V45 hosts. **7/7** initial adversarial tests green.

Independently retrieved previously archived historical B SA ZIP [artifact #12125610599](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39097840149/artifacts/12125610599) and all three new per-host ZIPs; original archive manifest SHA checks passed. Across all **6×1,024 read comparisons** there were **zero** mismatches in full 46-bit bitstrings, child seeds, selected indices, feasibility and energies (**12 fields per read**). New repo helper \`compare_frozen_archived_b.py\` and five additional tests make this repeatable. Full paper-style evidence and caveats in \`docs/FROZEN_QUBO_CROSSHOST_RESULTS.md\`, methods in \`docs/FROZEN_QUBO_CROSSHOST_PROTOCOL.md\`. Later documentation+test commits require new exact-head CI before signing off.

**Interpretation:** Observed **bitwise repeatability for frozen exact input** across checked hosts; not a universal guarantee. Earlier PR #27 controlled sensitivity established the 665-vs-698 difference is driven by a one-ULP penalty input under the tested setup, *not* necessarily unseeded OpenJij sampling. Remaining parent #24 investigation must trace the original free–fixed interaction last-bit divergence to specific operations; do not normalize/retune published results. Historical source, modern clean notebook PR #56, main, preview and production unmodified. PR #59 remains draft; no merge authorization.

---

# Issue #58 — frozen historical B-mode QUBO cross-host study (2026-10-18 UTC)

**Current task:** Create **one immutable byte-for-byte B/B historical QUBO fixture**, pin exact SHA and original 32×32 read-seed protocol, then evaluate **classical** OpenJij on identical 46-variable inputs across separate fresh processes/hosts. This is complementary to but distinct from review-only modern N20 notebook PR #56 and source precision PR #57, and is based on the existing historical actual encoder/seed controls on PR #27 (`science-sa-ulp-causal-replay`). **No historical sources, model math, Streamlit app, main/preview/production are changed.**

- New branch `science-frozen-qubo-crosshost-sa` from PR #27 `c716367a`; issue #58.
- `docs/FROZEN_QUBO_CROSSHOST_PROTOCOL.md` fixes the scientific design before sampler results: historical B/B source archive SHA `07181560...`, B penalty exact `0x1.190ab5b15d1b3p+0`, 46 QUBO binary variables/323 terms, 32 parent×32 child seeds, 300 sweeps each, 3 fresh hosts×2 processes each = 6144 read-level results.
- `freeze_legacy_qubo.py` generates source-grounded exact model/QUBO/seed candidate JSON from upstream `sa_ulp_replay.build_arms()`; CI candidate artifact **must be inspected and committed** before the six host jobs run. No sampler in the candidate generation step. Do not recompute/retune the QUBO in each host job.
- The issue #26 controlled result already showed **one ULP change in B versus A row-sum penalty, not the four direct linear changes at fixed P, reproduced the 33-count feasibility difference**. This study only tests whether the same exact frozen QUBO + seeds produce bitwise-identical sampled full vectors on independent hosted processes.
- **Next gates**: review frozen JSON and exact hash; commit read-only artifact fixture; implement runtime QUBO+source evaluation and malformed-input tests; matrix-run on separate GitHub hosts; retain full state lists/artifact digests and report outcomes/limitations. Old QUBO modes are not replaced or normalized. Keep PR unmerged.

---

# Final scientific checkpoint — controlled A/B penalty-ULP mechanism (2026-10-18)

- **Verified draft PR #27:** https://github.com/carlers/quantum-opt-dashboard/pull/27, branch `science-sa-ulp-causal-replay`, stacked on other **unmerged non-live** research PRs. [CI 39102059377](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39102059377) at SHA `7764e7ddbcbc9be1e34ee96c6a091f34bda0fcb9`: **35/35 tests passed** (including replay, SHA archive integrity and synthetic tamper tests), all five scientific artifact uploads succeeded. [Controlled archive](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39102059377/artifacts/12126469611) contains 4096 samples; expiry ~2026-11-01 05:53 UTC.
- **Original A/B source files independently recovered:** same 20-site N20 model except exactly four 1–2×10⁻¹⁶ linear-coefficient differences at local sites 9,10,17,19; archived source model SHA A `22c6bdfce2df49c47263341e0a4fa6f1ab8e8dba60cd552a1e9a8b0b7ac60822`, B `0718156034e83d46223fa3e4e086bc9997c16f7252e3c348ca8ac70cf19d5532`. Original quadratic terms, coordinates, fixed adjacency and AHP config identical. Original SCIP proven optimum **−3.3012934918564643** selected local [0,1,3,6,7].
- **Causal, controlled replay mechanism for one pinned sampler and seed set:** four predeclared arms (B-linear/B-penalty, A-linear/B-penalty, B-linear/A-penalty, A-linear/A-penalty) each 1024 child-seeded OpenJij 0.12.2 classical SA draws at 300 sweeps. Feasible counts **[665,665,698,698]**, 13 exact optimum hits in every arm. **Changing only four archived linear values changed zero of 1024 full QUBO bitstrings at fixed penalty**. **Changing only row-sum penalty by one binary64 ULP (B `0x1.190ab5b15d1b3p+0` → A `0x1.190ab5b15d1b4p+0`) changed 882/1024 full bitstrings, 363 original-feasibility flags, and net +33 feasible.** Candidate index **17** is the unique maximal row-sum, so its 2.22e-16 linear drift propagates into penalty P.
- **Crucial independent archive verification:** downloaded original historical [A](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096889778/artifacts/12124762924), [B](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39097840149/artifacts/12125610599), and controlled ZIPs; *all 1024/1024* A/A and B/B samples matched the historical original sample records **bit-for-bit**, including child seed, full QUBO bits, selected locations, feasibility and energy fields. `compare_archived_sa.py` offers independent SHA-checked replay audit; synthetic tests included.
- **Remaining #24 uncertainty:** original site-17/free-fixed interaction coefficient first-principles float variability in `model.make_instance` still lacks a traced operation/library origin. The controlled result establishes effect of penalty ULP on fixed classical sampler but not global solver ranking, quantum advantage, publication parity, or cross-problem generalizability. Original source notebook/data/paper/model and deployed Streamlit untouched. **No merge/deployment without user's approval.**

---

# Current priority — controlled A/B ULP sensitivity test (2026-10-18)

- [Issue #26](https://github.com/carlers/quantum-opt-dashboard/issues/26) follows numeric drift blocker #24. **Archived GitHub Actions evidence A/B downloaded and compared directly:** source `notebook/instance.json` 20-site models differ **ONLY** at four linear coefficients (local 9,10,17,19) by 1-2e-16; common quadratic/graph/coordinates/utility and fixed-site data agree. SCIP optimum unchanged. The correlation with old SA 698 vs 665 feasible per 1024 has **not been causally established**.
- New isolated stacked branch `science-sa-ulp-causal-replay` (base `science-sa-precision-probe`, unmerged PR #25). Frozen four arms: B/B, A/B, B/A, A/A (linear instance source vs one-ULP notebook penalty); same 32 parent seeds × 32 child seeds × 300 sweeps per arm; total 4096 classical SA reads.
- `sa_ulp_replay.py` freezes archived B exact float coefficients/graph and four A `float.hex` overrides; validates source N20 reference via independent enumeration. `tests/test_sa_ulp_replay.py` checks exact coefficient differences, penalty bits, QUBO size, certified optimum. `SA_ULP_CONTROLLED_REPLAY.md` and issue #26 *pre-register experiment before CI result review*.
- CI adds `n20-ulp-controlled-replay` archive (JSON, all samples, trial rows, SHA-256 checksums). **Verification pending**; do not claim causal explanation until actual results and reproducibility reviewed.
- Strict safety: no merges or live deployments; default `main` and deployed `plugin-water-streamlit-pilot` frozen, original GeoJSON/notebook/paper/model untouched.

---

# Current task: exact float64 coefficient precision diagnosis — issue #24 (2026-10-18)

- Isolated scoped branch `science-sa-precision-probe` stacked above **unmerged** PR #23, not deployed and not merged to live Streamlit.
- Read-only `precision_probe.py` exports original N=20 instance 64-bit float values as `float.hex`, exact per-penalty QUBO coefficient digests/slack metadata and narrow CPU/BLAS environment metadata. Rebuild twice per process to test local stability, never infer cross-run sameness from one pass.
- CI adds `n20-precision-probe` archive (14-day retention) and `test_precision_probe.py` checks mathematical source/frozen hashes and file integrity.
- **Observed issue #24:** nominally fixed-seed row-sum SA yields 698 or 665 feasible draws out of 1,024 across successful GitHub Actions runs, each associated with a different **exact** N20 model-instance SHA while 12-decimal numerical fingerprints and SCIP optima agree. Root cause unverified; do not silently average runs or change paper/notebook/model/penalty.
- Goal: compare fresh diagnostic artifacts from at least two different runners, localize whether source floats/QUBO coefficients or CPU settings drift, and record a scientifically justified next validation gate.
- Live `plugin-water-streamlit-pilot` and `main` remain untouched. Explicit user approval required before any merge/deployment.

---

# Cross-run scientific reproducibility warning (2026-10-18; issue #24)

**Do not treat the first 3,072-draw paired-SA report as byte-for-byte replayable.** In GitHub Actions [39096889778](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096889778), row-sum feasibility was **698/1024**, whereas successful documentation-only reruns [39097001668](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39097001668) and [39097023374](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39097023374) each yielded **665/1024** with identical registered seeds. Row-sum optimum hits remained **13**, midpoint/global feasibility remained **790** each, and their optimum hits stayed **0/1**. The **raw input instance SHA differed** (`22c6bdf...` vs `07181560...`), though the **12-decimal numerical fingerprint and certified SCIP optimum matched**. The notebook row-sum penalty differed in its last binary rounding digit. Root cause is **unverified**; this correlation does not prove that the float drift alone caused the changed SA trajectories.

First-run feasibility differences of **+8.984 pp** for each higher penalty vs row sum became **+12.207 pp** in the reruns. Preserve BOTH and the separate paired-block intervals. Do not select a favorable number, average repeated CI runs as new independent experiment blocks, claim guaranteed OpenJij cross-run seed determinism, or infer general performance across different research instances. Dedicated blocker: [issue #24](https://github.com/carlers/quantum-opt-dashboard/issues/24). Original preregistration issue #22, draft PR #23 and historical provenance issue #16 remain open. No live merger/deployment.

---

# Current scoped milestone — preregistered paired-seed SA replication (2026-10-18)

- Scope: [issue #22](https://github.com/carlers/quantum-opt-dashboard/issues/22) preregistered **before results**, on isolated `science-sa-paired-replication` stacked above unmerged PR #21. New draft PR targets `science-openjij-sa-benchmark`, not the live Streamlit branch.
- Registered design: **32 NEW parent seeds `270010001..270010032`**, 32 independently child-seeded single reads per parent × 3 **unchanged** QUBO penalty configurations, **300 sweeps/read**, total **3,072 samples** from OpenJij 0.12.2 classical SA.
- Primary outcome: *original-feasible AND exact SCIP-optimum hit* (1e-7), denominator all samples including infeasible. Secondary: original feasibility. Report two paired differences against row-sum penalty, each with descriptive **10,000-resample parent-seed-block percentile bootstrap** intervals, fixed bootstrap PRNG seed 734021; no significance or generalization claim.
- Implementation: `sa_paired_replication.py`, `tests/test_sa_paired_replication.py`, `SA_PAIRED_REPLICATION.md` and scoped GitHub Actions artifact `n20-sa-paired-replication`.
- Independent SCIP 20-choose-5 certification and historical source checksums retained. No original notebook, GeoJSON, deployed app, model, or paper modification. Unresolved paper provenance issue #16.
- **Verified validation:** [GitHub Actions run 39096889778](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096889778) **30/30 tests passed**, original SCIP + 288 exploratory SA + preregistered 3072-sample analysis all executed and **three archives uploaded**. [Paired-study ZIP](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096889778/artifacts/12124762924) expires approximately 2026-11-01 04:23 UTC. No live merge/deploy without user approval.
- **Observed preregistered 1024-draw-per-penalty counts:** notebook row-sum 698 feasible (68.164%), 13 certified-optimum hits (1.270%); midpoint 790 feasible (77.148%), 0 optimum hits; global bound 790 feasible (77.148%), 1 optimum hit. Row-sum SCIP optimum −3.3012934918564643. Both larger penalty settings are +8.984 percentage points more feasible in this fixed experiment, but produce fewer optimum hits.
- **Paired-block descriptive bootstrap 95% intervals (10,000 × 32 parent blocks):** midpoint feasibility − row-sum +8.984 pp [5.469, 12.305], global − row-sum +8.984 pp [5.273,12.598]; midpoint optimum-hit − row-sum −1.270 pp [−1.855,−0.781], global − row-sum −1.172 pp [−1.758,−0.586]. No multiple testing inference or cross-instance generalization. The midpoint zero-hit bootstrap point interval [0,0] is degenerate and **not** a valid claim of zero underlying rare-event probability. Full interpretation in SA_PAIRED_REPLICATION.md.

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
