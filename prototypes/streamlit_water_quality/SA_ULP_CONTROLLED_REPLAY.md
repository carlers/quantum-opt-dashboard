# Controlled archived A/B one-ULP replay — research issue #26

**Pre-run registered specification.** This investigation is distinct from the earlier exploratory #20 and repeated-seed #22 studies. The same random seeds are *intentionally reused* so that we can isolate coefficient-level effects; therefore do not interpret this test as independent replication or additional evidence of real-world solver superiority.

## What the archived artifacts prove

We retrieved two original **SCIP evidence ZIPs from GitHub Actions** without interpolating any missing inputs:

- **A**: [run 39096889778, archive 12124693239](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096889778/artifacts/12124693239), SHA-256 of `notebook/instance.json` exactly `22c6bdfce2df49c47263341e0a4fa6f1ab8e8dba60cd552a1e9a8b0b7ac60822`. The simultaneously recorded SA result was **698/1024 original-feasible**, 13 exact-optimum hits, at notebook row-sum `P=1.097819667627033`.
- **B**: [run 39097840149, archive 12125012351](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39097840149/artifacts/12125012351), SHA-256 `0718156034e83d46223fa3e4e086bc9997c16f7252e3c348ca8ac70cf19d5532`. SA row sum was **665/1024 original-feasible**, 13 exact-optimum hits, at `P=1.0978196676270329`.

An independent field-by-field JSON comparison shows **only four** notebook-instance linear coefficients differ; **all original utility values, 12 free-free quadratic terms, original candidate/fixed sites and coordinates, Dmax, K=5, and one-hop adjacency arrays are identical**. The entire difference is captured here in exact `float.hex` strings:

| Local index | A | B | A − B |
|---|---|---|---:|
| 9 | `-0x1.7ef780983da1ap-3` | `-0x1.7ef780983da1ep-3` | +1.11×10⁻¹⁶ |
| 10 | `-0x1.5504f3b222e88p-5` | `-0x1.5504f3b222e78p-5` | −1.11×10⁻¹⁶ |
| 17 | `0x1.940eba845152ep-1` | `0x1.940eba845152cp-1` | +2.22×10⁻¹⁶ |
| 19 | `0x1.2b6a379dd0180p-8` | `0x1.2b6a379dd0200p-8` | −1.11×10⁻¹⁶ |

These four differences are **not a paper correction** and do not alter the previously certified feasible N20/K5 optimum `[0,1,3,6,7]` or `−3.3012934918564643` at normal numeric tolerance. All other original SCIP input arrays match exactly, as verified by the archived JSON comparison.

## Registered four interventions before inspecting outcomes

`sa_ulp_replay.py` constructs an immutable minimal mathematical `Instance` with the archived **B** numeric linear terms and the common original 12 quadratic pairs, 20 one-hop adjacency lists and fixed-neighbor mask. Its unused coordinates are placeholders; site selection and geometry are *not* rerun because the task is to replay the **already archived objective**. It then constructs the A form by altering exactly the four numbers above. The original certified optimum is checked against an independent **15,504-subset** enumeration. No handwritten or rounded alternative QUBO is substituted.

The sampler has **four predefined arms**, all preserving the original QUBO encoding and the same exact parent/child-seed manifest:

| Arm | Original linear terms | Penalty |
|---|---|---|
| `B-linear_B-penalty` | Archived B | `0x1.190ab5b15d1b3p+0` |
| `A-linear_B-penalty` | Archived A | Same B penalty |
| `B-linear_A-penalty` | Archived B | `0x1.190ab5b15d1b4p+0` |
| `A-linear_A-penalty` | Archived A | Same A penalty |

OpenJij **classical** `SASampler` 0.12.2; 32 parent seeds 270010001–270010032, each 32 distinct `SeedSequence.spawn` child seeds, one sampler read at **300 sweeps** per call. **4×32×32=4096** binary QUBO reads, 1024 per arm. The same random seeds are *deliberate* paired controls. No larger or custom stochastic search after viewing outcomes.

Each read is checked for original budget and local adjacency feasibility; original raw energy must not be confused with augmented QUBO energy, and expanded/unexpanded QUBO values are independently cross-validated. The `summary.json` stores per-arm **exact** QUBO SHA-256, source archived SHA labels, feasibility and optimum hit count; `trials.csv` has per-parent outcomes; `samples.csv` has every 46-bit state and both source/child seeds. `manifest.json` hashes those three outputs.

## Interpretation gate

