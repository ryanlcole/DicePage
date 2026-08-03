import { actionTemplate } from "./actions.js";
import { triggerTemplate } from "./triggers.js";
import { defaultTileImageRef } from "./assets.js";
import { deepClone, recordEvent } from "./state.js";
import { coordinateFromCell, coordinateToIndex, deriveHexCoverage, deriveSquareFromPhysical, deriveSquarePhysicalSize, isCellInBounds, normalizeMapGeometry, selectionForCell, tileCoordinates, worldToCell } from "./grid.js";
import { findTile, getCurrentMap, setTerrainAt, tileAt, updateSelectedTile } from "./maps.js";

export function selectedTile(state) {
  return findTile(getCurrentMap(state), state.selectedTileId);
}

export function attachActionToSelectedTile(state, type) {
  const tile = selectedTile(state);
  if (!tile) return { ok: false, message: "No tile selected." };
  tile.actions.push(actionTemplate(type, tile));
  return updateSelectedTile(state, { actions: tile.actions });
}

export function attachTriggerToSelectedTile(state, condition) {
  const map = getCurrentMap(state);
  const tile = selectedTile(state);
  if (!tile) return { ok: false, message: "No tile selected." };
  const trigger = triggerTemplate(condition, tile);
  map.triggers.push(trigger);
  tile.triggers = [...new Set([...(tile.triggers || []), trigger.id])];
  return updateSelectedTile(state, { triggers: tile.triggers });
}

export function attachEncounterToSelectedTile(state, encounterId) {
  const tile = selectedTile(state);
  if (!tile) return { ok: false, message: "No tile selected." };
  tile.encounterId = encounterId;
  if (!tile.actions.some((action) => action.type === "start_encounter")) {
    tile.actions.push(actionTemplate("start_encounter", tile));
  }
  return updateSelectedTile(state, { encounterId, actions: tile.actions });
}

export function setSelectedTileChildMap(state, childMapId) {
  const tile = selectedTile(state);
  if (!tile) return { ok: false, message: "No tile selected." };
  return updateSelectedTile(state, { childMapId: childMapId || null, entryPointId: childMapId ? "entry-from-parent" : null });
}

export function setSelectedTileFlags(state, flags) {
  const tile = selectedTile(state);
  if (tile && typeof flags.blocked === "boolean") {
    flags = {
      ...flags,
      collision: {
        ...(tile.collision || {}),
        ...(flags.collision || {}),
        blocksMovement: flags.blocked,
        blocksProjectile: flags.collision?.blocksProjectile ?? flags.blocked
      }
    };
  }
  return updateSelectedTile(state, flags);
}

export function setActiveTool(state, tool) {
  const allowed = new Set(["select", "paint", "erase", "fill", "child", "trigger", "encounter", "entity-start", "pan", "zoom"]);
  state.editor.activeTool = allowed.has(tool) ? tool : "select";
  return { ok: true, tool: state.editor.activeTool };
}

export function selectCell(state, map, cell) {
  if (!cell || cell.mapId !== map.id) return { ok: false, message: "No valid cell selected." };
  state.selection = {
    mapId: cell.mapId,
    cellId: cell.cellId,
    gridType: cell.gridType,
    coordinates: deepClone(cell.coordinates)
  };
  const index = coordinateToIndex(map, cell.coordinates);
  const tile = tileAt(map, index.x, index.y, state.role);
  state.selectedTileId = tile?.id || null;
  return { ok: true, tile, selection: state.selection };
}

export function selectWorldPoint(state, map, worldPoint) {
  const cell = worldToCell(map, worldPoint);
  return selectCell(state, map, cell);
}

export function paintTerrainAtCell(state, map, cell, definitionId) {
  if (!cell) return { ok: false, message: "No cell selected." };
  const before = captureEditState(state, "terrain_paint");
  const changed = setTerrainAt(map, cell.coordinates, definitionId);
  if (!changed) return { ok: false, message: "Paint target is outside the map." };
  recordEditorHistory(state, before);
  const index = coordinateToIndex(map, cell.coordinates);
  recordEvent(state, "tile_changed", { mapId: map.id, terrain: definitionId, coordinates: deepClone(cell.coordinates), x: index.x, y: index.y });
  return { ok: true };
}

export function fillTerrain(state, map, definitionId) {
  const before = captureEditState(state, "terrain_fill");
  map.terrain = { default: definitionId, overrides: [] };
  recordEditorHistory(state, before);
  recordEvent(state, "tile_changed", { mapId: map.id, terrainFill: definitionId });
  return { ok: true };
}

export function setSelectedTileImage(state, assetId) {
  const tile = selectedTile(state);
  if (!tile) return { ok: false, message: "No tile selected." };
  if (assetId && !state.tileAssets[assetId]) return { ok: false, message: "Tile image asset is not registered." };
  return updateSelectedTile(state, { image: assetId ? defaultTileImageRef(assetId) : null });
}

