# Shaelvien recursive zoom — governing spatial contract

**Status: canonical design requirement.**

Shaelvien is one persistent spatial world. WorldBuilder, RegionDefiner, Local,
and Instance are different representations encountered as the viewer zooms
deeper, but they do not replace canonical identity.

## WorldBuilder

WorldBuilder owns the complete world map, terrain, World Tiers, and source
objects.

A World Tier contains integer World Z positions 0 through 9:

- Z 0 = Layer 1;
- …
- Z 9 = Layer 10.

WorldBuilder is the authoritative source from which Region and Local views are
addressed.

## RegionDefiner — 15°

RegionDefiner is a filtered WorldBuilder view, not a second map engine.

A deed chooses:

- one World Tier;
- exact source X/Y cells from that tier.

Only those coordinates are needed after the deed is claimed. They become the
working table while retaining their WorldBuilder identity.

Regional detail occupies exact hundredths above the integer World Z:

- 0.01–0.09 above World Z 0;
- 1.01–1.09 above World Z 1;
- …
- 9.01–9.09 above World Z 9.

Regional objects remain attached to the map. These hundredths are depth/layer
addresses, not new World Tiers and not independent parallax planes.

The database stores exact integer hundredths (`z100`) rather than using a raw
floating-point decimal as spatial truth.

## Local — 30° object-anchored representation

Local repeats the recursive representation one level deeper while keeping the
same world and Region ancestry.

A Local is defined by selecting one already-placed Region object such as a city,
landmark, ruin, building cluster, ship, fortress, portal, or other local-bearing
object. Local definition does **not** claim another arbitrary set of world cells.

The Local records a stable parent Region ID plus the selected object's stable
identity, asset identity, Region-normalized X/Y footprint, rotation, parent
World Tier, World Z, Region Layer, and exact parent `z100`. The selected object
is therefore the Local's canonical anchor.

Local is presented at **30°**. Unlike RegionDefiner's shallow 15° editing view,
Local may visually express the depth already authored in the Region hierarchy.
That visual separation is representation only; it does not rewrite the Region
object's canonical coordinates.

Future Local-owned detail may occupy a deeper exact address model, but the
implementation must define that storage explicitly rather than infer truth from
display decimals or visual parallax.

## Instance — separate 45° builder

Instance is intentionally different from Region and Local.

When the viewer recurses into a building, landmark, portal, structure, or other
instance-bearing object, the system opens **Instance Builder**: a WorldBuilder-
style interior/world workspace at 45°.

The exterior footprint does not define the possible size of the interior.
A building may contain a room, a dungeon, a city-sized interior, another realm,
or any arbitrarily deep constructed space. Therefore Instance receives its own
internal tier/layer system and canonical transform back to its entrance/parent
object.

Instance Builder is not implemented merely by squeezing more fractional Z into
the outdoor World/Region/Local address.

## Continuous zoom

The intended traversal is:

**WORLD (0° overhead) → REGION (15°) → LOCAL (30°) → INSTANCE BUILDER (45°
when entering an instance-bearing object).**

For World → Region → Local, zoom changes detail and representation while
preserving the same world position.

For entry into Instance, the selected parent object becomes the canonical
portal/anchor into a separately scalable internal spatial system.

Zooming back out must recover:

- the same world;
- the same parent object/cell;
- the same X/Y;
- the same depth provenance;
- the same ownership and permissions.

## Identity and persistence

Objects carry stable identity and parent provenance.

WorldBuilder terrain remains canonical. Region overlays are stored as
region-owned entries in the same WorldBuilder source state. Local definitions
are anchored to selected Region objects and preserve that parent address rather
than creating an unrelated outdoor map truth.

Instance content has its own internal spatial graph but remains anchored to the
canonical parent object that is entered.

Browser caches are recovery/performance layers only.

## Streaming and permissions

A deeper representation receives only the authorized source scope needed for
that view.

A claimed RegionDefiner session receives its selected WorldBuilder cells, not
the whole parent world. A future Local session must follow the same
permission-filtered rule.

Instance Builder receives only the selected instance's authorized interior
graph plus its parent anchor metadata.

## Current implementation boundary

Implemented in RegionDefiner:

- selection of exact WorldBuilder cells on one parent World Tier;
- selected-cell source projection;
- immutable inherited WorldBuilder content;
- editable region-owned overlays;
- integer World Z 0–9;
- regional hundredth layers .01–.09 above each World Z;
- exact integer `z100` storage;
- map-attached/no-independent-parallax regional overlays;
- shared WorldBuilder-source persistence;
- 15° representation.

Implemented in Local staging:

- parent Region chooser with no new-Region/claim action;
- selection of one placed Region object rather than arbitrary map cells;
- stable Local identity anchored to that object's Region identity and coordinates;
- 30° Local representation;
- Local view may expose regional World-Z / Region-Layer depth as parallax while
  RegionDefiner remains map-attached at 15°.

Not yet implemented:

- Local-owned child authoring/persistence above the selected anchor;
- the final exact Local child-depth storage model;
- continuous camera handoff from Region into Local;
- Instance Builder at 45°;
- continuous entrance/exit transitions for arbitrary interiors.

Those later systems should reuse this provenance and coordinate discipline
rather than reintroduce independent copies of the outdoor world.
