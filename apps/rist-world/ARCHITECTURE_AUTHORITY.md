# Shaelvien / RIST Runtime Authority Map

This file defines ownership boundaries for the current RIST WORLD runtime. The goal is to preserve working systems while removing accidental competition between generations of code.

## Rules

1. **Working behavior is an asset.** Reorganize before rewriting.
2. **One canonical authority per responsibility.** Compatibility code may delegate, but must not independently redefine semantics.
3. **Representation is not identity.** Viewer CSS/JS may change how a world is shown without changing world state.
4. **World state belongs to `WorldSession`.** UI code does not invent world identity.
5. **Production only receives release-gated changes.** Build branches and backup refs remain recoverable.
6. **Third-party code must be license-compatible and attributable.** Shaelvien may optimize open-source/freeware components, but proprietary code is not copied.
7. **World identity is the persistence boundary.** Account ownership and world identity are related, but they are not the same thing.
8. **World math is absolute; viewer projection is contextual.** One cell is always 1 km × 1 km × 1 km. Parallax, zoom, and cartographic representation never redefine geometric scale.
9. **Layers require support; Tiers establish elevation.** Layer 1 is the base surface of a Tier. Higher Layers are supported stacks inside that Tier. A moved/resized tile that loses its immediate lower-Layer support degrades to the highest valid lower Layer. A Tier is an independent elevation band and does not require a filled Layer stack from lower Tiers.

## Current Authorities

| Responsibility | Canonical authority | Notes |
| --- | --- | --- |
| World identity | `WorldSession.WorldIdentity.cs` | Stable World ID, account relationship, world storage root, and world-scoped browser persistence. |
| World runtime state | `WorldSession*.cs` | Plane, Tier, Layer, role, grid state, pieces, authored terrain, and active world state. |
| Default world cube | `WorldSession.DefaultCube.cs` | 30×30 one-kilometre cells; Ocean 071 implicit terrain. |
| World geometry / projection contract | `WORLD_PROJECTION_CONTRACT.md` | Fixed 1 km³ world cells and the spatial→cartographic representation continuum. |
| WorldBuilder parallax projection | `wwwroot/worldbuilder-projection.js` | Presentation-only altitude parallax and cartographic blending. Never changes authored coordinates or footprint. |
| Save / load | `WorldSession.Persistence.cs` | World-scoped local/private persistence payload, legacy migration, and canonical reset. |
| Map renderer | `Components/WorldMap.razor` | Semantic render order: ocean → viewer grid → authored terrain → labels/dice/pieces. |
| Base map geometry / Ocean 071 | `Components/WorldMap.razor.css` | Square map surface and actual Ocean 071 rendering. |
| World Building visual authority | `wwwroot/css/worldbuilding-p0-authority.css` | Workspace-scoped presentation only. Must not redefine terrain identity. |
| WorldBuilder layer support | `Components/WorldBuilderStudio.Interactions.cs` | Layer support/degradation and independent Tier placement semantics. |
| Immersion presentation authority | `Components/ImmersionBuilderWorkspace.razor` | Dedicated studio boundary for Parallax, AR, Spatial Audio, High Resolution Assets, and Haptic Feedback. |
| World coordinate transforms / tile snapping | `wwwroot/world-coordinate-authority.js` | Canonical client→world transform and grid snapping. Legacy `ristWorld.tileDropPoint` delegates to this authority. |
| Coordinate frame labels | `wwwroot/grid-coordinate-system.js` | Viewer coordinate decoration; does not own placement. |
| Map visibility compatibility | `wwwroot/map-visibility-recovery.js` | Legacy recovery behavior; World Building is explicitly protected from old geometry recovery. |
| Workspace composition | `Components/WorkspaceSurface.razor` | World/Campaign/Asset/Roleplay workspace arrangement and control placement. |
| Public launch shell | `Components/PublicAlphaShell.razor` | Product workspace entry surface. |
| Build/release checks | `.github/workflows/public-alpha-ci.yml` | Release gate for functional launcher/worldbuilder and coordinate authority. |
| AWS production deployment | `.github/workflows/deploy-rist-frontend-aws.yml` | Deploys only from `live-alpha-rist-blazor-world`. |

