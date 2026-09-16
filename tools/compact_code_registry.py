#!/usr/bin/env python3
"""Compact the persistent code-ID registry without changing identity.

The code index enriches registry entries with current path/text/status metadata while
building. Those fields are derivable from tracked source and the searchable ledger,
so persisting them makes the identity registry unnecessarily large. The only durable
truth required by the allocator is fingerprint -> numeric ID ownership plus the
allocation cursor/format metadata.

This tool deliberately fails closed on malformed or colliding ownership and verifies
that compaction preserves the complete fingerprint/ID mapping before replacing the
registry atomically.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / ".code-index" / "id_registry.json"


def load_registry(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read persistent code ID registry: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("entries"), dict):
        raise SystemExit("Persistent code ID registry has an invalid schema.")
    return data


def ownership(entries: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    owners: dict[str, str] = {}
    for fingerprint, entry in entries.items():
        if not isinstance(fingerprint, str) or not fingerprint:
            raise SystemExit("Persistent code ID registry contains an invalid fingerprint key.")
        if not isinstance(entry, dict) or entry.get("id") in (None, ""):
            raise SystemExit(f"Persistent code ID registry entry {fingerprint[:12]} has no ID.")
        value = str(entry["id"])
        prior = owners.get(value)
        if prior is not None and prior != fingerprint:
            raise SystemExit(
                "Persistent code ID ownership collision during compaction: "
                f"{value} belongs to both {prior[:12]} and {fingerprint[:12]}."
            )
        owners[value] = fingerprint
        result[fingerprint] = value
    return result


def compact(path: Path = REGISTRY_PATH) -> dict:
    data = load_registry(path)
    before = ownership(data["entries"])
    numeric_ids = [int(value) for value in before.values() if value.isdigit()]
    max_id = max(numeric_ids, default=0)
    try:
        next_id = int(data.get("next_id", max_id + 1))
    except (TypeError, ValueError) as exc:
        raise SystemExit("Persistent code ID registry has an invalid next_id.") from exc
    next_id = max(1, next_id, max_id + 1)

    compacted = {
        "version": int(data.get("version", 1)),
        "width": int(data.get("width", 6)),
        "next_id": next_id,
        "entries": {fingerprint: {"id": value} for fingerprint, value in sorted(before.items())},
    }
    after = ownership(compacted["entries"])
    if before != after:
        raise SystemExit("Registry compaction changed persistent identity ownership; refusing write.")

    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(compacted, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as handle:
        handle.write(rendered)
        temp_path = Path(handle.name)
    temp_path.replace(path)

    return {
        "entries": len(before),
        "max_id": max_id,
        "next_id": next_id,
        "bytes": path.stat().st_size,
    }


def verify(path: Path = REGISTRY_PATH) -> dict:
    data = load_registry(path)
    mapping = ownership(data["entries"])
    unexpected = [
        fingerprint
        for fingerprint, entry in data["entries"].items()
        if set(entry) != {"id"}
    ]
    if unexpected:
        raise SystemExit(
            f"Persistent code ID registry is not compact: {len(unexpected)} entries contain derivable metadata."
        )
    return {"entries": len(mapping), "bytes": path.stat().st_size}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact Shaelvien persistent code ID ownership")
    parser.add_argument("command", choices=("compact", "verify"), nargs="?", default="compact")
    args = parser.parse_args()
    result = compact() if args.command == "compact" else verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
