#!/usr/bin/env python3
"""ReLiC project drift reporter.

This tool warns; it does not veto changes. It compares changed paths with bounded
project targets and emits an OBSERVATION-ready report. A warning is evidence to
review, never proof that a change is wrong.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TARGETS = Path(__file__).with_name("project_memory_targets.json")

PATH_PROJECTS = {
    "services/relic-host/": "RELIC_CORE",
    "infra/aws/relic-observatory": "RELIC_OBSERVATORY",
    "site/relic-home/relic/share/": "RELIC_SHARE",
    "site/relic-home/relic/": "RELIC_CORE",
    "apps/rist-world/": "RIST",
}


def classify(path: str) -> list[str]:
    hits = []
    for prefix, project in PATH_PROJECTS.items():
        if path.startswith(prefix):
            hits.append(project)
    return sorted(set(hits))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--paths-file")
    ap.add_argument("--output")
    args = ap.parse_args()

    paths = list(args.paths)
    if args.paths_file:
        paths.extend(p.strip() for p in Path(args.paths_file).read_text(encoding="utf-8").splitlines() if p.strip())

    targets = json.loads(TARGETS.read_text(encoding="utf-8"))
    affected = sorted({p for path in paths for p in classify(path)})
    unknown_paths = sorted(path for path in paths if not classify(path))

    report = {
        "schema": "RELIC-DRIFT-REPORT/1",
        "status": "OBSERVATION",
        "policy": "WARN_ONLY",
        "automatic_canon_promotion": False,
        "changed_paths": sorted(set(paths)),
        "affected_projects": affected,
        "project_targets": {p: targets["projects"][p] for p in affected},
        "unclassified_paths": unknown_paths,
        "warnings": [],
    }
    if affected:
        report["warnings"].append(
            "Review changed behavior against the listed intended project targets. Drift is permitted; preserve why it changed."
        )
    if unknown_paths:
        report["warnings"].append(
            "Some changed paths are not mapped to a project memory. This is UNKNOWN classification, not proof of drift."
        )

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    return 0  # Warning-only by doctrine.


if __name__ == "__main__":
    raise SystemExit(main())
