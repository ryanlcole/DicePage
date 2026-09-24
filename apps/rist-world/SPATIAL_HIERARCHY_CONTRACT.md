# Shaelvien / RIST Spatial Hierarchy Contract

Status: **FOUNDATIONAL / LOCKED**

This contract defines how World, Region, Local, and Instance spaces relate to one another.

## Canonical hierarchy

The spatial hierarchy is:

**WORLD → REGION → LOCAL → INSTANCE → ENCOUNTER**

Each child scope inherits the canonical parent position and adds its own vertical/depth address.

The complete nested address is:

- World Tier
- World Layer
- Region Tier
- Region Layer
- Local Tier
- Local Layer
- Instance Tier
- Instance Layer

These are independent tier/layer pairs. A child tier/layer never overwrites its parent tier/layer.

## Canonical X/Y

X/Y identify canonical position in the parent world coordinate system.

Entering Region, Local, or Instance does **not** create a second contradictory world location for the same object. Camera framing, cropping, zooming, and representation angle may change, but canonical position remains stable.

Representation is not truth.

## World

Worldbuilder authors World-scale content.

World content uses:

- World Tier
- World Layer
- canonical X/Y

World remains the root spatial authority.

## Region

A Region is a claimed portion of a World.

Region content inherits its World address and adds:

- Region Tier
- Region Layer

A Region may add higher-detail assets such as cities, landmarks, structures, terrain details, and other regional objects.

Those placed Region assets may become selectable parent anchors for Local.

## Local

A Local is created from **one selected placed Region asset**.

The user does not create an unrelated free-floating Local claim. In Local Definer:

1. Load the selected Region.
2. Present eligible placed Region objects.
3. User selects one object, such as a city, landmark, structure, cave entrance, harbor, forest feature, or other valid Local anchor.
4. That Region object becomes the locked Local parent/base representation.
5. The camera frames/crops to that selected Region asset so it behaves as the Local working map.
6. The parent object keeps its Region Tier / Region Layer identity.
7. New Local content inherits the parent World + Region address and adds Local Tier / Local Layer.

The Region asset itself does not silently become Local content. It remains the parent Region object being represented at Local scale.

## Local asset selection

Before a Local exists, Local Definer's Select tools operate on eligible Region assets only.

The selector should identify the parent object's Region depth, for example:

`Atsumaritas · rT0 rL3`

Selecting the object may either:

- open the existing Local anchored to that object; or
- create a new Local anchored to it.

A single Region object should not silently create multiple conflicting Local identities.

## Local editing

After the Local is opened, Local Definer exposes the same core asset interaction model used by Worldbuilder / Region Definer:

- Images
- Tiles
- Sprites
- Labels
- Select
- resize handles
- numeric sizing
- movement
- Local Tier / Local Layer controls
- delete where authority permits
- Save

The selected parent Region object is locked.

Newly placed graphics are Local children and receive:

- inherited World Tier / Layer
- inherited Region Tier / Layer
- Local Tier
- Local Layer

## Instance

Instance follows the same recursive rule as Local.

An Instance is created from **one selected placed Local asset**.

The selected Local asset remains a Local object and becomes the locked parent/base representation for the Instance working view.

New Instance content inherits:

- World Tier / Layer
- Region Tier / Layer
- Local Tier / Layer

and adds:

- Instance Tier
- Instance Layer

This is the intended next recursion of the Local implementation.

## Representation angles

Current representation ladder:

- World: 0°
- Region: 15°
- Local: 30°
- Instance: 45°

These are representation choices, not changes to canonical object identity.

## Persistence

Each scope persists separately.

- World source stores World truth.
- Region map stores Region-owned layers.
- Local map stores Local-owned layers.
- Instance map stores Instance-owned layers.

Saving a child scope must not rewrite its parent scope merely because the child displays the parent as its base.

Parent identity/reference is stored with the child.

## Ordering

Renderer ordering must consider the full nested address.

Conceptually:

`World depth → Region depth → Local depth → Instance depth`

The exact rendering scalar is an implementation detail. The persisted tier/layer pairs are authoritative.

## Authority

A user may edit only content they are authorized to edit.

A parent anchor shown inside a child editor is locked by default.

The Local editor cannot mutate its Region parent representation.
The Instance editor cannot mutate its Local parent representation.

Changes to a parent must occur in the corresponding parent editor.

## Locked invariants

1. World → Region → Local → Instance is recursive containment.
2. Region is a World claim.
3. Local is anchored to a placed Region object.
4. Instance is anchored to a placed Local object.
5. Parent objects remain parent objects when viewed at child scale.
6. Child content adds its own tier/layer pair; it does not overwrite parent depth.
7. Canonical X/Y identity remains stable across representation scales.
8. Camera crop/zoom/angle may change without changing canonical identity.
9. Each scope saves its own authored layers separately.
10. Parent representations are locked inside child editors.
11. Local asset selection is restricted to eligible Region objects before Local creation.
12. Instance asset selection is restricted to eligible Local objects before Instance creation.