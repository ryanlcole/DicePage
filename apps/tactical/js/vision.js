import {
  GRID_TYPES,
  coordinateFromCell,
  coordinateToIndex,
  isCellInBounds,
  normalizeMapGeometry,
  roundAxial
} from "./grid.js";
import { cellBlocksVision } from "./collision.js";
import { cellKey } from "./fog.js";

export function mapDistanceScale(map) {
  normalizeMapGeometry(map);
  if (map.gridType === GRID_TYPES.HEX) return Number(map.gridSettings.hex?.radius) || 5;
  return Math.max(Number(map.gridSettings.square?.cellWidth) || 5, Number(map.gridSettings.square?.cellHeight) || 5);
}

export function rangeToCells(map, range, unit = null) {
  const physical = Number(range);
  if (!Number.isFinite(physical) || physical <= 0) return 0;
  return physical / mapDistanceScale(map);
}

export function cellDistance(map, a, b) {
  normalizeMapGeometry(map);
  const ai = coordinateToIndex(map, a);
  const bi = coordinateToIndex(map, b);
  if (map.gridType === GRID_TYPES.HEX) {
    const aq = Number.isInteger(a.q) ? a.q : ai.x;
    const ar = Number.isInteger(a.r) ? a.r : ai.y;
    const bq = Number.isInteger(b.q) ? b.q : bi.x;
    const br = Number.isInteger(b.r) ? b.r : bi.y;
    return (Math.abs(aq - bq) + Math.abs(aq + ar - bq - br) + Math.abs(ar - br)) / 2;
  }
  return Math.hypot(ai.x - bi.x, ai.y - bi.y);
}

export function lineCells(map, from, to) {
  normalizeMapGeometry(map);
  return map.gridType === GRID_TYPES.HEX ? hexLine(map, from, to) : squareLine(map, from, to);
}

export function hasLineOfSight(state, map, from, to, profile = {}) {
  const indexedTo = coordinateToIndex(map, to);
  if (!isCellInBounds(map, coordinateFromCell(map, indexedTo.x, indexedTo.y))) return false;
  const maxCells = rangeToCells(map, profile.range ?? 120, profile.unit);
  if (cellDistance(map, from, to) > maxCells + 0.0001) return false;
  if (!withinArc(map, from, to, profile)) return false;
  const cells = lineCells(map, from, to);
  for (let index = 1; index < Math.max(1, cells.length - 1); index += 1) {
    if (cellBlocksVision(state, map, cells[index])) return false;
  }
  return true;
}

export function computeVisibleCells(state, map, origin, profile = {}) {
  normalizeMapGeometry(map);
  const visible = new Set();
  const maxCells = rangeToCells(map, profile.range ?? 120, profile.unit);
  const oi = coordinateToIndex(map, origin);
  const minX = Math.max(0, Math.floor(oi.x - maxCells - 1));
  const maxX = Math.min(map.width - 1, Math.ceil(oi.x + maxCells + 1));
  const minY = Math.max(0, Math.floor(oi.y - maxCells - 1));
  const maxY = Math.min(map.height - 1, Math.ceil(oi.y + maxCells + 1));
  for (let y = minY; y <= maxY; y += 1) {
    for (let x = minX; x <= maxX; x += 1) {
      const coordinates = coordinateFromCell(map, x, y);
      if (hasLineOfSight(state, map, origin, coordinates, profile)) visible.add(cellKey(map, coordinates));
    }
  }
  return visible;
}

function squareLine(map, from, to) {
  const a = coordinateToIndex(map, from);
  const b = coordinateToIndex(map, to);
  const cells = [];
  const dx = Math.abs(b.x - a.x);
  const dy = Math.abs(b.y - a.y);
  const sx = a.x < b.x ? 1 : -1;
  const sy = a.y < b.y ? 1 : -1;
  let err = dx - dy;
  let x = a.x;
  let y = a.y;
  while (true) {
    cells.push(coordinateFromCell(map, x, y));
    if (x === b.x && y === b.y) break;
    const e2 = err * 2;
    if (e2 > -dy) {
      err -= dy;
      x += sx;
    }
    if (e2 < dx) {
      err += dx;
      y += sy;
    }
  }
  return cells;
}

function hexLine(map, from, to) {
  const a = { q: Number.isInteger(from.q) ? from.q : from.x, r: Number.isInteger(from.r) ? from.r : from.y };
  const b = { q: Number.isInteger(to.q) ? to.q : to.x, r: Number.isInteger(to.r) ? to.r : to.y };
  const steps = Math.max(1, Math.round(cellDistance(map, a, b)));
  const cells = [];
  for (let i = 0; i <= steps; i += 1) {
    const t = i / steps;
    const rounded = roundAxial(lerp(a.q, b.q, t), lerp(a.r, b.r, t));
    const key = `${rounded.q}:${rounded.r}`;
    if (!cells.some((cell) => `${cell.q}:${cell.r}` === key)) cells.push(rounded);
  }
  return cells;
}

function withinArc(map, from, to, profile) {
  const arc = Number(profile.arcDeg ?? 360);
  if (arc >= 359) return true;
  const facing = Number(profile.facingDeg ?? 0);
  const a = coordinateToIndex(map, from);
  const b = coordinateToIndex(map, to);
  const angle = Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI;
  const delta = Math.abs((((angle - facing) % 360) + 540) % 360 - 180);
  return delta <= arc / 2;
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}
