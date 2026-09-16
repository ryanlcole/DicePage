#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def require_file(path: str) -> Path:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"COMPLIANCE GUARDRAIL FAILED: required file missing: {path}")
    return target


def require_text(path: str, phrases: list[str]) -> None:
    text = require_file(path).read_text(encoding="utf-8")
    for phrase in phrases:
        if phrase not in text:
            raise SystemExit(
                f"COMPLIANCE GUARDRAIL FAILED: {path} no longer contains required contract text: {phrase!r}"
            )


required_files = [
    "docs/SHAELVIEN_COMPLIANCE_PRECEDENCE.md",
    "apps/rist-world/AUTHORITY_SYSTEM.md",
    "apps/rist-world/wwwroot/ai-policy.json",
    "apps/rist-world/wwwroot/terms.html",
    "apps/rist-world/wwwroot/privacy.html",
    "apps/rist-world/wwwroot/safety.html",
    "apps/rist-world/wwwroot/dmca.html",
    "apps/rist-world/wwwroot/accessibility.html",
    "apps/rist-world/wwwroot/shaelvien-semantic-runtime.js",
    "apps/rist-world/wwwroot/shaelvien-wire.js",
    "apps/rist-world/wwwroot/shaelvien-perception-runtime.js",
    "apps/rist-world/wwwroot/shaelvien-input-runtime.js",
]
for item in required_files:
    require_file(item)

policy = json.loads(require_file("apps/rist-world/wwwroot/ai-policy.json").read_text(encoding="utf-8"))
checks = {
    "defaultDecision": policy.get("defaultDecision") == "DENY",
    "human affirmative agreement": policy.get("humanTerms", {}).get("affirmativeAgreementRequired") is True,
    "AI machine-readable notice": policy.get("aiTerms", {}).get("machineReadableNoticeRequired") is True,
    "AI worldbuilder human review": policy.get("aiTerms", {}).get("humanReviewRequiredBeforeCapability") is True,
    "natural language grants no authority": policy.get("identity", {}).get("naturalLanguageGrantsAuthority") is False,
    "player creations cannot be altered without authorization": policy.get("playerCreations", {}).get("alterWithoutAuthorization") is False,
    "player creations cannot be reused without authorization/lawful basis": policy.get("playerCreations", {}).get("reuseWithoutAuthorizationOrLawfulBasis") is False,
    "AI may not evade human rule/law tests": policy.get("beneficialContribution", {}).get("mayEvadeHumanRuleOrLawTests") is False,
    "substrate creates no exemption": policy.get("beneficialContribution", {}).get("substrateOrEmbodimentCreatesExemption") is False,
    "no government backdoor": policy.get("governmentAndLegal", {}).get("governmentBackdoor") is False,
    "verified lawful process required": policy.get("governmentAndLegal", {}).get("verifiedLawfulProcessRequired") is True,
    "legal disclosure limited to required scope": policy.get("governmentAndLegal", {}).get("disclosureLimitedToLegallyRequiredScope") is True,
    "unknown authority denies": policy.get("authority", {}).get("unknownOrAmbiguous") == "DENY",
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("COMPLIANCE GUARDRAIL FAILED: AI policy invariant(s) changed: " + ", ".join(failed))

require_text(
    "AGENTS.md",
    [
        "docs/SHAELVIEN_COMPLIANCE_PRECEDENCE.md",
        "fail closed or preserve the prior lawful behavior",
        "Semantic efficiency never outranks lawful human requirements",
    ],
)

require_text(
    "docs/SHAELVIEN_COMPLIANCE_PRECEDENCE.md",
    [
        "No optimization may convert DENY into ALLOW.",
        "No AI may waive a human right or legal obligation.",
        "No human instruction may authorize unlawful behavior.",
    ],
)

require_text(
    "apps/rist-world/AUTHORITY_SYSTEM.md",
    [
        "Non-delegable account security",
        "legal-agreement acceptance",
        "export of private user data",
        "otherwise deny",
    ],
)

require_text("apps/rist-world/wwwroot/terms.html", ["not intended for children under 13"])
require_text("apps/rist-world/wwwroot/privacy.html", ["not intended for children under 13"])
require_text("apps/rist-world/wwwroot/safety.html", ["TAKE IT DOWN", "within 48 hours"])

for runtime in [
    "apps/rist-world/wwwroot/shaelvien-semantic-runtime.js",
    "apps/rist-world/wwwroot/shaelvien-wire.js",
    "apps/rist-world/wwwroot/shaelvien-perception-runtime.js",
    "apps/rist-world/wwwroot/shaelvien-input-runtime.js",
]:
    source = require_file(runtime).read_text(encoding="utf-8")
    if "eval(" in source or "new Function(" in source:
        raise SystemExit(f"COMPLIANCE GUARDRAIL FAILED: arbitrary source execution found in {runtime}")

print("Compliance guardrails verified: required policy, authority, safety, age, and semantic-runtime invariants remain present.")
