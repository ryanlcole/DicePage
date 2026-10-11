import pytest

from observatory import EvidenceRef, Observation, code_change, user_error_report, verification


def test_code_change_is_observation_not_truth():
    item = code_change(
        repository="ryanlcole/DicePage",
        ref="relic-independent-service",
        commit="abc123",
        changed_paths=["b.py", "a.py", "a.py"],
        actor="developer",
    )
    event = item.event_payload()
    assert event["status"] == "OBSERVATION"
    assert event["payload"]["facts"]["changed_paths"] == ["a.py", "b.py"]
    assert event["payload"]["doctrine"]["observation_is_canon"] is False
    assert event["payload"]["doctrine"]["temporal_association_is_causation"] is False


def test_user_report_does_not_invent_cause():
    item = user_error_report(
        product="ReLiC Share",
        report_id="ERR-1",
        description="Page changed after an update",
        observed_version="deadbeef",
        reporter="user",
    )
    facts = item.event_payload()["payload"]["facts"]
    assert facts["claim_scope"] == "USER_REPORTED_EXPERIENCE"
    assert facts["cause"] == "UNKNOWN"


def test_observatory_rejects_truth_promotion():
    with pytest.raises(ValueError):
        Observation(
            kind="USER_ERROR_REPORT",
            status="CANON",
            subject="product:x:error:y",
            payload={},
            source="USER_REPORT",
        )


def test_verification_has_bounded_results():
    item = verification(
        subject="build:abc123",
        result="pass",
        method="pytest",
        evidence=[EvidenceRef("ci", "run:42")],
    )
    assert item.event_payload()["payload"]["facts"]["result"] == "PASS"
    with pytest.raises(ValueError):
        verification(subject="x", result="TRUE", method="guess")


def test_fingerprint_is_stable_for_same_observation():
    item = Observation(
        kind="TEST_RESULT",
        subject="test:one",
        payload={"result": "PASS"},
        source="CI",
        observed_at="2026-10-10T00:00:00+00:00",
    )
    assert item.fingerprint() == item.fingerprint()
