"""Build a bounded ReLiC project-state observation from an inspected Git ref.

This adapter records repository evidence about a project. It does not copy the
project database into ReLiC, does not claim runtime truth, and cannot promote
anything to canon. The generated envelope is intended for the existing
Observatory validation/private-ingestion path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECTS = {
    "SHAELVIEN": {
        "branch": "live-alpha-rist-blazor-world",
        "paths": ["apps/rist-world/", "site/relic-home/Game/", "docs/"],
        "subject": "project-state:SHAELVIEN",
    }
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def tracked_path_listing(commit: str, path: str) -> list[str]:
    """Return tracked entries below path without depending on the worktree.

    `git ls-tree -r <commit> -- <path>` can resolve the path against the current
    index/worktree context in surprising ways when the inspected commit is from
    another fetched branch. `git ls-tree -r --name-only <commit>` gives the
    commit's complete tree directly; filtering that immutable listing keeps the
    observation tied to the inspected commit.
    """
    normalized = path.rstrip("/")
    all_paths = git("ls-tree", "-r", "--name-only", commit).splitlines()
    prefix = f"{normalized}/"
    return [entry for entry in all_paths if entry == normalized or entry.startswith(prefix)]


def build(project: str, ref: str | None = None) -> dict[str, Any]:
    cfg = PROJECTS[project]
    requested_ref = ref or cfg["branch"]
    commit = git("rev-parse", requested_ref)
    tree = git("rev-parse", f"{commit}^{{tree}}")
    committed_at = git("show", "-s", "--format=%cI", commit)
    message = git("show", "-s", "--format=%s", commit)

    path_evidence: list[dict[str, Any]] = []
    for path in cfg["paths"]:
        lines = tracked_path_listing(commit, path)
        path_evidence.append({
            "path": path,
            "tracked_entries": len(lines),
            "listing_sha256": sha256_text("\n".join(lines)),
        })

    payload = {
        "schema": "RELIC-PROJECT-STATE/1",
        "project": project,
        "partition": project,
        "repository": "ryanlcole/DicePage",
        "ref": requested_ref,
        "commit": commit,
        "tree": tree,
        "commit_message": message,
        "committed_at": committed_at,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "paths": path_evidence,
        "doctrine": {
            "observation_is_canon": False,
            "representation_is_truth": False,
            "temporal_association_is_causation": False,
        },
        "truth_boundary": {
            "current_repository_state_is_implementation_evidence": True,
            "repository_state_proves_runtime": False,
            "representation_is_truth": False,
            "memory_is_canon": False,
            "observation_is_canon": False,
            "automatic_canon_promotion": False,
        },
        "purpose": "Bounded Shaelvien project-mind evidence for continuity and reconstruction.",
    }
    event = {
        "kind": "CODE_CHANGE",
        "status": "OBSERVATION",
        "subject": cfg["subject"],
        "payload": payload,
        "prior_event_id": None,
        "source": "GIT_REPOSITORY",
        "actor": "RELIC_PROJECT_OBSERVER",
    }
    return {
        "schema": "RELIC-OBSERVATORY/1",
        "event": event,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", choices=sorted(PROJECTS), default="SHAELVIEN")
    parser.add_argument("--ref")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    document = build(args.project, args.ref)
    text = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
