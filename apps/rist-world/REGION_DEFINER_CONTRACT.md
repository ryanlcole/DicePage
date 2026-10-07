# REGION DEFINER CONTRACT

Status: authoritative product/implementation contract for Region definition.

## Core separation

World Builder and Region Definer are separate tools with separate jobs.

**World Builder** creates and edits the continuous underlying World:
- World terrain,
- World Tiers and Layers,
- global features,
- canonical World assets and source state.

**Region Definer** does not create another map and does not begin by choosing a Tier or Layer. It defines a bounded authority/edit volume inside the already-existing World.

A Region is therefore:

`Xmin..Xmax × Ymin..Ymax × Tmin..Tmax`

The World underneath remains the same World before, during, and after Region definition.

## Region creation order

### 1. Open the same World top-down

Region Definer consumes the canonical World Builder source. It must not copy, crop, rasterize, fork, or replace World terrain as Region identity.

The permanent square coordinate grid is visible/available as the measuring authority.

The grid is **coordinates, not geography**.

### 2. Define horizontal bounds first

The first Region operation is exactly four horizontal boundaries:
- X minimum,
- X maximum,
- Y minimum,
- Y maximum.

The GM may establish those boundaries by dragging opposite corners or by entering the coordinate values directly.

Rules:
- no Tier prompt yet,
- no Layer prompt yet,
- no hex painting,
- no polygon painting required,
- no crop-as-identity,
- no second terrain map.

Persisted Region identity uses canonical normalized World X/Y bounds. Any cell list retained by older persistence, indexing, permission, or claim code is a **derived compatibility representation**, not semantic Region truth.

### 3. Define vertical extent second

Only after X/Y is confirmed does Region Definer ask for:
- Z minimum Tier,
- Z maximum Tier.

The bounds are inclusive Tier boundaries. Canonical persistence stores their layer-space equivalent as:
- `CanonicalZMin = MinTier × LayersPerTier`,
- `CanonicalZMax = (MaxTier + 1) × LayersPerTier`.

`CanonicalZMax` is therefore an exclusive upper layer boundary.

A Region may span a single Tier or multiple Tiers. Choosing a lower Min Tier and a higher Max Tier allows the Region to extend downward and upward through the World stack without rebuilding any World Tier.

### 4. Confirm volume, then switch to 60°

The Region view remains top-down while X/Y and Z are being defined.

After all six bounds are confirmed, Region representation switches to **60°**.

This camera change is representation only. It does not alter World geometry, World identity, or the canonical Region bounds.

### 5. Dress the Region

After the Region volume exists, the GM adds Region-scale miniature objects inside that volume, such as:
- mountains and rock formations,
- forests, trees, and vegetation,
- structures,
- roads and bridges,
- environmental props and effects.

Region objects are **additive detail** anchored to the canonical World. A World Tier may already contain terrain or a mountain range; Region miniatures add fidelity without replacing or duplicating that World Tier.

World terrain remains the parent context underneath Region objects.

## Local creation

A Local is not created by rebuilding the Region.

The GM selects one or more meaningful Region objects/areas and gives that selection meaning by naming or labeling it. That named selection establishes a Local footprint/perimeter and changes the representation to the Local viewing context.

**Defining meaning creates a Local.**

Local is the next fidelity level. Local-scale content may include:
- character/token-scale pieces,
- finer scenery,
- doors and furniture,
- NPCs,
- lighting,
- animated water,
- wind, smoke, fire, and weather sprites,
- other fine interactive scene detail.

The parent Region miniatures continue to exist as context. They are not rebuilt.

## Instance creation

Instance is the runtime transformation of the authored scene.

Starting play:
- changes the camera/runtime context,
- fixes each player's permitted perspective for that Instance,
- activates appropriate interaction/click commands,
- changes the surface from primarily authoring behavior to playable behavior.

**Starting play creates an Instance.**

## Authoring spine

The primary Region-detail authoring relationship is:

```text
WORLD
  ↓
REGION
X/Y bounds + Z min/max Tier
  ↓
Region miniature objects
  ↓
named selection / meaningful footprint
  ↓
LOCAL
  ↓
Local-scale objects + tokens + effects
  ↓
INSTANCE
player perspectives + interaction commands
```

This authoring spine does not delete other recursive semantic categories such as Site, Room, Object, Container, or Contents. Those may still describe meaning inside the same spatial continuity. They do not replace the World → Region → Local → Instance authoring transition defined here.

## Grid rule

The grid is contextual tooling, never geography identity.

- **World / Region definition:** square coordinate grid gives exact X/Y measurement and bounds.
- **Object placement:** a grid may appear when snapping or measurement is useful.
- **Play:** an appropriate tactical grid may appear when game rules require it.

A GM never has to paint a Region from tiny hexes.

## Canonical persistence

For a Region, semantic spatial authority is:
- `CanonicalMinX`,
- `CanonicalMaxX`,
- `CanonicalMinY`,
- `CanonicalMaxY`,
- `CanonicalZMin`,
- `CanonicalZMax`.

Derived/backward-compatible fields may include:
- selected cell indexes,
- boundary cell indexes,
- `TierIndex` as the minimum Tier compatibility value,
- source layer offsets,
- visible Tier/Layer presentation lists.

Derived representations must never override contradictory canonical XYZ bounds.

## Permission requests

Direct GM/owner Region creation supports the bounded multi-Tier volume contract.

The current older server claim-request transport still represents one Tier plus layer offsets. Until that server authority contract is migrated, claim-only users must not be told that a multi-Tier request was persisted when it was not. The UI must fail transparently or constrain that request rather than silently collapsing a requested volume.

## Prohibited regressions

Do not restore any of these as Region-definition authority:
- World Builder choosing a reference Tier/Layer before Region definition,
- 30×30 hex Region footprint painting,
- rough-focus/crop as Region identity,
- freehand polygon border as required Region identity,
- visible-tier checkboxes standing in for Z volume,
- copied Region terrain maps,
- Region geometry that can drift independently from its canonical World coordinates.

## Recursive rule

**Defining bounds creates a Region.**  
**Defining meaning creates a Local.**  
**Starting play creates an Instance.**
