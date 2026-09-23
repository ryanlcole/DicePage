# RegionDefiner Contract

> Governing recursive-world specification: [RECURSIVE_ZOOM_CONTRACT.md](RECURSIVE_ZOOM_CONTRACT.md).
> The current full-world load and client-side deed mask are transitional.
> The approved target is one continuously zoomable world with child-relative
> tier stacks and only selected source tiles delivered after a deed is claimed.

RegionDefiner is derived from WorldBuilder, but it does not become another authority over the world.

## Canonical flow

1. A World ID is selected first.
2. Choosing **RegionDefiner** opens a Region chooser styled like the World chooser. It lists saved regions and a **New** action.
3. Opening a saved region loads its stored Tier, source-world provenance, crop mask and regional map.
4. Choosing **New** opens a full-world preview sourced from the selected world's shared database-backed **WorldBuilder source snapshot**. RegionDefiner does not carry its own hard-coded world-map images: the Tier images, placed images, sprites and labels are called from the map state published by WorldBuilder. Endemar follows the same database source rule as every other world.
5. The New Region preview is swipeable across the three World Tiers. The user selects exactly one Tier. RegionDefiner never uses WorldBuilder's **All Parallax** mode for a new region.
6. After the Tier is selected, RegionDefiner enters selection-only mode: the only contextual keyboard is **Select**. Zoom/camera controls remain available so the user can navigate before choosing cells.
7. The viewer supports **Hex** and **Square** selection grids. Hex is the default for every new region; Square remains available. A new region starts with no selected cells, and at least one tile must be selected before Crop/Save can proceed. The chosen geometry also becomes the placement snap grid for later regional assets.
8. The user selects the region footprint on the 30×30 source grid, then chooses **Crop**. RegionDefiner does not permit the definition to be saved directly from raw selection mode.
9. Crop preview may mask the full parent map **before** claiming. After a deed is approved, the server projects only its selected source cells and applicable source layers; the chosen parent world tier becomes an immutable region base. Private/custom full-world bitmaps require independently addressable source cells before complete regional terrain is available.
10. In crop preview the user names the region. After naming, the contextual deed row contains only **Back** and **Claim Deed** beside the name field; the Tier/tile/grid readouts are removed from this confirmation step.
11. **Claim Deed** stores the region definition for an owner/GM, or submits the same deed footprint as a **Claim Request** when GM approval is required. A malformed legacy region with no selected cells must never produce an all-black mask.
12. A successful editable deed opens the regional WorldBuilder surface with **Region Tier 0** on top of the selected immutable parent world tier. There is no intermediate Build Region step; the owner can add higher child-relative tiers, with editable layers on each. Once saved, remove the selection-grid DOM so it cannot obstruct selection; maintain the deed's exact source cell scope. A request-only user remains unable to edit until GM approval.
13. The selected source world tier and its source layers are immutable in RegionDefiner. RegionDefiner has its own independent child-relative tiers 0–9 and each child tier has layers 0–9. Base-tier objects move with the parent map with no independent parallax; explicitly higher regional tiers may parallax independently.
14. Asset-library filters resolve to REGION assets while RegionDefiner is active. Region-authored items preserve their stable parent world and deed identities and are stored under their own child node in the same canonical world graph (`REGIONMAP#<regionId>` for shared worlds, or owner-scoped encrypted region storage for private worlds). Regional saves cannot overwrite parent WORLDSOURCE.
15. Region metadata retains its selected world tier, exact selected source cells and parent-world ID. Only child-owned objects, on the base or higher regional tiers, can be selected, dragged, altered or deleted. The first tap selects a saved regional object, and the next gesture drags it. A city embedded in a flattened parent raster must be authored as a separate regional asset to edit it independently.

## Representation

RegionDefiner uses a fixed **15° perspective tilt** with a shallow focal point. This may change the apparent viewer silhouette and visual spacing. It is presentation only. World coordinates, World ID, source tiles, scale, Tier, Layer and Z are not changed by the 15° portrayal.

After a claim is saved, the selected-cell mask is used as the visible regional extent and its bounds are fitted to the viewer as the regional full-map representation. The parent-world coordinates and selection mask remain available for provenance. RegionDefiner never treats an entire named world as a region merely because it has a special world identity.

## Claim authority

