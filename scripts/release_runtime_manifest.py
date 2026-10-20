"""Capture an OBSERVED, review-only Python 3.12 scientific runtime inventory.

Not a lockfile, signed attestation, portable numerical identity or an authority
for paper/field claims. No notebook is executed, datasets are only SHA-read.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from importlib import import_module, metadata
import json
import platform
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
ENTRYPOINT = ROOT / "prototypes/unified_dashboard/app.py"
REQUIRED_DISTRIBUTIONS = {
    "numpy": "numpy", "scipy": "scipy", "shapely": "shapely",
    "pandas": "pandas", "pyproj": "pyproj", "pydeck": "pydeck",
    "pyscipopt": "PySCIPOpt", "streamlit": "streamlit",
    "openjij": "openjij", "pyyaml": "PyYAML",
}
HEX40 = re.compile(r"[a-f0-9]{40}\Z")


def _digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _version_and_build():
    observed = {}
    for name, dist in sorted(REQUIRED_DISTRIBUTIONS.items()):
        # Installed exact versions, NOT versions inferred from requirements.
        observed[name] = metadata.version(dist)
    import shapely
    import pyproj
    import pyscipopt
    libs = {
        "geos_runtime_version": str(shapely.geos_version_string),
        "proj_runtime_version": str(pyproj.proj_version_str),
        "scip_runtime_version": None,
        "scip_runtime_version_readable": False,
    }
    # PySCIPOpt exposes SCIP version through Model version methods on
    # supported builds. If unavailable, do not invent a libscip version.
    model = pyscipopt.Model()
    try:
        funcs = [getattr(model, f"get{part}Version", None)
                 for part in ("Major", "Minor", "Tech")]
        if all(callable(f) for f in funcs):
            parts = [f() for f in funcs]
            if all(type(v) is int and v >= 0 for v in parts):
                libs["scip_runtime_version"] = ".".join(map(str, parts))
                libs["scip_runtime_version_readable"] = True
    finally:
        del model
    return observed, libs


def build_manifest(freeze: bytes, *, checked_out_git_sha: str,
                   pull_request_head_sha: str) -> dict:
    """No network calls, app imports, notebook modification or SCIP solve."""
    if not freeze or len(freeze) > 150_000 or b"\x00" in freeze:
        raise ValueError("Missing, oversized or invalid exact installed pip freeze")
    if not HEX40.fullmatch(checked_out_git_sha) or not HEX40.fullmatch(pull_request_head_sha):
        raise ValueError("Require actual 40-hex git checkout and PR head commit identities")
    if not SOURCE.is_file() or not ENTRYPOINT.is_file():
        raise FileNotFoundError("Canonical source GeoJSON or integrated Streamlit entrypoint absent")
    source_bytes = SOURCE.read_bytes()
    source_sha = _digest(source_bytes)
    if source_sha != "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7":
        raise ValueError("Current source bytes differ from pinned original GeoJSON")
    installed, libs = _version_and_build()
    return {
        "schema_version": 1,
        "claim": "observed_python312_runtime_dependencies_only",
        "source_data_claim": "original_notebook_derived_D2_road_NOT_manuscript_WorldPop",
        "scientific_status": {
            "original_N20_source_computational_verified": True,
            "published_manuscript_input_parity_established": False,
            "empirical_lake_RF_DO_validated": False,
            "quantum_hardware_or_advantage_demonstrated": False,
            "external_signer_or_remote_execution_attested": False,
        },
        "canonical_unified_entrypoint": str(ENTRYPOINT.relative_to(ROOT)),
        "original_GeoJSON_sha256": source_sha,
        "entrypoint_sha256": _digest(ENTRYPOINT.read_bytes()),
        "actual_checkout_git_sha": checked_out_git_sha,
        "pull_request_head_git_sha": pull_request_head_sha,
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "machine": platform.machine(),
            "system": platform.system(),
            "release": platform.release(),
            "architecture": platform.architecture()[0],
        },
        "exact_installed_dependency_versions": installed,
        "loaded_native_libraries": libs,
        "pip_freeze_sha256": _digest(freeze),
        "pip_freeze_bytes": len(freeze),
        "pip_freeze_lines": len(freeze.splitlines()),
        "limitations": [
            "versions and pip freeze from THIS runner, not a reproducible lockfile",
            "numpy scipy BLAS GEOS libscip build and platform can vary on other hosts",
            "two observed original binary64 objective coefficient SHA variants are DISTINCT exact identities",
            "GitHub CI + hashes are not owner signatures or third-party trusted execution",
            "algorithm timeout is not an operating system CPU or memory quota",
            "not manuscript AHP WorldPop D2 parity or measured radio/water-quality proof",
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--freeze", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--actual-checkout-sha", required=True)
    p.add_argument("--pull-request-head-sha", required=True)
    p.add_argument("--require-python-312", action="store_true")
    args = p.parse_args()
    if args.require_python_312 and sys.version_info[:2] != (3, 12):
        raise ValueError("Only Python 3.12 is accepted as the trial preview runtime")
    if args.output.exists():
        raise FileExistsError("Do not overwrite prior runtime research evidence")
    if args.freeze.is_symlink() or not args.freeze.is_file():
        raise ValueError("A concrete installed freeze file is required")
    report = build_manifest(
        args.freeze.read_bytes(), checked_out_git_sha=args.actual_checkout_sha,
        pull_request_head_sha=args.pull_request_head_sha,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(
        (json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False)
         + "\n").encode("utf-8")
    )
    print("UNIFIED_RUNTIME_PROVENANCE", json.dumps({
        "source_sha": report["original_GeoJSON_sha256"],
        "python": report["python"]["version"],
        "installed": report["exact_installed_dependency_versions"],
        "scip_runtime_version": report["loaded_native_libraries"]["scip_runtime_version"],
        "pip_freeze_sha256": report["pip_freeze_sha256"],
        "paper_field_or_signed_claims": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
