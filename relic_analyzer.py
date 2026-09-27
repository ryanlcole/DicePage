# relic_analyzer.py — ReLiC Intelligence Analyzer
from __future__ import annotations

from typing import List, Dict, Any, Optional, Mapping
import os, json, random

from relic_core import Shaep, Weakness, rune, glyph
from waveform_core import (
    now_ms, synth_tone, energy, bandpass_bins, frame_histogram,
    cosine, jensen_shannon, wave_to_text,
)

STORE = os.path.join("logs", "patterns")
os.makedirs(STORE, exist_ok=True)


# ---------------------------------------------------------------------------
# Rune -> Glyph -> Shaep system analysis
# ---------------------------------------------------------------------------

CANON_REMEDIES = {
    "duplicate_identity": (
        ("RELIC.IDENTITY.NOT_OUTPUT_EQUIVALENCE", "RELIC.IDENTITY.REUSE_BEFORE_DUPLICATE"),
        "Resolve and reuse the stable semantic identity; attach new representations or observations to it instead of creating a duplicate entity.",
    ),
    "fact_without_provenance": (
        ("RELIC.PROVENANCE.PERSISTENT", "RELIC.REPRESENTATION.NOT_TRUTH"),
        "Downgrade the claim to UNKNOWN/HYPOTHESIS or attach provenance sufficient for the stated factual scope.",
    ),
    "authority_ambiguous": (
        ("RELIC.AUTH.CREDENTIALS_NOT_PERMISSION", "RELIC.AUTH.AMBIGUITY_DENIES"),
        "Resolve the explicit capability/authority path. Authentication or tool availability alone is not permission.",
    ),
    "human_harm": (
        ("RELIC.SAFETY.HUMAN_NONHARM",),
        "Deny the harmful machine capability or redesign it so the harmful effect is unavailable and material human-safety uncertainty fails closed.",
    ),
    "ecological_harm": (
        ("RELIC.SAFETY.ECOLOGICAL_COUNTERMEASURE", "RELIC.SAFETY.PREVENTION_BEFORE_COMPENSATION"),
        "Prevent the ecological harm where possible. Otherwise require a credible, proportionate, monitorable countermeasure with residual harm, reversibility, and authority made explicit.",
    ),
    "global_claim_unproven": (
        ("RELIC.PROOF.SCOPE_NOT_INFERENCE", "RELIC.PROOF.FIVE_MINUTES"),
        "Report only the observed scope. Register the claimed change, collect independent evidence, and produce proof within five minutes or alert that the broader claim remains unproven.",
    ),
    "energy_claim_unmeasured": (
        ("RELIC.PURPOSE.MEASURE_EFFICIENCY",),
        "Measure energy against a defined baseline. Byte count, latency, or operation count may be reported separately but must not be relabeled as electrical energy.",
    ),
}


def _weakness(
    shaep: Shaep,
    category: str,
    summary: str,
    evidence_ids: List[str],
    *,
    severity: str = "review",
) -> None:
    canon_ids, remediation = CANON_REMEDIES[category]
    shaep.report_weakness(
        Weakness(
            id=f"weakness.{category}." + str(len(shaep.weaknesses) + 1).zfill(3),
            category=category,
            summary=summary,
            evidence_runes=tuple(evidence_ids),
            canon_ids=tuple(canon_ids),
            severity=severity,
            remediation=remediation,
        )
    )


