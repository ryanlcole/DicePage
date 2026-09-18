# RegionDefiner Contract

RegionDefiner is derived from WorldBuilder, but it does not become another authority over the world.

## Canonical flow

1. A World ID is selected first.
2. RegionDefiner displays that world as a **non-editable source**.
3. RegionDefiner uses the same viewer and contextual-keyboard architecture as WorldBuilder, but the source-world assets are locked.
4. The user chooses exactly one Tier at a time; RegionDefiner does not offer the WorldBuilder **All Parallax** working mode.
5. The **Select** keyboard exposes the 30×30 region-definition grid. The user selects world cells, names the region, and chooses **Create**.
6. The selected tile bounds are stored as a named region while the exact selected-cell mask and source Tier are retained.
7. Asset-library filters resolve to **REGION** assets while RegionDefiner is active. Regional overlays remain separate from source-world assets.
8. Region data is saved beneath `worlds/{WorldId}/regions/` and never rewrites the source WorldBuilder terrain.

## Representation

RegionDefiner uses a fixed **15° perspective tilt** with a shallow focal point. This may change the apparent viewer silhouette and visual spacing. It is presentation only. World coordinates, World ID, source tiles, scale, Tier, Layer and Z are not changed by the 15° portrayal.

## Source/overlay authority

- World source: read-only in RegionDefiner, including WorldBuilder images, sprites, labels and terrain placements.
- Region selection: references world cells from the selected world.
- Region crop: retains source World ID and selected-cell mask.
- Regional tiles: independent overlay records owned by the region.
- Region overlays may be added or removed without changing WorldBuilder terrain.
- A region may later support its own finer-scale representation, but that must not mutate the parent world coordinates.

## Extents

The viewer remains 30×30 one-kilometre cells. Ordinary worlds are bounded to 300×300 world tiles. **Geonaph is the explicit unbounded world exception.** World extent is a world capability, not a viewer-scale setting.
