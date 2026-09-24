# Shaelvien recursive zoom — governing spatial contract

**Status: canonical design requirement.**

Shaelvien is one persistent spatial world. WorldBuilder, RegionDefiner, Local,
and Instance are different representations encountered as the viewer zooms
deeper, but they do not replace canonical identity.

## Canonical hierarchical address

The authoritative nested vertical address is not one flattened Z number.

Every address may carry:

```text
WorldTier / WorldLayer
RegionTier / RegionLayer
LocalTier / LocalLayer
InstanceTier / InstanceLayer
```

or compactly:

```text
W(T,L) → R(T,L) → L(T,L) → I(T,L)
```

Each Layer is independently 0–9 inside its own Tier. Each Tier may increase
without overwriting the parent level's Tier/Layer pair.

The canonical runtime model is `RistHierarchicalAddress` in
`SpatialAddressModels.cs`.

Legacy values such as Region `z100` may remain as compatibility/projection
indexes for existing renderers and persistence migrations. They are **not** the
complete nested spatial truth and must never replace the hierarchical address.

## WorldBuilder — World address

WorldBuilder owns the complete world map, terrain, World Tier/Layer addressing,
and source objects.

World placement establishes:

- World X/Y;
- World Tier;
- World Layer 0–9.

Region, Local, and Instance addresses are initially zero until the object enters
those child contexts.

## RegionDefiner — 15° Region address

RegionDefiner is a filtered WorldBuilder view, not a second unrelated world.

A deed chooses:

- one World Tier;
- exact source X/Y cells from that tier.

Only those coordinates are needed after the deed is claimed. They become the
working Region table while retaining World identity.

Region-authored content adds its own independent:

- Region Tier;
- Region Layer 0–9.

The current renderer may still project World Layer + Region Layer into `z100`
for visual ordering/readback compatibility. That projection is derived from the
hierarchical address; it does not define Region identity.

Parent World terrain is immutable inside RegionDefiner. Region-owned content may
be moved/resized/edited only under Region authority.

## Local — 30° Region-asset-anchored representation

Local repeats the recursive representation one level deeper while preserving
the same World and Region ancestry.

A Local is defined by selecting one already-placed Region object such as a city,
landmark, ruin, building cluster, ship, fortress, portal, or other
Local-bearing object.

Local definition does **not** claim arbitrary World cells.

### Parent anchor rule

The selected Region object remains a Region object with its original:

- stable object/asset identity;
- Region X/Y footprint;
- World Tier/Layer;
- Region Tier/Layer;
- rotation and provenance.

When that object is opened as a Local, its graphic becomes the locked
**100% × 100% Local base canvas**.

This is a representation change, not an identity rewrite.

### Local coordinate rule

Local-owned placements use a new child coordinate frame:

- Local X/Y are normalized 0–1 inside the selected Region asset;
- Local Tier is independent from Region Tier;
- Local Layer is 0–9 inside the Local Tier.

The system retains a reversible projection from Local X/Y back through the
selected Region anchor into World/Region space. Local editing therefore does
not require the user to manipulate tiny World-normalized coordinates.

A Local child carries parent ancestry plus its own child address:

```text
World X/Y
W(T,L)
R(T,L)
Local X/Y
L(T,L)
```

The Local save format declares `local-anchor-normalized-v2`.

Legacy Local saves that stored child positions directly in World-normalized X/Y
may be migrated into the Local anchor frame on load.

## Instance — 45° Local-asset-anchored representation

Instance follows the same recursive selection rule one level deeper.

An Instance begins from one selected Local object/anchor. That Local object keeps
its Local identity and becomes the locked parent/base representation for the
Instance context.

Instance-owned placements then receive:

- Instance-local X/Y/geometry;
- Instance Tier;
- Instance Layer 0–9.

The canonical ancestry becomes:

```text
World → Region → Local → Instance
W(T,L)  R(T,L)  L(T,L)  I(T,L)
```

Instance may represent interiors, dungeons, ships, portals, nested realms, or
other spaces whose internal size is not limited by the exterior object's
displayed footprint. Its transform back to the Local parent anchor must remain
stable.

The same parent/child rule applies recursively:

- Region selects/claims World source;
- Local selects a Region asset;
- Instance selects a Local asset.

A child editor may never silently mutate its parent asset's authored coordinates
or Tier/Layer address.

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
- editable Region-owned overlays;
- explicit World Tier/Layer + Region Tier/Layer metadata;
- legacy `z100` Region projection for compatibility;
- map-attached/no-independent-parallax regional overlays;
- dedicated RegionMap persistence;
- 15° representation.

Implemented in Local:

- parent Region only; no new World/Region claim action;
- selection of one placed Region object as Local anchor;
- stable Local identity anchored to the Region object's identity/provenance;
- selected Region asset rebased visually to the locked 100% Local canvas;
- Local-normalized child X/Y coordinates;
- reversible Local → Region/World projection metadata;
- explicit Local Tier/Layer 0–9 controls;
- Local-owned image/tile/sprite/label authoring;
- separate LocalMap persistence using `RIST_LOCAL_MAP_V2`;
- legacy World-X/Y Local save migration;
- 30° representation.

Reserved/partially modeled for Instance:

- `InstanceTier` and `InstanceLayer` already exist in
  `RistHierarchicalAddress` and Local persistence;
- Instance must select a Local object as parent anchor;
- selected Local asset becomes the locked Instance base representation;
- Instance children use Instance-local geometry plus `I(T,L)`;
- Instance content must persist separately from Local content while retaining
  complete parent ancestry.

Not yet implemented:

- full Instance Builder UI/runtime;
- continuous camera transition from Local into Instance;
- generalized recursive coordinate transforms beyond Local → parent projection;
- server-authoritative spatial-effect intersection across all nested contexts.

Those systems must extend this hierarchy rather than flattening nested Tier/Layer
pairs into a single Z scalar.