export function clearSelectedTileContent(state) {
  const tile = selectedTile(state);
  if (!tile) return { ok: false, message: "No tile selected." };
  const patch = {
    actions: [],
    triggers: [],
    encounterId: null,
    childMapId: null,
    entryPointId: null,
    image: null,
    blocked: false,
    collision: { ...(tile.collision || {}), blocksMovement: false, blocksProjectile: false },
    hiddenFromPlayers: false
  };
  return updateSelectedTile(state, patch);
}

export function copySelectedTile(state) {
  const tile = selectedTile(state);
  if (!tile) return { ok: false, message: "No tile selected." };
  state.editor.copiedTile = deepClone(tile);
  return { ok: true, tile: state.editor.copiedTile };
}

export function pasteCopiedTile(state, map, cell) {
  if (!state.editor.copiedTile) return { ok: false, message: "No copied tile." };
  if (!cell) return { ok: false, message: "No target cell." };
  const index = coordinateToIndex(map, cell.coordinates);
  if (!isCellInBounds(map, coordinateFromCell(map, index.x, index.y))) return { ok: false, message: "Paste target is outside the map." };
  const before = captureEditState(state, "tile_paste");
  const tile = deepClone(state.editor.copiedTile);
  tile.id = `tile-copy-${Date.now().toString(36)}-${Math.floor(Math.random() * 1000)}`;
  tile.x = index.x;
  tile.y = index.y;
  if (map.gridType === "hex") {
    tile.q = index.x;
    tile.r = index.y;
  } else {
    delete tile.q;
    delete tile.r;
  }
  map.placedTiles.push(tile);
  state.selectedTileId = tile.id;
  state.selection = selectionForCell(map, coordinateFromCell(map, index.x, index.y));
  recordEditorHistory(state, before);
  recordEvent(state, "tile_placed", { mapId: map.id, tile: deepClone(tile), source: "paste" });
  return { ok: true, tile };
}

export function tileSummary(state) {
  const tile = selectedTile(state);
  if (!tile) return state.selection ? `Cell ${state.selection.cellId.split(":").slice(-2).join(",")}` : "No tile selected";
  const definition = state.tileDefinitions[tile.definitionId];
  const bits = [definition?.name || tile.definitionId, `${tile.x},${tile.y}`];
  if (tile.childMapId) bits.push("child");
  if (tile.triggers?.length) bits.push("trigger");
  if (tile.encounterId) bits.push("encounter");
  if (tile.hiddenFromPlayers) bits.push("hidden");
  if (tile.image?.imageAssetId) bits.push("image");
  return bits.join(" | ");
}

export function captureEditState(state, label) {
  const map = getCurrentMap(state);
  return {
    label,
    mapId: map.id,
    before: deepClone(map),
    selectedTileId: state.selectedTileId,
    selection: deepClone(state.selection)
  };
}

export function recordEditorHistory(state, entry) {
  if (!entry) return;
  const map = state.maps[entry.mapId];
  if (!map) return;
  entry.after = deepClone(map);
  state.editor.undoStack.push(entry);
  if (state.editor.undoStack.length > state.editor.historyLimit) state.editor.undoStack.shift();
  state.editor.redoStack = [];
}

export function undoEditorEdit(state) {
  const entry = state.editor.undoStack.pop();
  if (!entry) return { ok: false, message: "No edit to undo." };
  const current = state.maps[entry.mapId];
  state.editor.redoStack.push({ ...entry, before: deepClone(entry.before), after: deepClone(current) });
  state.maps[entry.mapId] = normalizeMapGeometry(deepClone(entry.before));
  state.currentMapId = entry.mapId;
  state.selectedTileId = entry.selectedTileId || null;
  state.selection = deepClone(entry.selection);
  recordEvent(state, "editor_undo", { mapId: entry.mapId, label: entry.label }, { stateChanging: false });
  return { ok: true };
}

export function redoEditorEdit(state) {
  const entry = state.editor.redoStack.pop();
  if (!entry) return { ok: false, message: "No edit to redo." };
  state.editor.undoStack.push({ ...entry, before: deepClone(entry.before), after: deepClone(entry.after) });
  state.maps[entry.mapId] = normalizeMapGeometry(deepClone(entry.after));
  state.currentMapId = entry.mapId;
  recordEvent(state, "editor_redo", { mapId: entry.mapId, label: entry.label }, { stateChanging: false });
  return { ok: true };
}

