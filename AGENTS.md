# Shaelvien/RIST Agent Entry Point

This repository contains an experimental semantic programming language used by Shaelvien/RIST. Coding agents, including ChatGPT/Codex sessions, must discover its semantics from repository truth rather than from conversational memory.

## Language discovery

Before generating, translating, refactoring, decoding, or inventing compact Shaelvien semantic code, read:

1. `.code-index/humans_language.json` — canonical machine-readable language contract.
2. `apps/rist-world/wwwroot/.well-known/shaelvien-language.json` — deployed discovery/compatibility manifest.
3. `docs/HUMANS_LANGUAGE.md` — human-readable epistemic/control-flow surface.
4. `docs/CODE_DATABASE_ARCHITECTURE.md` — CHID identity and relationship database.
5. `.code-index/semantic_units.json` — registered Rune/Glyph/SHAEP forms and equivalence conditions.
6. `docs/ERROR_GRAPH.md` — recurring error/regression semantics.

The deployed hidden reference page is `/_shaelvien-language.html`. It is intentionally absent from normal navigation and search indexing. The machine discovery endpoint is `/.well-known/shaelvien-language.json`.

The canonical contract and deployed manifest share a language version. The manifest also records the canonical contract SHA-256; governance CI must fail if they drift.

## Non-negotiable semantic rules

- Identity is not output equivalence.
- Representation is not truth.
- CHID is stable semantic code identity; spelling, file path, line number, language, and UI representation may change without changing identity.
- Rune is atomic semantic intent/operation.
- Glyph is compound behavior composed from Runes and/or other Glyphs.
- SHAEP preserves identity across payload/representation changes.
- FACT, HYPOTHESIS, FICTION, and UNKNOWN are separate truth domains. Never silently promote one into another.
- `Whatif` enters hypothesis space. `Maybe` means unresolved/unknown, not random chance. `Because` attaches rationale/provenance and does not prove causation.
- Compact forms such as `i3r20` are examples, not a frozen grammar, until the canonical contract explicitly marks a versioned grammar canonical.
- Search and reuse existing CHIDs/semantic units before creating a duplicate concept.
- Text equality does not prove semantic equality. Record relation type and conditions.

## Execution and security

The server holds authoritative truth; the browser/client produces perception. Client instructions are requests until authenticated, schema-validated, authority-validated, and accepted by the server.

Do not use `eval`, dynamic arbitrary source execution, or obscurity as security. Use registered Rune/Glyph handlers, typed operands, stable CHID/SHAEP resolution, version/schema checks, Recursive Authority/capabilities, provenance, resource budgets, and audit trails.

The language may be public; authority determines what it is allowed to do.

## Change discipline

Executable repository behavior remains runtime truth until the semantic compiler/runtime is explicitly promoted to authoritative execution. If the contract/manifest and working implementation disagree, preserve working behavior, identify the mismatch, and reconcile the semantic layer rather than silently changing behavior.

Never push project work to `main`; the active project branch is `live-alpha-rist-blazor-world` unless the user explicitly changes that policy.
