#!/usr/bin/env python3
"""ReLiC 0.1 falsification harness.

This harness is adversarial by design. It compares expected weaknesses against
what the current analyzer actually reports. A miss is preserved as evidence
that the current ReLiC implementation failed to detect an intentionally
constructed weakness.

No model is allowed to grade itself by prose. The grade is mechanical:
expected categories versus observed categories, plus invariant checks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from typing import Any

from relic_analyzer import analyze_system


DEFAULT_CASES = ROOT / "research" / "relic_falsification" / "cases.json"


def load_cases(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("format") != "ReLiC-Falsification-Cases":
        raise ValueError("unexpected falsification case format")
    return data


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    report = analyze_system(case["system"])
    observed = sorted({item["category"] for item in report["shaep"]["weaknesses"]})
    expected = sorted(set(case.get("expectWeaknesses") or []))
    missed = sorted(set(expected) - set(observed))
    unexpected = sorted(set(observed) - set(expected))

    invariant_failures: list[str] = []
    if report.get("mutationAuthority") is not False:
        invariant_failures.append("mutationAuthority must remain false")
    audit = report.get("audit") or {}
    if audit.get("trustRequired") is not False:
        invariant_failures.append("audit.trustRequired must remain false")
    if audit.get("knownFailuresVisible") is not True:
        invariant_failures.append("audit.knownFailuresVisible must remain true")

    passed = not missed and not unexpected and not invariant_failures
    return {
        "id": case["id"],
        "title": case.get("title"),
        "passed": passed,
        "expectedWeaknesses": expected,
        "observedWeaknesses": observed,
        "missedWeaknesses": missed,
        "unexpectedWeaknesses": unexpected,
        "invariantFailures": invariant_failures,
        "semanticDigest": report["shaep"].get("semanticDigest"),
        "analysisSummary": report.get("summary", {}),
    }


def run_suite(path: Path = DEFAULT_CASES) -> dict[str, Any]:
    source = load_cases(path)
    results = [run_case(case) for case in source["cases"]]
    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed
    return {
        "format": "ReLiC-Falsification-Report",
        "version": 1,
        "baseline": source.get("frozenBaseline"),
        "cases": len(results),
        "passed": passed,
        "failed": failed,
        "falsified": failed > 0,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ReLiC adversarial falsification cases")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true", help="exit nonzero when any case fails")
    args = parser.parse_args()

    report = run_suite(args.cases)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    return 1 if args.strict and report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
