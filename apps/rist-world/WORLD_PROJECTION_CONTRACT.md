# Shaelvien / RIST World Geometry and Projection Contract

This contract is canonical for WorldBuilder spatial math and viewer representation.

## World Geometry Invariants

1. One world grid cell is exactly **1 km × 1 km × 1 km**.
2. The same cell dimensions apply at sea level, mountain height, underground, sky layers, and every Tier/Layer.
3. X, Y, Z, Tier, and Layer are world-state coordinates. Viewer zoom, perspective, and parallax never rewrite them.
4. A tile's authored footprint is measured in world cells. A `4²` tile occupies 4 × 4 world cells regardless of altitude.
5. Travel cost, movement difficulty, route length, and game-system distance are gameplay rules. They do not redefine geometric distance.
6. Representation is not identity. A rendered object may look larger or smaller because of projection while retaining exactly the same authored world size.

## Projection Rule

The viewer transitions continuously between spatial and cartographic representations.

### Spatial / close view

- Higher-Z content may render slightly larger because it is visually closer to the viewer.
- Height may also produce a small parallax displacement relative to lower content.
- These effects are presentation only.
- Logical hit testing, placement, saves, permissions, and measurements continue to use unchanged world coordinates.

### Cartographic view

- As the viewer zooms outward, parallax is progressively reduced.
- At cartographic scale, projection becomes effectively orthographic.
- A kilometre measured at mountain height and a kilometre measured at sea level occupy the same map distance.
- Cartographic representation may simplify assets or aggregate detail, but it must not change spatial identity.

## Representation Continuum

The current viewer projection exposes representation bands for later asset/detail substitution:

`local-spatial → site-spatial → cartographic-local → cartographic-region → cartographic-world`

These names describe representation only. Moving through them must never mutate the underlying world.

## Parallax Authority

`wwwroot/worldbuilder-projection.js` is the WorldBuilder presentation authority for altitude-derived parallax and cartographic blending.

It may read:

- viewer zoom;
- tile Tier/Layer/Z;
- rendered tile position;
- viewer dimensions.

It may change only presentation variables such as rendered image scale and displacement. It must not change:

- tile X/Y/Z;
- Tier or Layer;
- tile footprint;
- Plane/Cube identity;
- grid measurement;
- persistence data.

## Grid Authority

The WorldBuilder viewer grid is a coordinate reference, not terrain and not an asset container.

- Every visible grid square represents one true square kilometre in X/Y.
- Every Z step represents one true kilometre in height.
- Tier/Layer organization may group Z addresses for editing and representation, but does not alter the kilometre unit.
- Ocean or other base terrain is representation/content laid against this fixed coordinate system.

## Core Principle

**World math is absolute. Viewer projection is contextual.**
