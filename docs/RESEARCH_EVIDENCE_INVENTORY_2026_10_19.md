# Evidence custody and archival inventory — 2026-10-19

**Scope:** research owner-held preservation of existing GitHub Actions artifacts. This record is **metadata only**, not a new public release, a repo transfer of raw results or publication clearance. Tracking: [#34 scientific CI/retention](https://github.com/carlers/quantum-opt-dashboard/issues/34), [#64 numerical policy](https://github.com/carlers/quantum-opt-dashboard/issues/64), and roadmap [#2](https://github.com/carlers/quantum-opt-dashboard/issues/2).

## Locally assembled owner copy (delivered to owner, not committed to repo)

The assistant independently collected the existing downloadable research ZIPs made available during the preceding scientific sessions, including newly retrieved final-exact-head NumPy dispatch/OpenBLAS controls from the current GitHub account.

- File delivered to owner in the conversation: **`quantum-opt-science-evidence-preservation-2026-10-19.zip`**.
- **Full outer bundle SHA-256:** `462add7e32375916957607b6f90f646fee046e73f21edd4818d3b8e1abadfdbc`.
- Size **662,663 bytes**, **26 byte-preserved nested ZIP archives** and **64 inner archive file entries**. All 26 original ZIPs passed ZIP integrity validation; every included nested ZIP SHA and member SHA was independently computed and cross-checked against the generated `MANIFEST.json`. **22/26** source ZIPs have independently grounded GitHub Actions run/artifact IDs. Four ZIPs lack verified run IDs in this conversation, so these entries are explicitly **null** rather than guessed.
- Bundle includes `README.md`, `MANIFEST.json` with outer and inner original ZIP SHA/byte sizes and source URLs where available, and `SHA256SUMS` covering all `evidence/*.zip` files. Standalone `quantum-opt-science-evidence-manifest.json` and `quantum-opt-science-evidence-SHA256SUMS.txt` were also generated for the owner.
- The historical QUBO exact B mode, full sampled SA states, N20 source coefficient precision/300-pair probes, fixed-input NumPy mathematical microcontrols, and **both exact-head runtime dispatch/OpenBLAS CI** records are represented **to the extent their raw artifacts were accessible and downloaded**. This is **not a claim that all historical CI artifacts are in the bundle**.
- **Deliberate exclusions:** owner DOCX manuscript, original geospatial datasets/GeoJSON, original historical source notebook, third-party raster layers and expert questionnaires. These are separate objects with separate source hashes/data rights. Do **not** infer the manuscript is licensed for public publication or put the evidence ZIP into a public PR.

### Selected separately source-verified CI provenance

| Experiment | Workflow / evidence | Scope |
| --- | --- | --- |
| Archived historical classical SA B | [Workflow 39097840149](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39097840149), [archived result 12125610599](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39097840149/artifacts/12125610599) | Original source B 1,024 read-level records, manifest SHAs |
| Frozen B new full SA states | [Workflow 39176026760](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39176026760), per-host artifacts #12154740329/#12154112387/#12154566050 | Six observed processes, all 46-bit results |
| 300 original N20 free/fixed pairs | [Workflow 39177889565](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39177889565), [stage difference 12154947499](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39177889565/artifacts/12154947499) | Exact recorded coefficient-building stages |
| Frozen NumPy norm/exp micro | [Workflows 39178324563](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39178324563) and [39178474623](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39178474623) | Homogeneous negative and heterogenous positive samples |
| Within-host NumPy SIMD intervention | [Exact-head workflow 39181566374](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181566374), [comparison artifact #12155963142](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181566374/artifacts/12155963142) | Twelve processes, same SHA-pinned binary; NumPy exp dispatch |
| Within-host OpenBLAS target intervention | [Exact-head workflow 39181566385](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181566385), [comparison artifact #12156332453](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181566385/artifacts/12156332453) | Twelve processes; naturally Haswell negative run |
| First actually contrastive OpenBLAS intervention | [Workflow 39181329033](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181329033), [comparison artifact #12156386935](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39181329033/artifacts/12156386935) | Observed auto SkylakeX → forced Haswell norm change |

**Important:** the newly created private outer bundle has a SHA, but its author/consumer must separately store it durably; a temporary ChatGPT conversation download is **not institutional archival custody**. GH Actions artifacts used here generally expire around **Nov 1–2, 2026 UTC**. The copies already downloaded in the owner-held bundle do not automatically expire if the owner keeps them.

## Reproducibility instructions

After extracting the private ZIP to a trusted directory, verify all nested originals without changing their contents:

```sh
sha256sum -c SHA256SUMS
```

Run the companion **stdlib-only** `scripts/verify_research_evidence_bundle.py --bundle /path/to/quantum-opt-science-evidence-preservation-2026-10-19.zip` once the review-only checker is available; this validates the manifest's outer and individual nested member SHA-256, sizes, safe paths and duplicate records, not just that the nested ZIPs open. A failed verification is a **blocking preservation problem**, not a request to regenerate old study results.

Before any publication or upload to a public service: identify rightsholder/licensing status for derived GeoJSON/expert data and site IDs, author consent, retention policy, personal-data exposure and independent scientific review. Potential future reviewed destinations include **private research/institutional storage** and—only with explicit lawful approval—a citable repository/release. A GitHub issue link, public PR body or a local checksum alone is **not** a substitute for storing the raw evidence.

## Coverage gaps and next steps

- [ ] Owner downloads/safeguards the private ZIP plus SHA, verifies it locally, and selects an approved persistent storage destination. This assistant has **not** uploaded the raw files to an external server.
- [ ] Retrieve missing source artifacts only when their actual GitHub artifact IDs are known and they remain within retention (the package does not include every host ZIP for every CI run).
- [ ] Establish independent source/original notebook, GeoJSON, manuscript and expert-data rights/provenance and references without stuffing unlicensed raw bytes into the research repo.
- [ ] Ask reviewer/adviser whether exact host/compiler/env metadata should be included in a public thesis appendix or retained restricted.
- [ ] Use [#64](https://github.com/carlers/quantum-opt-dashboard/issues/64) to approve what “reproduced” means before choosing baseline runtimes, scientific tolerances or any numerical stabilization.

**Next steps:** review the private bundle integrity, approve long-term custody, and publish only the legally permitted provenance/evidence subset after scientific signoff. No merge or live application change is implied.