export function deriveMapSettings(input) {
  if (input.gridType === "hex") {
    if (input.sizeMode === "physical") {
      return { ok: true, gridType: "hex", ...deriveHexCoverage(input) };
    }
    return {
      ok: true,
      gridType: "hex",
      columns: Math.max(1, Math.round(Number(input.columns) || 16)),
      rows: Math.max(1, Math.round(Number(input.rows) || 10)),
      orientation: input.orientation === "flat" ? "flat" : "pointy",
      radius: Number(input.hexRadius) > 0 ? Number(input.hexRadius) : 5,
      radiusMeaning: "center_to_corner",
      unitSystem: input.unitSystem === "metric" ? "metric" : "imperial",
      distanceUnit: input.distanceUnit || (input.unitSystem === "metric" ? "m" : "ft")
    };
  }
  if (input.sizeMode === "physical") {
    const derived = deriveSquareFromPhysical(input);
    if (!derived.wholeCells) {
      return { ok: false, message: "Square physical dimensions must resolve to whole cells.", ...derived };
    }
    return { ok: true, gridType: "square", columns: derived.columns, rows: derived.rows, ...derived };
  }
  return {
    ok: true,
    gridType: "square",
    ...deriveSquarePhysicalSize(input)
  };
}

export function previewResizeImpact(map, nextColumns, nextRows) {
  normalizeMapGeometry(map);
  const removedTiles = map.placedTiles.filter((tile) => tile.x + tile.width > nextColumns || tile.y + tile.height > nextRows);
  const removedEntities = map.entities.filter((entity) => entity.x >= nextColumns || entity.y >= nextRows);
  const removedTerrain = (map.terrain?.overrides || []).filter((item) => {
    const x = Number.isInteger(item.q) ? item.q : item.x;
    const y = Number.isInteger(item.r) ? item.r : item.y;
    return x >= nextColumns || y >= nextRows;
  });
  return {
    removedTiles: removedTiles.map((tile) => ({
      id: tile.id,
      childMapId: tile.childMapId || null,
      triggers: deepClone(tile.triggers || []),
      encounterId: tile.encounterId || null
    })),
    removedEntities: removedEntities.map((entity) => entity.id),
    removedTerrain: removedTerrain.length,
    protectedContentCount: removedTiles.filter((tile) => tile.childMapId || tile.encounterId || tile.triggers?.length).length + removedEntities.length
  };
}

export function applyMapSettings(state, input, { confirmShrink = false } = {}) {
  const map = getCurrentMap(state);
  const derived = deriveMapSettings(input);
  if (!derived.ok) return derived;
  const nextColumns = Math.max(1, Math.round(derived.columns));
  const nextRows = Math.max(1, Math.round(derived.rows));
  const impact = previewResizeImpact(map, nextColumns, nextRows);
  const shrinking = nextColumns < map.width || nextRows < map.height;
  if (shrinking && (impact.removedTiles.length || impact.removedEntities.length || impact.removedTerrain) && !confirmShrink) {
    return { ok: false, message: "Shrink would remove map content. Confirm shrink to continue.", impact };
  }

  const before = captureEditState(state, "map_settings");
  map.name = String(input.name || map.name).trim() || map.name;
  map.gridType = derived.gridType;
  map.width = nextColumns;
  map.height = nextRows;
  map.tileSize = Math.max(8, Math.round(Number(input.tileSize) || map.tileSize || 16));
  map.terrain = map.terrain || { default: input.defaultTerrain || "grass", overrides: [] };
  map.terrain.default = input.defaultTerrain || map.terrain.default || "grass";
  map.permissions = map.permissions || { gm: { canView: true, canEdit: true }, player: { canView: true } };
  if (input.playerVisibilityDefault === "hidden") map.permissions.player.canView = false;
  if (derived.gridType === "hex") {
    map.gridSettings = {
      hex: {
        orientation: derived.orientation,
        radius: derived.radius,
        radiusMeaning: "center_to_corner",
        unitSystem: derived.unitSystem,
        distanceUnit: derived.distanceUnit,
        layoutBounds: { columns: nextColumns, rows: nextRows }
      }
    };
  } else {
    map.gridSettings = {
      square: {
        columns: nextColumns,
        rows: nextRows,
        cellWidth: Number(input.cellWidth) > 0 ? Number(input.cellWidth) : derived.cellWidth || 5,
        cellHeight: Number(input.cellHeight) > 0 ? Number(input.cellHeight) : derived.cellHeight || 5,
        unitSystem: derived.unitSystem,
        distanceUnit: derived.distanceUnit
      }
    };
  }
  map.placedTiles = map.placedTiles.filter((tile) => tile.x + tile.width <= nextColumns && tile.y + tile.height <= nextRows);
  map.entities = map.entities.filter((entity) => entity.x < nextColumns && entity.y < nextRows);
  if (map.terrain?.overrides) {
    map.terrain.overrides = map.terrain.overrides.filter((item) => {
      const x = Number.isInteger(item.q) ? item.q : item.x;
      const y = Number.isInteger(item.r) ? item.r : item.y;
      return x < nextColumns && y < nextRows;
    });
  }
  normalizeMapGeometry(map);
  recordEditorHistory(state, before);
  recordEvent(state, "map_settings_changed", { mapId: map.id, gridType: map.gridType, width: map.width, height: map.height, impact });
  return { ok: true, map, impact, derived };
}
