import { SCENES, deepClone, recordEvent, pushMessage } from "./state.js";
import { GRID_TYPES, coordinateFromCell, coordinateToIndex, isCellInBounds, normalizeMapGeometry, selectionForCell, tileContainsCoordinate } from "./grid.js";
import { cellBlocksMovement, normalizeMapCollision, normalizePlacedTileCollision } from "./collision.js";
import { playerVisibleMapSnapshot } from "./perception.js";

export const MAP_SCHEMA_VERSION = "shaelvien.map.v2";
export const TILE_SCHEMA_VERSION = "shaelvien.tile.v2";

export function getCurrentMap(state) {
  const map = normalizeMapGeometry(state.maps[state.currentMapId] || state.maps["map-world"]);
  return normalizeMapCollision(map, state);
}

export function getMapPath(state, mapId = state.currentMapId) {
  const path = [];
  let cursor = state.maps[mapId];
  const seen = new Set();
  while (cursor && !seen.has(cursor.id)) {
    path.unshift({ id: cursor.id, name: cursor.name, category: cursor.category });
    seen.add(cursor.id);
    cursor = cursor.parentMapId ? state.maps[cursor.parentMapId] : null;
  }
  return path;
}

export function terrainAt(map, x, y) {
  normalizeMapGeometry(map);
  const override = map.terrain?.overrides?.find((item) => {
    if (map.gridType === GRID_TYPES.HEX) {
      const q = Number.isInteger(item.q) ? item.q : item.x;
      const r = Number.isInteger(item.r) ? item.r : item.y;
      return q === x && r === y;
    }
    return item.x === x && item.y === y;
  });
  return override?.definitionId || map.terrain?.default || "grass";
}

export function setTerrainAt(map, coordinates, definitionId) {
  normalizeMapGeometry(map);
  const index = coordinateToIndex(map, coordinates);
  if (!isCellInBounds(map, coordinateFromCell(map, index.x, index.y))) return false;
  map.terrain = map.terrain || { default: definitionId, overrides: [] };
  map.terrain.overrides = Array.isArray(map.terrain.overrides) ? map.terrain.overrides : [];
  const existing = map.terrain.overrides.find((item) => {
    const x = map.gridType === GRID_TYPES.HEX ? (Number.isInteger(item.q) ? item.q : item.x) : item.x;
    const y = map.gridType === GRID_TYPES.HEX ? (Number.isInteger(item.r) ? item.r : item.y) : item.y;
    return x === index.x && y === index.y;
  });
  if (existing) {
    existing.definitionId = definitionId;
    if (map.gridType === GRID_TYPES.HEX) {
      existing.q = index.x;
      existing.r = index.y;
    } else {
      existing.x = index.x;
      existing.y = index.y;
    }
  } else {
    map.terrain.overrides.push(map.gridType === GRID_TYPES.HEX
      ? { q: index.x, r: index.y, definitionId }
      : { x: index.x, y: index.y, definitionId });
  }
  return true;
}

export function visiblePlacedTiles(map, role) {
  return map.placedTiles.filter((tile) => tile.visible !== false && (role !== "player" || tile.hiddenFromPlayers !== true));
}

export function tileAt(map, x, y, role = "gm") {
  normalizeMapGeometry(map);
  const tiles = role === "player" ? visiblePlacedTiles(map, "player") : map.placedTiles;
  const coordinates = coordinateFromCell(map, x, y);
  for (let index = tiles.length - 1; index >= 0; index -= 1) {
    const tile = tiles[index];
    if (tileContainsCoordinate(map, tile, coordinates)) return tile;
  }
  return null;
}

export function findTile(map, tileId) {
  return map.placedTiles.find((tile) => tile.id === tileId) || null;
}

export function findEntity(map, entityId) {
  return map.entities.find((entity) => entity.id === entityId) || null;
}

export function canEntityEnterCell(state, map, x, y, entityId = null) {
  normalizeMapGeometry(map);
  normalizeMapCollision(map, state);
  return !cellBlocksMovement(state, map, coordinateFromCell(map, x, y), entityId);
}

