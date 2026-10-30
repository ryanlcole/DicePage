"""ReLiC independent continuity host.

Observer-first, append-only service. It does not grant mutation authority over
Shaelvien/RIST. Representation is not truth; current implementation claims must
still be verified against their authoritative source.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

import historical_import
import continuity_writer

DB_PATH = Path(os.getenv("RELIC_DB_PATH", "/data/relic.db"))
WRITE_TOKEN = os.getenv("RELIC_WRITE_TOKEN", "")

app = FastAPI(title="ReLiC Host", version="0.1.0")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def db() -> sqlite3.Connection:
    """Open the authoritative writer connection.

    ReLiC stores SQLite on EFS. WAL is intentionally forbidden here because
    SQLite WAL requires all processes to be on the same host and is unsafe for
    network filesystems. DELETE journal mode keeps locking in SQLite's normal
    rollback-journal path. MCP readers use their own read-only connection.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA journal_mode=DELETE")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def readonly_db() -> sqlite3.Connection:
    """Open ReLiC without schema, journal, or other mutation authority."""
    uri = f"file:{DB_PATH}?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA query_only=ON")
    return con


def init() -> None:
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS events (
          seq INTEGER PRIMARY KEY AUTOINCREMENT,
          id TEXT NOT NULL UNIQUE,
          recorded_at TEXT NOT NULL,
          kind TEXT NOT NULL,
          status TEXT NOT NULL,
          subject TEXT NOT NULL,
          payload TEXT NOT NULL,
          payload_hash TEXT NOT NULL,
          prior_event_id TEXT,
          source TEXT,
          actor TEXT,
          FOREIGN KEY(prior_event_id) REFERENCES events(id)
        );
        CREATE INDEX IF NOT EXISTS idx_events_subject_seq ON events(subject, seq);
        CREATE INDEX IF NOT EXISTS idx_events_kind_seq ON events(kind, seq);

        CREATE TABLE IF NOT EXISTS proposals (
          id TEXT PRIMARY KEY,
          created_at TEXT NOT NULL,
          subject TEXT NOT NULL,
          prior_event_id TEXT,
          proposed_payload TEXT NOT NULL,
          proposed_hash TEXT NOT NULL,
          necessity_state TEXT NOT NULL DEFAULT 'UNKNOWN',
          necessity_evidence TEXT,
          accuracy_state TEXT NOT NULL DEFAULT 'UNKNOWN',
          accuracy_evidence TEXT,
          approval_state TEXT NOT NULL DEFAULT 'PENDING',
          approval_evidence TEXT,
          status TEXT NOT NULL DEFAULT 'PROPOSED'
        );
        """)
        historical_import.init_schema(con)
        continuity_writer.init_schema(con)


@app.on_event("startup")
def startup() -> None:
    init()


class EventIn(BaseModel):
    kind: str
    status: str = "OBSERVATION"
    subject: str
    payload: dict[str, Any]
    prior_event_id: str | None = None
    source: str | None = None
    actor: str | None = None


class ProposalIn(BaseModel):
    subject: str
    proposed_payload: dict[str, Any]
    prior_event_id: str | None = None


class GateIn(BaseModel):
    state: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class HistoricalImportIn(BaseModel):
    candidate_id: str
    idempotency_key: str
    event: EventIn
    source_hash: str | None = None
    human_approved: bool = False
    approval_evidence: dict[str, Any] = Field(default_factory=dict)


def require_write(authorization: str | None) -> None:
    if not WRITE_TOKEN:
        raise HTTPException(503, "RELIC_WRITE_TOKEN is not configured")
    if authorization != f"Bearer {WRITE_TOKEN}":
        raise HTTPException(401, "write authorization required")


@app.get("/health")
def health() -> dict[str, Any]:
    init()
    with readonly_db() as con:
        count = con.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
    return {"service": "relic-host", "state": "SAFE", "observer_only": True, "events": count}


@app.get("/v1/events")
def events(subject: str | None = None, limit: int = Query(100, ge=1, le=1000)) -> list[dict[str, Any]]:
    with readonly_db() as con:
        if subject:
            rows = con.execute("SELECT * FROM events WHERE subject=? ORDER BY seq DESC LIMIT ?", (subject, limit)).fetchall()
        else:
            rows = con.execute("SELECT * FROM events ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
    return [{**dict(r), "payload": json.loads(r["payload"])} for r in rows]


@app.post("/v1/events")
def append_event(item: EventIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_write(authorization)
    event_id = str(uuid.uuid4())
    payload_hash = digest(item.payload)
    with db() as con:
        con.execute(
            "INSERT INTO events(id,recorded_at,kind,status,subject,payload,payload_hash,prior_event_id,source,actor) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (event_id, now(), item.kind, item.status, item.subject, canonical(item.payload), payload_hash, item.prior_event_id, item.source, item.actor),
        )
    return {"id": event_id, "payload_hash": payload_hash, "append_only": True}


@app.post("/v1/historical-import")
def append_historical_import(item: HistoricalImportIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    """Append an explicitly approved historical OBSERVATION exactly once."""
    require_write(authorization)
    if not item.human_approved or not item.approval_evidence:
        raise HTTPException(403, "explicit human approval evidence is required")
    if item.event.status != "OBSERVATION":
        raise HTTPException(400, "historical imports must remain OBSERVATION")
    if item.event.kind != "INVESTIGATION":
        raise HTTPException(400, "historical imports must use INVESTIGATION kind")
    if item.event.prior_event_id is not None:
        raise HTTPException(400, "historical candidate IDs are not live prior_event_id values")

    payload_hash = digest(item.event.payload)
    imported_at = now()
    event_id = str(uuid.uuid4())

    with db() as con:
        try:
            result = historical_import.import_once(
                con,
                candidate_id=item.candidate_id,
                idempotency_key=item.idempotency_key,
                payload_hash=payload_hash,
                source_hash=item.source_hash,
                approval_evidence_json=canonical(item.approval_evidence),
                imported_at=imported_at,
                append_event=lambda: _insert_historical_event(con, event_id, imported_at, item.event, payload_hash),
            )
        except historical_import.HistoricalImportConflict as exc:
            raise HTTPException(409, str(exc)) from exc
    return {**result, "append_only": True, "observation_status": "OBSERVATION"}


def _insert_historical_event(
    con: sqlite3.Connection,
    event_id: str,
    recorded_at: str,
    item: EventIn,
    payload_hash: str,
) -> str:
    con.execute(
        "INSERT INTO events(id,recorded_at,kind,status,subject,payload,payload_hash,prior_event_id,source,actor) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            event_id,
            recorded_at,
            item.kind,
            "OBSERVATION",
            item.subject,
            canonical(item.payload),
            payload_hash,
            None,
            item.source,
            item.actor,
        ),
    )
    return event_id


@app.post("/v1/proposals")
def propose(item: ProposalIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_write(authorization)
    proposal_id = str(uuid.uuid4())
    with db() as con:
        con.execute(
            "INSERT INTO proposals(id,created_at,subject,prior_event_id,proposed_payload,proposed_hash) VALUES(?,?,?,?,?,?)",
            (proposal_id, now(), item.subject, item.prior_event_id, canonical(item.proposed_payload), digest(item.proposed_payload)),
        )
    return {"id": proposal_id, "status": "PROPOSED", "mutation_allowed": False}


@app.post("/v1/proposals/{proposal_id}/gates/{gate}")
def gate(proposal_id: str, gate: str, item: GateIn, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_write(authorization)
    if gate not in {"necessity", "accuracy", "approval"}:
        raise HTTPException(400, "gate must be necessity, accuracy, or approval")
    allowed = {"necessity": {"PROVEN", "FAILED", "UNKNOWN"}, "accuracy": {"PROVEN", "FAILED", "UNKNOWN"}, "approval": {"APPROVED", "REJECTED", "PENDING"}}[gate]
    if item.state not in allowed:
        raise HTTPException(400, f"invalid {gate} state")
    with db() as con:
        if not con.execute("SELECT 1 FROM proposals WHERE id=?", (proposal_id,)).fetchone():
            raise HTTPException(404, "proposal not found")
        con.execute(f"UPDATE proposals SET {gate}_state=?, {gate}_evidence=? WHERE id=?", (item.state, canonical(item.evidence), proposal_id))
        row = con.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        ready = row["necessity_state"] == "PROVEN" and row["accuracy_state"] == "PROVEN" and row["approval_state"] == "APPROVED"
        con.execute("UPDATE proposals SET status=? WHERE id=?", ("AUTHORIZED" if ready else "BLOCKED", proposal_id))
    return {"id": proposal_id, "status": "AUTHORIZED" if ready else "BLOCKED", "mutation_allowed": ready}


@app.get("/v1/proposals/{proposal_id}")
def proposal(proposal_id: str) -> dict[str, Any]:
    with readonly_db() as con:
        row = con.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
    if not row:
        raise HTTPException(404, "proposal not found")
    result = dict(row)
    for key in ("proposed_payload", "necessity_evidence", "accuracy_evidence", "approval_evidence"):
        if result.get(key):
            result[key] = json.loads(result[key])
    result["mutation_allowed"] = result["necessity_state"] == "PROVEN" and result["accuracy_state"] == "PROVEN" and result["approval_state"] == "APPROVED"
    return result


# The dedicated capability cannot call the general event/proposal endpoints.
import sys
continuity_writer.install(sys.modules[__name__])
