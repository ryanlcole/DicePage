import { deepClone, recordEvent } from "./state.js";
import { normalizeMapGeometry, coordinateFromCell, coordinateToIndex, isCellInBounds, tileContainsCoordinate } from "./grid.js";
import { normalizeEntityCollision, normalizeMapCollision, normalizePlacedTileCollision, cellBlocksMovement, terrainAt } from "./collision.js";
import { computeVisibleCells, mapDistanceScale, rangeToCells } from "./vision.js";
import { perceivedSoundsForEntity, soundEventPublicView } from "./sound.js";
import { FOG_STATES, addDiscoveredCells, buildFogByCell, cellKey, ensureKnowledge, isVisibleNow } from "./fog.js";

export const PERCEPTION_SCHEMA_VERSION = "shaelvien.perception.v1";

export function normalizePerceptionProfiles(profiles) {
  const records = Array.isArray(profiles?.profiles) ? profiles.profiles : Array.isArray(profiles) ? profiles : [];
  return Object.fromEntries(records.map((profile) => [profile.id, deepClone(profile)]));
}

export function controlledPlayerEntity(state, map = null, playerId = state.actorPlayerId) {
  const targetMap = map || state.maps[state.currentMapId];
  if (!targetMap) return null;
  const selected = targetMap.entities?.find((entity) => entity.id === state.selectedEntityId && entity.controller === "player" && entity.assignedPlayerId === playerId);
  if (selected) return selected;
  return targetMap.entities?.find((entity) => entity.controller === "player" && entity.assignedPlayerId === playerId) || null;
}

export function perceptionProfileForEntity(state, entity) {
  const explicit = entity?.perceptionProfileId;
  const roleDefault = entity?.controller === "player" ? "starter_pc_default" : "creature_default";
  const profile = state.perceptionProfiles?.[explicit] || state.perceptionProfiles?.[roleDefault] || defaultProfile(roleDefault);
  return deepClone(profile);
}

export function computePlayerPerception(state, map = state.maps[state.currentMapId], playerId = state.actorPlayerId, options = {}) {
  normalizeMapGeometry(map);
  normalizeMapCollision(map, state);
  const entity = controlledPlayerEntity(state, map, playerId);
  if (!entity) {
    const fog = buildFogByCell(map, [], [], ensureKnowledge(state, playerId, map.id));
    return emptyPerception(map, playerId, fog);
  }
  normalizeEntityCollision(entity, state.collisionPresets || {});
  const profile = perceptionProfileForEntity(state, entity);
  const origin = perceptionOrigin(map, entity, profile);
  const visibleCells = computeVisibleCells(state, map, origin, profile.vision || {});
  const discovered = options.updateKnowledge === false
    ? ensureKnowledge(state, playerId, map.id)
    : addDiscoveredCells(state, map, playerId, visibleCells);
  const heard = perceivedSoundsForEntity(state, map, entity, profile.hearing || {});
  const audibleCellKeys = new Set(heard.map((item) => item.perceivedSound.markerCellId).filter(Boolean));
  const fogByCell = buildFogByCell(map, visibleCells, audibleCellKeys, discovered);
  const maxRangeCells = maxSensoryRangeCells(map, profile);
  const result = {
    schemaVersion: PERCEPTION_SCHEMA_VERSION,
    mapId: map.id,
    playerId,
    entityId: entity.id,
    origin,
    profileId: profile.id || "inline",
    visionRangeCells: rangeToCells(map, profile.vision?.range ?? 120, profile.vision?.unit),
    hearingRangeCells: rangeToCells(map, profile.hearing?.range ?? 140, profile.hearing?.unit),
    maxRangeCells,
    visibleCellKeys: [...visibleCells].sort(),
    audibleCellKeys: [...audibleCellKeys].sort(),
    discoveredCellKeys: [...discovered].sort(),
    fogByCell,
    perceivedSounds: heard.map(soundEventPublicView)
  };
  state.perception = state.perception && typeof state.perception === "object" ? state.perception : { current: null };
  state.perception.current = result;
  return result;
}

export function maxSensoryRangeCells(map, profile) {
  const vision = rangeToCells(map, profile.vision?.range ?? 0, profile.vision?.unit);
  const hearing = rangeToCells(map, profile.hearing?.range ?? 0, profile.hearing?.unit);
  return Math.max(vision, hearing, 1);
}

