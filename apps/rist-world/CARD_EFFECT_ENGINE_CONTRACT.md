# Shaelvien / RIST Card Effect Engine Contract

Status: **FOUNDATIONAL / LOCKED**

This contract defines the canonical relationship between cards, powers, joined effects, spatial targeting, representation, perception, and spawned entities in Shaelvien/RIST.

It applies to Roleplay, GameMaster, Character Card Designer, Powers, Encounters, Instances, tactical representation, weather/anomalies, items, feats, conditions, equipment, abilities, spells, summoned entities, and future systems that invoke the same mechanics.

## Core rule

**The card is the effect package.**

A player should not have to hunt through unrelated effect libraries, condition menus, targeting menus, sprite browsers, or calculation screens after choosing a card. A card carries or references the activation, targeting, resolution, joins/effects, representation, spawning, and lifecycle instructions required to use it.

The system may expose progressive choices contained by the card, but those choices resolve the card's authored behavior rather than requiring the player to reconstruct that behavior manually.

## Stable identities

The following identities are distinct and must not be collapsed:

1. **Card Definition** — the authored reusable behavior/template.
2. **Card Instance** — one owned, granted, equipped, prepared, drawn, or otherwise available copy/use of the definition.
3. **Effect Instance** — the runtime consequence created when the card is activated/resolved.
4. **Spawned Entity** — any persistent or temporary entity created by the effect.

Editing a Card Definition does not silently rewrite an Effect Instance that is already active. Runtime values and effect state do not rewrite the card graphic or authored layout.

## Shared joins

GameMasters define required/shared field names in the same way character-card requirements are defined. The displayed GM name becomes the shared relational join used across compatible characters, NPCs, encounters, powers, equipment, conditions, effects, and reports.

Examples include HEALTH, ARMOR, STRENGTH, MOVE, MANA, TOUGHNESS, or any GM-authored term.

The requirement identity remains stable internally so renaming a displayed field does not destroy its relationship. The join provides interoperability; it does not make unrelated fields identical unless the GM explicitly assigns them to the same shared meaning.

Players should not be required to perform cross-sheet lookup or manual difficulty arithmetic when the necessary joins are available.

## Universal effect flow

Cards may use this common pipeline:

```text
Card Definition / Card Instance
        ↓
Activation / Trigger
        ↓
Requirements / Cost
        ↓
Target selection
        ↓
Spatial geometry or entity target
        ↓
Shared join(s)
        ↓
Operation(s)
        ↓
Resolution
        ↓
Outcome
        ↓
Effect Instance
        ↓
Duration / stacking / activation state
        ↓
Effective values and/or spawned entities
        ↓
Authorized perception / representation
```

The engine is source-neutral. A feat, item, condition, spell, power, weapon, weather event, trap, environmental event, or encounter mechanic may use the same joined-effect machinery.

## Activation

A card may declare one or more activation modes, including:

- passive;
- action;
- reaction;
- trigger;
- toggle;
- scheduled/event-driven activation.

Activation state is runtime data. Toggling or expiring an effect does not edit the card artwork or layout.

## Requirements and costs

A card may define requirements or costs including:

- resource expenditure;
- charges, slots, or uses;
- cooldown;
- prerequisite state;
- position/range requirements;
- equipment or inventory requirements;
- concentration/sustain requirements;
- GM-defined custom joined requirements.

The GameMaster may name these concepts according to the active system.

## Targeting

A card may define:

- self;
- one selected target;
- multiple selected targets;
- party/group;
- point;
- object;
- location;
- area;
- path;
- encounter;
- GM-defined target selectors.

**Select Target** attaches the attempt/effect to one or more entities.

**Select Area** creates or selects spatial geometry.

A card may combine both, for example an aura attached to a selected character or a moving anomaly attached to a path.

When a card requiring spatial selection is used, the targeting/grid representation may appear regardless of the current map representation. The canonical target is the selected entity or world/instance geometry, not the screen pixels or hex graphics used to choose it.

## Spatial geometry

Spatial effects are stored as geometry in canonical world/instance coordinates. The map or grid is a representation of that geometry.

Supported geometry may include:

- point;
- cell/hex selection;
- line/ray;
- segment;
- cone;
- circle/disc;
- sphere;
- cylinder;
- box/volume;
- plane/wall;
- chain between targets;
- polygon;
- path;
- moving volume;
- GM-defined geometry.

A sphere is a true X/Y/Z volume. A line/ray may use direction, yaw/pitch, length, and width. Geometry may cross Z levels.

Range may be finite or unbounded within the applicable world/instance authority. Unbounded never means scanning unrelated worlds; it means no additional authored range limit inside the effect's valid spatial scope.

## Spatial perception

Affected cells/hexes are derived from the Effect Instance and current geometry. They are not the authoritative effect itself.

When appropriate, the current grid may flash or otherwise highlight the affected border/area for:

- the GameMaster; and
- users whose authorized perception allows them to perceive that effect.

Hidden effects remain hidden from unauthorized perception even if they mechanically exist.

A persistent/moving effect retains a stable Effect ID. As it moves, grows, shrinks, follows a target, crosses Z, expires, or is dispelled, its geometry is recomputed and its permitted representations update.

## Representation

Every card/effect may provide independent optional representation choices:

