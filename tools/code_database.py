#!/usr/bin/env python3
"""Build Shaelvien's semantic code database and recurring-error graph.

The persistent code index identifies source records. This tool adds semantic
symbols (CHIDs), references, graph edges, and normalized error signatures.
Python extraction is AST-backed. Other languages begin with conservative
structured extraction and preserve evidence/confidence rather than pretending
heuristics are parser facts.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ROOT / ".code-index"
INDEX_JSONL = INDEX_DIR / "code_index.jsonl"
CHID_REGISTRY = INDEX_DIR / "chid_registry.json"
DATABASE_PATH = INDEX_DIR / "code_graph.sqlite3"
MERMAID_PATH = INDEX_DIR / "relationships.mmd"
DOT_PATH = INDEX_DIR / "relationships.dot"
SUMMARY_PATH = INDEX_DIR / "code_database_summary.json"
ERROR_SOURCES_PATH = INDEX_DIR / "error_sources.json"
RUNTIME_ERRORS_PATH = INDEX_DIR / "runtime_errors.jsonl"

CS_CLASS = re.compile(r"\b(class|interface|record|struct|enum)\s+([A-Za-z_][A-Za-z0-9_]*)")
CS_METHOD = re.compile(
    r"^\s*(?:(?:public|private|protected|internal|static|virtual|override|async|sealed|partial|new|extern)\s+)*"
    r"(?P<type>[A-Za-z_][A-Za-z0-9_<>,.?\[\]]*)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\((?P<args>[^()]*)\)"
)
CS_VAR = re.compile(
    r"^\s*(?:(?:public|private|protected|internal|static|readonly|const|required|volatile)\s+)*"
    r"(?P<type>var|[A-Za-z_][A-Za-z0-9_<>,.?\[\]]*)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*(?:=|;|\{|$)"
)
JS_DECL = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)")
JS_FUNC = re.compile(r"\b(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(([^)]*)\)")
JS_CLASS = re.compile(r"\bclass\s+([A-Za-z_$][A-Za-z0-9_$]*)")
TS_TYPE = re.compile(r"\b(?:interface|type|enum)\s+([A-Za-z_$][A-Za-z0-9_$]*)")
HTML_ID = re.compile(r"\b(?:id|name)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
CALL = re.compile(r"\b([A-Za-z_][A-Za-z0-9_.]*)\s*\(")

ERROR_FILE_LINE_PATTERNS = [
    re.compile(r"(?P<path>[A-Za-z0-9_./\\-]+\.(?:py|cs|razor|js|ts|tsx|jsx|html|css))[:(](?P<line>\d+)"),
    re.compile(r"File \"(?P<path>[^\"]+)\", line (?P<line>\d+)"),
]
ERROR_CODE = re.compile(r"\b(?:CS|TS|NETSDK|NU|MSB|E|ERR)[-_]?[A-Z0-9]{2,8}\b", re.IGNORECASE)
TIMESTAMP = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+Z?\b")
GUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)
HEXADDR = re.compile(r"0x[0-9a-f]+", re.IGNORECASE)
LONG_NUMBER = re.compile(r"\b\d{4,}\b")
WS = re.compile(r"\s+")


@dataclass
class Symbol:
    fingerprint: str
    name: str
    qualified_name: str
    kind: str
    type_name: str
    path: str
    line: int
    scope: str
    language: str
    declaration_code_id: str | None
    signature: str
    confidence: float
    evidence: str
    chid: str = ""


@dataclass
class Ref:
    path: str
    line: int
    raw_name: str
    kind: str
    language: str
    source_code_id: str | None
    source_scope: str
    confidence: float
    evidence: str
    source_chid: str | None = None
    target_chid: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8", "replace")).hexdigest()


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def load_index() -> list[dict]:
    if not INDEX_JSONL.exists():
        raise SystemExit("Missing .code-index/code_index.jsonl; run code_index.py build first")
    rows = []
    for line in INDEX_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def source_files(rows: list[dict]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        if row.get("classification") == "source" and row.get("language"):
            result[row["path"]] = row["language"]
    return result


def line_ids(rows: list[dict]) -> dict[tuple[str, int], str]:
    return {
        (row["path"], int(row["line"])): row["id"]
        for row in rows if row.get("kind") == "code"
    }


def symbol_fp(path: str, kind: str, qualified: str, scope: str) -> str:
    return sha(path, kind, qualified, scope)


def load_chids() -> dict:
    value = read_json(CHID_REGISTRY, {})
    if not isinstance(value, dict) or not isinstance(value.get("entries"), dict):
        return {"version": 1, "next_id": 1, "entries": {}}
    return value


def assign_chids(symbols: list[Symbol]) -> dict:
    registry = load_chids()
    entries = registry.setdefault("entries", {})
    next_id = int(registry.get("next_id", 1))
    active = set()
    for symbol in symbols:
        active.add(symbol.fingerprint)
        entry = entries.get(symbol.fingerprint)
        if entry:
            symbol.chid = str(entry["chid"])
            aliases = set(entry.get("aliases", []))
            aliases.add(symbol.name)
            entry.update({
                "name": symbol.name,
                "qualified_name": symbol.qualified_name,
                "kind": symbol.kind,
                "path": symbol.path,
                "scope": symbol.scope,
                "aliases": sorted(aliases),
                "status": "active",
            })
        else:
            symbol.chid = f"chid.{next_id:06d}"
            next_id += 1
            entries[symbol.fingerprint] = {
                "chid": symbol.chid,
                "name": symbol.name,
                "qualified_name": symbol.qualified_name,
                "kind": symbol.kind,
                "path": symbol.path,
                "scope": symbol.scope,
                "aliases": [symbol.name],
                "status": "active",
            }
    for fp, entry in entries.items():
        if fp not in active:
            entry["status"] = "retired"
    registry["next_id"] = next_id
    CHID_REGISTRY.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry


class PyExtractor(ast.NodeVisitor):
    def __init__(self, path: str, ids: dict[tuple[str, int], str]):
        self.path = path
        self.ids = ids
        self.symbols: list[Symbol] = []
        self.refs: list[Ref] = []
        self.scopes: list[str] = []
        self.scope_kinds: list[str] = []

    @property
    def scope(self) -> str:
        return ".".join(self.scopes)

    def qualify(self, name: str) -> str:
        return f"{self.scope}.{name}" if self.scope else name

    def symbol(self, name: str, kind: str, node: ast.AST, type_name: str = "", signature: str = "") -> None:
        line = int(getattr(node, "lineno", 1))
        qualified = self.qualify(name)
        self.symbols.append(Symbol(
            symbol_fp(self.path, kind, qualified, self.scope), name, qualified, kind,
            type_name, self.path, line, self.scope, "python", self.ids.get((self.path, line)),
            signature, 1.0, "python-ast"
        ))

    def ref(self, name: str, kind: str, node: ast.AST) -> None:
        if not name:
            return
        line = int(getattr(node, "lineno", 1))
        self.refs.append(Ref(
            self.path, line, name, kind, "python", self.ids.get((self.path, line)),
            self.scope, 1.0, "python-ast"
        ))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.symbol(node.name, "class", node)
        self.scopes.append(node.name); self.scope_kinds.append("class")
        for child in node.body: self.visit(child)
        self.scope_kinds.pop(); self.scopes.pop()

    def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        kind = "method" if self.scope_kinds and self.scope_kinds[-1] == "class" else "function"
        args = [a.arg for a in node.args.args]
        self.symbol(node.name, kind, node, signature=f"{node.name}({', '.join(args)})")
        self.scopes.append(node.name); self.scope_kinds.append(kind)
        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            annotation = ast.unparse(arg.annotation) if arg.annotation is not None else ""
            self.symbol(arg.arg, "parameter", arg, annotation)
        for child in node.body: self.visit(child)
        self.scope_kinds.pop(); self.scopes.pop()

    visit_FunctionDef = _function
    visit_AsyncFunctionDef = _function

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name): self.symbol(target.id, "variable", target)
            elif isinstance(target, ast.Attribute): self.symbol(target.attr, "field", target)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        typename = ast.unparse(node.annotation) if node.annotation is not None else ""
        if isinstance(node.target, ast.Name): self.symbol(node.target.id, "variable", node.target, typename)
        elif isinstance(node.target, ast.Attribute): self.symbol(node.target.attr, "field", node.target, typename)
        if node.value: self.visit(node.value)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.symbol(alias.asname or alias.name.split(".")[0], "import", node, alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            self.symbol(alias.asname or alias.name, "import", node, f"{module}.{alias.name}".strip("."))

    def visit_Name(self, node: ast.Name) -> None:
        self.ref(node.id, "read" if isinstance(node.ctx, ast.Load) else "write", node)

    def visit_Call(self, node: ast.Call) -> None:
        name = dotted_name(node.func)
        if name: self.ref(name, "call", node)
        self.generic_visit(node)


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute):
        left = dotted_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return ""


def generic_symbol(path: str, lang: str, ids: dict[tuple[str, int], str], line: int,
                   name: str, kind: str, scope: str = "", type_name: str = "",
                   signature: str = "", confidence: float = 0.65, evidence: str = "structured-regex") -> Symbol:
    qualified = f"{scope}.{name}" if scope else name
    return Symbol(symbol_fp(path, kind, qualified, scope), name, qualified, kind, type_name,
                  path, line, scope, lang, ids.get((path, line)), signature, confidence, evidence)


def generic_ref(path: str, lang: str, ids: dict[tuple[str, int], str], line: int,
                name: str, kind: str, scope: str = "", confidence: float = 0.5,
                evidence: str = "heuristic-lexical") -> Ref:
    return Ref(path, line, name, kind, lang, ids.get((path, line)), scope, confidence, evidence)


def extract_python(path: str, text: str, ids: dict[tuple[str, int], str]) -> tuple[list[Symbol], list[Ref]]:
    try: tree = ast.parse(text, filename=path)
    except SyntaxError: return [], []
    extractor = PyExtractor(path, ids); extractor.visit(tree)
    return extractor.symbols, extractor.refs


def extract_csharp(path: str, text: str, lang: str, ids: dict[tuple[str, int], str]) -> tuple[list[Symbol], list[Ref]]:
    symbols: list[Symbol] = []; refs: list[Ref] = []; current_type = ""
    for no, line in enumerate(text.splitlines(), 1):
        cm = CS_CLASS.search(line)
        if cm:
            current_type = cm.group(2)
            symbols.append(generic_symbol(path, lang, ids, no, current_type, cm.group(1), confidence=0.85))
        mm = CS_METHOD.match(line)
        if mm and mm.group("name") not in {"if","for","foreach","while","switch","catch","using","lock"}:
            name, args = mm.group("name"), mm.group("args")
            symbols.append(generic_symbol(path, lang, ids, no, name, "method", current_type,
                                          mm.group("type"), f"{name}({args})", 0.8))
        else:
            vm = CS_VAR.match(line)
            if vm:
                symbols.append(generic_symbol(path, lang, ids, no, vm.group("name"),
                                              "field" if current_type else "variable", current_type,
                                              vm.group("type"), confidence=0.65))
        for call in CALL.finditer(line):
            raw = call.group(1)
            if raw.split(".")[-1] not in {"if","for","foreach","while","switch","catch","nameof","typeof"}:
                refs.append(generic_ref(path, lang, ids, no, raw, "call", current_type, 0.55))
        if lang == "razor":
            for match in HTML_ID.finditer(line):
                symbols.append(generic_symbol(path, lang, ids, no, match.group(1), "ui-id", current_type,
                                              confidence=0.8, evidence="html-attribute"))
    return symbols, refs


def extract_js(path: str, text: str, lang: str, ids: dict[tuple[str, int], str]) -> tuple[list[Symbol], list[Ref]]:
    symbols: list[Symbol] = []; refs: list[Ref] = []
    for no, line in enumerate(text.splitlines(), 1):
        for m in JS_CLASS.finditer(line): symbols.append(generic_symbol(path, lang, ids, no, m.group(1), "class", confidence=0.8))
        for m in JS_FUNC.finditer(line):
            symbols.append(generic_symbol(path, lang, ids, no, m.group(1), "function", signature=f"{m.group(1)}({m.group(2)})", confidence=0.8))
        if lang == "typescript":
            for m in TS_TYPE.finditer(line): symbols.append(generic_symbol(path, lang, ids, no, m.group(1), "type", confidence=0.8))
        for m in JS_DECL.finditer(line): symbols.append(generic_symbol(path, lang, ids, no, m.group(1), "variable", confidence=0.7))
        for m in CALL.finditer(line):
            raw = m.group(1)
            if raw not in {"if","for","while","switch","catch","function"}: refs.append(generic_ref(path, lang, ids, no, raw, "call", confidence=0.55))
    return symbols, refs


def extract_html(path: str, text: str, lang: str, ids: dict[tuple[str, int], str]) -> tuple[list[Symbol], list[Ref]]:
    symbols = []
    for no, line in enumerate(text.splitlines(), 1):
        for m in HTML_ID.finditer(line):
            symbols.append(generic_symbol(path, lang, ids, no, m.group(1), "ui-id", confidence=0.9, evidence="html-attribute"))
    return symbols, []


def extract(rows: list[dict]) -> tuple[list[Symbol], list[Ref]]:
    ids = line_ids(rows); symbols: list[Symbol] = []; refs: list[Ref] = []
    for path, lang in sorted(source_files(rows).items()):
        try: text = (ROOT / path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError): continue
        if lang == "python": found_s, found_r = extract_python(path, text, ids)
        elif lang in {"csharp", "razor"}: found_s, found_r = extract_csharp(path, text, lang, ids)
        elif lang in {"javascript", "typescript"}: found_s, found_r = extract_js(path, text, lang, ids)
        elif lang == "html": found_s, found_r = extract_html(path, text, lang, ids)
        else: found_s, found_r = [], []
        symbols.extend(found_s); refs.extend(found_r)
    dedup: dict[str, Symbol] = {}
    for symbol in symbols:
        if symbol.fingerprint not in dedup or symbol.confidence > dedup[symbol.fingerprint].confidence:
            dedup[symbol.fingerprint] = symbol
    return list(dedup.values()), refs


def resolve(symbols: list[Symbol], refs: list[Ref]) -> None:
    by_name: defaultdict[str, list[Symbol]] = defaultdict(list)
    by_path: defaultdict[str, list[Symbol]] = defaultdict(list)
    for symbol in symbols:
        by_name[symbol.name].append(symbol); by_path[symbol.path].append(symbol)
    for ref in refs:
        candidates = by_name.get(ref.raw_name.split(".")[-1], [])
        same_file = [s for s in candidates if s.path == ref.path]
        same_scope = [s for s in same_file if s.scope and (ref.source_scope == s.scope or ref.source_scope.startswith(s.scope + "."))]
        chosen = same_scope[0] if len(same_scope) == 1 else same_file[0] if len(same_file) == 1 else candidates[0] if len(candidates) == 1 else None
        if chosen:
            ref.target_chid = chosen.chid
            ref.confidence = min(1.0, ref.confidence + (0.25 if chosen in same_scope else 0.15))
        possible = [s for s in by_path[ref.path] if s.line <= ref.line]
        if ref.source_scope:
            scoped = [s for s in possible if s.qualified_name == ref.source_scope or ref.source_scope.startswith(s.qualified_name + ".")]
            if scoped: possible = scoped
        if possible:
            possible.sort(key=lambda s: (s.line, len(s.qualified_name)), reverse=True)
            ref.source_chid = possible[0].chid


def normalize_error(message: str) -> str:
    text = TIMESTAMP.sub("<time>", message)
    text = GUID.sub("<guid>", text)
    text = HEXADDR.sub("<addr>", text)
    text = LONG_NUMBER.sub("<n>", text)
    text = WS.sub(" ", text).strip()
    return text[:4000]


def detect_language(message: str, path: str = "") -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".cs", ".razor", ".csproj"}: return "csharp"
    if suffix == ".py": return "python"
    if suffix in {".js", ".jsx"}: return "javascript"
    if suffix in {".ts", ".tsx"}: return "typescript"
    if suffix in {".html", ".htm"}: return "html"
    if suffix == ".css": return "css"
    lower = message.lower()
    if re.search(r"\bcs\d{4}\b", lower) or "dotnet" in lower or "msbuild" in lower: return "csharp"
    if "traceback (most recent call last)" in lower or "syntaxerror" in lower or "python" in lower: return "python"
    if "typescript" in lower or re.search(r"\bts\d{4}\b", lower): return "typescript"
    if "typeerror:" in lower or "referenceerror:" in lower or "javascript" in lower: return "javascript"
    if "css" in lower and "error" in lower: return "css"
    return "unknown"


def error_location(message: str) -> tuple[str, int]:
    for pattern in ERROR_FILE_LINE_PATTERNS:
        match = pattern.search(message)
        if match:
            path = match.group("path").replace("\\", "/")
            try: path = Path(path).relative_to(ROOT).as_posix()
            except Exception: pass
            return path, int(match.group("line"))
    return "", 0


def error_signature(message: str, language: str, path: str = "") -> tuple[str, str, str]:
    normalized = normalize_error(message)
    code_match = ERROR_CODE.search(message)
    code = code_match.group(0).upper() if code_match else ""
    signature = sha(language, code, normalized)
    return signature, normalized, code


def iter_error_source_records() -> Iterable[dict]:
    config = read_json(ERROR_SOURCES_PATH, {"sources": []})
    for source in config.get("sources", []):
        if not source.get("enabled", True): continue
        pattern = source.get("glob", "")
        fmt = source.get("format", "text")
        if not pattern: continue
        for path in ROOT.glob(pattern):
            if not path.is_file(): continue
            rel = path.relative_to(ROOT).as_posix()
            try: content = path.read_text(encoding="utf-8", errors="replace")
            except OSError: continue
            if fmt == "jsonl":
                for line_no, raw in enumerate(content.splitlines(), 1):
                    if not raw.strip(): continue
                    try: obj = json.loads(raw)
                    except json.JSONDecodeError: obj = {"message": raw}
                    message = str(obj.get("message") or obj.get("error") or obj.get("stderr") or raw)
                    yield {"message": message, "source": rel, "source_line": line_no, "timestamp": obj.get("timestamp") or obj.get("time") or ""}
            else:
                block: list[str] = []
                start = 1
                for line_no, line in enumerate(content.splitlines(), 1):
                    looks_error = any(token in line.lower() for token in ("error", "exception", "failed", "traceback", "fatal"))
                    if looks_error and block:
                        yield {"message": "\n".join(block), "source": rel, "source_line": start, "timestamp": ""}
                        block = []
                    if looks_error:
                        start = line_no; block = [line]
                    elif block and (line.startswith(" ") or line.startswith("\t") or line.startswith("at ") or line.startswith("  at ")):
                        block.append(line)
                    elif block:
                        yield {"message": "\n".join(block), "source": rel, "source_line": start, "timestamp": ""}
                        block = []
                if block: yield {"message": "\n".join(block), "source": rel, "source_line": start, "timestamp": ""}


def create_schema(db: sqlite3.Connection) -> None:
    db.executescript("""
    PRAGMA foreign_keys=OFF;
    CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE code_records(code_id TEXT PRIMARY KEY, display_id TEXT, kind TEXT, language TEXT, classification TEXT, path TEXT, line INTEGER, text TEXT);
    CREATE INDEX idx_code_path_line ON code_records(path, line);
    CREATE TABLE symbols(chid TEXT PRIMARY KEY, name TEXT, qualified_name TEXT, kind TEXT, type_name TEXT, path TEXT, line INTEGER, scope TEXT, language TEXT, declaration_code_id TEXT, signature TEXT, confidence REAL, evidence TEXT);
    CREATE INDEX idx_symbols_name ON symbols(name);
    CREATE INDEX idx_symbols_path ON symbols(path);
    CREATE TABLE symbol_aliases(chid TEXT, alias TEXT, alias_kind TEXT, PRIMARY KEY(chid, alias, alias_kind));
    CREATE INDEX idx_alias_name ON symbol_aliases(alias);
    CREATE TABLE refs(ref_id INTEGER PRIMARY KEY AUTOINCREMENT, source_code_id TEXT, source_chid TEXT, target_chid TEXT, raw_name TEXT, kind TEXT, path TEXT, line INTEGER, language TEXT, source_scope TEXT, confidence REAL, evidence TEXT);
    CREATE INDEX idx_refs_target ON refs(target_chid);
    CREATE TABLE edges(edge_id INTEGER PRIMARY KEY AUTOINCREMENT, source_id TEXT, target_id TEXT, relation TEXT, confidence REAL, evidence TEXT, path TEXT, line INTEGER);
    CREATE INDEX idx_edges_source ON edges(source_id);
    CREATE INDEX idx_edges_target ON edges(target_id);
    CREATE TABLE epistemic_nodes(node_id TEXT PRIMARY KEY, domain TEXT CHECK(domain IN ('FACT','HYPOTHESIS','FICTION','UNKNOWN')), statement TEXT, scope TEXT, provenance TEXT, confidence REAL, source_code_id TEXT);
    CREATE TABLE error_signatures(error_id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE, language TEXT, error_code TEXT, normalized_message TEXT, first_seen TEXT, last_seen TEXT, occurrence_count INTEGER DEFAULT 0, resolution_state TEXT DEFAULT 'open', resolved_at TEXT, repeat_flag INTEGER DEFAULT 0, regression_flag INTEGER DEFAULT 0);
    CREATE INDEX idx_error_language ON error_signatures(language);
    CREATE INDEX idx_error_repeat ON error_signatures(repeat_flag, regression_flag);
    CREATE TABLE error_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT, error_id TEXT, seen_at TEXT, raw_message TEXT, source_log TEXT, source_log_line INTEGER, language TEXT, code_path TEXT, code_line INTEGER, code_id TEXT, chid TEXT, FOREIGN KEY(error_id) REFERENCES error_signatures(error_id));
    CREATE INDEX idx_error_events_error ON error_events(error_id);
    CREATE INDEX idx_error_events_code ON error_events(code_id, chid);
    CREATE TABLE error_resolutions(resolution_id INTEGER PRIMARY KEY AUTOINCREMENT, error_id TEXT, resolved_at TEXT, resolution TEXT, commit_sha TEXT, code_id TEXT, chid TEXT);
    """)


def lookup_code_context(db: sqlite3.Connection, path: str, line: int) -> tuple[str | None, str | None]:
    if not path or not line: return None, None
    row = db.execute("SELECT code_id FROM code_records WHERE path=? AND line=? ORDER BY kind='code' DESC LIMIT 1", (path, line)).fetchone()
    code_id = row[0] if row else None
    symbol = db.execute("SELECT chid FROM symbols WHERE path=? AND line<=? ORDER BY line DESC LIMIT 1", (path, line)).fetchone()
    return code_id, symbol[0] if symbol else None


def ingest_errors(db: sqlite3.Connection) -> dict:
    config = read_json(ERROR_SOURCES_PATH, {})
    repeat_threshold = int(config.get("repeat_threshold", 2))
    events = repeats = regressions = 0
    for record in iter_error_source_records():
        message = record["message"].strip()
        if not message: continue
        path, code_line = error_location(message)
        language = detect_language(message, path)
        fingerprint, normalized, error_code = error_signature(message, language, path)
        error_id = "err." + fingerprint[:12]
        seen_at = str(record.get("timestamp") or utc_now())
        existing = db.execute("SELECT occurrence_count, resolution_state FROM error_signatures WHERE fingerprint=?", (fingerprint,)).fetchone()
        if existing:
            count = int(existing[0]) + 1
            was_resolved = existing[1] == "resolved"
            db.execute("UPDATE error_signatures SET last_seen=?, occurrence_count=?, repeat_flag=?, regression_flag=? WHERE fingerprint=?",
                       (seen_at, count, int(count >= repeat_threshold), int(was_resolved), fingerprint))
            repeats += int(count >= repeat_threshold); regressions += int(was_resolved)
        else:
            count = 1
            db.execute("INSERT INTO error_signatures(error_id, fingerprint, language, error_code, normalized_message, first_seen, last_seen, occurrence_count, repeat_flag, regression_flag) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0)",
                       (error_id, fingerprint, language, error_code, normalized, seen_at, seen_at, count))
        canonical = db.execute("SELECT error_id FROM error_signatures WHERE fingerprint=?", (fingerprint,)).fetchone()[0]
        code_id, chid = lookup_code_context(db, path, code_line)
        # Avoid double-counting the same persistent log record on every rebuild.
        duplicate = db.execute("SELECT 1 FROM error_events WHERE error_id=? AND source_log=? AND source_log_line=? AND raw_message=? LIMIT 1",
                               (canonical, record["source"], record["source_line"], message)).fetchone()
        if duplicate: continue
        db.execute("INSERT INTO error_events(error_id, seen_at, raw_message, source_log, source_log_line, language, code_path, code_line, code_id, chid) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (canonical, seen_at, message, record["source"], record["source_line"], language, path, code_line, code_id, chid))
        events += 1
    # Recompute occurrence counts from actual unique events so rebuilds stay deterministic.
    db.execute("UPDATE error_signatures SET occurrence_count=(SELECT COUNT(*) FROM error_events e WHERE e.error_id=error_signatures.error_id)")
    db.execute("UPDATE error_signatures SET repeat_flag=CASE WHEN occurrence_count>=? THEN 1 ELSE 0 END", (repeat_threshold,))
    return {"new_error_events": events, "repeat_observations": repeats, "regression_observations": regressions}


def build_database(rows: list[dict], symbols: list[Symbol], refs: list[Ref], registry: dict) -> dict:
    # Preserve prior error/resolution history across graph regeneration.
    old_errors: list[tuple] = []; old_events: list[tuple] = []; old_resolutions: list[tuple] = []
    if DATABASE_PATH.exists():
        try:
            old = sqlite3.connect(DATABASE_PATH)
            old_errors = old.execute("SELECT * FROM error_signatures").fetchall()
            old_events = old.execute("SELECT * FROM error_events").fetchall()
            old_resolutions = old.execute("SELECT * FROM error_resolutions").fetchall()
            old.close()
        except sqlite3.Error:
            pass
        DATABASE_PATH.unlink()
    db = sqlite3.connect(DATABASE_PATH); create_schema(db)
    db.executemany("INSERT INTO meta(key,value) VALUES (?,?)", [("schema_version","1"),("truth_domains","FACT,HYPOTHESIS,FICTION,UNKNOWN"),("built_at",utc_now())])
    db.executemany("INSERT INTO code_records(code_id,display_id,kind,language,classification,path,line,text) VALUES (?,?,?,?,?,?,?,?)",
                   [(r["id"],r["display_id"],r["kind"],r["language"],r["classification"],r["path"],int(r["line"]),r["text"]) for r in rows])
    for symbol in symbols:
        db.execute("INSERT INTO symbols(chid,name,qualified_name,kind,type_name,path,line,scope,language,declaration_code_id,signature,confidence,evidence) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (symbol.chid,symbol.name,symbol.qualified_name,symbol.kind,symbol.type_name,symbol.path,symbol.line,symbol.scope,symbol.language,symbol.declaration_code_id,symbol.signature,symbol.confidence,symbol.evidence))
        db.execute("INSERT OR IGNORE INTO symbol_aliases VALUES (?,?,?)", (symbol.chid,symbol.name,"current"))
    active = {s.chid for s in symbols}
    for entry in registry.get("entries", {}).values():
        if entry.get("chid") in active:
            for alias in entry.get("aliases", []): db.execute("INSERT OR IGNORE INTO symbol_aliases VALUES (?,?,?)", (entry["chid"],alias,"historical" if alias != entry.get("name") else "current"))
    for ref in refs:
        db.execute("INSERT INTO refs(source_code_id,source_chid,target_chid,raw_name,kind,path,line,language,source_scope,confidence,evidence) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                   (ref.source_code_id,ref.source_chid,ref.target_chid,ref.raw_name,ref.kind,ref.path,ref.line,ref.language,ref.source_scope,ref.confidence,ref.evidence))
        if ref.target_chid:
            source = ref.source_chid or (f"code.{ref.source_code_id}" if ref.source_code_id else None)
            if source: db.execute("INSERT INTO edges(source_id,target_id,relation,confidence,evidence,path,line) VALUES (?,?,?,?,?,?,?)", (source,ref.target_chid,ref.kind,ref.confidence,ref.evidence,ref.path,ref.line))
    if old_errors:
        placeholders = ",".join("?" * len(old_errors[0])); db.executemany(f"INSERT INTO error_signatures VALUES ({placeholders})", old_errors)
    if old_events:
        placeholders = ",".join("?" * len(old_events[0])); db.executemany(f"INSERT INTO error_events VALUES ({placeholders})", old_events)
    if old_resolutions:
        placeholders = ",".join("?" * len(old_resolutions[0])); db.executemany(f"INSERT INTO error_resolutions VALUES ({placeholders})", old_resolutions)
    error_stats = ingest_errors(db)
    db.commit()
    counts = {
        "symbols": db.execute("SELECT COUNT(*) FROM symbols").fetchone()[0],
        "references": db.execute("SELECT COUNT(*) FROM refs").fetchone()[0],
        "resolved_references": db.execute("SELECT COUNT(*) FROM refs WHERE target_chid IS NOT NULL").fetchone()[0],
        "edges": db.execute("SELECT COUNT(*) FROM edges").fetchone()[0],
        "error_signatures": db.execute("SELECT COUNT(*) FROM error_signatures").fetchone()[0],
        "error_events": db.execute("SELECT COUNT(*) FROM error_events").fetchone()[0],
        "repeated_errors": db.execute("SELECT COUNT(*) FROM error_signatures WHERE repeat_flag=1").fetchone()[0],
        "regressions": db.execute("SELECT COUNT(*) FROM error_signatures WHERE regression_flag=1").fetchone()[0],
        **error_stats,
    }
    db.close(); return counts


def write_graph(symbols: list[Symbol], refs: list[Ref], limit: int = 500) -> None:
    by = {s.chid:s for s in symbols}; resolved = [r for r in refs if r.source_chid and r.target_chid]
    resolved.sort(key=lambda r:(-r.confidence,r.path,r.line)); selected = resolved[:limit]
    used = {r.source_chid for r in selected} | {r.target_chid for r in selected}
    m = ["flowchart LR"]
    d = ["digraph CodeGraph {", "  rankdir=LR;"]
    for chid in sorted(used):
        symbol = by.get(chid)
        if not symbol: continue
        node = re.sub(r"[^A-Za-z0-9_]","_",chid); label = f"{chid}\\n{symbol.name}\\n{symbol.kind}".replace('"',"'")
        m.append(f'  {node}["{label}"]')
        d.append(f'  "{chid}" [label="{label}"];')
    for r in selected:
        a = re.sub(r"[^A-Za-z0-9_]","_",r.source_chid or ""); b = re.sub(r"[^A-Za-z0-9_]","_",r.target_chid or "")
        m.append(f"  {a} -->|{r.kind}| {b}")
        d.append(f'  "{r.source_chid}" -> "{r.target_chid}" [label="{r.kind}"];')
    d.append("}")
    MERMAID_PATH.write_text("\n".join(m)+"\n",encoding="utf-8"); DOT_PATH.write_text("\n".join(d)+"\n",encoding="utf-8")


def record_error(message: str, language: str = "", path: str = "", line: int = 0, source: str = "manual") -> int:
    INDEX_DIR.mkdir(exist_ok=True)
    language = language or detect_language(message,path)
    entry = {"timestamp":utc_now(),"message":message,"language":language,"path":path,"line":line,"source":source}
    with RUNTIME_ERRORS_PATH.open("a",encoding="utf-8") as handle: handle.write(json.dumps(entry,ensure_ascii=False)+"\n")
    fingerprint, normalized, code = error_signature(message,language,path)
    repeat = 0; regression = 0
    if DATABASE_PATH.exists():
        db = sqlite3.connect(DATABASE_PATH)
        row = db.execute("SELECT occurrence_count,resolution_state FROM error_signatures WHERE fingerprint=?",(fingerprint,)).fetchone()
        if row: repeat = int(row[0] >= 1); regression = int(row[1] == "resolved")
        db.close()
    status = "REGRESSION" if regression else "REPEATED" if repeat else "NEW"
    print(f"{status} ERROR {language} err.{fingerprint[:12]} {code} {normalized[:300]}")
    return 3 if regression else 2 if repeat else 0


def mark_resolved(error_id: str, resolution: str, commit_sha: str = "") -> int:
    if not DATABASE_PATH.exists(): return 1
    db = sqlite3.connect(DATABASE_PATH); now = utc_now()
    row = db.execute("SELECT error_id FROM error_signatures WHERE error_id=?",(error_id,)).fetchone()
    if not row: db.close(); return 1
    db.execute("UPDATE error_signatures SET resolution_state='resolved',resolved_at=?,regression_flag=0 WHERE error_id=?",(now,error_id))
    db.execute("INSERT INTO error_resolutions(error_id,resolved_at,resolution,commit_sha) VALUES (?,?,?,?)",(error_id,now,resolution,commit_sha))
    db.commit(); db.close(); return 0


def query_symbol(term: str) -> int:
    if not DATABASE_PATH.exists(): return 1
    db=sqlite3.connect(DATABASE_PATH); needle=f"%{term}%"
    rows=db.execute("SELECT s.chid,s.kind,s.qualified_name,s.type_name,s.path,s.line,COUNT(r.ref_id) FROM symbols s LEFT JOIN refs r ON r.target_chid=s.chid WHERE s.name LIKE ? OR s.qualified_name LIKE ? OR s.chid LIKE ? GROUP BY s.chid ORDER BY COUNT(r.ref_id) DESC,s.path,s.line LIMIT 100",(needle,needle,needle)).fetchall(); db.close()
    for r in rows: print("\t".join(map(str,r)))
    return 0 if rows else 1


def query_error(term: str) -> int:
    if not DATABASE_PATH.exists(): return 1
    db=sqlite3.connect(DATABASE_PATH); needle=f"%{term}%"
    rows=db.execute("SELECT error_id,language,error_code,occurrence_count,repeat_flag,regression_flag,resolution_state,normalized_message FROM error_signatures WHERE error_id LIKE ? OR normalized_message LIKE ? OR error_code LIKE ? ORDER BY regression_flag DESC,repeat_flag DESC,occurrence_count DESC LIMIT 100",(needle,needle,needle)).fetchall(); db.close()
    for r in rows: print("\t".join(map(str,r)))
    return 0 if rows else 1


def build() -> int:
    rows=load_index(); symbols,refs=extract(rows); registry=assign_chids(symbols); resolve(symbols,refs)
    counts=build_database(rows,symbols,refs,registry); write_graph(symbols,refs)
    summary={"schema_version":1,"database":DATABASE_PATH.relative_to(ROOT).as_posix(),"mermaid":MERMAID_PATH.relative_to(ROOT).as_posix(),"dot":DOT_PATH.relative_to(ROOT).as_posix(),**counts}
    SUMMARY_PATH.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(summary,indent=2,sort_keys=True)); return 0


def main() -> int:
    p=argparse.ArgumentParser(description="Shaelvien semantic code database")
    sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("build")
    q=sub.add_parser("find-symbol"); q.add_argument("term")
    e=sub.add_parser("find-error"); e.add_argument("term")
    r=sub.add_parser("record-error"); r.add_argument("message"); r.add_argument("--language",default=""); r.add_argument("--path",default=""); r.add_argument("--line",type=int,default=0); r.add_argument("--source",default="manual")
    x=sub.add_parser("resolve-error"); x.add_argument("error_id"); x.add_argument("resolution"); x.add_argument("--commit",default="")
    args=p.parse_args()
    if args.cmd=="build": return build()
    if args.cmd=="find-symbol": return query_symbol(args.term)
    if args.cmd=="find-error": return query_error(args.term)
    if args.cmd=="record-error": return record_error(args.message,args.language,args.path,args.line,args.source)
    if args.cmd=="resolve-error": return mark_resolved(args.error_id,args.resolution,args.commit)
    return 2


if __name__=="__main__": raise SystemExit(main())
