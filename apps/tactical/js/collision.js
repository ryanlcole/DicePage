import {
  GRID_TYPES,
  coordinateFromCell,
  coordinateToIndex,
  isCellInBounds,
  normalizeMapGeometry,
  tileContainsCoordinate
} from "./grid.js";

export const COLLISION_SCHEMA_VERSION = "shaelvien.collision.v1";

const DEFAULT_COLLISION = Object.freeze({
  blocksMovement: false,
  blocksVision: false,
  blocksSound: false,
  blocksProjectile: false,
  blocksReach: false,
  blocksOverhead: false,
  isFloor: false,
  isCeiling: false,
  height: 1,
  heightUnit: "m",
  opacity: 0,
  soundTransmission: 1,
  soundAbsorption: 0,
  openings: []
});

const DEFAULT_SHAPE = Object.freeze({
  type: "tile_footprint",
  anchor: "center",
  width: 1,
  depth: 1,
  height: 1,
  unit: "cell"
});

const CATEGORY_PRESETS = Object.freeze({
  wall: "solid_wall",
  mountain: "solid_wall",
  cliff: "solid_wall",
  water: "floor_hazard",
  door: "open_door",
  window: "window",
  curtain: "curtain",
  bush: "bush",
  forest: "bush",
  tree: "tree",
  table: "table",
  chair: "chair",
  bar: "table",
  chest: "crate",
  crate: "crate",
  barrel: "crate",
  boulder: "solid_wall",
  rock: "crate",
  fence: "closed_door",
  fireplace: "solid_wall",
  shelves: "crate",
  bed: "table",
  player_start: "decorative",
  enemy_start: "decorative",
  trigger_marker: "decorative"
});

export function collisionPresetIdForDefinition(definition) {
  const category = String(definition?.category || definition?.id || "decorative").replace(/\s+/g, "_").toLowerCase();
  return CATEGORY_PRESETS[category] || (definition?.blocked ? "crate" : "decorative");
}

export function collisionPresetIdForEntity(entity) {
  if (entity?.controller === "player" || entity?.faction === "players") return "player";
  if (entity?.controller === "gm" || entity?.faction === "monsters") return "creature";
  return "creature";
}

export function normalizeCollisionRecord(record = {}, fallback = {}) {
  const merged = { ...DEFAULT_COLLISION, ...fallback, ...(record || {}) };
  merged.blocksMovement = Boolean(merged.blocksMovement);
  merged.blocksVision = Boolean(merged.blocksVision);
  merged.blocksSound = Boolean(merged.blocksSound);
  merged.blocksProjectile = Boolean(merged.blocksProjectile);
  merged.blocksReach = Boolean(merged.blocksReach);
  merged.blocksOverhead = Boolean(merged.blocksOverhead);
  merged.isFloor = Boolean(merged.isFloor);
  merged.isCeiling = Boolean(merged.isCeiling);
  merged.height = finiteNumber(merged.height, DEFAULT_COLLISION.height);
  merged.heightUnit = merged.heightUnit || "m";
  merged.opacity = clamp(finiteNumber(merged.opacity, merged.blocksVision ? 1 : 0), 0, 1);
  merged.soundTransmission = clamp(finiteNumber(merged.soundTransmission, merged.blocksSound ? 0.1 : 1), 0, 1);
  merged.soundAbsorption = clamp(finiteNumber(merged.soundAbsorption, merged.blocksSound ? 0.75 : 0), 0, 1);
  merged.openings = Array.isArray(merged.openings) ? merged.openings : [];
  return merged;
}

export function normalizeCollisionShape(shape = {}, fallback = {}) {
  const merged = { ...DEFAULT_SHAPE, ...fallback, ...(shape || {}) };
  const validTypes = new Set(["rectangle", "circle", "polygon", "tile_footprint", "hex_footprint", "line_segment", "doorway", "opening"]);
  merged.type = validTypes.has(merged.type) ? merged.type : DEFAULT_SHAPE.type;
  merged.anchor = merged.anchor || "center";
  merged.width = finiteNumber(merged.width, DEFAULT_SHAPE.width);
  merged.depth = finiteNumber(merged.depth, DEFAULT_SHAPE.depth);
  merged.height = finiteNumber(merged.height, DEFAULT_SHAPE.height);
  merged.unit = merged.unit || "cell";
  return merged;
}

