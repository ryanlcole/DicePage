import pytest

from github_observer import observation_from_push


def push(**overrides):
    payload = {
        "ref": "refs/heads/relic-independent-service",
        "before": "1111111",
        "after": "2222222",
        "created": False,
        "forced": False,
        "compare": "https://github.com/ryanlcole/DicePage/compare/111...222",
        "repository": {"full_name": "ryanlcole/DicePage"},
        "sender": {"login": "ryanlcole"},
        "commits": [
            {"added": ["new.py"], "modified": ["same.py"], "removed": []},
            {"added": [], "modified": ["same.py", "other.py"], "removed": ["old.py"]},
        ],
    }
    payload.update(overrides)
    return payload


def test_push_becomes_bounded_code_observation():
    item = observation_from_push(push())
    event = item.event_payload()
    facts = event["payload"]["facts"]
    assert event["kind"] == "CODE_CHANGE"
    assert event["status"] == "OBSERVATION"
    assert event["source"] == "GIT_REPOSITORY"
    assert facts["commit"] == "2222222"
    assert facts["changed_paths"] == ["new.py", "old.py", "other.py", "same.py"]
    assert facts["before"] == "1111111"
    assert facts["commit_count_in_payload"] == 2
    assert event["payload"]["doctrine"]["temporal_association_is_causation"] is False


def test_missing_identity_is_rejected():
    with pytest.raises(ValueError):
        observation_from_push(push(ref=None))
    with pytest.raises(ValueError):
        observation_from_push(push(repository={}))


def test_branch_delete_is_not_misrepresented_as_commit():
    with pytest.raises(ValueError):
        observation_from_push(push(after="0" * 40))
