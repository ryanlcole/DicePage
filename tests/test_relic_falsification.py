from __future__ import annotations

from pathlib import Path

from research.relic_falsification.run_falsification import run_suite


def test_registered_falsification_cases_are_detected():
    report = run_suite(Path("research/relic_falsification/cases.json"))
    failures = {
        item["id"]: {
            "missed": item["missedWeaknesses"],
            "unexpected": item["unexpectedWeaknesses"],
            "invariants": item["invariantFailures"],
        }
        for item in report["results"]
        if not item["passed"]
    }
    assert report["failed"] == 0, failures
    assert report["falsified"] is False
