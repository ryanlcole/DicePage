# RegionDefiner Contract

> Governing spatial model: [RECURSIVE_ZOOM_CONTRACT.md](RECURSIVE_ZOOM_CONTRACT.md).

RegionDefiner is **WorldBuilder restricted to a claimed coordinate footprint**.
It does not own another map, another world-tier stack, or another terrain truth.

## Canonical source

WorldBuilder remains the authoritative map.

A region deed records:

- World ID;
- parent World Tier;
- exact selected 30×30 WorldBuilder source cells;
- grid geometry used to address those cells;
- permitted source layers;
- owner/edit authority.

Before the deed is claimed, RegionDefiner may show the full selected World Tier
so the user can choose cells. After the deed is claimed, only the selected
source-cell subset is loaded into RegionDefiner. Those inherited cells and all
inherited WorldBuilder content are read-only.

The selected cells are the RegionDefiner **table**. They are not copied into an
independent world. Their WorldBuilder identity and X/Y position remain canonical.

## Claim flow

1. Select the world.
2. Open RegionDefiner and choose **New** or an existing deed.
3. For New, preview one World Tier. All-parallax is not a claim target.
4. Select exact source cells on that World Tier. Hex is the default; Square is
   supported.
5. Crop is a pre-claim visual preview only.
6. Name the deed.
7. The confirmation row contains **Back** and **Claim Deed**.
8. A direct-authority user creates the deed; a request-only user submits the
   same footprint for approval.
9. After claim, the selection grid is removed. The selected source cells
   themselves are the working table.
10. The parent World Tier and inherited WorldBuilder content remain untouchable;
    RegionDefiner can add and edit only region-owned overlays inside the deed.

Camera zoom, pan, tilt, viewport size, or phone orientation must never change
which source-cell IDs the deed addresses.

## Z model

The selected World Tier is fixed by the deed.

Within that World Tier, WorldBuilder depth is integer:

- World Z 0 = WorldBuilder Layer 1;
- World Z 1 = WorldBuilder Layer 2;
- …
- World Z 9 = WorldBuilder Layer 10.

RegionDefiner adds detail **between** those integer World Z positions:

- World Z 0 → regional overlays 0.01 through 0.09;
- World Z 1 → regional overlays 1.01 through 1.09;
- …
- World Z 9 → regional overlays 9.01 through 9.09.

A regional city at 2.03 is still on the deed's selected World Tier. It did not
create or move to another World Tier. It is simply Region Layer 3 above
WorldBuilder World Z 2.

The implementation stores regional depth exactly as integer hundredths
(`z100 = worldZ * 100 + regionLayer`) and derives the decimal display. Raw
floating-point values are not authoritative coordinates.

Region layers are always 1–9. World Z is always 0–9.

## Movement and parallax

Region-owned images, labels, tiles, and sprites are map-attached.

They use the same parent map camera transform as the inherited WorldBuilder
terrain. RegionDefiner does not give them independent parallax merely because
they are above the parent map. Moving a regional object between 0.01 and 9.09
changes its draw/depth order, not its parent World Tier or map alignment.

Parallax between World Tiers remains a WorldBuilder concern. RegionDefiner is a
15° representation of one selected World Tier and its claimed coordinates.

## Persistence

There is one WorldBuilder source truth.

For shared worlds, a regional save semantically patches only that region's
entries in the canonical `WORLDSOURCE.state.userLayers`. Every region-owned
entry carries its `regionId`, parent World Tier, World Z, Region Layer,
exact `z100`, X/Y, and asset identity.

For private Sandbox worlds, the same semantic merge is performed against the
owner-scoped encrypted WorldBuilder source.

A regional save must preserve:

- inherited terrain;
- inherited lakes/rivers and other source tiles;
- parent WorldBuilder images/labels/sprites;
- other regions' overlays;
- all world identity and source provenance.

RegionDefiner must never replace the World Map image, overwrite parent terrain,
or create a second map authority.

## Selected-source loading

A claimed region receives only source assets applicable to its selected cells.

Official Geonaph World Tier imagery is build-indexed into independently
addressable source cells. Independently authored WorldBuilder tiles and source
objects are filtered by parent tier, integer World Z, and selected cell.

A legacy custom/private full-world bitmap without an addressable source index
must be indexed before its inherited terrain can be shown without loading
unclaimed territory. Missing indexing fails closed; it does not justify loading
the entire parent map into a claimed RegionDefiner session.

## Editing authority

The inherited WorldBuilder table is locked.

Only objects with the active `regionId` are selectable, draggable, editable,
or removable in RegionDefiner. A WorldBuilder object visible underneath may be
used as context but does not enter the editable Select dropdown.

All server writes verify:

- active world;
- deed identity;
- edit authority;
- selected parent World Tier;
- selected source cells;
- X/Y inside that footprint;
- World Z 0–9;
- Region Layer 1–9;
- exact Z consistency;
- no world-map replacement.

## Representation

RegionDefiner uses a fixed **15°** presentation. The angle is representational;
it does not modify source X/Y, World Tier, integer World Z, deed IDs, or exact
regional Z.

## Reset for the Z-model transition

The 2026-09-24 transition to the exact World-Z/region-hundredth model explicitly
resets the existing Geonaph region deeds and legacy region-owned overlays, as
requested by the project owner. It preserves WorldBuilder terrain and
non-region WorldBuilder content. The reset is guarded by a one-time migration
marker so it cannot repeat on every Lambda cold start.

## Acceptance

A correct RegionDefiner must pass this sequence:

1. Select source cells containing recognizable terrain such as a lake.
2. Claim them.
3. Open the deed and see exactly those WorldBuilder cells, with the lake intact.
4. Confirm inherited terrain and inherited source objects cannot be selected.
5. Place a city at World Z 0 / Region Layer 1 and observe exact Z 0.01.
6. Move it to Region Layer 9 and observe 0.09 without map drift.
7. Move it to World Z 1 / Region Layer 1 and observe 1.01 without changing
   World Tier.
8. Pan/zoom/tilt and verify city and terrain remain attached.
9. Save, reopen, and verify identical X/Y, World Z, Region Layer, and asset ID.
10. Verify no unclaimed source cells were delivered to the claimed editor.
