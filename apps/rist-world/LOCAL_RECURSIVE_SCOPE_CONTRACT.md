# RIST Local Recursive Scope Contract

Status: CANONICAL LOCAL EDITOR DIRECTION
Date: 2026-09-25
Parent authority: [RECURSIVE_SCOPE_EDITOR_CONTRACT.md](RECURSIVE_SCOPE_EDITOR_CONTRACT.md)

## Scope

Local Definer authors a **LOCAL** recursive scope at a fixed **30°** representation.

The selected parent Region asset is the Local root/reference. Opening a Local
must hide unrelated Region assets from the authoring view without changing or
copying parent Region truth.

## Root

The Local root is the stable parent Region placement identity selected when the
Local is created.

Canonical LOCAL root state:

- scopeKind = LOCAL
- scopeId = LocalId
- parentScopeId = RegionId
- parentAssetId = AnchorObjectId
- x = 0
- y = 0
- tier = 1
- layer = 1
- viewDegrees = 30
- locked = true

The parent Region placement remains a Region-owned asset. The Local root is a
read-only recursive reference to it, not a duplicate asset.

## Coordinates

LOCAL coordinates restart at the root.

The compatibility renderer may continue to project Local placements into the
parent Region/World canvas while migration is in progress, but recursive LOCAL
X/Y are authoritative.

For the current adapter, a Local coordinate is an anchor-relative normalized
delta from the root center:

- localX = (projectedWorldX - anchorCenterX) / anchorWidth
- localY = (projectedWorldY - anchorCenterY) / anchorHeight

Therefore the root center is always LOCAL (0,0). Moving the camera or changing
representation does not change LOCAL X/Y.

## Tier and Layer

LOCAL Tier and visual Layer are independent and one-based.

- Tier changes parallax/depth only.
- Layer changes ordinary compositing order only.
- Tier never participates in ordinary front/back sorting.
- Layer never changes parallax distance.
- Layer is not capped by the legacy 1..9 compatibility window.

The root reference begins at Tier 1 / Layer 1. A new Tier-1 asset overlapping
that root begins above it at Layer 2. On another Tier, the first placement may
begin at Layer 1.

Legacy localTier/localLayer/hierarchical fields may remain beside recursive
truth during migration. They are compatibility projections only.

## Asset editor

Local uses the same GIMP-inspired asset list as World and Region:

- visibility
- position/edit lock
- stable asset name/identity
- opacity
- visual Layer
- spatial Tier
- linked/group state
- selected-principal permission state

Permissions remain server-authoritative and do not alter geometry.

## Local markers

A Local marker is a named LOCAL asset intended to become a future INSTANCE
anchor.

A marker stores:

- its stable Local asset identity;
- its LOCAL recursive coordinates;
- the stable asset it touches/intersects as anchorAssetId.

Instance creation resolves the marker and touched asset; it does not infer an
Instance from visual equivalence.

## Persistence

New Local map state uses RIST_RECURSIVE_SCOPE_V1 and carries:

- LOCAL scope metadata;
- root reference metadata;
- recursive envelopes for Local-owned assets;
- compatibility parent projection fields only where required by the current
  renderer.

Legacy Local saves are read through an adapter. They are not overwritten in
place until a successful recursive save.

## Acceptance

1. Open a saved Local and show only its root Region asset plus Local children.
2. Root is LOCAL x=0, y=0, Tier 1, Layer 1 at 30°.
3. Place a child on Tier 1 over the root and assign visual Layer 2.
4. Change child Layer; Tier and X/Y do not change.
5. Change child Tier; Layer and X/Y do not change.
6. Move child; recursive LOCAL X/Y change while parent Region identity remains.
7. Save/reopen and recover identical LOCAL x/y, Tier, Layer and stable asset ID.
8. Server permission edits do not change geometry.
9. Unrelated Region assets never enter the Local authoring surface.