## World Relationship Contract

The live cloud model is authoritative. A package is an optional snapshot/export representation, not the runtime database.

The canonical relationship is:

`Account → Worlds → World → Plane → Cube → Tier → Layer → Region/Spatial Content`

For the single-world alpha, `WorldSession.CurrentWorldId` identifies the first proof world. Future multi-world support changes which World ID is selected; it does not change the hierarchy beneath a world.

Persistence rules:

- every serialized world save contains its `WorldId`;
- every private AWS world checkpoint lives beneath `worlds/{WorldId}/` inside the authenticated account's private storage;
- browser saves and reset markers are also scoped by World ID;
- legacy single-world account saves may be adopted only when no world-scoped save exists;
- a save naming a different World ID must never be loaded into the active world;
- the legacy AWS object is retained during alpha as a recovery copy after migration;
- world-owned objects inherit world identity through their spatial parent and do not independently redefine World ID;
- account identity answers **who may own/access the world**; World ID answers **which world the data belongs to**.

This structure allows one account to own many worlds later without changing the renderer, coordinate model, Region model, or world-building tools.

## World Building Contract

The P0 worldbuilder must satisfy all of these simultaneously:

- one square authored world surface;
- 30 columns × 30 rows = 900 addressable one-kilometre cells;
- every X/Y/Z cell is exactly 1 km × 1 km × 1 km at every altitude;
- Ocean 071 is implicit base terrain and does not create 900 save records;
- the viewer grid is independent from terrain;
- authored terrain is sparse above the ocean;
- tile placement snaps in **world coordinates after pan/zoom inversion**;
- tile footprint is measured in world cells and does not change with altitude;
- Plane/Tier/Layer remain world-state coordinates, not viewport tricks;
- **Layer 1 is the base working surface of each Tier; Layer 2+ must be supported by overlapping content on the immediately lower Layer of the same Tier;**
- **when a tile moves or changes footprint and loses Layer support, only that tile degrades downward until it reaches the highest supported Layer;**
- **a Tier establishes independent structural elevation and therefore does not require a continuous Layer stack from a lower Tier;**
- close views may use presentation-only parallax so higher-Z objects appear nearer;
- cartographic zoom progressively removes parallax so equal true distances map to equal displayed distances;
- landscape uses surplus horizontal space for World Controls;
- portrait keeps the map usable without changing world geometry;
- save/reload preserves authored state without changing the implicit ocean identity.

## ImmersionBuilder Contract

WorldBuilder defines **what exists**. ImmersionBuilder defines **how the world is experienced**.

The canonical ImmersionBuilder domains are:

1. **Parallax** — derives visual depth from existing world Tier/Layer/Z information without changing spatial identity.
2. **Augmented Reality** — anchors compatible world representations into physical space while preserving world identity and scale.
3. **Spatial Audio** — places ambience, voices, effects, and environmental sound using existing world position and distance.
4. **High Resolution Assets** — selects higher-detail representations for capable devices and viewing conditions without replacing asset identity.
5. **Haptic Feedback** — translates supported boundaries, materials, events, and accessibility cues into touch/controller feedback.

Authority rule: **ImmersionBuilder may read World ID, regions, coordinates, tiers, layers, objects, assets, and events, but it may never redefine them.** Immersion settings attach to the world as presentation data. They do not become world-coordinate authority.

For the first alpha, Parallax is the first functional ImmersionBuilder module. The remaining domains may exist as planned workspace modules until implementation reaches them.

## Refactor Strategy

When duplicate behavior is found:

1. identify which implementation currently carries the correct semantics;
2. establish or confirm the canonical authority;
3. redirect callers to it without changing external contracts;
4. add a behavior test;
5. remove the superseded implementation only after callers are proven migrated;
6. promote through CI and production deployment gates.

This lets Shaelvien become simpler without discarding working code.
