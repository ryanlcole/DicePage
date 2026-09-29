# Shaelvien GameMaster Flow Contract

Status: **FOUNDATIONAL UI / AUTHORITY CONTRACT**

This contract records the selection-first Shaelvien GameMaster flow. It separates world identity, spatial selection, representation editing, context, and permission authority so the universal X/Y/left/right control surface does not change semantics accidentally.

## 1. Account-facing Shaelvien world list

The GameMaster world selector is account-scoped.

- Platform owner/admin: Endemar origin, realms owned by the account, **Inspect**, and **Explore**.
- Normal GameMaster: realms owned by the account plus explicitly delegated realms, then **Explore**.
- **Explore** is the entry to the shared MMO map. It shows geometrically open frontier zones even when the account has no token, allows entry into public or otherwise view-authorized zones, and exposes only the names of restricted claimed zones.
- **Claim Deed** is an action inside Explore after an open zone is selected. It remains available after an account already owns a realm when the account has an unspent token.
- **Inspect** is developer/admin access to the same MMO map. It may edit canonical world state without transferring realm ownership, but every committed inspection edit requires a written reason.
- Inspection reasons are append-only audit evidence. A later map save must preserve earlier inspection-audit entries rather than replacing them.

The currently selected realm establishes the root world context for everything below it.

## 2. Explore and Claim Deed topology

Endemar is the Shaelvien origin. Deed expansion is orthogonal.

A new deed is eligible only when its square shares a **flat side** with Endemar or a claimed deed in the frontier. Corner-only contact is never sufficient.

The claim coordinate display is relative to the Endemar origin. Endemar is **0,0**. The viewer may change representation, but the claim graph and canonical cell identity do not.

The MMO deed surface is a single world-level representation. Parallax is not required to decide land ownership.

Zone visibility is explicit canonical metadata:

- **Public** — visible/openable from Explore.
- **Restricted** — Explore shows the zone name, but not its contents unless the current account has explicit access.
- **Open** — unclaimed frontier property space. Open topology is visible even without a token; token ownership determines whether the Claim Deed action is enabled.

Developer Inspect shares this exact map rather than maintaining a second administrative map. Inspect may change zone name or Public/Restricted visibility and may enter the normal world editor with developer authority. Every Inspect commit consumes one reason; a subsequent edit requires a new reason.

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
