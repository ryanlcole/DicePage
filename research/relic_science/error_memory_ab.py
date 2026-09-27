#!/usr/bin/env python3
"""A/B evaluator for preserved-failure memory without model retraining.

The harness compares two otherwise matched runs:
A = error memory disabled
B = normalized prior-failure constraints enabled

It evaluates outcomes; it does not manufacture solver behavior.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


BOOLEAN_FIELDS = ("success", "repeatedError", "regression")


def _rate(rows: list[dict[str, Any]], key: str) -> float | None:
    vals = [bool(r.get(key)) for r in rows if key in r]
    return sum(vals) / len(vals) if vals else None


def _mean(rows: list[dict[str, Any]], key: str) -> float | None:
    vals = []
    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        try:
            vals.append(float(value))
        except (TypeError, ValueError):
            continue
    return statistics.fmean(vals) if vals else None


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n": len(rows),
        "successRate": _rate(rows, "success"),
        "repeatedErrorRate": _rate(rows, "repeatedError"),
        "regressionRate": _rate(rows, "regression"),
        "meanWallTimeMs": _mean(rows, "wallTimeMs"),
        "meanCpuTimeMs": _mean(rows, "cpuTimeMs"),
        "meanPeakBytes": _mean(rows, "peakBytes"),
        "meanEnergyJoules": _mean(rows, "energyJoules"),
    }


def _delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return b - a


def compare(records: list[dict[str, Any]]) -> dict[str, Any]:
    a = [r for r in records if str(r.get("condition", "")).upper() == "A"]
    b = [r for r in records if str(r.get("condition", "")).upper() == "B"]
    if not a or not b:
        raise ValueError("records must contain both condition A and condition B")

    sa = summarize(a)
    sb = summarize(b)
    return {
        "conditionA": sa,
        "conditionB": sb,
        "deltaBMinusA": {
            "successRate": _delta(sa["successRate"], sb["successRate"]),
            "repeatedErrorRate": _delta(sa["repeatedErrorRate"], sb["repeatedErrorRate"]),
            "regressionRate": _delta(sa["regressionRate"], sb["regressionRate"]),
            "meanWallTimeMs": _delta(sa["meanWallTimeMs"], sb["meanWallTimeMs"]),
            "meanCpuTimeMs": _delta(sa["meanCpuTimeMs"], sb["meanCpuTimeMs"]),
            "meanPeakBytes": _delta(sa["meanPeakBytes"], sb["meanPeakBytes"]),
            "meanEnergyJoules": _delta(sa["meanEnergyJoules"], sb["meanEnergyJoules"]),
        },
        "interpretationRule": (
            "Error memory is supported only when matched trials show fewer repeated/regressed "
            "failures or higher task success without an unacceptable resource penalty. Exact-string "
            "memorization alone is insufficient; controlled variants should be included."
        ),
        "truthDomain": "HYPOTHESIS",
    }


def paired_case_check(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_case: dict[str, dict[str, dict[str, Any]]] = {}
    for row in records:
        case = str(row.get("caseId") or "")
        condition = str(row.get("condition") or "").upper()
        if not case or condition not in {"A", "B"}:
            continue
        by_case.setdefault(case, {})[condition] = row
    paired = {k: v for k, v in by_case.items() if {"A", "B"} <= set(v)}
    improvements = 0
    regressions = 0
    unchanged = 0
    for pair in paired.values():
        a_success = bool(pair["A"].get("success"))
        b_success = bool(pair["B"].get("success"))
        if b_success and not a_success:
            improvements += 1
        elif a_success and not b_success:
            regressions += 1
        else:
            unchanged += 1
    return {
        "pairedCases": len(paired),
        "successImprovements": improvements,
        "successRegressions": regressions,
        "successUnchanged": unchanged,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ReLiC error-memory A/B evaluator")
    parser.add_argument("records_json")
    args = parser.parse_args()
    records = json.loads(Path(args.records_json).read_text(encoding="utf-8"))
    result = compare(records)
    result["pairedCaseCheck"] = paired_case_check(records)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
