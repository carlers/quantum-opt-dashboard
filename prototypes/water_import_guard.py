"""Fail closed on preloaded *bare-name* water prototype import collisions.

Issue #108 bounded transition safeguard. This does not fix global sys.path
races, attacker-controlled qualified namespaces, or process-global sys.modules.
Original scientific Python model, geometry, QUBO and attestation code is never
imported or executed by this read-only check.
"""
from __future__ import annotations

from pathlib import Path
import sys

# Direct/transitive bare-name imports reached through the unified water MVP
# or research/SA route. Other standalone scientific scripts are out of scope.
WATER_BARE_MODULE_NAMES = (
    "model",
    "mvp_audit",
    "wireless_topology",
    "runtime_attestation",
    "scip_lp_structure",
    "evidence",
    "qubo",
    "sa_benchmark",
    "formulation_audit",
)

WATER_SOURCE_DIR = (Path(__file__).resolve().parent / "streamlit_water_quality").resolve()


class WaterImportOriginError(RuntimeError):
    """A pre-existing same-name module does not come from the pinned source."""


def require_water_import_origins() -> None:
    """Validate existing module-cache entries BEFORE any water path insertion.

    No side effects on sys.path, sys.modules, module attributes or Streamlit.
    Only detects origin mismatch already observable at the time of the call;
    another ScriptRunner could still mutate process-global import state later.
    """
    for name in WATER_BARE_MODULE_NAMES:
        loaded = sys.modules.get(name)
        if loaded is None:
            continue
        expected = (WATER_SOURCE_DIR / (name + ".py")).resolve()
        try:
            filename = getattr(loaded, "__file__", None)
            spec = getattr(loaded, "__spec__", None)
            origin = getattr(spec, "origin", None)
            actual_file = Path(filename).resolve() if isinstance(filename, str) else None
            actual_spec = Path(origin).resolve() if isinstance(origin, str) else None
        except (ValueError, OSError, RuntimeError, TypeError):
            actual_file = actual_spec = None
        if actual_file != expected or actual_spec != expected:
            raise WaterImportOriginError(
                "Water import preflight rejected preloaded bare module "
                + repr(name)
                + ": existing module origin differs from the pinned local source "
                + "or lacks an identifiable Python import spec. "
                + "Do not alias sys.modules or silently fall back to another model."
            )
