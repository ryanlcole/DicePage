# Shaelvien recursive zoom — governing spatial contract

**Status: canonical design requirement.**

## One connected world

WorldBuilder, RegionDefiner, Local, and Instance are connected levels of representation, not duplicated realities. X/Y identity and ancestry survive every recursion and every zoom transition.

The first three scales share one exact external spatial address:

**World → Region → Local**

Instance is different: entering a building or landmark opens a new interior world whose external anchor is the object or landmark that contains it.

## WorldBuilder — integer Z

WorldBuilder is the full world map and terrain authoring system.

Within a selected World tier, World depth is integer Z `0 … 9`:

- `0` = World layer 1
- …
- `9` = World layer 10

World terrain, lakes, roads, and world-scale authored objects occupy this integer structure.

Region claims select exact X/Y coordinates from one World tier. Claiming never creates a replacement map.

## RegionDefiner — hundredth Z, 15°

RegionDefiner is WorldBuilder filtered to the selected World tier and selected claimed coordinates.

The selected WorldBuilder source cells become the RegionDefiner table and are immutable. Regional detail is placed directly above World integer Z at hundredths:

- `0.01 … 0.09`
- `1.01 … 1.09`
- …
- `9.01 … 9.09`

Regional objects stay attached to the parent map. They do **not** receive independent parallax merely because they are regional.

Storage uses exact components rather than binary floating point:

- parent World tier
- `worldLayer` 0–9
- `regionLayer` 1–9
- `z100 = worldLayer * 100 + regionLayer`
- canonical X/Y
- region identity and parent provenance

## Local — tenth Z, 30°

Local reuses the same parent coordinate model at the next visual scale.

Local detail occupies tenths:

- `0.1 … 0.9`
- `1.1 … 1.9`
- …
- `9.1 … 9.9`

This is a finer representation of the same place, shown at 30°. Local does not copy or replace the World or Region truth.

Exact storage must preserve scale separately so `0.1` is not confused with `0.10` as a floating-point artifact. The renderer may display decimal Z, but identity is structured.

## Instance Builder — separate interior world, 45°

Instance is not merely another decimal band of the exterior map.

Recursing into a building, landmark, dungeon entrance, vessel, portal, or similar object opens an **Instance Builder**. Instance Builder is a WorldBuilder-style authoring system for the inner world anchored to that exterior object.

Its important properties are:

- 45° representation;
- independent interior X/Y extent;
- tier after tier and layer after layer may be built;
- interior size is not required to match exterior footprint;
- the instance keeps a stable parent anchor to the exterior object;
- exiting the instance resolves back to the same exterior identity and coordinates.

This allows a hut, tower, cave, ship, portal, or magical landmark to contain an interior world of any required size without corrupting exterior scale.

## Continuous zoom

World → Region → Local remains one continuously connected exterior spatial system.

Camera scale and representation may change while identity stays fixed:

- World: native WorldBuilder representation
- Region: 15°
- Local: 30°
- Instance: enter separate anchored 45° interior system

Zooming back out must resolve the same parent object, coordinates, permissions, and authored state.

## Permission-filtered streaming

Clients receive only the currently authorized subset.

A claimed Region receives only its selected World coordinates and permitted source layers. A Local view receives only the permitted subset needed for that Local representation. Instance receives the authorized interior node and its descendants.

Permission filtering changes what is delivered; it does not create another truth.

## Mandatory acceptance

1. Select a World tier and exact cells that include recognizable terrain such as a lake.
2. Claim them and confirm RegionDefiner loads those exact coordinates only.
3. Confirm inherited lake/terrain remains visible and untouchable.
4. Place a city at `0.01`, move/edit it, and verify it stays attached to the parent map with no independent parallax.
5. Move regional placement through `.01 … .09` and World Z `0 … 9` without changing the claimed World tier or X/Y authority.
6. Reopen the region and confirm the same coordinates, exact Z, identities, and edits.
7. Build Local at 30° using the tenth-depth address model and verify round-trip back to Region and World.
8. Enter a building/landmark into the 45° Instance Builder, build an interior larger or smaller than the exterior footprint, then exit to the same exterior anchor.

## Current implementation boundary

RegionDefiner now targets the filtered-WorldBuilder model with integer World Z and hundredth Region overlays. Previous independent regional child-tier state is obsolete.

Local tenth-depth rendering and the separate 45° Instance Builder are the next implementation stages. Do not represent them as production-complete until their own runtime and round-trip acceptance tests pass.
