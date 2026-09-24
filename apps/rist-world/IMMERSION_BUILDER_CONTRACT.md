# Shaelvien / RIST ImmersionBuilder Contract

Status: **FOUNDATIONAL / LOCKED**

ImmersionBuilder owns representation handoff while moving through an already-authored world. It does **not** own terrain, Regions, Locals, Instances, objects, coordinates, tier/layer identity, or map truth.

## Canonical sequence

The authored spatial hierarchy remains:

**WORLD → REGION → LOCAL → IMMERSION HANDOFF → INSTANCE**

ImmersionBuilder sits between Local authoring and Instance authoring because it defines how the viewer transitions through the already-existing World, Region, and Local representations before an Instance can inherit that experience.

## Core rule

**WorldBuilder/Region/Local define what exists. ImmersionBuilder defines when representation changes while approaching it.**

A handoff never redefines the parent or child geometry.

## Default behavior

An immersion path starts at fitted World view.

For a selected World → Region → Local destination, the system derives default zoom thresholds from the actual Region and Local footprints:

1. below the first threshold, render the World representation;
2. at/above the World → Region threshold, render the selected Region representation;
3. at/above the Region → Local threshold, render the selected Local representation.

Defaults are starting values, not immutable rules.

## GameMaster authoring

The GameMaster may:

- select a Region;
- optionally select a Local inside that Region;
- start at World fit;
- zoom/pan naturally toward the destination;
- capture the current zoom as **SET REGION SWITCH HERE**;
- continue zooming;
- capture the current zoom as **SET LOCAL SWITCH HERE**;
- focus World, Region, or Local for authoring convenience;
- reset thresholds to footprint-derived defaults;
- save the immersion profile.

The Region → Local threshold must be greater than the World → Region threshold.

## Persistence

An immersion profile is scoped to:

- World ID;
- Region ID;
- optional Local ID.

The profile stores presentation state only, including:

- stable Profile ID;
- World/Region/Local identity;
- World → Region zoom threshold;
- Region → Local zoom threshold;
- destination focus X/Y;
- transition mode;
- update timestamp.

The profile is saved to local fallback storage and, when authenticated, the world database.

## Coordinate rule

Focus coordinates remain canonical world-normalized coordinates.

Region and Local assets retain their own hierarchical depth addresses:

- World tier/layer;
- Region tier/layer;
- Local tier/layer;
- later Instance tier/layer.

Immersion zoom thresholds do not replace or encode those addresses.

## Viewer rule

ImmersionBuilder uses the same canonical viewer/camera used by world authoring where practical.

The camera may zoom or crop. That does not change object identity, ownership, canonical X/Y, or hierarchical tier/layer addresses.

## Runtime handoff

At runtime, the saved threshold determines which authored representation should be active for the current approach path.

A future transition renderer may use cut, crossfade, progressive parallax, or other presentation methods, but representation changes may not silently mutate world truth.

## Instance boundary

Instance authoring comes **after** this transition system.

A future Local → Instance handoff may extend the same profile model, but Instance must not be implemented as a substitute for World → Region → Local immersion transitions.

## Locked invariants

1. ImmersionBuilder is presentation authority, not spatial authority.
2. The default experience begins at World fit.
3. World → Region and Region → Local are explicit zoom handoffs.
4. The GameMaster may capture both thresholds by zooming to the desired point.
5. Default thresholds are derived from the actual selected footprint.
6. Region/Local identity and hierarchical depth remain unchanged by immersion settings.
7. The Region → Local threshold must occur after the World → Region threshold.
8. Profiles are scoped to the selected World/Region/Local path.
9. Instance follows ImmersionBuilder in the authoring sequence.
10. Changes to these invariants require an explicit contract revision.
