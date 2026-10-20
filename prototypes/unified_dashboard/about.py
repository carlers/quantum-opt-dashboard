"""Plain-language scientific scope and consolidated provenance of the MVP."""
import streamlit as st

st.title("About the scientific workbench")
st.caption("One unified MVP · existing validated research prototypes kept intact")

st.markdown(
    """
This dashboard combines the original water-quality sensor-placement research,
a **synthetic configurable optimization workbench**, and a bounded classical
simulated-annealing research demonstration.

### Current capabilities

**Water-quality placement.** One committed Laguna de Bay input source, 20
notebook-derived free candidates, explicitly marked existing stations, a
configurable new-site budget, numerical formulation inspection, exact SCIP
optimization, an original-model feasibility check, geospatial results, and
downloadable model/result/LP evidence.

**Configurable synthetic models.** User-selected JSON/CSV/GeoJSON fixtures,
support for two synthetic evacuation-center models and small user-defined
binary/integer/continuous optimization models, guided objective and constraint
editors, original model versus SCIP comparison, and safe model compatibility
checks. Synthetic evacuation examples are *not real hazard guidance*.

**Research QUBO/SA.** Exact slack-augmented QUBO inspection for the validated
lake instance; small, manually triggered **classical** OpenJij SA sampling with
individual child seeds and original-feasibility checks. Full replication and
numerical-precision studies remain separate research scripts and CI artifacts.

### Key scientific boundaries

- **Not a replication of the published numerical paper:** its AHP weights,
  D2 semantics, station provenance and published SCIP energy differ from
  the committed notebook reference and remain under investigation.
- **Local one-hop connectivity is not global network connectivity.**
- **SCIP uses an exact binary-product MILP** to solve the supported quadratic
  binary model; it is not a native QUBO sampler.
- **OpenJij SASampler is classical simulated annealing**, not quantum
  hardware. Floating-point last-bit changes can change returned samples.
- User-authored constrained QUBOs and general continuous/integer quadratic
  products require separate mathematical validation; unsupported conversions
  are explicitly refused.
- CSV and GeoJSON examples in the general workbench are **synthetic-only**.
  Real emergency-site data and deployment decisions require data rights,
  ground truth, assumptions and scientific validation.

### Reproducibility

The app exposes the original mathematical coefficients and selected
configuration, source hashes, actual SCIP LP, decoded result and sample seeds.
Full reproducibility still requires tracking platform and floating-point
environment, preserving exact artifact bytes, and manually archiving
research evidence: short-lived GitHub Actions artifacts are not a journal
deposit.

The original source notebook, GeoJSON, manuscript and historical
research branches remain unchanged. This is a combined **research MVP**,
not a fully generalized or operational decision-making service.
"""
)
# Visible three-scope research claim ladder. This is *not* a runtime field
# certification: the independent pinned source-science branch remains unmerged.
# Keep factual state labels conservative until human source/field review.
st.subheader("Scientific evidence status")
st.markdown(
    """
| Scope | Research status | What the tests and data actually establish |
| --- | --- | --- |
| **Original notebook computation (N20/K5)** | **Computationally verified, source-only** | 20 original candidate sites, 15 marked existing sites, K=5; **1,077 feasible of 15,504** using the original local one-hop rule. Exact SCIP and independent mathematical enumeration support original winning candidate indices **[0, 1, 3, 6, 7]**. |
| **All-original-fixed globally connected network** | **Exploratory mathematical scenario** | Separate exact geometric graph search; **860 feasible of 15,504** K5 combinations when all 15 existing stations must belong to the same modeled connected graph. This is not measured radio connectivity. |
| **Published manuscript and original AHP/GIS inputs** | **Not reconciled** | The committed historical source uses **D2 road proximity**; the manuscript describes population/WorldPop. Original expert AHP matrices, criterion transformation records and exact input parity are not established. |
| **Physical lake monitoring performance** | **Not validated** | No confirmed field RF/backhaul links, surveyed physical shoreline constraints, hydrodynamic current/DO transport or observed sensor detection outcomes. |

The independent scientific source/claim checks run in a **separate, pinned
GitHub checkout**, not as automatically merged app source. Solver/LP
mathematical checks are not an authenticated first SCIP process, an externally
signed research verdict, published-paper replication or field deployment
certificate. The detached verifier is **unsigned** and has no trusted external
source-commitment custodian or nonce-replay registry.

The working optimization platform is therefore a **research MVP candidate**,
not a validated environmental deployment service. Classical OpenJij SA is
not quantum hardware; no quantum advantage is claimed.
"""
)

st.page_link(
    "https://github.com/carlers/quantum-opt-dashboard/issues/2",
    label="Project roadmap on GitHub", icon="📋",
)
