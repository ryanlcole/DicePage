# Shaelvien/RIST Agent Entry Point

This repository contains an experimental semantic programming and transport language used by Shaelvien/RIST. Coding agents, including ChatGPT/Codex sessions, must discover its semantics from repository truth rather than reconstructing them from conversational memory.

## Compliance discovery — read first

Before changing runtime behavior, authority, AI/EI behavior, user data handling, perception, input, deployment, monetization, accessibility, or any semantic execution path, read:

1. `docs/SHAELVIEN_COMPLIANCE_PRECEDENCE.md` — foundational engineering constraint for law, human/AI policy, safety, consent, privacy, accessibility, ownership, lawful process, and non-bypass behavior.
2. `apps/rist-world/AUTHORITY_SYSTEM.md` — foundational Recursive Authority & Supervision contract.
3. `apps/rist-world/wwwroot/ai-policy.json` — deployed AI-access policy.
4. The deployed legal/safety surfaces under `apps/rist-world/wwwroot/`, including `terms.html`, `privacy.html`, `safety.html`, `dmca.html`, and `accessibility.html`.

If a requirement is unknown, ambiguous, conflicting, stale, jurisdiction-dependent, or not yet implemented safely, fail closed or preserve the prior lawful behavior and escalate for qualified human/legal review. Semantic efficiency never outranks lawful human requirements, consent, privacy, safety, accessibility, ownership, or established Shaelvien/RIST policy.

## Language discovery

Before generating, translating, refactoring, decoding, or inventing compact Shaelvien semantic code, read:

1. `.code-index/humans_language.json` — canonical machine-readable language contract.
2. `docs/SHAELVIEN_SEMANTIC_LANGUAGE.md` — architecture reference for Rune/Glyph/SHAEP/CHID/CCTV, permissions, perception, compact streams, and pixel/property binding.
3. `apps/rist-world/wwwroot/.well-known/shaelvien-language.json` — deployed discovery/compatibility manifest.
4. `docs/HUMANS_LANGUAGE.md` — human-readable epistemic/control-flow surface.
5. `docs/CODE_DATABASE_ARCHITECTURE.md` — CHID identity and relationship database.
6. `.code-index/semantic_units.json` — registered Rune/Glyph/SHAEP forms and equivalence conditions.
7. `apps/rist-world/SHAEP_FORMAT.md` — current SHAEP v2 contract.
8. `apps/rist-world/AUTHORITY_SYSTEM.md` — foundational Recursive Authority & Supervision contract.
9. `docs/ERROR_GRAPH.md` — recurring error/regression semantics.

Repository discovery pointer: `SHAELVIEN_LANGUAGE.md`.

The deployed hidden reference page is `/Game/_shaelvien-language.html`. It is intentionally absent from normal navigation and search indexing. The machine discovery endpoint is `/Game/.well-known/shaelvien-language.json`.

The canonical machine contract and deployed manifest share a language version. The manifest also records the canonical contract SHA-256; governance CI must fail if they drift.

A fresh ChatGPT conversation does not automatically know this language merely because these files exist. A repo-aware/connected coding session should read this file and the canonical references above before making semantic-language changes.

## Non-negotiable semantic rules

- Identity is not output equivalence.
- Representation is not truth.
- The server stores authoritative truth; the viewer/client produces authorized perception.
- CHID is stable semantic code identity; spelling, file path, line number, language, and UI representation may change without changing identity.
- Rune is atomic semantic intent/operation.
- Glyph is contextual or compound meaning composed from Runes and/or other Glyphs.
- SHAEP means Spatial Hot Preservation Object; current canonical format is SHAEP v2 as defined by `apps/rist-world/SHAEP_FORMAT.md`.
- CCTV names the trusted context translation/verification boundary under development. Its long-form expansion is not canon; do not invent one.
- FACT, HYPOTHESIS, FICTION, and UNKNOWN are separate truth domains. Never silently promote one into another.
- `Whatif` enters hypothesis space. `Maybe` means unresolved/unknown, not random chance. `Because` attaches rationale/provenance and does not prove causation.
- The semantic layer uses typed booleans. Do not assume numeric `0`, `1`, or `-1` universally means TRUE or FALSE; only an explicit target/wire schema may define such a mapping.
- Compact forms such as `i3r20` and perception packets such as `H52|C1|X23|Y42|Z74|T1|L9|I` are examples, not frozen grammar, until the canonical contract explicitly marks a versioned grammar canonical.
- Search and reuse existing CHIDs/semantic units before creating a duplicate concept.
- Text equality does not prove semantic equality. Record relation type and conditions.

## Context, permissions, and perception

Recursive Authority remains authoritative for permissions. Credentials prove authentication; permissions determine allowed behavior.

The intended semantic authority flow is:

```text
authenticated/effective identity
  + protected resource/SHAEP
  + active containment path
  + intent/context
        -> CCTV
        -> contextual capability Glyph
        -> allowlisted Rune/result stream
```

CCTV must expose capability without exposing the credential that created it. Ambiguous permission paths deny rather than guess.

For map/world perception, keep hidden facts on the trusted side. Resolve identity, character, location/tier/layer, SHAEP/world object, authority, character metadata, and any authoritative perception roll/check before emitting only the revealed Rune/value result. Never ship a hidden trap/DC/GM note to the browser just because CSS or UI code intends to hide it.

## Pixels and UI identity

Pixels are representation, not persistent identity.

Resolve interactive screen positions through:

```text
pixel/screen position
  -> current representation node/hit target
  -> CHID or semantic UI identity
  -> permitted Rune/Glyph action
```

Responsive layout, localization, zoom, accessibility, and alternate input may move or replace the pixels while preserving semantic identity. No essential action should require one sense or one input mechanism alone.

## Execution and security

The server holds authoritative truth; the browser/client produces perception. Client instructions are requests until authenticated, schema-validated, authority-validated, and accepted by the server.

Do not use `eval`, dynamic arbitrary source execution, or obscurity as security. Use registered Rune/Glyph handlers, typed operands, stable CHID/SHAEP resolution, version/schema checks, Recursive Authority/capabilities, provenance, resource budgets, anti-replay controls where needed, and audit trails.

The language may be public; authority determines what it is allowed to do.

## Change discipline

Executable repository behavior remains runtime truth until the semantic compiler/runtime is explicitly promoted to authoritative execution. If the contract/manifest/reference and working implementation disagree, preserve working behavior, identify the mismatch, and reconcile the semantic layer rather than silently changing behavior.

Version semantic-breaking changes. Never silently reuse a stable semantic ID/opcode for a different meaning.

Never push project work to `main`; the active project branch is `live-alpha-rist-blazor-world` unless the user explicitly changes that policy.

## Project knowledge discovery

For source-linked project context, read `docs/PROJECT_KNOWLEDGE.md` and query
`knowledge/project/public.json` or the code database's `project_*` tables. Preserve
source status, dates, scope, visibility, truth domain, and provenance. The corpus
is evidence, not permission, live-deployment verification, or automatic canon
promotion. Explicit source conflicts remain unresolved until the appropriate
authority reconciles them. Private project exports must not be committed to this
public repository.
