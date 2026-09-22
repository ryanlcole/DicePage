#!/usr/bin/env python3
"""Build the public ReLiC Observer seed from source-controlled project evidence.

The browser seed contains:
1. curated public Project Knowledge records, without raw source bodies; and
2. a small explicit allowlist of current/public repository source overlays.

Private corpora are never read by this build step. Repository overlays exist so ReLiC
can observe current contracts, its current Observer implementation, and selected
historical ReLiC prototypes without publishing arbitrary repository files.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "knowledge" / "project" / "public.json"
TARGET = ROOT / "apps" / "rist-world" / "wwwroot" / "data" / "relic-observer-seed.json"
SEMANTIC_UNITS = ROOT / ".code-index" / "semantic_units.json"
ALLOWED_TRUTH = {"FACT", "HYPOTHESIS", "FICTION", "UNKNOWN"}
OVERLAY_CHUNK_CHARACTERS = 1800
OVERLAY_CHUNK_OVERLAP = 160

# Explicit public-source allowlist. Nothing outside this list may enter the browser
# seed through repository overlay discovery.
REPOSITORY_OVERLAY = (
    {
        "path": "AGENTS.md",
        "category": "architecture",
        "status": "current-repository-contract",
        "truth_domain": "FACT",
        "scope": "project-specification",
    },
    {
        "path": ".code-index/humans_language.json",
        "category": "architecture",
        "status": "current-repository-contract",
        "truth_domain": "FACT",
        "scope": "project-specification",
    },
    {
        "path": ".code-index/semantic_units.json",
        "category": "architecture",
        "status": "current-repository-contract",
        "truth_domain": "FACT",
        "scope": "project-specification",
    },
    {
        "path": "docs/SHAELVIEN_SEMANTIC_LANGUAGE.md",
        "category": "architecture",
        "status": "current-repository-contract",
        "truth_domain": "FACT",
        "scope": "project-specification",
    },
    {
        "path": "apps/rist-world/SHAEP_FORMAT.md",
        "category": "architecture",
        "status": "current-repository-contract",
        "truth_domain": "FACT",
        "scope": "project-specification",
    },
    {
        "path": "apps/rist-world/AUTHORITY_SYSTEM.md",
        "category": "authority",
        "status": "current-repository-contract",
        "truth_domain": "FACT",
        "scope": "project-specification",
    },
    {
        "path": "docs/ERROR_GRAPH.md",
        "category": "architecture",
        "status": "current-repository-contract",
        "truth_domain": "FACT",
        "scope": "project-specification",
    },
    {
        "path": "docs/RELIC_OBSERVER_ARCHITECTURE.md",
        "category": "architecture",
        "status": "current-observer-contract",
        "truth_domain": "FACT",
        "scope": "project-specification",
    },
    {
        "path": "apps/rist-world/ReLiCObserverService.cs",
        "category": "implementation",
        "status": "current-implementation-source",
        "truth_domain": "UNKNOWN",
        "scope": "implementation-source",
    },
    {
        "path": "apps/rist-world/Components/ReLiCObserverWorkspace.razor",
        "category": "implementation",
        "status": "current-implementation-source",
        "truth_domain": "UNKNOWN",
        "scope": "implementation-source",
    },
    {
        "path": "apps/rist-world/prepare_relic_observer.py",
        "category": "implementation",
        "status": "current-implementation-source",
        "truth_domain": "UNKNOWN",
        "scope": "implementation-source",
    },
    {
        "path": "relic_core.py",
        "category": "historical-prototype",
        "status": "historical-relic-prototype-source",
        "truth_domain": "UNKNOWN",
        "scope": "historical-prototype",
    },
    {
        "path": "relic_analyzer.py",
        "category": "historical-prototype",
        "status": "historical-relic-prototype-source",
        "truth_domain": "UNKNOWN",
        "scope": "historical-prototype",
    },
    {
        "path": "glyph_ai_core.py",
        "category": "historical-prototype",
        "status": "historical-relic-prototype-source",
        "truth_domain": "UNKNOWN",
        "scope": "historical-prototype",
    },
    {
        "path": "shaelvien_ai_adapter.py",
        "category": "historical-prototype",
        "status": "historical-relic-prototype-source",
        "truth_domain": "UNKNOWN",
        "scope": "historical-prototype",
    },
)


def _text(value, default=""):
    return str(value).strip() if value is not None else default


def _truth(value):
    normalized = _text(value, "UNKNOWN").upper()
    return normalized if normalized in ALLOWED_TRUTH else "UNKNOWN"


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, value: str, length: int = 24) -> str:
    return prefix + hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _bounded_chunks(text: str, size: int = OVERLAY_CHUNK_CHARACTERS, overlap: int = OVERLAY_CHUNK_OVERLAP):
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    if len(normalized) <= size:
        return [normalized]

    chunks = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + size)
        if end < len(normalized):
            window_start = max(start + size // 2, end - 360)
            candidates = [
                normalized.rfind("\n\n", window_start, end),
                normalized.rfind("\n#", window_start, end),
                normalized.rfind("\ndef ", window_start, end),
                normalized.rfind("\nclass ", window_start, end),
                normalized.rfind("\n}", window_start, end),
            ]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + (2 if normalized.startswith("\n\n", boundary) else 1)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(start + 1, end - overlap)
    return chunks


def _repository_uri(path: str) -> str:
    ref = os.environ.get("GITHUB_SHA") or os.environ.get("RELIC_REPOSITORY_REF") or "live-alpha-rist-blazor-world"
    return f"https://github.com/ryanlcole/DicePage/blob/{ref}/{path}"


def _semantic_alias_groups() -> list[dict]:
    """Compile bounded retrieval aliases from the registered semantic-unit ledger.

    These are candidate recall hints only. They do not assert exact identity between
    every surface form and do not mint new semantic units.
    """
    if not SEMANTIC_UNITS.is_file():
        return []

    data = json.loads(SEMANTIC_UNITS.read_text(encoding="utf-8"))
    units = {str(item.get("unit_id", "")).strip(): item for item in data.get("units", [])}
    forms_by_unit: dict[str, list[dict]] = {}
    for form in data.get("forms", []):
        unit_id = str(form.get("unit_id", "")).strip()
        if unit_id in units:
            forms_by_unit.setdefault(unit_id, []).append(form)

    ignored = {"init", "condition", "step", "body", "media", "generic", "cstyle", "sql"}
    groups = []
    for unit_id, unit in sorted(units.items()):
        terms = set()
        name = str(unit.get("name", "")).strip().lower()
        if name:
            terms.add(name)
            terms.update(part for part in re.split(r"[_\-\s]+", name) if len(part) >= 2)

        suffix = unit_id.rsplit(".", 1)[-1].lower()
        if suffix:
            terms.add(suffix)
            terms.update(part for part in re.split(r"[_\-]+", suffix) if len(part) >= 2)

        form_rows = forms_by_unit.get(unit_id, [])
        conditions = []
        relations = set()
        for form in form_rows:
            surface = str(form.get("surface", "")).strip().lower()
            relation = str(form.get("relation", "")).strip()
            condition = str(form.get("conditions", "")).strip()
            if relation:
                relations.add(relation)
            if condition:
                conditions.append(condition)
            if surface.startswith(".") and re.fullmatch(r"\.[a-z0-9]{2,8}", surface):
                terms.add(surface[1:])
            elif re.fullmatch(r"[a-z_][a-z0-9_.-]{1,31}", surface):
                terms.add(surface)
            else:
                for token in re.findall(r"[a-z_][a-z0-9_-]*", surface):
                    if len(token) >= 2 and token not in ignored:
                        terms.add(token)

        terms = sorted(term for term in terms if len(term) >= 2 and term not in ignored)
        if len(terms) < 2:
            continue
        groups.append({
            "unitId": unit_id,
            "kind": str(unit.get("kind", "")).strip().upper(),
            "name": str(unit.get("name", "")).strip(),
            "terms": terms[:24],
            "relations": sorted(relations),
            "conditions": conditions[:8],
        })
    return groups


def _overlay_rows(existing_sources: list[dict]) -> tuple[list[dict], list[dict]]:
    existing_by_title = {_text(item.get("title")): item for item in existing_sources}
    sources = []
    records = []

    for spec in REPOSITORY_OVERLAY:
        relative = spec["path"]
        path = ROOT / relative
        if not path.is_file():
            continue

        content = path.read_text(encoding="utf-8", errors="replace")
        digest = _sha_text(content)

        # The curated Project Knowledge snapshot already carries this exact source
        # revision, so a duplicate overlay would add no information.
        existing = existing_by_title.get(relative)
        if existing and _text(existing.get("sha256")) == digest:
            continue

        source_id = _stable_id("source.overlay.", relative, 20)
        sources.append({
            "sourceId": source_id,
            "title": relative,
            "kind": "repository_overlay",
            "uri": _repository_uri(relative),
            "status": spec["status"],
            "visibility": "public-existing-source",
            "observedAt": "",
            "sha256": digest,
            "sourceOrigin": "UNKNOWN",
        })

        chunks = _bounded_chunks(content)
        for index, chunk in enumerate(chunks, 1):
            records.append({
                "recordId": _stable_id("overlay.", f"{relative}:{index}:{_sha_text(chunk)}"),
                "title": relative if len(chunks) == 1 else f"{relative} · current chunk {index}",
                "category": spec["category"],
                "status": spec["status"],
                "truthDomain": _truth(spec["truth_domain"]),
                "scope": spec["scope"],
                "effectiveDate": "",
                "sourceIds": [source_id],
                "sourceLocator": f"{relative}#overlay-chunk-{index}",
                "text": chunk,
            })

    return sources, records


def build_seed(source_path: Path = SOURCE) -> dict:
    raw = source_path.read_bytes()
    data = json.loads(raw)
    if data.get("dataset_id") != "shaelvien-project-knowledge":
        raise ValueError("Unexpected project knowledge dataset")

    source_rows = data.get("sources") or []
    allowed = {}
    public_sources = []
    for source in source_rows:
        visibility = _text(source.get("visibility"))
        if not visibility.startswith("public"):
            continue
        source_id = _text(source.get("source_id"))
        if not source_id:
            continue
        item = {
            "sourceId": source_id,
            "title": _text(source.get("title"), source_id),
            "kind": _text(source.get("kind")),
            "uri": _text(source.get("uri")),
            "status": _text(source.get("status")),
            "visibility": visibility,
            "observedAt": _text(source.get("observed_at")),
            "sha256": _text(source.get("sha256")),
            "sourceOrigin": _text(source.get("source_origin"), "UNKNOWN"),
        }
        # Raw curated source.content is intentionally not copied into a browser bundle.
        allowed[source_id] = item
        public_sources.append(item)

    public_records = []
    for record in data.get("records") or []:
        ids = [_text(x) for x in (record.get("source_ids") or []) if _text(x)]
        if not ids or any(source_id not in allowed for source_id in ids):
            continue
        public_records.append({
            "recordId": _text(record.get("record_id")),
            "title": _text(record.get("title")),
            "category": _text(record.get("category")),
            "status": _text(record.get("status")),
            "truthDomain": _truth(record.get("truth_domain")),
            "scope": _text(record.get("scope")),
            "effectiveDate": _text(record.get("effective_date")),
            "sourceIds": ids,
            "sourceLocator": _text(record.get("source_locator")),
            "text": _text(record.get("text")),
        })

    overlay_sources, overlay_records = _overlay_rows(source_rows)
    for item in overlay_sources:
        if item["sourceId"] in allowed:
            raise ValueError("Repository overlay source identity collision")
        allowed[item["sourceId"]] = item
        public_sources.append(item)
    public_records.extend(overlay_records)

    public_sources.sort(key=lambda item: (item["title"].casefold(), item["sourceId"]))
    public_records.sort(key=lambda item: (item["category"].casefold(), item["title"].casefold(), item["recordId"]))
    semantic_alias_groups = _semantic_alias_groups()

    return {
        "schemaVersion": 1,
        "datasetId": data["dataset_id"],
        "snapshotDate": _text(data.get("snapshot_date")),
        "corpusSha256": hashlib.sha256(raw).hexdigest(),
        "extractionProvenance": "OUTSIDER_AI/RED",
        "sourceCount": len(public_sources),
        "recordCount": len(public_records),
        "overlaySourceCount": len(overlay_sources),
        "overlayRecordCount": len(overlay_records),
        "semanticAliasGroupCount": len(semantic_alias_groups),
        "semanticAliasGroups": semantic_alias_groups,
        "sources": public_sources,
        "records": public_records,
    }


def validate_seed(seed: dict):
    if seed.get("schemaVersion") != 1:
        raise ValueError("Observer seed schema mismatch")
    sources = seed.get("sources") or []
    records = seed.get("records") or []
    alias_groups = seed.get("semanticAliasGroups") or []
    if not sources or not records:
        raise ValueError("Observer seed is empty")
    ids = {item["sourceId"] for item in sources}
    overlay_ids = {item["sourceId"] for item in sources if item.get("kind") == "repository_overlay"}
    if len(ids) != len(sources):
        raise ValueError("Duplicate Observer source IDs")
    if any(not item.get("visibility", "").startswith("public") for item in sources):
        raise ValueError("Non-public source attempted to enter Observer seed")
    if any("content" in item for item in sources):
        raise ValueError("Raw source body field must not enter Observer seed")
    seen_alias_units = set()
    for group in alias_groups:
        unit_id = str(group.get("unitId", "")).strip()
        terms = group.get("terms") or []
        if not unit_id or unit_id in seen_alias_units:
            raise ValueError("Invalid or duplicate semantic alias unit")
        if len(terms) < 2 or len(terms) > 24 or len(set(terms)) != len(terms):
            raise ValueError("Invalid bounded semantic alias group")
        seen_alias_units.add(unit_id)

    for record in records:
        if record.get("truthDomain") not in ALLOWED_TRUTH:
            raise ValueError("Invalid truth domain")
        if not record.get("sourceIds") or any(source_id not in ids for source_id in record["sourceIds"]):
            raise ValueError("Observer record has an unresolved source")
        is_overlay = any(source_id in overlay_ids for source_id in record["sourceIds"])
        if is_overlay and len(record.get("text", "")) > OVERLAY_CHUNK_CHARACTERS + OVERLAY_CHUNK_OVERLAP + 400:
            raise ValueError("Repository overlay record exceeds bounded evidence size")
    return True


def write_seed(target_path: Path = TARGET) -> dict:
    seed = build_seed()
    validate_seed(seed)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(seed, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return seed


if __name__ == "__main__":
    seed = write_seed()
    print(
        f"relic-observer-seed sources={len(seed['sources'])} "
        f"records={len(seed['records'])} overlays={seed['overlaySourceCount']}/"
        f"{seed['overlayRecordCount']} aliases={seed['semanticAliasGroupCount']} "
        f"snapshot={seed['snapshotDate']}"
    )
