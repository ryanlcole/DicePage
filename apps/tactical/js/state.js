import { normalizeMapCollision } from "./collision.js";

export const SCENES = Object.freeze({
  BOOT: "BOOT",
  MAP_VIEW: "MAP_VIEW",
  MAP_EDIT: "MAP_EDIT",
  DIALOGUE: "DIALOGUE",
  ENCOUNTER: "ENCOUNTER",
  REPLAY: "REPLAY",
  PAUSE: "PAUSE"
});

export const RULES_VERSION = "shaelvien.rules.0.1";
export const APP_SCHEMA_VERSION = "shaelvien.tabletop.state.v2";

export function deepClone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

export function byId(items) {
  return Object.fromEntries(items.map((item) => [item.id, deepClone(item)]));
}

export function byAssetId(items) {
  return Object.fromEntries(items.map((item) => [item.assetId, deepClone(item)]));
}

export function createGameState(bundle, persisted = null) {
  const state = {
    schemaVersion: APP_SCHEMA_VERSION,
    rulesVersion: RULES_VERSION,
    scene: SCENES.BOOT,
    previousScene: null,
    role: "gm",
    actorPlayerId: "player-a",
    currentMapId: "map-world",
    lastValidMapId: "map-world",
    selectedTileId: null,
    selection: null,
    selectedEntityId: "pc-lyra",
    selectedPaletteId: "grass",
    selectedTileImageAssetId: "",
    selectedActionCost: 0,
    maps: normalizeMaps(byId(bundle.maps)),
    tileManifest: deepClone(bundle.tileManifest),
    tileDefinitions: byId(bundle.tileManifest.definitions),
    tileAssetRegistry: deepClone(bundle.tileAssetRegistry || { schemaVersion: "shaelvien.tile_asset_registry.v1", assets: [] }),
    tileAssets: byAssetId(bundle.tileAssetRegistry?.assets || []),
    collisionPresets: byId(bundle.collisionPresets?.presets || []),
    perceptionProfiles: normalizePerceptionProfiles(bundle.perceptionProfiles || []),
    acousticMaterials: byId(bundle.acousticMaterials?.materials || []),
    encounters: byId(bundle.encounters),
    characters: byId(bundle.characters),
    creatures: byId(bundle.creatures),
    playerKnowledge: { discoveredCellsByPlayer: {} },
    soundEvents: [],
    perception: { current: null },
    activeEncounter: null,
    explorationBeforeEncounter: null,
    replay: {
      selectedReplayId: null,
      cursor: 0,
      playing: false,
      speed: 1,
      inspectedEntityId: null,
      displayState: null,
      accumulator: 0
    },
    replays: [],
    eventLog: [],
    messages: [],
    settings: {
      rejectionLogging: true
    },
    editor: {
      activeTool: "select",
      copiedTile: null,
      contextMenu: { open: false, x: 0, y: 0, cell: null, tileId: null },
      inspectorOpen: true,
      inspectorWidth: 336,
      inspectorSheetState: "collapsed",
      moreMenuOpen: false,
      perceptionDebug: {
        enabled: false,
        vision: true,
        hearing: true,
        fog: true,
        acousticPaths: true
      },
      undoStack: [],
      redoStack: [],
      historyLimit: 40,
      longPressMs: 550,
      viewportByMap: {}
    },
    input: {
      pointerActive: false,
      lastPointerCell: null,
      lastGesture: null
    },
    nextEventSeq: 1,
    createdAt: "local-static"
  };

  if (persisted && (persisted.schemaVersion === APP_SCHEMA_VERSION || persisted.schemaVersion === "shaelvien.tabletop.state.v1")) {
    state.scene = sanitizeScene(persisted.scene);
    state.previousScene = persisted.previousScene || null;
    state.role = persisted.role === "player" ? "player" : "gm";
    state.actorPlayerId = persisted.actorPlayerId || "player-a";
    state.currentMapId = state.maps[persisted.currentMapId] ? persisted.currentMapId : "map-world";
    state.lastValidMapId = state.maps[persisted.lastValidMapId] ? persisted.lastValidMapId : state.currentMapId;
    state.selectedTileId = persisted.selectedTileId || null;
    state.selection = normalizeSelection(persisted.selection, state.currentMapId);
    state.selectedEntityId = persisted.selectedEntityId || "pc-lyra";
    state.selectedPaletteId = state.tileDefinitions[persisted.selectedPaletteId] ? persisted.selectedPaletteId : "grass";
    state.selectedTileImageAssetId = state.tileAssets[persisted.selectedTileImageAssetId] ? persisted.selectedTileImageAssetId : "";
    state.maps = persisted.maps ? normalizeMaps(mergeKnownMaps(state.maps, persisted.maps)) : state.maps;
    state.eventLog = Array.isArray(persisted.eventLog) ? persisted.eventLog : [];
    state.messages = Array.isArray(persisted.messages) ? persisted.messages : [];
    state.replays = Array.isArray(persisted.replays) ? persisted.replays : [];
    state.playerKnowledge = persisted.playerKnowledge && typeof persisted.playerKnowledge === "object" ? persisted.playerKnowledge : state.playerKnowledge;
    state.soundEvents = Array.isArray(persisted.soundEvents) ? persisted.soundEvents : [];
    state.nextEventSeq = Number.isInteger(persisted.nextEventSeq) ? persisted.nextEventSeq : state.eventLog.length + 1;
    state.replay.selectedReplayId = persisted.replay?.selectedReplayId || state.replays.at(-1)?.replayId || null;
    if (persisted.editor && typeof persisted.editor === "object") {
      state.editor.activeTool = typeof persisted.editor.activeTool === "string" ? persisted.editor.activeTool : state.editor.activeTool;
      state.editor.inspectorOpen = persisted.editor.inspectorOpen !== false;
      state.editor.inspectorWidth = Number(persisted.editor.inspectorWidth) > 0 ? Number(persisted.editor.inspectorWidth) : state.editor.inspectorWidth;
      state.editor.inspectorSheetState = ["collapsed", "half", "full"].includes(persisted.editor.inspectorSheetState) ? persisted.editor.inspectorSheetState : state.editor.inspectorSheetState;
      state.editor.viewportByMap = persisted.editor.viewportByMap && typeof persisted.editor.viewportByMap === "object" ? persisted.editor.viewportByMap : {};
      state.editor.perceptionDebug = persisted.editor.perceptionDebug && typeof persisted.editor.perceptionDebug === "object"
        ? { ...state.editor.perceptionDebug, ...persisted.editor.perceptionDebug }
        : state.editor.perceptionDebug;
    }
  }

  if (!state.maps[state.currentMapId]) {
    state.currentMapId = "map-world";
  }
  if (state.scene === SCENES.BOOT || state.scene === SCENES.ENCOUNTER || state.scene === SCENES.REPLAY || state.scene === SCENES.DIALOGUE || state.scene === SCENES.PAUSE) {
    state.scene = SCENES.MAP_VIEW;
    state.currentMapId = state.maps[state.lastValidMapId] ? state.lastValidMapId : "map-world";
  }
  state.lastValidMapId = state.currentMapId;
  Object.values(state.maps).forEach((map) => normalizeMapCollision(map, state));
  return state;
}

