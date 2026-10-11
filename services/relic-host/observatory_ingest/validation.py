"""Dependency-free validation boundary shared by Observatory ingestion paths.

OBSERVATION != CANON. Temporal association != causation.
"""
from __future__ import annotations

from typing import Any


def validate_envelope(document: dict[str, Any]) -> dict[str, Any]:
    event = document.get("event")
    if not isinstance(event, dict):
        raise ValueError("missing Observatory event envelope")
    required = ("kind", "status", "subject", "payload", "source")
    missing = [key for key in required if not event.get(key)]
    if missing:
        raise ValueError(f"missing event fields: {', '.join(missing)}")
    if event["status"] != "OBSERVATION":
        raise ValueError("collector accepts Observatory OBSERVATION records only")
    doctrine = (event.get("payload") or {}).get("doctrine") or {}
    if doctrine.get("observation_is_canon") is not False:
        raise ValueError("event must explicitly preserve observation != canon")
    if doctrine.get("temporal_association_is_causation") is not False:
        raise ValueError("event must explicitly preserve association != causation")
    return event
