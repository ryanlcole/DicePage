# Shaelvien Adaptive Perception

Status: **EXPERIMENTAL / NONCANONICAL MIGRATION ARCHITECTURE**

This document describes the first adaptive presentation layer built on the Shaelvien semantic membrane. It does not freeze Rune/Glyph grammar, wire opcodes, CCTV terminology, or a canonical representation compiler.

## Purpose

A single authorized truth may have several presentation-equivalent representations. A capable client may render semantic/local state, while another client may receive pixel deltas or encoded media. The representation can change without changing the underlying CHID/SHAEP identity or authoritative world state.

The intended direction is:

```text
authoritative truth
  -> Recursive Authority / content / safety / provenance / CCTV checks
  -> authorized perception result
  -> trusted representation offer
  -> coarse client capability negotiation
  -> selected representation
  -> browser perception
```

The reverse path remains separate:

```text
user signal
  -> current representation hit/semantic resolver
  -> Rune/Glyph intent request
  -> authentication + schema + authority checks
  -> authoritative truth transition
```

Presentation optimization never runs in the reverse path.

## Representation modes

The migration runtime recognizes four descriptive modes. These are runtime-local presentation categories, not canonical Rune/Glyph ids or frozen wire opcodes.

- `semantic` — registered semantic presentation/state operations.
- `local-render` — trusted authorized state rendered locally by browser/runtime facilities.
- `pixel-delta` — bounded pixel-region updates, using the existing registered perception surface operations.
- `encoded-media` — an authorized encoded audio/video/media presentation path. The current control wire does not embed large media payloads.

A producer must never offer a representation that contains facts the viewer is not authorized to know. Choosing a different representation is not a security boundary.

## Capability negotiation

`shaelvien-client-perception.js` exposes a deliberately coarse local capability profile. It avoids exact screen geometry, user-agent strings, CPU counts, device-memory values, GPU identity, measured bandwidth, and similar high-entropy fingerprint data.

Capability is not authority. The browser may select only from modes that trusted application code already determined are authorized and presentation-equivalent for that viewer.

The capability profile is local by default and is not automatically sent through the semantic transport.

## Adaptive scheduling

`shaelvien-adaptive-perception.js` provides an opt-in scheduler around existing registered perception envelopes.

Each presentation stream has its own monotonically increasing sequence. Sequence is a presentation-stream ordering value only; it is not a world revision, transaction id, permission version, or proof of authority.

A queued entry can be either:

- **supersedable** — obsolete pending presentation may be discarded when a newer presentation for the same stream arrives; or
- **ordered** — remains an ordering barrier and cannot be jumped by later supersedable entries.

Example: camera frames or rapidly changing visual previews may be supersedable. A deliberately ordered presentation transition can be non-supersedable.

The scheduler accepts only envelopes that already validate as:

```text
kind = perception
operation.type = runtime-perception
```

Input, intent, user action, authority decisions, persistence operations, payments, legal agreements, moderation decisions, and world-state mutations are outside this scheduler and must never be dropped or coalesced by it.

## Backpressure law

The system may forget perception that has already become obsolete; it may not forget truth or intent merely because a newer presentation exists.

In compact form:

```text
obsolete perception -> MAY SUPERSEDE
ordered perception  -> PRESERVE ORDER
user intent/action  -> NEVER ENTER PERCEPTION QUEUE
authoritative truth -> NEVER DERIVED FROM QUEUE LOSS
```

This is the architectural distinction that allows high-frequency visual/audio presentation to evolve independently from reliable world transitions.

## Existing behavior remains authoritative

The adaptive scheduler does not intercept `runtime.receive()` automatically. Existing pages continue to execute through their established runtime. A surface opts into adaptive scheduling only when it has been migrated and its producer can supply a valid presentation stream id, monotonic sequence, and explicit supersedability decision.

This preserves working behavior while migration proceeds incrementally.

## First migrated surface: Worldbuilder auto camera

The first production-facing migration is deliberately narrow.