function normalizeMaps(maps) {
  Object.values(maps).forEach((map) => normalizeMapGeometry(map));
  return maps;
}

function normalizeMapGeometry(map) {
  if (!map || typeof map !== "object") return map;
  map.gridType = map.gridType === "hex" ? "hex" : "square";
  map.width = Number.isInteger(map.width) && map.width > 0 ? map.width : 16;
  map.height = Number.isInteger(map.height) && map.height > 0 ? map.height : 10;
  map.tileSize = Number.isInteger(map.tileSize) && map.tileSize > 0 ? map.tileSize : 16;
  map.gridSettings = map.gridSettings && typeof map.gridSettings === "object" ? map.gridSettings : {};
  if (map.gridType === "hex") {
    const hex = map.gridSettings.hex && typeof map.gridSettings.hex === "object" ? map.gridSettings.hex : {};
    const bounds = hex.layoutBounds && typeof hex.layoutBounds === "object" ? hex.layoutBounds : {};
    map.gridSettings.hex = {
      orientation: hex.orientation === "flat" ? "flat" : "pointy",
      radius: Number(hex.radius) > 0 ? Number(hex.radius) : 5,
      radiusMeaning: "center_to_corner",
      unitSystem: ["metric", "abstract"].includes(hex.unitSystem) ? hex.unitSystem : "imperial",
      distanceUnit: hex.distanceUnit || (hex.unitSystem === "metric" ? "m" : "ft"),
      layoutBounds: {
        columns: Number.isInteger(bounds.columns) ? bounds.columns : map.width,
        rows: Number.isInteger(bounds.rows) ? bounds.rows : map.height
      }
    };
    map.width = map.gridSettings.hex.layoutBounds.columns;
    map.height = map.gridSettings.hex.layoutBounds.rows;
  } else {
    const square = map.gridSettings.square && typeof map.gridSettings.square === "object" ? map.gridSettings.square : {};
    map.gridSettings.square = {
      columns: Number.isInteger(square.columns) ? square.columns : map.width,
      rows: Number.isInteger(square.rows) ? square.rows : map.height,
      cellWidth: Number(square.cellWidth) > 0 ? Number(square.cellWidth) : 5,
      cellHeight: Number(square.cellHeight) > 0 ? Number(square.cellHeight) : 5,
      unitSystem: ["metric", "abstract"].includes(square.unitSystem) ? square.unitSystem : "imperial",
      distanceUnit: square.distanceUnit || (square.unitSystem === "metric" ? "m" : "ft")
    };
    map.width = map.gridSettings.square.columns;
    map.height = map.gridSettings.square.rows;
  }
  return map;
}

