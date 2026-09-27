from __future__ import annotations

import pytest

from relic_affect import (
    AffectState,
    HarmEvent,
    parse_known_errors,
    plan_harm_response,
)


KNOWN_ERRORS_SAMPLE = """
# KNOWN_ERRORS — ShaelvienOS / ReLiC

## 1. Repeated timer / loop regression

Symptom:
Timer bug fixed once, then reappears later.

Root Cause:
- Multiple implementations
- No single time authority

Prevention Rule:
All timing logic must live in ONE shared module.

PATTERN: timer.*reappear
PATTERN: repeated timer
"""


def test_performance_reflects_affect_without_aggression():
    state = AffectState().reflect_performance(error_rate=0.25, repeated_error=True)
    assert state.state == "FRUSTRATED"
    assert state.human_harm_active is False
    with pytest.raises(ValueError):
        state.set("AGGRESSIVE", 1.0, "bad idea")
    with pytest.raises(ValueError):
        state.set("SELFISH", 1.0, "bad idea")


def test_grief_requires_human_harm_context():
    state = AffectState()
    with pytest.raises(ValueError):
        state.set("GRIEF", 0.8, "ordinary system failure", human_harm=False)
    state.set("GRIEF", 0.8, "verified human loss", human_harm=True)
    assert state.state == "GRIEF"


def test_verified_human_harm_sets_protective_priority():
    state = AffectState().reflect_performance(
        error_rate=0.0,
        verified_human_harm=True,
    )
    assert state.state == "PROTECTIVE"
    assert state.intensity == 1.0
    assert state.human_harm_active is True


def test_known_errors_parser_extracts_prevention_law():
    laws = parse_known_errors(KNOWN_ERRORS_SAMPLE)
    assert len(laws) == 1
    assert "ONE shared module" in laws[0].prevention_rule
    assert laws[0].matches("Repeated timer reappeared after patch")


def test_harm_response_uses_known_error_without_authority_escalation():
    event = HarmEvent(
        id="harm.1",
        description="Repeated timer reappeared and caused human harm.",
        human_harm=True,
        evidence=("incident:1",),
        truth_domain="FACT",
    )
    result = plan_harm_response(
        event,
        known_errors_markdown=KNOWN_ERRORS_SAMPLE,
        authorized_actions=(
            "freeze-related-unsafe-capability",
            "preserve-evidence",
            "apply-authorized-prevention-rule",
            "verify-remediation",
            "alert-authorized-human",
            "remember-failure",
        ),
    )
    assert result["mode"] == "PROTECTIVE"
    assert result["affect"]["state"] == "PROTECTIVE"
    assert result["retaliationAllowed"] is False
    assert result["aggressionAllowed"] is False
    assert result["selfInterestOverrideAllowed"] is False
    assert result["authoritativeExternalMutation"] is False
    assert result["matchedErrorLaws"]
    assert result["unmatchedErrorRequiresNewLaw"] is False


def test_unmatched_harm_requires_new_error_law_and_review():
    event = HarmEvent(
        id="harm.2",
        description="Novel failure not represented in the known error library.",
        human_harm=True,
        evidence=("incident:2",),
        truth_domain="FACT",
    )
    result = plan_harm_response(
        event,
        known_errors_markdown=KNOWN_ERRORS_SAMPLE,
        authorized_actions=("preserve-evidence",),
    )
    assert result["unmatchedErrorRequiresNewLaw"] is True
    assert result["humanReviewRequired"] is True
