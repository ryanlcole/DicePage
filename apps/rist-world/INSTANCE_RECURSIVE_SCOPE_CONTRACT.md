# RIST Instance Recursive Scope Contract

Status: CANONICAL INSTANCE EDITOR DIRECTION
Date: 2026-09-25
Parent authority: [RECURSIVE_SCOPE_EDITOR_CONTRACT.md](RECURSIVE_SCOPE_EDITOR_CONTRACT.md)

## Scope

Instance Builder authors an **INSTANCE** recursive scope at a fixed **45°**
representation.

An Instance is rooted by two stable identities from one Local:

1. a **named marker** chosen from the Local;
2. the **asset touched by that marker**.

The pair is explicit data. Instance creation never infers identity from visual
similarity and never copies Local geometry into a new global coordinate chain.

## Root

The Instance root stores:

- WorldId;
- RegionId;
- LocalId;
- InstanceId;
- MarkerAssetId and MarkerName;
- TouchedAssetId and TouchedAssetName;
- RecursiveScopeFormat = RIST_RECURSIVE_SCOPE_V1;
- ViewDegrees = 45.

The marker and touched asset remain Local-owned references.

## Grid and cells

INSTANCE geometry is a local grid. Every cell has stable identity derived from
InstanceId + column + row.

A cell owns its terrain rules directly. Rules are not represented by invisible
tokens.

Canonical cell state may contain:

- signed ElevationSteps;
- TerrainType;
- MovementCost;
- BlocksMovement;
- BlocksSight;
- Tags;
- Notes.

Elevation is stored only as signed integer steps.

Every 10 elevation steps crosses one parallax distance:

- +10 steps => +1 elevation parallax band;
- -10 steps => -1 elevation parallax band.

The GM measurement preference translates steps for display only. Changing feet,
meters, or units-per-step never changes ElevationSteps.

## Cell surfaces

The top of every cell is a valid asset surface.

When neighboring cells have different elevation, each exposed vertical step on
the higher cell becomes a deterministic asset surface. Surface identity is
derived from:

InstanceId + cell + face + exposed step.

Raised/lowered geometry therefore creates addressable surfaces without spawning
rule tokens.

## Instance assets

Instance-owned placements reference a source asset but receive their own stable
placement identity.

Each placement stores independently:

- cell;
- surface identity;
- Instance Tier;
- visual Layer;
- opacity;
- visibility;
- edit lock;
- linked/group identity;
- permission resource identity.

Tier changes parallax/depth only.

Layer changes ordinary compositing order only.

Tier never participates in normal front/back sorting. Layer is one-based and is
not capped by a legacy 1..9 window.

## Permissions

Permissions remain server-authoritative. Geometry stores only the stable
permission resource identity.

The Instance asset list uses the same GIMP-inspired editing concepts as the
other scopes and exposes one selected principal permission column at a time.

## Persistence

Instance catalog records and Instance map state are persisted separately from
Local maps.

Instance map format:

- RIST_INSTANCE_MAP_V1
- RecursiveScopeFormat = RIST_RECURSIVE_SCOPE_V1
- ViewDegrees = 45

Parent Local content is referenced, never duplicated into Instance truth.

## Campaign boundary

Instance owns geometry and stable cell/surface/placement identities.

Campaign may later attach NPCs, encounters, traps, loot, perception thresholds,
initiative presentation, and interaction rules to those identities. Campaign
does not rewrite Instance geometry.

## Acceptance

1. Create an Instance from a Local named marker + explicit touched asset.
2. Open at 45° with a local grid.
3. Change a cell to positive and negative signed elevation.
4. Verify each 10-step crossing changes the derived elevation parallax band.
5. Change display measurement and verify ElevationSteps is unchanged.
6. Verify exposed vertical surfaces receive deterministic IDs.
7. Edit cell terrain rules without creating hidden rule objects.
8. Place two assets on one Instance Tier and change visual Layer independently.
9. Change Instance Tier without changing Layer.
10. Save/reopen and recover root identities, cells, surfaces, Tier, Layer and
    stable placement IDs.
11. Permission changes never mutate geometry.
12. Campaign can reference Instance IDs later without becoming a geometry
    editor.
