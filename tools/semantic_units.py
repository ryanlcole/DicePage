#!/usr/bin/env python3
"""Load Rune/Glyph/SHAEP semantic units into the Shaelvien code graph database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / ".code-index" / "code_graph.sqlite3"
REGISTRY_PATH = ROOT / ".code-index" / "semantic_units.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS semantic_units(
    unit_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK(kind IN ('RUNE','GLYPH','SHAEP')),
    name TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS semantic_forms(
    form_id TEXT PRIMARY KEY,
    language TEXT NOT NULL,
    surface TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    conditions TEXT,
    FOREIGN KEY(unit_id) REFERENCES semantic_units(unit_id)
);
CREATE INDEX IF NOT EXISTS idx_semantic_forms_surface ON semantic_forms(surface);
CREATE INDEX IF NOT EXISTS idx_semantic_forms_unit ON semantic_forms(unit_id);

CREATE TABLE IF NOT EXISTS semantic_relations(
    relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    left_id TEXT NOT NULL,
    right_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    symmetric INTEGER NOT NULL DEFAULT 0,
    conditions TEXT,
    truth_status TEXT NOT NULL CHECK(truth_status IN ('FACT','HYPOTHESIS','FICTION','UNKNOWN')),
    UNIQUE(left_id, right_id, relation, conditions)
);
CREATE INDEX IF NOT EXISTS idx_semantic_relations_left ON semantic_relations(left_id);
CREATE INDEX IF NOT EXISTS idx_semantic_relations_right ON semantic_relations(right_id);

CREATE TABLE IF NOT EXISTS code_semantic_bindings(
    binding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_id TEXT,
    chid TEXT,
    form_id TEXT,
    unit_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    evidence TEXT,
    UNIQUE(code_id, chid, form_id, unit_id, relation)
);
CREATE INDEX IF NOT EXISTS idx_code_semantic_code ON code_semantic_bindings(code_id);
CREATE INDEX IF NOT EXISTS idx_code_semantic_chid ON code_semantic_bindings(chid);
CREATE INDEX IF NOT EXISTS idx_code_semantic_unit ON code_semantic_bindings(unit_id);
"""


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def install() -> int:
    if not DB_PATH.exists():
        print("Missing code_graph.sqlite3; run tools/code_database.py build first", file=sys.stderr)
        return 2

    data = load_registry()
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)

    for unit in data.get("units", []):
        db.execute(
            """INSERT INTO semantic_units(unit_id, kind, name, description)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(unit_id) DO UPDATE SET
                 kind=excluded.kind,
                 name=excluded.name,
                 description=excluded.description""",
            (unit["unit_id"], unit["kind"], unit["name"], unit.get("description", "")),
        )

    for form in data.get("forms", []):
        db.execute(
            """INSERT INTO semantic_forms(form_id, language, surface, unit_id, relation, conditions)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(form_id) DO UPDATE SET
                 language=excluded.language,
                 surface=excluded.surface,
                 unit_id=excluded.unit_id,
                 relation=excluded.relation,
                 conditions=excluded.conditions""",
            (
                form["form_id"], form["language"], form["surface"], form["unit_id"],
                form["relation"], form.get("conditions", ""),
            ),
        )

    for relation in data.get("relations", []):
        db.execute(
            """INSERT OR REPLACE INTO semantic_relations(
                 left_id, right_id, relation, symmetric, conditions, truth_status
               ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                relation["left"], relation["right"], relation["relation"],
                int(bool(relation.get("symmetric"))), relation.get("conditions", ""),
                relation.get("truth_status", "UNKNOWN"),
            ),
        )

    db.commit()
    counts = {
        "semantic_units": db.execute("SELECT COUNT(*) FROM semantic_units").fetchone()[0],
        "semantic_forms": db.execute("SELECT COUNT(*) FROM semantic_forms").fetchone()[0],
        "semantic_relations": db.execute("SELECT COUNT(*) FROM semantic_relations").fetchone()[0],
        "code_semantic_bindings": db.execute("SELECT COUNT(*) FROM code_semantic_bindings").fetchone()[0],
    }
    db.close()
    print(json.dumps(counts, indent=2, sort_keys=True))
    return 0


def search(term: str) -> int:
    if not DB_PATH.exists():
        return 2
    db = sqlite3.connect(DB_PATH)
    needle = f"%{term}%"
    rows = db.execute(
        """SELECT f.form_id, f.language, f.surface, u.unit_id, u.kind, u.name,
                  f.relation, f.conditions
           FROM semantic_forms f
           JOIN semantic_units u ON u.unit_id = f.unit_id
           WHERE f.surface LIKE ? OR f.language LIKE ? OR u.name LIKE ? OR u.unit_id LIKE ?
           ORDER BY u.kind, u.unit_id, f.language, f.surface""",
        (needle, needle, needle, needle),
    ).fetchall()
    db.close()
    for row in rows:
        print("\t".join(str(x) for x in row))
    return 0 if rows else 1


def relate(left: str, right: str) -> int:
    if not DB_PATH.exists():
        return 2
    db = sqlite3.connect(DB_PATH)
    rows = db.execute(
        """SELECT left_id, right_id, relation, symmetric, conditions, truth_status
           FROM semantic_relations
           WHERE (left_id=? AND right_id=?) OR (symmetric=1 AND left_id=? AND right_id=?)""",
        (left, right, right, left),
    ).fetchall()
    db.close()
    for row in rows:
        print("\t".join(str(x) for x in row))
    return 0 if rows else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Shaelvien Rune/Glyph/SHAEP semantic registry")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("install")
    find = sub.add_parser("find")
    find.add_argument("term")
    rel = sub.add_parser("relate")
    rel.add_argument("left")
    rel.add_argument("right")
    args = parser.parse_args()

    if args.cmd == "install":
        return install()
    if args.cmd == "find":
        return search(args.term)
    if args.cmd == "relate":
        return relate(args.left, args.right)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
