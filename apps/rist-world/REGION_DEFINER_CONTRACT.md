# RegionDefiner Contract

RegionDefiner is derived from WorldBuilder, but it does not become another authority over the world.

## Canonical flow

1. A World ID is selected first.
2. Choosing **RegionDefiner** opens a Region chooser styled like the World chooser. It lists saved regions and a **New** action.
3. Opening a saved region loads its stored Tier, source-world provenance, crop mask and regional map.
4. Choosing **New** opens a full-world preview sourced from the selected world's shared database-backed **WorldBuilder source snapshot**. RegionDefiner does not carry its own hard-coded world-map images: the Tier images, placed images, sprites and labels are called from the map state published by WorldBuilder. Endemar follows the same database source rule as every other world.
5. The New Region preview is swipeable across the three World Tiers. The user selects exactly one Tier. RegionDefiner never uses WorldBuilder's **All Parallax** mode for a new region.
6. After the Tier is selected, RegionDefiner enters selection-only mode: the only contextual keyboard is **Select**. Zoom/camera controls remain available so the user can navigate before choosing cells.
7. The viewer supports **Square** and **Hex** selection grids. Square is the default. The chosen geometry also becomes the placement snap grid for later regional assets.
8. The user selects the region footprint on the 30×30 source grid, names it, and chooses **Save Region** or the persistent Save control.
9. Saving stores the region definition, crops away everything outside the selected mask, fits the cropped extent as the full regional map, and then restores the remaining contextual keyboards and builder UI.
10. **Build Region** opens the regional asset workflow against that cropped map.
11. Within the active Tier, each of the ten locked World source layers may be independently shown/hidden after the region is saved. Layer visibility never unlocks or mutates WorldBuilder source assets.
12. Asset-library filters resolve to **REGION** assets while RegionDefiner is active. Regional overlays remain separate from source-world assets and stay visible when source layers are hidden.
13. Region data is saved beneath `worlds/{WorldId}/regions/` and never rewrites the source WorldBuilder terrain.

## Representation

RegionDefiner uses a fixed **15° perspective tilt** with a shallow focal point. This may change the apparent viewer silhouette and visual spacing. It is presentation only. World coordinates, World ID, source tiles, scale, Tier, Layer and Z are not changed by the 15° portrayal.

After a claim is saved, the selected-cell mask is used as the visible regional extent and its bounds are fitted to the viewer as the regional full-map representation. The parent-world coordinates and selection mask remain available for provenance. RegionDefiner never treats an entire named world as a region merely because it has a special world identity.

## Claim authority

Selecting a map portion is not equivalent to owning or editing it.

- an owner/GM may claim and build directly within their authority;
- an invited non-owner may select a portion and submit a **Claim Request** when their world claim policy permits it;
- **Blocked** removes the claim action;
- **Restricted** permits requests only inside already-authorized personal/character scopes;
- **Limited** permits requests but the GM chooses the final approved spatial/resource scope;
- **Co-Operative** grants shared ownership of the approved resource while locally protected child resources may retain secrets;
- **Release Ownership** transfers the granting owner's ownership only after exact written approval in a direct authenticated session.

A pending request does not unlock regional building. The GM decision is the authority boundary.

## Source/overlay authority

- World source: read-only in RegionDefiner, including WorldBuilder images, sprites, labels and terrain placements.
- Region selection: references world cells from the selected world.
- Region crop: retains source World ID, selected-cell mask, source Tier, selected World layer offsets, and Square/Hex grid geometry.
- Claimed source tiles are normalized into regional-map coordinates while the parent-world bounds retain their provenance.
- Regional tiles: independent overlay records owned by the region.
- Region overlays may be added or removed without changing WorldBuilder terrain.
- A region may later support its own finer-scale representation, but that must not mutate the parent world coordinates.

## Extents

The source viewer remains 30×30 addressable cells for claiming. RegionDefiner applies the same claim/crop/build process to every selected world, including Endemar. Any underlying world-extent or ownership rules remain world-level authority and do not change the RegionDefiner workflow.


## Shared WorldBuilder source

WorldBuilder publishes its saved map representation to the world database as one shared source snapshot. The browser IndexedDB copy is a cache/recovery surface, not RegionDefiner authority. A shared source snapshot carries the World ID, Tier image references, viewer Tier/Layer metadata, grid metadata, and the authored WorldBuilder layer references needed to reconstruct the map. RegionDefiner consumes that snapshot read-only and applies its 15° presentation and claim/crop workflow without rewriting the parent source.