export function playerVisibleMapSnapshot(state, map, playerId = state.actorPlayerId) {
  const perception = computePlayerPerception(state, map, playerId, { updateKnowledge: true });
  const visibleNow = new Set(perception.visibleCellKeys);
  const discovered = new Set(perception.discoveredCellKeys);
  const knownOrAudible = new Set([...perception.visibleCellKeys, ...perception.discoveredCellKeys, ...perception.audibleCellKeys]);
  const publicTerrainOverrides = (map.terrain?.overrides || []).filter((item) => {
    const x = Number.isInteger(item.q) ? item.q : item.x;
    const y = Number.isInteger(item.r) ? item.r : item.y;
    return discovered.has(cellKey(map, coordinateFromCell(map, x, y))) || visibleNow.has(cellKey(map, coordinateFromCell(map, x, y)));
  });
  return {
    id: map.id,
    name: map.name,
    category: map.category,
    width: map.width,
    height: map.height,
    tileSize: map.tileSize,
    gridType: map.gridType,
    gridSettings: deepClone(map.gridSettings),
    terrain: {
      default: map.terrain?.default || "grass",
      overrides: deepClone(publicTerrainOverrides)
    },
    fog: {
      states: deepClone(perception.fogByCell),
      visibleCellKeys: deepClone(perception.visibleCellKeys),
      audibleCellKeys: deepClone(perception.audibleCellKeys),
      discoveredCellKeys: deepClone(perception.discoveredCellKeys)
    },
    placedTiles: (map.placedTiles || [])
      .filter((tile) => tile.visible !== false && tile.hiddenFromPlayers !== true && tileCells(tile, map).some((key) => visibleNow.has(key) || discovered.has(key)))
      .map((tile) => {
        const currentlyVisible = tileCells(tile, map).some((key) => visibleNow.has(key));
        return {
          id: tile.id,
          definitionId: tile.definitionId,
          x: tile.x,
          y: tile.y,
          q: tile.q,
          r: tile.r,
          width: tile.width,
          height: tile.height,
          rotation: tile.rotation,
          visible: tile.visible,
          blocked: Boolean(tile.collision?.blocksMovement ?? tile.blocked),
          image: currentlyVisible && tile.image ? deepClone(tile.image) : null,
          childMapId: currentlyVisible && tile.childMapId ? tile.childMapId : null,
          actions: currentlyVisible ? (tile.actions || [])
            .filter((action) => action.allowedActors?.includes("player"))
            .map((action) => ({ id: action.id, label: action.label, type: action.type, timeCost: action.timeCost })) : [],
          metadata: { label: tile.metadata?.label || state.tileDefinitions[tile.definitionId]?.name || tile.definitionId },
          perceptionState: currentlyVisible ? FOG_STATES.VISIBLE_NOW : FOG_STATES.DISCOVERED_NOT_VISIBLE
        };
      }),
    entities: (map.entities || [])
      .filter((entity) => {
        const key = cellKey(map, coordinateFromCell(map, entity.x, entity.y));
        return entity.visible !== false && (visibleNow.has(key) || (entity.controller === "player" && entity.assignedPlayerId === playerId));
      })
      .map((entity) => ({
        id: entity.id,
        name: entity.name,
        controller: entity.controller,
        assignedPlayerId: entity.assignedPlayerId,
        x: entity.x,
        y: entity.y
      })),
    perceivedSounds: deepClone(perception.perceivedSounds),
    dataFilteredByPerception: true,
    knownCellCount: knownOrAudible.size
  };
}

export function legalStartCellsForPlayer(state, map, playerId = state.actorPlayerId) {
  normalizeMapGeometry(map);
  return (map.placedTiles || [])
    .filter((tile) => tile.visible !== false && tile.hiddenFromPlayers !== true && tile.definitionId === "player-start")
    .filter((tile) => !tile.metadata?.allowedPlayerId || tile.metadata.allowedPlayerId === playerId)
    .flatMap((tile) => {
      const cells = [];
      for (let y = 0; y < tile.height; y += 1) {
        for (let x = 0; x < tile.width; x += 1) {
          const cx = tile.x + x;
          const cy = tile.y + y;
          if (!cellBlocksMovement(state, map, coordinateFromCell(map, cx, cy), ownedEntityIdForPlayer(state, map, playerId))) {
            cells.push(coordinateFromCell(map, cx, cy));
          }
        }
      }
      return cells;
    });
}

