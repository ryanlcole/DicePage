export const GRID_TYPES = Object.freeze({
  SQUARE: "square",
  HEX: "hex"
});

export const HEX_ORIENTATIONS = Object.freeze({
  POINTY: "pointy",
  FLAT: "flat"
});

const SQRT3 = Math.sqrt(3);
const COS_30 = Math.cos(Math.PI / 6);

export function normalizeMapGeometry(map) {
  if (!map || typeof map !== "object") return map;
  map.gridType = map.gridType === GRID_TYPES.HEX ? GRID_TYPES.HEX : GRID_TYPES.SQUARE;
  map.width = positiveInteger(map.width, 16);
  map.height = positiveInteger(map.height, 10);
  map.tileSize = positiveInteger(map.tileSize, 16);
  map.gridSettings = map.gridSettings && typeof map.gridSettings === "object" ? map.gridSettings : {};

  if (map.gridType === GRID_TYPES.HEX) {
    const hex = map.gridSettings.hex && typeof map.gridSettings.hex === "object" ? map.gridSettings.hex : {};
    const bounds = hex.layoutBounds && typeof hex.layoutBounds === "object" ? hex.layoutBounds : {};
    map.gridSettings.hex = {
      orientation: hex.orientation === HEX_ORIENTATIONS.FLAT ? HEX_ORIENTATIONS.FLAT : HEX_ORIENTATIONS.POINTY,
      radius: positiveNumber(hex.radius, 5),
      radiusMeaning: "center_to_corner",
      unitSystem: normalizeUnitSystem(hex.unitSystem),
      distanceUnit: hex.distanceUnit || (hex.unitSystem === "metric" ? "m" : "ft"),
      layoutBounds: {
        columns: positiveInteger(bounds.columns, map.width),
        rows: positiveInteger(bounds.rows, map.height)
      }
    };
    map.width = map.gridSettings.hex.layoutBounds.columns;
    map.height = map.gridSettings.hex.layoutBounds.rows;
    return map;
  }

  const square = map.gridSettings.square && typeof map.gridSettings.square === "object" ? map.gridSettings.square : {};
  map.gridSettings.square = {
    columns: positiveInteger(square.columns, map.width),
    rows: positiveInteger(square.rows, map.height),
    cellWidth: positiveNumber(square.cellWidth, 5),
    cellHeight: positiveNumber(square.cellHeight, 5),
    unitSystem: normalizeUnitSystem(square.unitSystem),
    distanceUnit: square.distanceUnit || (square.unitSystem === "metric" ? "m" : "ft")
  };
  map.width = map.gridSettings.square.columns;
  map.height = map.gridSettings.square.rows;
  return map;
}

export function positiveInteger(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.max(1, Math.round(parsed)) : fallback;
}

export function positiveNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export function normalizeUnitSystem(value) {
  return value === "metric" || value === "abstract" ? value : "imperial";
}

export function mapColumns(map) {
  return normalizeMapGeometry(map).width;
}

export function mapRows(map) {
  return normalizeMapGeometry(map).height;
}

export function gridType(map) {
  return normalizeMapGeometry(map).gridType;
}

export function hexOrientation(map) {
  return normalizeMapGeometry(map).gridSettings.hex?.orientation || HEX_ORIENTATIONS.POINTY;
}

export function hexPhysicalRadius(map) {
  return normalizeMapGeometry(map).gridSettings.hex?.radius || 5;
}

export function hexPixelRadius(map) {
  return Math.max(8, normalizeMapGeometry(map).tileSize / 2);
}

export function hexApothem(radius) {
  return radius * COS_30;
}

export function coordinateFromCell(map, x, y) {
  if (gridType(map) === GRID_TYPES.HEX) return { q: x, r: y };
  return { x, y };
}

export function coordinateToIndex(map, coordinates) {
  if (gridType(map) === GRID_TYPES.HEX) {
    return {
      x: Number.isInteger(coordinates?.q) ? coordinates.q : coordinates?.x,
      y: Number.isInteger(coordinates?.r) ? coordinates.r : coordinates?.y
    };
  }
  return { x: coordinates?.x, y: coordinates?.y };
}

export function isCellInBounds(map, coordinates) {
  const { x, y } = coordinateToIndex(map, coordinates);
  return Number.isInteger(x) && Number.isInteger(y) && x >= 0 && y >= 0 && x < mapColumns(map) && y < mapRows(map);
}

export function cellId(map, coordinates) {
  const normalized = coordinateFromCell(map, coordinateToIndex(map, coordinates).x, coordinateToIndex(map, coordinates).y);
  if (gridType(map) === GRID_TYPES.HEX) return `${map.id}:hex:${normalized.q}:${normalized.r}`;
  return `${map.id}:square:${normalized.x}:${normalized.y}`;
}

export function selectionForCell(map, coordinates) {
  const indexed = coordinateToIndex(map, coordinates);
  const normalized = coordinateFromCell(map, indexed.x, indexed.y);
  return {
    mapId: map.id,
    cellId: cellId(map, normalized),
    gridType: gridType(map),
    coordinates: normalized
  };
}

