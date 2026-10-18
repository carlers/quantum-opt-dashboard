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
