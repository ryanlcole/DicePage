# Shaelvien GameMaster Flow Contract

Status: **FOUNDATIONAL UI / AUTHORITY CONTRACT**

This contract records the selection-first Shaelvien GameMaster flow. It separates world identity, spatial selection, representation editing, context, and permission authority so the universal X/Y/left/right control surface does not change semantics accidentally.

## 1. Account-facing Shaelvien world list

The GameMaster world selector is account-scoped.

- Platform owner/admin: Endemar origin, realms owned by the account, **Inspect**, and **Claim Deed**.
- Normal GameMaster: realms owned by the account plus explicitly delegated realms, then **Claim Deed**.
- **Inspect** is administrative/audit access. It does not transfer realm ownership or silently grant edit authority.
- **Claim Deed** remains present even after an account already owns a realm. Its token summary comes from server-authoritative token state.

The currently selected realm establishes the root world context for everything below it.

## 2. Claim Deed topology

Endemar is the Shaelvien origin. Deed expansion is orthogonal.

A new deed is eligible only when its square shares a **flat side** with Endemar or a claimed deed in the frontier. Corner-only contact is never sufficient.

The claim coordinate display is relative to the Endemar origin. Endemar is **0,0**. The viewer may change representation, but the claim graph and canonical cell identity do not.

The MMO deed surface is a single world-level representation. Parallax is not required to decide land ownership.

### Deferred claim actions already reserved by canon

These remain required follow-on actions and must not be silently replaced with generic claiming:

- **Insert Token** for an available unclaimed deed.
- **Bid** for a forfeited deed when bidding is enabled for that deed.
- **Co-GameMaster** to select an existing realm and request authority from its owner.

A bid changes acquisition resolution, not spatial identity. Co-GameMaster access changes permission, not ownership unless an explicit ownership transfer is separately completed.

## 3. GameMaster root after realm selection

After a realm is selected, the two top-level paths are:

- **World Builder**
- **Context**

World Builder defines or changes representation and spatial content. Context describes what is known or asserted about that content.

## 4. World Builder hierarchy

The canonical World Builder tree is:

```
WORLD
REGION
LOCAL
INSTANCE
CAMPAIGN
```

Editing is **selection-first**.

- WORLD may enter Tier/Layer editing after the realm itself is selected.
- REGION must select or create a Region before Tier/Layer editing becomes available.
- LOCAL must first have a selected Region, then select or create a Local before Tier/Layer editing becomes available.
- INSTANCE must first have a selected Region and Local, then select or create an Instance before Tier/Layer editing becomes available.
- Browser/controller Back preserves valid parent selections. Moving upward must not invent or substitute a different parent.

The active lineage is explicit:

```
Shaelvien realm
└─ Region
   └─ Local
      └─ Instance
```

Viewer depth is not edit depth. Zooming or viewing a deeper representation never grants edit authority and never changes the active edit object.

## 5. Context hierarchy

The canonical Context tree is:

```
HISTORY
LORE
TRUTH
```

Context is attached to the active world/spatial lineage but does not redefine its identity, coordinates, Tier, Layer, permissions, or assets.

## 6. Representation depth

Within an explicitly selected World/Region/Local/Instance:

```
TIER
└─ LAYER
```

A placed asset stores both its representation scope and the selected spatial-node identity. Assets created for one Local or Instance must not become another Local or Instance merely because the viewer navigated there.

## 7. Layer editing tree

At Layer scope:

```
ART
SETTINGS
CONTEXT
CAMPAIGN
```

Navigation is semantic, not browser-history based. Forward depth is `TIER → LAYER → ART`; Back reverses that flow as `ART → LAYER → TIER → parent spatial selection`. Saving an Art placement commits the representation but remains on the same Art method so the GameMaster can continue working without being ejected to the deed/start screen.

Art begins from reusable source classes rather than hard-wiring one editor:

```
BLUEPRINTS
IMAGES
TILES
SPRITES
CANVASES
EXISTING...
UPLOAD
NEW
```

A new Blueprint may recurse into CAD categories and CAD tools. Equivalent adapters may be used for image, tile, sprite, canvas, audio, video, or future engines while the universal controller semantics remain stable.

## 8. Permission tree

Permission choices remain recursive authority, not presentation toggles:

```
ONLY YOU
CO-GAMEMASTERS
PLAYERS
PUBLIC

VIEW
EDIT
OWNER
```

The right-side permission controls may display allowed/denied state, but UI color is representation only. Server permission evaluation remains authoritative.

An owner may not reduce their own ownership through an ordinary permission toggle. If ownership is transferred, the recipient becomes the owner and any later demotion/removal of the prior owner must come from valid ownership authority rather than a self-demotion shortcut.

## 9. Authority and persistence

Spatial child identity is persisted beneath the active Shaelvien realm authority record. Region/Local/Instance identity must survive page reload and must be included in authored placement provenance.

The viewer may show ancestor context while editing a descendant, but only the explicitly selected lineage is the target for new edits.

Authentication answers who the person is. Recursive permissions answer what that person may do. Spatial selection answers which object an authorized edit applies to. None of those three concepts may substitute for another.

## 10. Implementation safety

Do not reintroduce a direct jump from **REGION**, **LOCAL**, or **INSTANCE** to Tier/Layer editing. Any future UI, keyboard, touch, controller, gesture, or accessibility adapter must pass through the same explicit selection state.

Do not treat successful deployment as proof of live interaction behavior. Runtime behavior must be exercised separately after deployment.
