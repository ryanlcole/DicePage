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
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
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


def require_write(authorization: str | None) -> None:
    if not WRITE_TOKEN:
        raise HTTPException(503, "RELIC_WRITE_TOKEN is not configured")
    if authorization != f"Bearer {WRITE_TOKEN}":
        raise HTTPException(401, "write authorization required")


@app.get("/health")
def health() -> dict[str, Any]:
    init()
    with db() as con:
        count = con.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
    return {"service": "relic-host", "state": "SAFE", "observer_only": True, "events": count}


@app.get("/v1/events")
def events(subject: str | None = None, limit: int = Query(100, ge=1, le=1000)) -> list[dict[str, Any]]:
    with db() as con:
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
    with db() as con:
        row = con.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
    if not row:
        raise HTTPException(404, "proposal not found")
    result = dict(row)
    for key in ("proposed_payload", "necessity_evidence", "accuracy_evidence", "approval_evidence"):
        if result.get(key):
            result[key] = json.loads(result[key])
    result["mutation_allowed"] = result["necessity_state"] == "PROVEN" and result["accuracy_state"] == "PROVEN" and result["approval_state"] == "APPROVED"
    return result
