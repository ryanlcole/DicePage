import asyncio
import importlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

import app
import continuity_client
import continuity_writer as writer

AUTH = {"Authorization": "Bearer scoped-test-token"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "DB_PATH", tmp_path / "events.db")
    monkeypatch.setattr(app, "WRITE_TOKEN", "test-token")
    monkeypatch.setenv("RELIC_APPEND_TOKEN", "scoped-test-token")
    monkeypatch.setenv("RELIC_APPEND_ACTOR", "CHATGPT_PRIVATE_CONNECTOR")
    monkeypatch.setenv("RELIC_APPEND_PROJECTS", "SOURCERORS,RELIC_CORE")
    with TestClient(app.app) as client:
        yield client


def record(**changes):
    return dict(project="SOURCERORS", idempotency_key="test-record-001",
                classification="DECISION", subject="continuity writer",
                summary="User authorized a scoped append operation.",
                source_refs=["conversation:test:message-1"],
                occurred_at="2026-10-30T10:00:00Z", **changes)


def post(client, data=None, headers=AUTH):
    return client.post("/v1/continuity-events", json=data or record(), headers=headers)


def test_receipt_survives_reopen_and_preserves_claim(client):
    receipt = post(client).json()
    assert receipt["stored"] and not receipt["canon_promoted"]
    with sqlite3.connect(app.DB_PATH) as con:
        row = con.execute("SELECT payload,status,actor FROM events WHERE id=?", (receipt["event_id"],)).fetchone()
    payload = json.loads(row[0])
    assert row[1:] == ("OBSERVATION", "CHATGPT_PRIVATE_CONNECTOR")
    assert payload["classification"] == "DECISION"
    assert payload["provenance"]["claims_independently_verified"] is False
    assert receipt["payload_hash"] == app.digest(payload)


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"}, {"Authorization": "Bearer test-token"}])
def test_wrong_capability_denied(client, headers):
    assert post(client, headers=headers).status_code == 401


def test_scoped_token_cannot_use_general_writer_or_proposals(client):
    assert client.post("/v1/events", headers=AUTH, json={"kind": "X", "subject": "X", "payload": {}}).status_code == 401
    assert client.post("/v1/proposals", headers=AUTH, json={"subject": "X", "proposed_payload": {}}).status_code == 401


def test_disabled_and_cross_project_denied(client, monkeypatch):
    data = record(); data["project"] = "UNAUTHORIZED"
    assert post(client, data).status_code == 403
    monkeypatch.delenv("RELIC_APPEND_TOKEN")
    assert post(client).status_code == 503
    assert client.get("/v1/events").json() == []


def test_retry_and_changed_envelope(client):
    first = post(client).json()
    second = post(client).json()
    assert second["duplicate"] and first["event_id"] == second["event_id"]
    for field, value in [("summary", "Changed"), ("subject", "Changed"), ("source_refs", ["different-source"]), ("classification", "ERROR")]:
        data = record(); data[field] = value
        assert post(client, data).status_code == 409
    assert len(client.get("/v1/events").json()) == 1


def test_concurrent_retries_append_once(client):
    item = writer.ContinuityEvent(**record())
    with ThreadPoolExecutor(max_workers=8) as pool:
        receipts = list(pool.map(lambda _: writer.append(app, item, AUTH["Authorization"]), range(12)))
    assert len({r["event_id"] for r in receipts}) == 1
    assert sum(not r["duplicate"] for r in receipts) == 1


def test_corrections_keep_original_and_require_same_project(client):
    first = post(client).json()["event_id"]
    data = record(); data.update(idempotency_key="correction-001", prior_event_id=first, summary="Correction")
    assert post(client, data).status_code == 200
    data.update(project="RELIC_CORE", idempotency_key="cross-project-001")
    assert post(client, data).status_code == 400
    rows = client.get("/v1/events").json()
    assert len(rows) == 2 and rows[1]["payload"]["summary"] == record()["summary"]


@pytest.mark.parametrize("changes", [
    {"status": "FACT"}, {"actor": "Ryan"}, {"classification": "AUTHORITY"},
    {"source_refs": []}, {"occurred_at": "2026-10-30T10:00:00"},
    {"summary": " "}, {"summary": "password=do-not-echo"},
    {"summary": "x" * 12001},
])
def test_reject_invalid_or_secret_without_echo(client, changes):
    data = record(); data.update(changes)
    response = post(client, data)
    assert response.status_code == 422
    assert "do-not-echo" not in response.text
    assert client.get("/v1/events").json() == []


def test_request_limit(client):
    assert client.post("/v1/continuity-events", content=b"x" * 65537).status_code == 413


def test_failure_rolls_back_and_retry_is_safe(client):
    with app.db() as con:
        con.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON continuity_receipts BEGIN SELECT RAISE(ABORT, 'simulated interruption'); END")
    with pytest.raises(sqlite3.IntegrityError):
        writer.append(app, writer.ContinuityEvent(**record()), AUTH["Authorization"])
    assert client.get("/v1/events").json() == []
    with app.db() as con:
        con.execute("DROP TRIGGER fail_receipt")
    assert post(client).json()["stored"]


def test_mcp_registration_is_opt_in_and_readonly_database(client, monkeypatch):
    import mcp_server
    monkeypatch.delenv("RELIC_MCP_APPEND_ENABLED", raising=False)
    importlib.reload(mcp_server)
    assert "relic_append_event" not in {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}
    monkeypatch.setenv("RELIC_MCP_APPEND_ENABLED", "1")
    importlib.reload(mcp_server)
    tool = next(t for t in asyncio.run(mcp_server.mcp.list_tools()) if t.name == "relic_append_event")
    assert tool.annotations.readOnlyHint is False and tool.annotations.idempotentHint is True
    with app.readonly_db() as con:
        with pytest.raises(sqlite3.OperationalError):
            con.execute("DELETE FROM events")
    monkeypatch.delenv("RELIC_MCP_APPEND_ENABLED")
    importlib.reload(mcp_server)


def test_bridge_validates_receipt_and_uses_only_fixed_host(client, monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size): return json.dumps(self.result).encode()
    response = Response()
    class Opener:
        def open(self, request, timeout):
            assert request.full_url == "http://127.0.0.1:8080/v1/continuity-events"
            response.result = client.post("/v1/continuity-events", content=request.data, headers=dict(request.header_items())).json()
            return response
    monkeypatch.setattr(continuity_client, "build_opener", lambda *args: Opener())
    assert continuity_client.submit(writer.ContinuityEvent(**record()))["stored"]
