# Recursive WorldBuilder Viewer / Controller Canon

Status: CANON — user-confirmed 2026-10-09

## Rebuild rule

A rebuild means: preserve the current implementation as a recoverable historical version, then rewrite from canon. Historical code is evidence and a quick-retrieval implementation library; it is not architectural authority unless a complete restore is explicitly requested.

## Truth boundaries

- Identity is not representation.
- Representation is not semantic truth.
- The viewer observes and represents; it does not create spatial truth.
- The controller expresses semantic intent; device-specific input does not create separate behavior.
- The active Shaep supplies context.
- Spatial/topology authority determines coordinates, tier, layer, containment, and traversal.
- Camera zoom, camera angle, parallax, Z movement, and recursive Enter/Back are distinct operations.

## Recursive hierarchy

WORLD → REGION → LOCAL → SITE/BUILDING → ROOM/INTERIOR → TACTICAL ENCOUNTER → OBJECT → CONTAINER → CONTENTS

These are contexts of one recursive editor, not separate editors. Enter descends to a child context. Back ascends to the parent. Identity, coordinates, ownership, permissions, and parent/child relationships survive representation changes.

Layers are properties of the active spatial context, not hierarchy peers.

## Z topology

- 10 layers per tier.
- Layer identifiers exposed to builders are 1 through 10.
- Internal storage may remain zero-based (offset 0 through 9) only as an implementation representation.
- Builder Layer 1 maps to internal offset 0.
- Layer 1 is the parallax layer and carries a second identifier binding it to its tier.
- A tier does not consume an additional spatial layer.
- 30 tiers × 10 layers = 300 layers for the full 300-layer world Z model.
- No component may independently redefine LayersPerTier.

## Viewer

One persistent viewer represents the active Shaep. Its state separates:

1. Spatial address: X, Y, Z / tier / layer.
2. Recursive context: current Shaep and parent/child path.
3. Camera: pan, zoom, angle.
4. Parallax representation.
5. Selection.
6. Authority/permissions.

Changing camera state cannot change spatial identity. Changing recursive context cannot silently remap coordinates. Changing parallax cannot relocate content.

## Universal controller

The canonical physical-independent control vocabulary is exactly four primary inputs:

- X axis
- Y axis
- Left action
- Right action

Mouse, touch, keyboard, game controller, gesture, accessibility devices, and future adapters translate into those semantic inputs. The active Shaep/context assigns their current meaning.

Additional device buttons may provide shortcuts, but shortcuts must dispatch the same semantic action and may not create a second control authority.

Typical navigation context:

- X/Y: move selection
- Left: Back
- Right: Enter/Select

Typical placement context:

- X/Y: move selected content
- Left: Cancel/Back
- Right: Place/Confirm

## Preservation rule

Old code is retained through Git history and explicit pre-rebuild backup refs. It may be mined for algorithms, assets, interaction details, edge cases, and previously working mechanisms. Reusing old code requires checking it against current canon first.

A complete restore is a separate explicit operation and may reinstate the historical implementation as a whole.
