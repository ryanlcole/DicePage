# RegionDefiner Contract

RegionDefiner is derived from WorldBuilder, but it does not become another authority over the world.

## Canonical flow

1. A World ID is selected first.
2. RegionDefiner displays that world as a **non-editable source**.
3. The initial 30×30 viewer grid is selectable.
4. The user selects world tiles and chooses **Create Region**.
5. The selected tile bounds are cropped into a named region while the exact selected-cell mask is retained.
6. Regional assets may then be placed above the world-source crop.
7. Region data is saved beneath `worlds/{WorldId}/regions/` and never rewrites the source WorldBuilder terrain.

## Representation

RegionDefiner uses a slight 5° perspective with a shallow focal point. This may change the apparent viewer silhouette and visual spacing. It is presentation only. World coordinates, World ID, source tiles, scale, Tier, Layer and Z are not changed by the 5° portrayal.

## Source/overlay authority

- World source: read-only in RegionDefiner.
- Region selection: references world cells from the selected world.
- Region crop: retains source World ID and selected-cell mask.
- Regional tiles: independent overlay records owned by the region.
- Region overlays may be added or removed without changing WorldBuilder terrain.
- A region may later support its own finer-scale representation, but that must not mutate the parent world coordinates.

## Extents

The viewer remains 30×30 one-kilometre cells. Ordinary worlds are bounded to 300×300 world tiles. **Geonaph is the explicit unbounded world exception.** World extent is a world capability, not a viewer-scale setting.
