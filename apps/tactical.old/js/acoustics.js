import { coordinateFromCell, coordinateToIndex, isCellInBounds, normalizeMapGeometry } from "./grid.js";
import { cellKey } from "./fog.js";
import { cellDistance, mapDistanceScale } from "./vision.js";
import { cellSoundCost, isOpeningCell } from "./collision.js";

const NEIGHBORS = Object.freeze([
  { dx: 1, dy: 0 },
  { dx: -1, dy: 0 },
  { dx: 0, dy: 1 },
  { dx: 0, dy: -1 },
  { dx: 1, dy: 1 },
  { dx: -1, dy: -1 }
]);

const HEX_NEIGHBORS = Object.freeze([
  { dx: 1, dy: 0 },
  { dx: 1, dy: -1 },
  { dx: 0, dy: -1 },
  { dx: -1, dy: 0 },
  { dx: -1, dy: 1 },
  { dx: 0, dy: 1 }
]);

export function propagateSound(state, map, soundEvent, listener, hearingProfile = {}) {
  normalizeMapGeometry(map);
  const source = soundEvent.sourcePosition;
  const listenerPosition = { x: listener.x, y: listener.y };
  const maxCells = (Number(hearingProfile.range) || 140) / mapDistanceScale(map);
  const path = acousticPath(state, map, source, listenerPosition, maxCells);
  if (!path.reached) {
    return {
      heard: false,
      reason: "sealed_or_out_of_range",
      totalCost: path.totalCost,
      maxCost: maxCells,
      path: path.path
    };
  }
  if (path.totalCost > maxCells) {
    return {
      heard: false,
      reason: "out_of_range",
      totalCost: path.totalCost,
      maxCost: maxCells,
      path: path.path
    };
  }
  const intensity = Number(soundEvent.intensity ?? 0.8);
  const heardStrength = intensity - path.totalCost / Math.max(1, maxCells * 1.8);
  if (heardStrength < 0.06) {
    return {
      heard: false,
      reason: "attenuated",
      totalCost: path.totalCost,
      maxCost: maxCells,
      path: path.path
    };
  }
  const perceived = perceivedSoundLocation(state, map, path.path, source, listenerPosition, hearingProfile, soundEvent);
  return {
    heard: true,
    soundEventId: soundEvent.soundEventId,
    category: soundEvent.category,
    description: soundEvent.description,
    totalCost: Number(path.totalCost.toFixed(3)),
    maxCost: Number(maxCells.toFixed(3)),
    strength: Number(heardStrength.toFixed(3)),
    path: path.path,
    perceivedSound: perceived
  };
}

export function acousticPath(state, map, sourcePosition, listenerPosition, maxCells) {
  const source = coordinateToIndex(map, sourcePosition);
  const target = coordinateToIndex(map, listenerPosition);
  const start = coordinateFromCell(map, source.x, source.y);
  const goalKey = cellKey(map, coordinateFromCell(map, target.x, target.y));
  const queue = [{ coordinates: start, cost: 0, path: [start] }];
  const best = new Map([[cellKey(map, start), 0]]);
  const limit = Math.max(1, maxCells * 2.2);

  while (queue.length) {
    queue.sort((a, b) => a.cost - b.cost);
    const current = queue.shift();
    const currentKey = cellKey(map, current.coordinates);
    if (currentKey === goalKey) return { reached: true, totalCost: current.cost, path: current.path };
    if (current.cost > limit) continue;

    for (const next of acousticNeighbors(map, current.coordinates)) {
      if (!isCellInBounds(map, next)) continue;
      const stepCost = cellSoundCost(state, map, next);
      if (!Number.isFinite(stepCost)) continue;
      const nextCost = current.cost + stepCost;
      const nextKey = cellKey(map, next);
      if (nextCost >= (best.get(nextKey) ?? Infinity)) continue;
      best.set(nextKey, nextCost);
      queue.push({ coordinates: next, cost: nextCost, path: [...current.path, next] });
    }
  }
  return { reached: false, totalCost: Infinity, path: [] };
}

export function perceivedSoundLocation(state, map, path, source, listenerPosition, profile = {}, soundEvent = {}) {
  const sourceIndex = coordinateToIndex(map, source);
  const listenerIndex = coordinateToIndex(map, listenerPosition);
  let marker = null;
  for (let index = path.length - 1; index >= 0; index -= 1) {
    if (isOpeningCell(state, map, path[index])) {
      marker = path[index];
      break;
    }
  }
  if (!marker) marker = approximateDirectMarker(map, sourceIndex, listenerIndex, profile, soundEvent);
  const mi = coordinateToIndex(map, marker);
  const directionDeg = angleDeg(listenerIndex, mi);
  const estimatedDistance = cellDistance(map, listenerPosition, marker) * mapDistanceScale(map);
  const directionAccuracy = clamp(Number(profile.directionAccuracy ?? 0.6), 0.05, 1);
  const distanceAccuracy = clamp(Number(profile.distanceAccuracy ?? 0.5), 0.05, 1);
  return {
    directionDeg: Number(directionDeg.toFixed(1)),
    directionUncertaintyDeg: Number((28 * (1 - directionAccuracy)).toFixed(1)),
    estimatedDistance: Number(estimatedDistance.toFixed(1)),
    distanceUncertainty: Number((estimatedDistance * (1 - distanceAccuracy)).toFixed(1)),
    markerPosition: map.gridType === "hex" ? { q: mi.x, r: mi.y } : { x: mi.x, y: mi.y },
    markerCellId: cellKey(map, coordinateFromCell(map, mi.x, mi.y)),
    sourceIdentityRevealed: false
  };
}

function acousticNeighbors(map, coordinates) {
  const index = coordinateToIndex(map, coordinates);
  const neighbors = map.gridType === "hex" ? HEX_NEIGHBORS : NEIGHBORS.slice(0, 4);
  return neighbors.map((direction) => coordinateFromCell(map, index.x + direction.dx, index.y + direction.dy));
}

function approximateDirectMarker(map, source, listener, profile, soundEvent) {
  const accuracy = clamp(Number(profile.distanceAccuracy ?? 0.5), 0.05, 1);
  const dx = source.x - listener.x;
  const dy = source.y - listener.y;
  const distance = Math.max(1, Math.hypot(dx, dy));
  const jitter = deterministicJitter(soundEvent.soundEventId || "sound", 0.65 * (1 - accuracy));
  const scale = Math.max(1, distance - jitter);
  const x = Math.round(listener.x + dx / distance * scale);
  const y = Math.round(listener.y + dy / distance * scale);
  return coordinateFromCell(map, clamp(Math.round(x), 0, map.width - 1), clamp(Math.round(y), 0, map.height - 1));
}

function angleDeg(a, b) {
  return (((Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI) % 360) + 360) % 360;
}

function deterministicJitter(value, amount) {
  let hash = 0;
  for (const char of String(value)) hash = ((hash << 5) - hash + char.charCodeAt(0)) | 0;
  return ((Math.abs(hash) % 1000) / 1000) * amount;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
