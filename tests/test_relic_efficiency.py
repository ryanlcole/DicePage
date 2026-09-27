from __future__ import annotations

from relic_efficiency import (
    RecursionStep,
    RecursionTrace,
    TrialMeasurement,
    aggregate_energy_trials,
    compare_trial_pair,
    request_fingerprint,
)


def test_request_fingerprint_hides_plaintext_and_is_keyed():
    question = "What did ReLiC already know about this system?"
    first = request_fingerprint(question, b"secret-a")
    same = request_fingerprint(question, b"secret-a")
    other_key = request_fingerprint(question, b"secret-b")
    assert first == same
    assert first != other_key
    assert question not in first


def test_recursion_trace_records_path_without_raw_question():
    trace = RecursionTrace(
        request_fingerprint="rq.test",
        semantic_request_id="shaep.request.1",
    )
    trace.add(RecursionStep(
        id="step.1",
        parent_id=None,
        operation="resolve-request",
        semantic_ids=("rune.question.intent",),
        input_bytes=120,
        output_bytes=32,
    ))
    trace.add(RecursionStep(
        id="step.2",
        parent_id="step.1",
        operation="reuse-canon",
        semantic_ids=("rune.canon.identity", "glyph.identity-rule"),
        cache_hit=True,
        input_bytes=32,
        output_bytes=64,
    ))
    trace.add(RecursionStep(
        id="step.3",
        parent_id="step.2",
        operation="model-synthesis",
        semantic_ids=("shaep.answer.1",),
        model_call=True,
        input_bytes=96,
        output_bytes=180,
    ))
    report = trace.summary()
    assert report["rawQuestionStored"] is False
    assert report["totals"]["stepCount"] == 3
    assert report["totals"]["cacheHits"] == 1
    assert report["totals"]["modelCalls"] == 1
    assert "rune.canon.identity" in report["reusedSemanticIds"]


def test_recursion_trace_rejects_unknown_parent():
    trace = RecursionTrace(request_fingerprint="rq.test", semantic_request_id="shaep.request.1")
    try:
        trace.add(RecursionStep(id="step.2", parent_id="missing", operation="bad"))
    except ValueError as exc:
        assert "unknown recursion parent" in str(exc)
    else:
        raise AssertionError("unknown parent should fail")


def test_energy_claim_blocked_when_joules_are_missing():
    baseline = TrialMeasurement(
        wall_time_ns=1_000,
        input_bytes=10_000,
        model_calls=2,
        quality_score=1.0,
    )
    relic = TrialMeasurement(
        wall_time_ns=500,
        input_bytes=2_000,
        model_calls=1,
        quality_score=1.0,
    )
    report = compare_trial_pair(baseline, relic)
    assert report["computeEvidence"]["inputByteReductionPercent"] == 80.0
    assert report["energyEvidence"]["status"] == "UNMEASURED"
    assert report["energyEvidence"]["claimAllowed"] is False


def test_measured_energy_savings_are_reported_only_with_quality_equivalence():
    baseline = TrialMeasurement(
        wall_time_ns=1_000,
        measured_joules=10.0,
        quality_score=1.0,
    )
    relic = TrialMeasurement(
        wall_time_ns=800,
        measured_joules=6.0,
        quality_score=0.99,
    )
    report = compare_trial_pair(baseline, relic)
    assert report["energyEvidence"]["status"] == "MEASURED"
    assert report["energyEvidence"]["savedJoules"] == 4.0
    assert report["energyEvidence"]["savedPercent"] == 40.0
    assert report["energyEvidence"]["claimAllowed"] is True


def test_energy_claim_blocked_if_quality_collapses():
    baseline = TrialMeasurement(
        wall_time_ns=1_000,
        measured_joules=10.0,
        quality_score=1.0,
    )
    relic = TrialMeasurement(
        wall_time_ns=400,
        measured_joules=3.0,
        quality_score=0.5,
    )
    report = compare_trial_pair(baseline, relic)
    assert report["qualityEquivalent"] is False
    assert report["energyEvidence"]["claimAllowed"] is False


def test_energy_aggregate_reports_confidence_band():
    trials = [
        compare_trial_pair(
            TrialMeasurement(wall_time_ns=1000, measured_joules=10.0, quality_score=1.0),
            TrialMeasurement(wall_time_ns=800, measured_joules=8.0, quality_score=1.0),
        ),
        compare_trial_pair(
            TrialMeasurement(wall_time_ns=1000, measured_joules=12.0, quality_score=1.0),
            TrialMeasurement(wall_time_ns=800, measured_joules=9.0, quality_score=1.0),
        ),
    ]
    out = aggregate_energy_trials(trials)
    assert out["status"] == "MEASURED"
    assert out["measuredTrials"] == 2
    assert out["meanSavedJoules"] > 0
    assert out["ci95PercentPoints"] >= 0
    assert out["claimAllowed"] is True