export function presetCollision(presetId, presets = {}) {
  const preset = presets[presetId] || presets.decorative || {};
  return normalizeCollisionRecord(preset.collision || preset, {});
}

export function presetShape(presetId, presets = {}, map = null) {
  const preset = presets[presetId] || presets.decorative || {};
  const footprint = map?.gridType === GRID_TYPES.HEX ? "hex_footprint" : "tile_footprint";
  return normalizeCollisionShape(preset.collisionShape || {}, { type: footprint });
}

export function normalizePlacedTileCollision(tile, definition, presets = {}, map = null) {
  const presetId = tile.collisionPresetId || collisionPresetIdForDefinition(definition);
  const preset = presetCollision(presetId, presets);
  const category = String(definition?.category || definition?.id || "").toLowerCase();
  const explicitBlocked = tile.blocked === true || definition?.blocked === true;
  const doorIsClosed = category === "door" && (tile.blocked === true || tile.metadata?.state === "closed");
  const fallback = {
    ...preset,
    blocksMovement: doorIsClosed ? true : preset.blocksMovement || explicitBlocked,
    blocksVision: doorIsClosed ? true : preset.blocksVision,
    blocksProjectile: doorIsClosed ? true : preset.blocksProjectile || explicitBlocked,
    blocksSound: doorIsClosed ? true : preset.blocksSound,
    opacity: doorIsClosed ? 1 : preset.opacity,
    soundTransmission: doorIsClosed ? 0.35 : preset.soundTransmission,
    soundAbsorption: doorIsClosed ? 0.45 : preset.soundAbsorption
  };
  tile.collisionPresetId = presetId;
  tile.collision = normalizeCollisionRecord(tile.collision, fallback);
  tile.collisionShape = normalizeCollisionShape(tile.collisionShape, presetShape(presetId, presets, map));
  return tile;
}

export function normalizeEntityCollision(entity, presets = {}) {
  const presetId = entity.collisionPresetId || collisionPresetIdForEntity(entity);
  entity.collisionPresetId = presetId;
  entity.collision = normalizeCollisionRecord(entity.collision, presetCollision(presetId, presets));
  entity.collisionShape = normalizeCollisionShape(entity.collisionShape, presetShape(presetId, presets));
  return entity;
}

export function normalizeMapCollision(map, stateOrBundle = {}) {
  if (!map) return map;
  normalizeMapGeometry(map);
  const presets = stateOrBundle.collisionPresets || {};
  const definitions = stateOrBundle.tileDefinitions || {};
  map.placedTiles = Array.isArray(map.placedTiles) ? map.placedTiles : [];
  map.entities = Array.isArray(map.entities) ? map.entities : [];
  map.placedTiles.forEach((tile) => normalizePlacedTileCollision(tile, definitions[tile.definitionId], presets, map));
  map.entities.forEach((entity) => normalizeEntityCollision(entity, presets));
  return map;
}

export function cellBlocksMovement(state, map, coordinates, movingEntityId = null) {
  const index = coordinateToIndex(map, coordinates);
  if (!isCellInBounds(map, coordinateFromCell(map, index.x, index.y))) return true;
  const terrain = terrainCollision(state, map, index);
  if (terrain.blocksMovement) return true;
  for (const tile of map.placedTiles || []) {
    if (tile.visible === false) continue;
    if (!tile.collision?.blocksMovement && !tile.blocked) continue;
    if (tileContainsCoordinate(map, tile, coordinateFromCell(map, index.x, index.y))) return true;
  }
  return (map.entities || []).some((entity) => (
    entity.visible !== false
    && entity.id !== movingEntityId
    && entity.collision?.blocksMovement !== false
    && entity.x === index.x
    && entity.y === index.y
  ));
}

