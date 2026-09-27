#!/usr/bin/env python3
"""Validate and normalize an independent ReLiC audit response.

External criticism is preserved as evidence, never promoted directly to canon.
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

from relic_core import Shaep, glyph, rune


ALLOWED_PROVENANCE = {"HUMAN", "OUTSIDER_AI"}
ALLOWED_SEVERITY = {"info", "review", "block"}


def validate_response(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(value.get("reviewer") or "").strip():
        errors.append("reviewer is required")
    if value.get("provenance") not in ALLOWED_PROVENANCE:
        errors.append("provenance must be HUMAN or OUTSIDER_AI")
    if not str(value.get("baselineCommit") or "").strip():
        errors.append("baselineCommit is required")
    findings = value.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        return errors
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            errors.append(f"findings[{index}] must be an object")
            continue
        for key in ("id", "target", "claim", "evidence", "counterexample", "expectedBehavior"):
            if not str(finding.get(key) or "").strip():
                errors.append(f"findings[{index}].{key} is required")
        if finding.get("severity") not in ALLOWED_SEVERITY:
            errors.append(f"findings[{index}].severity is invalid")
        confidence = finding.get("confidence")
        if confidence is not None:
            try:
                numeric = float(confidence)
            except (TypeError, ValueError):
                errors.append(f"findings[{index}].confidence must be numeric or null")
            else:
                if not 0.0 <= numeric <= 1.0:
                    errors.append(f"findings[{index}].confidence must be in [0,1]")
    return errors


def normalize_response(value: dict[str, Any]) -> dict[str, Any]:
    errors = validate_response(value)
    if errors:
        return {"valid": False, "errors": errors}

    reviewer = str(value["reviewer"])
    provenance = str(value["provenance"])
    baseline = str(value["baselineCommit"])
    shaep = Shaep.for_subject(f"external-audit:{baseline}:{reviewer}")

    baseline_rune = rune(
        "audit-baseline",
        baseline,
        identity=f"baseline.{baseline}",
        truth_domain="FACT",
        provenance=provenance,
        source=reviewer,
    )
    shaep.add_rune(baseline_rune)

    for finding in value["findings"]:
        finding_id = str(finding["id"])
        observation = rune(
            "external-audit-finding",
            {
                "target": finding["target"],
                "claim": finding["claim"],
                "evidence": finding["evidence"],
                "counterexample": finding["counterexample"],
                "expectedBehavior": finding["expectedBehavior"],
                "severity": finding["severity"],
                "confidence": finding.get("confidence"),
            },
            identity=f"audit.finding.{finding_id}",
            truth_domain="HYPOTHESIS",
            provenance=provenance,
            source=reviewer,
        )
        shaep.add_rune(observation)
        shaep.add_glyph(
            glyph(
                "challenges",
                [observation, baseline_rune],
                truth_domain="HYPOTHESIS",
                conditions=("requires-independent-verification", "not-canon-by-submission"),
            )
        )

    return {
        "valid": True,
        "promotionAuthority": False,
        "truthDomain": "HYPOTHESIS",
        "provenance": provenance,
        "shaep": shaep.as_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("response_json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    value = json.loads(args.response_json.read_text(encoding="utf-8"))
    result = normalize_response(value)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if result.get("valid") else 2


if __name__ == "__main__":
    raise SystemExit(main())