export function tileCoordinates(map, tile) {
  if (gridType(map) === GRID_TYPES.HEX) {
    return { q: Number.isInteger(tile.q) ? tile.q : tile.x, r: Number.isInteger(tile.r) ? tile.r : tile.y };
  }
  return { x: tile.x, y: tile.y };
}

export function tileContainsCoordinate(map, tile, coordinates) {
  const index = coordinateToIndex(map, coordinates);
  const tileX = Number.isInteger(tile.q) && gridType(map) === GRID_TYPES.HEX ? tile.q : tile.x;
  const tileY = Number.isInteger(tile.r) && gridType(map) === GRID_TYPES.HEX ? tile.r : tile.y;
  return index.x >= tileX && index.y >= tileY && index.x < tileX + tile.width && index.y < tileY + tile.height;
}

export function mapPixelBounds(map) {
  normalizeMapGeometry(map);
  if (map.gridType === GRID_TYPES.SQUARE) {
    return { minX: 0, minY: 0, maxX: map.width * map.tileSize, maxY: map.height * map.tileSize, width: map.width * map.tileSize, height: map.height * map.tileSize };
  }
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (let r = 0; r < map.height; r += 1) {
    for (let q = 0; q < map.width; q += 1) {
      cellPolygon(map, { q, r }).forEach((point) => {
        minX = Math.min(minX, point.x);
        minY = Math.min(minY, point.y);
        maxX = Math.max(maxX, point.x);
        maxY = Math.max(maxY, point.y);
      });
    }
  }
  return { minX, minY, maxX, maxY, width: Math.ceil(maxX - minX), height: Math.ceil(maxY - minY) };
}

export function cellCenter(map, coordinates) {
  normalizeMapGeometry(map);
  const index = coordinateToIndex(map, coordinates);
  if (map.gridType === GRID_TYPES.SQUARE) {
    return { x: index.x * map.tileSize + map.tileSize / 2, y: index.y * map.tileSize + map.tileSize / 2 };
  }
  const radius = hexPixelRadius(map);
  if (hexOrientation(map) === HEX_ORIENTATIONS.FLAT) {
    return {
      x: radius + radius * 1.5 * index.x,
      y: radius + SQRT3 * radius * (index.y + index.x / 2)
    };
  }
  return {
    x: radius + SQRT3 * radius * (index.x + index.y / 2),
    y: radius + radius * 1.5 * index.y
  };
}

export function cellPolygon(map, coordinates) {
  normalizeMapGeometry(map);
  const index = coordinateToIndex(map, coordinates);
  if (map.gridType === GRID_TYPES.SQUARE) {
    const left = index.x * map.tileSize;
    const top = index.y * map.tileSize;
    return [
      { x: left, y: top },
      { x: left + map.tileSize, y: top },
      { x: left + map.tileSize, y: top + map.tileSize },
      { x: left, y: top + map.tileSize }
    ];
  }
  const center = cellCenter(map, coordinates);
  const radius = hexPixelRadius(map);
  const startDeg = hexOrientation(map) === HEX_ORIENTATIONS.FLAT ? 0 : -90;
  return Array.from({ length: 6 }, (_, index) => {
    const angle = ((startDeg + index * 60) * Math.PI) / 180;
    return {
      x: center.x + radius * Math.cos(angle),
      y: center.y + radius * Math.sin(angle)
    };
  });
}

export function worldToCell(map, point) {
  normalizeMapGeometry(map);
  if (map.gridType === GRID_TYPES.SQUARE) {
    const coordinates = { x: Math.floor(point.x / map.tileSize), y: Math.floor(point.y / map.tileSize) };
    return isCellInBounds(map, coordinates) ? { ...selectionForCell(map, coordinates), polygon: cellPolygon(map, coordinates) } : null;
  }
  const rounded = pixelToAxial(map, point);
  if (!isCellInBounds(map, rounded)) return null;
  const polygon = cellPolygon(map, rounded);
  if (!pointInPolygon(point, polygon)) return null;
  return { ...selectionForCell(map, rounded), polygon };
}

export function pixelToAxial(map, point) {
  const radius = hexPixelRadius(map);
  const px = point.x - radius;
  const py = point.y - radius;
  let q;
  let r;
  if (hexOrientation(map) === HEX_ORIENTATIONS.FLAT) {
    q = (2 / 3 * px) / radius;
    r = (-1 / 3 * px + SQRT3 / 3 * py) / radius;
  } else {
    q = (SQRT3 / 3 * px - 1 / 3 * py) / radius;
    r = (2 / 3 * py) / radius;
  }
  return roundAxial(q, r);
}

export function roundAxial(q, r) {
  let x = q;
  let z = r;
  let y = -x - z;
  let rx = Math.round(x);
  let ry = Math.round(y);
  let rz = Math.round(z);
  const xDiff = Math.abs(rx - x);
  const yDiff = Math.abs(ry - y);
  const zDiff = Math.abs(rz - z);
  if (xDiff > yDiff && xDiff > zDiff) rx = -ry - rz;
  else if (yDiff > zDiff) ry = -rx - rz;
  else rz = -rx - ry;
  return { q: rx, r: rz };
}

