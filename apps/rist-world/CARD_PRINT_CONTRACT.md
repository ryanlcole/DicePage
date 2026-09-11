# Shaelvien / RIST Card Printing Contract

A Shaelvien card is one canonical recursive object with multiple print/render targets. The target changes representation only; it does not change card identity, ownership, language, provenance, references, or world truth.

## Canonical rule

`Card identity → artwork + human-readable face + glyph/data mark + provenance + recursive references`

The card must remain useful when no computer is present. Therefore a printable card carries its artwork and the exact human-visible language that is permitted for that card. If the card is restricted to an in-game language, the physical/exported card carries only that in-game wording and must not embed a translated plaintext copy that would bypass the restriction.

A browser cannot reliably determine whether the selected operating-system printer is an ordinary printer, a production card printer, or a 3D printer. Shaelvien therefore treats these as explicit print/export targets. A future native tabletop/desktop bridge may map known hardware to the same targets automatically.

## Print targets

### Standard printer

A standard household/office printer produces a low-cost physical reference. The card uses standard raster artwork and a clearly visible Shaelvien glyph/data block so the card remains machine-readable after ordinary printing/scanning. This target is intentionally economical rather than production quality.

### Card maker / production card printer

A card-production device receives the high-resolution artwork representation. The same Card ID, manifest hash, art data mark, permitted language, and creator provenance are embedded in the output. The glyph/data mark may be integrated into Shaelvien artwork instead of presented as the large visible code used by the standard-printer profile. Higher print quality does not create a different card identity.

### 3D printer

A 3D-print target does not flatten a recursive map into one image. World/Region/Local/Instance/Encounter map cards expose their ordered image/asset, Tier, Layer, X/Y, footprint, rotation, and treatment manifest so the 3D renderer can build physical depth from the same authored structure. Tier establishes independent elevation; Layer is supported depth inside the Tier. The intended production interchange format is 3MF. Generation of printer-ready 3MF geometry is a renderer responsibility; it may not modify canonical X/Y/Z/Tier/Layer state.

## Creator provenance and rights

Every exported or printed card carries a public `CreatorProvenanceId` derived from the authenticated account identity. AWS retains the authenticated ownership relationship so Shaelvien can resolve that provenance back to the account that created or published the card without printing the raw private account ID on the object itself.

The provenance mark is included in all three print profiles: visible/glyph-linked on standard print, integrated into the production card data mark, and preserved as a physical/data mark in 3D output.

Provenance is an audit and attribution mechanism. It can support enforcement of creator terms and copyright complaints, but it does not by itself decide legal copyright liability or eliminate platform obligations; rights declarations, takedown procedure, terms, and applicable law remain separate concerns.

## Recursive rendering

The same card can therefore be rendered as:

- digital interactive card;
- ordinary printed card;
- production-quality trading card;
- scanner-readable physical artifact;
- 3D physical representation of its Tier/Layer structure.

Identity remains constant across every representation.
