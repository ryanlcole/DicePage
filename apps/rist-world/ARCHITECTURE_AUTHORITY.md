# Shaelvien / RIST Runtime Authority Map

This file defines ownership boundaries for the current RIST WORLD runtime. The goal is to preserve working systems while removing accidental competition between generations of code.

## Rules

1. **Working behavior is an asset.** Reorganize before rewriting.
2. **One canonical authority per responsibility.** Compatibility code may delegate, but must not independently redefine semantics.
3. **Representation is not identity.** Viewer CSS/JS may change how a world is shown without changing world state.
4. **World state belongs to `WorldSession`.** UI code does not invent world identity.
5. **Production only receives release-gated changes.** Build branches and backup refs remain recoverable.
6. **Third-party code must be license-compatible and attributable.** Shaelvien may optimize open-source/freeware components, but proprietary code is not copied.

## Current Authorities

| Responsibility | Canonical authority | Notes |
| --- | --- | --- |
| World identity / runtime state | `WorldSession*.cs` | Plane, Tier, Layer, role, grid state, pieces, authored terrain, persistence. |
| Default world cube | `WorldSession.DefaultCube.cs` | 30×30 one-mile cells; Ocean 071 implicit terrain. |
| Save / load | `WorldSession.Persistence.cs` | Local/private persistence payload and canonical reset. |
| Map renderer | `Components/WorldMap.razor` | Semantic render order: ocean → viewer grid → authored terrain → labels/dice/pieces. |
| Base map geometry / Ocean 071 | `Components/WorldMap.razor.css` | Square map surface and actual Ocean 071 rendering. |
| World Building visual authority | `wwwroot/css/worldbuilding-p0-authority.css` | Workspace-scoped presentation only. Must not redefine terrain identity. |
| Immersion presentation authority | `Components/ImmersionBuilderWorkspace.razor` | Dedicated studio boundary for Parallax, AR, Spatial Audio, High Resolution Assets, and Haptic Feedback. |
| World coordinate transforms / tile snapping | `wwwroot/world-coordinate-authority.js` | Canonical client→world transform and grid snapping. Legacy `ristWorld.tileDropPoint` delegates to this authority. |
| Coordinate frame labels | `wwwroot/grid-coordinate-system.js` | Viewer coordinate decoration; does not own placement. |
| Map visibility compatibility | `wwwroot/map-visibility-recovery.js` | Legacy recovery behavior; World Building is explicitly protected from old geometry recovery. |
| Workspace composition | `Components/WorkspaceSurface.razor` | World/Campaign/Asset/Roleplay workspace arrangement and control placement. |
| Public launch shell | `Components/PublicAlphaShell.razor` | Product workspace entry surface. |
| Build/release checks | `.github/workflows/public-alpha-ci.yml` | Release gate for functional launcher/worldbuilder and coordinate authority. |
| AWS production deployment | `.github/workflows/deploy-rist-frontend-aws.yml` | Deploys only from `live-alpha-rist-blazor-world`. |

## World Building Contract

The P0 worldbuilder must satisfy all of these simultaneously:

- one square authored world surface;
- 30 columns × 30 rows = 900 addressable one-mile cells;
- Ocean 071 is implicit base terrain and does not create 900 save records;
- the viewer grid is independent from terrain;
- authored terrain is sparse above the ocean;
- tile placement snaps in **world coordinates after pan/zoom inversion**;
- Plane/Tier/Layer remain world-state coordinates, not viewport tricks;
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
