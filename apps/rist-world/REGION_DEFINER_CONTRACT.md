# RegionDefiner Contract

> Governing recursive-world specification: [RECURSIVE_ZOOM_CONTRACT.md](RECURSIVE_ZOOM_CONTRACT.md).

RegionDefiner is **WorldBuilder constrained by a claimed X/Y footprint on one selected World tier**. It is not a second map, not a copied map, and not an independent tier graph.

## Canonical flow

1. A World is selected first.
2. Choosing **RegionDefiner** opens the region chooser and **New**.
3. **New** opens the working WorldBuilder map for that world so the user selects a World tier and exact map cells.
4. Claim selection is performed against canonical WorldBuilder coordinates, not viewer pixels.
5. Hex or Square is only a claiming/placement geometry. The stored deed is the selected canonical cell IDs plus selected World tier.
6. The user crops, names, and confirms with **Back** or **Claim Deed**.
7. Once claimed, the selection grid is removed. The claimed cells become the RegionDefiner table.
8. RegionDefiner calls only those selected coordinates from the selected World tier. The rest of the world remains in the database but is not part of the regional editing surface.
9. Inherited WorldBuilder terrain, lakes, roads, images, labels, sprites, and other source objects inside those coordinates are visible but immutable.
10. Region-authored objects are editable overlays stored in the same canonical WorldBuilder source with their region ID and exact parent address.
11. There is no separate Region tier stack. Region depth is a finer address inside World Z.
12. The first regional overlay above World Z `n` is `n.01`; regional overlay depth continues through `n.09`.
13. Regional overlays are map-attached and have no independent parallax. They move exactly with their selected parent World tier.
14. RegionDefiner uses the same placement/editing tools as WorldBuilder, except parent World content is locked and placement is restricted to claimed coordinates.
15. A request-only user receives no edit authority until the deed is approved.

## Exact Z model

WorldBuilder owns integer Z:

- World Z `0` = first WorldBuilder layer.
- World Z `1` = second WorldBuilder layer.
- …
- World Z `9` = tenth WorldBuilder layer.

RegionDefiner inserts detail at hundredths above each World Z:

- World `0` → Region `0.01 … 0.09`
- World `1` → Region `1.01 … 1.09`
- …
- World `9` → Region `9.01 … 9.09`

The runtime stores this exactly as integer `z100 = worldLayer * 100 + regionLayer`; floating point is presentation only.

The selected World **tier** remains fixed by the deed. `worldLayer` is the integer World Z within that selected tier. `regionLayer` is 1–9. A Region object therefore stores its selected parent tier, worldLayer, regionLayer, z100, X/Y coordinates, regionId, and parent provenance.

## Representation

RegionDefiner uses the regional presentation angle, currently 15°. This changes representation only. X/Y identity, selected World tier, World Z, exact Region Z, and source ownership do not change.

The claimed source cells themselves are the post-claim table. The pre-claim mask is only a selection/crop aid; after claim, the renderer uses the selected source cells rather than depending on an opacity mask over the full world.

## Claim authority

Selecting territory is not equivalent to owning it.

- an owner/GM may claim and edit directly within their authority;
- an invited non-owner may submit a Claim Request where policy permits;
- Blocked, Restricted, Limited, Co-Operative, and Release Ownership remain authority decisions;
- a pending request never grants edit authority.

## Canonical-map authority

There is one recursive map truth.

- WorldBuilder authors the world.
- RegionDefiner is the same world filtered to a claimed coordinate subset.
- Parent World content is immutable while RegionDefiner is active.
- Region-authored overlays are written into the canonical WorldBuilder source with region provenance.
- Saving a Region never replaces the parent world map.
- Browser storage is recovery/cache only, never map authority.

## Extents and geometry

The claim UI uses the canonical 30×30 addressable source grid. Hex uses the established flat-top column-staggered lattice; Square remains supported. Claim display, server permission checks, selected source-cell streaming, placement snapping, and persisted cell identity must resolve the same cell IDs.

## Current reset

The previous RegionDefiner model used independent relative Region tiers and REGIONMAP child records. Existing Geonaph regions from that model are intentionally reset during deployment of the new exact-Z architecture. WorldBuilder terrain and non-region WorldBuilder content are preserved.
