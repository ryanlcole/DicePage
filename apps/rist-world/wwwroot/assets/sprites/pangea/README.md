# Pangea sprite library

Pangea assets use a registered 1200 × 1200 pixel canvas mapped to the 30 × 30
WorldBuilder grid (40 pixels per world cell). The origin is the top-left corner.
Every registered layer for a chunk must keep that canvas and origin unchanged.

The canonical drawing/elevation folders are recorded in `library.json`:

1. Ocean floor — Tier 0 / Layer 0
2. Ocean surface — Tier 0 / Layer 9
3. Coast and shallows — Tier 1 / Layer 0
4. Low plains — Tier 1 / Layer 1
5. Valleys and depressions — Tier 1 / Layer 2
6. Forests and wetlands — Tier 1 / Layer 4
7. Hills and uplands — Tier 2 / Layer 1
8. Mountains and peaks — Tier 2 / Layer 5
9. Waterways — Tier 1 / Layer 6
10. Special terrain — Tier 2 / Layer 8

`catalog.json` is loaded alongside the existing tile catalog. Entries marked with
`authoredDepth: true` retain their default tier and layer when placed. Registered
chunk sprites also specify `defaultFootprint: 30`, so they fill the map and align
at its origin. The `registered/` tree is keyed by chunk coordinate.

The registered PNGs are served from the RIST asset CDN under
`assets/sprites/pangea/registered/`. Runtime composition uses the independent
registered images so either layer can be replaced or streamed without flattening
the other. The combined ocean sprite strip remains an interchange artifact in
the downloadable source package rather than being bundled into the application.
