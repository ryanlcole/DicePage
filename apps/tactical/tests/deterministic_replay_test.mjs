import fs from "node:fs/promises";
import { createGameState, SCENES } from "../js/state.js";
import { findTile, getCurrentMap, getMapPath, moveExplorationEntity, openChildMapFromTile, playerVisibleSnapshot } from "../js/maps.js";
import { processMapEvent } from "../js/triggers.js";
import { activeCombatant, autoResolveEncounterToEnd, executeEncounterAction } from "../js/encounter.js";
import { directMonsterOverride, issueCommanderOrder } from "../js/commander.js";
import { comparableEncounterState, verifyReplayRecord } from "../js/replay.js";

const root = new URL("../", import.meta.url);

async function readJson(relativePath) {
  return JSON.parse(await fs.readFile(new URL(relativePath, root), "utf8"));
}

async function bundle() {
  const tileManifest = await readJson("data/tile_manifest.json");
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
  return { tileManifest, maps, encounters, characters, creatures };
}

const requiredMapFields = [
  "schemaVersion", "id", "name", "category", "parentMapId", "parentTileId", "width", "height", "tileSize",
  "terrain", "placedTiles", "entities", "entryPoints", "exitPoints", "triggers", "permissions", "atmosphere",
  "encounterReferences"
];

const requiredTileFields = [
  "id", "definitionId", "x", "y", "width", "height", "rotation", "visible", "hiddenFromPlayers", "blocked",
  "childMapId", "entryPointId", "actions", "triggers", "encounterId", "metadata"
];

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function schemaChecks(state) {
  Object.values(state.maps).forEach((map) => {
    requiredMapFields.forEach((field) => assert(Object.prototype.hasOwnProperty.call(map, field), `map ${map.id} missing ${field}`));
    map.placedTiles.forEach((tile) => requiredTileFields.forEach((field) => assert(Object.prototype.hasOwnProperty.call(tile, field), `tile ${tile.id} missing ${field}`)));
  });
}

function openTile(state, tileId) {
  const map = getCurrentMap(state);
  const tile = findTile(map, tileId);
  assert(tile, `missing ${tileId}`);
  const result = openChildMapFromTile(state, tile, { role: "gm" });
  assert(result.ok, `open failed ${tileId}: ${result.message || ""}`);
}

function movePlayer(state, direction) {
  const vectors = { right: [1, 0], left: [-1, 0], up: [0, -1], down: [0, 1] };
  const [dx, dy] = vectors[direction];
  const result = moveExplorationEntity(state, "pc-lyra", dx, dy, { role: "player", playerId: "player-a" });
  assert(result.ok, `move failed ${direction}: ${result.message || ""}`);
  processMapEvent(state, "player_enters_tile", { entityId: "pc-lyra", from: result.from, to: result.to, actorRole: "player" });
}

const state = createGameState(await bundle());
state.scene = SCENES.MAP_VIEW;
schemaChecks(state);

openTile(state, "tile-world-city");
openTile(state, "tile-city-block");
openTile(state, "tile-block-tavern");
assert(getMapPath(state).map((item) => item.name).join(" > ") === "World > City > Block > Tavern Main Floor", "breadcrumb path mismatch");

const publicMap = playerVisibleSnapshot(state);
assert(!publicMap.placedTiles.some((tile) => tile.id === "tile-tavern-ambush-trigger"), "hidden trigger leaked into player snapshot");

movePlayer(state, "right");
movePlayer(state, "right");
movePlayer(state, "right");
assert(state.scene === SCENES.ENCOUNTER, "trigger did not launch encounter");
assert(state.activeEncounter.territoryId === "map-tavern-main-floor", "territory context mismatch");

const order = issueCommanderOrder(state, { role: "gm" }, "attack_nearest", { targetId: "pc-lyra" });
assert(order.ok, "commander order failed");
assert(order.queued.length === 3, "ordinary monster queue count mismatch");

const overriddenMonsterId = order.queued[0].entityId;
const direct = directMonsterOverride(state, { role: "gm" }, overriddenMonsterId, "defend");
assert(direct.ok, "direct override failed");
assert(state.activeEncounter.pendingCommanderActions.some((item) => item.entityId === overriddenMonsterId && item.source === "direct_gm"), "override queue missing");

assert(activeCombatant(state).id === "pc-lyra", "first player activation mismatch");
const inspected = executeEncounterAction(state, { role: "player", playerId: "player-a" }, { type: "inspect" });
assert(inspected.ok, "valid player inspect rejected");
assert(activeCombatant(state).timeSpent === 0, "inspect consumed time");
const moved = executeEncounterAction(state, { role: "player", playerId: "player-a" }, { type: "move", direction: "right" });
assert(moved.ok, "valid player move rejected");
assert(activeCombatant(state).timeSpent === 1, "move time cost mismatch");
const invalid = executeEncounterAction(state, { role: "player", playerId: "player-b" }, { type: "defend" });
assert(!invalid.ok, "unauthorized player action accepted");
assert(activeCombatant(state).timeSpent === 1, "invalid action consumed time");
executeEncounterAction(state, { role: "player", playerId: "player-a" }, { type: "move", direction: "right" });
executeEncounterAction(state, { role: "player", playerId: "player-a" }, { type: "defend" });
assert(activeCombatant(state).timeSpent === 4, "chained time cost mismatch");
executeEncounterAction(state, { role: "player", playerId: "player-a" }, { type: "wait" });
assert(state.activeEncounter.activeEntityId !== "pc-lyra", "wait did not advance activation");

const finish = autoResolveEncounterToEnd(state);
assert(finish.ok, "encounter did not complete");
assert(state.replays.length === 1, "replay was not saved");

const replay = state.replays[0];
const liveSnapshot = comparableEncounterState(state.activeEncounter);
const verification = verifyReplayRecord(replay, liveSnapshot);
assert(verification.finalStateHashMatches, "replay final hash mismatch");
assert(verification.repeatHashMatches, "repeat replay hash mismatch");
assert(verification.replayDoesNotMutateLiveState, "replay mutated live state");

const requiredEvents = [
  "map_opened", "child_map_entered", "trigger_activated", "encounter_started", "commander_order_issued",
  "commander_action_generated", "direct_gm_override", "movement", "attack", "defend", "interaction",
  "time_spent", "entity_defeated", "round_ended", "encounter_completed"
];
const eventTypes = new Set([...state.eventLog.map((event) => event.type), ...state.activeEncounter.events.map((event) => event.type)]);
requiredEvents.forEach((type) => assert(eventTypes.has(type), `required event missing ${type}`));

console.log(JSON.stringify({
  ok: true,
  finalStateHash: replay.finalStateHash,
  integrityHash: replay.integrityHash,
  orderedEvents: replay.orderedEvents.length,
  globalEvents: state.eventLog.length,
  verification
}, null, 2));
