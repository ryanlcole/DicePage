import fs from "node:fs/promises";
import { createGameState, SCENES } from "../js/state.js";
import { getCurrentMap, playerVisibleSnapshot } from "../js/maps.js";
import { normalizeMapGeometry, coordinateFromCell } from "../js/grid.js";
import { normalizeMapCollision, cellBlocksMovement, cellBlocksVision } from "../js/collision.js";
import { computePlayerPerception, legalStartCellsForPlayer, placeOwnedPlayerCharacter } from "../js/perception.js";
import { emitSoundEvent } from "../js/sound.js";
import { FOG_STATES, cellKey, fogCounts } from "../js/fog.js";

const root = new URL("../", import.meta.url);

async function readJson(relativePath) {
  return JSON.parse(await fs.readFile(new URL(relativePath, root), "utf8"));
}

async function bundle() {
  const tileManifest = await readJson("data/tile_manifest.json");
  const tileAssetRegistry = await readJson("data/assets/tile_asset_registry.json");
  const collisionPresets = await readJson("data/collision_presets.json");
  const perceptionProfiles = await readJson("data/perception_profiles.json");
  const acousticMaterials = await readJson("data/acoustic_materials.json");
  const maps = await Promise.all([
    "data/maps/world.json",
    "data/maps/city.json",
    "data/maps/block.json",
    "data/maps/tavern_exterior.json",
    "data/maps/tavern_main_floor.json",
    "data/maps/tavern_encounter.json"
  ].map(readJson));
  const encounters = [await readJson("data/encounters/tavern_ambush.json")];
  const characters = (await readJson("data/characters/players.json")).characters;
  const creatures = (await readJson("data/creatures/monsters.json")).creatures;
  return { tileManifest, tileAssetRegistry, collisionPresets, perceptionProfiles, acousticMaterials, maps, encounters, characters, creatures };
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function scenarioMap(id, options = {}) {
  const width = options.openField ? 32 : 10;
  const height = options.openField ? 5 : 7;
  const overrides = [];
  const placedTiles = [];
  if (options.openField) {
    placedTiles.push(baseTile("open-field-bush", "bush", 28, 2, false));
  } else {
    for (let y = 0; y < height; y += 1) overrides.push({ x: 5, y, definitionId: "wall" });
    if (options.doorway) overrides[3] = { x: 5, y: 3, definitionId: "door" };
    if (options.closedDoor) {
      overrides[3] = { x: 5, y: 3, definitionId: "floor" };
      placedTiles.push({ ...baseTile("closed-door-test", "door", 5, 3, true), metadata: { label: "Closed Door", state: "closed", gmNotes: "test" } });
    }
  }
  return normalizeMapGeometry({
    schemaVersion: "shaelvien.map.v2",
    id,
    name: id,
    category: "interior",
    parentMapId: null,
    parentTileId: null,
    width,
    height,
    tileSize: 16,
    gridType: "square",
    gridSettings: { square: { columns: width, rows: height, cellWidth: 5, cellHeight: 5, unitSystem: "imperial", distanceUnit: "ft" } },
    terrain: { default: "floor", overrides },
    placedTiles,
    entities: [{ id: "pc-lyra", definitionId: "char-lyra", name: "Lyra", controller: "player", assignedPlayerId: "player-a", x: options.openField ? 0 : 2, y: options.openField ? 2 : 3, visible: true }],
    entryPoints: [],
    exitPoints: [],
    triggers: [],
    permissions: { gm: { canView: true, canEdit: true }, player: { canView: true } },
    atmosphere: { light: "test", sound: "test", gmNotes: "" },
    encounterReferences: []
  });
}

function baseTile(id, definitionId, x, y, blocked = false) {
  return {
    schemaVersion: "shaelvien.tile.v2",
    id,
    definitionId,
    x,
    y,
    width: 1,
    height: 1,
    rotation: 0,
    visible: true,
    hiddenFromPlayers: false,
    blocked,
    childMapId: null,
    entryPointId: null,
    actions: [],
    triggers: [],
    encounterId: null,
    image: null,
    metadata: { label: id, gmNotes: "test" }
  };
}

const state = createGameState(await bundle());
state.scene = SCENES.MAP_VIEW;

Object.values(state.maps).forEach((map) => {
  assert(map.placedTiles.every((tile) => tile.collision && tile.collisionShape), `missing tile collision on ${map.id}`);
  assert(map.entities.every((entity) => entity.collision && entity.collisionShape), `missing entity collision on ${map.id}`);
});

state.currentMapId = "map-tavern-main-floor";
state.role = "player";
state.actorPlayerId = "player-a";
state.selectedEntityId = "pc-lyra";
const tavern = getCurrentMap(state);
const starts = legalStartCellsForPlayer(state, tavern, "player-a");
assert(starts.length >= 1, "no legal player start cells");
const placed = placeOwnedPlayerCharacter(state, tavern, "pc-lyra", starts[0], { role: "player", playerId: "player-a" });
assert(placed.ok, "owned PC placement rejected");
const unauthorized = placeOwnedPlayerCharacter(state, tavern, "pc-lyra", starts[0], { role: "player", playerId: "player-b" });
assert(!unauthorized.ok, "unauthorized PC placement accepted");
assert(cellBlocksMovement(state, tavern, { x: 3, y: 2 }, "pc-lyra"), "table collision did not block movement");
assert(cellBlocksVision(state, tavern, { x: 0, y: 0 }), "wall collision did not block vision");
const publicTavern = playerVisibleSnapshot(state, tavern);
assert(publicTavern.dataFilteredByPerception, "player snapshot was not perception-filtered");
assert(!publicTavern.placedTiles.some((tile) => tile.id === "tile-tavern-ambush-trigger"), "hidden trigger leaked to player");

const openField = normalizeMapCollision(scenarioMap("test-open-field", { openField: true }), state);
state.maps[openField.id] = openField;
state.currentMapId = openField.id;
state.soundEvents = [];
emitSoundEvent(state, {
  soundEventId: "sound-open-field-bush",
  mapId: openField.id,
  sourcePosition: { x: 28, y: 2 },
  intensity: 0.8,
  category: "creature",
  description: "distant movement behind brush"
}, { record: false });
const openPerception = computePlayerPerception(state, openField, "player-a", { updateKnowledge: true });
const openPublic = playerVisibleSnapshot(state, openField);
assert(!openPerception.visibleCellKeys.includes(cellKey(openField, { x: 28, y: 2 })), "vision exceeded 120 ft open-field range");
assert(openPerception.perceivedSounds.length === 1, "open-field sound was not heard at 140 ft");
assert(!openPublic.placedTiles.some((tile) => tile.id === "open-field-bush"), "audible-only bush terrain/object was revealed");

const farSoundState = createGameState(await bundle());
const farMap = normalizeMapCollision(scenarioMap("test-far-sound", { openField: true }), farSoundState);
farSoundState.maps[farMap.id] = farMap;
farSoundState.currentMapId = farMap.id;
emitSoundEvent(farSoundState, {
  soundEventId: "sound-too-far",
  mapId: farMap.id,
  sourcePosition: { x: 31, y: 2 },
  intensity: 0.8,
  category: "creature",
  description: "too distant"
}, { record: false });
const farPerception = computePlayerPerception(farSoundState, farMap, "player-a", { updateKnowledge: true });
assert(farPerception.perceivedSounds.length === 0, "hearing exceeded configured range");

const doorway = normalizeMapCollision(scenarioMap("test-doorway", { doorway: true }), state);
state.maps[doorway.id] = doorway;
state.currentMapId = doorway.id;
state.soundEvents = [];
emitSoundEvent(state, {
  soundEventId: "sound-kitchen-door",
  mapId: doorway.id,
  sourcePosition: { x: 8, y: 3 },
  intensity: 0.9,
  category: "object impact",
  description: "heavy clambering"
}, { record: false });
const doorwayPerception = computePlayerPerception(state, doorway, "player-a", { updateKnowledge: true });
const marker = doorwayPerception.perceivedSounds[0]?.perceivedSound?.markerPosition;
assert(marker?.x === 5 && marker?.y === 3, "hidden-room sound did not redirect to doorway");
assert(!doorwayPerception.visibleCellKeys.includes(cellKey(doorway, { x: 8, y: 1 })), "wall failed to block hidden-room vision");
assert(doorwayPerception.visibleCellKeys.includes(cellKey(doorway, { x: 8, y: 3 })), "open door did not permit line of sight");

const closedDoor = normalizeMapCollision(scenarioMap("test-closed-door", { closedDoor: true }), state);
state.maps[closedDoor.id] = closedDoor;
state.currentMapId = closedDoor.id;
state.soundEvents = [];
const closedDoorPerception = computePlayerPerception(state, closedDoor, "player-a", { updateKnowledge: true });
assert(!closedDoorPerception.visibleCellKeys.includes(cellKey(closedDoor, { x: 8, y: 3 })), "closed door did not block vision");

const sealed = normalizeMapCollision(scenarioMap("test-sealed", { doorway: false }), state);
state.maps[sealed.id] = sealed;
state.currentMapId = sealed.id;
state.soundEvents = [];
emitSoundEvent(state, {
  soundEventId: "sound-sealed-room",
  mapId: sealed.id,
  sourcePosition: { x: 8, y: 3 },
  intensity: 0.7,
  category: "machinery",
  description: "muffled grinding"
}, { record: false });
const sealedPerception = computePlayerPerception(state, sealed, "player-a", { updateKnowledge: true });
assert(sealedPerception.perceivedSounds.length === 0, "sealed room generated false doorway pulse");

const moving = openField.entities[0];
const beforeCounts = fogCounts(openPerception.fogByCell);
moving.x = 31;
moving.y = 2;
const afterMove = computePlayerPerception(state, openField, "player-a", { updateKnowledge: true });
const afterCounts = fogCounts(afterMove.fogByCell);
assert(afterCounts[FOG_STATES.DISCOVERED_NOT_VISIBLE] > 0, "discovered and currently visible states did not diverge");
assert(beforeCounts[FOG_STATES.UNKNOWN] > 0, "unknown cells were not represented");

console.log(JSON.stringify({
  ok: true,
  tavernStartCells: starts.length,
  openField: {
    visibleCells: openPerception.visibleCellKeys.length,
    heard: openPerception.perceivedSounds.length,
    publicTiles: openPublic.placedTiles.length
  },
  doorwayMarker: marker,
  sealedSounds: sealedPerception.perceivedSounds.length,
  fogAfterMove: afterCounts
}, null, 2));
