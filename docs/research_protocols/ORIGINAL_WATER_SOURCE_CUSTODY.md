# Original Laguna de Bay source custody — fast immutable input check

**Status: review-only scientific source preservation.** The original notebook and GeoJSON were **not modified**. The scientific workbench, paper parity, data rights, original research result, solver execution, and deployed Streamlit pilot were not changed. No OCI resources or spending.

## Why preserve the original source, rather than clean the historical notebook in place?

The notebook contains 25 code cells (including duplicated historical solver and grid-search versions). All 25 currently have null execution counts and empty saved outputs. Those duplicates and original method inconsistencies are valuable *historical evidence* and should not be rewritten, executed, reordered, normalized or dropped inside the original reference file merely to make a modern notebook easier to run.

For a cleaned executable research workflow, develop **a separate derived notebook or Python module** with a provenance map back to each historical JSON cell index. Use [the existing source-to-dashboard parity table](../NOTEBOOK_DASHBOARD_PARITY_2026_10_26.md), and never relabel the new explicit slack QUBO as notebook JijModeling/OMMX parity without independent tests.

## Frozen research objects (original bytes)

| Original source | SHA-256 | Git blob SHA-1 | Scope |
| --- | --- | --- | --- |
| `problems/water_quality/notebooks/experiment9 grid search copy.ipynb` | `08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048` | `a554f4f37957e924c0ed417e53af2dab04e45ffa` | Historical 25-cell Python notebook, no saved execution output |
| `problems/water_quality/data/LDB_centroids_clean.geojson` | `e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7` | `de79af608585bc02eb0ab05c0fd4cc2f02e9acd7` | Historical Laguna de Bay centroid/factor source, **not manuscript WorldPop/AHP parity** |

The SHA-256 bytes already appear in the restricted N20 exact-reference test in `prototypes/streamlit_water_quality/tests/test_n20_reference.py`; this PR makes the check run fast and standalone instead of requiring a full N20 SCIP run. Git object IDs were read from the existing GitHub source tree and are checked through Git's blob framing convention, not used as cryptographic author identity.

The machine-readable file `docs/research_protocols/original_water_sources_v1.json` duplicates the independent literal cold fingerprints in `scripts/verify_research_sources.py`; changing the catalog alone cannot silently redefine the baseline. Both must undergo human scrutiny for any intentional historical source replacement.

## Fast local / CI checks

```bash
python scripts/verify_research_sources.py
python -m unittest discover -s problems/water_quality/tests -p test_source_provenance.py -v
```

Standard-library-only, no scientific library installation. A new PR-only workflow `.github/workflows/original-water-source-integrity.yml` runs on edits to either source, the manifest, the verifier, its tests, or this documentation.

The verifier checks exact source SHA-256 and Git blob identity, a bounded notebook JSON structure of 25 code cells and unique cell IDs, absence of stored execution outputs, permitted paths/no source symlinks, and an exact manifest schema. The 14 tests include intentional synthetic output/ID/cell mutation, duplicate JSON keys, symlinks, manifest alteration and rights metadata tampering.

### Proof limitations

- A matching hash proves **file byte identity relative to these pinned references**, not who collected the source, correctness of field factors, custody independence, authenticity, or dataset reuse permission.
- GitHub availability of the GeoJSON does **not** mean its redistribution or derivatives have an independently verified license. Check original data provider/institution, applicable privacy terms and manuscript publication rights **before any public data release**.
- The notebook is **not executed** by this checker; source validity is separate from solver validity.
- The historical eight-factor notebook uses road-based D2 and notebook weights, which are **not identical** to the manuscript's described WorldPop/AHP inputs.
- Current source-restricted N20/K5 SCIP optimum is a **classical** result with local one-hop connectivity and is not a general water-quality, quantum-computing, or field-validation claim.
- The source hashes stored on this same GitHub repository are **not** independently governed attestation. An attacker permitted to rewrite all refs can evade these checks; use independent university/archive custody for publication-level provenance.

## Next research repository cleanup

1. Keep historical notebook+GeoJSON unchanged, independently verify source rights.
2. Build a **separate derived and side-effect-free notebook**, running only small bounded synthetic or source-authorized examples; map each cell to original provenance and pin random seeds.
3. Record exact solver and platform environment, model coefficients/LP fingerprints, complete result manifests, expected plots/tables and independent validators. Separate fast source/contract CI from costly exact solver and scientific acceptance CI.
4. Review publication citation/author/DOI/license metadata with the human researcher before creating a `CITATION.cff` that might invent publication metadata.
5. Keep all OCI, IAM, remote deployment and paid storage blocked by the owner's **$0/month** requirement.

Related: [academic reproducibility survey](../ACADEMIC_REPRODUCIBILITY_SURVEY.md), [notebook parity matrix](../NOTEBOOK_DASHBOARD_PARITY_2026_10_26.md), and [scientific research roadmap](https://github.com/carlers/quantum-opt-dashboard/issues/2).
