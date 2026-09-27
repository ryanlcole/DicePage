"""ReLiC semantic reasoning core.

ReLiC reasons through stable semantic structures:

Rune  -> atomic meaning, observation, value, or operation
Glyph -> typed relationship / compound meaning assembled from Runes
Shaep -> stabilized active reasoning shape assembled from Runes + Glyphs

"Shaep" here is a ReLiC reasoning shape. It is intentionally distinct from
uppercase SHAEP, the existing Spatial Hot Preservation Object media/archive
format documented in apps/rist-world/SHAEP_FORMAT.md.

Representations may change. Stable semantic identity may not silently change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import time
from typing import Any, Iterable


TRUTH_DOMAINS = frozenset({"FACT", "HYPOTHESIS", "FICTION", "UNKNOWN"})
PROVENANCE_DOMAINS = frozenset({"HUMAN", "OUTSIDER_AI", "SHAELVIEN_EI", "SYSTEM", "UNKNOWN"})


def _stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Rune:
    """Atomic semantic identity.

    A Rune is not a spelling, pixel, filename, or model utterance. Those are
    representations/provenance attached to the Rune.
    """

    id: str
    value: Any = None
    truth_domain: str = "UNKNOWN"
    provenance: str = "UNKNOWN"
    source: str | None = None
    observed_at_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Rune.id is required")
        if self.truth_domain not in TRUTH_DOMAINS:
            raise ValueError(f"invalid Rune truth domain: {self.truth_domain}")
        if self.provenance not in PROVENANCE_DOMAINS:
            raise ValueError(f"invalid Rune provenance: {self.provenance}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "value": self.value,
            "truthDomain": self.truth_domain,
            "provenance": self.provenance,
            "source": self.source,
            "observedAtMs": self.observed_at_ms,
        }


@dataclass(frozen=True)
class Glyph:
    """Compound/contextual meaning assembled from stable semantic identities."""

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
            raise ValueError(f"invalid Glyph truth domain: {self.truth_domain}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "runeIds": list(self.rune_ids),
            "relation": self.relation,
            "truthDomain": self.truth_domain,
            "conditions": list(self.conditions),
        }


@dataclass(frozen=True)
class Weakness:
    """A canon-grounded weakness found while observing another system."""

    id: str
    category: str
    summary: str
    evidence_runes: tuple[str, ...]
    canon_ids: tuple[str, ...]
    severity: str = "review"
    remediation: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "summary": self.summary,
            "evidenceRunes": list(self.evidence_runes),
            "canonIds": list(self.canon_ids),
            "severity": self.severity,
            "remediation": self.remediation,
        }


@dataclass
class Shaep:
    """A stabilized active ReLiC reasoning shape.

    Shaeps are query/system-specific active structures. They reuse stable Runes
    and Glyphs rather than duplicating prose into a second truth store.
    """

    id: str
    subject: str
    runes: dict[str, Rune] = field(default_factory=dict)
    glyphs: dict[str, Glyph] = field(default_factory=dict)
    weaknesses: list[Weakness] = field(default_factory=list)
    created_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def add_rune(self, rune: Rune) -> Rune:
        current = self.runes.get(rune.id)
        if current is not None and current != rune:
            raise ValueError(
                f"Rune identity conflict for {rune.id}; resolve identity instead of overwriting it"
            )
        self.runes[rune.id] = rune
        return rune

    def add_glyph(self, glyph: Glyph) -> Glyph:
        missing = [rune_id for rune_id in glyph.rune_ids if rune_id not in self.runes]
        if missing:
            raise ValueError(f"Glyph {glyph.id} references unknown Runes: {missing}")
        current = self.glyphs.get(glyph.id)
        if current is not None and current != glyph:
            raise ValueError(
                f"Glyph identity conflict for {glyph.id}; resolve identity instead of overwriting it"
            )
        self.glyphs[glyph.id] = glyph
        return glyph

    def report_weakness(self, weakness: Weakness) -> Weakness:
        if not any(item.id == weakness.id for item in self.weaknesses):
            self.weaknesses.append(weakness)
        return weakness

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "format": "ReLiC-Shaep",
            "version": 1,
            "id": self.id,
            "subject": self.subject,
            "createdAtMs": self.created_at_ms,
            "runes": [self.runes[key].as_dict() for key in sorted(self.runes)],
            "glyphs": [self.glyphs[key].as_dict() for key in sorted(self.glyphs)],
            "weaknesses": [item.as_dict() for item in self.weaknesses],
        }
        payload["semanticDigest"] = _stable_digest({
            key: value for key, value in payload.items() if key not in {"createdAtMs", "semanticDigest"}
        })
        return payload


def make_shaep(subject: str, runes: Iterable[Rune] = (), glyphs: Iterable[Glyph] = ()) -> Shaep:
    if not subject or not subject.strip():
        raise ValueError("subject is required")
    # Iterables may be generators, so materialize before reading them.
    rune_list = list(runes)
    glyph_list = list(glyphs)
    seed = {
        "subject": subject.strip(),
        "runes": sorted(r.id for r in rune_list),
        "glyphs": sorted(g.id for g in glyph_list),
    }
    shaep = Shaep(id="shaep." + _stable_digest(seed)[:16], subject=subject.strip())
    for rune in rune_list:
        shaep.add_rune(rune)
    for glyph in glyph_list:
        shaep.add_glyph(glyph)
    return shaep


def on_power_change(prev_state: str, next_state: str) -> None:
    """Backward-compatible legacy hook."""
    print(f"[relic_core] Power: {prev_state} -> {next_state}")


def resonance_for(glyph: dict) -> float:
    """Backward-compatible legacy resonance helper."""
    gid = glyph.get("id")
    table = {
        "daemon": 0.85,
        "tray": 0.95,
        "hud": 1.10,
        "spark": 1.60,
        "solar": 1.25,
        "lunar": 0.60,
        "stone": 0.50,
        "element": 1.40,
        "matter": 0.70,
        "dna": 1.15,
        "wave": 1.80,
    }
    return table.get(gid, 1.0)
