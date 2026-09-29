"""Compact ReLiC context translation for ChatGPT-style clients.

This module is a read-only representation layer. It never rewrites project
knowledge, ReLiC memory, canon, or world state. Compression is pointer-based:
the authoritative/source-backed record remains external and can be expanded
through the referenced MCP read tool when more detail is required.
"""
from __future__ import annotations

import hashlib
import json
import re

FORMAT_VERSION = "RELIC-CONTEXT/1"
STOP_WORDS = {
    "about", "after", "again", "also", "been", "before", "being", "between",
    "chatgpt", "could", "does", "from", "have", "into", "just", "more",
    "need", "only", "other", "should", "that", "their", "there", "these",
    "they", "this", "through", "user", "using", "want", "what", "when",
    "where", "which", "while", "with", "would",
}


def _text(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _short(value, limit: int) -> str:
    value = _text(value)
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)].rstrip() + "…"


def _canon(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def query_terms(query: str, explicit_terms=None, limit: int = 16) -> list[str]:
    """Return stable lookup terms without inventing semantic meaning."""
    terms: list[str] = []
    seen: set[str] = set()

    def add(value):
        value = _text(value)
        key = value.casefold()
        if not value or key in seen:
            return
        seen.add(key)
        terms.append(value)

    for value in explicit_terms or []:
        add(value)
        if len(terms) >= limit:
            return terms

    # Preserve quoted/named phrases first, then useful tokens. These terms are
    # only retrieval candidates; a match still has to resolve to a stored ID.
    for value in re.findall(r'"([^"]{2,120})"|\'([^\']{2,120})\'', query or ""):
        add(value[0] or value[1])
        if len(terms) >= limit:
            return terms

    for token in re.findall(r"[A-Za-z0-9_.:-]{3,}", query or ""):
        if token.casefold() in STOP_WORDS:
            continue
        add(token)
        if len(terms) >= limit:
            break
    return terms


def _project_rune(record: dict, index: int) -> dict:
    rid = _text(record.get("recordId") or record.get("record_id"))
    return {
        "id": f"P{index}",
        "kind": "project-record",
        "ref": rid,
        "truth": _text(record.get("truthDomain") or record.get("truth_domain") or "UNKNOWN"),
        "status": _text(record.get("status")),
        "label": _short(record.get("title"), 96),
        "hint": _short(record.get("text"), 220),
        "sources": [
            _text(source.get("sourceId") or source.get("source_id"))
            for source in (record.get("sources") or [])
            if _text(source.get("sourceId") or source.get("source_id"))
        ][:8],
        "expand": {"tool": "relic_project_fetch", "recordId": rid},
    }


def _neuron_rune(observed: dict, index: int) -> dict | None:
    entity = observed.get("entity") or {}
    eid = _text(entity.get("entityId"))
    if not eid:
        return None
    return {
        "id": f"N{index}",
        "kind": "neuron",
        "ref": eid,
        "truth": _text(entity.get("truthDomain") or "UNKNOWN"),
        "revision": int(entity.get("revision") or 0),
        "label": _short(entity.get("label"), 96),
        "type": _short(entity.get("entityType"), 80),
        "sourceRef": _short(entity.get("sourceRef"), 160),
        "expand": {
            "tool": "relic_observe",
            "entityId": eid,
            "includeEvents": False,
            "relationshipDepth": 1,
        },
    }


def _glyphs(project_runes: list[dict], neuron_runes: list[dict], private_context: dict | None) -> list[dict]:
    glyphs: list[dict] = []

    for rune in project_runes:
        for source_id in rune.get("sources") or []:
            glyphs.append({
                "id": f"G{len(glyphs)}",
                "relation": "SUPPORTED_BY",
                "from": rune["id"],
                "to": f"SRC:{source_id}",
            })

    by_ref = {r["ref"]: r["id"] for r in neuron_runes}
    for observed in (private_context or {}).get("entities") or []:
        entity = observed.get("entity") or {}
        source = by_ref.get(_text(entity.get("entityId")))
        if not source:
            continue
        for rel in observed.get("relationships") or []:
            target = by_ref.get(_text(rel.get("targetId")))
            if target:
                glyphs.append({
                    "id": f"G{len(glyphs)}",
                    "relation": _short(rel.get("relationType") or "RELATED_TO", 80),
                    "from": source,
                    "to": target,
                    "truth": _text(rel.get("truthDomain") or "UNKNOWN"),
                })
    return glyphs[:64]


def _compact_lines(query: str, runes: list[dict], glyphs: list[dict], digest: str) -> str:
    lines = [
        f"RCTX1 sha={digest[:16]}",
        "LAW ID!=REP; REP!=TRUTH; UNKNOWN!=FACT; MEMORY!=CANON; PTR_EXPAND_ON_DEMAND",
        f"Q {_short(query, 240)}",
    ]
    for rune in runes:
        if rune["kind"] == "project-record":
            lines.append(
                f"R {rune['id']} P ref={rune['ref']} t={rune['truth']} s={rune['status']} "
                f"| {rune['label']} | {rune['hint']}"
            )
        else:
            lines.append(
                f"R {rune['id']} N ref={rune['ref']} t={rune['truth']} rev={rune['revision']} "
                f"| {rune['label']}"
            )
    for glyph in glyphs:
        lines.append(
            f"G {glyph['id']} {glyph['from']} -{glyph['relation']}-> {glyph['to']}"
            + (f" t={glyph['truth']}" if glyph.get("truth") else "")
        )
    lines.append("S S0 load=" + ",".join(r["id"] for r in runes) + " expand=on-demand")
    return "\n".join(lines)


def build_context_pack(
    query: str,
    project_records: list[dict] | None,
    private_context: dict | None = None,
    *,
    project_snapshot: str | None = None,
    max_runes: int = 12,
) -> dict:
    """Build a compact, reversible-by-reference context package.

    The returned Rune text is intentionally small. Exact detail is preserved in
    the referenced project record or private ReLiC entity and is fetched only
    when reasoning requires it.
    """
    query = _text(query)
    if not query:
        raise ValueError("query is required")
    max_runes = max(1, min(int(max_runes), 32))

    project_records = list(project_records or [])
    private_entities = list((private_context or {}).get("entities") or [])

    # Keep both sources represented when possible instead of letting one source
    # consume the whole budget.
    project_budget = max_runes
    neuron_budget = 0
    if private_entities:
        neuron_budget = max(1, max_runes // 3)
        project_budget = max(0, max_runes - neuron_budget)

    project_runes = [_project_rune(r, i) for i, r in enumerate(project_records[:project_budget])]
    neuron_runes = []
    for observed in private_entities:
        rune = _neuron_rune(observed, len(neuron_runes))
        if rune:
            neuron_runes.append(rune)
        if len(neuron_runes) >= neuron_budget:
            break

    # If the project side did not use its allocation, spend the remaining
    # capacity on resolved private neurons without exceeding max_runes.
    if len(project_runes) < project_budget and private_entities:
        for observed in private_entities[len(neuron_runes):]:
            if len(project_runes) + len(neuron_runes) >= max_runes:
                break
            rune = _neuron_rune(observed, len(neuron_runes))
            if rune:
                neuron_runes.append(rune)

    runes = project_runes + neuron_runes
    glyphs = _glyphs(project_runes, neuron_runes, private_context)
    basis = {
        "format": FORMAT_VERSION,
        "query": query,
        "projectSnapshot": project_snapshot,
        "runes": runes,
        "glyphs": glyphs,
    }
    digest = hashlib.sha256(_canon(basis).encode("utf-8")).hexdigest()

    return {
        **basis,
        "contextSha256": digest,
        "shaep": {
            "id": "S0",
            "purpose": "chatgpt-working-context",
            "load": [r["id"] for r in runes],
            "expansionPolicy": "Expand a Rune only when its compact hint is insufficient; use its expand tool and stable ref.",
            "conflictPolicy": "Preserve truth domain, status, provenance, and authority. Do not resolve conflicts by recency or repetition alone.",
        },
        "legend": {
            "R": "Rune: smallest context reference used in working context.",
            "G": "Glyph: relationship between Rune/source identities.",
            "S": "Shaep: bounded set of Runes/Glyphs loaded for one reasoning task.",
            "P": "project database record",
            "N": "authenticated ReLiC neuron/memory identity",
            "PTR_EXPAND_ON_DEMAND": "compact text is a pointer view; exact source detail remains external and must be fetched when needed",
        },
        "compactContext": _compact_lines(query, runes, glyphs, digest),
        "truthBoundary": (
            "This is a read-only pointer compression of retrieved context. The project database and ReLiC memory remain unchanged. "
            "Compact hints are representations, not replacements for source truth; expand stable references before relying on omitted detail."
        ),
    }
