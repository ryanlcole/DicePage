from __future__ import annotations

"""ReLiC semantic core.

ReLiC's native reasoning representation is:

    Rune -> Glyph -> Shaep

Rune
    Atomic semantic identity, observation, operation, constraint, or value.
Glyph
    Contextual compound assembled from resolved Runes.
Shaep
    Stabilized reasoning/context structure assembled from Glyphs and their
    relationships for one subject/query.

"Shaep" here is the ReLiC reasoning structure. It is deliberately distinct
from the repository's uppercase SHAEP media/archive format (Spatial Hot
Preservation Object). A Shaep may refer to a SHAEP identity without changing
that file-format contract.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional
import hashlib
import json
import time


TRUTH_DOMAINS = {"FACT", "HYPOTHESIS", "FICTION", "UNKNOWN"}
PROVENANCE_DOMAINS = {"HUMAN", "OUTSIDER_AI", "SHAELVIEN_EI", "SYSTEM", "UNKNOWN"}


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return f"{prefix}." + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Rune:
    """Atomic semantic unit.

    Identity is explicit and is never inferred solely from representation.
    """

    id: str
    kind: str
    value: Any = None
    truth_domain: str = "UNKNOWN"
    provenance: str = "UNKNOWN"
    source: Optional[str] = None
    observed_at_ms: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Rune.id is required")
        if not self.kind or not self.kind.strip():
            raise ValueError("Rune.kind is required")
        if self.truth_domain not in TRUTH_DOMAINS:
            raise ValueError(f"Unknown truth domain: {self.truth_domain}")
        if self.provenance not in PROVENANCE_DOMAINS:
            raise ValueError(f"Unknown provenance domain: {self.provenance}")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "value": self.value,
            "truthDomain": self.truth_domain,
            "provenance": self.provenance,
            "source": self.source,
            "observedAtMs": self.observed_at_ms,
        }


@dataclass(frozen=True)
class Glyph:
    """Compound semantic meaning built from already-resolved Runes."""

    id: str
    rune_ids: tuple[str, ...]
    relation: str
    truth_domain: str = "UNKNOWN"
    conditions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Glyph.id is required")
        if not self.rune_ids:
            raise ValueError("Glyph requires at least one Rune")
        if not self.relation or not self.relation.strip():
            raise ValueError("Glyph.relation is required")
        if self.truth_domain not in TRUTH_DOMAINS:
            raise ValueError(f"Unknown truth domain: {self.truth_domain}")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "runeIds": list(self.rune_ids),
            "relation": self.relation,
            "truthDomain": self.truth_domain,
            "conditions": list(self.conditions),
        }


@dataclass(frozen=True)
class Weakness:
    """Observed system weakness with explicit canon-grounded repair guidance."""

    id: str
    category: str
    summary: str
    evidence_runes: tuple[str, ...]
    canon_ids: tuple[str, ...]
    severity: str = "review"
    remediation: Optional[str] = None
    truth_domain: str = "FACT"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "summary": self.summary,
            "evidenceRunes": list(self.evidence_runes),
            "canonIds": list(self.canon_ids),
            "severity": self.severity,
            "remediation": self.remediation,
            "truthDomain": self.truth_domain,
        }


@dataclass(frozen=True)
class Update:
    """One proof/status event suitable for humans, MCP clients, or adapters."""

    id: str
    change_id: str
    status: str
    message: str
    observed_scope: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    created_at_ms: int = 0
    alert: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "changeId": self.change_id,
            "status": self.status,
            "message": self.message,
            "observedScope": list(self.observed_scope),
            "evidence": list(self.evidence),
            "createdAtMs": self.created_at_ms,
            "alert": self.alert,
        }


@dataclass
class ChangeProof:
    """Five-minute proof contract for a claimed AI change.

    claimed_scope and observed_scope are intentionally separate. Observing two
    connected models never proves a global change.
    """

    id: str
    description: str
    claimed_scope: tuple[str, ...]
    started_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    deadline_ms: int = 0
    observed_scope: set[str] = field(default_factory=set)
    evidence: List[str] = field(default_factory=list)
    updates: List[Update] = field(default_factory=list)
    verified: bool = False

    PROOF_WINDOW_MS = 5 * 60 * 1000

    def __post_init__(self) -> None:
        if not self.deadline_ms:
            self.deadline_ms = self.started_at_ms + self.PROOF_WINDOW_MS

    def add_proof(self, scope: Iterable[str], evidence: Iterable[str], now_ms: Optional[int] = None) -> Update:
        now = int(time.time() * 1000) if now_ms is None else int(now_ms)
        self.observed_scope.update(str(x) for x in scope if str(x))
        self.evidence.extend(str(x) for x in evidence if str(x))
        self.verified = bool(self.claimed_scope) and set(self.claimed_scope).issubset(self.observed_scope)
        status = "VERIFIED" if self.verified else "PARTIAL"
        update = Update(
            id=_stable_id("update", self.id, now, status, sorted(self.observed_scope), self.evidence),
            change_id=self.id,
            status=status,
            message=(
                "Claimed scope is verified by supplied evidence."
                if self.verified
                else "Proof received, but the claimed scope is not fully verified."
            ),
            observed_scope=tuple(sorted(self.observed_scope)),
            evidence=tuple(self.evidence),
            created_at_ms=now,
            alert=False,
        )
        self.updates.append(update)
        return update

    def evaluate(self, now_ms: Optional[int] = None) -> Update:
        now = int(time.time() * 1000) if now_ms is None else int(now_ms)
        if self.verified:
            status, message, alert = "VERIFIED", "Claim remains verified.", False
        elif now >= self.deadline_ms:
            status, message, alert = (
                "UNPROVEN",
                "Five-minute proof window expired before the claimed scope was verified.",
                True,
            )
        else:
            status, message, alert = (
                "PENDING",
                "Change is inside the proof window and remains unverified.",
                False,
            )
        update = Update(
            id=_stable_id("update", self.id, now, status, sorted(self.observed_scope)),
            change_id=self.id,
            status=status,
            message=message,
            observed_scope=tuple(sorted(self.observed_scope)),
            evidence=tuple(self.evidence),
            created_at_ms=now,
            alert=alert,
        )
        self.updates.append(update)
        return update

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "claimedScope": list(self.claimed_scope),
            "startedAtMs": self.started_at_ms,
            "deadlineMs": self.deadline_ms,
            "observedScope": sorted(self.observed_scope),
            "evidence": list(self.evidence),
            "verified": self.verified,
            "updates": [x.as_dict() for x in self.updates],
        }


@dataclass
class Shaep:
    """Stabilized ReLiC reasoning structure for one subject/query."""

    id: str
    subject: str
    runes: Dict[str, Rune] = field(default_factory=dict)
    glyphs: Dict[str, Glyph] = field(default_factory=dict)
    weaknesses: List[Weakness] = field(default_factory=list)
    created_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    @classmethod
    def for_subject(cls, subject: str) -> "Shaep":
        if not subject.strip():
            raise ValueError("subject is required")
        return cls(id=_stable_id("shaep", subject), subject=subject.strip())

    def add_rune(self, rune: Rune) -> Rune:
        existing = self.runes.get(rune.id)
        if existing is not None and existing != rune:
            raise ValueError(
                f"Rune identity conflict for {rune.id}; resolve identity instead of overwriting it"
            )
        self.runes[rune.id] = rune
        return rune

    def add_glyph(self, glyph: Glyph) -> Glyph:
        missing = [rid for rid in glyph.rune_ids if rid not in self.runes]
        if missing:
            raise ValueError(f"Glyph {glyph.id} references unknown Runes: {missing}")
        existing = self.glyphs.get(glyph.id)
        if existing is not None and existing != glyph:
            raise ValueError(
                f"Glyph identity conflict for {glyph.id}; resolve identity instead of overwriting it"
            )
        self.glyphs[glyph.id] = glyph
        return glyph

    def report_weakness(self, weakness: Weakness) -> Weakness:
        if not any(x.id == weakness.id for x in self.weaknesses):
            self.weaknesses.append(weakness)
        return weakness

    def as_dict(self) -> Dict[str, Any]:
        return {
            "format": "ReLiC-Shaep",
            "id": self.id,
            "subject": self.subject,
            "createdAtMs": self.created_at_ms,
            "runes": [r.as_dict() for r in self.runes.values()],
            "glyphs": [g.as_dict() for g in self.glyphs.values()],
            "weaknesses": [w.as_dict() for w in self.weaknesses],
        }


def rune(
    kind: str,
    value: Any = None,
    *,
    identity: Optional[str] = None,
    truth_domain: str = "UNKNOWN",
    provenance: str = "UNKNOWN",
    source: Optional[str] = None,
) -> Rune:
    """Create a Rune without treating its surface representation as identity."""

    rid = identity or _stable_id("rune", kind, value, truth_domain, provenance, source)
    return Rune(
        id=rid,
        kind=kind,
        value=value,
        truth_domain=truth_domain,
        provenance=provenance,
        source=source,
        observed_at_ms=int(time.time() * 1000),
    )


def glyph(
    relation: str,
    runes: Iterable[Rune],
    *,
    identity: Optional[str] = None,
    truth_domain: str = "UNKNOWN",
    conditions: Iterable[str] = (),
) -> Glyph:
    items = tuple(runes)
    if not items:
        raise ValueError("glyph requires at least one Rune")
    gid = identity or _stable_id("glyph", relation, [x.id for x in items], truth_domain, tuple(conditions))
    return Glyph(
        id=gid,
        rune_ids=tuple(x.id for x in items),
        relation=relation,
        truth_domain=truth_domain,
        conditions=tuple(conditions),
    )


# Backward-compatible hooks retained for older ReLiC experiments.
def on_power_change(prev_state: str, next_state: str) -> None:
    print(f"[relic_core] Power: {prev_state} -> {next_state}")


def resonance_for(glyph_value: dict) -> float:
    gid = glyph_value.get("id")
    table = {
        "daemon": 0.85, "tray": 0.95, "hud": 1.10, "spark": 1.60,
        "solar": 1.25, "lunar": 0.60, "stone": 0.50,
        "element": 1.40, "matter": 0.70, "dna": 1.15, "wave": 1.80,
    }
    return table.get(gid, 1.0)