export function createPlacedTile(state, definitionId, x, y) {
  const map = getCurrentMap(state);
  const definition = state.tileDefinitions[definitionId];
  if (!definition) return null;
  const suffix = `${definitionId}-${Date.now().toString(36)}-${Math.floor(Math.random() * 1000)}`;
  const tile = {
    schemaVersion: TILE_SCHEMA_VERSION,
    id: `tile-${suffix}`,
    definitionId,
    x,
    y,
    width: definition.defaultWidth || 1,
    height: definition.defaultHeight || 1,
    rotation: 0,
    visible: true,
    hiddenFromPlayers: false,
    blocked: definition.blocked === true,
    childMapId: null,
    entryPointId: null,
    actions: [],
    triggers: [],
    encounterId: null,
    image: null,
    metadata: {
      label: definition.name,
      gmNotes: ""
    }
  };
  if (map.gridType === GRID_TYPES.HEX) {
    tile.q = x;
    tile.r = y;
  }
  return normalizePlacedTileCollision(tile, definition, state.collisionPresets || {}, map);
}

export function placeTile(state, definitionId, x, y) {
  const map = getCurrentMap(state);
  const tile = createPlacedTile(state, definitionId, x, y);
  if (!tile) {
    recordEvent(state, "tile_placed", { definitionId, x, y, reason: "unknown definition" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Unknown tile definition." };
  }
  if (x < 0 || y < 0 || x + tile.width > map.width || y + tile.height > map.height) {
    recordEvent(state, "tile_placed", { definitionId, x, y, reason: "out of bounds" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Tile is outside the map." };
  }
  map.placedTiles.push(tile);
  state.selectedTileId = tile.id;
  state.selection = selectionForCell(map, coordinateFromCell(map, x, y));
  recordEvent(state, "tile_placed", { mapId: map.id, tile: deepClone(tile) });
  return { ok: true, tile };
}

export function moveSelectedTile(state, dx, dy) {
  const map = getCurrentMap(state);
  const tile = findTile(map, state.selectedTileId);
  if (!tile) return { ok: false, message: "No tile selected." };
  const nextX = tile.x + dx;
  const nextY = tile.y + dy;
  if (nextX < 0 || nextY < 0 || nextX + tile.width > map.width || nextY + tile.height > map.height) {
    recordEvent(state, "tile_changed", { tileId: tile.id, reason: "out of bounds" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Tile move is outside the map." };
  }
  const from = { x: tile.x, y: tile.y };
  tile.x = nextX;
  tile.y = nextY;
  if (map.gridType === GRID_TYPES.HEX) {
    tile.q = nextX;
    tile.r = nextY;
  }
  state.selection = selectionForCell(map, coordinateFromCell(map, tile.x, tile.y));
  recordEvent(state, "tile_changed", { mapId: map.id, tileId: tile.id, from, to: { x: tile.x, y: tile.y } });
  return { ok: true, tile };
}

export function removeSelectedTile(state) {
  const map = getCurrentMap(state);
  const index = map.placedTiles.findIndex((tile) => tile.id === state.selectedTileId);
  if (index < 0) return { ok: false, message: "No tile selected." };
  const [tile] = map.placedTiles.splice(index, 1);
  state.selectedTileId = null;
  recordEvent(state, "tile_changed", { mapId: map.id, tileId: tile.id, removed: true });
  return { ok: true };
}

export function updateSelectedTile(state, patch) {
  const map = getCurrentMap(state);
  const tile = findTile(map, state.selectedTileId);
  if (!tile) return { ok: false, message: "No tile selected." };
  Object.assign(tile, deepClone(patch));
  recordEvent(state, "tile_changed", { mapId: map.id, tileId: tile.id, patch: deepClone(patch) });
  return { ok: true, tile };
}

export function createChildMapFromSelectedTile(state) {
  const parent = getCurrentMap(state);
  const tile = findTile(parent, state.selectedTileId);
  if (!tile) return { ok: false, message: "No tile selected." };
  const id = `map-custom-${state.nextEventSeq}`;
  const definition = state.tileDefinitions[tile.definitionId];
  const child = normalizeMapGeometry({
    schemaVersion: MAP_SCHEMA_VERSION,
    id,
    name: `${definition?.name || "Tile"} Interior`,
    category: "interior",
    parentMapId: parent.id,
    parentTileId: tile.id,
    width: 10,
    height: 8,
    tileSize: parent.tileSize,
    terrain: { default: "floor", overrides: [] },
    placedTiles: [],
    entities: [],
    entryPoints: [{ id: "entry-from-parent", x: 1, y: 1, label: "Entry", fromMapId: parent.id, fromTileId: tile.id }],
    exitPoints: [{ id: "exit-to-parent", x: 1, y: 1, label: "Exit", targetMapId: parent.id, targetTileId: tile.id }],
    triggers: [],
    permissions: { gm: { canView: true, canEdit: true }, player: { canView: true } },
    atmosphere: { light: "warm", sound: "quiet", gmNotes: "" },
    encounterReferences: []
  });
  state.maps[id] = child;
  tile.childMapId = id;
  tile.entryPointId = "entry-from-parent";
  recordEvent(state, "map_created", { parentMapId: parent.id, parentTileId: tile.id, childMapId: id });
  recordEvent(state, "tile_changed", { mapId: parent.id, tileId: tile.id, patch: { childMapId: id, entryPointId: tile.entryPointId } });
  return { ok: true, map: child, tile };
}

export function openChildMapFromTile(state, tile, actor = { role: state.role }) {
  const map = getCurrentMap(state);
  if (!tile || !tile.childMapId || !state.maps[tile.childMapId]) {
    return { ok: false, message: "No child map is assigned." };
  }
  if (actor.role === "player" && (tile.hiddenFromPlayers || tile.visible === false)) {
    return { ok: false, message: "The child map is not visible to this player." };
  }
  const previousMapId = map.id;
  state.currentMapId = tile.childMapId;
  state.lastValidMapId = state.currentMapId;
  state.selectedTileId = null;
  state.selectedAtlasInstanceId = null;
  state.selection = null;
  state.scene = SCENES.MAP_VIEW;
  recordEvent(state, "map_opened", { mapId: state.currentMapId, fromMapId: previousMapId, viaTileId: tile.id, actorRole: actor.role });
  recordEvent(state, "child_map_entered", { parentMapId: previousMapId, childMapId: state.currentMapId, parentTileId: tile.id, entryPointId: tile.entryPointId, actorRole: actor.role });
  return { ok: true, map: state.maps[state.currentMapId] };
}

export function returnToParentMap(state, actor = { role: state.role }) {
  const map = getCurrentMap(state);
  if (!map.parentMapId || !state.maps[map.parentMapId]) {
    return { ok: false, message: "Current map has no parent." };
  }
  state.currentMapId = map.parentMapId;
  state.lastValidMapId = state.currentMapId;
  state.selectedTileId = map.parentTileId || null;
  state.selectedAtlasInstanceId = map.parentAtlasInstanceId || null;
  const parentMap = state.maps[state.currentMapId];
  const parentTile = parentMap ? findTile(parentMap, state.selectedTileId) : null;
  state.selection = parentMap && parentTile ? selectionForCell(parentMap, coordinateFromCell(parentMap, parentTile.x, parentTile.y)) : null;
  state.scene = SCENES.MAP_VIEW;
  recordEvent(state, "parent_map_returned", { fromMapId: map.id, parentMapId: state.currentMapId, parentTileId: state.selectedTileId, actorRole: actor.role });
  return { ok: true, map: state.maps[state.currentMapId] };
}

export function moveExplorationEntity(state, entityId, dx, dy, actor = { role: state.role, playerId: state.actorPlayerId }) {
  const map = getCurrentMap(state);
  const entity = findEntity(map, entityId);
  if (!entity) return { ok: false, message: "Entity is not on this map." };
  if (actor.role === "player" && (entity.controller !== "player" || entity.assignedPlayerId !== actor.playerId)) {
    recordEvent(state, "movement", { entityId, reason: "unauthorized player control" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Player cannot control that character." };
  }
  const to = { x: entity.x + dx, y: entity.y + dy };
  if (!canEntityEnterCell(state, map, to.x, to.y, entity.id)) {
    recordEvent(state, "movement", { entityId, from: { x: entity.x, y: entity.y }, to, reason: "blocked" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Movement blocked." };
  }
  const from = { x: entity.x, y: entity.y };
  entity.x = to.x;
  entity.y = to.y;
  state.selectedEntityId = entity.id;
  recordEvent(state, "movement", { mapId: map.id, entityId, from, to, actorRole: actor.role });
  return { ok: true, entity, from, to, enteredTile: tileAt(map, to.x, to.y, "gm") };
}

export function playerVisibleSnapshot(state, map = getCurrentMap(state)) {
  normalizeMapGeometry(map);
  normalizeMapCollision(map, state);
  return playerVisibleMapSnapshot(state, map, state.actorPlayerId);
}

export function restoreExplorationAfterEncounter(state) {
  const targetMapId = state.explorationBeforeEncounter?.currentMapId || state.lastValidMapId || "map-world";
  state.currentMapId = state.maps[targetMapId] ? targetMapId : "map-world";
  state.lastValidMapId = state.currentMapId;
  state.activeEncounter = null;
  state.scene = SCENES.MAP_VIEW;
  pushMessage(state, "Returned to exploration.");
}
