"""Translate GitHub push evidence into bounded ReLiC Observatory observations.

This module does not call ReLiC and does not hold write credentials.  It parses
GitHub's push event file, validates the minimum evidence needed for a code
observation, and emits a JSON event envelope for an authorized collector.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from observatory import Observation, code_change


def observation_from_push(payload: dict[str, Any]) -> Observation:
    repository = (payload.get("repository") or {}).get("full_name")
    ref = payload.get("ref")
    commit = payload.get("after")
    if not repository or not ref or not commit:
        raise ValueError("GitHub push requires repository.full_name, ref, and after")
    if set(str(commit)) == {"0"}:
        raise ValueError("branch deletion is not a code-state commit observation")

    commits = payload.get("commits") or []
    paths: set[str] = set()
    for item in commits:
        for key in ("added", "modified", "removed"):
            paths.update(str(path) for path in (item.get(key) or []))

    head = payload.get("head_commit") or {}
    actor = ((payload.get("sender") or {}).get("login")
             or (head.get("author") or {}).get("username")
             or (head.get("author") or {}).get("name"))

    observation = code_change(
        repository=str(repository),
        ref=str(ref),
        commit=str(commit),
        changed_paths=paths,
        actor=str(actor) if actor else None,
    )
    # Preserve bounded GitHub facts without asserting correctness or causation.
    facts = observation.payload
    facts["before"] = payload.get("before")
    facts["created"] = bool(payload.get("created", False))
    facts["forced"] = bool(payload.get("forced", False))
    facts["compare"] = payload.get("compare")
    facts["commit_count_in_payload"] = len(commits)
    return observation


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a ReLiC CODE_CHANGE observation from a GitHub push event")
    parser.add_argument("event", type=Path, help="Path to GitHub push event JSON")
    parser.add_argument("--output", type=Path, help="Write event envelope to this file")
    args = parser.parse_args()

    payload = json.loads(args.event.read_text(encoding="utf-8"))
    observation = observation_from_push(payload)
    envelope = observation.event_payload()
    rendered = json.dumps({"fingerprint": observation.fingerprint(), "event": envelope}, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