Selecting a map portion is not equivalent to owning or editing it.

- an owner/GM may claim and build directly within their authority;
- an invited non-owner may select a portion and submit a **Claim Request** when their world claim policy permits it;
- **Blocked** removes the claim action;
- **Restricted** permits requests only inside already-authorized personal/character scopes;
- **Limited** permits requests but the GM chooses the final approved spatial/resource scope;
- **Co-Operative** grants shared ownership of the approved resource while locally protected child resources may retain secrets;
- **Release Ownership** transfers the granting owner's ownership only after exact written approval in a direct authenticated session.

A pending request does not unlock regional building. The GM decision is the authority boundary.

## Canonical-map authority

There is one recursive map truth in the database. WorldBuilder, RegionDefiner, landmark/interior viewers, object viewers, player views and battle instances are permission-filtered windows over that same truth.

- WorldBuilder works on the authorized world/zone portion.
- RegionDefiner works on an authorized region portion.
- Landmark and interior tools recurse into smaller coordinate scopes.
- Objects, players and battle instances remain anchored to canonical parent coordinates.
- A tool may crop, tilt, simplify, hide, or increase detail for presentation; it does not create another authoritative map.
- Regional edits persist as child nodes in the same canonical world graph, with region provenance and permission checks; they never mutate the inherited parent terrain.
- Browser storage is recovery/cache only and is never authoritative map truth.

## Extents

The source viewer remains 30×30 addressable cells for claiming. RegionDefiner applies the same claim/crop/build process to every selected world, including Endemar. Any underlying world-extent or ownership rules remain world-level authority and do not change the RegionDefiner workflow.


## One recursive map

The database stores one recursive spatial truth:

**World → Regions → Landmarks → Interior depth → Objects → Players → Battle instances.**

Every child keeps its parent identity and canonical coordinates. A deeper viewer changes scale and representation, not truth.

Shaelvien is the special performance case: its enormous world may be streamed as **zones**. A zone is a storage/render partition only, not a separate reality. Cross-zone identity and coordinates remain part of the same Shaelvien map.

Region records persist their canonical parent address and normalized X/Y bounds plus Z range so later regional changes can be projected back into higher-level world representations without losing position.

## Permission-filtered knowledge

There are no separate "player maps" that overwrite truth. The server projects the canonical map through permissions.

A GM may reveal a node or a chosen recursion depth to a user, party, or session. Knowledge does not automatically leak between parties. A visitor can attend one session with only that session's revealed map and return later without gaining discoveries made by another party. Party/user/session reveal grants are separate from ownership and edit authority.

The GM may later reveal a changed region upward at different detail levels: for example only a landmark at WORLD view, a road network at REGION view, or full interiors only when the viewer has permission to recurse that far.

## Exact hex territory and city editing

RegionDefiner's 30×30 flat-top hexes use a column-staggered lattice: visible width 22.75 and height 30.5. Displayed claim buttons, deed SVG masks, fitted claim boundaries, object snapping and the server's region edit permission check must resolve the same cell ID. A saved deed retains its original selected-cell IDs: a geometry correction must never silently change ownership, assign another region or grant territory. If a legacy claim is incorrect, its owner must inspect and explicitly request a boundary correction.

The parent world's selected tier is immutable in RegionDefiner. Region-authored city images/sprites/labels are individually editable objects above it. Choosing one in the Select dropdown opens the appropriate editor without another off-screen EDIT action.


## Same-tier image anchoring and complete world reference

An image, city, sprite or label first placed on a world map is an editable layer attached to the currently selected tier; its depth motion is inherited exactly from its parent tier (zero independent parallax). Moving it to a **different tier** in WorldBuilder explicitly enables tier parallax. Returning to its initial tier reattaches it. Existing legacy WorldBuilder layers without a stored parallax mode retain their prior depth representation. RegionDefiner never grants edits to the canonical source or another tier.

Opening a saved deed requests only its source cells and applicable parent source layers. Official Geonaph tiers are indexed into per-cell hex/square WebP images at build time; independently published source tiles are filtered by deed cell and tier. Custom/private parent rasters without source-cell indexing remain an explicit incomplete-index condition, not an invitation to fetch an unauthorized full-world image. Do not silently modify existing deed coordinates or ownership to compensate. Parent terrain and lakes outside the deed stay outside the regional representation.
