"""ReLiC semantic core: Rune -> Glyph -> Shaep.

Rune is atomic machine-facing semantic identity.
Glyph is compound/contextual meaning assembled from Runes.
Shaep is a stabilized ReLiC reasoning/context object assembled from Glyphs.

ReLiC Shaep is intentionally distinct from uppercase SHAEP, the existing
Spatial Hot Preservation Object media/archive format. A Shaep may reference a
SHAEP identity without redefining the archive contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional
import hashlib
import json
import time


TRUTH_DOMAINS = {"FACT", "HYPOTHESIS", "FICTION", "UNKNOWN"}
PROVENANCE_DOMAINS = {"HUMAN", "OUTSIDER_AI", "SHAELVIEN_EI", "SYSTEM", "UNKNOWN"}


def _stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Rune:
    id: str
    value: Any = None
    truth_domain: str = "UNKNOWN"
    provenance: str = "UNKNOWN"
    source: Optional[str] = None
    unit: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Rune.id is required")
        if self.truth_domain not in TRUTH_DOMAINS:
            raise ValueError(f"Unknown truth domain: {self.truth_domain}")
        if self.provenance not in PROVENANCE_DOMAINS:
            raise ValueError(f"Unknown provenance domain: {self.provenance}")


@dataclass(frozen=True)
class Glyph:
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
        if not self.relation:
            raise ValueError("Glyph.relation is required")
        if self.truth_domain not in TRUTH_DOMAINS:
            raise ValueError(f"Unknown truth domain: {self.truth_domain}")


@dataclass(frozen=True)
class Weakness:
    id: str
    category: str
    summary: str
    evidence_runes: tuple[str, ...]
    canon_ids: tuple[str, ...]
    severity: str = "review"
    remediation: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
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
    id: str
    subject: str
    runes: Dict[str, Rune] = field(default_factory=dict)
    glyphs: Dict[str, Glyph] = field(default_factory=dict)
    weaknesses: list[Weakness] = field(default_factory=list)
    created_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def add_rune(self, rune: Rune) -> Rune:
        existing = self.runes.get(rune.id)
        if existing is not None and existing != rune:
            raise ValueError(
                f"Rune identity conflict for {rune.id}; resolve identity instead of overwriting it"
            )
        self.runes[rune.id] = rune
        return rune

    def add_glyph(self, glyph: Glyph) -> Glyph:
        missing = [rune_id for rune_id in glyph.rune_ids if rune_id not in self.runes]
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
        if not any(item.id == weakness.id for item in self.weaknesses):
            self.weaknesses.append(weakness)
        return weakness

    def as_dict(self) -> Dict[str, Any]:
        body = {
            "format": "ReLiC-Shaep",
            "version": 1,
            "id": self.id,
            "subject": self.subject,
            "createdAtMs": self.created_at_ms,
            "runes": [
                {
                    "id": r.id,
                    "value": r.value,
                    "truthDomain": r.truth_domain,
                    "provenance": r.provenance,
                    "source": r.source,
                    "unit": r.unit,
                }
                for r in sorted(self.runes.values(), key=lambda x: x.id)
            ],
            "glyphs": [
                {
                    "id": g.id,
                    "runeIds": list(g.rune_ids),
                    "relation": g.relation,
                    "truthDomain": g.truth_domain,
                    "conditions": list(g.conditions),
                }
                for g in sorted(self.glyphs.values(), key=lambda x: x.id)
            ],
            "weaknesses": [w.as_dict() for w in self.weaknesses],
        }
        body["semanticDigest"] = _stable_digest(body)
        return body


def build_shaep(subject: str, runes: Iterable[Rune], glyphs: Iterable[Glyph] = ()) -> Shaep:
    identity = "shaep-relic-" + _stable_digest({"subject": subject})[:24]
    shaep = Shaep(id=identity, subject=subject)
    for rune in runes:
        shaep.add_rune(rune)
    for glyph in glyphs:
        shaep.add_glyph(glyph)
    return shaep


# Legacy compatibility -------------------------------------------------------
# Existing early prototypes call these functions. Preserve them while the
# semantic core replaces the old resonance-only implementation.

def on_power_change(prev_state: str, next_state: str) -> None:
    print(f"[relic_core] Power: {prev_state} -> {next_state}")


def resonance_for(glyph: dict) -> float:
    gid = glyph.get("id")
    table = {
        "daemon": 0.85, "tray": 0.95, "hud": 1.10, "spark": 1.60,
        "solar": 1.25, "lunar": 0.60, "stone": 0.50,
        "element": 1.40, "matter": 0.70, "dna": 1.15, "wave": 1.80,
    }
    return table.get(gid, 1.0)
