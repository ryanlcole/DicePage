from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from research.relic_science.benchmark import lock_prediction, score_vectors, verify_prediction
from research.relic_science.infoton_audit import (
    energy_equivalent_frequency,
    identity_intercept_log10,
    identity_residual,
    p30_arithmetic_reduction,
)
from code_database import error_signature


def test_infoton_identity_is_algebraic_when_temperature_is_derived_from_mass():
    assert abs(identity_intercept_log10() - 39.9727) < 0.001
    for mass in (9.1093837139e-31, 1.67262192595e-27, 1.23456789e-20):
        assert abs(identity_residual(mass)) < 1e-12


def test_p30_percentage_is_only_the_count_ratio():
    assert math.isclose(p30_arithmetic_reduction(), 99.48630136986301, rel_tol=0, abs_tol=1e-12)


def test_mitochondrial_conversion_matches_energy_equivalent_frequency():
    assert math.isclose(energy_equivalent_frequency(0.150) / 1e12, 36.269884522228416, rel_tol=1e-12)


def test_prediction_commitment_detects_post_lock_change(tmp_path):
    prediction = {"gene": "TEST1", "response": [1.0, 2.0, 3.0]}
    path = tmp_path / "commitment.json"
    lock_prediction(prediction, path, {"experiment": "unit-test"})
    commitment = json.loads(path.read_text(encoding="utf-8"))
    assert verify_prediction(prediction, commitment)
    changed = {"gene": "TEST1", "response": [1.0, 2.0, 3.1]}
    assert not verify_prediction(changed, commitment)


def test_vector_scoring_perfect_prediction():
    score = score_vectors([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert score["mae"] == 0.0
    assert score["rmse"] == 0.0
    assert math.isclose(score["pearson"], 1.0)


def test_error_code_parser_prefers_compiler_code_not_generic_error_word():
    _, _, code = error_signature(
        "2026-09-27T12:00:00Z Foo.cs(83): error CS0103: name 'x' does not exist",
        "csharp",
        "Foo.cs",
    )
    assert code == "CS0103"
