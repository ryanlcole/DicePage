"""Approval-gated, idempotent historical migration support for ReLiC.

This module does not ingest anything by itself. The host endpoint calls it only
after write authorization and explicit per-request human approval.

Historical material is appended as OBSERVATION evidence. It is never promoted
to canon by this adapter, and existing ReLiC events are never rewritten.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Callable


class HistoricalImportConflict(ValueError):
    """The same candidate/idempotency key was presented with different data."""


def init_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS historical_import_ledger (
          candidate_id TEXT PRIMARY KEY,
          idempotency_key TEXT NOT NULL UNIQUE,
          event_id TEXT NOT NULL UNIQUE,
          payload_hash TEXT NOT NULL,
          imported_at TEXT NOT NULL,
          approval_evidence TEXT NOT NULL,
          source_hash TEXT,
          FOREIGN KEY(event_id) REFERENCES events(id)
        );
        CREATE INDEX IF NOT EXISTS idx_historical_import_event
          ON historical_import_ledger(event_id);
        """
    )


def lookup(
    con: sqlite3.Connection,
    *,
    candidate_id: str,
    idempotency_key: str,
) -> sqlite3.Row | None:
    return con.execute(
        """SELECT * FROM historical_import_ledger
           WHERE candidate_id=? OR idempotency_key=?""",
        (candidate_id, idempotency_key),
    ).fetchone()


def import_once(
    con: sqlite3.Connection,
    *,
    candidate_id: str,
    idempotency_key: str,
    payload_hash: str,
    source_hash: str | None,
    approval_evidence_json: str,
    imported_at: str,
    append_event: Callable[[], str],
) -> dict[str, Any]:
    """Append once and record the stable candidate -> live-event mapping.

    The event insert and ledger insert share the caller's SQLite transaction.
    A retry returns the prior event id without appending another event. A reuse
    of a candidate/key with different payload/source evidence is rejected.
    """
    existing = lookup(
        con,
        candidate_id=candidate_id,
        idempotency_key=idempotency_key,
    )
    if existing:
        if (
            existing["candidate_id"] != candidate_id
            or existing["idempotency_key"] != idempotency_key
            or existing["payload_hash"] != payload_hash
            or existing["source_hash"] != source_hash
        ):
            raise HistoricalImportConflict(
                "historical import candidate/idempotency key already maps to different evidence"
            )
        return {
            "stored": True,
            "duplicate": True,
            "candidate_id": candidate_id,
            "idempotency_key": idempotency_key,
            "event_id": existing["event_id"],
            "payload_hash": existing["payload_hash"],
            "canon_promoted": False,
        }

    event_id = append_event()
    con.execute(
        """INSERT INTO historical_import_ledger(
             candidate_id,idempotency_key,event_id,payload_hash,imported_at,
             approval_evidence,source_hash
           ) VALUES(?,?,?,?,?,?,?)""",
        (
            candidate_id,
            idempotency_key,
            event_id,
            payload_hash,
            imported_at,
            approval_evidence_json,
            source_hash,
        ),
    )
    return {
        "stored": True,
        "duplicate": False,
        "candidate_id": candidate_id,
        "idempotency_key": idempotency_key,
        "event_id": event_id,
        "payload_hash": payload_hash,
        "canon_promoted": False,
    }