- **Sprite** — animated visual/effect representation, including chained sprite sets.
- **Image** — static visual/decal/template.
- **Draw** — authored or runtime drawn representation.
- **None** — mechanically real with no visible representation.

Representation is not truth. Removing or replacing a sprite/image does not silently remove the Effect Instance.

## Joined operations

A card may read or modify one or more shared joins.

Initial operations include:

- add;
- subtract;
- multiply;
- set/override;
- clamp;
- grant;
- remove;
- replace/convert;
- toggle;
- move;
- spawn;
- destroy.

Base/runtime field values remain distinct from calculated effective values.

Effects such as feats, buffs, conditions, equipment, and powers may target another shared field and contribute differences without rewriting the target's stored base value.

## Resolution

Resolution may be:

- automatic;
- roll versus difficulty;
- opposed roll;
- save/defense;
- threshold;
- GameMaster decision/override;
- GM-defined resolver.

An attempted effect can have states such as Ready, Pending, Applied, Rejected, Expired, or Removed.

A roll or GameMaster decision determines whether the proposed change becomes active. The GameMaster may alter an applied amount when the system grants that authority.

## Powers and magic

The internal mechanic is **POWER**, not hard-coded MAGIC.

Magic is one possible GM-named family/category of Power. Other families may include divine, psionic, technique, technology, mutation, alchemy, song, rune, prayer, program, or any GM-defined family.

A Power may define source, family, discipline, resource, cost, availability, target, joined effects, resolution, duration, representation, and spawning. The GameMaster names these concepts according to the active system.

Spells and other Powers use the same card/effect engine rather than a separate magic runtime.

## Duration, activation, and stacking

Effects may be:

- instant;
- persistent;
- active/inactive;
- time-limited;
- turn/round/scene limited;
- concentration/sustain limited;
- attached to a source or target;
- moving along a path.

Stacking policy is authored and may include:

- add;
- intensity stacking;
- duration stacking;
- replace;
- highest/lowest wins;
- exclusive;
- GM-defined behavior.

Counter/removal policy may include expiration, cleanse, dispel, interruption, condition end, resource exhaustion, leaving the area, source destruction, or GameMaster termination.

## Card-contained effects

Cards should carry the effect instructions needed for play.

Examples:

- a weapon card carries its attack targeting, joins, resolution, and optional line/cone geometry;
- a feat card carries its passive or activated joined modifiers;
- a spell/power card carries targeting, costs, joins, resolution, duration, sprite/image/draw representation, and spawning;
- a weather/anomaly card can carry a moving spatial volume/path and chained sprite representation;
- an encounter card can publish joins used by the GameMaster Tracker and difficulty comparison.

The player selects/uses the card and supplies only the choices the card requires.

## Summoning and spawning

**Summon is a spawn effect.**

A summon card may generate a runtime entity whose representations include:

- a map token;
- a Character/NPC card;
- shared join/stat state;
- permissions/ownership;
- duration/lifecycle;
- abilities/cards;
- sprite/image representation.

The token and Character/NPC card are two representations of the **same spawned entity identity**, not manually synchronized independent objects.

A spawned entity may be temporary or persistent. Multiple spawned entities may share a reusable definition while retaining distinct runtime identity and state.

The generalized spawn mechanism may also create:

- objects;
- terrain;
- walls;
- hazards;
- item cards;
- effect cards;
- map geometry;
- other explicitly allowed entity types.

## Instances and encounters

Cards/effects connect to the active Instance through canonical identity and coordinates rather than through one particular map UI.

An Effect Instance records enough context to resolve its scope, including as applicable:

- World;
- Region;
- Local;
- Instance;
- Encounter;
- source entity;
- target entity/entities;
- canonical X/Y/Z geometry;
- Effect ID;
- start/time state.

The same effect may therefore be perceived in different map scales or representations without changing its identity.

## GameMaster reporting

Shared joins provide the bridge between character state, encounter state, and GameMaster reports.

Effective values should be available to reporting while preserving base/current/max values and modifier provenance.

The GameMaster can use common joins to compare characters, parties, NPCs, and encounters without asking players to manually reconcile temporary buffs, feats, conditions, equipment, or powers first.

## Authority

All card use, target selection, state mutation, spawning, visibility, and GameMaster override remain subject to Recursive Authority and applicable content/perception policy.

The client requests an action. Authoritative state changes require validated server-side identity, permissions, rules, and target scope.

## Locked invariants

1. **The card is the effect package.**
2. **Card Definition, Card Instance, Effect Instance, and Spawned Entity are distinct identities.**
3. **Shared GM-named joins connect compatible systems and remove unnecessary manual arithmetic.**
4. **Base values are not silently rewritten by temporary effects; effective values are derived.**
5. **Target geometry is canonical; grids/hexes are representations.**
6. **Spatial effects may use X/Y/Z and may cross representation layers.**
7. **Sprite/image/draw are optional representations, not effect truth.**
8. **Perception controls who sees effect geometry/highlights.**
9. **Summoned token and Character/NPC card represent one spawned entity identity.**
10. **Powers, including Magic, reuse this engine rather than creating a separate runtime.**
11. **Cards carry their own activation/targeting/effect behavior so players do not hunt across unrelated tools during play.**
12. **Changes to these invariants require an explicit contract revision; do not silently reinterpret them.**
