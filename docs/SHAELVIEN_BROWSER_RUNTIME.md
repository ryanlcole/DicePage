# Shaelvien Browser Runtime

Status: **Foundational architecture; compatibility migration active.**

This document locks the browser-side execution boundary that follows the canonical Shaelvien semantic language contract. It does not replace `.code-index/humans_language.json`, `docs/SHAELVIEN_SEMANTIC_LANGUAGE.md`, `apps/rist-world/SHAEP_FORMAT.md`, or `apps/rist-world/AUTHORITY_SYSTEM.md`. Those sources remain authoritative for semantic identity, SHAEP, and Recursive Authority.

## Locked architecture

The trusted system stores and resolves truth. The browser receives only an authorized perception of that truth and returns user input as feedback or semantic intent requests.

```text
AUTHENTICATED / EFFECTIVE IDENTITY
             +
AUTHORITATIVE WORLD / RESOURCE / SHAEP
             +
ACTIVE CONTAINMENT + CONTEXT + INTENT
             |
             v
     CCTV + Recursive Authority
             |
             v
  authorized Rune / Glyph result
             |
             v
      semantic envelope
             |
             v
  BROWSER PERCEPTION RUNTIME
      |       |       |
     DOM    PIXELS  AUDIO/VIDEO
      |       |       |
      +-------+-------+
              |
              v
             USER
              |
   pointer / touch / key / voice / controller
              |
              v
 representation feedback -> declared Rune/Glyph intent request
              |
              v
      trusted validation / authority
              |
              v
      authoritative truth change
```

### Invariants

1. **Identity is not output equivalence.** CHID/SHAEP identity does not come from a DOM id, filename, text label, coordinate, opcode, pixel, or wire spelling.
2. **Representation is not truth.** Pixels, audio samples, video frames, layout, animation, localization, and accessibility presentations are viewer output.
3. **The server/trusted runtime stores truth; the client produces authorized perception.** Hidden facts are filtered before perception is emitted. A browser must not receive a secret merely because CSS or UI later hides it.
4. **Runes and Glyphs are semantic operations, not browser-event names.** The browser runtime only emits a Rune/Glyph intent when application code explicitly declares one. Unannotated legacy DOM interaction remains representation feedback.
5. **A client intent is a request, not authority.** Authentication, schema validation, context resolution, capability checks, Recursive Authority, provenance, anti-replay, resource budgets, and audit remain trusted-side concerns.
6. **No arbitrary source execution.** The browser may execute only registered presentation handlers. No `eval`, generated functions, or semantic packet that silently becomes source code.
7. **Accessibility and localization may change representation without changing identity.** No essential action should depend on one pixel position, language spelling, color, sense, or input method.

## Sitewide semantic membrane

`wwwroot/shaelvien-semantic-runtime.js` is loaded before the existing application scripts. It provides a shared semantic envelope, target resolution, diagnostics, declared-intent dispatch, a registered perception-operation table, and an optional transport boundary.

Existing Blazor/JavaScript remains operational during migration. The membrane observes it without canceling events. This is intentional: runtime executable behavior remains truth until each legacy behavior is deliberately migrated and verified.

Elements may opt into semantic resolution with explicit declarations:

```html
<button data-chid="..." data-rune="...">...</button>
<div data-shaep="..." data-glyph="..."></div>
```

`data-semantic-id` is available for a semantic identity that is neither asserted to be a CHID nor a SHAEP. The runtime never infers CHID/SHAEP from DOM ids, text, CSS classes, paths, or screen coordinates.

## Pixel perception

`wwwroot/shaelvien-perception-runtime.js` treats a canvas as a bounded perception surface. The first implementation supports full RGBA frames and rectangular RGBA deltas.

For a `1024 x 2048` RGBA8 surface:

```text
2,097,152 pixels x 4 bytes = 8,388,608 bytes of raw perception
```

That is a representation cost, not a requirement to retransmit every pixel every frame. Future transports may select among:

- full encoded frames,
- changed rectangles/tiles,
- video/audio codecs,
- waveform/sample streams,
- semantic Rune/Glyph deltas rendered locally,
- or hybrids chosen by device capability and context.

A powerful client can produce more perception locally. A weak client can receive more fully rendered perception. The authoritative world meaning remains the same.

Pixels never become persistent object identity. A screen point resolves through the current representation to an explicitly bound CHID/SHAEP/semantic target when one exists.

## Input feedback

`wwwroot/shaelvien-input-runtime.js` observes selected browser input in capture phase without `preventDefault` or `stopPropagation`. This lets the existing site continue working while a semantic layer is introduced underneath it.

Two paths are deliberately distinct:

```text
unannotated UI -> representation-only `shaelvien:input`
explicit data-rune/data-glyph -> `shaelvien:input` + request-only `shaelvien:intent`
```

This prevents old DOM ids, labels, or pixel positions from accidentally becoming canonical language.

Sensitive browser fields must not expose their values through the feedback layer. Server-side code must still treat all client messages as untrusted.

## Wire representation

`wwwroot/shaelvien-wire.js` begins with versioned UTF-8 JSON control envelopes:

```text
shaelvien.semantic-envelope/1
```

This is deliberate. The current semantic contract explicitly does **not** freeze example compact packets or numeric opcodes into a universal grammar. JSON is therefore a transparent migration representation while the semantics stabilize.

Large image/audio/video payloads should travel in binary/media channels and be referenced or paired with semantic control envelopes rather than copied into JSON.

A later compact binary representation may map frequently used semantics to session- or schema-scoped integers/varints, but the wire code must remain a representation of stable semantic identity, never become that identity itself. Numeric truthiness is not implied.

## Runtime-local operation namespace

Browser presentation handlers use `runtime-perception` operations. Current pixel handlers are:

- `runtime.perception.pixel.rgba.frame`
- `runtime.perception.pixel.rgba.rect`

These are runtime-local presentation handler names, **not declarations that new canonical Rune CHIDs have been assigned**. Canonical Rune/Glyph identity must continue through the repository semantic-governance process.

## Evolution path

The migration direction is:

```text
NOW
Blazor + legacy JavaScript
        |
sitewide semantic membrane (observes, preserves behavior)
        |
explicit semantic bindings added to verified surfaces
        |
trusted services emit authorized perception envelopes
        |
legacy executors progressively become compatibility adapters
        |
Rune/Glyph-native site with multiple interchangeable renderers/transports
```

The target is not a browser that knows every implementation language. The target is a browser that understands a small, versioned semantic/perception boundary. C#, JavaScript, WebAssembly, native engines, render farms, or future runtimes may implement either side without redefining the world.

## Promotion gates

A semantic path should not replace its existing site behavior until all of the following are true:

1. canonical identity/operation is defined or explicitly marked runtime-local;
2. authoritative filtering occurs trusted-side;
3. inputs remain request-only until validated and authorized;
4. old and new paths have behavioral regression coverage;
5. accessibility and alternate-input behavior is preserved;
6. provenance is preserved across generated/modified content;
7. resource bounds and malformed-packet rejection are tested;
8. deployment verifies the exact branch head intended for release.

Until then, the membrane is additive and compatibility-first.
