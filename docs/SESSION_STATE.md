# Separate exact N20 source evidence downloaded, not yet owner-archived — 2026-10-19 UTC

**Standing user preference:** every completed response includes **Next steps** and exact step-by-step user actions when approval/storage is needed. Downloaded 15 new verified original GitHub Actions artifact ZIPs (37 internal files) across runs #39186452841, #39187619344, #39191911068, #39191911072, #39192139080 and #39192139090. Packaged privately in `quantum-opt-n20-integrated-evidence-2026-10-19.zip`, SHA256 `7463332681fafc26ee441c9456251e89059722844ba26a548bb4cb20808879c9`; separate SHA and manifest provided to user in conversation. **Not uploaded to institutional/private external storage; user needs to download and retain.** Existing earlier 26-ZIP package remains a separate previously offered object (SHA `462add7e32375916957607b6f90f646fee046e73f21edd4818d3b8e1abadfdbc`). Live source artifact expiries **Nov 2, 2026 UTC**. No raw GeoJSON/paper was re-released. Details `docs/RESEARCH_EVIDENCE_INVENTORY_2026_10_19.md`.

**Next steps:** confirm latest fast PR #65 CI, add a short and accurate custody update to issue #34 and PR #65, and give user steps for private storage + decision(s) needed. Owner/adviser scientific B1–B6 decisions remain unsigned; no merges/deploys/public archives without explicit approval.

---

# Adviser N20 computational acceptance handoff — 2026-10-19 UTC

**Owner standing rule:** Always include explicit **Next steps**. New unsigned, source-evidence-grounded `docs/N20_ADVISER_ACCEPTANCE_CHECKLIST.md` added to this **review-only draft PR #65**. It verifies bounded original notebook N20/K5 computational claims against exact-head CI #39192139080 and #39192139090 on **unmerged draft PR #68** and separates those from **seven unapproved owner/adviser decisions** (source authority; hull/adjacency; numerical tolerance and R0/R1/R2 tier; manuscript AHP/D2/SCIP discrepancy; allowed claims/new evacuation model; evidence rights/storage; separately authorized merge action). No signer name or approval is fabricated. It links the published-manuscript source audit #16 and policy #64 and recognizes old GIS/archived source checksums.

Latest **live metadata** independently fetched after #66–#68 exist: **32 open PRs, all drafts**, across five main-rooted families, largest family 13 and deepest parent lineage 11; source #56 family now **7** with two sibling scientific forks and combined draft #68. Former auto-audit 29-PR figure remains a **historical prior snapshot**, not current CI evidence.

**Next steps:** get exact-head fast policy/evidence CI green, update PR #65/Issues #5/#16/#64/#34/#2, ask adviser to complete decision record, store rights-authorized evidence before 2026-11-02, and plan separate reviewed integration/merge only if explicitly permitted. Do not merge, deploy, change main/preview/production or alter source manuscript.

---

# Current research policy/evidence checkpoint — 2026-10-19 UTC

**Owner instruction:** Work continuously on next roadmap tasks, and include a clear **Next steps** statement in every user-facing response and research handoff. No permission to merge or deploy scientific PRs.

**Independent doc + fast-verifier branch:** `research-numerical-policy-evidence-handoff` branched from unmodified `main` `41cdc51097ceb98ea2f44194e3b72a0a3aeb3f3c`, not from a stacked scientific PR. It changes ONLY review/provenance docs, two pure-stdlib verification scripts, their tests and one fast CI workflow.

- `docs/SCIENTIFIC_NUMERICAL_EQUIVALENCE_POLICY_DRAFT.md`: **PROPOSED**, not approved, exact input/model invariants vs candidate energy tolerance vs float-hex diagnostic; science runtime tiers R0/R1/R2; no silent NumPy/OpenBLAS masks, rounding or publication “fix.”
- `docs/MANUSCRIPT_NOTEBOOK_PROVENANCE_AUDIT.md`: compared owner-provided DOCX's printed AHP Tables III/IV, source derived N20 SCIP vs published Table V/VII and contradictory D2 metadata. Independent printed-matrix eigenvector/reported CR, unverified raw expert/source data explicitly identified. Original DOCX not modified/committed.
- `docs/RESEARCH_EVIDENCE_INVENTORY_2026_10_19.md`: owner-held **26 original downloaded ZIP archives, 64 inner files**, verified SHA pack `462add7e32375916957607b6f90f646fee046e73f21edd4818d3b8e1abadfdbc`, delivered privately via conversation; NOT published to GitHub or durable external store. 22/26 source IDs verified, four deliberately unknown; rights and missing-run gaps documented. No original manuscript or GeoJSON bundled.
- `scripts/verify_research_evidence_bundle.py`: stdlib CLI checks full outer SHA (when independently supplied), all original artifact ZIP hashes, nested members, counts and safe paths; adversarial tests. `scripts/replay_printed_manuscript_ahp.py` + tests reproduce printed matrix eigenvector and Table IV mismatch **without** pretending to reconstruct raw questionnaires.
- `docs/SCIENTIFIC_PR_REVIEW_HANDOFF.md`: review #56→#57→#61→#63 and separate #27→#59; original scientific PRs remain draft/unmerged. Independent policy PR can be reviewed without adopting any source math.
- `.github/workflows/research-evidence-policy-checks.yml`: fast Python stdlib tests; **not a claim** that source-lake SCIP or SA was rerun on this document-only branch.

**Next steps:** get exact-head fast CI success; comment #64 (numerical policy), #16 (paper discrepancies), #34 (raw evidence rights/retention) and roadmap #2; request human/adviser decisions and owner long-term archive choice. Do not merge, change `main`/preview/production, or publish unlicensed data until separately authorized.

---

# Session checkpoint

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