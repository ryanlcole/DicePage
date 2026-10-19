# Shaelvien Launch Product Freeze — 2026-10-19

Status: PRODUCT DECISION — launch rebuild contract

This document freezes the launch-facing product scope. Historical implementation remains preserved in Git history and the pre-change backup branch. This freeze changes the public/user-facing creation model; it does not declare historical representations false or delete underlying identity, persistence, authority, provenance, or spatial data.

## Launch thesis

Shaelvien launches as a persistent world canvas where documents provide context, images and sprites provide representation, characters provide actors, campaigns describe possible futures, and GameMasters make worlds live.

User-facing world representation is reduced to:

1. Image — static visual representation.
2. Sprite — animated visual representation.
3. Token — image/sprite bound to a character, NPC, creature, vehicle, or other actor.

Tiles are not a launch-facing creation primitive. Existing coordinate, identity, metadata, persistence, asset, authority, and simulation systems may remain underneath the simplified interface where they are still required.

## Controller

### Remember
- Select documents to upload.
- Connect documents and records to contextual/historical keys.
- Initial relationship families include chronology, connected themes, location relevance, people/entities, events, and campaign/world relevance.
- Source material remains source material; ingestion or retrieval does not silently promote it to canon.

### Exist
- Select image, sprite, or token.
- Place it in the world.
- Adjust position, layer, tier, size/scale, rotation, opacity, visibility, lock state, and sprite/token speed or animation rate where applicable.
- Deeper identifiers, metadata, provenance, storage keys, and authority remain implementation details rather than ordinary builder controls.

### Live
- Create and manage characters.
- Character sheets are rules-capable and rules-profile driven rather than hard-wired to one game system.
- Character identity, portrait/token, attributes, abilities/powers, inventory, resources, conditions, relationships, notes, and ownership/control may be represented by the sheet/profile.

### Imagine
- Create world goals.
- Define campaigns and possible/predictive changes.
- Predictions are advisory/possible futures, not automatic world truth.

### Create
- GameMaster and roleplay surface.
- Run play using the world's characters, assets, documents/context, chat, dice/rules interfaces, and GM controls.

## Initial reference worlds

- Ryan / Mine — Endemar: video-game RPG style; may use the existing MMO/simulation systems as needed.
- Ryan / Mine — Geonaph: geography/history/investigation style inspired by location-and-clue educational adventure play; document/context/location relationships are primary.
- Don — Antrasis: tabletop campaign world; Pathfinder-compatible/open rules material plus Don's custom rules only where licensing permits.
- Ken — Naeja: tabletop campaign world; Pathfinder-compatible/open rules material plus Ken's custom rules only where licensing permits.
- Calforth's games: tabletop-first presentation with optional grid, tokens, character sheets, rules references, dice, and GM controls.

World owners/GameMasters manage their own worlds and NPCs unless they explicitly use optional automation. Endemar's richer MMO automation is not a mandatory burden inherited by other worlds.

## Launch-facing removals / demotions

Remove or demote from the ordinary launch World Builder interface:

- Tiles as a primary user-facing creation concept.
- Tile catalogs and tile-specific placement workflows where image/sprite/token placement supersedes them.
- Terrain painting/generation as a required launch workflow.
- Automatic world population or terrain seeding.
- Cartography, Draw, and Lightboard as required primary creation modes.
- Mandatory construction-grid controls during ordinary image/sprite world building.
- Duplicate Library vs Sprite placement pipelines when one placement pipeline can preserve different rendering semantics.
- Controls that expose implementation metadata without helping ordinary placement or play.

Do not destructively erase historical code merely to satisfy this scope. Prefer removing routes/controls from the launch surface, isolating legacy components, or leaving dormant compatibility paths when they are still required for persisted data.

## Preserve underneath

Preserve as needed:

- world identity and ownership
- authentication and world-scoped authority
- X/Y/Z or equivalent canonical spatial addressing
- tier/layer/depth semantics required by persisted worlds
- PlacementId / TypeId / GroupId or equivalent identity/representation separation
- asset provenance and metadata
- persistence, recovery, save/load/publish behavior
- permissions and public/private/GM visibility
- viewer/camera and accessibility/input support
- optional tabletop grids
- MMO/simulation hooks for worlds that opt into them
- ReLiC observation/continuity boundaries

## Rules architecture

Do not make Pathfinder itself the foundational engine. Use a generic rules-profile/character-sheet engine. Any Pathfinder-compatible profile must use only content/branding permitted by the applicable license. Custom Don and Ken rules layer on the generic profile rather than forking the world engine.

## Rebuild priority

1. Preserve current implementation with a dated backup ref.
2. Establish this launch contract on a dedicated rebuild branch.
3. Simplify navigation/controller to Remember / Exist / Live / Imagine / Create.
4. Make one image/sprite/token placement pipeline reliable across touch, mouse, keyboard, and controller input.
5. Make character creation and rules profiles reliable.
6. Make document/context upload and relationship keys reliable.
7. Make Create/roleplay consume those shared systems.
8. Configure the five reference worlds.
9. Verify authentication, persistence, ownership/permissions, mobile viewport, accessibility, and recovery before launch.

## Non-goals for launch

Launch does not require a universal new TTRPG ruleset, automatic NPC simulation for every GM, a tile-based terrain editor, procedural terrain, or every historical builder feature to remain exposed.
