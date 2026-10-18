"""Regression checks for read-only float64 precision instrumentation (#24)."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence import canonical_bytes
from precision_probe import build_probe, write_probe


def test_probe_exposes_exact_float_inputs_and_unmodified_n20_provenance(tmp_path):
    record = write_probe(tmp_path)
    original = record["model_source"]
    assert original["source_geojson_sha256"] == (
        "e303cce3d6af6ff4162bb31e09ca27215bc4e29b164fa0181e3f6931de3ae3a7")
    assert original["source_notebook_sha256"] == (
        "08cbc1572048f4c34aab508ae195c82575acd685c7d29695d0eccecdf67cc048")
    assert original["num_dataset_sites"] == 5417
    assert len(original["fixed_feature_positions"]) == 15
    assert len(original["free_feature_positions"]) == 20
    assert len(original["linear_float64_hex"]) == 20
    assert len(original["quadratic_float64_hex"]) == 12
    assert all(x.startswith(("0x", "-0x")) for x in original["linear_float64_hex"])
    assert record["repeated_build_same_process_bitwise_match"] is True
    assert hashlib.sha256(canonical_bytes(original)).hexdigest() == record[
        "raw_model_input_sha256"
    ]
    assert len(record["numeric_model_fingerprint_12_decimal_sha256"]) == 64

    assert set(record["qubo_by_penalty"]) == {
        "notebook-local-row-sum", "midpoint-exploratory", "global-feasibility-bound"
    }
    for label, entry in record["qubo_by_penalty"].items():
        qubo = entry["full_float64_input"]
        assert qubo["n_binary_variables"] == 46
        assert len(qubo["coefficients_float64_hex"]) >= 300
        assert qubo["penalty_float64_hex"].startswith("0x")
        assert hashlib.sha256(canonical_bytes(qubo)).hexdigest() == entry[
            "raw_qubo_sha256"
        ]
        assert record["second_build_qubo_sha256"][label] == entry[
            "raw_qubo_sha256"
        ]

    assert record["environment"]["openjij"] == "0.12.2"
    assert record["environment"]["cpu_model"]
    assert json.loads((tmp_path / "precision_probe.json").read_text()) == record
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert hashlib.sha256((tmp_path / "precision_probe.json").read_bytes()).hexdigest() == (
        manifest["file_sha256"]["precision_probe.json"]
    )
