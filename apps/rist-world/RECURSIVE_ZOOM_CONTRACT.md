# Shaelvien recursive zoom — governing spatial contract

**Status: canonical design requirement.** This contract governs the next
RegionDefiner → Local → Instance refactor; it is not a claim that the present
runtime has implemented every requirement.

## One world, continuously traversed

WorldBuilder, RegionDefiner, Local and Instance are **levels of representation
of the same persistent world**, not independent or duplicated maps. Every
object retains stable identity, ancestry, canonical parent coordinates, layer
provenance and permissions as a camera zooms down or back up. The database
stores one recursively addressable spatial graph; clients load only the nodes
and asset subsets needed for the currently authorized view.

The world view owns its own tiers. Each deeper editing view starts from an
*exact chosen parent tier* and *exact chosen parent source tiles*. That selection
becomes the child's base working surface (the "table"), upon which the child
builds its own **relative** layers and tiers (the next cakes). A child's first
editable layer is not another parent-world tier.

### WorldBuilder — source world

WorldBuilder authors the full world terrain, water, lakes, source tiles and
world tiers. Region creation selects actual source tile identities and
addresses **on a chosen world tier**, not visual hexes or positions projected
from the browser viewport. A selectable grid is allowed as the UI, but each
hit must resolve to one canonical source tile identity and must round-trip
through the exact parent map coordinate transform. Camera zoom, tilt, crop or
screen size must not change which world tile is selected.

### RegionDefiner — 15-degree representation

On deed approval, the claimed source tile subset of the selected world tier
becomes the **immutable regional base**. The region's selected tiles are
streamed from the canonical source: unselected world tile data, artwork and
unrevealed locations are not loaded into the editing view. A full-world image
can be used in the *pre-claim world selection* preview, but a claimed region
must use indexed/cropped source assets instead of silently transferring full
world tier images to mask client-side. Any legacy bitmap-only world tier needs
an indexing/extraction path before this guarantee is true.

Regional objects such as cities, lakeside buildings, roads and sprites occupy
editable layers **relative to that regional base**. The terrain and lakes
inherited from the selected parent source tier remain visible and immutable.
A new city placed on the base moves with its terrain: it does not get independent
parallax and is not silently promoted into another parent-world tier. Only
placing an object into an explicitly created *regional* higher tier introduces
relative depth/parallax. A parent world tier and a child regional tier are
distinct identifiers, even when their ordinal numbers happen to match.

### Local — 30-degree representation

Select source tiles and a tier from the region's authored spatial graph. The
selected regional subset becomes the local base. Local adds its own editable
relative layers and tiers while keeping the source region objects and parent
relationships intact. Local terrain is not an independent copy of a world
image.

### Instance — 45-degree representation

Select source tiles and a tier from Local. Its base can represent a structure
or location; its editable layers and tiers provide interiors and finer detail.
The same identity, permission, source-selection and coordinate rules apply.

## Coordinates and identity

- Parent nodes have immutable world-scoped IDs. Children persist
  `worldId`, `parentNodeId`, `parentTierId` and the exact ordered
  `sourceTileIds` or validated equivalent canonical cell addresses.
- A child's local XY is mapped into its selected source tile footprint through
  an explicit, reversible parent/child transform. Relative depth uses the
  child's own tier/layer address and does not overwrite parent Z.
- Child edits persist under the child's identity within the same canonical
  world graph, with parent linkage and exact permission scope. Independent
  recovery caches are not additional world truth.
- A client requesting RegionDefiner, Local or Instance gets the authorized
  selected source subset plus child-owned layers, not a full parent-world
  snapshot with an obscuring opacity mask.

## Continuous zoom

The camera moves across World → Region → Local → Instance representation
boundaries without changing the underlying world or replacing an object's
identity. The renderer may change tilt (world native angle, 15°, 30°, 45°),
scale, assets, spatial resolution and interaction scope at each boundary.
Zooming back out resolves the same parent node and original location.
Parallax is **relative to the owning tier**, not a side effect of moving
between editor pages or cropping the viewport.

Permission-filtered streaming is part of the traversal: the viewer receives
only authorized ancestors, selected parent source tiles and the currently
permitted child depth. Existing region deeds must not be silently remapped
when tile indexing or transform code changes; explicitly review and migrate
legacy deeds when their saved footprint is ambiguous.

## Mandatory end-to-end acceptance

1. Select one WorldBuilder tier and exact source tiles covering a lake. Confirm
   that panning, zooming and selection overlay position cannot change their IDs.
2. Claim those tiles. The region loader requests only that source subset and
   resolves the lake in the immutable regional base. No neighboring world
   tiles or entire full-world tier PNG are transferred after the claim.
3. Place a city on the region base and edit it by touch and mouse. With camera
   pan, zoom and tilt, the city stays attached to the same terrain/lake position
   and has no independent parallax.
4. Add an explicit higher regional tier and place an object there. That object
   may exhibit parallax relative to the regional base; the world source tier
   remains unchanged.
5. Zoom back out to World and back into the region. Verify the same IDs,
   coordinates, lake, city, relative depth and permissions, with no duplicate
   world or region records.
6. Repeat from a chosen region tier to Local at 30°, then from a chosen Local
   tier to Instance at 45°. Round-trip all the way back to World without any
   positional drift or loss of source provenance.

## Implementation and outstanding work

The RegionDefiner child projection endpoint filters saved deeds to exact selected
source cells, parent tier and source layers. Region-owned objects and independently
authored regional tier stacks persist under child nodes in the same world graph.
The approved Geonaph source tiers are pre-indexed into individual hex/square WebP
source cells, and individually authored source tiles can be projected by their
cell addresses. Private Sandbox worlds can project independently published
source tiles using owner-scoped storage; parent world images are never returned
whole to claimed-region viewers.

Legacy full-world bitmap art in a non-Geonaph world still needs an index/export
pass before its terrain is visible in the claimed-region view. The editor
reports that missing index rather than downloading the full parent world and
masking other territory. Exact deed IDs, parent coordinates and ownership
must remain unchanged during asset migration.

Continuous camera crossing from WorldBuilder into RegionDefiner and then
Local (30°) and Instance (45°) is later integration work. The regional child
workspace and relative tiers are in the present build; do not claim completed
cross-level continuous zoom or Local/Instance editing prematurely. CI plus
interactive mobile verification of a claimed lake and editable city remain
release acceptance gates.