export function cellBlocksVision(state, map, coordinates) {
  const index = coordinateToIndex(map, coordinates);
  if (!isCellInBounds(map, coordinateFromCell(map, index.x, index.y))) return true;
  const terrain = terrainCollision(state, map, index);
  if (terrain.blocksVision || terrain.opacity >= 1) return true;
  return (map.placedTiles || []).some((tile) => (
    tile.visible !== false
    && tile.collision?.blocksVision === true
    && tile.collision?.opacity >= 0.98
    && tileContainsCoordinate(map, tile, coordinateFromCell(map, index.x, index.y))
  ));
}

export function cellVisionOpacity(state, map, coordinates) {
  const index = coordinateToIndex(map, coordinates);
  const values = [terrainCollision(state, map, index).opacity || 0];
  (map.placedTiles || []).forEach((tile) => {
    if (tile.visible === false) return;
    if (tileContainsCoordinate(map, tile, coordinateFromCell(map, index.x, index.y))) values.push(tile.collision?.opacity || 0);
  });
  return clamp(Math.max(...values), 0, 1);
}

export function cellSoundCost(state, map, coordinates) {
  const index = coordinateToIndex(map, coordinates);
  if (!isCellInBounds(map, coordinateFromCell(map, index.x, index.y))) return Infinity;
  const terrain = terrainCollision(state, map, index);
  if (terrain.blocksSound && terrain.soundTransmission <= 0.1) return Infinity;
  let cost = 1 + (terrain.soundAbsorption || 0) * 6 + (terrain.blocksSound ? 10 * (1 - terrain.soundTransmission) : 0);
  for (const tile of map.placedTiles || []) {
    if (tile.visible === false) continue;
    if (!tileContainsCoordinate(map, tile, coordinateFromCell(map, index.x, index.y))) continue;
    const collision = tile.collision || {};
    if (collision.blocksSound && collision.soundTransmission <= 0.1) return Infinity;
    cost += (collision.soundAbsorption || 0) * 4 + (collision.blocksSound ? 7 * (1 - (collision.soundTransmission ?? 0.1)) : 0);
    if (isOpeningCollision(collision)) cost = Math.min(cost, 1.25);
  }
  return cost;
}

export function isOpeningCell(state, map, coordinates) {
  const index = coordinateToIndex(map, coordinates);
  const terrainDefinition = state.tileDefinitions?.[terrainAt(map, index.x, index.y)];
  if (["door", "window", "stairs", "entrance", "exit"].includes(terrainDefinition?.category || terrainDefinition?.id)) return true;
  return (map.placedTiles || []).some((tile) => (
    tile.visible !== false
    && tileContainsCoordinate(map, tile, coordinateFromCell(map, index.x, index.y))
    && (isOpeningCollision(tile.collision) || ["door", "window", "stairs", "entrance", "exit"].includes(state.tileDefinitions?.[tile.definitionId]?.category))
  ));
}

export function isOpeningCollision(collision = {}) {
  return collision.blocksMovement === false
    && collision.blocksVision === false
    && (collision.soundTransmission ?? 1) >= 0.65
    && collision.soundAbsorption <= 0.35;
}

export function terrainAt(map, x, y) {
  const override = map.terrain?.overrides?.find((item) => {
    const ox = Number.isInteger(item.q) ? item.q : item.x;
    const oy = Number.isInteger(item.r) ? item.r : item.y;
    return ox === x && oy === y;
  });
  return override?.definitionId || map.terrain?.default || "grass";
}

export function terrainCollision(state, map, index) {
  const definition = state.tileDefinitions?.[terrainAt(map, index.x, index.y)];
  const presetId = collisionPresetIdForDefinition(definition);
  const preset = presetCollision(presetId, state.collisionPresets || {});
  return normalizeCollisionRecord({}, {
    ...preset,
    blocksMovement: preset.blocksMovement || definition?.blocked === true,
    blocksProjectile: preset.blocksProjectile || definition?.blocked === true
  });
}

export function collisionSummary(target) {
  const c = normalizeCollisionRecord(target?.collision || {});
  const flags = [];
  if (c.blocksMovement) flags.push("movement");
  if (c.blocksVision) flags.push("vision");
  if (c.blocksSound) flags.push("sound");
  if (c.blocksProjectile) flags.push("projectile");
  if (c.blocksReach) flags.push("reach");
  return flags.length ? flags.join(", ") : "non-blocking";
}

function finiteNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
