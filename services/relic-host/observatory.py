"""ReLiC Observatory: engineering experience observation gateway.

Observatory watches durable engineering facts, not AI conversations.  It turns
code changes, executions, deployments, tests, and user-reported errors into
bounded OBSERVATION records that can be appended to ReLiC by an authorized
collector.

Representation != truth.  Temporal association != causation.  An observation
never promotes itself to canon or grants mutation authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

OBSERVATION_STATUS = "OBSERVATION"
ALLOWED_KINDS = {
    "CODE_CHANGE",
    "BUILD_RESULT",
    "TEST_RESULT",
    "DEPLOYMENT",
    "RUNTIME_ERROR",
    "USER_ERROR_REPORT",
    "INVESTIGATION",
    "CORRECTIVE_CHANGE",
    "VERIFICATION",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidenceRef:
    """Pointer to source evidence.  The pointer is evidence, not a truth claim."""

    system: str
    locator: str
    observed_hash: str | None = None


@dataclass(frozen=True)
class Observation:
    kind: str
    subject: str
    payload: dict[str, Any]
    source: str
    actor: str | None = None
    prior_event_id: str | None = None
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    observed_at: str = field(default_factory=utc_now)
    status: str = OBSERVATION_STATUS

    def __post_init__(self) -> None:
        if self.kind not in ALLOWED_KINDS:
            raise ValueError(f"unsupported Observatory kind: {self.kind}")
        if self.status != OBSERVATION_STATUS:
            raise ValueError("Observatory may emit OBSERVATION records only")
        if not self.subject.strip() or not self.source.strip():
            raise ValueError("subject and source are required")

    def event_payload(self) -> dict[str, Any]:
        body = {
            "observed_at": self.observed_at,
            "facts": self.payload,
            "evidence": [asdict(ref) for ref in self.evidence],
            "doctrine": {
                "representation_is_truth": False,
                "temporal_association_is_causation": False,
                "observation_is_canon": False,
            },
        }
        return {
            "kind": self.kind,
            "status": self.status,
            "subject": self.subject,
            "payload": body,
            "prior_event_id": self.prior_event_id,
            "source": self.source,
            "actor": self.actor,
        }

    def fingerprint(self) -> str:
        """Stable collector-side dedupe key; it does not replace ReLiC's event id."""
        return digest(self.event_payload())


def code_change(*, repository: str, ref: str, commit: str, changed_paths: Iterable[str],
                actor: str | None = None) -> Observation:
    paths = sorted(set(changed_paths))
    return Observation(
        kind="CODE_CHANGE",
        subject=f"git:{repository}:{ref}",
        source="GIT_REPOSITORY",
        actor=actor,
        payload={
            "repository": repository,
            "ref": ref,
            "commit": commit,
            "changed_paths": paths,
        },
        evidence=(EvidenceRef("git", f"{repository}@{commit}"),),
    )


def user_error_report(*, product: str, report_id: str, description: str,
                      observed_version: str | None = None,
                      reporter: str | None = None,
                      source_locator: str | None = None) -> Observation:
    facts: dict[str, Any] = {
        "report_id": report_id,
        "description": description,
        "observed_version": observed_version,
        "claim_scope": "USER_REPORTED_EXPERIENCE",
        "cause": "UNKNOWN",
    }
    refs = () if not source_locator else (EvidenceRef("user_report", source_locator),)
    return Observation(
        kind="USER_ERROR_REPORT",
        subject=f"product:{product}:error:{report_id}",
        source="USER_REPORT",
        actor=reporter,
        payload=facts,
        evidence=refs,
    )


def verification(*, subject: str, result: str, method: str,
                 evidence: Iterable[EvidenceRef] = (), actor: str | None = None,
                 prior_event_id: str | None = None) -> Observation:
    normalized = result.upper()
    if normalized not in {"PASS", "FAIL", "INCONCLUSIVE"}:
        raise ValueError("verification result must be PASS, FAIL, or INCONCLUSIVE")
    return Observation(
        kind="VERIFICATION",
        subject=subject,
        source="ENGINEERING_VERIFICATION",
        actor=actor,
        prior_event_id=prior_event_id,
        payload={"result": normalized, "method": method},
        evidence=tuple(evidence),
    )
