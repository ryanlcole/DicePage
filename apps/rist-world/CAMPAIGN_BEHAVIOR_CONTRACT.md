# RIST Campaign Behavior Contract

Status: CANONICAL CAMPAIGN BUILDER DIRECTION
Date: 2026-09-25
Parent authority: [RECURSIVE_SCOPE_EDITOR_CONTRACT.md](RECURSIVE_SCOPE_EDITOR_CONTRACT.md)

## Boundary

Campaign Builder is **not** another geometry editor.

World, Region, Local, and Instance own spatial truth. Campaign owns behavior attached
to stable identities produced by those scopes.

Campaign rules reference stable IDs such as:

- world, region, local, or instance identity;
- recursive asset placement identity;
- Instance cell identity;
- Instance surface identity.

Campaign data never becomes the source of X/Y, elevation, Tier, Layer, grid shape,
or visual compositing order.

## Behavior kinds

The first canonical behavior vocabulary is:

- PERCEPTION_THRESHOLD
- CONTEXTUAL_INTERACTION
- TRAP
- ENEMY_TRIGGER
- INITIATIVE_PRESENTATION
- NPC
- LOOT
- ENCOUNTER

Additional behavior kinds may be added without changing map geometry.

## Rule identity

Every rule has its own stable RuleId and references one stable TargetId.

A rule may store:

- Name
- BehaviorKind
- TargetKind
- TargetId
- Threshold
- Trigger
- Action
- PayloadRefId
- Notes
- Enabled

Threshold/trigger/action are behavior semantics only. They must not be interpreted as
hidden geometry.

## Persistence

Campaign behavior is stored separately from map files:

- format: RIST_CAMPAIGN_BEHAVIOR_V1
- world-scoped campaign behavior document
- stable rule IDs
- stable target IDs

Deleting or changing a campaign rule does not rewrite the referenced map/cell/asset.

## Permissions

Permissions remain external/server-authoritative. Campaign behavior may reference
permission-bearing identities, but a rule never embeds credentials or mutates the
geometry permission model.

## Acceptance

1. A rule can target a stable World/Region/Local/Instance/asset/cell/surface ID.
2. Creating/editing/deleting a rule does not alter map geometry.
3. Perception thresholds, traps, enemy triggers, initiative presentation, NPCs,
   loot and encounters are represented as behavior records.
4. Save/reopen preserves RuleId and TargetId.
5. Campaign Builder contains no canonical X/Y, elevation, Tier or Layer fields.
6. Geometry remains owned by the recursive builder that created the target identity.
