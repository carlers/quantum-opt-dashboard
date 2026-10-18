# Independently verified synthetic evacuation optimization (prototype)

**SYNTHETIC SCIENTIFIC MODEL ONLY**. Not an official shelter recommendation, not a geographic evacuation system, and not an approved thesis formulation. This bounded implementation follows research proposal [issue #30](https://github.com/carlers/quantum-opt-dashboard/issues/30) and proof task [issue #32](https://github.com/carlers/quantum-opt-dashboard/issues/32).

## Why this is different from the lake model

The water-quality site selection experiment optimizes utility and pairwise redundancy with a local one-hop graph constraint. The emergency-shelter proposal instead represents estimated evacuee demand, **usable shelter capacity**, **road reachability** and **unserved people**. No water-quality penalty or geometry is copied into this domain, and there is **no claim of real shelter safety or road availability**.

### Mathematical implementation (provisional)

**Maximal covering reference.** Enumerate binary open shelter subsets x with at most K and declared eligibility e. For each zone i, the binary "covered" label means at least one open site has a reachable arc. Maximize Σ d_i covered_i. This is **potentially reachable demand, not capacity-feasible demand served**. It ignores capacities deliberately; the two metrics must never be conflated in figures.

**Capacitated model.** Binary opened x_j, continuous nonnegative y_ij persons assigned on reachable arcs, and u_i unmet persons. Constraints: Σ_j y_ij+u_i=d_i for every i; Σ_i y_ij<=C_j x_j for each site; x_j<=e_j and Σ_j x_j<=K. Solve **lexicographically**: first minimize total unmet persons Σ u_i using SCIP; then constrain Σ u_i<=U*+1e-9 numerical tolerance and minimize Σ t_ij y_ij (person-minutes). SCIP's second stage is not an artificial weighted sum. No integer family assignment or road congestion is included.

A separate `independent_enumeration` procedure visits **every** permitted opened-site subset and solves each continuous assignment using **SciPy HiGHS `linprog`**, implementing demand/capacity matrices independently rather than calling SCIP or sharing its model objects. A separate feasibility checker verifies demand balance, opened eligibility, capacity, reachable arcs and budgets.

### Artificial two-zone reference (frozen before CI)

| Quantity | Value | Interpretation |
|---|---:|---|
| Zone demands | [4,3] persons | Fake evacuees |
| Candidate capacity | [5,5] persons | Fake shelters |
| Max opened sites | 1 | Only one facility |
| Travel times | [[1,9],[2,4]] minutes | Synthetic connected graph |
| Minimum unserved | **2 persons** | Capacity five < demand seven |
| Best opened site, zero-based | **site 0** | First candidate (sometimes called center 1 in 1-based notation) |
| Assigned to site 0 | **4 from zone 0 and 1 from zone 1** | Zone 1 leaves 2 unserved |
| Best travel | **6 person-minutes** | 4×1+1×2 |
| Maximal-coverage potential | **7 persons** | Does not mean seven can be accommodated |

The source fixture `fixtures/tiny_synthetic.json` explicitly declares all values, units, selected center and expected outcomes. Any attempt to infer actual Philippine demand or facility safety from it is an error.

## Runtime, testing and export

From repository root on this **isolated research draft** (not main or live Streamlit):

```bash
python -m pip install 'numpy>=2,<3' 'scipy>=1.11,<2' 'pyscipopt>=5,<7' 'pytest>=8'
python -m pytest problems/evacuation_centers/tests -q
python problems/evacuation_centers/synthetic_reference.py --output-dir /tmp/evacuation-synthetic
```

GitHub Actions workflow `.github/workflows/evacuation-synthetic.yml` automatically verifies only changes to this domain/its own workflow. It uploads `evacuation-tiny-synthetic-reference` containing the source fake fixture, independent/SCIP cross-check summary, **actual SCIP stage-one and stage-two LP files** exported from the exact models, and checksum manifest. All artifacts are temporary (14 days); do not cite that as a durable thesis deposit.

Test cases include expected numeric optimum, capacity-vs-coverage semantics, required-all-served infeasibility, zero/two opened sites, an unreachable demand zone, no hazard-eligible sites, zero demand/capacity, malformed or unknown facility capacities, invalid negative travel, incorrect eligibility and illegal allocations, and variants where the two solvers must agree. CI passing does **not** establish correctness on real hazard data, larger geographic networks, evacuation routing dynamics or quantum advantage.

## Next scientific gates

1. Review this baseline's scientific meaning and staged objective with adviser/owner. Selecting shelter 0 here says nothing about real shelters.
2. Design network model and real source schema for a **chosen and authorized** geography. Verify 2024 PSA population/PSGC joins, legitimate LGU shelter registers with *usable capacity*, permissible hazard layers and licensing, and road travel mode/snapshot. See [data audit](../../docs/EVACUATION_DATA_AUDIT.md) and [issue #33](https://github.com/carlers/quantum-opt-dashboard/issues/33).
3. Consider genuine robust/hazard scenarios and equity after the data permissions and research outcome definitions are approved. A candidate QUBO version is **not automatically possible with small overhead**, and current SCIP model is **not** a QUBO benchmark.
4. Only after two independently reviewed domains demonstrate common scientific interfaces should we refactor reusable solvers, datasets and mathematical inspectors into framework abstractions.

**Safety:** no merge or deployment without explicit user approval. No real evacuation-center locations, route advice, or sensitive data exist here.
