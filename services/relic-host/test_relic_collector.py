import pytest

from observatory import code_change
from relic_collector import validate_envelope


def envelope():
    item = code_change(
        repository="ryanlcole/DicePage",
        ref="refs/heads/relic-independent-service",
        commit="abc123",
        changed_paths=["services/relic-host/app.py"],
        actor="ryanlcole",
    )
    return {"fingerprint": item.fingerprint(), "event": item.event_payload()}


def test_valid_observation_passes():
    event = validate_envelope(envelope())
    assert event["status"] == "OBSERVATION"
    assert event["kind"] == "CODE_CHANGE"


def test_canon_promotion_is_rejected():
    document = envelope()
    document["event"]["status"] = "CANON"
    with pytest.raises(ValueError):
        validate_envelope(document)


def test_causal_collapse_is_rejected():
    document = envelope()
    document["event"]["payload"]["doctrine"]["temporal_association_is_causation"] = True
    with pytest.raises(ValueError):
        validate_envelope(document)


def test_missing_source_is_rejected():
    document = envelope()
    document["event"]["source"] = None
    with pytest.raises(ValueError):
        validate_envelope(document)
