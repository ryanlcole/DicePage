# RegionDefiner Contract

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
9. Crop preview immediately hides everything outside the selected footprint and fits that footprint as the full regional-map presentation. This is still a view over canonical world coordinates, not a copied map.
10. In crop preview the user names the region and chooses **Save Region**, or submits a **Claim Request** when GM approval is required.
11. Saving stores the region definition, reapplies the persisted crop, and exposes **Build Region**. A malformed legacy region with no selected cells must never produce an all-black mask.
12. **Build Region** opens the regional asset workflow against that cropped map.
13. Within the active Tier, each of the ten locked World source layers may be independently shown/hidden after the region is saved. Layer visibility never unlocks or mutates WorldBuilder source assets.
14. Asset-library filters resolve to **REGION** assets while RegionDefiner is active. Region-authored items keep region provenance but are written through the canonical world source; there is no second regional map truth.
15. Region metadata is stored under the selected World identity. Authorized regional map edits are written to the canonical database map with region permission checks and must not create an independent terrain copy.

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
- Regional edits write back into the same canonical world truth with region provenance and permission checks.
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
