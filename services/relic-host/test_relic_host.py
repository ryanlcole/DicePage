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
