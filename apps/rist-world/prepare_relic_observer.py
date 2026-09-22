#!/usr/bin/env python3
"""Build the public ReLiC Observer seed from the source-controlled project corpus.

The generated browser seed contains only public-existing-source metadata and curated
project records. It deliberately excludes raw source bodies and every private corpus.
Private material belongs in authenticated account storage at runtime.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "knowledge" / "project" / "public.json"
TARGET = ROOT / "apps" / "rist-world" / "wwwroot" / "data" / "relic-observer-seed.json"
ALLOWED_TRUTH = {"FACT", "HYPOTHESIS", "FICTION", "UNKNOWN"}


def _text(value, default=""):
    return str(value).strip() if value is not None else default


def _truth(value):
    normalized = _text(value, "UNKNOWN").upper()
    return normalized if normalized in ALLOWED_TRUTH else "UNKNOWN"


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
        # Raw source.content is intentionally not copied into a browser bundle.
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

    public_sources.sort(key=lambda item: (item["title"].casefold(), item["sourceId"]))
    public_records.sort(key=lambda item: (item["category"].casefold(), item["title"].casefold(), item["recordId"]))

    return {
        "schemaVersion": 1,
        "datasetId": data["dataset_id"],
        "snapshotDate": _text(data.get("snapshot_date")),
        "corpusSha256": hashlib.sha256(raw).hexdigest(),
        "extractionProvenance": "OUTSIDER_AI/RED",
        "sourceCount": len(public_sources),
        "recordCount": len(public_records),
        "sources": public_sources,
        "records": public_records,
    }


def validate_seed(seed: dict):
    if seed.get("schemaVersion") != 1:
        raise ValueError("Observer seed schema mismatch")
    sources = seed.get("sources") or []
    records = seed.get("records") or []
    if not sources or not records:
        raise ValueError("Observer seed is empty")
    ids = {item["sourceId"] for item in sources}
    if len(ids) != len(sources):
        raise ValueError("Duplicate Observer source IDs")
    if any(not item.get("visibility", "").startswith("public") for item in sources):
        raise ValueError("Non-public source attempted to enter Observer seed")
    if any("content" in item for item in sources):
        raise ValueError("Raw source content must not enter Observer seed")
    for record in records:
        if record.get("truthDomain") not in ALLOWED_TRUTH:
            raise ValueError("Invalid truth domain")
        if not record.get("sourceIds") or any(source_id not in ids for source_id in record["sourceIds"]):
            raise ValueError("Observer record has an unresolved source")
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
        f"records={len(seed['records'])} snapshot={seed['snapshotDate']}"
    )
