import { cellId, coordinateFromCell, coordinateToIndex } from "./grid.js";

export const FOG_STATES = Object.freeze({
  VISIBLE_NOW: "VISIBLE_NOW",
  DISCOVERED_NOT_VISIBLE: "DISCOVERED_NOT_VISIBLE",
  AUDIBLE_ONLY: "AUDIBLE_ONLY",
  UNKNOWN: "UNKNOWN"
});

export function cellKey(map, coordinates) {
  return cellId(map, coordinates);
}

export function ensureKnowledge(state, playerId = state.actorPlayerId, mapId = state.currentMapId) {
  state.playerKnowledge = state.playerKnowledge && typeof state.playerKnowledge === "object"
    ? state.playerKnowledge
    : { discoveredCellsByPlayer: {} };
  state.playerKnowledge.discoveredCellsByPlayer = state.playerKnowledge.discoveredCellsByPlayer || {};
  state.playerKnowledge.discoveredCellsByPlayer[playerId] = state.playerKnowledge.discoveredCellsByPlayer[playerId] || {};
  state.playerKnowledge.discoveredCellsByPlayer[playerId][mapId] = state.playerKnowledge.discoveredCellsByPlayer[playerId][mapId] || [];
  return state.playerKnowledge.discoveredCellsByPlayer[playerId][mapId];
}

export function addDiscoveredCells(state, map, playerId, visibleCellKeys) {
  const known = new Set(ensureKnowledge(state, playerId, map.id));
  visibleCellKeys.forEach((key) => known.add(key));
  const sorted = [...known].sort();
  state.playerKnowledge.discoveredCellsByPlayer[playerId][map.id] = sorted;
  return sorted;
}

export function buildFogByCell(map, visibleCellKeys, audibleCellKeys, discoveredCellKeys) {
  const visible = new Set(visibleCellKeys);
  const audible = new Set(audibleCellKeys);
  const discovered = new Set(discoveredCellKeys);
  const fog = {};
  for (let y = 0; y < map.height; y += 1) {
    for (let x = 0; x < map.width; x += 1) {
      const coordinates = coordinateFromCell(map, x, y);
      const key = cellKey(map, coordinates);
      if (visible.has(key)) fog[key] = FOG_STATES.VISIBLE_NOW;
      else if (discovered.has(key)) fog[key] = FOG_STATES.DISCOVERED_NOT_VISIBLE;
      else if (audible.has(key)) fog[key] = FOG_STATES.AUDIBLE_ONLY;
      else fog[key] = FOG_STATES.UNKNOWN;
    }
  }
  return fog;
}

export function fogStateFor(perception, map, coordinates) {
  if (!perception) return FOG_STATES.UNKNOWN;
  return perception.fogByCell?.[cellKey(map, coordinates)] || FOG_STATES.UNKNOWN;
}

export function isVisibleNow(perception, map, coordinates) {
  return fogStateFor(perception, map, coordinates) === FOG_STATES.VISIBLE_NOW;
}

export function isKnownToPlayer(perception, map, coordinates) {
  const state = fogStateFor(perception, map, coordinates);
  return state === FOG_STATES.VISIBLE_NOW || state === FOG_STATES.DISCOVERED_NOT_VISIBLE || state === FOG_STATES.AUDIBLE_ONLY;
}

export function fogCounts(fogByCell = {}) {
  return Object.values(fogByCell).reduce((counts, state) => {
    counts[state] = (counts[state] || 0) + 1;
    return counts;
  }, {});
}

export function coordinateKeyToIndex(key) {
  const parts = String(key).split(":");
  const type = parts.at(-3);
  if (type === "hex") return { q: Number(parts.at(-2)), r: Number(parts.at(-1)) };
  return { x: Number(parts.at(-2)), y: Number(parts.at(-1)) };
}

export function coordinatesEqual(map, a, b) {
  const ai = coordinateToIndex(map, a);
  const bi = coordinateToIndex(map, b);
  return ai.x === bi.x && ai.y === bi.y;
}