export function placeOwnedPlayerCharacter(state, map, entityId, coordinates, actor = { role: state.role, playerId: state.actorPlayerId }) {
  if (actor.role !== "player") return { ok: false, message: "Only a player placement request uses this command." };
  normalizeMapGeometry(map);
  const index = coordinateToIndex(map, coordinates);
  if (!isCellInBounds(map, coordinateFromCell(map, index.x, index.y))) return rejectPlacement(state, entityId, "Placement is outside the map.");
  const entity = map.entities.find((item) => item.id === entityId) || map.entities.find((item) => item.controller === "player" && item.assignedPlayerId === actor.playerId);
  if (!entity) return rejectPlacement(state, entityId, "No owned player character is available on this map.");
  if (entity.controller !== "player" || entity.assignedPlayerId !== actor.playerId) return rejectPlacement(state, entityId, "Player cannot place that entity.");
  const legalKeys = new Set(legalStartCellsForPlayer(state, map, actor.playerId).map((cell) => cellKey(map, cell)));
  const target = coordinateFromCell(map, index.x, index.y);
  if (!legalKeys.has(cellKey(map, target))) return rejectPlacement(state, entity.id, "Target is not an authorized player start region.");
  if (cellBlocksMovement(state, map, target, entity.id)) return rejectPlacement(state, entity.id, "Target start cell is blocked.");
  const from = { x: entity.x, y: entity.y };
  entity.x = index.x;
  entity.y = index.y;
  state.selectedEntityId = entity.id;
  computePlayerPerception(state, map, actor.playerId, { updateKnowledge: true });
  recordEvent(state, "pc_placed", { mapId: map.id, entityId: entity.id, from, to: { x: entity.x, y: entity.y }, playerId: actor.playerId });
  return { ok: true, entity };
}

export function visibleForPlayer(state, map, coordinates, playerId = state.actorPlayerId) {
  const perception = computePlayerPerception(state, map, playerId, { updateKnowledge: true });
  return isVisibleNow(perception, map, coordinates);
}

export function perceptionOrigin(map, entity, profile = {}) {
  const index = coordinateToIndex(map, { x: entity.x, y: entity.y });
  const anchor = profile.originAnchor || entity.perceptionOrigin || "center";
  const coordinates = coordinateFromCell(map, index.x, index.y);
  return { ...coordinates, anchor };
}

export function perceptionZoomBounds(map, perception) {
  const radiusCells = Math.max(1, perception?.maxRangeCells || 1);
  const diameterPixels = Math.max(1, radiusCells * 2 * (map.tileSize || 16));
  return { radiusCells, diameterPixels };
}

export function terrainVisibleToPlayer(perception, map, x, y) {
  const key = cellKey(map, coordinateFromCell(map, x, y));
  return perception.fogByCell[key] === FOG_STATES.VISIBLE_NOW || perception.fogByCell[key] === FOG_STATES.DISCOVERED_NOT_VISIBLE;
}

function emptyPerception(map, playerId, fogByCell) {
  return {
    schemaVersion: PERCEPTION_SCHEMA_VERSION,
    mapId: map.id,
    playerId,
    entityId: null,
    origin: null,
    profileId: "none",
    visionRangeCells: 0,
    hearingRangeCells: 0,
    maxRangeCells: 1,
    visibleCellKeys: [],
    audibleCellKeys: [],
    discoveredCellKeys: ensureKnowledge({ playerKnowledge: { discoveredCellsByPlayer: { [playerId]: { [map.id]: [] } } } }, playerId, map.id),
    fogByCell,
    perceivedSounds: []
  };
}

function tileCells(tile, map) {
  const cells = [];
  for (let y = 0; y < tile.height; y += 1) {
    for (let x = 0; x < tile.width; x += 1) {
      cells.push(cellKey(map, coordinateFromCell(map, tile.x + x, tile.y + y)));
    }
  }
  return cells;
}

function ownedEntityIdForPlayer(state, map, playerId) {
  return map.entities.find((entity) => entity.controller === "player" && entity.assignedPlayerId === playerId)?.id || null;
}

function rejectPlacement(state, entityId, reason) {
  recordEvent(state, "pc_placed", { entityId, reason }, { rejected: true, stateChanging: false });
  return { ok: false, message: reason };
}

function defaultProfile(id) {
  return {
    id,
    vision: { range: 120, unit: "ft", arcDeg: 360, requiresLight: true, minimumLight: 0.2, ignoresPartialCover: false },
    hearing: { range: 140, unit: "ft", directionAccuracy: 0.6, distanceAccuracy: 0.5, throughWalls: true }
  };
}