function normalizeSelection(selection, fallbackMapId) {
  if (!selection || typeof selection !== "object" || !selection.cellId) return null;
  return {
    mapId: selection.mapId || fallbackMapId,
    cellId: selection.cellId,
    gridType: selection.gridType === "hex" ? "hex" : "square",
    coordinates: selection.coordinates && typeof selection.coordinates === "object" ? deepClone(selection.coordinates) : {}
  };
}

function sanitizeScene(scene) {
  return Object.values(SCENES).includes(scene) ? scene : SCENES.MAP_VIEW;
}

function mergeKnownMaps(defaultMaps, savedMaps) {
  const merged = deepClone(defaultMaps);
  Object.entries(savedMaps).forEach(([id, map]) => {
    if (map && map.schemaVersion && Number.isInteger(map.width) && Number.isInteger(map.height)) {
      merged[id] = normalizeMapGeometry(deepClone(map));
    }
  });
  return merged;
}

function normalizePerceptionProfiles(profiles) {
  const records = Array.isArray(profiles?.profiles) ? profiles.profiles : Array.isArray(profiles) ? profiles : [];
  return Object.fromEntries(records.map((profile) => [profile.id, deepClone(profile)]));
}

export function recordEvent(state, type, payload = {}, options = {}) {
  const event = {
    sequence: state.nextEventSeq++,
    type,
    scene: state.scene,
    mapId: state.currentMapId,
    encounterId: state.activeEncounter?.encounterId || null,
    round: state.activeEncounter?.round || null,
    rejected: options.rejected === true,
    stateChanging: options.stateChanging !== false,
    payload: deepClone(payload)
  };
  if (!event.rejected || state.settings.rejectionLogging) {
    state.eventLog.push(event);
  }
  return event;
}

export function pushMessage(state, message, tone = "info") {
  state.messages.push({
    sequence: state.nextEventSeq,
    tone,
    message: String(message)
  });
  if (state.messages.length > 12) state.messages.shift();
}

export function serializableState(state) {
  return {
    schemaVersion: state.schemaVersion,
    rulesVersion: state.rulesVersion,
    scene: state.scene,
    previousScene: state.previousScene,
    role: state.role,
    actorPlayerId: state.actorPlayerId,
    currentMapId: state.currentMapId,
    lastValidMapId: state.lastValidMapId,
    selectedTileId: state.selectedTileId,
    selection: deepClone(state.selection),
    selectedEntityId: state.selectedEntityId,
    selectedPaletteId: state.selectedPaletteId,
    selectedTileImageAssetId: state.selectedTileImageAssetId,
    maps: deepClone(state.maps),
    eventLog: deepClone(state.eventLog),
    messages: deepClone(state.messages),
    playerKnowledge: deepClone(state.playerKnowledge),
    soundEvents: deepClone(state.soundEvents),
    replays: deepClone(state.replays),
    replay: {
      selectedReplayId: state.replay.selectedReplayId
    },
    editor: {
      activeTool: state.editor.activeTool,
      inspectorOpen: state.editor.inspectorOpen,
      inspectorWidth: state.editor.inspectorWidth,
      inspectorSheetState: state.editor.inspectorSheetState,
      perceptionDebug: deepClone(state.editor.perceptionDebug),
      viewportByMap: deepClone(state.editor.viewportByMap)
    },
    nextEventSeq: state.nextEventSeq
  };
}