Compare `B/B` to archived B **665/1024** and `A/A` to archived A **698/1024**. If both match and only changing linear coefficients causes the 33-draw swing, the controlled replay supports a causal influence of last-bit input changes *within this pinned sampler/code/run setup*. If the penalty-only change causes a different result, document it. If neither matches, do not dismiss cross-host/sampler nondeterminism.

**Do not claim a globally consistent root cause from one controlled experiment.** A fully conclusive coefficient-origin explanation still needs tracing the original linear-increment calculation (`model.make_instance`) and cross-run bytewise fidelity of generated QUBO inputs. Statistical intervals from reused seeds are not a fresh inferential test. No live Streamlit branch, source notebook/GeoJSON, paper or original model is edited. Parent #24, #22, #16.


## Results appended after pre-registered four-arm CI experiment (2026-10-18)

**GitHub Actions run [39101669013](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39101669013) passed 33/33 tests**, original SCIP/288-read/3072-read/precision pipelines passed, four-arm **4096-read** experiment finished, and all evidence artifacts uploaded.

[Download the controlled replay's complete 4096 states, parent trials, exact QUBO digests and SHA-256 manifest](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39101669013/artifacts/12126374351) (14-day GitHub retention).

| Arm | Exactly preserved archived linear terms | Exactly preserved P | Original-feasible / 1024 | SCIP optimum hits / 1024 | QUBO SHA-256 prefix |
|---|---|---|---:|---:|---|
| B-linear/B-penalty | B | B | **665** | **13** | `2402d0a1...` |
| A-linear/B-penalty | A | B | **665** | **13** | `abb0be00...` |
| B-linear/A-penalty | B | A | **698** | **13** | `2bef4467...` |
| A-linear/A-penalty | A | A | **698** | **13** | `fed3756b...` |

**Controlled conclusion for this N20 instance and pinned OpenJij binary:** changing **only the four archived linear coefficients** did not change feasibility, selected original placements or any of the 1,024 complete 46-bit returned sample states for a fixed penalty. Changing **only the penalty by one binary64 ULP** (`0x1.190ab5b15d1b3p+0` to `0x1.190ab5b15d1b4p+0`) changed the final full bitstrings for **882 of 1,024** identically seeded reads; **363** read-level feasibility flags flipped, yielding a **net +33 feasible draws** (+3.22265625 percentage points). It **exactly recreated the prior 665 and 698 modes and their 13 optimum hits**.

The notebook's row-sum formula has its **unique maximum at local candidate 17** in both archives. That candidate's original linear coefficient differs by 2.22×10⁻¹⁶; this shifts the calculated global row-sum heuristic by exactly one ULP. The three other last-bit linear differences are documented as real but are not necessary to produce the observed feasibility swing in this particular controlled replay.

### Stronger independent post-run artifact verification

After the controlled CI run, we independently downloaded **all three original GitHub Actions ZIPs** (historical [A](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39096889778/artifacts/12124762924), historical [B](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39097840149/artifacts/12125610599), and new [four-arm controlled](https://github.com/carlers/quantum-opt-dashboard/actions/runs/39101669013/artifacts/12126374351)). Their archived SHA-256 manifests were retained in each ZIP.

**All 1,024 A/A replay results matched the original historical A result at the exact bitstring level. All 1,024 B/B results matched the original historical B result at the same level.** For each paired child seed/read index, original vs controlled output matched in all inspected fields: child seed, entire 46-bit state, selected local positions, original-feasible flag, budget/connectivity flags, occurrence count, raw objective, QUBO augmented energy and sampler-reported QUBO energy.

The audit also found that changing only the four linear coefficients gave **0/1024 full-bitstring changes** in either penalty setting. Penalty-only changes gave **882/1024 full-bitstring changes**, **882/1024 selected-position changes** and **363/1024 feasibility-flag changes**, with 13 optimum hits under both penalties. The separate `compare_archived_sa.py` CLI documents and automates this zipped archive comparison for future review.

**What remains unresolved:** The controlled experiment identifies the *numerical-parameter mechanism*: original candidate-17 linear rounding → derived row-sum penalty ULP difference → dramatically different sampled trajectories. It does **not yet identify which exact underlying operations, compiler/library architecture, or reduction ordering caused the original candidate-17 linear coefficient to vary across CI processes.** Future work should isolate contributions in `model.make_instance` (e.g. free/fixed interaction/wake terms) and fully version float64 transformations, rather than rounding original research data or claiming any quantum advantage. Replayed fixed seeds are **not independent validation samples**.
