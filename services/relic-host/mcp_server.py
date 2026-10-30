"""Read-only retrieval plus an opt-in, scoped continuity submission bridge.

Database access remains read-only. Only the independent host commits events.
No proposal-gate, delete, shell, or external mutation operations are exposed.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

import app as relic
from continuity_writer import ContinuityEvent
from continuity_client import submit

PROJECTLOPEDIA_PATH = Path(__file__).with_name("project_memory_targets.json")

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


def _projectlopedia() -> dict[str, Any]:
    if not PROJECTLOPEDIA_PATH.is_file():
        return {}
    return json.loads(PROJECTLOPEDIA_PATH.read_text(encoding="utf-8"))


@mcp.tool()
def relic_get_event(event_id: str) -> dict[str, Any]:
    """Fetch one ReLiC event by immutable event ID. Read-only."""
    with relic.readonly_db() as con:
        row = con.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    if not row:
        return {"found": False, "event_id": event_id}
    return {"found": True, "event": _event(row)}


@mcp.tool()
def relic_search(query: str, limit: int = 20) -> dict[str, Any]:
    """Search bounded ReLiC event fields and payload text. Read-only."""
    bounded_limit = max(1, min(int(limit), 100))
    needle = f"%{query}%"
    with relic.readonly_db() as con:
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
    """Return a bounded continuity pack relevant to a query. Read-only."""
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


@mcp.tool()
def relic_project_context(project: str = "RELIC_CORE", query: str = "", limit: int = 20) -> dict[str, Any]:
    """Read bounded Projectlopedia pointers and project methodology. Read-only.

    Source content is not copied into this response. External knowledge remains
    at its source identity and is returned as a connector/reference only.
    """
    data = _projectlopedia()
    if not data:
        return {"available": False, "project": project, "observer_only": True}
    bounded_limit = max(1, min(int(limit), 100))
    projects = data.get("projects", {})
    selected = projects.get(project)
    if selected is None:
        return {
            "available": True,
            "found": False,
            "project": project,
            "known_projects": list(projects)[:bounded_limit],
            "observer_only": True,
        }
    refs = data.get("external_references", {})
    connected = []
    for identity in selected.get("connects", []):
        if identity in refs:
            connected.append({"identity": identity, **refs[identity]})
    needle = query.casefold().strip()
    if needle:
        connected = [
            item for item in connected
            if needle in item["identity"].casefold()
            or needle in item.get("title", "").casefold()
            or needle in item.get("source", "").casefold()
        ]
    return {
        "available": True,
        "found": True,
        "schema": data.get("schema"),
        "name": data.get("name", "Projectlopedia"),
        "project": project,
        "query": query,
        "project_definition": selected,
        "connected_sources": connected[:bounded_limit],
        "source_domains": data.get("source_domains", {}),
        "behavior": data.get("behavior", {}),
        "observer_only": True,
        "representation_is_truth": False,
        "source_content_copied": False,
    }


if os.getenv("RELIC_MCP_APPEND_ENABLED") == "1":
    @mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False,
                           "idempotentHint": True, "openWorldHint": False})
    def relic_append_event(event: ContinuityEvent) -> dict[str, Any]:
        """Append authorized continuity through the dedicated ReLiC host writer.

        Supply only significant, authorized project history and source pointers.
        Omit credentials and unnecessary personal information. Keep the exact same
        record and idempotency_key when retrying. A changed record needs a new key.
        Corrections reference prior_event_id; they never overwrite history.
        Classification describes the submitted claim, not independent verification.
        Persistence is confirmed only by stored=true and an immutable event_id.
        This tool cannot promote canon or modify observed systems.
        """
        return submit(event)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

