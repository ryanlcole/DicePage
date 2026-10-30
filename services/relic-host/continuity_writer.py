"""Narrow continuity capability; never exposes the host's general write token."""
from __future__ import annotations

import hmac
import json
import os
import re
import uuid
from contextlib import closing
from datetime import datetime
from typing import Literal

from fastapi import Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from starlette.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ContinuityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project: str = Field(pattern=r"^[A-Z][A-Z0-9_]{0,63}$")
    idempotency_key: str = Field(pattern=r"^[A-Za-z0-9._:-]{8,128}$")
    classification: Literal[
        "OBSERVATION", "INTENT", "DECISION", "IMPLEMENTATION_EVIDENCE",
        "VERIFIED_BEHAVIOR", "ERROR", "CONTRADICTION", "DRIFT",
        "COMPLIANCE_CHECK", "WARNING", "HYPOTHESIS", "UNKNOWN",
    ]
    subject: str = Field(min_length=1, max_length=256)
    summary: str = Field(min_length=1, max_length=12000)
    source_refs: list[str] = Field(min_length=1, max_length=32)
    occurred_at: datetime
    prior_event_id: uuid.UUID | None = None

    @field_validator("occurred_at")
    @classmethod
    def timezone_required(cls, value):
        if value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value

    @field_validator("source_refs")
    @classmethod
    def bounded_refs(cls, refs):
        if any(not ref.strip() or len(ref) > 2048 for ref in refs):
            raise ValueError("source references must be nonempty and at most 2048 characters")
        return refs

    @field_validator("subject", "summary")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("text must not be blank")
        return value

    @model_validator(mode="after")
    def minimize(self):
        text = self.model_dump_json()
        if len(text.encode()) > 32768:
            raise ValueError("continuity record exceeds 32 KiB")
        # Defense in depth only: callers must omit secrets and unnecessary PII.
        if re.search(r"(?i)(bearer\s+\S+|-----BEGIN .*PRIVATE KEY|\bAKIA[A-Z0-9]{16}\b|\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}|(?:password|api[_-]?key|access[_-]?token|secret)\s*[:=]\s*\S+)", text):
            raise ValueError("possible credential material is not allowed")
        return self


def init_schema(con):
    con.execute("""CREATE TABLE IF NOT EXISTS continuity_receipts (
        actor TEXT NOT NULL, project TEXT NOT NULL, request_key TEXT NOT NULL,
        request_hash TEXT NOT NULL, event_id TEXT NOT NULL UNIQUE,
        PRIMARY KEY(actor, project, request_key),
        FOREIGN KEY(event_id) REFERENCES events(id)
    )""")


def authorize(authorization, project):
    token = os.getenv("RELIC_APPEND_TOKEN", "")
    actor = os.getenv("RELIC_APPEND_ACTOR", "")
    projects = set(filter(None, os.getenv("RELIC_APPEND_PROJECTS", "").split(",")))
    if not token or not actor or not projects:
        raise HTTPException(503, "continuity writer is not configured")
    if token == os.getenv("RELIC_WRITE_TOKEN", ""):
        raise HTTPException(503, "continuity credential must be separate from general writer")
    if not hmac.compare_digest((authorization or "").encode(), f"Bearer {token}".encode()):
        raise HTTPException(401, "continuity authorization required")
    if project not in projects:
        raise HTTPException(403, "project is outside this capability")
    return actor


def append(relic, item, authorization):
    actor = authorize(authorization, item.project)
    request = item.model_dump(mode="json")
    request_hash = relic.digest(request)
    payload = {
        "schema": "RELIC-CONTINUITY/1", "project": item.project,
        "classification": item.classification, "summary": item.summary,
        "source_refs": item.source_refs, "occurred_at": request["occurred_at"],
        "provenance": {"submitted_by": actor, "origin": "OUTSIDER_AI",
                       "claims_independently_verified": False},
        "doctrine": {"observation_is_canon": False, "memory_is_canon": False,
                     "representation_is_truth": False},
    }
    duplicate = False
    # One transaction serializes retries and commits the event and receipt together.
    with closing(relic.db()) as con, con:
        con.execute("BEGIN IMMEDIATE")
        previous = con.execute(
            "SELECT request_hash,event_id FROM continuity_receipts WHERE actor=? AND project=? AND request_key=?",
            (actor, item.project, item.idempotency_key),
        ).fetchone()
        if previous:
            if previous["request_hash"] != request_hash:
                raise HTTPException(409, "idempotency key already used for a different record")
            event_id = previous["event_id"]
            duplicate = True
        else:
            prior = str(item.prior_event_id) if item.prior_event_id else None
            if prior:
                row = con.execute("SELECT payload FROM events WHERE id=?", (prior,)).fetchone()
                if not row or json.loads(row["payload"]).get("project") != item.project:
                    raise HTTPException(400, "prior event must exist in the same project")
            event_id = str(uuid.uuid4())
            con.execute(
                "INSERT INTO events(id,recorded_at,kind,status,subject,payload,payload_hash,prior_event_id,source,actor) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (event_id, relic.now(), "CONTINUITY", "OBSERVATION",
                 f"continuity:{item.project}:{item.subject}", relic.canonical(payload),
                 relic.digest(payload), prior, "MCP_CONTINUITY_SUBMISSION", actor),
            )
            con.execute("INSERT INTO continuity_receipts VALUES(?,?,?,?,?)",
                        (actor, item.project, item.idempotency_key, request_hash, event_id))
        row = con.execute("SELECT seq,recorded_at,payload_hash FROM events WHERE id=?", (event_id,)).fetchone()
        receipt = {"stored": True, "event_id": event_id, "project": item.project,
                   "duplicate": duplicate, "append_only": True, "canon_promoted": False,
                   "status": "OBSERVATION", "request_hash": request_hash, **dict(row)}
    # This return is deliberately after successful COMMIT.
    return receipt


def install(relic):
    @relic.app.middleware("http")
    async def bound_continuity_body(request, call_next):
        if request.url.path == "/v1/continuity-events":
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 65536:
                    return JSONResponse({"detail": "continuity request too large"}, status_code=413)
            request._body = bytes(body)
        return await call_next(request)

    @relic.app.exception_handler(RequestValidationError)
    async def private_validation_error(request, exc):
        if request.url.path == "/v1/continuity-events":
            # Pydantic errors otherwise echo submitted values, possibly secrets.
            return JSONResponse({"detail": "invalid continuity record; check schema, bounds, timestamp and omit secrets"}, status_code=422)
        return await request_validation_exception_handler(request, exc)

    @relic.app.post("/v1/continuity-events")
    def append_continuity(item: ContinuityEvent, authorization: str | None = Header(default=None)):
        return append(relic, item, authorization)
