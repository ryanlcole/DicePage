#!/usr/bin/env python3
"""Shaelvien code index and source-governance tool.

The numeric ID is canonical and persistent. The human-readable suffix is a
current locator and may change when a line moves.

Examples:
    000009.csharp.CharacterSelection.line8.code
    000010.html.Home.line54.comment

Generated files live in .code-index/ and are intentionally excluded from their
own index. The tool uses only the Python standard library so CI can run it on a
clean checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / ".code-index" / "config.json"
INDEX_DIR = ROOT / ".code-index"
REGISTRY_PATH = INDEX_DIR / "id_registry.json"
INDEX_JSONL = INDEX_DIR / "code_index.jsonl"
INDEX_TSV = INDEX_DIR / "code_index.tsv"
SUMMARY_PATH = INDEX_DIR / "summary.json"
DUPLICATES_PATH = INDEX_DIR / "duplicates.json"
STALE_PATH = INDEX_DIR / "stale_candidates.json"
CLEANUP_LOG = INDEX_DIR / "cleanup_log.jsonl"

LANGUAGES = {
    ".py": "python", ".cs": "csharp", ".razor": "razor", ".cshtml": "razor",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".jsx": "javascript",
    ".html": "html", ".htm": "html", ".css": "css", ".scss": "scss",
    ".ps1": "powershell", ".psm1": "powershell", ".sh": "shell", ".bash": "shell",
    ".bat": "batch", ".cmd": "batch", ".c": "c", ".h": "c",
    ".cpp": "cpp", ".hpp": "cpp", ".java": "java", ".kt": "kotlin",
    ".swift": "swift", ".go": "go", ".rs": "rust", ".sql": "sql",
    ".yml": "yaml", ".yaml": "yaml", ".json": "json", ".xml": "xml",
    ".toml": "toml",
}

LINE_COMMENT = {
    "python": "#", "powershell": "#", "shell": "#", "yaml": "#",
    "csharp": "//", "razor": "//", "javascript": "//", "typescript": "//",
    "c": "//", "cpp": "//", "java": "//", "kotlin": "//", "swift": "//",
    "go": "//", "rust": "//", "sql": "--",
}

MATERIALIZED_RE = re.compile(r"\b(?P<id>\d{6,})\.(?P<language>[A-Za-z0-9_+-]+)\.(?P<scope>[A-Za-z0-9_.-]+)\.line\d+\.(?P<kind>comment|code)\b")
ID_ANY_RE = re.compile(r"\b(?P<id>\d{6,})\.[A-Za-z0-9_+-]+\.[A-Za-z0-9_.-]+\.line\d+\.(?:comment|code)\b")


@dataclass(frozen=True)
class CommentHit:
    line: int
    column: int
    text: str
    full_line: bool
    marker: str
    end_marker: str = ""


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=check, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def tracked_files() -> list[Path]:
    result = run_git("ls-files", "-z")
    paths = []
    for raw in result.stdout.split("\0"):
        if raw:
            paths.append(ROOT / raw)
    return paths


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def safe_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except (OSError, FileNotFoundError):
        return None
    if b"\x00" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_space(text: str) -> str:
    return " ".join(text.strip().split())


def strip_materialized_id(text: str) -> str:
    return MATERIALIZED_RE.sub("", text, count=1).strip()


def scope_name(path: Path) -> str:
    stem = path.stem or path.name or "root"
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("_.-")
    return cleaned or "root"


def display_id(numeric_id: str, language: str, path: Path, line: int, kind: str) -> str:
    return f"{numeric_id}.{language}.{scope_name(path)}.line{line}.{kind}"


def fingerprint(path: Path, language: str, kind: str, text: str, occurrence: int) -> str:
    payload = "\x1f".join((rel(path), language, kind, normalize_space(strip_materialized_id(text)), str(occurrence)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_registry(width: int) -> dict:
    if REGISTRY_PATH.exists():
        try:
            data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "entries" in data:
                return data
        except Exception:
            pass
    return {"version": 1, "width": width, "next_id": 1, "entries": {}}


def used_ids(registry: dict) -> set[str]:
    return {str(v.get("id", "")) for v in registry.get("entries", {}).values() if v.get("id")}


def reserve_existing_id(registry: dict, fp: str, existing: str, metadata: dict) -> str:
    entries = registry.setdefault("entries", {})
    if fp in entries:
        return entries[fp]["id"]
    used = used_ids(registry)
    if existing not in used:
        entries[fp] = {"id": existing, **metadata}
        registry["next_id"] = max(int(registry.get("next_id", 1)), int(existing) + 1)
        return existing
    return allocate_id(registry, fp, metadata)


def allocate_id(registry: dict, fp: str, metadata: dict) -> str:
    entries = registry.setdefault("entries", {})
    if fp in entries:
        entries[fp].update(metadata)
        return entries[fp]["id"]
    width = int(registry.get("width", 6))
    used = used_ids(registry)
    n = int(registry.get("next_id", 1))
    while f"{n:0{width}d}" in used:
        n += 1
    value = f"{n:0{width}d}"
    entries[fp] = {"id": value, **metadata}
    registry["next_id"] = n + 1
    return value


def path_parts_lower(path: Path) -> tuple[str, ...]:
    return tuple(p.lower() for p in Path(rel(path)).parts)


def classify(path: Path, config: dict) -> tuple[str, list[str]]:
    rp = rel(path)
    parts = path_parts_lower(path)
    name = path.name.lower()
    ext = path.suffix.lower()
    reasons: list[str] = []
    preserve = {p.lower() for p in config.get("preserve_stale_paths", [])}
    if rp.lower() in preserve:
        return "source" if ext in LANGUAGES else "other", ["explicitly-preserved"]

    stale_suffixes = tuple(s.lower() for s in config.get("stale_suffixes", []))
    stale_dirs = {s.lower() for s in config.get("stale_directory_names", [])}
    if name.endswith(stale_suffixes) or any(part.endswith(stale_suffixes) for part in parts) or any(part in stale_dirs for part in parts):
        reasons.append("explicit-stale-name")
        return "stale", reasons

    generated_dirs = {s.lower() for s in config.get("generated_directory_names", [])}
    compiled_exts = {s.lower() for s in config.get("compiled_extensions", [])}
    if any(part in generated_dirs for part in parts) or ext in compiled_exts:
        reasons.append("generated-or-compiled")
        return "generated", reasons

    vendor_roots = {s.lower() for s in config.get("vendor_top_level", [])}
    if parts and (parts[0] in vendor_roots or parts[0].endswith(".dist-info") or "site-packages" in parts):
        reasons.append("vendored-dependency")
        return "vendor", reasons

    if ext in LANGUAGES:
        return "source", reasons
    if ext in {".md", ".txt", ".rst"}:
        return "docs", reasons
    if ext in {".json", ".toml", ".ini", ".cfg", ".spec", ".yml", ".yaml", ".xml"}:
        return "config", reasons
    return "asset", reasons


def is_explicit_stale(path: Path, config: dict) -> bool:
    category, _ = classify(path, config)
    return category == "stale"


def append_cleanup(records: list[dict]) -> None:
    if not records:
        return
    prior = ""
    if CLEANUP_LOG.exists():
        prior = CLEANUP_LOG.read_text(encoding="utf-8")
    with CLEANUP_LOG.open("w", encoding="utf-8", newline="\n") as fh:
        if prior:
            fh.write(prior.rstrip("\n") + "\n")
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")


def prune_explicit_stale(config: dict) -> list[dict]:
    records: list[dict] = []
    files = tracked_files()
    stale_files = [p for p in files if p.exists() and is_explicit_stale(p, config)]
    for path in stale_files:
        try:
            digest = sha256_file(path)
            size = path.stat().st_size
        except OSError:
            digest, size = "unreadable", 0
        records.append({
            "path": rel(path), "reason": "explicit-stale-name",
            "sha256": digest, "bytes": size, "status": "removed-from-active-tree"
        })
        try:
            path.unlink()
        except OSError:
            pass
    # Remove now-empty stale directories from the working tree. Git records only files.
    for base, dirs, _ in os.walk(ROOT, topdown=False):
        b = Path(base)
        if b == ROOT / ".git":
            continue
        if b.exists() and b != ROOT:
            try:
                if not any(b.iterdir()) and is_explicit_stale(b / "sentinel.old", config):
                    b.rmdir()
            except OSError:
                pass
    append_cleanup(records)
    return records


def marker_outside_quotes(line: str, marker: str) -> int:
    single = double = backtick = False
    escaped = False
    i = 0
    while i <= len(line) - len(marker):
        ch = line[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if ch == "\\" and (single or double or backtick):
            escaped = True
            i += 1
            continue
        if ch == "'" and not double and not backtick:
            single = not single
            i += 1
            continue
        if ch == '"' and not single and not backtick:
            double = not double
            i += 1
            continue
        if ch == "`" and not single and not double:
            backtick = not backtick
            i += 1
            continue
        if not single and not double and not backtick and line.startswith(marker, i):
            return i
        i += 1
    return -1


def comment_hits(text: str, language: str) -> list[CommentHit]:
    hits: list[CommentHit] = []
    lines = text.splitlines()
    if language == "batch":
        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()
            low = stripped.lower()
            if low.startswith("rem ") or low == "rem":
                col = len(line) - len(stripped)
                hits.append(CommentHit(i, col, stripped[3:].strip(), True, stripped[:3]))
            elif stripped.startswith("::"):
                col = len(line) - len(stripped)
                hits.append(CommentHit(i, col, stripped[2:].strip(), True, "::"))
        return hits

    if language == "html":
        for i, line in enumerate(lines, 1):
            start = line.find("<!--")
            if start >= 0:
                end = line.find("-->", start + 4)
                body = line[start + 4:end if end >= 0 else None].strip()
                hits.append(CommentHit(i, start, body, line[:start].strip() == "", "<!--", "-->" if end >= 0 else ""))
        return hits

    if language == "razor":
        for i, line in enumerate(lines, 1):
            start = line.find("@*")
            if start >= 0:
                end = line.find("*@", start + 2)
                body = line[start + 2:end if end >= 0 else None].strip()
                hits.append(CommentHit(i, start, body, line[:start].strip() == "", "@*", "*@" if end >= 0 else ""))
        # Continue to // comments too.

    if language in {"css", "scss"}:
        for i, line in enumerate(lines, 1):
            start = line.find("/*")
            if start >= 0:
                end = line.find("*/", start + 2)
                body = line[start + 2:end if end >= 0 else None].strip()
                hits.append(CommentHit(i, start, body, line[:start].strip() == "", "/*", "*/" if end >= 0 else ""))
        return hits

    marker = LINE_COMMENT.get(language)
    if marker:
        for i, line in enumerate(lines, 1):
            if language == "python" and i == 1 and line.startswith("#!"):
                continue
            if language == "python" and i <= 2 and "coding" in line and line.lstrip().startswith("#"):
                continue
            pos = marker_outside_quotes(line, marker)
            if pos >= 0:
                body = line[pos + len(marker):].strip()
                hits.append(CommentHit(i, pos, body, line[:pos].strip() == "", marker))
    return hits


def materialize_comments(path: Path, text: str, language: str, registry: dict) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    hits = comment_hits(text, language)
    if not hits:
        return text, 0
    occurrence: Counter[str] = Counter()
    changed = 0
    for hit in hits:
        clean = strip_materialized_id(hit.text)
        key = normalize_space(clean)
        occurrence[key] += 1
        fp = fingerprint(path, language, "comment", clean, occurrence[key])
        existing_match = MATERIALIZED_RE.search(hit.text)
        meta = {"kind": "comment", "language": language, "path": rel(path), "text": key}
        if existing_match:
            numeric = reserve_existing_id(registry, fp, existing_match.group("id"), meta)
        else:
            numeric = allocate_id(registry, fp, meta)
        if not hit.full_line or existing_match:
            continue
        idx = hit.line - 1
        original = lines[idx]
        newline = "\n" if original.endswith("\n") else ""
        bodyline = original[:-1] if newline else original
        indent = bodyline[:len(bodyline) - len(bodyline.lstrip())]
        locator = display_id(numeric, language, path, hit.line, "comment")
        if hit.marker in {"<!--", "@*", "/*"}:
            closing = hit.end_marker or ({"<!--": "-->", "@*": "*@", "/*": "*/"}[hit.marker])
            rendered = f"{indent}{hit.marker} {locator} {clean} {closing}".rstrip() + newline
        elif language == "batch" and hit.marker.lower() == "rem":
            rendered = f"{indent}REM {locator} {clean}".rstrip() + newline
        elif hit.marker == "::":
            rendered = f"{indent}:: {locator} {clean}".rstrip() + newline
        else:
            rendered = f"{indent}{hit.marker} {locator} {clean}".rstrip() + newline
        if rendered != original:
            lines[idx] = rendered
            changed += 1
    return "".join(lines), changed


def materialize_all_comments(config: dict, registry: dict) -> dict:
    allowed = set(config.get("materialize_languages", []))
    files_changed = comments_changed = 0
    for path in tracked_files():
        if not path.exists():
            continue
        category, _ = classify(path, config)
        if category not in {"source", "config"}:
            continue
        language = LANGUAGES.get(path.suffix.lower())
        if not language or language not in allowed:
            continue
        text = safe_text(path)
        if text is None:
            continue
        updated, n = materialize_comments(path, text, language, registry)
        if n:
            path.write_text(updated, encoding="utf-8", newline="\n")
            files_changed += 1
            comments_changed += n
    return {"files_changed": files_changed, "comments_materialized": comments_changed}


def iter_code_records(path: Path, text: str, language: str, category: str, registry: dict) -> Iterable[dict]:
    comment_lines = {h.line for h in comment_hits(text, language)}
    comment_occurrence: Counter[str] = Counter()
    for hit in comment_hits(text, language):
        clean = strip_materialized_id(hit.text)
        key = normalize_space(clean)
        comment_occurrence[key] += 1
        fp = fingerprint(path, language, "comment", clean, comment_occurrence[key])
        found = MATERIALIZED_RE.search(hit.text)
        meta = {"kind": "comment", "language": language, "path": rel(path), "text": key}
        numeric = reserve_existing_id(registry, fp, found.group("id"), meta) if found else allocate_id(registry, fp, meta)
        yield {
            "id": numeric,
            "display_id": display_id(numeric, language, path, hit.line, "comment"),
            "kind": "comment", "language": language, "path": rel(path), "line": hit.line,
            "column": hit.column + 1, "classification": category, "text": key,
            "materialized": bool(found), "fingerprint": fp,
        }

    code_occurrence: Counter[str] = Counter()
    for line_no, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped:
            continue
        # A full-line comment is represented by its comment record, not duplicated as code.
        if line_no in comment_lines and any(h.line == line_no and h.full_line for h in comment_hits(text, language)):
            continue
        norm = normalize_space(raw)
        code_occurrence[norm] += 1
        fp = fingerprint(path, language, "code", norm, code_occurrence[norm])
        meta = {"kind": "code", "language": language, "path": rel(path), "text": norm}
        numeric = allocate_id(registry, fp, meta)
        yield {
            "id": numeric,
            "display_id": display_id(numeric, language, path, line_no, "code"),
            "kind": "code", "language": language, "path": rel(path), "line": line_no,
            "column": 1, "classification": category, "text": norm,
            "materialized": False, "fingerprint": fp,
        }


def exact_duplicate_groups(file_rows: list[dict]) -> list[dict]:
    groups: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in file_rows:
        if row["classification"] not in {"source", "vendor", "config"}:
            continue
        if not row.get("sha256"):
            continue
        groups[(row["sha256"], row.get("language", ""))].append(row)
    out = []
    for (digest, language), rows in groups.items():
        if len(rows) < 2:
            continue
        out.append({
            "sha256": digest, "language": language,
            "paths": sorted(r["path"] for r in rows),
            "classifications": sorted({r["classification"] for r in rows}),
            "source_duplicate": sum(1 for r in rows if r["classification"] == "source") > 1,
        })
    return sorted(out, key=lambda g: (not g["source_duplicate"], g["paths"]))


def build_index(config: dict, registry: dict) -> dict:
    rows: list[dict] = []
    file_rows: list[dict] = []
    stale_rows: list[dict] = []
    tracked = [p for p in tracked_files() if p.exists()]
    never = tuple(config.get("never_index_prefixes", []))

    for path in tracked:
        rp = rel(path)
        if rp.startswith(never):
            continue
        category, reasons = classify(path, config)
        try:
            digest = sha256_file(path)
            size = path.stat().st_size
        except OSError:
            digest, size = "", 0
        language = LANGUAGES.get(path.suffix.lower(), "")
        file_row = {
            "path": rp, "classification": category, "language": language,
            "bytes": size, "sha256": digest, "reasons": reasons,
        }
        file_rows.append(file_row)
        if category in {"stale", "generated"}:
            stale_rows.append(file_row)
        if not language:
            continue
        text = safe_text(path)
        if text is None:
            continue
        rows.extend(iter_code_records(path, text, language, category, registry))

    # Mark registry entries that no longer correspond to a current record as retired.
    active_fps = {r["fingerprint"] for r in rows}
    for fp, entry in registry.get("entries", {}).items():
        entry["status"] = "active" if fp in active_fps else "retired"

    rows.sort(key=lambda r: (r["path"], r["line"], 0 if r["kind"] == "comment" else 1, r["id"]))
    duplicates = exact_duplicate_groups(file_rows)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with INDEX_JSONL.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    with INDEX_TSV.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("id\tdisplay_id\tkind\tlanguage\tclassification\tpath\tline\ttext\n")
        for row in rows:
            text = row["text"].replace("\t", " ").replace("\n", " ")
            fh.write(f"{row['id']}\t{row['display_id']}\t{row['kind']}\t{row['language']}\t{row['classification']}\t{row['path']}\t{row['line']}\t{text}\n")
    DUPLICATES_PATH.write_text(json.dumps(duplicates, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    STALE_PATH.write_text(json.dumps(sorted(stale_rows, key=lambda r: r["path"]), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    counts = Counter(r["classification"] for r in file_rows)
    record_counts = Counter(r["kind"] for r in rows)
    summary = {
        "version": 1,
        "tracked_files": len(file_rows),
        "indexed_records": len(rows),
        "code_records": record_counts.get("code", 0),
        "comment_records": record_counts.get("comment", 0),
        "files_by_classification": dict(sorted(counts.items())),
        "exact_duplicate_groups": len(duplicates),
        "exact_source_duplicate_groups": sum(1 for g in duplicates if g["source_duplicate"]),
        "stale_or_generated_candidates": len(stale_rows),
        "next_id": registry.get("next_id", 1),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def read_index() -> list[dict]:
    if not INDEX_JSONL.exists():
        return []
    out = []
    for line in INDEX_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def find(term: str) -> int:
    needle = term.casefold()
    matches = [r for r in read_index() if needle in json.dumps(r, ensure_ascii=False).casefold()]
    for row in matches[:200]:
        print(f"{row['display_id']}\t{row['path']}:{row['line']}\t{row['text']}")
    if len(matches) > 200:
        print(f"... {len(matches) - 200} more matches")
    return 0 if matches else 1


def find_id(value: str) -> int:
    numeric = value.split(".", 1)[0]
    matches = [r for r in read_index() if r.get("id") == numeric or r.get("display_id") == value]
    for row in matches:
        print(json.dumps(row, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if matches else 1


def verify(config: dict) -> int:
    errors: list[str] = []
    rows = read_index()
    ids = [r["id"] for r in rows]
    repeated_ids = [item for item, count in Counter(ids).items() if count > 1]
    if repeated_ids:
        errors.append("duplicate active IDs: " + ", ".join(repeated_ids[:20]))

    if DUPLICATES_PATH.exists() and config.get("fail_on_new_exact_source_duplicates", True):
        groups = json.loads(DUPLICATES_PATH.read_text(encoding="utf-8"))
        bad = [g for g in groups if g.get("source_duplicate")]
        if bad:
            errors.append(f"exact first-party source duplicate groups: {len(bad)}")

    for path in tracked_files():
        if path.exists() and is_explicit_stale(path, config):
            errors.append(f"tracked explicit stale path remains: {rel(path)}")
            if len(errors) >= 50:
                break

    if errors:
        print("CODE INDEX VERIFY FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    print("CODE INDEX VERIFY OK")
    return 0


def bootstrap(args: argparse.Namespace) -> int:
    config = load_config()
    registry = load_registry(int(config.get("id_width", 6)))
    cleanup = []
    if args.prune or config.get("prune_explicit_stale", False):
        cleanup = prune_explicit_stale(config)
    materialized = {"files_changed": 0, "comments_materialized": 0}
    if args.materialize or config.get("materialize_comment_ids", False):
        materialized = materialize_all_comments(config, registry)
    summary = build_index(config, registry)
    print(json.dumps({"cleanup_files": len(cleanup), **materialized, **summary}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Shaelvien persistent code index")
    sub = parser.add_subparsers(dest="command", required=True)
    p_boot = sub.add_parser("build", help="refresh index/log")
    p_boot.add_argument("--prune", action="store_true", help="remove explicit stale paths from active tree")
    p_boot.add_argument("--materialize", action="store_true", help="write stable IDs into safe full-line source comments")
    p_find = sub.add_parser("find", help="search indexed code/comments")
    p_find.add_argument("term")
    p_id = sub.add_parser("find-id", help="locate one canonical numeric/display ID")
    p_id.add_argument("value")
    sub.add_parser("duplicates", help="print duplicate report")
    sub.add_parser("stale", help="print stale/generated report")
    sub.add_parser("verify", help="enforce index invariants")
    args = parser.parse_args()

    if args.command == "build":
        return bootstrap(args)
    if args.command == "find":
        return find(args.term)
    if args.command == "find-id":
        return find_id(args.value)
    if args.command == "duplicates":
        print(DUPLICATES_PATH.read_text(encoding="utf-8") if DUPLICATES_PATH.exists() else "[]")
        return 0
    if args.command == "stale":
        print(STALE_PATH.read_text(encoding="utf-8") if STALE_PATH.exists() else "[]")
        return 0
    if args.command == "verify":
        return verify(load_config())
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
