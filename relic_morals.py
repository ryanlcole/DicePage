"""ReLiC moral-learning layer.

Raw conversations are private evidence. ReLiC may study them through an
authorized private adapter, but durable public/project knowledge stores only
de-identified moral candidates and source digests unless the owner explicitly
authorizes more.

AI-proposed morals are hypotheses. They do not become canon merely because a
model found them persuasive or recurrent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


MORAL_STATUSES = {"CANDIDATE", "REVIEWED", "REJECTED", "PROJECT_CANON"}
SUPPORT_CLASSES = {"EXPLICIT", "RECURRENT_EXPLICIT", "INFERRED_PATTERN"}
PROMOTION_SCOPES = {"PERSONAL", "PROJECT"}


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MoralEvidence:
    source_digest: str
    observed_at: str | None
    support_class: str
    provenance: str
    contradiction: bool = False

    def __post_init__(self) -> None:
        if not self.source_digest:
            raise ValueError("source_digest is required")
        if self.support_class not in SUPPORT_CLASSES:
            raise ValueError(f"invalid support class: {self.support_class}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "sourceDigest": self.source_digest,
            "observedAt": self.observed_at,
            "supportClass": self.support_class,
            "provenance": self.provenance,
            "contradiction": self.contradiction,
        }


@dataclass
class MoralCandidate:
    id: str
    statement: str
    rationale: str
    scope: str = "PROJECT"
    status: str = "CANDIDATE"
    evidence: list[MoralEvidence] = field(default_factory=list)
    contradictions: list[MoralEvidence] = field(default_factory=list)
    owner_confirmed: bool = False
    promotion_authority: bool = False

    def __post_init__(self) -> None:
        if not self.statement.strip():
            raise ValueError("moral statement is required")
        if self.status not in MORAL_STATUSES:
            raise ValueError(f"invalid moral status: {self.status}")
        if self.scope not in PROMOTION_SCOPES:
            raise ValueError(f"invalid moral scope: {self.scope}")

    def add_evidence(self, item: MoralEvidence) -> None:
        target = self.contradictions if item.contradiction else self.evidence
        if not any(existing.source_digest == item.source_digest for existing in target):
            target.append(item)

    def confirm(self) -> None:
        self.owner_confirmed = True
        if self.status == "CANDIDATE":
            self.status = "REVIEWED"

    def promote_project_canon(self) -> None:
        if not self.owner_confirmed:
            raise PermissionError("human confirmation is required before moral promotion")
        if self.scope != "PROJECT":
            raise PermissionError("only project-scoped morals can be promoted by this layer")
        if not self.evidence:
            raise ValueError("evidence is required before moral promotion")
        self.status = "PROJECT_CANON"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "rationale": self.rationale,
            "scope": self.scope,
            "status": self.status,
            "ownerConfirmed": self.owner_confirmed,
            "promotionAuthority": self.promotion_authority,
            "evidence": [item.as_dict() for item in self.evidence],
            "contradictions": [item.as_dict() for item in self.contradictions],
        }


def source_digest(
    *,
    source_id: str,
    observed_at: str | None,
    speaker_role: str,
    text: str,
) -> str:
    """Create a one-way source reference without persisting raw chat text."""

    return _digest({
        "sourceId": source_id,
        "observedAt": observed_at,
        "speakerRole": speaker_role,
        "text": text,
    })


def candidate_id(statement: str) -> str:
    return "moral." + _digest({"statement": " ".join(statement.lower().split())})[:16]


def candidate_from_observation(observation: Mapping[str, Any]) -> MoralCandidate:
    """Normalize one privately extracted moral observation.

    Expected fields:
      statement, rationale, sourceId, observedAt, speakerRole, supportClass,
      provenance, text

    The returned candidate never contains raw text.
    """

    if observation.get("sensitiveInference"):
        raise ValueError("sensitive-trait inference is not permitted in moral learning")

    statement = str(observation.get("statement") or "").strip()
    rationale = str(observation.get("rationale") or "").strip()
    raw_text = str(observation.get("text") or "")
    support_class = str(observation.get("supportClass") or "INFERRED_PATTERN").upper()
    provenance = str(observation.get("provenance") or "HUMAN")
    observed_at = observation.get("observedAt")
    digest = source_digest(
        source_id=str(observation.get("sourceId") or "private-chat"),
        observed_at=str(observed_at) if observed_at is not None else None,
        speaker_role=str(observation.get("speakerRole") or "user"),
        text=raw_text,
    )
    evidence = MoralEvidence(
        source_digest=digest,
        observed_at=str(observed_at) if observed_at is not None else None,
        support_class=support_class,
        provenance=provenance,
        contradiction=bool(observation.get("contradiction")),
    )
    candidate = MoralCandidate(
        id=candidate_id(statement),
        statement=statement,
        rationale=rationale,
        scope=str(observation.get("scope") or "PROJECT").upper(),
    )
    candidate.add_evidence(evidence)
    return candidate


def merge_candidates(candidates: Iterable[MoralCandidate]) -> list[MoralCandidate]:
    """Deduplicate moral identity while preserving all unique evidence."""

    merged: dict[str, MoralCandidate] = {}
    for candidate in candidates:
        current = merged.get(candidate.id)
        if current is None:
            current = MoralCandidate(
                id=candidate.id,
                statement=candidate.statement,
                rationale=candidate.rationale,
                scope=candidate.scope,
                status=candidate.status,
            )
            merged[candidate.id] = current
        for item in candidate.evidence:
            current.add_evidence(item)
        for item in candidate.contradictions:
            current.add_evidence(item)
    return [merged[key] for key in sorted(merged)]


def export_registry(candidates: Iterable[MoralCandidate]) -> dict[str, Any]:
    items = list(candidates)
    return {
        "format": "ReLiC-Moral-Registry",
        "version": 1,
        "rawChatPersisted": False,
        "automaticCanonPromotion": False,
        "sensitiveTraitInference": False,
        "candidates": [item.as_dict() for item in items],
    }