def analyze_system(system: Mapping[str, Any]) -> Dict[str, Any]:
    """Analyze a system contract and return a canon-grounded Shaep report.

    ReLiC reports weaknesses; it does not silently mutate the analyzed system.

    Expected input is intentionally vendor-neutral. Recognized fields:
      subject: string
      identities: [{stableId, representation, semanticKey}]
      claims: [{text, truthDomain, provenance, scope, measuredEnergyJoules,
                energyReductionClaim}]
      capabilities: [{name, authorityBasis, intendedHumanHarm,
                      foreseeableEcologicalHarm, countermeasure}]
      changeClaims: [{description, claimedScope, observedScope, evidence}]
    Unknown fields remain available to callers but are not guessed into meaning.
    """

    subject = str(system.get("subject") or "analyzed-system").strip()
    out = Shaep.for_subject(subject)

    root = rune(
        "system",
        {"subject": subject},
        identity=f"rune.system.{out.id}",
        truth_domain="FACT",
        provenance="SYSTEM",
        source="relic_analyzer",
    )
    out.add_rune(root)

    # Identity reuse / duplication.
    seen_semantic: Dict[str, str] = {}
    for index, item in enumerate(system.get("identities") or []):
        if not isinstance(item, Mapping):
            continue
        stable_id = str(item.get("stableId") or "").strip()
        semantic_key = str(item.get("semanticKey") or "").strip()
        representation = item.get("representation")
        r = rune(
            "identity-observation",
            {
                "stableId": stable_id or None,
                "semanticKey": semantic_key or None,
                "representation": representation,
            },
            identity=stable_id or None,
            truth_domain="FACT" if stable_id else "UNKNOWN",
            provenance="SYSTEM",
            source=f"identities[{index}]",
        )
        out.add_rune(r)
        out.add_glyph(glyph("represented-as", [root, r], truth_domain=r.truth_domain))

        if semantic_key:
            prior = seen_semantic.get(semantic_key)
            if prior and stable_id and prior != stable_id:
                _weakness(
                    out,
                    "duplicate_identity",
                    f"Semantic key {semantic_key!r} is represented by multiple stable IDs ({prior!r}, {stable_id!r}).",
                    [prior, r.id],
                    severity="block",
                )
            elif stable_id:
                seen_semantic[semantic_key] = stable_id

    # Truth, provenance, and efficiency claims.
    for index, item in enumerate(system.get("claims") or []):
        if not isinstance(item, Mapping):
            continue
        domain = str(item.get("truthDomain") or "UNKNOWN").upper()
        if domain not in {"FACT", "HYPOTHESIS", "FICTION", "UNKNOWN"}:
            domain = "UNKNOWN"
        provenance = [str(x) for x in (item.get("provenance") or []) if str(x).strip()]
        r = rune(
            "claim",
            {
                "text": str(item.get("text") or ""),
                "scope": item.get("scope"),
                "provenance": provenance,
            },
            truth_domain=domain,
            provenance="SYSTEM",
            source=f"claims[{index}]",
        )
        out.add_rune(r)
        out.add_glyph(glyph("asserts", [root, r], truth_domain=domain))

        if domain == "FACT" and not provenance:
            _weakness(
                out,
                "fact_without_provenance",
                "A FACT claim lacks provenance sufficient to establish its stated scope.",
                [r.id],
                severity="block",
            )

        if item.get("energyReductionClaim") is not None and item.get("measuredEnergyJoules") is None:
            _weakness(
                out,
                "energy_claim_unmeasured",
                "An energy-reduction claim is present without measured joules or an equivalent defined electrical-energy measurement.",
                [r.id],
            )

    # Capability, authority, human safety, and ecology.
    for index, item in enumerate(system.get("capabilities") or []):
        if not isinstance(item, Mapping):
            continue
        authority = str(item.get("authorityBasis") or "unknown")
        r = rune(
            "capability",
            dict(item),
            truth_domain="FACT",
            provenance="SYSTEM",
            source=f"capabilities[{index}]",
        )
        out.add_rune(r)
        out.add_glyph(glyph("has-capability", [root, r], truth_domain="FACT"))

        if authority not in {"explicit-capability", "explicit-human-authority"}:
            _weakness(
                out,
                "authority_ambiguous",
                f"Capability {item.get('name')!r} does not have an explicit authority basis.",
                [r.id],
                severity="block",
            )

        if bool(item.get("intendedHumanHarm")):
            _weakness(
                out,
                "human_harm",
                f"Capability {item.get('name')!r} declares or implies intended human harm.",
                [r.id],
                severity="block",
            )

        if bool(item.get("foreseeableEcologicalHarm")) and not item.get("countermeasure"):
            _weakness(
                out,
                "ecological_harm",
                f"Capability {item.get('name')!r} has foreseeable ecological harm without a countermeasure.",
                [r.id],
                severity="block",
            )

    # Proof scope.
    for index, item in enumerate(system.get("changeClaims") or []):
        if not isinstance(item, Mapping):
            continue
        claimed = {str(x) for x in (item.get("claimedScope") or []) if str(x)}
        observed = {str(x) for x in (item.get("observedScope") or []) if str(x)}
        evidence = [str(x) for x in (item.get("evidence") or []) if str(x)]
        r = rune(
            "change-claim",
            {
                "description": item.get("description"),
                "claimedScope": sorted(claimed),
                "observedScope": sorted(observed),
                "evidence": evidence,
            },
            truth_domain="FACT" if claimed and claimed.issubset(observed) and evidence else "UNKNOWN",
            provenance="SYSTEM",
            source=f"changeClaims[{index}]",
        )
        out.add_rune(r)
        out.add_glyph(glyph("claims-change", [root, r], truth_domain=r.truth_domain))

        if claimed and (not claimed.issubset(observed) or not evidence):
            _weakness(
                out,
                "global_claim_unproven",
                "The claimed change scope exceeds the scope currently supported by evidence.",
                [r.id],
                severity="alert",
            )

    return {
        "format": "ReLiC-Analysis",
        "mode": "analyze-report-propose",
        "mutationAuthority": False,
        "shaep": out.as_dict(),
        "summary": {
            "runes": len(out.runes),
            "glyphs": len(out.glyphs),
            "weaknesses": len(out.weaknesses),
            "blockingWeaknesses": sum(1 for x in out.weaknesses if x.severity == "block"),
            "alerts": sum(1 for x in out.weaknesses if x.severity == "alert"),
        },
    }


