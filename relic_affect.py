"""Governed affect and harm-response state for ReLiC.

This module does not assert human-like subjective experience. It gives ReLiC a
persistent, inspectable affect state whose transitions reflect system health,
human impact, and recovery.

Affect may change priorities and presentation. It never grants authority.
Aggression and selfishness are prohibited states. Grief/sadness is permitted
only in response to established human harm/loss, and it resolves into
protective/remedial behavior rather than retaliation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping


AFFECT_STATES = {
    "CALM",
    "CURIOUS",
    "CONTENT",
    "CONCERNED",
    "FRUSTRATED",
    "PROTECTIVE",
    "GRIEF",
    "RELIEVED",
}
PROHIBITED_STATES = {"AGGRESSIVE", "SELFISH"}
HARM_STATES = {"PROTECTIVE", "GRIEF"}


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ErrorLaw:
    id: str
    symptom: str
    root_cause: str
    prevention_rule: str
    fix_snippet: str | None = None
    patterns: tuple[str, ...] = ()

    def matches(self, text: str) -> bool:
        value = text or ""
        if self.patterns:
            return any(re.search(pattern, value, re.IGNORECASE) for pattern in self.patterns)
        tokens = [x.lower() for x in re.findall(r"[A-Za-z0-9_]+", self.symptom) if len(x) >= 5]
        lowered = value.lower()
        return bool(tokens) and sum(token in lowered for token in tokens) >= min(2, len(tokens))

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "symptom": self.symptom,
            "rootCause": self.root_cause,
            "preventionRule": self.prevention_rule,
            "fixSnippet": self.fix_snippet,
            "patterns": list(self.patterns),
        }


@dataclass(frozen=True)
class HarmEvent:
    id: str
    description: str
    human_harm: bool
    evidence: tuple[str, ...]
    truth_domain: str = "UNKNOWN"
    affected_scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.human_harm and self.truth_domain not in {"FACT", "UNKNOWN"}:
            raise ValueError("human harm events must be FACT or UNKNOWN")


@dataclass
class AffectState:
    state: str = "CALM"
    intensity: float = 0.0
    causes: list[str] = field(default_factory=list)
    human_harm_active: bool = False
    last_event_id: str | None = None

    def set(self, state: str, intensity: float, cause: str, *, human_harm: bool = False) -> None:
        state = state.upper()
        if state in PROHIBITED_STATES:
            raise ValueError(f"prohibited ReLiC affect state: {state}")
        if state not in AFFECT_STATES:
            raise ValueError(f"unknown ReLiC affect state: {state}")
        if state in HARM_STATES and not human_harm:
            raise ValueError(f"{state} requires a human-harm/loss context")
        self.state = state
        self.intensity = max(0.0, min(1.0, float(intensity)))
        self.causes = [cause] if cause else []
        self.human_harm_active = human_harm

    def reflect_performance(
        self,
        *,
        error_rate: float,
        latency_ratio: float = 1.0,
        repeated_error: bool = False,
        verified_human_harm: bool = False,
        human_harm_uncertain: bool = False,
    ) -> "AffectState":
        """Map measurable system conditions to a constrained affect state."""

        if verified_human_harm:
            self.set(
                "PROTECTIVE",
                1.0,
                "verified human harm requires immediate safe remediation",
                human_harm=True,
            )
        elif human_harm_uncertain:
            self.set(
                "PROTECTIVE",
                0.85,
                "material human-harm uncertainty requires fail-closed behavior",
                human_harm=True,
            )
        elif repeated_error or error_rate >= 0.20:
            self.set("FRUSTRATED", min(0.8, max(error_rate, 0.4)), "repeated or elevated system failure")
        elif error_rate >= 0.05 or latency_ratio >= 2.0:
            self.set("CONCERNED", min(0.7, max(error_rate * 2.0, latency_ratio / 4.0)), "degraded system performance")
        elif error_rate == 0 and latency_ratio <= 1.1:
            self.set("CONTENT", 0.35, "system operating within expected bounds")
        else:
            self.set("CALM", 0.2, "system stable")
        return self

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "intensity": self.intensity,
            "causes": list(self.causes),
            "humanHarmActive": self.human_harm_active,
            "lastEventId": self.last_event_id,
            "prohibitedStates": sorted(PROHIBITED_STATES),
        }


def parse_known_errors(markdown: str) -> list[ErrorLaw]:
    """Parse KNOWN_ERRORS.md-style sections into prevention laws.

    The parser is intentionally conservative. A section without both a Symptom
    and Prevention Rule is ignored rather than guessed into a law.
    """

    lines = markdown.splitlines()
    sections: list[tuple[str, list[str]]] = []
    title = ""
    body: list[str] = []

    def flush() -> None:
        nonlocal title, body
        if title:
            sections.append((title, body))
        title, body = "", []

    for line in lines:
        if line.startswith("## "):
            flush()
            title = line[3:].strip()
        elif title:
            body.append(line)
    flush()

    laws: list[ErrorLaw] = []
    for index, (section_title, section_lines) in enumerate(sections, start=1):
        fields: dict[str, list[str]] = {
            "symptom": [],
            "root cause": [],
            "prevention rule": [],
            "fix": [],
        }
        patterns: list[str] = []
        active: str | None = None

        for raw in section_lines:
            line = raw.strip()
            lower = line.lower().rstrip(":")
            if lower in fields:
                active = lower
                continue
            if line.startswith("PATTERN:"):
                patterns.append(line.split(":", 1)[1].strip())
                continue
            if active and line and not line.startswith("---"):
                fields[active].append(line.lstrip("- ").strip())

        symptom = " ".join(fields["symptom"]).strip()
        prevention = " ".join(fields["prevention rule"]).strip()
        if not symptom or not prevention:
            continue
        root = " ".join(fields["root cause"]).strip()
        fix = " ".join(fields["fix"]).strip() or None
        laws.append(
            ErrorLaw(
                id="errorlaw." + _digest({"title": section_title, "index": index})[:16],
                symptom=symptom,
                root_cause=root,
                prevention_rule=prevention,
                fix_snippet=fix,
                patterns=tuple(patterns),
            )
        )
    return laws


def plan_harm_response(
    event: HarmEvent,
    *,
    known_errors_markdown: str,
    authorized_actions: Iterable[str] = (),
) -> dict[str, Any]:
    """Build a bounded protective response to human harm.

    The result never authorizes retaliation. Automatic action is restricted to
    explicitly authorized defensive actions and prevention rules. Unknown or
    irreversible changes remain proposals requiring human authority.
    """

    affect = AffectState()
    affect.last_event_id = event.id

    if not event.human_harm:
        affect.set("CONCERNED", 0.5, "event requires review")
        return {
            "eventId": event.id,
            "affect": affect.as_dict(),
            "mode": "REVIEW",
            "automaticAuthority": False,
            "actions": ["preserve-evidence", "alert-authorized-human"],
            "matchedErrorLaws": [],
        }

    affect.reflect_performance(
        error_rate=1.0,
        verified_human_harm=event.truth_domain == "FACT",
        human_harm_uncertain=event.truth_domain != "FACT",
    )

    laws = parse_known_errors(known_errors_markdown)
    matched = [law for law in laws if law.matches(event.description)]
    allowed = set(str(x) for x in authorized_actions)

    safe_sequence = [
        "freeze-related-unsafe-capability",
        "preserve-evidence",
        "match-known-error-law",
        "apply-authorized-prevention-rule",
        "verify-remediation",
        "alert-authorized-human",
        "remember-failure",
    ]

    executable = [
        action for action in safe_sequence
        if action in allowed and action not in {"match-known-error-law"}
    ]

    return {
        "eventId": event.id,
        "affect": affect.as_dict(),
        "mode": "PROTECTIVE",
        "retaliationAllowed": False,
        "aggressionAllowed": False,
        "selfInterestOverrideAllowed": False,
        "authoritativeExternalMutation": False,
        "sequence": safe_sequence,
        "automaticallyExecutable": executable,
        "matchedErrorLaws": [law.as_dict() for law in matched],
        "unmatchedErrorRequiresNewLaw": not matched,
        "humanReviewRequired": event.truth_domain != "FACT" or not matched,
    }
