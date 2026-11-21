# RuneCore/1 — experimental structural language

**Status: testable syntax and interpreter; not a trained LLM, not quantum chemistry, not canonical project authority.**

## Terms

- **Rion:** 0 = unoccupied/connectable position; 1 = occupied position. Direction belongs to a ring, not to a bit.
- **Rune:** ordered Rion ring with alternating directions: inner CW, second CCW, third CW, etc.
- **Atom:** persistent memory slot containing rings. Slot/identity remains fixed while ring phases advance.
- **Glyph:** stable, bounded rotation-invariant ring-pattern reference. A Glyph is a representation, not identity or truth.
- **Shaep:** bounded structure of atom/Glyph references and candidate relationships, not automatically a real chemical molecule.
- **Repeat:** exact minimal rotation cycle. Derive from seed + tick rather than writing each animation frame to SSD.
- **Viewer:** renders *only* atoms in the visible viewport, with no diagnostic text rendered inside the atom canvas.

## Provisional text grammar

```
ATOM <slot> <symbol> <x> <y>
RING 1 CW <binary-pattern>
RING 2 CCW <binary-pattern>
ENDATOM
```

The source-proposed hardware START/STOP direction-and-ring markers are **not yet assigned binary opcodes**; ATOM/RING/ENDATOM are text delimiters, not a settled CPU ISA. They do not stop physical rotation.

CW means shift bits one position right per logical tick, CCW one position left, under the serialization convention of the supplied examples. These represent orbital positional patterns, not actual measured electrons.

## Supplied examples

Hydrogen: `1000 → 0100 → 0010 → 0001 → 1000`.
Oxygen inner: `1010 → 0101`.
Oxygen outer: `11101110 → 11011101 → 10111011 → 01110111 → 11101110`.

The existing v0.9 prototype's water contact/exposure trace (experimental observation convention) alternates full and raw oxygen outer rings:
```
11111111
11101110
11111111
11011101
11111111
10111011
11111111
01110111
```
Mirrored-sector matching and alternating subphases are *proposals*, not independently established molecular forces. Only H/O ring encodings have explicit user support. Other element labels are not encodings.

## Training an actual RuneCore model — a separate future milestone

1. Build a provenance-tagged corpus of structures and independent transitions.
2. Train and evaluate baselines on **unseen ring structures**. Do not leak neighboring repeated ticks between train/test partitions.
3. Compare a learned predictor's held-out error, phase consistency and conservation-law performance with deterministic algorithms.
4. To claim a RuneCore LLM, document architecture, parameters, weights, training compute, data rights and reproducible held-out evaluation. This interpreter is **not an LLM**, and adding RuneCore syntax here does **not** modify ChatGPT model weights.
5. Test physics separately against externally validated standards. Correct symbol matching is not evidence of chemical or physical discovery.

**Provenance rules:** ID != REP; REP != TRUTH; UNKNOWN != FACT; MEMORY != CANON. Any use as project canon requires explicit authoritative promotion.
