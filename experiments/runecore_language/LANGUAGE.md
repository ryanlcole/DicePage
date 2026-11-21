# RuneCore/1 — experimental structural language

**Status: testable syntax and interpreter; not a trained LLM, not quantum chemistry, not canonical project authority.**

## Terms

- **Rion:** 0 = unoccupied/connectable position; 1 = occupied position. Direction belongs to a ring, not to a bit.
- **Ring:** atomic ring of Rions; inner clockwise, second counterclockwise, alternating.
- **Rune:** encoded element in a fixed memory slot, built from Rings. Atom is a legacy code alias.
- **Glyph:** periodic-table identity (atomic number and symbol), not a structural signature.
- **Shaep:** what connected Runes form, with candidate contacts; not automatically a verified molecule.
- **Repeat:** exact minimal rotation cycle. Derive from seed + tick rather than writing each animation frame to SSD.
- **Viewer:** renders *only* atoms in the visible viewport, with no diagnostic text rendered inside the atom canvas.

## Provisional text grammar

```
RUNE <slot> <symbol> <x> <y>
RING 1 CW <binary-pattern>
RING 2 CCW <binary-pattern>
ENDRUNE
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


## Owner terminology correction — 2026-11-20
The old draft treated Rune as a ring and Glyph as a rotation hash. Both are **superseded** by the owner's direct correction: Rion=binary, Ring=atomic ring, Rune=element, Glyph=periodic-table element identity, Shaep=what elements form. Repeat=cyclic recurrence. Old Git revisions remain historical evidence.

The 118 symbolic periodic Glyph references are catalog metadata, not inferred ring encodings. Only H/O have owner-supplied encodings. A rotation-invariant pattern_signature is separate from Glyph; same bits do not prove same element. Legacy ATOM/ENDATOM text records still parse, but new records use RUNE/ENDRUNE. The Old ReLiC authority term AuthorityRune is separate from elemental Rune.
