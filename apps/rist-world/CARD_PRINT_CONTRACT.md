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

## Card stacks and in-game mesh assembly

A physical table does not need every card spread flat. Players may place multiple physical cards in one pile to conserve table space. Shaelvien treats that pile as a compact physical representation of an ordered digital `RistCardStack`.

Cards are scanned individually. Each scan resolves the card's own Card ID, manifest identity, card type, and creator provenance. The game then adds that card identity to the active stack in bottom-to-top order. Stacking does not merge, destroy, or rewrite the source cards; every card remains independently addressable and removable.

The game assembles the visual/3D composition from the cards in the stack. Each card contributes its own recursive artwork, geometry, references, Tier/Layer information, and permitted language. Stack order controls composition precedence where representations overlap, but does not silently rewrite a card's canonical world coordinates or Tier/Layer values.

The canonical flow is:

`physical cards → individual glyph scans → ordered in-game card stack → assembled digital mesh/scene → optional 3D-print representation`

A saved stack stores only the ordered card identities and composition metadata needed to reconstruct the scene. AWS stores the authenticated stack for logged-in users while the individual cards remain separate inventory objects.

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
- an element in an ordered table/card stack;
- 3D physical representation of its Tier/Layer structure or an assembled stack.

Identity remains constant across every representation.
