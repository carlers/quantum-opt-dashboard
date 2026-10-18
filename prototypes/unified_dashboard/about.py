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
st.page_link(
    "https://github.com/carlers/quantum-opt-dashboard/issues/2",
    label="Project roadmap on GitHub", icon="📋",
)
