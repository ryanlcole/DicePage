import os
import tempfile

import pytest

fd, path = tempfile.mkstemp(prefix="relic-test-", suffix=".db")
os.close(fd)
os.unlink(path)
os.environ["RELIC_DB_PATH"] = path
os.environ["RELIC_WRITE_TOKEN"] = "test-token"

from fastapi.testclient import TestClient
import app

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client():
    # Enter TestClient as a context manager so FastAPI's startup lifecycle
    # runs and initializes the SQLite schema before requests are sent.
    with TestClient(app.app) as test_client:
        yield test_client


def test_event_is_append_only_and_readable(client):
    r = client.post("/v1/events", headers=AUTH, json={
        "kind": "CONTINUITY",
        "status": "VERIFIED",
        "subject": "relic.boundary",
        "payload": {"chatgpt_memory_is_authority": False},
    })
    assert r.status_code == 200
    event_id = r.json()["id"]
    rows = client.get("/v1/events", params={"subject": "relic.boundary"}).json()
    assert any(row["id"] == event_id for row in rows)


def historical_request(**overrides):
    value = {
        "candidate_id": "PK-test-001",
        "idempotency_key": "idempotency-test-001",
        "source_hash": "source-hash-001",
        "human_approved": True,
        "approval_evidence": {"approver": "human-test", "scope": "test-only"},
        "event": {
            "kind": "INVESTIGATION",
            "status": "OBSERVATION",
            "subject": "historical-continuity:TEST:PK-test-001",
            "payload": {
                "doctrine": {
                    "representation_is_truth": False,
                    "observation_is_canon": False,
                },
                "audit_record": {"record_id": "PK-test-001", "gap_status": "MISSING"},
                "migration": {"automatic_canon_promotion": False},
            },
            "source": "HISTORICAL_CONTINUITY_AUDIT",
            "actor": "OUTSIDER_AI",
        },
    }
    value.update(overrides)
    return value


def test_historical_import_requires_explicit_human_approval(client):
    request = historical_request(human_approved=False, approval_evidence={})
    before = client.get("/v1/events").json()
    r = client.post("/v1/historical-import", headers=AUTH, json=request)
    assert r.status_code == 403
    assert client.get("/v1/events").json() == before


def test_historical_import_is_idempotent_and_returns_same_live_event(client):
    request = historical_request()
    first = client.post("/v1/historical-import", headers=AUTH, json=request)
    assert first.status_code == 200
    assert first.json()["duplicate"] is False
    assert first.json()["canon_promoted"] is False
    event_id = first.json()["event_id"]

    second = client.post("/v1/historical-import", headers=AUTH, json=request)
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert second.json()["event_id"] == event_id

    rows = client.get("/v1/events", params={"subject": request["event"]["subject"]}).json()
    assert [row["id"] for row in rows].count(event_id) == 1


def test_historical_import_rejects_idempotency_collision(client):
    request = historical_request()
    first = client.post("/v1/historical-import", headers=AUTH, json=request)
    assert first.status_code == 200

    changed = historical_request()
    changed["event"]["payload"]["audit_record"]["gap_status"] = "CONTRADICTORY"
    r = client.post("/v1/historical-import", headers=AUTH, json=changed)
    assert r.status_code == 409


def test_historical_import_cannot_promote_status_or_kind(client):
    promoted = historical_request()
    promoted["event"]["status"] = "VERIFIED"
    assert client.post("/v1/historical-import", headers=AUTH, json=promoted).status_code == 400

    wrong_kind = historical_request(candidate_id="PK-test-002", idempotency_key="idempotency-test-002")
    wrong_kind["event"]["kind"] = "CONTINUITY"
    assert client.post("/v1/historical-import", headers=AUTH, json=wrong_kind).status_code == 400


def test_historical_import_rejects_unresolved_prior_event_id(client):
    request = historical_request(candidate_id="PK-test-003", idempotency_key="idempotency-test-003")
    request["event"]["prior_event_id"] = "historical-source-id-not-live-event"
    r = client.post("/v1/historical-import", headers=AUTH, json=request)
    assert r.status_code == 400


def test_proposal_refuses_mutation_until_all_three_gates_pass(client):
    proposal = client.post("/v1/proposals", headers=AUTH, json={
        "subject": "report.section",
        "proposed_payload": {"operation": "omit", "section": "limitations"},
    }).json()
    pid = proposal["id"]
    assert proposal["mutation_allowed"] is False

    r = client.post(f"/v1/proposals/{pid}/gates/necessity", headers=AUTH, json={"state": "PROVEN", "evidence": {"reason": "test"}})
    assert r.json()["mutation_allowed"] is False
    r = client.post(f"/v1/proposals/{pid}/gates/accuracy", headers=AUTH, json={"state": "PROVEN", "evidence": {"source": "test"}})
    assert r.json()["mutation_allowed"] is False
    r = client.post(f"/v1/proposals/{pid}/gates/approval", headers=AUTH, json={"state": "APPROVED", "evidence": {"approver": "human-test"}})
    assert r.json()["mutation_allowed"] is True


def test_failed_gate_keeps_change_blocked(client):
    pid = client.post("/v1/proposals", headers=AUTH, json={"subject": "canon", "proposed_payload": {"change": "x"}}).json()["id"]
    client.post(f"/v1/proposals/{pid}/gates/necessity", headers=AUTH, json={"state": "FAILED", "evidence": {}})
    client.post(f"/v1/proposals/{pid}/gates/accuracy", headers=AUTH, json={"state": "PROVEN", "evidence": {}})
    r = client.post(f"/v1/proposals/{pid}/gates/approval", headers=AUTH, json={"state": "APPROVED", "evidence": {}})
    assert r.json()["mutation_allowed"] is False