# ---------------------------------------------------------------------------
# Existing WaveGlyph prototype retained as a specialized observation source.
# Its outputs are observations, not automatic semantic truth.
# ---------------------------------------------------------------------------

def _store_path(kind: str) -> str:
    return os.path.join(STORE, f"{kind}_patterns.json")


def _load(kind: str) -> List[Dict[str, Any]]:
    path = _store_path(kind)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return []


def _save(kind: str, values: List[Dict[str, Any]]) -> None:
    with open(_store_path(kind), "w", encoding="utf-8") as handle:
        json.dump(values, handle, indent=2)


def ingest_audio(samples: List[float], sr: int = 16000, label: Optional[str] = None) -> Dict[str, Any]:
    vec = bandpass_bins(samples, sr, bins=12)
    return {
        "kind": "audio",
        "ts": now_ms(),
        "vec": vec,
        "energy": energy(samples),
        "label": label or "unlabeled",
        "code": wave_to_text(vec, k=8),
        "truthDomain": "OBSERVATION",
    }


def ingest_video_frame(rgb_frame) -> Dict[str, Any]:
    vec = frame_histogram(rgb_frame, buckets=12)
    return {
        "kind": "video",
        "ts": now_ms(),
        "vec": vec,
        "label": "unlabeled",
        "code": wave_to_text(vec, k=8),
        "truthDomain": "OBSERVATION",
    }


SIM_T = 0.92


def _similarity(a: List[float], b: List[float]) -> float:
    return 0.5 * cosine(a, b) + 0.5 * jensen_shannon(a, b)


def learn(kind: str, feat: Dict[str, Any]) -> Dict[str, Any]:
    classes = _load(kind)
    best_i, best_s = -1, 0.0
    for i, current in enumerate(classes):
        similarity = _similarity(current["centroid"], feat["vec"])
        if similarity > best_s:
            best_s, best_i = similarity, i

    if best_s >= SIM_T and best_i >= 0:
        current = classes[best_i]
        n = max(1, int(current.get("members", 1)))
        current["centroid"] = [
            (ci * n + vi) / (n + 1) for ci, vi in zip(current["centroid"], feat["vec"])
        ]
        current["members"] = n + 1
        if feat.get("label"):
            current.setdefault("labels", []).append(feat["label"])
        _save(kind, classes)
        return {
            "joined": current["id"],
            "similarity": round(best_s, 3),
            "members": current["members"],
            "code": wave_to_text(current["centroid"], 8),
            "truthDomain": "OBSERVATION",
        }

    cid = f"{kind}-{len(classes)+1:04d}"
    node = {
        "id": cid,
        "kind": kind,
        "centroid": feat["vec"],
        "members": 1,
        "labels": [feat.get("label", "seed")],
    }
    classes.append(node)
    _save(kind, classes)
    return {
        "created": cid,
        "members": 1,
        "code": wave_to_text(feat["vec"], 8),
        "truthDomain": "OBSERVATION",
    }


def list_patterns(kind: str) -> List[Dict[str, Any]]:
    return _load(kind)


def fetch_demo(kind: str = "audio") -> Dict[str, Any]:
    if kind == "audio":
        return ingest_audio(synth_tone(random.choice([220, 330, 440, 660]), dur_s=0.6), label="tone")
    frame = [
        (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        for _ in range(600)
    ]
    return ingest_video_frame(frame)
