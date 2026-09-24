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

## Local — 30° future stage

Local repeats the same idea one representation deeper while keeping the same
world identity and X/Y ancestry.

Local depth occupies tenths across the same World Z range:

- 0.1–0.9;
- 1.1–1.9;
- …
- 9.1–9.9.

Local is presented at 30°. Its implementation must preserve reversible parent
coordinates so zooming out returns to the same region/world location without
drift.

The exact Local storage representation will be specified before implementation;
the conceptual decimal notation must not force floating-point storage.

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

**WORLD → REGION (15°) → LOCAL (30°) → INSTANCE BUILDER (45° when entering an
instance-bearing object).**

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
region-owned entries in the same WorldBuilder source state. Local will extend
that same address model rather than create an unrelated map truth.

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

Not yet implemented:

- Local at 30° using tenths;
- continuous camera handoff from Region into Local;
- Instance Builder at 45°;
- continuous entrance/exit transitions for arbitrary interiors.

Those later systems should reuse this provenance and coordinate discipline
rather than reintroduce independent copies of the outdoor world.
