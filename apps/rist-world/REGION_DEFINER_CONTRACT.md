# RegionDefiner Contract

RegionDefiner is a scoped authoring/view surface over the selected World. It never becomes another map authority.

## Canonical flow

1. A World ID is selected first.
2. Choosing **RegionDefiner** opens the selected World from the shared database-backed WorldBuilder source. Endemar follows the same source rule as every other World.
3. A new Region begins in the full top-down World view. The user does **not** define geography by painting visible grid cells.
4. The user chooses a rough **focus shape** around the area they want to work in. Supported authoring shapes are rectangle, ellipse and freeform/lasso.
5. Choosing **Crop View** focuses the viewer and establishes an edit limit. Crop is presentation/edit scope only: it does not duplicate, cut, fork, flatten, or save another map.
6. Inside that focused World view, the user draws the actual Region border. Border tools are:
   - **Line** — deliberate straight-segment boundaries;
   - **Pencil** — freehand boundaries;
   - **Magic Select** — seeds an editable boundary proposal from the current focus shape so the author can refine or replace it.
7. Choosing **Set Region Border** establishes the Region's geographic/authority boundary over canonical World coordinates.
8. After the border is set, RegionDefiner switches to a fixed **60° regional representation**.
9. The user chooses which World Tiers are visible in the Region view. Tier visibility changes presentation only; it does not remove or mutate source-world data.
10. The user names and saves the Region, or submits a Claim Request when GM approval is required.
11. Saving stores Region authority/view metadata against the selected World identity. The canonical World map remains the only map truth.
12. Once the Region is saved, regional building/editing continues against that same canonical map under Region permissions.
13. Grids are **not** the primary Region geography-definition interface. Grids return when they are useful: tile placement, construction/snap operations, and play/encounter spatial rules.

## Crop and context

A Region crop is a **viewer focus and edit limit**, not a new asset or map.

The rough focus shape should normally extend beyond the final Region border. That surrounding area remains visible context, allowing a viewer near a Region edge to naturally see neighboring terrain, coastlines, mountains, roads, settlements or other Regions when permissions allow it.

The final Region border determines the Region's authority/context boundary. Visibility outside that border is not automatically erased merely because the viewer is inside the Region.

Changing the focus/crop must never silently resize the Region. Crop/focus and Region border are separate concepts.

## Hidden spatial representation

RegionDefiner may compile the authored focus and border into hidden coordinate/cell representations required by persistence, permissions, snapping, compatibility or spatial queries.

Those hidden cells are implementation/storage representation only. They must never force the user to define geography by targeting tiny Square or Hex cells.

The user-authored border and canonical World coordinates remain the semantic Region definition. Grid rendering is deferred until placement or play needs it.

## Representation

RegionDefiner uses:

- top-down World presentation while choosing the rough focus and drawing the border;
- fixed **60°** presentation after the Region border is confirmed;
- author-selected visible Tiers for the resulting Region view;
- a focused view/edit window that may include context outside the final Region boundary.

These are presentation rules. World ID, source assets, coordinates, scale, Tier/Layer identity, Z and canonical parent relationships are not reauthored by the view angle or crop.

## Canonical-map authority

There is one recursive spatial truth in the database. WorldBuilder, RegionDefiner, Local/landmark/interior tools, object viewers, player views and battle instances are permission-filtered windows over that same truth.

- WorldBuilder works on the authorized World/zone portion.
- RegionDefiner works on an authorized Region portion.
- Local and deeper tools recurse into smaller coordinate scopes.
- Objects, players and battle instances remain anchored to canonical parent coordinates.
- A tool may focus, crop, tilt, simplify, hide, reveal, or increase detail for presentation; it does not create another authoritative map.
- Regional edits write through to the same canonical World truth with Region provenance and permission checks.
- Browser storage is recovery/cache only and is never authoritative map truth.

## Claim authority

Selecting or drawing a map portion is not equivalent to owning or editing it.

- an owner/GM may define and build directly within their authority;
- an invited non-owner may define a proposed boundary and submit a **Claim Request** when their World claim policy permits it;
- **Blocked** removes the claim action;
- **Restricted** permits requests only inside already-authorized personal/character scopes;
- **Limited** permits requests but the GM chooses the final approved spatial/resource scope;
- **Co-Operative** grants shared ownership of the approved resource while locally protected child resources may retain secrets;
- **Release Ownership** transfers the granting owner's ownership only after exact written approval in a direct authenticated session.

A pending request does not unlock regional building. The GM decision remains the authority boundary.

## One recursive map

The database stores one recursive spatial truth:

**World → Region → Local → Site/Building → Interior → Tactical/Instance → Object → Container → Contents.**

Every child keeps its parent identity and canonical coordinates. A deeper viewer changes scale, detail, visibility and representation, not truth.

Shaelvien may stream very large Worlds as zones for storage/render performance. A zone is a partition, not a separate reality. Cross-zone identity and coordinates remain part of the same Shaelvien map.

## Permission-filtered knowledge

There are no separate player maps that overwrite truth. The server projects the canonical map through permissions.

A GM may reveal a node or chosen recursion depth to a user, party or session. Knowledge does not automatically leak between parties. A visitor can attend one session with only that session's revealed map and return later without gaining discoveries made by another party. Party/user/session reveal grants are separate from ownership and edit authority.

The GM may later reveal a changed Region upward at different detail levels: for example only a landmark at WORLD view, a road network at REGION view, or full interiors only when the viewer has permission to recurse that far.

## Non-negotiable invariants

- Crop is view/edit scope, never a duplicated map.
- Border is Region authority geometry, separate from crop.
- Region presentation after border confirmation is 60°.
- Visible Tiers are chosen by the author and are presentation only.
- Geography authoring is gridless to the user; grids return for tile placement and play.
- Cursor selection and touch selection are equivalent semantic inputs.
- RegionDefiner never creates an independent terrain/world database.
