"""Authorized collector for ReLiC Observatory evidence.

The collector is deliberately separate from AI-facing MCP. It accepts a locally
generated Observatory envelope, validates its bounded status, and appends it to
ReLiC's authenticated /v1/events endpoint. Credentials come only from runtime
environment variables and are never written into an artifact.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from observatory_ingest.validation import validate_envelope


def append(url: str, token: str, event: dict[str, Any]) -> dict[str, Any]:
    target = url.rstrip("/") + "/v1/events"
    request = urllib.request.Request(
        target,
        data=json.dumps(event, sort_keys=True).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ReLiC append failed with HTTP {exc.code}: {detail}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Append validated Observatory evidence to ReLiC")
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="validate without contacting ReLiC")
    args = parser.parse_args()

    document = json.loads(args.evidence.read_text(encoding="utf-8"))
    event = validate_envelope(document)
    if args.dry_run:
        print(json.dumps({"valid": True, "kind": event["kind"], "subject": event["subject"]}, sort_keys=True))
        return 0

    url = os.getenv("RELIC_INGEST_URL", "")
    token = os.getenv("RELIC_WRITE_TOKEN", "")
    if not url or not token:
        raise SystemExit("RELIC_INGEST_URL and RELIC_WRITE_TOKEN are required")
    result = append(url, token, event)
    print(json.dumps({"stored": True, "id": result.get("id"), "payload_hash": result.get("payload_hash")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