export function pointInPolygon(point, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i, i += 1) {
    const pi = polygon[i];
    const pj = polygon[j];
    const intersects = ((pi.y > point.y) !== (pj.y > point.y))
      && (point.x < ((pj.x - pi.x) * (point.y - pi.y)) / ((pj.y - pi.y) || Number.EPSILON) + pi.x);
    if (intersects) inside = !inside;
  }
  return inside;
}

export function deriveSquarePhysicalSize({ columns, rows, cellWidth, cellHeight, unitSystem = "imperial", distanceUnit = "ft" }) {
  const safeColumns = positiveInteger(columns, 1);
  const safeRows = positiveInteger(rows, 1);
  const safeCellWidth = positiveNumber(cellWidth, 5);
  const safeCellHeight = positiveNumber(cellHeight, 5);
  return {
    unitSystem: normalizeUnitSystem(unitSystem),
    distanceUnit,
    columns: safeColumns,
    rows: safeRows,
    actualWidth: safeColumns * safeCellWidth,
    actualHeight: safeRows * safeCellHeight,
    cellWidth: safeCellWidth,
    cellHeight: safeCellHeight
  };
}

export function deriveSquareFromPhysical({ width, height, cellWidth, cellHeight, unitSystem = "imperial", distanceUnit = "ft" }) {
  const safeWidth = positiveNumber(width, 80);
  const safeHeight = positiveNumber(height, 50);
  const safeCellWidth = positiveNumber(cellWidth, 5);
  const safeCellHeight = positiveNumber(cellHeight, 5);
  const columns = safeWidth / safeCellWidth;
  const rows = safeHeight / safeCellHeight;
  return {
    unitSystem: normalizeUnitSystem(unitSystem),
    distanceUnit,
    requestedWidth: safeWidth,
    requestedHeight: safeHeight,
    cellWidth: safeCellWidth,
    cellHeight: safeCellHeight,
    columns,
    rows,
    wholeCells: Number.isInteger(columns) && Number.isInteger(rows)
  };
}

export function deriveHexCoverage({ mapWidth, mapHeight, hexRadius, orientation = "pointy", unitSystem = "imperial", distanceUnit = "ft" }) {
  const requestedWidth = positiveNumber(mapWidth, 80);
  const requestedHeight = positiveNumber(mapHeight, 50);
  const radius = positiveNumber(hexRadius, 5);
  const normalizedOrientation = orientation === HEX_ORIENTATIONS.FLAT ? HEX_ORIENTATIONS.FLAT : HEX_ORIENTATIONS.POINTY;
  const horizontalStep = normalizedOrientation === HEX_ORIENTATIONS.FLAT ? radius * 1.5 : radius * SQRT3;
  const verticalStep = normalizedOrientation === HEX_ORIENTATIONS.FLAT ? radius * SQRT3 : radius * 1.5;
  const columns = Math.max(1, Math.ceil((requestedWidth - radius * 2) / horizontalStep) + 1);
  const rows = Math.max(1, Math.ceil((requestedHeight - radius * 2) / verticalStep) + 1);
  const tempMap = {
    id: "hex-coverage",
    gridType: GRID_TYPES.HEX,
    width: columns,
    height: rows,
    tileSize: radius * 2,
    gridSettings: {
      hex: {
        orientation: normalizedOrientation,
        radius,
        radiusMeaning: "center_to_corner",
        unitSystem: normalizeUnitSystem(unitSystem),
        distanceUnit,
        layoutBounds: { columns, rows }
      }
    }
  };
  const previousTileSize = tempMap.tileSize;
  tempMap.tileSize = radius * 2;
  const bounds = hexPhysicalBounds(columns, rows, radius, normalizedOrientation);
  tempMap.tileSize = previousTileSize;
  return {
    unitSystem: normalizeUnitSystem(unitSystem),
    distanceUnit,
    orientation: normalizedOrientation,
    radius,
    radiusMeaning: "center_to_corner",
    requestedWidth,
    requestedHeight,
    columns,
    rows,
    actualWidth: Number(bounds.width.toFixed(3)),
    actualHeight: Number(bounds.height.toFixed(3)),
    deltaWidth: Number((bounds.width - requestedWidth).toFixed(3)),
    deltaHeight: Number((bounds.height - requestedHeight).toFixed(3))
  };
}

function hexPhysicalBounds(columns, rows, radius, orientation) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (let r = 0; r < rows; r += 1) {
    for (let q = 0; q < columns; q += 1) {
      const center = orientation === HEX_ORIENTATIONS.FLAT
        ? { x: radius + radius * 1.5 * q, y: radius + SQRT3 * radius * (r + q / 2) }
        : { x: radius + SQRT3 * radius * (q + r / 2), y: radius + radius * 1.5 * r };
      const startDeg = orientation === HEX_ORIENTATIONS.FLAT ? 0 : -90;
      for (let i = 0; i < 6; i += 1) {
        const angle = ((startDeg + i * 60) * Math.PI) / 180;
        const x = center.x + radius * Math.cos(angle);
        const y = center.y + radius * Math.sin(angle);
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
      }
    }
  }
  return { width: maxX - minX, height: maxY - minY };
}
