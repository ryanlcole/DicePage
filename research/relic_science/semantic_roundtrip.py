#!/usr/bin/env python3
"""Cross-domain semantic conservation checks for Rune -> Glyph -> Shaep -> representation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_META = ("truthDomain", "provenance")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def encode_record(domain: str, identity: str, fields: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not domain or not identity:
        raise ValueError("domain and identity are required")
    runes = []
    for name in sorted(fields):
        spec = fields[name]
        missing = [k for k in REQUIRED_META if not spec.get(k)]
        if missing:
            raise ValueError(f"field {name} missing metadata: {missing}")
        runes.append({
            "id": f"rune.{domain}.{name}",
            "field": name,
            "value": spec.get("value"),
            "unit": spec.get("unit"),
            "valueType": spec.get("valueType") or type(spec.get("value")).__name__,
            "truthDomain": spec["truthDomain"],
            "provenance": spec["provenance"],
            "constraints": spec.get("constraints") or {},
        })

    glyph = {
        "id": f"glyph.{domain}.record",
        "relation": "composes",
        "runeIds": [r["id"] for r in runes],
    }
    shaep = {
        "format": "ReLiC-Shaep",
        "version": 1,
        "domain": domain,
        "identity": identity,
        "runes": runes,
        "glyphs": [glyph],
    }
    shaep["semanticDigest"] = _digest({
        "domain": domain,
        "identity": identity,
        "runes": runes,
        "glyphs": [glyph],
    })
    return shaep


def decode_record(shaep: dict[str, Any]) -> dict[str, Any]:
    return {
        "domain": shaep["domain"],
        "identity": shaep["identity"],
        "fields": {
            rune["field"]: {
                "value": rune.get("value"),
                "unit": rune.get("unit"),
                "valueType": rune.get("valueType"),
                "truthDomain": rune.get("truthDomain"),
                "provenance": rune.get("provenance"),
                "constraints": rune.get("constraints") or {},
            }
            for rune in shaep.get("runes") or []
        },
    }


def compare_roundtrip(original: dict[str, Any], decoded: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "domain": original["domain"],
        "identity": original["identity"],
        "fields": original["fields"],
    }
    failures = []
    if decoded.get("domain") != expected["domain"]:
        failures.append("domain")
    if decoded.get("identity") != expected["identity"]:
        failures.append("identity")
    for field, spec in expected["fields"].items():
        got = (decoded.get("fields") or {}).get(field)
        if got is None:
            failures.append(f"missing:{field}")
            continue
        for key in ("value", "unit", "valueType", "truthDomain", "provenance", "constraints"):
            want = spec.get(key)
            if key == "valueType" and want is None:
                want = type(spec.get("value")).__name__
            if key == "constraints" and want is None:
                want = {}
            if got.get(key) != want:
                failures.append(f"{field}:{key}")
    return {
        "preserved": not failures,
        "failures": failures,
        "originalDigest": _digest(expected),
        "decodedDigest": _digest(decoded),
        "boundary": (
            "Passing proves conservation for the tested representation only. It does not prove "
            "that one vocabulary captures every domain or that domain science is correct."
        ),
    }


def run_roundtrip(record: dict[str, Any]) -> dict[str, Any]:
    shaep = encode_record(record["domain"], record["identity"], record["fields"])
    decoded = decode_record(shaep)
    return {
        "shaep": shaep,
        "decoded": decoded,
        "validation": compare_roundtrip(record, decoded),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ReLiC cross-domain semantic round-trip")
    parser.add_argument("record_json")
    args = parser.parse_args()
    record = json.loads(Path(args.record_json).read_text(encoding="utf-8"))
    print(json.dumps(run_roundtrip(record), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
