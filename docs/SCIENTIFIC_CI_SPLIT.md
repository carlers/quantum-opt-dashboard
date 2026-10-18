# GitHub Actions: fast checks vs frozen research protocols

**Status:** Scoped draft change for [issue #34](https://github.com/carlers/quantum-opt-dashboard/issues/34). Scientific math, sampler seed sets, sweeps, inputs, original notebook and GeoJSON have **not** changed. Applies to unmerged Streamlit/science branch stack, not to deployed `plugin-water-streamlit-pilot` or `main`.

## Why split the pipelines?

Before this change, every source/UI PR matching `prototypes/streamlit_water_quality/**` compiled Python, ran all tests, **and re-ran five output-producing jobs**, including 288 exploratory SA draws, 3,072 preregistered draws and 4,096 archived ULP replay draws. This needlessly re-executed experiments for documentation/UI changes, emitted misleading apparent replicate runs with *identical seeds*, and created expiring 14-day archives.

The change isolates validation responsibility:

| Workflow | Trigger and scope | Actual work | Intended result |
|---|---|---|---|
| `streamlit-pilot.yml`: **Streamlit pilot fast regression** | PR changes within `prototypes/streamlit_water_quality/**` or either workflow; approved existing pilot-branch pushes | Python compile, **all** numerical and smoke tests (real small SCIP, proof-oriented small QUBO, seeded tiny OpenJij, Streamlit AppTest, numeric QUBO/LP inspector) | Fail early when the model/CLI/UI breaks; never re-run a 3,072/4,096-read study |
| `streamlit-research-evidence.yml`: **Water-quality research evidence (SCIP + classical OpenJij)** | PR changes to explicit scientific model, QUBO, benchmark, proof-test, source data/notebook or research workflow paths; `workflow_dispatch` explicit full run | Standalone numerical proof suite + original N20 SCIP reference, 288-read exploratory SA, 3,072-read paired SA, float64 probe, 4,096-read ULP replay; uploads **all five** archives | Review a complete bounded scientific evidence package only when scientific code/inputs change or a reviewer intentionally invokes it |

A change only to `app.py` / UI styling or a research design Markdown file **does not** automatically run the 3,072/4,096-draw experiment. A change to `model.py`, `qubo.py`, the frozen experiment runners, source notebook, GeoJSON, relevant science-test files or full-research workflow **does** trigger full research. Ordinary Python tests in the fast gate always include the real Streamlit `AppTest` and mathematical N20 baseline.

**GitHub Actions event note:** `workflow_dispatch` is defined in the full-research workflow; GitHub generally requires that workflow file to exist on the default branch for the Run Workflow control to appear. On this **unmerged draft branch**, the full-research PR-path trigger is the acceptance proof. Do not claim the user can already click Run Workflow on production/main. After a reviewed integration to the default branch, start a manual run via GitHub Actions → Water-quality research evidence → Run workflow, select the intended ref, and archive its exact run SHA. Do not treat the same registered seeds as new independent samples.

## Frozen experiment contract

The **exact existing CLIs** and fixed research inputs are preserved, not rewritten:
- `evidence.py --scenario all --time-limit 120`: certified N20 SCIP source-parity scenarios.
- `sa_benchmark.py --seeds 20261018,20261019,20261020 --reads 32 --sweeps 300`: **288** classical OpenJij SA reads.
- `sa_paired_replication.py`: **3,072** preregistered classical SA reads with parent-seed block uncertainty (issue #22).
- `precision_probe.py`: exact float64 and QUBO coefficient/provenance diagnostic (issue #24).
- `sa_ulp_replay.py`: **4,096** fixed-seed controlled retrospective input/penalty replay (issue #26).

All five outputs are separate GitHub Actions archives with `if-no-files-found: error` and **14-day retention**. Research runs use `GITHUB_HEAD_SHA=${{ github.event.pull_request.head.sha || github.sha }}` for PR and manual provenance. The manual-run Git SHA should be compared to the true source ref; workflow outputs alone are not a complete environment lock.

## Scientific boundaries and quality gates

- **Do not compare counts across repeated CI reruns as independent experimental repetitions.** Historical unmerged results are still exploratory or post-registered controlled replay with original parent seeds. An exact input instance may differ by binary64 ULP across hosts even where a 12-decimal fingerprint matches.
- The previous N20/K5 certified SCIP reference energy ≈ **−3.3012934918564643** is the original notebook-derived source reference, *not* historical paper parity. The QUBO is independently implemented with slack bits; OpenJij's sampler is **classical**.
- Keep GitHub Actions workflow permissions at `contents: read` and avoid `git push`, releasing, merging or deployment. The deployment branch remains `plugin-water-streamlit-pilot` and receives **no workflow changes until approved**.
- `tests/test_ci_workflow_contract.py` uses PyYAML BaseLoader to enforce both trigger scopes, all five complete archives, nonzero pytest invocation, and that the fast PR job does not invoke heavy CLIs. This is a **static contract test**, not a substitute for checking actual GitHub Actions traces.
- PySCIPOpt / NumPy / SciPy / Shapely and dashboard dependencies remain **range-pinned**, not fully lockfile-frozen. OpenJij is fixed to 0.12.2. Full environment-lock and cross-host precision provenance remain a **future release gate**; the split does not solve #24.
- The changed tests are still comparatively light (<10 seconds **after installation** in a previous CI run), but GitHub runner dependency setup and the Streamlit app smoke will dominate total wall clock. Do not claim a measured end-to-end speedup without recording comparable new run durations.

## Durable research artifact plan (still open)

Action artifacts expire after **14 days**: a successful CI run is not a permanent thesis deposit. Before publishing, require an approved author/licensing decision, dataset-redistribution assessment and a code-tag/release process. Candidate repositories include an institutional research archive or DOI-backed repository (e.g., Zenodo/OSF), but **do not auto-create a release or upload any potentially restricted GeoJSON/hazard/facility dataset**.

A release candidate should bundle stable code revision and LICENSE/CITATION metadata (only after real owner review), raw/derived dataset hashes and legitimate access instructions, pinned environment/software/CPU metadata, exact MIQP/SCIP LP and QUBO coefficients, predeclared study protocol and seeds, raw trial rows, source checksums, readable regeneration commands, figures generated from raw data, and limitations/negative results. Reserve published DOI/reference identifiers only after an actual archival deposit.

## Reviewer acceptance checklist

1. Observe a PR that only edits the `app.py` or inspector docs: fast checks pass; full research does not run automatically.
2. Observe a PR changing `model.py`, `qubo.py`, experiment source or the research workflow: **both** fast tests and complete bounded research workflow run.
3. Confirm all existing filenames, sample counts, seed manifests, penalty parameters and five evidence archive names remain unchanged.
4. Confirm fast suite collects meaningful tests and passes, including a real SCIP solve and dashboard AppTest; separate full job runs the scientific tests (without UI dependencies) and all five archived CLIs.
5. Do not call issue #34 completely done until two-trigger behavior is empirically observed, science result artifacts are inspected, archive/retention decision is reviewed, and user approves eventual merge. No deployment authorization.

Related: academic [Phase 5 #7](https://github.com/carlers/quantum-opt-dashboard/issues/7), [thesis artifacts #11](https://github.com/carlers/quantum-opt-dashboard/issues/11), manuscript issues #16, #24, umbrella #2.