`shaelvien-worldbuilder-perception-bridge.js` owns the runtime-local presentation stream `worldbuilder.camera`. It can build a registered Worldbuilder camera perception envelope and enqueue it through `Shaelvien.AdaptivePerception` with a local monotonically increasing presentation sequence.

`worldbuilder-camera-window.js` uses that adaptive stream only for automatic camera-window recalculation such as responsive resize/orientation/layout updates while the viewer is in automatic camera mode. These updates are marked supersedable because only the newest pending automatic camera perception matters.

The following remain deliberately outside that adaptive path during this phase:

- manual zoom/control calls;
- viewer grid enable/disable;
- camera navigation lock;
- asset placement or removal;
- coordinates that define world truth;
- save/load/publish operations;
- permissions, content gates, legal agreements, payments, moderation, or account actions.

If the adaptive camera queue is unavailable or rejects execution, the camera-window falls back to the previous direct `ristViewerAuthority` automatic-zoom path. Manual camera state continues to use the existing synchronous viewer authority path.

This is the migration pattern for later surfaces: first identify presentation-only state, preserve the old implementation as a fallback, add one semantic/adaptive boundary, and promote further only after runtime and governance checks remain healthy.

## Second migrated surface: transient quick-slot placement preview

The second migration applies the same law to the high-frequency drag ghost and loupe shown while a quick-slot asset is being dragged across the Worldbuilder.

`shaelvien-worldbuilder-perception-bridge.js` owns the runtime-local stream `worldbuilder.placement-preview` and the registered operation `runtime.perception.worldbuilder.placement-preview.pointer`. The envelope contains only a bounded local preview-session id plus finite screen-space pointer coordinates. It is explicitly marked transient, perception-only, and non-authoritative.

`worldbuilder-drag-preview.js` keeps creation and destruction of the preview local, then routes subsequent quick-slot pointer-move presentation through the adaptive stream. These pointer frames are supersedable: if several are waiting, an obsolete ghost position may be dropped in favor of the newest pending position.

Each drag receives a local preview-session id. The visual presenter applies an adaptive frame only when that session is still the active drag. Pointer-up, cancellation, page reset, prompt transition, or preview clearing invalidates the active session. A delayed frame from an earlier drag therefore becomes a harmless no-op instead of resurrecting a cleared preview or attaching itself to a later drag.

The actual placement commit is deliberately outside the adaptive queue. The existing `ristPlacement.set(...)` treatment handoff and trusted pointer-up redispatch remain the reliable placement path. Overlap choices such as blend, trim, layer, and tier are likewise kept outside the adaptive preview stream. The placed-tile mover also remains synchronous during this phase.

If the adaptive preview runtime is unavailable or rejects the newest active preview request, the script falls back to the previous direct `updatePreview(...)` rendering path. Older failed requests are not allowed to move the ghost backward after a newer request has been issued.

The boundary is therefore:

```text
pointer-move ghost/loupe position -> MAY SUPERSEDE
preview session after finish       -> INVALID / NO-OP
placement treatment choice         -> RELIABLE
pointer-up placement commit        -> RELIABLE
persisted world coordinates        -> AUTHORITATIVE PATH ONLY
```

## Safety and compliance

`docs/SHAELVIEN_COMPLIANCE_PRECEDENCE.md` remains higher authority than this experimental layer.

No representation, codec, renderer, client capability, optimization, or queue behavior may weaken:

- law or verified lawful process;
- human consent or contractual/legal agreement requirements;
- privacy and data-minimization requirements;
- age/guardian/content gates;
- accessibility requirements;
- player ownership and authorization boundaries;
- AI provenance and AI-zone restrictions;
- Recursive Authority;
- safety/reporting/removal obligations; or
- audit requirements for protected actions.

Unknown or ambiguous authority remains DENY. Where a migration conflicts with existing lawful behavior, preserve the existing behavior and resolve the conflict before promotion.

## Future direction

A later version may formalize a trusted perception/representation compiler that chooses among equivalent render paths according to authorization, accessibility needs, client support, resource budgets, latency, and bandwidth.

That compiler is not canonical yet. It must not be promoted until its schemas, authority boundary, provenance behavior, tests, compatibility rules, and failure semantics are explicitly defined.
