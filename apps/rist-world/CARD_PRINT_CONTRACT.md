# Shaelvien / RIST Card Printing Contract

A Shaelvien card is one canonical recursive object with multiple print/render targets. The target changes representation only; it does not change card identity, ownership, language, provenance, references, or world truth.

## Canonical rule

`Card identity → artwork + human-readable face + glyph/data mark + provenance + recursive references`

The card must remain useful when no computer is present. Therefore a printable card carries its artwork and the exact human-visible language that is permitted for that card. If the card is restricted to an in-game language, the physical/exported card carries only that in-game wording and must not embed a translated plaintext copy that would bypass the restriction.

## Print targets

### Standard printer

A standard household/office printer produces a low-cost physical reference. The card uses standard raster artwork and a clearly visible Shaelvien glyph/data block so the card remains machine-readable after ordinary printing/scanning.

### Card maker / production card printer

A card-production device receives the high-resolution artwork representation. The same Card ID, manifest hash, art data mark, language contract, and creator provenance are embedded in the output. Higher print quality does not create a different card identity.

### 3D printer

A 3D-print target interprets recursive map geometry rather than flattening it. World/Region/Local/Instance/Encounter map cards expose their ordered Tier/Layer manifest so a future 3D renderer can construct physical height/depth from the same authored coordinates. Tier establishes independent elevation; Layer is supported depth inside the Tier. The print target may create geometry from those layers, but it may not modify canonical X/Y/Z/Tier/Layer state.

## Creator provenance and rights

Every exported/printed card carries a public `CreatorProvenanceId` derived from the authenticated account identity. The public card does not need to expose the raw private account identifier. Shaelvien can retain the authenticated ownership relationship in AWS so a published or exported artifact can be traced to the account that created/published it.

Provenance is an audit and attribution mechanism. It does not by itself decide legal copyright liability or eliminate platform obligations; rights handling, takedown procedure, terms, and applicable law remain separate concerns.

## Recursive rendering

The same card can therefore be rendered as:

- digital interactive card;
- ordinary printed card;
- production-quality trading card;
- scanner-readable physical artifact;
- 3D physical representation of its Tier/Layer structure.

Identity remains constant across every representation.
