# RIST Recursive Scope Editor Contract

Status: CANONICAL EDITOR DIRECTION
Date: 2026-09-25

## 1. Core separation

The editor MUST keep these concepts independent:

- **Layer** = GIMP-style visual composition order inside the current scope.
- **Tier** = Shaelvien parallax/depth distance inside the current scope.
- **Coordinates** = recursive coordinates local to the current scope.
- **View** = scope representation angle; it is not a layer and not a tier.
- **Permissions** = per-asset authority/visibility state; they do not alter geometry.
- **Transparency** = image/pixel composition behavior; it does not alter world identity.

Changing one of these MUST NOT silently mutate the others.

## 2. Shared placed-asset identity

Every placed asset uses one recursive envelope:

- assetId: stable identity.
- scopeId: scope that owns this placement.
- parentAssetId: optional parent asset that anchors a child scope.
- x, y: coordinates local to the current scope.
- viewDegrees: representation angle inherited from scope unless explicitly overridden.
- tier: parallax/depth plane inside current scope.
- layer: visual compositing order inside current tier.
- opacity / transparency / visibility.
- linkedGroupId: optional visual grouping.
- permissionResourceId: stable authority identity.

UI numbering is 1-based for tier/layer. The first asset in a new scope is:
- x = 0
- y = 0
- tier = 1
- layer = 1
- view = scope default.

The first asset defines the scope's local origin. The camera may center it visually without changing canonical x/y.

## 3. GIMP-style layer behavior

Within one scope and tier:

1. Placing an asset that overlaps an existing asset assigns:
   layer = highest overlapping visible layer + 1.
2. Placing an asset with no overlap begins at layer 1 unless the GM explicitly chooses another layer.
3. LAYER + increments layer only.
4. LAYER - decrements layer only, minimum 1.
5. TIER + increments tier only.
6. TIER - decrements tier only, minimum 1.
7. Tier distance drives parallax.
8. Layer order drives compositing.
9. FRONT/BACK is a layer-list operation, never a tier mutation.

The layer panel is GIMP-inspired, not a copy of GIMP code or branding. Each row can expose:
- visible checkbox/eye
- edit/position lock
- asset name
- tier
- layer
- opacity/transparency
- linked-group state
- permission indicators

## 4. Permissions in the layer list

Asset rows are permission-bearing using the existing recursive authority model.

The layer list MAY expose selected principals (user/group) as checkbox columns so a GM can grant or deny visibility/editing without leaving the editor.

Canonical permission semantics remain:
- View
- Edit
- Public
- Deny
- inherited authority where applicable

A checkbox is only a UI projection of server-authoritative permission state.

## 5. Worldbuilder

Scope: WORLD
Default view: 0 degrees (top-down)

- First asset is x=0, y=0, tier=1, layer=1.
- All World assets use WORLD-local coordinates.
- Layer behavior is GIMP-style.
- Tier behavior is Shaelvien parallax.
- Worldbuilder establishes the top recursive coordinate frame.

## 6. Region Definer

Scope: REGION
Default view: 15 degrees

Claiming/deed selection remains the boundary that defines the Region.

After claim:
- Region asset coordinates are local to the Region scope.
- Region tier/layer numbering starts again at 1/1.
- Region tiers/layers DO NOT reuse World tier/layer numbers.
- Region output recursively amends the final World representation.
- Region assets can provide anchors for Local scopes.
- Region graphics enhancements use the same shared asset editor.

## 7. Local Builder

Scope: LOCAL
Default view: 30 degrees

A Local is created from any eligible asset placed in the parent Region.

Opening a Local:
- shows the selected parent Region asset as the Local root/reference,
- hides unrelated Region assets from the authoring view,
- assigns that root local coordinate x=0, y=0,
- starts Local tier/layer numbering at 1/1,
- allows new assets to be built recursively on top of the selected root asset.

Local markers:
- can be placed and named,
- identify landmarks / future Instance anchors,
- retain the asset they touch/intersect as anchorAssetId.

## 8. Instance Builder

Scope: INSTANCE
Default view: 45 degrees

An Instance is opened by selecting a named Local marker.

The Instance:
1. resolves the marker's touching/anchored Local asset,
2. shows that asset as the Instance root,
3. subdivides it into GM-selected square or hex cells,
4. accepts GM-defined X/Y grid maximums,
5. gives each cell independent elevation/depth,
6. allows exposed sides created by elevation separation to receive assets.

Elevation:
- stored as signed height steps,
- each +10 or -10 height steps crosses one parallax distance,
- physical height/depth is displayed using the GM's selected measurement system,
- measurement display does not alter canonical height-step truth.

Instance tile menu:
- rules attach to the TILE/CELL, not to separate rule tokens,
- tile terrain can define allowed/denied character options,
- rules are inherited by occupants unless explicitly overridden.

## 9. Campaign Builder

Campaign Builder overlays gameplay/state objects onto the authored recursive world.

Examples:
- NPCs
- encounters
- traps
- loot
- quests/events
- perception thresholds
- interaction/context thresholds
- pre-emptive enemy strike conditions
- initiative display placement
- other runtime/gameplay rules

Campaign objects reference stable World/Region/Local/Instance asset or cell identities. They do not redefine map geometry.

Example:
- perception >= X reveals object
- interaction = context action
- perception failure may trigger configured pre-emptive strike
- initiative display location is GM-authored campaign presentation state

## 10. Recursive composition

Final world rendering resolves transforms in order:

WORLD asset
  -> REGION scope anchored to World
    -> LOCAL scope anchored to Region asset
      -> INSTANCE scope anchored to Local marker / Local asset
        -> CAMPAIGN objects anchored to any stable scope object/cell

Each scope owns its own:
- x/y
- tier
- layer
- view angle
- permissions
- children

Parent and child identities remain separate.

## 11. Accessibility and mobile

All editor functions must work without precision dragging.

Required:
- tap/click to select without moving
- explicit Move mode
- keyboard/d-pad nudge
- large touch targets
- screen-reader names and state announcements
- layer/tier values editable as controls, not gesture-only
- visibility and permission controls expose checked/unchecked state
- no browser prompt() for required names
- named fields are inline and keyboard accessible

## 12. Migration

Legacy saved objects may contain mixed/0-based tier/layer coordinates.

Migration rules:
- do not overwrite legacy truth in place before successful conversion,
- read legacy data through an adapter,
- write new recursive-scope records with format versioning,
- preserve stable asset identity,
- preserve Region/Local anchor relationships,
- do not infer a child scope from visual equivalence alone.

New canonical format name:
RIST_RECURSIVE_SCOPE_V1
