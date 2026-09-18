# RegionDefiner Contract

RegionDefiner is derived from WorldBuilder, but it does not become another authority over the world.

## Canonical flow

1. A World ID is selected first.
2. RegionDefiner opens on the **surface** representation by default.
3. RegionDefiner displays that world as a **non-editable source** using the same viewer and contextual-keyboard architecture as WorldBuilder.
4. The **Select** keyboard begins with **Claim Region**.
5. Claim Region requires the user to choose exactly one Tier. RegionDefiner does not use WorldBuilder's **All Parallax** working mode while claiming.
6. The viewer supports **Square** and **Hex** selection/placement grids. Square is the default. The chosen geometry also becomes the placement snap grid for regional assets.
7. The user selects the region tiles on the 30×30 source grid. **Crop** previews the claim.
8. The user names the claim and chooses **Save Claim**. Saving stores the region definition, crops away everything outside the selected mask, and presents the claim as the full regional map.
9. **Build Region** opens the regional asset workflow against that cropped map.
10. Within the active Tier, each of the ten locked World source layers may be independently shown/hidden and included/excluded from the region definition. Layer visibility never unlocks or mutates WorldBuilder source assets.
11. Asset-library filters resolve to **REGION** assets while RegionDefiner is active. Regional overlays remain separate from source-world assets and stay visible when source layers are hidden.
12. Region data is saved beneath `worlds/{WorldId}/regions/` and never rewrites the source WorldBuilder terrain.

## Representation

RegionDefiner uses a fixed **15° perspective tilt** with a shallow focal point. This may change the apparent viewer silhouette and visual spacing. It is presentation only. World coordinates, World ID, source tiles, scale, Tier, Layer and Z are not changed by the 15° portrayal.

After a claim is saved, the selected-cell mask is used as the visible regional extent and its bounds are fitted to the viewer as the regional full-map representation. The parent-world coordinates and selection mask remain available for provenance.

## Source/overlay authority

- World source: read-only in RegionDefiner, including WorldBuilder images, sprites, labels and terrain placements.
- Region selection: references world cells from the selected world.
- Region crop: retains source World ID, selected-cell mask, source Tier, selected World layer offsets, and Square/Hex grid geometry.
- Claimed source tiles are normalized into regional-map coordinates while the parent-world bounds retain their provenance.
- Regional tiles: independent overlay records owned by the region.
- Region overlays may be added or removed without changing WorldBuilder terrain.
- A region may later support its own finer-scale representation, but that must not mutate the parent world coordinates.

## Extents

The source viewer remains 30×30 addressable cells. Ordinary worlds retain their normal world limits. **Endemar** remains the Shaelvien-controlled world exception. World extent is a world capability, not a viewer-scale setting.
