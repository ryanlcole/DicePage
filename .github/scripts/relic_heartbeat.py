#!/usr/bin/env python3
"""Observer-only ReLiC heartbeat probe.

Reads repository evidence, emits one compact current-state heartbeat, and never
repairs or mutates source truth. The output is ephemeral CI evidence by design.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PATHS = [
    ".code-index/relic_heartbeat_contract.json",
    ".code-index/relic_paths.json",
    ".code-index/semantic_units.json",
    ".code-index/summary.json",
    ".code-index/code_database_summary.json",
    "KNOWN_ERRORS.md",
    ".github/workflows/code-index.yml",
    ".github/workflows/compliance-guardrails.yml",
    ".github/workflows/authenticated-e2e.yml",
]

CRITICAL_PATHS = [
    ".github/scripts/verify-compliance-guardrails.py",
    "tools/code_index.py",
    "tools/code_database.py",
    "tools/semantic_units.py",
]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def check_path(path: str, critical: bool = False) -> dict:
    exists = (ROOT / path).exists()
    return {
        "id": f"path:{path}",
        "state": "SAFE" if exists else ("UNSAFE" if critical else "DEGRADED"),
        "critical": critical,
        "detail": "present" if exists else "missing",
        "pointer": path,
    }


def load_json(path: str) -> tuple[dict | None, str | None]:
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8")), None
    except Exception as exc:  # bounded evidence only
        return None, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="relic-heartbeat.json")
    args = parser.parse_args()

    checks = [check_path(p, p in CRITICAL_PATHS) for p in REQUIRED_PATHS + CRITICAL_PATHS]

    summary, summary_error = load_json(".code-index/summary.json")
    checks.append({
        "id": "code-index:summary-readable",
        "state": "SAFE" if summary is not None else "UNSAFE",
        "critical": True,
        "detail": "readable" if summary is not None else summary_error,
        "pointer": ".code-index/summary.json",
    })

    semantic, semantic_error = load_json(".code-index/semantic_units.json")
    checks.append({
        "id": "semantic-units:readable",
        "state": "SAFE" if semantic is not None else "UNSAFE",
        "critical": True,
        "detail": "readable" if semantic is not None else semantic_error,
        "pointer": ".code-index/semantic_units.json",
    })

    unsafe = [c for c in checks if c["state"] == "UNSAFE"]
    degraded = [c for c in checks if c["state"] == "DEGRADED"]
    state = "UNSAFE" if unsafe else "DEGRADED" if degraded else "SAFE"

    heartbeat = {
        "schema_version": 1,
        "system": "RIST-WEB",
        "repository": os.getenv("GITHUB_REPOSITORY", "ryanlcole/DicePage"),
        "branch": os.getenv("GITHUB_REF_NAME", git("branch", "--show-current") or "detached"),
        "observed_commit": os.getenv("GITHUB_SHA", git("rev-parse", "HEAD")),
        "state": state,
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "checks": checks,
        "diagnostic_pointers": sorted({c["pointer"] for c in checks if c["state"] != "SAFE"}),
        "summary": {
            "safe": sum(c["state"] == "SAFE" for c in checks),
            "degraded": len(degraded),
            "unsafe": len(unsafe),
            "tracked_files": summary.get("tracked_files") if summary else None,
            "indexed_records": summary.get("indexed_records") if summary else None,
        },
    }

    output = Path(args.output)
    output.write_text(json.dumps(heartbeat, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "system": heartbeat["system"],
        "commit": heartbeat["observed_commit"],
        "state": state,
        "safe": heartbeat["summary"]["safe"],
        "degraded": heartbeat["summary"]["degraded"],
        "unsafe": heartbeat["summary"]["unsafe"],
        "diagnostic_pointers": heartbeat["diagnostic_pointers"],
    }, indent=2))

    # Heartbeat reports state. It deliberately does not repair anything.
    return 1 if state == "UNSAFE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
