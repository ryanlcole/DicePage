#!/usr/bin/env python3
"""Shaelvien persistent code index and source-governance tool.

Canonical truth is the six-digit numeric ID. The readable suffix is a locator
that is regenerated as code moves, for example:

    000009.csharp.CharacterSelection.line8.code
    000010.html.Home.line54.comment

Every indexed code line and every detected source comment receives an ID in the
external log. Source rewriting is deliberately conservative: only languages
with a parser-safe materializer are changed in-place. At present that is Python
comments via the standard-library tokenizer. Other languages are fully indexed
without risking a semantic change to strings, templates, heredocs, or docs.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tokenize
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / ".code-index"
CONFIG_PATH = INDEX_DIR / "config.json"
REGISTRY_PATH = INDEX_DIR / "id_registry.json"
INDEX_JSONL = INDEX_DIR / "code_index.jsonl"
INDEX_TSV = INDEX_DIR / "code_index.tsv"
SUMMARY_PATH = INDEX_DIR / "summary.json"
DUPLICATES_PATH = INDEX_DIR / "duplicates.json"
DUPLICATE_BASELINE_PATH = INDEX_DIR / "duplicate_baseline.json"
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
    "powershell": "#", "shell": "#", "yaml": "#",
    "csharp": "//", "razor": "//", "javascript": "//", "typescript": "//",
    "c": "//", "cpp": "//", "java": "//", "kotlin": "//", "swift": "//",
    "go": "//", "rust": "//", "sql": "--",
}
C_BLOCK_LANGUAGES = {
    "csharp", "javascript", "typescript", "c", "cpp", "java", "kotlin",
    "swift", "go", "rust", "css", "scss"
}
MATERIALIZED_RE = re.compile(
    r"\b(?P<id>\d{6,})\.(?P<language>[A-Za-z0-9_+-]+)\."
    r"(?P<scope>[A-Za-z0-9_.-]+)\.line\d+\.(?P<kind>comment|code)\b"
)


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


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def tracked_files() -> list[Path]:
    result = run_git("ls-files", "-z")
    return [ROOT / item for item in result.stdout.split("\0") if item]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def safe_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    payload = "\x1f".join((
        rel(path), language, kind,
        normalize_space(strip_materialized_id(text)), str(occurrence),
    ))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_registry(width: int) -> dict:
    if REGISTRY_PATH.exists():
        try:
            data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("entries"), dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return {"version": 1, "width": width, "next_id": 1, "entries": {}}


def used_ids(registry: dict) -> set[str]:
    return {
        str(entry.get("id"))
        for entry in registry.get("entries", {}).values()
        if entry.get("id")
    }


def allocate_id(registry: dict, fp: str, metadata: dict, preferred: str | None = None) -> str:
    entries = registry.setdefault("entries", {})
    if fp in entries:
        entries[fp].update(metadata)
        return str(entries[fp]["id"])

    used = used_ids(registry)
    if preferred and preferred not in used:
        value = preferred
        registry["next_id"] = max(int(registry.get("next_id", 1)), int(preferred) + 1)
    else:
        width = int(registry.get("width", 6))
        n = int(registry.get("next_id", 1))
        while f"{n:0{width}d}" in used:
            n += 1
        value = f"{n:0{width}d}"
        registry["next_id"] = n + 1
    entries[fp] = {"id": value, **metadata}
    return value


def classify(path: Path, config: dict) -> tuple[str, list[str]]:
    rp = rel(path)
    parts = tuple(part.lower() for part in Path(rp).parts)
    name = path.name.lower()
    ext = path.suffix.lower()
    preserve = {item.lower() for item in config.get("preserve_stale_paths", [])}
    if rp.lower() in preserve:
        return ("source" if ext in LANGUAGES else "other"), ["explicitly-preserved"]

    stale_suffixes = tuple(s.lower() for s in config.get("stale_suffixes", []))
    stale_dirs = {s.lower() for s in config.get("stale_directory_names", [])}
    if (
        (stale_suffixes and name.endswith(stale_suffixes))
        or any(stale_suffixes and part.endswith(stale_suffixes) for part in parts)
        or any(part in stale_dirs for part in parts)
    ):
        return "stale", ["explicit-stale-name"]

    generated_dirs = {s.lower() for s in config.get("generated_directory_names", [])}
    compiled_exts = {s.lower() for s in config.get("compiled_extensions", [])}
    if any(part in generated_dirs for part in parts) or ext in compiled_exts:
        return "generated", ["generated-or-compiled"]

    vendor_roots = {s.lower() for s in config.get("vendor_top_level", [])}
    if parts and (
        parts[0] in vendor_roots
        or parts[0].endswith(".dist-info")
        or "site-packages" in parts
    ):
        return "vendor", ["vendored-dependency"]

    if ext in LANGUAGES:
        return "source", []
    if ext in {".md", ".txt", ".rst"}:
        return "docs", []
    if ext in {".json", ".toml", ".ini", ".cfg", ".spec", ".yml", ".yaml", ".xml"}:
        return "config", []
    return "asset", []


def is_explicit_stale(path: Path, config: dict) -> bool:
    return classify(path, config)[0] == "stale"


def append_cleanup(records: list[dict]) -> None:
    if not records:
        return
    existing = ""
    if CLEANUP_LOG.exists():
        existing = CLEANUP_LOG.read_text(encoding="utf-8")
    with CLEANUP_LOG.open("w", encoding="utf-8", newline="\n") as handle:
        if existing:
            handle.write(existing.rstrip("\n") + "\n")
        for row in records:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def prune_explicit_stale(config: dict) -> list[dict]:
    records: list[dict] = []
    for path in tracked_files():
        if not path.exists() or not is_explicit_stale(path, config):
            continue
        try:
            digest = sha256_file(path)
            size = path.stat().st_size
        except OSError:
            digest, size = "unreadable", 0
        records.append({
            "path": rel(path),
            "reason": "explicit-stale-name",
            "sha256": digest,
            "bytes": size,
            "status": "removed-from-active-tree",
        })
        try:
            path.unlink()
        except OSError:
            pass
    append_cleanup(records)
    return records


def marker_outside_quotes(line: str, marker: str) -> int:
    single = double = backtick = False
    escaped = False
    i = 0
    limit = len(line) - len(marker)
    while i <= limit:
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


def python_comment_hits(text: str) -> list[CommentHit]:
    hits: list[CommentHit] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in tokens:
            if token.type != tokenize.COMMENT:
                continue
            line_no, col = token.start
            raw = token.string
            # Leave interpreter and encoding directives untouched as source text.
            if line_no == 1 and raw.startswith("#!"):
                continue
            if line_no <= 2 and "coding" in raw:
                continue
            source_line = token.line or ""
            hits.append(CommentHit(
                line=line_no,
                column=col,
                text=raw[1:].strip(),
                full_line=(source_line[:col].strip() == ""),
                marker="#",
            ))
    except (tokenize.TokenError, IndentationError):
        # Broken Python is still indexed as code; comments are not guessed.
        pass
    return hits


def comment_hits(text: str, language: str) -> list[CommentHit]:
    if language == "python":
        return python_comment_hits(text)

    lines = text.splitlines()
    hits: list[CommentHit] = []
    if language == "batch":
        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()
            low = stripped.lower()
            col = len(line) - len(stripped)
            if low.startswith("rem ") or low == "rem":
                hits.append(CommentHit(i, col, stripped[3:].strip(), True, stripped[:3]))
            elif stripped.startswith("::"):
                hits.append(CommentHit(i, col, stripped[2:].strip(), True, "::"))
        return hits

    if language == "html":
        for i, line in enumerate(lines, 1):
            start = line.find("<!--")
            if start < 0:
                continue
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

    if language in C_BLOCK_LANGUAGES:
        for i, line in enumerate(lines, 1):
            start = marker_outside_quotes(line, "/*")
            if start >= 0:
                actual = "/**" if line.startswith("/**", start) else "/*"
                end = line.find("*/", start + len(actual))
                body = line[start + len(actual):end if end >= 0 else None].strip()
                hits.append(CommentHit(i, start, body, line[:start].strip() == "", actual, "*/" if end >= 0 else ""))

    marker = LINE_COMMENT.get(language)
    if marker:
        for i, line in enumerate(lines, 1):
            pos = marker_outside_quotes(line, marker)
            if pos < 0:
                continue
            actual = marker
            if marker == "//" and line.startswith("///", pos):
                actual = "///"
            body = line[pos + len(actual):].strip()
            hits.append(CommentHit(i, pos, body, line[:pos].strip() == "", actual))
    return sorted(hits, key=lambda hit: (hit.line, hit.column, hit.marker))


def materialize_python_comments(path: Path, text: str, registry: dict) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    hits = python_comment_hits(text)
    occurrence: Counter[str] = Counter()
    changed = 0
    for hit in hits:
        clean = strip_materialized_id(hit.text)
        key = normalize_space(clean)
        occurrence[key] += 1
        fp = fingerprint(path, "python", "comment", clean, occurrence[key])
        existing = MATERIALIZED_RE.search(hit.text)
        meta = {"kind": "comment", "language": "python", "path": rel(path), "text": key}
        numeric = allocate_id(registry, fp, meta, existing.group("id") if existing else None)
        if not hit.full_line or existing:
            continue
        idx = hit.line - 1
        original = lines[idx]
        newline = "\n" if original.endswith("\n") else ""
        body = original[:-1] if newline else original
        indent = body[:len(body) - len(body.lstrip())]
        locator = display_id(numeric, "python", path, hit.line, "comment")
        rendered = f"{indent}# {locator} {clean}".rstrip() + newline
        if rendered != original:
            lines[idx] = rendered
            changed += 1
    return "".join(lines), changed


def materialize_all_comments(config: dict, registry: dict) -> dict:
    allowed = set(config.get("materialize_languages", []))
    files_changed = comments_changed = 0
    if "python" not in allowed:
        return {"files_changed": 0, "comments_materialized": 0}
    for path in tracked_files():
        if not path.exists() or path.suffix.lower() != ".py":
            continue
        category, _ = classify(path, config)
        if category != "source":
            continue
        text = safe_text(path)
        if text is None:
            continue
        updated, count = materialize_python_comments(path, text, registry)
        if count:
            path.write_text(updated, encoding="utf-8", newline="\n")
            files_changed += 1
            comments_changed += count
    return {"files_changed": files_changed, "comments_materialized": comments_changed}


def iter_records(path: Path, text: str, language: str, category: str, registry: dict) -> Iterable[dict]:
    hits = comment_hits(text, language)
    full_comment_lines = {hit.line for hit in hits if hit.full_line}
    comment_occurrence: Counter[str] = Counter()

    for hit in hits:
        clean = strip_materialized_id(hit.text)
        norm = normalize_space(clean)
        comment_occurrence[norm] += 1
        fp = fingerprint(path, language, "comment", clean, comment_occurrence[norm])
        existing = MATERIALIZED_RE.search(hit.text)
        meta = {"kind": "comment", "language": language, "path": rel(path), "text": norm}
        numeric = allocate_id(registry, fp, meta, existing.group("id") if existing else None)
        yield {
            "id": numeric,
            "display_id": display_id(numeric, language, path, hit.line, "comment"),
            "kind": "comment",
            "language": language,
            "path": rel(path),
            "line": hit.line,
            "column": hit.column + 1,
            "classification": category,
            "text": norm,
            "materialized": bool(existing),
            "fingerprint": fp,
        }

    code_occurrence: Counter[str] = Counter()
    for line_no, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or line_no in full_comment_lines:
            continue
        norm = normalize_space(raw)
        code_occurrence[norm] += 1
        fp = fingerprint(path, language, "code", norm, code_occurrence[norm])
        meta = {"kind": "code", "language": language, "path": rel(path), "text": norm}
        numeric = allocate_id(registry, fp, meta)
        yield {
            "id": numeric,
            "display_id": display_id(numeric, language, path, line_no, "code"),
            "kind": "code",
            "language": language,
            "path": rel(path),
            "line": line_no,
            "column": 1,
            "classification": category,
            "text": norm,
            "materialized": False,
            "fingerprint": fp,
        }


def exact_duplicate_groups(file_rows: list[dict]) -> list[dict]:
    grouped: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in file_rows:
        if row["classification"] not in {"source", "vendor", "config"} or not row.get("sha256"):
            continue
        grouped[(row["sha256"], row.get("language", ""))].append(row)
    result: list[dict] = []
    for (digest, language), rows in grouped.items():
        if len(rows) < 2:
            continue
        paths = sorted(row["path"] for row in rows)
        result.append({
            "key": digest + ":" + "|".join(paths),
            "sha256": digest,
            "language": language,
            "paths": paths,
            "classifications": sorted({row["classification"] for row in rows}),
            "source_duplicate": sum(row["classification"] == "source" for row in rows) > 1,
        })
    return sorted(result, key=lambda row: (not row["source_duplicate"], row["paths"]))


def write_duplicate_baseline(duplicates: list[dict], config: dict) -> None:
    if DUPLICATE_BASELINE_PATH.exists() or not config.get("baseline_existing_exact_source_duplicates", True):
        return
    keys = sorted(row["key"] for row in duplicates if row.get("source_duplicate"))
    DUPLICATE_BASELINE_PATH.write_text(
        json.dumps({"version": 1, "allowed_existing_source_duplicate_keys": keys}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_index(config: dict, registry: dict) -> dict:
    records: list[dict] = []
    file_rows: list[dict] = []
    stale_rows: list[dict] = []
    never = tuple(config.get("never_index_prefixes", []))

    for path in tracked_files():
        if not path.exists():
            continue
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
            "path": rp,
            "classification": category,
            "language": language,
            "bytes": size,
            "sha256": digest,
            "reasons": reasons,
        }
        file_rows.append(file_row)
        if category in {"stale", "generated"}:
            stale_rows.append(file_row)
        if not language:
            continue
        text = safe_text(path)
        if text is not None:
            records.extend(iter_records(path, text, language, category, registry))

    active_fps = {row["fingerprint"] for row in records}
    for fp, entry in registry.get("entries", {}).items():
        entry["status"] = "active" if fp in active_fps else "retired"

    records.sort(key=lambda row: (row["path"], row["line"], row["column"], row["kind"], row["id"]))
    duplicates = exact_duplicate_groups(file_rows)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    with INDEX_JSONL.open("w", encoding="utf-8", newline="\n") as handle:
        for row in records:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    with INDEX_TSV.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("id\tdisplay_id\tkind\tlanguage\tclassification\tpath\tline\ttext\n")
        for row in records:
            clean_text = row["text"].replace("\t", " ").replace("\n", " ")
            handle.write(
                f"{row['id']}\t{row['display_id']}\t{row['kind']}\t{row['language']}\t"
                f"{row['classification']}\t{row['path']}\t{row['line']}\t{clean_text}\n"
            )

    DUPLICATES_PATH.write_text(json.dumps(duplicates, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    STALE_PATH.write_text(json.dumps(sorted(stale_rows, key=lambda row: row["path"]), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_duplicate_baseline(duplicates, config)

    file_counts = Counter(row["classification"] for row in file_rows)
    record_counts = Counter(row["kind"] for row in records)
    summary = {
        "version": 1,
        "tracked_files": len(file_rows),
        "indexed_records": len(records),
        "code_records": record_counts.get("code", 0),
        "comment_records": record_counts.get("comment", 0),
        "files_by_classification": dict(sorted(file_counts.items())),
        "exact_duplicate_groups": len(duplicates),
        "exact_source_duplicate_groups": sum(bool(row["source_duplicate"]) for row in duplicates),
        "stale_or_generated_candidates": len(stale_rows),
        "next_id": registry.get("next_id", 1),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def read_index() -> list[dict]:
    if not INDEX_JSONL.exists():
        return []
    return [json.loads(line) for line in INDEX_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]


def find(term: str) -> int:
    needle = term.casefold()
    matches = [row for row in read_index() if needle in json.dumps(row, ensure_ascii=False).casefold()]
    for row in matches[:200]:
        print(f"{row['display_id']}\t{row['path']}:{row['line']}\t{row['text']}")
    if len(matches) > 200:
        print(f"... {len(matches) - 200} more matches")
    return 0 if matches else 1


def find_id(value: str) -> int:
    numeric = value.split(".", 1)[0]
    matches = [row for row in read_index() if row.get("id") == numeric or row.get("display_id") == value]
    for row in matches:
        print(json.dumps(row, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if matches else 1


def verify(config: dict) -> int:
    errors: list[str] = []
    rows = read_index()
    repeated = [value for value, count in Counter(row["id"] for row in rows).items() if count > 1]
    if repeated:
        errors.append("duplicate active IDs: " + ", ".join(repeated[:20]))

    for path in tracked_files():
        if path.exists() and is_explicit_stale(path, config):
            errors.append(f"tracked explicit stale path remains: {rel(path)}")
            if len(errors) >= 50:
                break

    if config.get("fail_on_new_exact_source_duplicates", True) and DUPLICATES_PATH.exists():
        duplicate_rows = json.loads(DUPLICATES_PATH.read_text(encoding="utf-8"))
        current = {row["key"] for row in duplicate_rows if row.get("source_duplicate")}
        allowed: set[str] = set()
        if DUPLICATE_BASELINE_PATH.exists():
            baseline = json.loads(DUPLICATE_BASELINE_PATH.read_text(encoding="utf-8"))
            allowed = set(baseline.get("allowed_existing_source_duplicate_keys", []))
        new_groups = sorted(current - allowed)
        if new_groups:
            errors.append(f"new exact first-party source duplicate groups: {len(new_groups)}")

    if errors:
        print("CODE INDEX VERIFY FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    print("CODE INDEX VERIFY OK")
    return 0


def build_command(args: argparse.Namespace) -> int:
    config = load_config()
    registry = load_registry(int(config.get("id_width", 6)))
    removed = []
    if args.prune or config.get("prune_explicit_stale", False):
        removed = prune_explicit_stale(config)
    materialized = {"files_changed": 0, "comments_materialized": 0}
    if args.materialize or config.get("materialize_comment_ids", False):
        materialized = materialize_all_comments(config, registry)
    summary = build_index(config, registry)
    print(json.dumps({"cleanup_files": len(removed), **materialized, **summary}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Shaelvien persistent code index")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="refresh index/log")
    build.add_argument("--prune", action="store_true", help="remove explicit stale paths from active tree")
    build.add_argument("--materialize", action="store_true", help="materialize parser-safe source comment IDs")
    search = sub.add_parser("find", help="search indexed code/comments")
    search.add_argument("term")
    lookup = sub.add_parser("find-id", help="locate one canonical numeric/display ID")
    lookup.add_argument("value")
    sub.add_parser("duplicates", help="print exact duplicate report")
    sub.add_parser("stale", help="print stale/generated report")
    sub.add_parser("verify", help="enforce index invariants")
    args = parser.parse_args()

    if args.command == "build":
        return build_command(args)
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
