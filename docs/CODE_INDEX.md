# Shaelvien Code Index

The code index is the repository's searchable code ledger. It gives executable code and source comments persistent numeric identities, records where each item currently lives, separates first-party source from vendor/generated/stale material, and maintains evidence for cleanup.

## Identity model

The canonical identity is the six-digit number. A current human-readable locator is rendered around it:

```text
000009.csharp.CharacterSelection.line8.code
000010.html.Home.line54.comment
```

The numeric portion is the identity. `language`, file/scope, line, and kind are navigation metadata. This matters because inserting a line must not renumber the rest of the system.

Every nonblank indexed code line receives a `code` record. Every detected source comment receives a `comment` record. Records are written to `.code-index/code_index.jsonl` and `.code-index/code_index.tsv`.

Parser-safe source materialization is intentionally stricter than indexing. Python comments are parsed with Python's tokenizer and safe full-line comments are rewritten with their display ID. Other languages still receive comment IDs in the index, but the indexer does not blindly rewrite them until a parser can prove that the apparent comment is not inside a raw string, template, heredoc, documentation construct, or other semantic text.

Example source:

```python
count = 3
# 000009.python.character_selection.line8.comment count controls the character-selection loop
```

The code line itself is separately present in the index with its own code ID, so the repository does not need a second explanatory comment after every executable line.

## Files

- `.code-index/code_index.jsonl` — canonical machine-searchable current record log.
- `.code-index/code_index.tsv` — grep/editor-friendly current index.
- `.code-index/id_registry.json` — persistent allocation registry, including retired IDs.
- `.code-index/summary.json` — counts and health summary.
- `.code-index/duplicates.json` — exact duplicate file groups.
- `.code-index/duplicate_baseline.json` — duplicate debt that existed when the system was introduced. New exact first-party duplicates fail verification.
- `.code-index/stale_candidates.json` — generated/compiled material still present for review.
- `.code-index/cleanup_log.jsonl` — immutable-style evidence ledger for files removed from the active tree, including their former path, size, and SHA-256.
- `.code-index/config.json` — classification and enforcement policy.

Git history plus the pre-index backup branch preserves removed material. Cleanup means removal from the authoritative active tree, not erasure of history.

## Commands

```bash
python tools/code_index.py build
python tools/code_index.py find WorldBuilder
python tools/code_index.py find-id 000009
python tools/code_index.py duplicates
python tools/code_index.py stale
python tools/code_index.py verify
```

`find` searches IDs, language, classification, path, and source text together. `find-id` resolves either the six-digit canonical ID or a full display locator.

## Classification

The index classifies repository files before duplicate/stale analysis:

- `source` — first-party code/config under active authority.
- `vendor` — copied dependency trees; searchable, but not treated as Shaelvien-authored code.
- `generated` — compiled/build products and generated output.
- `stale` — explicit legacy names such as `.old`, `.bak`, cache trees, and other configured stale patterns.
- `docs`, `config`, `asset` — non-executable project material.

This prevents a copied Python package, a binary, an old backup, and an authoritative Worldbuilder source file from appearing equally valid merely because all are tracked by Git.

## Duplicate policy

Exact source duplicates are grouped by SHA-256 and language. Duplicate groups present on the first governed build are recorded as baseline debt so adoption does not deadlock the branch. Any new exact first-party duplicate group fails `verify`.

Similarity and semantic duplication are review problems rather than automatic deletion problems. The index exposes exact evidence first; consolidation should then choose a single authority and remove callers of stale implementations before deleting the duplicate.

## Stale-code policy

Paths explicitly marked stale by naming convention are removed from the active branch during governed builds. Before removal the indexer records path, byte length, SHA-256, reason, and removal status in `cleanup_log.jsonl`. Generated and vendor material is reported but not automatically deleted merely because it looks unnecessary.

This follows the project rule that changes must leave a trace: the active tree becomes cleaner while Git history, the backup branch, the ID registry, and cleanup ledger retain provenance.

## CI behavior

The `Code Index Governance` workflow rebuilds the index on the authoritative development branch and on pull requests. On the development branch it can commit safe comment-ID materialization, stale-path cleanup, and refreshed index artifacts. Pull requests run verification without silently choosing between semantically different implementations.

The index is therefore both a navigation tool and a regression firewall: stale backup naming cannot quietly return, IDs cannot collide, and new exact first-party duplicate files cannot be introduced unnoticed.
