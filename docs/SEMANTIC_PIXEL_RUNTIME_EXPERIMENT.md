# Semantic Tile/Pixel Runtime Experiment

Status: `HYPOTHESIS / EXPERIMENTAL / NON-AUTHORITATIVE`

Branch: `experiment/semantic-pixel-runtime`

Base truth: `6ab8cd859abc545e2df51d797df071843da428f3`

## Purpose

Test the smallest useful runtime claim from the Shaelvien semantic-language reference without changing authoritative World Builder behavior:

> A rendered tile/pixel may carry or locate a stable semantic reference while its visual representation changes. Pixel values are observation data, not semantic authority.

This experiment does **not** promote a semantic compiler, new CHID, Rune, Glyph, SHAEP form, permission rule, or world-state authority.

## Boundary

The experiment is routed only through the test surface:

- `?semanticpixellab=1`
- `/worldbuildersemanticpixeltest` when the host/router sends that path into the Blazor application.

The normal World Builder remains unchanged.

All sample identities use the `EXP:` namespace and are local to this experiment. They are intentionally absent from `.code-index/semantic_units.json` and must not be treated as canonical IDs.

## Runtime path

```text
experimental semantic reference
        -> DOM data-semantic-id
        -> mutable visual representation
           (palette / size / position / render mode)
        -> browser observation
           { semanticId, visual properties }
        -> exact experimental registry lookup by semanticId only
        -> known meaning OR fail-closed UNKNOWN
```

The resolver does not map RGB, CSS position, dimensions, or render mode to meaning.

## Acceptance tests

1. **Identity survives palette mutation** — change the visual colors; semantic reference is unchanged.
2. **Identity survives size mutation** — change width/height; semantic reference is unchanged.
3. **Identity survives position mutation** — move/rotate the representation; semantic reference is unchanged.
4. **Identity survives representation-mode mutation** — tile/pixel/glyph presentation does not create a new semantic identity.
5. **Unknown fails closed** — inject an unregistered experimental semantic reference; the resolver returns no meaning and does not infer from appearance.
6. **No production authority** — the lab writes no world state, permission state, SHAEP payload, registry entry, or server truth.

The `RUN PROOF` control executes a four-state browser-side mutation sequence against one DOM representation and reports whether the attached semantic reference remained byte-for-byte stable.

## Promotion rule

A successful experiment proves only the local mechanism. Promotion into the canonical semantic registry/runtime requires a separate deliberate change that defines versioned identities, relations, authority, provenance, and compatibility behavior. Do not silently reinterpret these `EXP:` references as canonical language forms.
