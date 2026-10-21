"""Prove source import module origins and observed runtime-manifest semantics.

These tests deliberately do NOT claim that process-global sys.path pollution
has been eliminated. Module origin, no cross-page result, and per-run source
correctness are testable; multi-thread malicious isolation requires a refactor.
"""
from __future__ import annotations

from hashlib import sha256
from importlib import metadata, util
from pathlib import Path
import sys

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "prototypes/unified_dashboard/app.py"
MANIFEST = ROOT / "scripts/release_runtime_manifest.py"


def manifest_module():
    spec = util.spec_from_file_location("qopt_runtime_manifest_review", MANIFEST)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_origin(module_name: str, relative: str):
    loaded = sys.modules.get(module_name)
    assert loaded is not None, f"{module_name} was never imported"
    path = Path(loaded.__file__).resolve()
    assert path == (ROOT / relative).resolve(), (
        f"Untrusted module origin for {module_name}: {path}"
    )


def test_route_water_custom_research_water_resolves_expected_scientific_modules():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception, app.exception
    require_origin("model", "prototypes/streamlit_water_quality/model.py")
    require_origin("wireless_topology", "prototypes/streamlit_water_quality/wireless_topology.py")
    require_origin("runtime_attestation", "prototypes/streamlit_water_quality/runtime_attestation.py")
    assert "mvp_result" not in app.session_state

    app.switch_page("pages/custom.py").run()
    assert not app.exception, app.exception
    require_origin("problems.water_quality.notebook_reference_model",
                   "problems/water_quality/notebook_reference_model.py")
    require_origin("problems.evacuation_centers.bundle_runner",
                   "problems/evacuation_centers/bundle_runner.py")
    require_origin("qopt.core.experiment_bundle",
                   "framework/python/qopt/core/experiment_bundle.py")
    require_origin("qopt.core.binary_quadratic",
                   "framework/python/qopt/core/binary_quadratic.py")
    require_origin("qopt.core.math_ir",
                   "framework/python/qopt/core/math_ir.py")
    require_origin("prototypes.streamlit_configurable.app",
                   "prototypes/streamlit_configurable/app.py")
    require_origin("prototypes.streamlit_configurable.guided_math_ui",
                   "prototypes/streamlit_configurable/guided_math_ui.py")
    assert not app.session_state.get("completed_run")
    assert "mvp_result" not in app.session_state

    app.switch_page("pages/research.py").run()
    assert not app.exception, app.exception
    require_origin("model", "prototypes/streamlit_water_quality/model.py")
    require_origin("qubo", "prototypes/streamlit_water_quality/qubo.py")
    require_origin("prototypes.unified_dashboard.research",
                   "prototypes/unified_dashboard/research.py")
    assert "unified_sa_run" not in app.session_state

    app.switch_page("pages/water.py").run()
    assert not app.exception, app.exception
    require_origin("model", "prototypes/streamlit_water_quality/model.py")
    assert "mvp_result" not in app.session_state
    assert any("Water-quality sensor placement" in x.value for x in app.title)


def test_manifest_binds_checkout_source_and_observed_metadata(monkeypatch):
    x = manifest_module()
    freeze = b"numpy==2.1.2\nstreamlit==1.50.0\npyscipopt==6.2.0\n"
    installed = {name: "observed-only-" + name for name in x.REQUIRED_DISTRIBUTIONS}
    libs = {"geos_runtime_version": "test", "proj_runtime_version": "test",
            "scip_runtime_version": None, "scip_runtime_version_readable": False}
    monkeypatch.setattr(x, "_version_and_build", lambda: (installed, libs))
    out = x.build_manifest(
        freeze, checked_out_git_sha="a" * 40,
        pull_request_head_sha="b" * 40,
    )
    assert out["pip_freeze_sha256"] == sha256(freeze).hexdigest()
    assert out["pip_freeze_bytes"] == len(freeze)
    assert out["exact_installed_dependency_versions"] == installed
    assert out["loaded_native_libraries"] == libs
    assert out["canonical_unified_entrypoint"] == "prototypes/unified_dashboard/app.py"
    assert out["original_GeoJSON_sha256"] == (
        "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7"
    )
    assert out["actual_checkout_git_sha"] == "a" * 40
    assert out["pull_request_head_git_sha"] == "b" * 40
    assert out["scientific_status"]["published_manuscript_input_parity_established"] is False
    assert out["scientific_status"]["empirical_lake_RF_DO_validated"] is False
    assert out["scientific_status"]["external_signer_or_remote_execution_attested"] is False
    assert any("DISTINCT exact identities" in t for t in out["limitations"])


@pytest.mark.parametrize("raw,sha", [
    (b"", "a" * 40),
    (b"\x00oops\n", "a" * 40),
    (b"x" * 150001, "a" * 40),
    (b"numpy==2.3\n", "not_a_commit_sha"),
])
def test_manifest_rejects_bad_freeze_or_unidentified_source_commit(raw, sha):
    x = manifest_module()
    with pytest.raises(ValueError):
        x.build_manifest(raw, checked_out_git_sha=sha,
                         pull_request_head_sha="a" * 40)


def test_runtime_inventory_reads_actual_installed_versions_without_guessing():
    x = manifest_module()
    versions, libraries = x._version_and_build()
    assert set(versions) == set(x.REQUIRED_DISTRIBUTIONS)
    for name, distribution in x.REQUIRED_DISTRIBUTIONS.items():
        assert versions[name] == metadata.version(distribution)
        assert isinstance(versions[name], str) and versions[name]
    assert libraries["geos_runtime_version"]
    assert libraries["proj_runtime_version"]
    if libraries["scip_runtime_version_readable"]:
        assert libraries["scip_runtime_version"]
    else:
        assert libraries["scip_runtime_version"] is None
