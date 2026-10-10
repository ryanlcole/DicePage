"""Read-only MCP interface for the independent ReLiC continuity host.

This adapter exposes bounded retrieval tools over MCP. It deliberately does not
expose append, proposal-gate, delete, shell, database, or external mutation
operations. ReLiC remains the continuity authority; MCP is a representation and
retrieval boundary only.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from mcp.server.fastmcp import FastMCP

import app as relic

mcp = FastMCP(
    "ReLiC",
    instructions=(
        "ReLiC is an observer-first continuity source. Representation is not "
        "truth. Return stored evidence with status, provenance, sequence, and "
        "hashes intact. Do not promote observations or hypotheses to canon."
    ),
)


def _event(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["payload"] = json.loads(result["payload"])
    return result


@mcp.tool()
def relic_get_event(event_id: str) -> dict[str, Any]:
    """Fetch one ReLiC event by immutable event ID. Read-only."""
    relic.init()
    with relic.db() as con:
        row = con.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not row:
        return {"found": False, "event_id": event_id}
    return {"found": True, "event": _event(row)}


@mcp.tool()
def relic_search(query: str, limit: int = 20) -> dict[str, Any]:
    """Search bounded ReLiC event fields and payload text. Read-only."""
    relic.init()
    bounded_limit = max(1, min(int(limit), 100))
    needle = f"%{query}%"
    with relic.db() as con:
        rows = con.execute(
            """
            SELECT * FROM events
            WHERE subject LIKE ? COLLATE NOCASE
               OR kind LIKE ? COLLATE NOCASE
               OR status LIKE ? COLLATE NOCASE
               OR payload LIKE ? COLLATE NOCASE
               OR source LIKE ? COLLATE NOCASE
               OR actor LIKE ? COLLATE NOCASE
            ORDER BY seq DESC
            LIMIT ?
            """,
            (needle, needle, needle, needle, needle, needle, bounded_limit),
        ).fetchall()
    return {
        "query": query,
        "count": len(rows),
        "events": [_event(row) for row in rows],
        "representation_is_truth": False,
    }


@mcp.tool()
def relic_context_pack(query: str, limit: int = 20) -> dict[str, Any]:
    """Return a bounded continuity pack relevant to a query. Read-only.

    The pack preserves each stored event's status and provenance. It is context
    for an AI client, not automatic canon and not permission to mutate anything.
    """
    result = relic_search(query=query, limit=limit)
    return {
        "format": "RELIC-CONTEXT/1",
        "query": query,
        "laws": [
            "IDENTITY!=REPRESENTATION",
            "REPRESENTATION!=TRUTH",
            "UNKNOWN!=FACT",
            "MEMORY!=CANON",
        ],
        "authority": "ReLiC durable event store",
        "observer_only": True,
        "events": result["events"],
        "count": result["count"],
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
