import { STORAGE_KEY, clearSavedState, createInitialState, loadGameBundle, saveState } from "./api.js";
import { SCENES, createGameState, deepClone, pushMessage, recordEvent } from "./state.js";
import {
  findEntity,
  findTile,
  getCurrentMap,
  getMapPath,
  moveExplorationEntity,
  moveSelectedTile,
  openChildMapFromTile,
  placeTile,
  playerVisibleSnapshot,
  removeSelectedTile,
  returnToParentMap,
  setTerrainAt,
  tileAt
} from "./maps.js";
import { executeEncounterAction, executeQueuedActionForActive, exitEncounterToMap, activeCombatant, actionCost, autoResolveEncounterToEnd, remainingTime } from "./encounter.js";
import { executeFirstTileAction, manualTriggerSelectedTile } from "./actions.js";
import { processMapEvent } from "./triggers.js";
import {
  applyMapSettings,
  captureEditState,
  clearSelectedTileContent,
  copySelectedTile,
  deriveMapSettings,
  fillTerrain,
  paintTerrainAtCell,
  pasteCopiedTile,
  previewResizeImpact,
  recordEditorHistory,
  redoEditorEdit,
  selectCell,
  selectedTile,
  setActiveTool,
  setSelectedTileChildMap,
  setSelectedTileFlags,
  setSelectedTileImage,
  tileSummary,
  undoEditorEdit,
  attachActionToSelectedTile,
  attachEncounterToSelectedTile,
  attachTriggerToSelectedTile
} from "./editor.js";
import { COMMANDER_ORDERS, directMonsterOverride, issueCommanderOrder } from "./commander.js";
import { comparableEncounterState, rebuildEncounterState, replayRounds, stableHash, verifyReplayRecord } from "./replay.js";
import { bindInput, directionVector } from "./input.js";
import { atlasAssets, duplicateAssetByHash, hashBrowserFile, tileAssets } from "./assets.js";
import {
  atlasCollections,
  atlasRenderableAssets,
  createAtlasInstance,
  findAtlasInstance,
  moveSelectedAtlasInstance,
  removeSelectedAtlasInstance,
  rotateSelectedAtlasInstance,
  setAtlasInstanceChildMap,
  sortedAtlasInstances
} from "./atlas.js";
import { GRID_TYPES, cellCenter, cellId, cellPolygon, coordinateFromCell, coordinateToIndex, deriveHexCoverage, hexPhysicalRadius, hexPixelRadius, isCellInBounds, mapPixelBounds, normalizeMapGeometry, pointInPolygon, selectionForCell, worldToCell } from "./grid.js";
import { collisionSummary, normalizeMapCollision, presetCollision, presetShape } from "./collision.js";
import { computePlayerPerception, legalStartCellsForPlayer, perceptionZoomBounds, placeOwnedPlayerCharacter, visibleForPlayer } from "./perception.js";
import { FOG_STATES, cellKey, fogStateFor, isVisibleNow } from "./fog.js";
import { emitSoundEvent } from "./sound.js";
import { angleDeg, distance, midpoint as gestureMidpoint, sameTapTarget, snapRotationDeg } from "./tabletop/gestures.js";
import { activeScene, closeOverlay, openOverlay, tabletopProjection } from "./tabletop/scene.js";
import { drawTopCard, commanderHand, selectCard, selectDeck } from "./tabletop/decks.js";
import { shareCard } from "./tabletop/cards.js";
import { rollDie } from "./tabletop/dice.js";
import { resolveDiceBagAction } from "./tabletop/dice_bag.js";
import { visibleModifierRows } from "./tabletop/chips.js";
import { advanceInitiative } from "./tabletop/initiative.js";
import { pauseClock, resumeClock, clockProgress } from "./tabletop/clock.js";
import { shareLoreCard, toggleLoreScroll } from "./tabletop/lore.js";
import { startDrag, endDrag } from "./tabletop/drag_drop.js";

let state = null;
let bundleCache = null;
let canvas = null;
let context = null;
let lastFrame = 0;
let spriteCache = new Map();
let assetImageCache = new Map();
let atlasAlphaHitCache = new Map();
let viewportElement = null;
let activePointers = new Map();
let gesture = null;
let longPressTimer = null;
let spacePanActive = false;
let lastTap = null;

const elements = {};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot, { once: true });
} else {
  boot();
}

async function boot() {
  collectElements();
  setText("connectionStatus", "Loading");
  try {
    bundleCache = await loadGameBundle();
    const hasPersistedState = Boolean(localStorage.getItem(STORAGE_KEY));
    state = await createInitialState();
    if (!hasPersistedState && state.maps["map-atlas-region-stream-demo"]) {
      state.currentMapId = "map-atlas-region-stream-demo";
      state.lastValidMapId = state.currentMapId;
      state.scene = SCENES.MAP_EDIT;
      state.role = "gm";
      state.editor.inspectorOpen = window.innerWidth >= 900;
      state.editor.inspectorSheetState = "collapsed";
      state.selectedAtlasCollection = "streams_and_small_watercourses";
    }
    if (!hasPersistedState && window.innerWidth < 900) {
      state.editor.inspectorOpen = false;
      state.editor.inspectorSheetState = "collapsed";
    }
    state.scene = SCENES.MAP_VIEW;
    canvas = elements.gameCanvas;
    viewportElement = elements.mapViewport || canvas.parentElement;
    context = canvas.getContext("2d");
    context.imageSmoothingEnabled = false;
    bindControls();
    bindViewportResize();
    buildSpriteCache();
    buildAssetImageCache();
    renderAll();
    window.requestAnimationFrame(() => fitCurrentMap({ persist: false, onlyIfUninitialized: true }));
    setText("connectionStatus", "Local");
    window.requestAnimationFrame(loop);
    window.shaelvienApp = {
      getState: () => state,
      runAcceptanceScript,
      runEditorAcceptanceScript,
      runWorkspaceAcceptanceScript,
      runPerceptionAcceptanceScript,
      runTabletopAcceptanceScript,
      runAtlasAcceptanceScript,
      openTabletopOverlay,
      showMapForVerification,
      verifyCurrentReplay,
      workspacePointForCell,
      resetApplication
    };
    if (new URLSearchParams(window.location.search).get("acceptance") === "1") {
      runAcceptanceScript()
        .then((result) => writeAcceptanceResult({ ok: true, result }))
        .catch((error) => writeAcceptanceResult({ ok: false, error: error.message }));
    }
  } catch (error) {
    setText("connectionStatus", "Failed");
    setText("errorStatus", error.message);
    console.error(error);
  }
}

function openTabletopOverlay(category = "scene") {
  openOverlay(state.tabletop, category);
  renderAll();
}

function writeAcceptanceResult(payload) {
  let node = document.getElementById("acceptanceResult");
  if (!node) {
    node = document.createElement("pre");
    node.id = "acceptanceResult";
    node.hidden = true;
    document.body.appendChild(node);
  }
  node.textContent = JSON.stringify(payload, null, 2);
  document.body.dataset.acceptance = payload.ok ? "complete" : "failed";
}

function collectElements() {
  [
    "sceneStatus", "connectionStatus", "errorStatus", "gmRoleButton", "playerRoleButton", "playerIdentity",
    "mapViewButton", "mapEditButton", "replayButton", "pauseButton", "saveButton", "resetButton", "breadcrumb",
    "mapViewport", "gameCanvas", "selectionStatus", "timeStatus", "mapMeta", "openChildButton", "returnParentButton",
    "interactButton", "placePcButton", "tilePalette", "moveTileLeftButton", "moveTileRightButton", "moveTileUpButton",
    "moveTileDownButton", "deleteTileButton", "createChildButton", "hiddenToggle", "blockedToggle",
    "collisionPresetSelect", "collisionMovementToggle", "collisionVisionToggle", "collisionSoundToggle",
    "collisionProjectileToggle", "collisionReachToggle", "collisionShapeSelect", "collisionHeightInput",
    "soundTransmissionInput", "soundAbsorptionInput",
    "childMapSelect", "actionTypeSelect", "attachActionButton", "triggerTypeSelect", "attachTriggerButton",
    "encounterSelect", "attachEncounterButton", "manualTriggerButton", "encounterMeta", "timeAvailable",
    "timeSpent", "selectedCost", "timeRemaining", "commanderOrder", "issueCommanderButton", "monsterSelect",
    "directAction", "directOverrideButton", "runQueuedButton", "finishEncounterButton", "replayRestartButton",
    "replayPlayButton", "replayPauseButton", "replayPrevButton", "replayNextButton", "replayPrevRoundButton",
    "replayNextRoundButton", "replaySpeedButton", "replayInspectButton", "replaySelect", "replayMeta", "replayDetail", "eventLog", "logCount",
    "toggleInspectorButton", "closeInspectorButton", "inspectorPanel", "assetSelect", "assignTileImageButton", "removeTileImageButton",
    "brushImageSelect", "assetFileInput", "assetImportStatus", "zoomInButton", "zoomOutButton", "fitMapButton", "fitSelectionButton",
    "atlasCollectionSelect", "atlasSearchInput", "atlasBrowser", "placeAtlasAssetButton", "selectedAtlasInstanceSummary",
    "moveAtlasLeftButton", "moveAtlasRightButton", "moveAtlasUpButton", "moveAtlasDownButton", "rotateAtlasLeftButton",
    "rotateAtlasRightButton", "removeAtlasInstanceButton", "atlasChildMapSelect", "attachAtlasChildButton", "openAtlasChildButton",
    "fitWidthButton", "fitHeightButton", "actualSizeButton", "resetViewButton", "rotateLeftButton", "rotateRightButton",
    "resetRotationButton", "compassButton", "compassNeedle", "compassAngle", "zoomSelect", "mobileZoomInButton", "mobileZoomOutButton",
    "floatingZoomLabel", "gridVisibleToggle", "moreMenuButton", "moreMenu", "workspaceMapHud", "currentLocationLabel",
    "statusMap", "statusGrid", "statusScale", "statusZoom", "statusRotation", "tileInspectorSummary", "inspectorResizeHandle",
    "newMapButton", "openMapMenuButton", "measureToolButton",
    "resetViewButton", "mapSettingsButton", "mapSettingsDialog", "mapSettingsForm", "mapSettingsCancelButton", "mapSettingsPreview",
    "mapSettingsConfirmShrink", "settingsMapName", "settingsMapId", "settingsGridType", "settingsHexOrientation", "settingsSizeMode",
    "settingsColumns", "settingsRows", "settingsPhysicalWidth", "settingsPhysicalHeight", "settingsUnitSystem", "settingsDistanceUnit",
    "settingsCellWidth", "settingsCellHeight", "settingsHexRadius", "settingsTileSize", "settingsDefaultTerrain", "settingsPlayerVisibility",
    "tileContextMenu", "contextMenuTitle", "tabletopOverlay", "tabletopOverlayBackdrop", "tabletopOverlayTitle",
    "tabletopOverlayTabs", "tabletopOverlayContent", "closeTabletopOverlayButton", "tabletopInitiativeStrip",
    "tabletopClock", "tabletopClockFace", "tabletopClockButton", "tabletopClockPauseButton", "tabletopLoreScroll",
    "tabletopEffectsTray", "tabletopRightTray", "tabletopBottomTray", "tabletopPlayerDeck", "tabletopMonsterDeck",
    "tabletopDiceRow", "tabletopCardDetail", "tabletopReducedMotionToggle"
  ].forEach((id) => {
    elements[id] = document.getElementById(id);
  });
}

function bindControls() {
  elements.gmRoleButton.addEventListener("click", () => setRole("gm"));
  elements.playerRoleButton.addEventListener("click", () => setRole("player"));
  elements.playerIdentity.addEventListener("change", () => {
    state.actorPlayerId = elements.playerIdentity.value;
    const map = getCurrentMap(state);
    const assigned = map.entities.find((entity) => entity.assignedPlayerId === state.actorPlayerId);
    if (assigned) state.selectedEntityId = assigned.id;
    persistAndRender();
  });
  elements.mapViewButton.addEventListener("click", () => setScene(SCENES.MAP_VIEW));
  elements.mapEditButton.addEventListener("click", () => setScene(SCENES.MAP_EDIT));
  elements.replayButton.addEventListener("click", () => setScene(SCENES.REPLAY));
  elements.pauseButton.addEventListener("click", () => setScene(SCENES.PAUSE));
  elements.saveButton.addEventListener("click", () => {
    saveState(state);
    pushMessage(state, "Saved locally.");
    renderAll();
  });
  elements.resetButton.addEventListener("click", resetApplication);
  elements.toggleInspectorButton?.addEventListener("click", () => {
    if (window.innerWidth < 900) {
      state.editor.inspectorOpen = true;
      state.editor.inspectorSheetState = state.editor.inspectorSheetState === "full" ? "collapsed" : "half";
      if (state.editor.inspectorSheetState === "collapsed") state.editor.inspectorOpen = false;
    } else {
      state.editor.inspectorOpen = !state.editor.inspectorOpen;
    }
    persistAndRender();
  });
  elements.closeInspectorButton?.addEventListener("click", () => {
    state.editor.inspectorOpen = false;
    state.editor.inspectorSheetState = "collapsed";
    persistAndRender();
  });
  elements.inspectorPanel?.querySelector(".inspector-title")?.addEventListener("click", (event) => {
    if (window.innerWidth >= 900 || event.target.closest("button")) return;
    if (!state.editor.inspectorOpen) {
      state.editor.inspectorOpen = true;
      state.editor.inspectorSheetState = "half";
    } else if (state.editor.inspectorSheetState === "half") {
      state.editor.inspectorSheetState = "full";
    } else {
      state.editor.inspectorOpen = false;
      state.editor.inspectorSheetState = "collapsed";
    }
    persistAndRender();
  });

  document.querySelectorAll("[data-editor-tool]").forEach((button) => {
    button.addEventListener("click", () => {
      setActiveTool(state, button.dataset.editorTool);
      if (state.role === "gm" && state.scene !== SCENES.ENCOUNTER && state.scene !== SCENES.REPLAY) state.scene = SCENES.MAP_EDIT;
      persistAndRender();
    });
  });
  document.querySelectorAll("[data-editor-command]").forEach((button) => {
    button.addEventListener("click", () => handleEditorCommand(button.dataset.editorCommand));
  });
  elements.zoomInButton?.addEventListener("click", () => zoomViewport(1.2));
  elements.zoomOutButton?.addEventListener("click", () => zoomViewport(1 / 1.2));
  elements.mobileZoomInButton?.addEventListener("click", () => zoomViewport(1.2));
  elements.mobileZoomOutButton?.addEventListener("click", () => zoomViewport(1 / 1.2));
  elements.fitMapButton?.addEventListener("click", () => fitCurrentMap());
  elements.fitWidthButton?.addEventListener("click", () => fitMapMode("fit-width"));
  elements.fitHeightButton?.addEventListener("click", () => fitMapMode("fit-height"));
  elements.actualSizeButton?.addEventListener("click", () => setActualSize());
  elements.fitSelectionButton?.addEventListener("click", () => fitSelection());
  elements.resetViewButton?.addEventListener("click", resetCurrentViewport);
  elements.rotateLeftButton?.addEventListener("click", () => rotateViewport(-90));
  elements.rotateRightButton?.addEventListener("click", () => rotateViewport(90));
  elements.resetRotationButton?.addEventListener("click", resetRotation);
  elements.compassButton?.addEventListener("click", resetRotation);
  elements.zoomSelect?.addEventListener("change", handleZoomSelect);
  elements.gridVisibleToggle?.addEventListener("change", () => {
    currentViewport().gridVisible = elements.gridVisibleToggle.checked;
    persistAndRender();
  });
  elements.moreMenuButton?.addEventListener("click", openMoreMenu);
  elements.moreMenu?.addEventListener("click", (event) => {
    const action = event.target.closest("[data-more-action]")?.dataset.moreAction;
    if (!action) return;
    closeMoreMenu();
    handleMoreAction(action);
  });
  elements.newMapButton?.addEventListener("click", openMapSettings);
  elements.openMapMenuButton?.addEventListener("click", () => {
    pushMessage(state, "Use the breadcrumb or child-map actions to open maps in this slice.");
    renderAll();
  });
  elements.measureToolButton?.addEventListener("click", () => {
    pushMessage(state, "Measure overlay is reserved for the next bounded editor pass.");
    renderAll();
  });
  elements.inspectorResizeHandle?.addEventListener("pointerdown", beginInspectorResize);
  elements.mapSettingsButton?.addEventListener("click", openMapSettings);
  elements.mapSettingsCancelButton?.addEventListener("click", closeMapSettings);
  document.querySelectorAll("[data-dialog-close]").forEach((button) => {
    button.addEventListener("click", () => {
      const dialog = document.getElementById(button.dataset.dialogClose);
      if (dialog?.close) dialog.close();
      else if (dialog) dialog.hidden = true;
    });
  });
  elements.mapSettingsForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    applyCurrentMapSettings();
  });
  [
    "settingsMapName", "settingsGridType", "settingsHexOrientation", "settingsSizeMode", "settingsColumns",
    "settingsRows", "settingsPhysicalWidth", "settingsPhysicalHeight", "settingsUnitSystem", "settingsDistanceUnit",
    "settingsCellWidth", "settingsCellHeight", "settingsHexRadius", "settingsTileSize", "settingsDefaultTerrain"
  ].forEach((id) => elements[id]?.addEventListener("input", updateMapSettingsPreview));
  elements.assetSelect?.addEventListener("change", () => {
    state.selectedTileImageAssetId = elements.assetSelect.value;
    persistAndRender();
  });
  elements.brushImageSelect?.addEventListener("change", () => {
    state.selectedTileImageAssetId = elements.brushImageSelect.value;
    persistAndRender();
  });
  elements.assignTileImageButton?.addEventListener("click", () => editorCommand("assign tile image", () => setSelectedTileImage(state, state.selectedTileImageAssetId || elements.assetSelect.value)));
  elements.removeTileImageButton?.addEventListener("click", () => editorCommand("remove tile image", () => setSelectedTileImage(state, "")));
  elements.assetFileInput?.addEventListener("change", inspectSelectedAssetFile);
  elements.atlasCollectionSelect?.addEventListener("change", () => {
    state.selectedAtlasCollection = elements.atlasCollectionSelect.value;
    renderAtlasBrowser();
  });
  elements.atlasSearchInput?.addEventListener("input", renderAtlasBrowser);
  elements.placeAtlasAssetButton?.addEventListener("click", () => editorCommand("place atlas asset", placeSelectedAtlasAsset));
  elements.moveAtlasLeftButton?.addEventListener("click", () => editorCommand("move atlas left", () => moveSelectedAtlasInstance(state, getCurrentMap(state), -8, 0)));
  elements.moveAtlasRightButton?.addEventListener("click", () => editorCommand("move atlas right", () => moveSelectedAtlasInstance(state, getCurrentMap(state), 8, 0)));
  elements.moveAtlasUpButton?.addEventListener("click", () => editorCommand("move atlas up", () => moveSelectedAtlasInstance(state, getCurrentMap(state), 0, -8)));
  elements.moveAtlasDownButton?.addEventListener("click", () => editorCommand("move atlas down", () => moveSelectedAtlasInstance(state, getCurrentMap(state), 0, 8)));
  elements.rotateAtlasLeftButton?.addEventListener("click", () => editorCommand("rotate atlas left", () => rotateSelectedAtlasInstance(state, getCurrentMap(state), -90)));
  elements.rotateAtlasRightButton?.addEventListener("click", () => editorCommand("rotate atlas right", () => rotateSelectedAtlasInstance(state, getCurrentMap(state), 90)));
  elements.removeAtlasInstanceButton?.addEventListener("click", () => editorCommand("remove atlas instance", () => removeSelectedAtlasInstance(state, getCurrentMap(state))));
  elements.attachAtlasChildButton?.addEventListener("click", () => editorCommand("attach atlas child", () => setAtlasInstanceChildMap(state, getCurrentMap(state), elements.atlasChildMapSelect?.value || "")));
  elements.openAtlasChildButton?.addEventListener("click", openSelectedAtlasChild);

  elements.openChildButton.addEventListener("click", openSelectedChild);
  elements.returnParentButton.addEventListener("click", () => commandResult(returnToParentMap(state, actor())));
  elements.interactButton.addEventListener("click", interactSelectedTile);
  elements.placePcButton?.addEventListener("click", placeSelectedOwnedPc);
  document.querySelectorAll("[data-map-move]").forEach((button) => {
    button.addEventListener("click", () => handleDirection(button.dataset.mapMove));
  });

  elements.moveTileLeftButton.addEventListener("click", () => editorCommand("move tile left", () => moveSelectedTile(state, -1, 0)));
  elements.moveTileRightButton.addEventListener("click", () => editorCommand("move tile right", () => moveSelectedTile(state, 1, 0)));
  elements.moveTileUpButton.addEventListener("click", () => editorCommand("move tile up", () => moveSelectedTile(state, 0, -1)));
  elements.moveTileDownButton.addEventListener("click", () => editorCommand("move tile down", () => moveSelectedTile(state, 0, 1)));
  elements.deleteTileButton.addEventListener("click", () => editorCommand("delete tile", () => removeSelectedTile(state)));
  elements.createChildButton.addEventListener("click", () => {
    import("./maps.js").then((module) => editorCommand("create child map", () => module.createChildMapFromSelectedTile(state)));
  });
  elements.hiddenToggle.addEventListener("change", () => editorCommand("toggle hidden", () => setSelectedTileFlags(state, { hiddenFromPlayers: elements.hiddenToggle.checked })));
  elements.blockedToggle.addEventListener("change", () => editorCommand("toggle blocked", () => setSelectedTileFlags(state, { blocked: elements.blockedToggle.checked })));
  elements.collisionPresetSelect?.addEventListener("change", () => editorCommand("collision preset", applyCollisionInspectorValues));
  [
    "collisionMovementToggle", "collisionVisionToggle", "collisionSoundToggle", "collisionProjectileToggle",
    "collisionReachToggle", "collisionShapeSelect", "collisionHeightInput", "soundTransmissionInput", "soundAbsorptionInput"
  ].forEach((id) => elements[id]?.addEventListener("change", () => editorCommand("collision properties", applyCollisionInspectorValues)));
  elements.childMapSelect.addEventListener("change", () => editorCommand("set child map", () => setSelectedTileChildMap(state, elements.childMapSelect.value)));
  elements.attachActionButton.addEventListener("click", () => editorCommand("attach action", () => attachActionToSelectedTile(state, elements.actionTypeSelect.value)));
  elements.attachTriggerButton.addEventListener("click", () => editorCommand("attach trigger", () => attachTriggerToSelectedTile(state, elements.triggerTypeSelect.value)));
  elements.attachEncounterButton.addEventListener("click", () => editorCommand("attach encounter", () => attachEncounterToSelectedTile(state, elements.encounterSelect.value)));
  elements.manualTriggerButton.addEventListener("click", () => commandResult(manualTriggerSelectedTile(state)));

  document.querySelectorAll("[data-encounter-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const type = button.dataset.encounterAction;
      const action = type === "move"
        ? { type, direction: button.dataset.dir }
        : { type, targetId: state.selectedEntityId };
      commandResult(executeEncounterAction(state, actor(), action));
    });
  });
  elements.issueCommanderButton.addEventListener("click", () => commandResult(issueCommanderOrder(state, actor(), elements.commanderOrder.value, { targetId: playerTargetId() })));
  elements.directOverrideButton.addEventListener("click", () => commandResult(directMonsterOverride(state, actor(), elements.monsterSelect.value, elements.directAction.value)));
  elements.runQueuedButton.addEventListener("click", () => commandResult(executeQueuedActionForActive(state)));
  elements.finishEncounterButton.addEventListener("click", () => commandResult(autoResolveEncounterToEnd(state)));

  elements.replaySelect.addEventListener("change", () => {
    state.replay.selectedReplayId = elements.replaySelect.value;
    initializeReplayDisplay();
    persistAndRender();
  });
  elements.replayRestartButton.addEventListener("click", () => {
    state.replay.cursor = 0;
    state.replay.playing = false;
    initializeReplayDisplay();
    renderAll();
  });
  elements.replayPlayButton.addEventListener("click", () => {
    state.replay.playing = true;
    renderAll();
  });
  elements.replayPauseButton.addEventListener("click", () => {
    state.replay.playing = false;
    renderAll();
  });
  elements.replayPrevButton.addEventListener("click", () => stepReplay(-1));
  elements.replayNextButton.addEventListener("click", () => stepReplay(1));
  elements.replayPrevRoundButton.addEventListener("click", () => stepReplayRound(-1));
  elements.replayNextRoundButton.addEventListener("click", () => stepReplayRound(1));
  elements.replaySpeedButton.addEventListener("click", () => {
    state.replay.speed = state.replay.speed === 1 ? 2 : 1;
    renderAll();
  });
  elements.replayInspectButton.addEventListener("click", () => {
    const combatants = state.replay.displayState?.combatants || [];
    const currentIndex = Math.max(0, combatants.findIndex((entity) => entity.id === state.replay.inspectedEntityId));
    const next = combatants[(currentIndex + 1) % Math.max(1, combatants.length)];
    state.replay.inspectedEntityId = next?.id || null;
    renderAll();
  });

  bindInput(canvas, {
    onPointerState: (active) => {
      state.input.pointerActive = active;
      if (!active) state.input.lastPointerCell = null;
      renderStatus();
    },
    onPointerDown: handlePointerDown,
    onPointerMove: handlePointerMove,
    onPointerRelease: handlePointerRelease,
    onContextMenu: handleCanvasContextMenu,
    onWheel: handleCanvasWheel,
    onShortcut: handleShortcut,
    onDirection: handleDirection
  });

  document.addEventListener("click", (event) => {
    if (!elements.tileContextMenu || elements.tileContextMenu.hidden) return;
    if (!elements.tileContextMenu.contains(event.target) && event.target !== canvas) closeContextMenu();
  });
  document.addEventListener("click", (event) => {
    if (!elements.moreMenu || elements.moreMenu.hidden) return;
    if (!elements.moreMenu.contains(event.target) && event.target !== elements.moreMenuButton) closeMoreMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (!["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement?.tagName) && event.code === "Space") {
      spacePanActive = true;
    }
    if (event.key !== "Escape") return;
    closeContextMenu();
    closeMoreMenu();
    closeOverlay(state.tabletop);
    renderAll();
  });
  document.addEventListener("keyup", (event) => {
    if (event.code === "Space") spacePanActive = false;
  });
  elements.tileContextMenu?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-context-action]");
    if (!button) return;
    handleContextAction(button.dataset.contextAction);
  });
  elements.tabletopOverlayBackdrop?.addEventListener("click", () => {
    closeOverlay(state.tabletop);
    persistAndRender();
  });
  elements.closeTabletopOverlayButton?.addEventListener("click", () => {
    closeOverlay(state.tabletop);
    persistAndRender();
  });
  elements.tabletopOverlayTabs?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-tabletop-category]");
    if (!button) return;
    openOverlay(state.tabletop, button.dataset.tabletopCategory);
    persistAndRender();
  });
  document.addEventListener("click", (event) => {
    const action = event.target.closest("[data-tabletop-action]")?.dataset.tabletopAction;
    if (!action) return;
    handleTabletopAction(action, event.target.closest("[data-card-id], [data-deck-id], [data-die-id]") || event.target);
  });
  document.addEventListener("dblclick", (event) => {
    const card = event.target.closest("[data-card-id]");
    const die = event.target.closest("[data-die-id]");
    if (card) handleTabletopAction("open-card", card);
    else if (die) handleTabletopAction("roll-die", die);
  });
  document.addEventListener("dragstart", (event) => {
    if (event.target.closest(".tabletop-object")) event.preventDefault();
  });
}

function handleTabletopAction(action, target = null) {
  if (!state?.tabletop) return;
  const deckId = target?.dataset?.deckId;
  const cardId = target?.dataset?.cardId;
  const dieId = target?.dataset?.dieId;
  let result = { ok: true };
  if (action === "open-menu") openOverlay(state.tabletop, target?.dataset?.tabletopCategory || "scene");
  else if (action === "close-menu") closeOverlay(state.tabletop);
  else if (action === "select-deck") result = selectDeck(state.tabletop, deckId);
  else if (action === "draw-card") result = drawTopCard(state.tabletop, deckId);
  else if (action === "select-card") result = selectCard(state.tabletop, cardId);
  else if (action === "select-die") {
    if (state.tabletop.dice[dieId]) state.tabletop.layout.selectedDieId = dieId;
  }
  else if (action === "open-card") {
    result = selectCard(state.tabletop, cardId);
    if (result.ok) openOverlay(state.tabletop, "cards", { cardId });
  } else if (action === "open-commander") {
    result = selectCard(state.tabletop, cardId || "card-orc-commander");
    openOverlay(state.tabletop, "decks", { cardId: cardId || "card-orc-commander", deckId: "deck-orcs-001" });
  } else if (action === "roll-die") result = rollDie(state.tabletop, dieId || "d20", { source: "tabletop_double_activation" });
  else if (action === "dice-bag") result = resolveDiceBagAction(state.tabletop, cardId || "card-weapon-sword-001", "attack", { baseAttack: state.characters["pc-lyra"]?.baseAttack || 3 });
  else if (action === "toggle-lore") result = toggleLoreScroll(state.tabletop);
  else if (action === "share-lore") result = shareLoreCard(state.tabletop, cardId || "card-lore-tavern-warning", "scene_shared");
  else if (action === "share-card") result = shareCard(state.tabletop, cardId || state.tabletop.layout.selectedCardId, "scene_shared");
  else if (action === "advance-initiative") result = advanceInitiative(state.tabletop);
  else if (action === "pause-clock") result = state.tabletop.initiative.paused ? resumeClock(state.tabletop) : pauseClock(state.tabletop);
  else if (action === "start-drag") result = startDrag(state.tabletop, target?.dataset?.dragType || "card", cardId || dieId || deckId, { source: "pointer" });
  else if (action === "end-drag") result = endDrag(state.tabletop, { type: "table" });
  else if (action === "toggle-reduced-motion") {
    state.tabletop.layout.reducedMotion = !state.tabletop.layout.reducedMotion;
  } else if (action === "open-selected-child") openSelectedChild();
  if (result && result.ok === false) pushMessage(state, result.message || "Tabletop action rejected.", "warn");
  persistAndRender();
}

function setRole(role) {
  state.role = role === "player" ? "player" : "gm";
  if (state.role === "player" && state.scene === SCENES.MAP_EDIT) state.scene = SCENES.MAP_VIEW;
  if (state.role === "player") {
    const tile = selectedTile(state);
    const map = getCurrentMap(state);
    if (tile?.hiddenFromPlayers || tile?.visible === false || (tile && !visibleForPlayer(state, map, coordinateFromCell(map, tile.x, tile.y), state.actorPlayerId))) clearMapSelection();
    closeContextMenu();
  }
  persistAndRender();
}

function setScene(scene) {
  if (scene === SCENES.MAP_EDIT && state.role !== "gm") return;
  if (scene === SCENES.REPLAY) {
    if (!state.replays.length) {
      pushMessage(state, "No replay has been saved.", "warn");
      renderAll();
      return;
    }
    state.scene = SCENES.REPLAY;
    state.replay.selectedReplayId = state.replay.selectedReplayId || state.replays.at(-1).replayId;
    initializeReplayDisplay();
  } else if (scene === SCENES.PAUSE) {
    state.previousScene = state.scene;
    state.scene = SCENES.PAUSE;
  } else {
    state.scene = scene;
  }
  persistAndRender();
}

function actor() {
  return { role: state.role, playerId: state.actorPlayerId };
}

function playerTargetId() {
  const target = state.activeEncounter?.combatants.find((entity) => entity.id === state.selectedEntityId && entity.faction === "players" && !entity.defeated);
  return target?.id || null;
}

function commandResult(result) {
  Promise.resolve(result)
    .then((value) => {
      if (value && value.ok === false) pushMessage(state, value.message || "Command rejected.", "warn");
      persistAndRender();
    })
    .catch((error) => {
      setText("errorStatus", error.message);
      console.error(error);
    });
}

function editorCommand(label, operation) {
  const before = captureEditState(state, label);
  const undoCount = state.editor.undoStack.length;
  Promise.resolve(operation())
    .then((value) => {
      if (value && value.ok !== false && state.editor.undoStack.length === undoCount) recordEditorHistory(state, before);
      if (value && value.ok === false) pushMessage(state, value.message || "Editor command rejected.", "warn");
      persistAndRender();
    })
    .catch((error) => {
      setText("errorStatus", error.message);
      console.error(error);
    });
}

function handleEditorCommand(command) {
  if (!state || state.role !== "gm") return;
  if (command === "undo") commandResult(undoEditorEdit(state));
  else if (command === "redo") commandResult(redoEditorEdit(state));
  else if (command === "copy") commandResult(copySelectedTile(state));
  else if (command === "paste") {
    const map = getCurrentMap(state);
    const cell = state.selection || selectionForCell(map, coordinateFromCell(map, 0, 0));
    editorCommand("paste tile", () => pasteCopiedTile(state, map, cell));
  } else if (command === "clear") editorCommand("clear tile", () => clearSelectedTileContent(state));
  else if (command === "delete") editorCommand("delete tile", () => removeSelectedTile(state));
  else if (command === "map-settings") openMapSettings();
}

function currentViewport() {
  const map = currentRenderedMap();
  const key = map.id;
  state.editor.viewportByMap[key] = state.editor.viewportByMap[key] || defaultViewport();
  const viewport = state.editor.viewportByMap[key];
  viewport.zoom = clamp(Number(viewport.zoom) || 1, 0.25, 4);
  viewport.zoom = Math.max(viewport.zoom, minimumAllowedZoomForPlayer(map));
  viewport.offsetX = Number(viewport.offsetX) || 0;
  viewport.offsetY = Number(viewport.offsetY) || 0;
  viewport.rotationDeg = normalizeRotation(viewport.rotationDeg);
  viewport.fitMode = viewport.fitMode || "fit-map";
  viewport.gridVisible = viewport.gridVisible !== false;
  viewport.compassVisible = viewport.compassVisible !== false;
  return viewport;
}

function defaultViewport() {
  return {
    zoom: 1,
    offsetX: 0,
    offsetY: 0,
    rotationDeg: 0,
    fitMode: "fit-map",
    gridVisible: true,
    compassVisible: true,
    initialized: false
  };
}

function minimumAllowedZoomForPlayer(map) {
  if (!state || state.role !== "player" || state.scene !== SCENES.MAP_VIEW) return 0.25;
  const perception = computePlayerPerception(state, map, state.actorPlayerId, { updateKnowledge: true });
  const bounds = perceptionZoomBounds(map, perception);
  const width = Math.max(1, viewportElement?.clientWidth || canvas?.clientWidth || 1);
  const height = Math.max(1, viewportElement?.clientHeight || canvas?.clientHeight || 1);
  const minZoom = Math.max(width / bounds.diameterPixels, height / bounds.diameterPixels);
  return clamp(minZoom, 0.25, 4);
}

function screenToWorld(point) {
  const viewport = currentViewport();
  const local = {
    x: (point.x - viewport.offsetX) / viewport.zoom,
    y: (point.y - viewport.offsetY) / viewport.zoom
  };
  return inverseTransformWorldPoint(local, viewport);
}

function worldToScreen(point) {
  const viewport = currentViewport();
  const local = transformWorldPoint(point, viewport);
  return {
    x: local.x * viewport.zoom + viewport.offsetX,
    y: local.y * viewport.zoom + viewport.offsetY
  };
}

function zoomViewport(factor, focusPoint = null) {
  const viewport = currentViewport();
  const focus = focusPoint || { x: canvas.clientWidth / 2, y: canvas.clientHeight / 2 };
  const world = screenToWorld(focus);
  viewport.zoom = clamp(viewport.zoom * factor, minimumAllowedZoomForPlayer(currentRenderedMap()), 4);
  viewport.fitMode = "custom";
  viewport.initialized = true;
  centerScreenOnWorld(world, focus);
  persistAndRender();
}

function fitCurrentMap(options = {}) {
  fitMapMode("fit-map", options);
}

function fitMapMode(mode = "fit-map", options = {}) {
  const map = currentRenderedMap();
  const viewport = currentViewport();
  if (options.onlyIfUninitialized && viewport.initialized) return;
  const bounds = mapPixelBounds(map);
  const rotated = transformedMapBounds(map, viewport);
  const width = Math.max(1, viewportElement?.clientWidth || canvas.clientWidth || 1);
  const height = Math.max(1, viewportElement?.clientHeight || canvas.clientHeight || 1);
  const pad = 0.94;
  let zoom = Math.min(width / rotated.width, height / rotated.height) * pad;
  if (mode === "fit-width") zoom = (width / rotated.width) * pad;
  if (mode === "fit-height") zoom = (height / rotated.height) * pad;
  zoom = clamp(zoom, 0.25, 4);
  zoom = Math.max(zoom, minimumAllowedZoomForPlayer(map));
  viewport.zoom = zoom;
  viewport.offsetX = (width - rotated.width * zoom) / 2 - rotated.minX * zoom;
  viewport.offsetY = (height - rotated.height * zoom) / 2 - rotated.minY * zoom;
  viewport.fitMode = mode;
  viewport.initialized = true;
  if (options.persist !== false) persistAndRender();
}

function fitSelection(options = {}) {
  const map = currentRenderedMap();
  const selection = state.selection?.mapId === map.id ? state.selection : null;
  if (!selection) return fitCurrentMap(options);
  const center = cellCenter(map, selection.coordinates);
  const viewport = currentViewport();
  viewport.zoom = clamp(Math.max(viewport.zoom, 2), 0.25, 4);
  viewport.zoom = Math.max(viewport.zoom, minimumAllowedZoomForPlayer(map));
  viewport.fitMode = "fit-selection";
  viewport.initialized = true;
  centerScreenOnWorld(center, {
    x: (viewportElement?.clientWidth || canvas.clientWidth) / 2,
    y: (viewportElement?.clientHeight || canvas.clientHeight) / 2
  });
  if (options.persist !== false) persistAndRender();
}

function resetCurrentViewport() {
  const viewport = currentViewport();
  viewport.zoom = 1;
  viewport.zoom = Math.max(viewport.zoom, minimumAllowedZoomForPlayer(currentRenderedMap()));
  viewport.offsetX = 0;
  viewport.offsetY = 0;
  viewport.rotationDeg = 0;
  viewport.fitMode = "actual-size";
  viewport.initialized = true;
  persistAndRender();
}

function setActualSize(options = {}) {
  const viewport = currentViewport();
  const worldCenter = viewportCenterWorld();
  viewport.zoom = 1;
  viewport.zoom = Math.max(viewport.zoom, minimumAllowedZoomForPlayer(currentRenderedMap()));
  viewport.fitMode = "actual-size";
  viewport.initialized = true;
  centerScreenOnWorld(worldCenter);
  if (options.persist !== false) persistAndRender();
}

function rotateViewport(delta) {
  const viewport = currentViewport();
  const center = viewportCenterWorld();
  viewport.rotationDeg = normalizeRotation(viewport.rotationDeg + delta);
  viewport.initialized = true;
  if (["fit-map", "fit-width", "fit-height"].includes(viewport.fitMode)) fitMapMode(viewport.fitMode, { persist: false });
  else centerScreenOnWorld(center);
  persistAndRender();
}

function resetRotation() {
  const viewport = currentViewport();
  const center = viewportCenterWorld();
  viewport.rotationDeg = 0;
  if (["fit-map", "fit-width", "fit-height"].includes(viewport.fitMode)) fitMapMode(viewport.fitMode, { persist: false });
  else centerScreenOnWorld(center);
  persistAndRender();
}

function normalizeRotation(value) {
  const angle = Number.isFinite(Number(value)) ? Number(value) : 0;
  return ((Math.round(angle / 90) * 90) % 360 + 360) % 360;
}

function viewportCenterWorld() {
  return screenToWorld({
    x: (viewportElement?.clientWidth || canvas.clientWidth || 1) / 2,
    y: (viewportElement?.clientHeight || canvas.clientHeight || 1) / 2
  });
}

function centerScreenOnWorld(world, screenPoint = null) {
  const viewport = currentViewport();
  const target = screenPoint || {
    x: (viewportElement?.clientWidth || canvas.clientWidth || 1) / 2,
    y: (viewportElement?.clientHeight || canvas.clientHeight || 1) / 2
  };
  const transformed = transformWorldPoint(world, viewport);
  viewport.offsetX = target.x - transformed.x * viewport.zoom;
  viewport.offsetY = target.y - transformed.y * viewport.zoom;
}

function transformWorldPoint(point, viewport = currentViewport()) {
  const center = mapViewCenter();
  const radians = (normalizeRotation(viewport.rotationDeg) * Math.PI) / 180;
  const dx = point.x - center.x;
  const dy = point.y - center.y;
  return {
    x: center.x + dx * Math.cos(radians) - dy * Math.sin(radians),
    y: center.y + dx * Math.sin(radians) + dy * Math.cos(radians)
  };
}

function inverseTransformWorldPoint(point, viewport = currentViewport()) {
  const center = mapViewCenter();
  const radians = (-normalizeRotation(viewport.rotationDeg) * Math.PI) / 180;
  const dx = point.x - center.x;
  const dy = point.y - center.y;
  return {
    x: center.x + dx * Math.cos(radians) - dy * Math.sin(radians),
    y: center.y + dx * Math.sin(radians) + dy * Math.cos(radians)
  };
}

function mapViewCenter() {
  const bounds = mapPixelBounds(currentRenderedMap());
  return { x: bounds.minX + bounds.width / 2, y: bounds.minY + bounds.height / 2 };
}

function transformedMapBounds(map, viewport = currentViewport()) {
  const bounds = mapPixelBounds(map);
  const corners = [
    { x: bounds.minX, y: bounds.minY },
    { x: bounds.maxX, y: bounds.minY },
    { x: bounds.maxX, y: bounds.maxY },
    { x: bounds.minX, y: bounds.maxY }
  ].map((point) => transformWorldPoint(point, viewport));
  const xs = corners.map((point) => point.x);
  const ys = corners.map((point) => point.y);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const maxX = Math.max(...xs);
  const maxY = Math.max(...ys);
  return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY };
}

function handleZoomSelect() {
  const value = elements.zoomSelect.value;
  if (value === "fit-map") fitMapMode("fit-map");
  else if (value === "fit-width") fitMapMode("fit-width");
  else if (value === "fit-height") fitMapMode("fit-height");
  else if (value === "actual-size") setActualSize();
  else if (value === "fit-selection") fitSelection();
  else {
    const viewport = currentViewport();
    const center = viewportCenterWorld();
    viewport.zoom = clamp(Number(value) || viewport.zoom, minimumAllowedZoomForPlayer(currentRenderedMap()), 4);
    viewport.fitMode = "custom";
    viewport.initialized = true;
    centerScreenOnWorld(center);
    persistAndRender();
  }
}

function bindViewportResize() {
  const observer = new ResizeObserver(() => handleWorkspaceResize());
  if (viewportElement) observer.observe(viewportElement);
  window.addEventListener("resize", handleWorkspaceResize);
}

function handleWorkspaceResize() {
  if (!state || !canvas || !viewportElement) return;
  const viewport = currentViewport();
  const center = viewportCenterWorld();
  if (["fit-map", "fit-width", "fit-height"].includes(viewport.fitMode)) fitMapMode(viewport.fitMode, { persist: false });
  else centerScreenOnWorld(center);
  renderAll();
}

function beginInspectorResize(event) {
  if (!state || window.innerWidth < 900) return;
  event.preventDefault();
  const startX = event.clientX;
  const startWidth = state.editor.inspectorWidth || 336;
  const move = (moveEvent) => {
    const delta = startX - moveEvent.clientX;
    state.editor.inspectorWidth = clamp(startWidth + delta, 288, 440);
    document.documentElement.style.setProperty("--inspector-w", `${state.editor.inspectorWidth}px`);
  };
  const release = () => {
    window.removeEventListener("pointermove", move);
    window.removeEventListener("pointerup", release);
    persistAndRender();
  };
  window.addEventListener("pointermove", move);
  window.addEventListener("pointerup", release, { once: true });
}

function clearMapSelection() {
  state.selection = null;
  state.selectedTileId = null;
  state.selectedAtlasInstanceId = null;
}

function clearLongPressTimer() {
  if (longPressTimer) {
    window.clearTimeout(longPressTimer);
    longPressTimer = null;
  }
}

function startPinch() {
  const viewport = currentViewport();
  return {
    distance: currentPinchDistance(),
    angle: currentPinchAngle(),
    startZoom: viewport.zoom,
    startRotation: viewport.rotationDeg
  };
}

function currentPinchDistance() {
  const points = [...activePointers.values()];
  if (points.length < 2) return 0;
  return Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
}

function currentPinchAngle() {
  const points = [...activePointers.values()];
  if (points.length < 2) return 0;
  return angleDeg(points[0], points[1]);
}

function midpoint(points) {
  return {
    x: points.reduce((sum, point) => sum + point.x, 0) / points.length,
    y: points.reduce((sum, point) => sum + point.y, 0) / points.length
  };
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function finiteClamp(value, fallback, min, max) {
  const parsed = Number(value);
  return clamp(Number.isFinite(parsed) ? parsed : fallback, min, max);
}

function openContextMenuAt(point, cell) {
  if (!elements.tileContextMenu || state.role !== "gm" || state.scene !== SCENES.MAP_EDIT) return;
  const map = getCurrentMap(state);
  if (cell) selectCell(state, map, cell);
  const tile = selectedTile(state);
  state.editor.contextMenu = {
    open: true,
    x: point.clientX ?? point.x,
    y: point.clientY ?? point.y,
    cell: cell ? deepClone(cell) : null,
    tileId: tile?.id || null
  };
  renderContextMenu();
}

function openTabletopMapMenu(point, cell) {
  const map = currentRenderedMap();
  if (cell) selectCell(state, map, cell);
  openOverlay(state.tabletop, "map");
  state.input.lastGesture = {
    type: "long_press_menu",
    mapId: map.id,
    cellId: cell?.cellId || null,
    point: { x: point.clientX ?? point.x, y: point.clientY ?? point.y }
  };
  renderAll();
}

function openMoreMenu() {
  if (!elements.moreMenu || !elements.moreMenuButton) return;
  state.editor.moreMenuOpen = !state.editor.moreMenuOpen;
  renderMoreMenu();
}

function closeMoreMenu() {
  if (!state?.editor) return;
  state.editor.moreMenuOpen = false;
  if (elements.moreMenu) elements.moreMenu.hidden = true;
  if (elements.moreMenuButton) elements.moreMenuButton.setAttribute("aria-expanded", "false");
}

function renderMoreMenu() {
  const menu = elements.moreMenu;
  if (!menu) return;
  if (!state.editor.moreMenuOpen) {
    menu.hidden = true;
    elements.moreMenuButton?.setAttribute("aria-expanded", "false");
    return;
  }
  menu.hidden = false;
  elements.moreMenuButton?.setAttribute("aria-expanded", "true");
  const anchor = elements.moreMenuButton?.getBoundingClientRect();
  const rect = menu.getBoundingClientRect();
  const x = anchor ? anchor.right - rect.width : window.innerWidth - rect.width - 8;
  const y = anchor ? anchor.bottom + 6 : 44;
  menu.style.left = `${Math.min(window.innerWidth - rect.width - 8, Math.max(8, x))}px`;
  menu.style.top = `${Math.min(window.innerHeight - rect.height - 8, Math.max(8, y))}px`;
}

function handleMoreAction(action) {
  if (action === "fit-width") fitMapMode("fit-width");
  else if (action === "fit-height") fitMapMode("fit-height");
  else if (action === "actual-size") setActualSize();
  else if (action === "fit-selection") fitSelection();
  else if (action === "reset-view") resetCurrentViewport();
  else if (action === "toggle-grid") {
    const viewport = currentViewport();
    viewport.gridVisible = !viewport.gridVisible;
    persistAndRender();
  } else if (action === "toggle-compass") {
    const viewport = currentViewport();
    viewport.compassVisible = !viewport.compassVisible;
    persistAndRender();
  } else if (action === "toggle-perception-debug" && state.role === "gm") {
    state.editor.perceptionDebug.enabled = !state.editor.perceptionDebug.enabled;
    persistAndRender();
  } else if (action === "map-settings") openMapSettings();
}

function closeContextMenu() {
  if (!state?.editor) return;
  state.editor.contextMenu.open = false;
  if (elements.tileContextMenu) elements.tileContextMenu.hidden = true;
}

function renderContextMenu() {
  const menu = elements.tileContextMenu;
  if (!menu) return;
  const contextMenu = state.editor.contextMenu;
  if (state.role !== "gm" || state.scene !== SCENES.MAP_EDIT || !contextMenu.open) {
    menu.hidden = true;
    return;
  }
  const map = getCurrentMap(state);
  const tile = selectedTile(state);
  setText("contextMenuTitle", tile ? tile.metadata?.label || tile.id : "Empty cell");
  const available = new Set(["select", "inspect", "change_terrain", "paste"]);
  if (tile) {
    [
      "edit", "set_image", "remove_image", "toggle_hidden", "toggle_blocked", "attach_action", "attach_trigger",
      "attach_encounter", "create_child", "delete", "copy", "clear"
    ].forEach((action) => available.add(action));
    if (tile.childMapId) available.add("open_child");
  }
  menu.querySelectorAll("[data-context-action]").forEach((button) => {
    button.hidden = !available.has(button.dataset.contextAction);
  });
  menu.hidden = false;
  const rect = menu.getBoundingClientRect();
  const x = Math.min(window.innerWidth - rect.width - 8, Math.max(8, contextMenu.x));
  const y = Math.min(window.innerHeight - rect.height - 8, Math.max(8, contextMenu.y));
  menu.style.left = `${x}px`;
  menu.style.top = `${y}px`;
}

function handleContextAction(action) {
  const map = getCurrentMap(state);
  const cell = state.editor.contextMenu.cell || state.selection;
  closeContextMenu();
  if (action === "select" || action === "inspect" || action === "edit") {
    if (cell) selectCell(state, map, cell);
    state.editor.inspectorOpen = true;
    persistAndRender();
    return;
  }
  if (action === "change_terrain") editorCommand("context terrain", () => paintTerrainAtCell(state, map, cell, state.selectedPaletteId));
  else if (action === "set_image") editorCommand("context image", () => setSelectedTileImage(state, state.selectedTileImageAssetId || elements.assetSelect?.value));
  else if (action === "remove_image") editorCommand("context remove image", () => setSelectedTileImage(state, ""));
  else if (action === "toggle_hidden") editorCommand("context hidden", () => setSelectedTileFlags(state, { hiddenFromPlayers: !selectedTile(state)?.hiddenFromPlayers }));
  else if (action === "toggle_blocked") editorCommand("context blocked", () => setSelectedTileFlags(state, { blocked: !selectedTile(state)?.blocked }));
  else if (action === "attach_action") editorCommand("context action", () => attachActionToSelectedTile(state, elements.actionTypeSelect.value));
  else if (action === "attach_trigger") editorCommand("context trigger", () => attachTriggerToSelectedTile(state, elements.triggerTypeSelect.value));
  else if (action === "attach_encounter") editorCommand("context encounter", () => attachEncounterToSelectedTile(state, elements.encounterSelect.value));
  else if (action === "create_child") {
    import("./maps.js").then((module) => editorCommand("context child map", () => module.createChildMapFromSelectedTile(state)));
  } else if (action === "open_child") openSelectedChild();
  else if (action === "delete") editorCommand("context delete", () => removeSelectedTile(state));
  else if (action === "copy") commandResult(copySelectedTile(state));
  else if (action === "paste") editorCommand("context paste", () => pasteCopiedTile(state, map, cell));
  else if (action === "clear") editorCommand("context clear", () => clearSelectedTileContent(state));
}

function openMapSettings() {
  const map = getCurrentMap(state);
  normalizeMapGeometry(map);
  elements.settingsMapName.value = map.name;
  elements.settingsMapId.value = map.id;
  elements.settingsGridType.value = map.gridType;
  elements.settingsHexOrientation.value = map.gridSettings.hex?.orientation || "pointy";
  elements.settingsSizeMode.value = "tile-count";
  elements.settingsColumns.value = map.width;
  elements.settingsRows.value = map.height;
  elements.settingsPhysicalWidth.value = map.gridType === "square"
    ? map.width * (map.gridSettings.square?.cellWidth || 5)
    : Math.ceil(deriveHexCoverage({ mapWidth: 80, mapHeight: 50, hexRadius: map.gridSettings.hex?.radius || 5, orientation: map.gridSettings.hex?.orientation || "pointy" }).actualWidth);
  elements.settingsPhysicalHeight.value = map.gridType === "square"
    ? map.height * (map.gridSettings.square?.cellHeight || 5)
    : Math.ceil(deriveHexCoverage({ mapWidth: 80, mapHeight: 50, hexRadius: map.gridSettings.hex?.radius || 5, orientation: map.gridSettings.hex?.orientation || "pointy" }).actualHeight);
  elements.settingsUnitSystem.value = map.gridSettings[map.gridType]?.unitSystem || "imperial";
  elements.settingsDistanceUnit.value = map.gridSettings[map.gridType]?.distanceUnit || "ft";
  elements.settingsCellWidth.value = map.gridSettings.square?.cellWidth || 5;
  elements.settingsCellHeight.value = map.gridSettings.square?.cellHeight || 5;
  elements.settingsHexRadius.value = map.gridSettings.hex?.radius || 5;
  elements.settingsTileSize.value = map.tileSize;
  elements.settingsDefaultTerrain.value = map.terrain?.default || "grass";
  elements.settingsPlayerVisibility.value = map.permissions?.player?.canView === false ? "hidden" : "visible";
  elements.mapSettingsConfirmShrink.checked = false;
  updateMapSettingsPreview();
  if (typeof elements.mapSettingsDialog.showModal === "function") elements.mapSettingsDialog.showModal();
  else elements.mapSettingsDialog.hidden = false;
}

function closeMapSettings() {
  if (!elements.mapSettingsDialog) return;
  if (typeof elements.mapSettingsDialog.close === "function") elements.mapSettingsDialog.close();
  else elements.mapSettingsDialog.hidden = true;
}

function readMapSettingsForm() {
  return {
    name: elements.settingsMapName.value,
    id: elements.settingsMapId.value,
    gridType: elements.settingsGridType.value,
    orientation: elements.settingsHexOrientation.value,
    sizeMode: elements.settingsSizeMode.value,
    columns: Number(elements.settingsColumns.value),
    rows: Number(elements.settingsRows.value),
    width: Number(elements.settingsPhysicalWidth.value),
    height: Number(elements.settingsPhysicalHeight.value),
    mapWidth: Number(elements.settingsPhysicalWidth.value),
    mapHeight: Number(elements.settingsPhysicalHeight.value),
    unitSystem: elements.settingsUnitSystem.value,
    distanceUnit: elements.settingsDistanceUnit.value,
    cellWidth: Number(elements.settingsCellWidth.value),
    cellHeight: Number(elements.settingsCellHeight.value),
    hexRadius: Number(elements.settingsHexRadius.value),
    tileSize: Number(elements.settingsTileSize.value),
    defaultTerrain: elements.settingsDefaultTerrain.value,
    playerVisibilityDefault: elements.settingsPlayerVisibility.value
  };
}

function updateMapSettingsPreview() {
  if (!elements.mapSettingsPreview || !state) return;
  const input = readMapSettingsForm();
  const derived = deriveMapSettings(input);
  const map = getCurrentMap(state);
  const columns = derived.ok ? Math.round(derived.columns) : Number(input.columns);
  const rows = derived.ok ? Math.round(derived.rows) : Number(input.rows);
  const impact = Number.isFinite(columns) && Number.isFinite(rows) ? previewResizeImpact(map, columns, rows) : null;
  const lines = [];
  if (!derived.ok) lines.push(`Rejected: ${derived.message}`);
  else if (derived.gridType === "hex") {
    lines.push(`Hex ${derived.orientation}, radius ${derived.radius} ${derived.distanceUnit}, center-to-corner.`);
    if (input.sizeMode === "physical") {
      lines.push(`Requested ${derived.requestedWidth}x${derived.requestedHeight}; derived ${derived.columns}x${derived.rows}; covers ${derived.actualWidth}x${derived.actualHeight}; delta ${derived.deltaWidth}, ${derived.deltaHeight}.`);
    } else {
      lines.push(`Tile-count bounds ${derived.columns} columns x ${derived.rows} rows.`);
    }
  } else {
    lines.push(`Square ${columns}x${rows}; cell ${input.cellWidth || 5}x${input.cellHeight || 5} ${input.distanceUnit}.`);
    if (input.sizeMode === "physical") lines.push(`Whole-cell result: ${derived.wholeCells ? "yes" : "no"}.`);
  }
  if (impact && (impact.removedTiles.length || impact.removedEntities.length || impact.removedTerrain)) {
    lines.push(`Shrink impact: ${impact.removedTiles.length} tiles, ${impact.removedEntities.length} entities, ${impact.removedTerrain} terrain overrides. Protected attachments: ${impact.protectedContentCount}.`);
  } else {
    lines.push("Resize impact: no content would be removed.");
  }
  elements.mapSettingsPreview.textContent = lines.join("\n");
}

function applyCurrentMapSettings() {
  editorCommand("map settings", () => applyMapSettings(state, readMapSettingsForm(), { confirmShrink: elements.mapSettingsConfirmShrink.checked }));
  closeMapSettings();
}

async function inspectSelectedAssetFile() {
  const file = elements.assetFileInput.files?.[0];
  if (!file) return;
  const result = await hashBrowserFile(file);
  if (!result.ok) {
    setText("assetImportStatus", result.message);
    return;
  }
  const duplicate = duplicateAssetByHash(state.tileAssetRegistry, result.contentHash);
  setText(
    "assetImportStatus",
    duplicate
      ? `Duplicate image hash matches ${duplicate.name}. Reuse registered asset ${duplicate.assetId}.`
      : `Image is valid (${result.mimeType}, ${result.contentHash.slice(0, 12)}). Static build needs the approved upload endpoint before registration.`
  );
}

function persistAndRender() {
  refreshPerceptionForCurrentView();
  saveState(state);
  renderAll();
}

function refreshPerceptionForCurrentView() {
  if (!state || state.scene !== SCENES.MAP_VIEW || state.role !== "player") return null;
  const map = getCurrentMap(state);
  return computePlayerPerception(state, map, state.actorPlayerId, { updateKnowledge: true });
}

async function resetApplication() {
  clearSavedState();
  state = createGameState(bundleCache);
  state.scene = SCENES.MAP_VIEW;
  if (window.innerWidth < 900) {
    state.editor.inspectorOpen = false;
    state.editor.inspectorSheetState = "collapsed";
  }
  buildSpriteCache();
  buildAssetImageCache();
  persistAndRender();
}

function openSelectedChild() {
  const map = getCurrentMap(state);
  const tile = findTile(map, state.selectedTileId);
  commandResult(tile ? openChildMapFromTile(state, tile, actor()) : { ok: false, message: "No tile selected." });
}

function placeSelectedAtlasAsset() {
  const map = getCurrentMap(state);
  const coordinates = state.selection?.mapId === map.id ? state.selection.coordinates : null;
  return createAtlasInstance(state, map, state.selectedAtlasAssetId, coordinates);
}

function openSelectedAtlasChild() {
  const map = getCurrentMap(state);
  const instance = findAtlasInstance(map, state.selectedAtlasInstanceId);
  if (!instance) {
    commandResult({ ok: false, message: "No Atlas instance selected." });
    return;
  }
  if (!instance.childMapId || !state.maps[instance.childMapId]) {
    commandResult({ ok: false, message: "Selected Atlas instance has no child map." });
    return;
  }
  const previousMapId = map.id;
  state.currentMapId = instance.childMapId;
  state.lastValidMapId = state.currentMapId;
  state.selectedTileId = null;
  state.selectedAtlasInstanceId = null;
  state.selection = null;
  recordEvent(state, "atlas_child_map_entered", {
    parentMapId: previousMapId,
    childMapId: state.currentMapId,
    atlasInstanceId: instance.instanceId,
    actorRole: state.role
  });
  fitCurrentMap({ persist: false });
  persistAndRender();
}

function interactSelectedTile() {
  const map = getCurrentMap(state);
  const tile = findTile(map, state.selectedTileId);
  if (!tile) {
    pushMessage(state, "No tile selected.", "warn");
    renderAll();
    return;
  }
  if (state.role === "player" && !visibleForPlayer(state, map, coordinateFromCell(map, tile.x, tile.y), state.actorPlayerId)) {
    recordEvent(state, "action_executed", { tileId: tile.id, reason: "tile not currently visible", actorRole: "player" }, { rejected: true, stateChanging: false });
    pushMessage(state, "That tile is not currently visible.", "warn");
    renderAll();
    return;
  }
  const beforeScene = state.scene;
  const result = executeFirstTileAction(state, tile, actor());
  if (result.ok && beforeScene === SCENES.MAP_VIEW && state.scene === SCENES.MAP_VIEW) {
    processMapEvent(state, "player_interacts", { sourceTileId: tile.id, actorRole: state.role });
  }
  commandResult(result);
}

function placeSelectedOwnedPc() {
  const map = getCurrentMap(state);
  const cell = state.selection?.mapId === map.id ? state.selection : null;
  if (!cell) {
    pushMessage(state, "Select an authorized start cell first.", "warn");
    renderAll();
    return;
  }
  const entity = controlledPlayerEntityForUi(map);
  commandResult(placeOwnedPlayerCharacter(state, map, entity?.id || state.selectedEntityId, cell.coordinates, actor()));
}

function controlledPlayerEntityForUi(map = getCurrentMap(state)) {
  const selected = map.entities.find((entity) => entity.id === state.selectedEntityId && entity.controller === "player" && entity.assignedPlayerId === state.actorPlayerId);
  return selected || map.entities.find((entity) => entity.controller === "player" && entity.assignedPlayerId === state.actorPlayerId) || null;
}

function applyCollisionInspectorValues() {
  const tile = selectedTile(state);
  if (!tile) return { ok: false, message: "No tile selected." };
  const presetId = elements.collisionPresetSelect?.value || tile.collisionPresetId || "decorative";
  const collision = presetCollision(presetId, state.collisionPresets);
  const shape = presetShape(presetId, state.collisionPresets, getCurrentMap(state));
  const patch = {
    collisionPresetId: presetId,
    blocked: elements.collisionMovementToggle?.checked === true,
    collision: {
      ...collision,
      ...(tile.collision || {}),
      blocksMovement: elements.collisionMovementToggle?.checked === true,
      blocksVision: elements.collisionVisionToggle?.checked === true,
      blocksSound: elements.collisionSoundToggle?.checked === true,
      blocksProjectile: elements.collisionProjectileToggle?.checked === true,
      blocksReach: elements.collisionReachToggle?.checked === true,
      height: Number(elements.collisionHeightInput?.value) || collision.height,
      soundTransmission: finiteClamp(elements.soundTransmissionInput?.value, collision.soundTransmission ?? 1, 0, 1),
      soundAbsorption: finiteClamp(elements.soundAbsorptionInput?.value, collision.soundAbsorption ?? 0, 0, 1),
      opacity: elements.collisionVisionToggle?.checked === true ? Math.max(tile.collision?.opacity || 0, 1) : tile.collision?.opacity || collision.opacity || 0
    },
    collisionShape: {
      ...shape,
      ...(tile.collisionShape || {}),
      type: elements.collisionShapeSelect?.value || shape.type,
      height: Number(elements.collisionHeightInput?.value) || shape.height
    }
  };
  return setSelectedTileFlags(state, patch);
}

function handleDirection(direction) {
  if (!state) return;
  const vector = directionVector(direction);
  if (state.scene === SCENES.MAP_EDIT && state.role === "gm") {
    editorCommand("keyboard tile move", () => moveSelectedTile(state, vector.dx, vector.dy));
    return;
  }
  if (state.scene === SCENES.ENCOUNTER) {
    commandResult(executeEncounterAction(state, actor(), { type: "move", direction }));
    return;
  }
  const map = getCurrentMap(state);
  const entity = findEntity(map, state.selectedEntityId) || map.entities.find((item) => item.assignedPlayerId === state.actorPlayerId);
  if (!entity) return;
  const result = moveExplorationEntity(state, entity.id, vector.dx, vector.dy, actor());
  if (result.ok && actor().role === "player") {
    processMapEvent(state, "player_enters_tile", { entityId: entity.id, from: result.from, to: result.to, actorRole: "player" });
  }
  commandResult(result);
}

function handlePointerDown(point, event) {
  if (!state) return;
  closeContextMenu();
  closeMoreMenu();
  const pointerId = event.pointerId ?? 1;
  activePointers.set(pointerId, point);
  const world = screenToWorld(point);
  const map = currentRenderedMap();
  const cell = worldToCell(map, world);
  const placementTools = new Set(["paint", "erase", "fill", "child", "trigger", "encounter", "entity-start"]);
  const canDirectDragPan = event.pointerType === "touch" && !placementTools.has(state.editor.activeTool) && state.scene !== SCENES.ENCOUNTER && state.scene !== SCENES.REPLAY;
  state.input.lastPointerCell = cell?.coordinates || null;
  gesture = {
    pointerId,
    pointerType: event.pointerType || "mouse",
    startPoint: point,
    previousPoint: point,
    startWorld: world,
    cell,
    moved: false,
    panning: state.editor.activeTool === "pan" || event.button === 1 || event.button === 2 || (spacePanActive && event.button === 0),
    canPanOnDrag: canDirectDragPan,
    longPressed: false
  };
  if (activePointers.size === 2) {
    gesture.panning = false;
    gesture.pinch = startPinch();
    gesture.mode = "pinch";
    clearLongPressTimer();
  } else if (event.pointerType === "touch" && state.scene !== SCENES.ENCOUNTER && state.scene !== SCENES.REPLAY) {
    clearLongPressTimer();
    longPressTimer = window.setTimeout(() => {
      if (!gesture || gesture.moved || gesture.pointerId !== pointerId) return;
      gesture.longPressed = true;
      if (state.role === "gm" && state.scene === SCENES.MAP_EDIT) openContextMenuAt(point, cell);
      else openTabletopMapMenu(point, cell);
    }, state.editor.longPressMs);
  }
}

function handlePointerMove(point, event) {
  if (!state) return;
  const pointerId = event.pointerId ?? 1;
  if (activePointers.has(pointerId)) activePointers.set(pointerId, point);
  if (activePointers.size === 2 && gesture?.pinch) {
    const next = currentPinchDistance();
    if (next > 0 && gesture.pinch.distance > 0) {
      const focus = gestureMidpoint([...activePointers.values()]);
      const worldBefore = screenToWorld(focus);
      const viewport = currentViewport();
      viewport.zoom = clamp(gesture.pinch.startZoom * (next / gesture.pinch.distance), minimumAllowedZoomForPlayer(currentRenderedMap()), 4);
      const angleDelta = currentPinchAngle() - gesture.pinch.angle;
      viewport.rotationDeg = snapRotationDeg(gesture.pinch.startRotation + angleDelta);
      viewport.fitMode = "custom";
      viewport.initialized = true;
      centerScreenOnWorld(worldBefore, focus);
      renderAll();
    }
    return;
  }
  if (!gesture || gesture.pointerId !== pointerId) return;
  const dx = point.x - gesture.previousPoint.x;
  const dy = point.y - gesture.previousPoint.y;
  const total = Math.hypot(point.x - gesture.startPoint.x, point.y - gesture.startPoint.y);
  if (total > 7) {
    gesture.moved = true;
    clearLongPressTimer();
    if (gesture.canPanOnDrag) gesture.panning = true;
  }
  if (gesture.panning || (state.editor.activeTool === "pan" && event.buttons)) {
    const viewport = currentViewport();
    viewport.offsetX += dx;
    viewport.offsetY += dy;
    renderAll();
  }
  gesture.previousPoint = point;
}

function handlePointerRelease(point, event) {
  const pointerId = event.pointerId ?? 1;
  activePointers.delete(pointerId);
  clearLongPressTimer();
  if (gesture?.pinch && activePointers.size < 2) {
    currentViewport().rotationDeg = snapRotationDeg(currentViewport().rotationDeg);
    activePointers.clear();
    persistAndRender();
    gesture = null;
    return;
  }
  if (!gesture || gesture.pointerId !== pointerId) return;
  const currentGesture = gesture;
  gesture = null;
  if (currentGesture.longPressed || currentGesture.panning || currentGesture.moved) {
    persistAndRender();
    return;
  }
  const map = currentRenderedMap();
  const cell = worldToCell(map, screenToWorld(point));
  if (!cell) {
    if (!viewportElement?.contains(event.target)) clearMapSelection();
    persistAndRender();
    return;
  }
  handleCanvasTap(cell, point);
}

function handleCanvasTap(cell, point) {
  const map = currentRenderedMap();
  const nextTap = {
    mapId: map.id,
    cellId: cell.cellId,
    point,
    time: performance.now()
  };
  const doubleTap = sameTapTarget(lastTap, nextTap);
  handleCanvasCell(cell, point);
  if (doubleTap) {
    lastTap = null;
    handleCanvasDoubleActivation(cell, point);
    return;
  }
  lastTap = nextTap;
}

function handleCanvasDoubleActivation(cell, point = null) {
  if (state.scene === SCENES.ENCOUNTER || state.scene === SCENES.REPLAY) return;
  const map = getCurrentMap(state);
  const worldPoint = point ? screenToWorld(point) : cellCenter(map, cell.coordinates);
  const atlasInstance = hitTestAtlasInstanceAtPoint(map, worldPoint, state.role);
  if (atlasInstance) {
    state.selectedAtlasInstanceId = atlasInstance.instanceId;
    if (atlasInstance.childMapId && state.maps[atlasInstance.childMapId]) {
      openSelectedAtlasChild();
      return;
    }
    if (state.role === "gm") {
      state.editor.inspectorOpen = true;
      pushMessage(state, "Atlas instance selected. Attach a child map from the Atlas panel.");
    } else {
      pushMessage(state, "No accessible child layer here.", "warn");
    }
    persistAndRender();
    return;
  }
  const index = coordinateToIndex(map, cell.coordinates);
  const hitEntity = map.entities.find((entity) => entity.visible !== false && entity.x === index.x && entity.y === index.y);
  if (hitEntity) {
    state.selectedEntityId = hitEntity.id;
    openOverlay(state.tabletop, "entities");
    pushMessage(state, `Opened entity ${hitEntity.name || hitEntity.id}.`);
    persistAndRender();
    return;
  }
  const tile = tileAt(map, index.x, index.y, state.role);
  if (tile?.childMapId) {
    const result = openChildMapFromTile(state, tile, actor());
    if (!result.ok) pushMessage(state, result.message || "Child map entry rejected.", "warn");
    else fitCurrentMap({ persist: false });
    persistAndRender();
    return;
  }
  if (state.role === "gm") {
    openOverlay(state.tabletop, "map");
    pushMessage(state, "No child map attached. Use Map tools to create or attach one.");
  } else {
    pushMessage(state, "No accessible child layer here.", "warn");
  }
  persistAndRender();
}

function handleCanvasCell(cell, point = null) {
  const map = currentRenderedMap();
  const index = coordinateToIndex(map, cell.coordinates);
  if (state.scene === SCENES.ENCOUNTER) {
    const hit = state.activeEncounter.combatants.find((entity) => !entity.defeated && entity.x === index.x && entity.y === index.y);
    if (hit) state.selectedEntityId = hit.id;
    persistAndRender();
    return;
  }
  if (state.scene === SCENES.REPLAY) {
    const hit = state.replay.displayState?.combatants?.find((entity) => !entity.defeated && entity.x === index.x && entity.y === index.y);
    if (hit) state.replay.inspectedEntityId = hit.id;
    renderAll();
    return;
  }
  const role = state.role;
  const mapState = getCurrentMap(state);
  const worldPoint = point ? screenToWorld(point) : cellCenter(mapState, cell.coordinates);
  const atlasInstance = hitTestAtlasInstanceAtPoint(mapState, worldPoint, role);
  const perception = role === "player" && state.scene === SCENES.MAP_VIEW
    ? computePlayerPerception(state, mapState, state.actorPlayerId, { updateKnowledge: true })
    : null;
  const visibleCell = !perception || isVisibleNow(perception, mapState, cell.coordinates);
  const hitEntity = mapState.entities.find((entity) => {
    if (entity.visible === false || entity.x !== index.x || entity.y !== index.y) return false;
    if (role !== "player") return true;
    return visibleCell || (entity.controller === "player" && entity.assignedPlayerId === state.actorPlayerId);
  });
  if (state.scene === SCENES.MAP_EDIT && role === "gm") {
    if (state.editor.activeTool === "select" && atlasInstance) {
      state.selectedAtlasInstanceId = atlasInstance.instanceId;
      state.selectedTileId = null;
      state.selection = {
        mapId: mapState.id,
        cellId: cell.cellId,
        gridType: cell.gridType,
        coordinates: deepClone(cell.coordinates)
      };
      persistAndRender();
      return;
    }
    handleEditorToolCell(mapState, cell);
  } else {
    if (atlasInstance && role === "gm") state.selectedAtlasInstanceId = atlasInstance.instanceId;
    if (hitEntity) state.selectedEntityId = hitEntity.id;
    selectCell(state, mapState, cell);
    if (role === "player" && !visibleCell) state.selectedTileId = null;
  }
  persistAndRender();
}

function handleEditorToolCell(map, cell) {
  const tool = state.editor.activeTool;
  if (tool === "paint") {
    editorCommand("paint terrain", () => paintTerrainAtCell(state, map, cell, state.selectedPaletteId));
    return;
  }
  if (tool === "erase") {
    selectCell(state, map, cell);
    editorCommand("erase tile", () => removeSelectedTile(state));
    return;
  }
  if (tool === "fill") {
    editorCommand("fill terrain", () => fillTerrain(state, map, state.selectedPaletteId));
    return;
  }
  if (tool === "child") {
    selectCell(state, map, cell);
    editorCommand("place child map tile", () => ensureTileThenChildMap(map, cell));
    return;
  }
  if (tool === "trigger") {
    selectCell(state, map, cell);
    editorCommand("place trigger", () => ensureTileThenAttach("trigger"));
    return;
  }
  if (tool === "encounter") {
    selectCell(state, map, cell);
    editorCommand("place encounter", () => ensureTileThenAttach("encounter"));
    return;
  }
  if (tool === "entity-start") {
    editorCommand("place entity start", () => placeTile(state, "player-start", coordinateToIndex(map, cell.coordinates).x, coordinateToIndex(map, cell.coordinates).y));
    return;
  }
  selectCell(state, map, cell);
}

function ensureTileThenChildMap(map, cell) {
  if (!selectedTile(state)) {
    const index = coordinateToIndex(map, cell.coordinates);
    const placed = placeTile(state, state.selectedPaletteId || "entrance", index.x, index.y);
    if (!placed.ok) return placed;
  }
  return import("./maps.js").then((module) => module.createChildMapFromSelectedTile(state));
}

function ensureTileThenAttach(kind) {
  if (!selectedTile(state) && state.selection) {
    const map = getCurrentMap(state);
    const index = coordinateToIndex(map, state.selection.coordinates);
    const placed = placeTile(state, kind === "trigger" ? "trigger-marker" : state.selectedPaletteId, index.x, index.y);
    if (!placed.ok) return placed;
  }
  if (kind === "trigger") return attachTriggerToSelectedTile(state, elements.triggerTypeSelect.value || "gm_manual");
  if (kind === "encounter") return attachEncounterToSelectedTile(state, elements.encounterSelect.value || Object.keys(state.encounters)[0]);
  return { ok: false, message: "Unknown attachment kind." };
}

function handleCanvasContextMenu(point, event) {
  event.preventDefault();
  const map = currentRenderedMap();
  const cell = worldToCell(map, screenToWorld(point));
  if (state.role === "gm" && state.scene === SCENES.MAP_EDIT) openContextMenuAt(point, cell);
  else openTabletopMapMenu(point, cell);
}

function handleCanvasWheel(point, event) {
  if (state.scene === SCENES.ENCOUNTER || state.scene === SCENES.REPLAY) return;
  zoomViewport(event.deltaY < 0 ? 1.12 : 1 / 1.12, point);
}

function handleShortcut(event) {
  if (!state || state.role !== "gm") return false;
  const key = event.key.toLowerCase();
  if (event.ctrlKey && key === "z" && !event.shiftKey) {
    commandResult(undoEditorEdit(state));
    return true;
  }
  if ((event.ctrlKey && key === "y") || (event.ctrlKey && event.shiftKey && key === "z")) {
    commandResult(redoEditorEdit(state));
    return true;
  }
  if (event.key === "Delete") {
    editorCommand("delete selected tile", () => removeSelectedTile(state));
    return true;
  }
  const toolMap = { v: "select", b: "paint", e: "erase", f: "fill", h: "pan" };
  if (toolMap[key]) {
    setActiveTool(state, toolMap[key]);
    renderAll();
    return true;
  }
  return false;
}

function renderAll() {
  if (!state) return;
  document.body.dataset.role = state.role;
  document.body.dataset.scene = state.scene;
  document.body.classList.toggle("inspector-open", state.editor.inspectorOpen);
  document.body.dataset.sheetState = state.editor.inspectorSheetState || "collapsed";
  elements.gmRoleButton.classList.toggle("is-active", state.role === "gm");
  elements.playerRoleButton.classList.toggle("is-active", state.role === "player");
  elements.playerIdentity.value = state.actorPlayerId;
  document.querySelectorAll(".gm-only").forEach((node) => node.classList.toggle("is-hidden", state.role !== "gm"));
  document.querySelectorAll(".player-only").forEach((node) => node.classList.toggle("is-hidden", state.role !== "player"));
  setText("sceneStatus", state.scene);
  setText("errorStatus", state.messages.at(-1)?.message || "No errors");
  renderBreadcrumb();
  renderToolbars();
  renderAssetSelectors();
  renderAtlasBrowser();
  renderPalette();
  renderEditorControls();
  renderEncounterControls();
  renderReplayControls();
  renderLog();
  renderStatus();
  renderTabletop();
  renderContextMenu();
  renderMoreMenu();
}

function renderBreadcrumb() {
  const parts = getMapPath(state);
  elements.breadcrumb.innerHTML = "";
  parts.forEach((part, index) => {
    if (index > 0) {
      const sep = document.createElement("span");
      sep.textContent = ">";
      elements.breadcrumb.appendChild(sep);
    }
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = part.name;
    button.dataset.mapId = part.id;
    button.addEventListener("click", () => {
      state.currentMapId = part.id;
      state.lastValidMapId = part.id;
      state.selectedTileId = null;
      state.scene = SCENES.MAP_VIEW;
      persistAndRender();
    });
    elements.breadcrumb.appendChild(button);
  });
}

function renderPalette() {
  elements.tilePalette.innerHTML = "";
  state.tileManifest.definitions.forEach((definition) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `palette-tile${state.selectedPaletteId === definition.id ? " is-active" : ""}`;
    button.dataset.tileDefinition = definition.id;
    button.title = definition.name;
    const swatch = document.createElement("span");
    swatch.className = "swatch";
    swatch.style.background = definition.sprite.base;
    const label = document.createElement("span");
    label.textContent = definition.name;
    button.append(swatch, label);
    button.addEventListener("click", () => {
      state.selectedPaletteId = definition.id;
      if (state.role === "gm") setActiveTool(state, "paint");
      renderPalette();
      renderToolbars();
    });
    elements.tilePalette.appendChild(button);
  });
}

function renderToolbars() {
  document.querySelectorAll("[data-editor-tool]").forEach((button) => {
    button.classList.toggle("is-active", state.editor.activeTool === button.dataset.editorTool);
    button.disabled = state.role !== "gm";
  });
  document.querySelectorAll("[data-editor-command='undo']").forEach((button) => { button.disabled = !state.editor.undoStack.length; });
  document.querySelectorAll("[data-editor-command='redo']").forEach((button) => { button.disabled = !state.editor.redoStack.length; });
  if (elements.toggleInspectorButton) {
    elements.toggleInspectorButton.classList.toggle("is-active", state.editor.inspectorOpen);
    elements.toggleInspectorButton.setAttribute("aria-expanded", String(state.editor.inspectorOpen));
  }
  const viewport = currentViewport();
  if (elements.gridVisibleToggle) elements.gridVisibleToggle.checked = viewport.gridVisible !== false;
  if (elements.zoomSelect) {
    const exactOption = [...elements.zoomSelect.options].find((option) => Math.abs(Number(option.value) - viewport.zoom) < 0.005);
    elements.zoomSelect.value = ["fit-map", "fit-width", "fit-height", "actual-size", "fit-selection"].includes(viewport.fitMode)
      ? viewport.fitMode
      : exactOption?.value || "1";
  }
}

function renderAssetSelectors() {
  const assets = tileAssets(state.tileAssetRegistry);
  const options = [`<option value="">Color tile</option>`].concat(assets.map((asset) => `<option value="${escapeHtml(asset.assetId)}">${escapeHtml(asset.name)}</option>`)).join("");
  if (elements.assetSelect && elements.assetSelect.dataset.options !== options) {
    elements.assetSelect.innerHTML = options;
    elements.assetSelect.dataset.options = options;
  }
  if (elements.brushImageSelect && elements.brushImageSelect.dataset.options !== options) {
    elements.brushImageSelect.innerHTML = options;
    elements.brushImageSelect.dataset.options = options;
  }
  if (elements.assetSelect) elements.assetSelect.value = state.selectedTileImageAssetId || selectedTile(state)?.image?.imageAssetId || "";
  if (elements.brushImageSelect) elements.brushImageSelect.value = state.selectedTileImageAssetId || "";
}

function renderAtlasBrowser() {
  if (!elements.atlasBrowser) return;
  const collections = atlasCollections(state.atlasRegistry);
  if (!state.selectedAtlasCollection && collections[0]) state.selectedAtlasCollection = collections[0].id;
  const collectionOptions = collections
    .map((collection) => `<option value="${escapeHtml(collection.id)}">${escapeHtml(collection.name)} (${collection.count})</option>`)
    .join("");
  if (elements.atlasCollectionSelect && elements.atlasCollectionSelect.dataset.options !== collectionOptions) {
    elements.atlasCollectionSelect.innerHTML = collectionOptions;
    elements.atlasCollectionSelect.dataset.options = collectionOptions;
  }
  if (elements.atlasCollectionSelect) elements.atlasCollectionSelect.value = state.selectedAtlasCollection || "";

  const query = String(elements.atlasSearchInput?.value || "").trim().toLowerCase();
  const assets = atlasRenderableAssets(state.atlasRegistry).filter((asset) => {
    if (state.selectedAtlasCollection && asset.collection !== state.selectedAtlasCollection) return false;
    if (!query) return true;
    return [asset.name, asset.category, asset.collection, ...(asset.tags || [])].join(" ").toLowerCase().includes(query);
  });
  elements.atlasBrowser.innerHTML = "";
  assets.forEach((asset) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `atlas-asset-card${state.selectedAtlasAssetId === asset.assetId ? " is-active" : ""}`;
    button.dataset.atlasAssetId = asset.assetId;
    button.title = `${asset.name} | ${asset.collection} | ${asset.layer}`;
    const img = document.createElement("img");
    img.src = asset.thumbnailPath;
    img.alt = "";
    img.loading = "lazy";
    const label = document.createElement("span");
    label.textContent = asset.name;
    const meta = document.createElement("small");
    meta.textContent = `${asset.category} | ${asset.layer}`;
    button.append(img, label, meta);
    button.addEventListener("click", () => {
      state.selectedAtlasAssetId = asset.assetId;
      renderAtlasBrowser();
    });
    button.addEventListener("dblclick", () => editorCommand("place atlas asset", placeSelectedAtlasAsset));
    elements.atlasBrowser.appendChild(button);
  });
  if (!assets.length) {
    const empty = document.createElement("p");
    empty.className = "microcopy";
    empty.textContent = "No Atlas assets match the current filter.";
    elements.atlasBrowser.appendChild(empty);
  }

  const map = getCurrentMap(state);
  const selectedInstance = findAtlasInstance(map, state.selectedAtlasInstanceId);
  if (elements.selectedAtlasInstanceSummary) {
    const selectedAsset = selectedInstance ? state.atlasAssets[selectedInstance.assetId] : null;
    elements.selectedAtlasInstanceSummary.textContent = selectedInstance
      ? `${selectedAsset?.name || selectedInstance.assetId} | x:${Math.round(selectedInstance.x)} y:${Math.round(selectedInstance.y)} | r:${selectedInstance.rotationDeg} | ${selectedInstance.childMapId || "no child"}`
      : "No Atlas instance selected";
  }
  const hasAsset = Boolean(state.selectedAtlasAssetId && state.atlasAssets[state.selectedAtlasAssetId]);
  const hasInstance = Boolean(selectedInstance);
  [
    elements.placeAtlasAssetButton,
    elements.moveAtlasLeftButton,
    elements.moveAtlasRightButton,
    elements.moveAtlasUpButton,
    elements.moveAtlasDownButton,
    elements.rotateAtlasLeftButton,
    elements.rotateAtlasRightButton,
    elements.removeAtlasInstanceButton,
    elements.attachAtlasChildButton,
    elements.openAtlasChildButton
  ].forEach((button) => {
    if (!button) return;
    button.disabled = button === elements.placeAtlasAssetButton ? !hasAsset : !hasInstance;
  });
  if (elements.atlasChildMapSelect) {
    const childOptions = [`<option value="">No child map</option>`].concat(
      Object.values(state.maps)
        .filter((candidate) => candidate.id !== map.id)
        .map((candidate) => `<option value="${escapeHtml(candidate.id)}">${escapeHtml(candidate.name)}</option>`)
    ).join("");
    if (elements.atlasChildMapSelect.dataset.options !== childOptions) {
      elements.atlasChildMapSelect.innerHTML = childOptions;
      elements.atlasChildMapSelect.dataset.options = childOptions;
    }
    elements.atlasChildMapSelect.value = selectedInstance?.childMapId || "";
  }
}

function renderEditorControls() {
  const map = getCurrentMap(state);
  const tile = selectedTile(state);
  setText("mapMeta", `${map.name} ${map.gridType || "square"} ${map.width}x${map.height}`);
  setText("inspectorHeading", tile ? tile.metadata?.label || tile.id : state.selection?.mapId === map.id ? "Cell Selection" : "Map Inspector");
  setText("tileInspectorSummary", tile ? tileSummary(state) : state.selection?.mapId === map.id ? `Selected ${state.selection.cellId}` : "Select a tile or cell to edit properties.");
  elements.hiddenToggle.checked = tile?.hiddenFromPlayers === true;
  elements.blockedToggle.checked = tile?.blocked === true;
  elements.hiddenToggle.disabled = !tile;
  elements.blockedToggle.disabled = !tile;
  if (elements.placePcButton) {
    const legalStarts = legalStartCellsForPlayer(state, map, state.actorPlayerId);
    elements.placePcButton.disabled = state.role !== "player" || !state.selection || !legalStarts.some((cell) => cellKey(map, cell) === cellKey(map, state.selection.coordinates));
    elements.placePcButton.title = legalStarts.length ? "Place selected owned PC on this start cell" : "No authorized start cells on this map";
  }
  renderCollisionInspector(tile);
  elements.childMapSelect.innerHTML = `<option value="">None</option>${Object.values(state.maps).map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)}</option>`).join("")}`;
  elements.childMapSelect.value = tile?.childMapId || "";
  elements.childMapSelect.disabled = !tile;
  elements.actionTypeSelect.innerHTML = ["enter_child_map", "return_to_parent", "open", "close", "reveal", "hide", "inspect", "search", "unlock", "move_entity", "change_tile_state", "start_encounter"]
    .map((type) => `<option value="${type}">${type}</option>`)
    .join("");
  elements.triggerTypeSelect.innerHTML = ["player_enters_tile", "player_leaves_tile", "player_interacts", "gm_manual", "map_entered", "map_exited", "elapsed_time", "round_started", "entity_defeated", "tile_state_changed"]
    .map((type) => `<option value="${type}">${type}</option>`)
    .join("");
  elements.encounterSelect.innerHTML = Object.values(state.encounters).map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)}</option>`).join("");
  if (elements.inspectorPanel) {
    elements.inspectorPanel.classList.toggle("is-collapsed", !state.editor.inspectorOpen);
    document.documentElement.style.setProperty("--inspector-w", `${clamp(state.editor.inspectorWidth || 336, 288, 440)}px`);
  }
}

function renderCollisionInspector(tile) {
  if (!elements.collisionPresetSelect) return;
  const options = Object.values(state.collisionPresets || {})
    .map((preset) => `<option value="${escapeHtml(preset.id)}">${escapeHtml(preset.name || preset.id)}</option>`)
    .join("");
  if (elements.collisionPresetSelect.dataset.options !== options) {
    elements.collisionPresetSelect.innerHTML = options;
    elements.collisionPresetSelect.dataset.options = options;
  }
  const collision = tile?.collision || {};
  const shape = tile?.collisionShape || {};
  elements.collisionPresetSelect.value = tile?.collisionPresetId || "decorative";
  elements.collisionMovementToggle.checked = Boolean(collision.blocksMovement ?? tile?.blocked);
  elements.collisionVisionToggle.checked = Boolean(collision.blocksVision);
  elements.collisionSoundToggle.checked = Boolean(collision.blocksSound);
  elements.collisionProjectileToggle.checked = Boolean(collision.blocksProjectile);
  elements.collisionReachToggle.checked = Boolean(collision.blocksReach);
  elements.collisionShapeSelect.value = shape.type || "tile_footprint";
  elements.collisionHeightInput.value = Number(collision.height ?? shape.height ?? 1);
  elements.soundTransmissionInput.value = Number(collision.soundTransmission ?? 1);
  elements.soundAbsorptionInput.value = Number(collision.soundAbsorption ?? 0);
  [
    "collisionPresetSelect", "collisionMovementToggle", "collisionVisionToggle", "collisionSoundToggle",
    "collisionProjectileToggle", "collisionReachToggle", "collisionShapeSelect", "collisionHeightInput",
    "soundTransmissionInput", "soundAbsorptionInput"
  ].forEach((id) => {
    if (elements[id]) elements[id].disabled = !tile;
  });
}

function renderEncounterControls() {
  const encounter = state.activeEncounter;
  if (!encounter) {
    setText("encounterMeta", "Inactive");
    ["timeAvailable", "timeSpent", "selectedCost", "timeRemaining"].forEach((id) => setText(id, "0"));
    elements.monsterSelect.innerHTML = "";
    return;
  }
  const active = activeCombatant(state);
  setText("encounterMeta", `${encounter.name} R${encounter.round} ${active?.name || "none"}`);
  setText("timeAvailable", String(encounter.timeAllowance));
  setText("timeSpent", String(active?.timeSpent || 0));
  setText("selectedCost", String(state.selectedActionCost || 0));
  setText("timeRemaining", String(active ? remainingTime(active, encounter) : 0));
  setText("timeStatus", active ? `${active.name}: ${active.timeSpent} / ${encounter.timeAllowance}` : "Time: 0 / 0");
  elements.commanderOrder.innerHTML = COMMANDER_ORDERS.map((order) => `<option value="${order}">${order}</option>`).join("");
  const monsters = encounter.combatants.filter((entity) => entity.faction === "monsters" && !entity.defeated);
  elements.monsterSelect.innerHTML = monsters.map((monster) => `<option value="${escapeHtml(monster.id)}">${escapeHtml(monster.name)}</option>`).join("");
}

function renderReplayControls() {
  elements.replaySelect.innerHTML = state.replays.map((replay) => `<option value="${escapeHtml(replay.replayId)}">${escapeHtml(replay.replayId)}</option>`).join("");
  if (state.replay.selectedReplayId) elements.replaySelect.value = state.replay.selectedReplayId;
  const replay = currentReplay();
  const count = replay?.orderedEvents.length || 0;
  setText("replayMeta", replay ? `${state.replay.cursor}/${count} ${state.replay.speed}x` : "None");
  elements.replaySpeedButton.textContent = state.replay.speed === 1 ? "Double Speed" : "Normal Speed";
  if (!replay) {
    elements.replayDetail.textContent = "No replay selected.";
    return;
  }
  const currentEvent = replay.orderedEvents[Math.max(0, state.replay.cursor - 1)] || replay.orderedEvents[0];
  const commander = [...replay.orderedEvents].reverse().find((event) => event.type === "commander_order_issued");
  const inspected = state.replay.displayState?.combatants?.find((entity) => entity.id === state.replay.inspectedEntityId)
    || state.replay.displayState?.combatants?.find((entity) => entity.id === state.replay.displayState?.activeEntityId)
    || state.replay.displayState?.combatants?.[0];
  elements.replayDetail.innerHTML = [
    `<strong>Event</strong> ${escapeHtml(currentEvent?.type || "start")} R${escapeHtml(currentEvent?.round || 1)}`,
    `<strong>Commander</strong> ${escapeHtml(commander?.payload?.orderType || "none")}`,
    `<strong>Entity</strong> ${escapeHtml(inspected ? `${inspected.name || inspected.id} HP ${inspected.hp}/${inspected.maxHp} T ${inspected.timeSpent}` : "none")}`,
    `<strong>Hash</strong> ${escapeHtml(replay.finalStateHash)}`
  ].join("<br>");
}

function renderLog() {
  const visibleEvents = state.role === "player"
    ? state.eventLog.filter((event) => !["commander_action_generated", "direct_gm_override"].includes(event.type) && !event.payload?.trigger?.hidden)
    : state.eventLog;
  const rows = visibleEvents.slice(-34).reverse();
  elements.eventLog.innerHTML = rows.map((event) => `<li>${escapeHtml(event.sequence)} ${escapeHtml(event.type)} ${event.rejected ? "rejected" : ""}</li>`).join("");
  setText("logCount", String(visibleEvents.length));
}

function renderStatus() {
  const map = getCurrentMap(state);
  const tile = selectedTile(state);
  const selection = state.scene === SCENES.ENCOUNTER
    ? activeCombatant(state)
    : tile;
  const viewport = currentViewport();
  const scale = map.gridType === "hex"
    ? `${map.gridSettings.hex?.radius || 5} ${map.gridSettings.hex?.distanceUnit || "ft"}/radius`
    : `${map.gridSettings.square?.cellWidth || 5} ${map.gridSettings.square?.distanceUnit || "ft"}/cell`;
  const dimensions = map.gridType === "hex"
    ? `Hex ${map.width}x${map.height}`
    : `Square ${map.width}x${map.height}`;
  const rotation = normalizeRotation(viewport.rotationDeg);
  const zoomLabel = `${Math.round(viewport.zoom * 100)}%`;
  let selectionLabel = state.scene === SCENES.ENCOUNTER ? `Active: ${selection?.name || "none"}` : tileSummary(state);
  if (state.role === "gm" && tile) selectionLabel = `${selectionLabel} | collision: ${collisionSummary(tile)}`;
  if (state.role === "player" && state.scene === SCENES.MAP_VIEW) {
    const perception = computePlayerPerception(state, map, state.actorPlayerId, { updateKnowledge: true });
    selectionLabel = `${selectionLabel} | seen ${perception.visibleCellKeys.length} heard ${perception.perceivedSounds.length}`;
  }
  setText("selectionStatus", selectionLabel);
  if (!state.activeEncounter) setText("timeStatus", `Map: ${map.name}`);
  setText("sceneStatus", state.scene);
  setText("currentLocationLabel", getMapPath(state).map((item) => item.name).join(" > "));
  setText("workspaceMapHud", `${map.name} | ${dimensions} | ${scale}`);
  setText("statusMap", map.name);
  setText("statusGrid", dimensions);
  setText("statusScale", scale);
  setText("statusZoom", zoomLabel);
  setText("statusRotation", rotation === 0 ? "North-up" : `${rotation} deg`);
  setText("floatingZoomLabel", zoomLabel);
  if (elements.compassNeedle) elements.compassNeedle.style.transform = `rotate(${-rotation}deg)`;
  if (elements.compassAngle) elements.compassAngle.textContent = `${rotation} deg`;
  if (elements.compassButton) elements.compassButton.hidden = viewport.compassVisible === false;
}

function renderTabletop() {
  if (!state?.tabletop) return;
  const projection = tabletopProjection(state.tabletop, state.role, state.actorPlayerId);
  const active = activeScene(state.tabletop);
  renderTabletopEffects(projection);
  renderTabletopInitiative(projection);
  renderTabletopClock();
  renderTabletopDecks(projection);
  renderTabletopDice(projection);
  renderTabletopRightTray(projection);
  renderTabletopOverlay(projection, active);
  document.body.classList.toggle("tabletop-overlay-open", state.tabletop.overlay.open);
}

function renderTabletopEffects(projection) {
  if (!elements.tabletopEffectsTray) return;
  elements.tabletopEffectsTray.innerHTML = projection.chips.map((chip) => (
    `<span class="tabletop-chip ${escapeHtml(chip.category)}" title="${escapeHtml(chip.duration || "scene")}">${escapeHtml(chip.label)}</span>`
  )).join("");
}

function renderTabletopInitiative(projection) {
  if (!elements.tabletopInitiativeStrip) return;
  const activeEntryId = state.tabletop.initiative.activeEntryId;
  elements.tabletopInitiativeStrip.innerHTML = projection.initiativeEntries.map((entry) => `
    <button class="initiative-entry ${entry.entryId === activeEntryId ? "is-active" : ""}" data-card-id="${escapeHtml(entry.cardId || "")}" data-tabletop-action="open-card" type="button">
      <strong>${escapeHtml(entry.name)}</strong>
      <span>${escapeHtml(entry.role)}</span>
    </button>
  `).join("");
}

function renderTabletopClock() {
  const progress = clockProgress(state.tabletop);
  if (elements.tabletopClockFace) elements.tabletopClockFace.textContent = progress.paused ? "II" : String(Math.round(progress.remaining));
  if (elements.tabletopClock) {
    elements.tabletopClock.style.setProperty("--timer-used", String(progress.usedRatio));
    elements.tabletopClock.classList.toggle("is-paused", progress.paused);
    elements.tabletopClock.classList.add("tabletop-fade-card");
  }
  if (elements.tabletopClockPauseButton) elements.tabletopClockPauseButton.textContent = progress.paused ? "Resume" : "Pause";
}

function renderTabletopDecks(projection) {
  const playerDeck = projection.decks.find((deck) => deck.deckType === "player");
  const monsterDeck = projection.decks.find((deck) => deck.deckType === "monster");
  if (elements.tabletopPlayerDeck) elements.tabletopPlayerDeck.innerHTML = renderDeck(playerDeck, "Player Deck");
  if (elements.tabletopMonsterDeck) elements.tabletopMonsterDeck.innerHTML = renderDeck(monsterDeck, "Monster Deck");
}

function renderDeck(deck, fallbackTitle) {
  if (!deck) return `<div class="deck-title"><span>${escapeHtml(fallbackTitle)}</span><span>Hidden</span></div>`;
  const cards = (deck.cards || []).slice(0, 3).map((cardId) => state.tabletop.cards[cardId]).filter(Boolean);
  return `
    <div class="deck-title">
      <span>${escapeHtml(deck.name || deck.groupName || fallbackTitle)}</span>
      <button type="button" data-deck-id="${escapeHtml(deck.deckId)}" data-tabletop-action="draw-card">Draw</button>
    </div>
    ${cards.map((card, index) => renderSmallCard(card, index === 0 && deck.deckType === "monster" ? "open-commander" : "select-card")).join("")}
  `;
}

function renderSmallCard(card, action = "select-card") {
  const selected = state.tabletop.layout.selectedCardId === card.cardId;
  const remaining = cardStackRemainingSafe(card.cardId);
  const stack = card.stackCount ? `<span>Stack ${remaining}/${card.stackCount}</span>` : "";
  return `
    <button class="tabletop-deck-card ${selected ? "is-selected" : ""}" type="button" data-card-id="${escapeHtml(card.cardId)}" data-tabletop-action="${escapeHtml(action)}">
      <strong>${escapeHtml(card.name)}</strong>
      <span>${escapeHtml(card.cardType)}</span>
      ${stack}
    </button>
  `;
}

function cardStackRemainingSafe(cardId) {
  const card = state.tabletop.cards[cardId];
  if (!card?.stackCount) return 0;
  const used = Number(state.tabletop.sceneState.cardUseCounts[cardId] || 0);
  return Math.max(0, Number(card.stackCount) - used);
}

function renderTabletopDice(projection) {
  if (!elements.tabletopDiceRow) return;
  elements.tabletopDiceRow.innerHTML = projection.dice.map((die) => `
    <button class="tabletop-die ${state.tabletop.layout.selectedDieId === die.dieId ? "is-selected" : ""}" type="button" data-die-id="${escapeHtml(die.dieId)}" data-tabletop-action="select-die" title="Double-click or double-tap to roll ${escapeHtml(die.label)}">
      ${escapeHtml(die.label)}
    </button>
  `).join("");
}

function renderTabletopRightTray(projection) {
  if (!elements.tabletopRightTray) return;
  const selected = state.tabletop.cards[state.tabletop.layout.selectedCardId];
  const hand = selected?.cardId === "card-orc-commander" ? commanderHand(state.tabletop, selected.cardId) : [];
  const latestRoll = state.tabletop.sceneState.diceResults.at(-1);
  elements.tabletopRightTray.innerHTML = `
    ${selected ? `<div class="tabletop-card-detail tabletop-object"><strong>${escapeHtml(selected.name)}</strong><br>${escapeHtml(selected.cardType)}${selected.cardId === "card-weapon-sword-001" ? `<br><button type="button" data-card-id="${escapeHtml(selected.cardId)}" data-tabletop-action="dice-bag">Dice Bag</button>` : ""}</div>` : ""}
    ${hand.map((card) => renderSmallCard(card, "select-card")).join("")}
    ${latestRoll ? `<div class="tabletop-result tabletop-object"><strong>${escapeHtml(latestRoll.label)}</strong><br>${escapeHtml(latestRoll.face)}</div>` : ""}
  `;
  if (elements.tabletopLoreScroll) elements.tabletopLoreScroll.classList.toggle("is-open", state.tabletop.layout.ancientScrollOpen);
}

function renderTabletopOverlay(projection, active) {
  const overlay = elements.tabletopOverlay;
  const backdrop = elements.tabletopOverlayBackdrop;
  if (!overlay || !backdrop) return;
  overlay.hidden = !state.tabletop.overlay.open;
  backdrop.hidden = !state.tabletop.overlay.open;
  if (!state.tabletop.overlay.open) return;
  const category = state.tabletop.overlay.category || "scene";
  setText("tabletopOverlayTitle", `${category[0].toUpperCase()}${category.slice(1)}`);
  elements.tabletopOverlayTabs?.querySelectorAll("[data-tabletop-category]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tabletopCategory === category);
  });
  if (!elements.tabletopOverlayContent) return;
  elements.tabletopOverlayContent.innerHTML = tabletopOverlayHtml(category, projection, active);
}

function tabletopOverlayHtml(category, projection, active) {
  if (category === "map") {
    const map = getCurrentMap(state);
    return `<div class="tabletop-menu-grid">
      <section class="tabletop-menu-panel"><h3>${escapeHtml(map.name)}</h3><p>${escapeHtml(map.gridType)} ${map.width}x${map.height}</p><button type="button" data-tabletop-action="open-selected-child">Open selected child</button></section>
      <section class="tabletop-menu-panel"><h3>Selection</h3><p>${escapeHtml(state.selection?.cellId || "No cell selected")}</p></section>
    </div>`;
  }
  if (category === "decks") {
    return `<div class="tabletop-menu-grid">${projection.decks.map((deck) => `<section class="tabletop-menu-panel"><h3>${escapeHtml(deck.name || deck.groupName)}</h3>${(deck.cards || []).map((id) => renderSmallCard(state.tabletop.cards[id], "open-card")).join("")}</section>`).join("")}</div>`;
  }
  if (category === "cards") {
    const card = state.tabletop.cards[state.tabletop.overlay.detailCardId || state.tabletop.layout.selectedCardId] || projection.cards[0];
    if (!card) return `<p>No authorized card selected.</p>`;
    const modifiers = visibleModifierRows(state.tabletop, "attack").map((chip) => `<span class="tabletop-chip ${escapeHtml(chip.category)}">${escapeHtml(chip.label)}</span>`).join("");
    return `<section class="tabletop-menu-panel">
      <h3>${escapeHtml(card.name)}</h3>
      <p>${escapeHtml(card.text || "")}</p>
      <p>Visibility: ${escapeHtml(card.visibility)}</p>
      ${card.cardId === "card-weapon-sword-001" ? `<button type="button" data-card-id="${escapeHtml(card.cardId)}" data-tabletop-action="dice-bag">Roll Dice Bag</button>` : ""}
      <div>${modifiers}</div>
    </section>`;
  }
  if (category === "dice") {
    const latest = state.tabletop.sceneState.diceResults.at(-1);
    return `<div class="tabletop-menu-grid">
      <section class="tabletop-menu-panel"><h3>Dice Tray</h3><div class="tabletop-dice-row">${projection.dice.map((die) => `<button class="tabletop-die" type="button" data-die-id="${escapeHtml(die.dieId)}" data-tabletop-action="roll-die">${escapeHtml(die.label)}</button>`).join("")}</div></section>
      <section class="tabletop-menu-panel"><h3>Latest Result</h3><p>${latest ? `${escapeHtml(latest.label)}: ${escapeHtml(latest.face)}` : "No roll yet."}</p></section>
    </div>`;
  }
  if (category === "initiative") {
    return `<section class="tabletop-menu-panel"><h3>Initiative</h3>${projection.initiativeEntries.map((entry) => `<p>${entry.entryId === state.tabletop.initiative.activeEntryId ? "> " : ""}${escapeHtml(entry.name)} - ${escapeHtml(entry.role)}</p>`).join("")}<button type="button" data-tabletop-action="advance-initiative">Advance</button><button type="button" data-tabletop-action="pause-clock">${state.tabletop.initiative.paused ? "Resume" : "Pause"}</button></section>`;
  }
  if (category === "effects") {
    return `<section class="tabletop-menu-panel"><h3>Visible Modifier Chips</h3>${projection.chips.map((chip) => `<span class="tabletop-chip ${escapeHtml(chip.category)}">${escapeHtml(chip.label)}</span>`).join(" ")}</section>`;
  }
  if (category === "lore") {
    const loreCards = projection.cards.filter((card) => card.cardType === "lore");
    return `<section class="tabletop-menu-panel"><h3>Ancient Scroll</h3><button type="button" data-tabletop-action="toggle-lore">${state.tabletop.layout.ancientScrollOpen ? "Roll Scroll" : "Unroll Scroll"}</button>${loreCards.map((card) => `<article class="tabletop-card"><strong>${escapeHtml(card.name)}</strong><p>${escapeHtml(card.text)}</p><button type="button" data-card-id="${escapeHtml(card.cardId)}" data-tabletop-action="share-lore">Share to Scene</button></article>`).join("") || "<p>No lore cards authorized for this view.</p>"}</section>`;
  }
  if (category === "replay") {
    return `<section class="tabletop-menu-panel"><h3>Tabletop Replay Boundary</h3><p>Authoritative tabletop events: ${state.tabletop.replayBoundary.authoritativeEvents.length}</p><p>Encounter replay events remain separate.</p></section>`;
  }
  if (category === "settings") {
    return `<section class="tabletop-menu-panel"><h3>Accessibility</h3><button type="button" data-tabletop-action="toggle-reduced-motion">${state.tabletop.layout.reducedMotion ? "Disable" : "Enable"} reduced motion</button><p>Viewport, tray, and menu state are personal UI state and are excluded from gameplay replay.</p></section>`;
  }
  return `<section class="tabletop-menu-panel"><h3>${escapeHtml(active?.name || "Scene")}</h3><p>${escapeHtml(active?.narration?.[0]?.text || "Tabletop scene ready.")}</p></section>`;
}

function loop(timestamp) {
  const elapsed = lastFrame ? timestamp - lastFrame : 0;
  lastFrame = timestamp;
  if (state?.scene === SCENES.REPLAY && state.replay.playing) {
    state.replay.accumulator += elapsed * state.replay.speed;
    if (state.replay.accumulator >= 600) {
      state.replay.accumulator = 0;
      stepReplay(1, false);
    }
  }
  if (state?.tabletop && !state.tabletop.initiative.paused && state.tabletop.initiative.remainingSeconds > 0 && !state.tabletop.layout.reducedMotion) {
    state.tabletop.initiative.remainingSeconds = Math.max(0, state.tabletop.initiative.remainingSeconds - elapsed / 1000);
    renderTabletopClock();
  }
  draw();
  window.requestAnimationFrame(loop);
}

function currentRenderedMap() {
  if (state.scene === SCENES.REPLAY) {
    const replay = currentReplay();
    return replay ? state.maps[state.encounters[replay.encounterId].battleMapId] : getCurrentMap(state);
  }
  return getCurrentMap(state);
}

function draw() {
  if (!state || !context) return;
  const map = currentRenderedMap();
  resizeCanvasToViewport();
  context.imageSmoothingEnabled = false;
  context.setTransform(1, 0, 0, 1, 0, 0);
  context.clearRect(0, 0, canvas.width, canvas.height);
  const dpr = window.devicePixelRatio || 1;
  context.setTransform(dpr, 0, 0, dpr, 0, 0);
  context.fillStyle = "#11161c";
  context.fillRect(0, 0, canvas.clientWidth, canvas.clientHeight);
  const viewport = currentViewport();
  if (!viewport.initialized) fitMapMode(viewport.fitMode || "fit-map", { persist: false });
  const center = mapViewCenter();
  context.save();
  context.translate(viewport.offsetX, viewport.offsetY);
  context.scale(viewport.zoom, viewport.zoom);
  context.translate(center.x, center.y);
  context.rotate((normalizeRotation(viewport.rotationDeg) * Math.PI) / 180);
  context.translate(-center.x, -center.y);
  const playerPerception = currentPlayerPerception(map);
  drawMapBase(map, playerPerception);
  if (state.scene === SCENES.ENCOUNTER) {
    drawEncounter(state.activeEncounter);
  } else if (state.scene === SCENES.REPLAY && state.replay.displayState) {
    drawEncounter(state.replay.displayState);
  } else {
    drawExploration(map, playerPerception);
  }
  if (viewport.gridVisible) drawGrid(map, playerPerception);
  drawPerceptionPresentation(map, playerPerception);
  context.restore();
}

function currentPlayerPerception(map) {
  if (state.role !== "player" || state.scene !== SCENES.MAP_VIEW) return null;
  return computePlayerPerception(state, map, state.actorPlayerId, { updateKnowledge: true });
}

function resizeCanvasToViewport() {
  const dpr = window.devicePixelRatio || 1;
  const width = Math.max(320, Math.floor((viewportElement?.clientWidth || canvas.clientWidth || 640)));
  const height = Math.max(260, Math.floor((viewportElement?.clientHeight || canvas.clientHeight || 420)));
  const pixelWidth = Math.floor(width * dpr);
  const pixelHeight = Math.floor(height * dpr);
  if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
    canvas.width = pixelWidth;
    canvas.height = pixelHeight;
    canvas.style.setProperty("--canvas-aspect", `${width} / ${height}`);
    context.imageSmoothingEnabled = false;
  }
}

function drawMapBase(map, perception = null) {
  normalizeMapGeometry(map);
  normalizeMapCollision(map, state);
  for (let y = 0; y < map.height; y += 1) {
    for (let x = 0; x < map.width; x += 1) {
      const coordinates = coordinateFromCell(map, x, y);
      const fogState = perception ? fogStateFor(perception, map, coordinates) : FOG_STATES.VISIBLE_NOW;
      if (fogState === FOG_STATES.UNKNOWN || fogState === FOG_STATES.AUDIBLE_ONLY) {
        drawFogCell(map, coordinates, fogState);
        continue;
      }
      const definitionId = map.terrain?.overrides?.find((item) => {
        const ox = Number.isInteger(item.q) ? item.q : item.x;
        const oy = Number.isInteger(item.r) ? item.r : item.y;
        return ox === x && oy === y;
      })?.definitionId || map.terrain?.default || "grass";
      context.save();
      if (fogState === FOG_STATES.DISCOVERED_NOT_VISIBLE) context.globalAlpha = 0.38;
      drawTileDefinition(definitionId, coordinates, map, 1);
      context.restore();
    }
  }
  drawAtlasMapInstances(map, perception);
  const tiles = state.role === "player" && state.scene !== SCENES.ENCOUNTER && state.scene !== SCENES.REPLAY
    ? map.placedTiles.filter((tile) => tile.visible !== false && !tile.hiddenFromPlayers && tilePerceptionState(tile, map, perception) !== FOG_STATES.UNKNOWN && tilePerceptionState(tile, map, perception) !== FOG_STATES.AUDIBLE_ONLY)
    : map.placedTiles.filter((tile) => tile.visible !== false);
  tiles.forEach((tile) => {
    const visibility = tilePerceptionState(tile, map, perception);
    context.save();
    if (visibility === FOG_STATES.DISCOVERED_NOT_VISIBLE) context.globalAlpha = 0.35;
    drawPlacedTile(tile, map);
    context.restore();
  });
}

function drawExploration(map, perception = null) {
  map.entities.filter((entity) => {
    if (entity.visible === false) return false;
    if (!perception) return true;
    const key = cellKey(map, coordinateFromCell(map, entity.x, entity.y));
    return perception.visibleCellKeys.includes(key) || (entity.controller === "player" && entity.assignedPlayerId === state.actorPlayerId);
  }).forEach((entity) => {
    drawEntitySprite(entity, entity.x, entity.y, map, entity.id === state.selectedEntityId);
  });
  const tile = findTile(map, state.selectedTileId);
  if (tile && (state.role === "gm" || (!tile.hiddenFromPlayers && tilePerceptionState(tile, map, perception) === FOG_STATES.VISIBLE_NOW))) drawTileSelection(map, tile, "#f4c75e");
  const atlasInstance = findAtlasInstance(map, state.selectedAtlasInstanceId);
  if (atlasInstance && (state.role === "gm" || atlasInstance.hiddenFromPlayers !== true)) drawAtlasSelection(atlasInstance, "#8fd3ff");
  if (state.selection?.mapId === map.id && !tile) drawCellSelection(map, state.selection.coordinates, "#f4c75e");
}

function tilePerceptionState(tile, map, perception) {
  if (!perception) return FOG_STATES.VISIBLE_NOW;
  const states = [];
  for (let y = 0; y < tile.height; y += 1) {
    for (let x = 0; x < tile.width; x += 1) {
      states.push(fogStateFor(perception, map, coordinateFromCell(map, tile.x + x, tile.y + y)));
    }
  }
  if (states.includes(FOG_STATES.VISIBLE_NOW)) return FOG_STATES.VISIBLE_NOW;
  if (states.includes(FOG_STATES.DISCOVERED_NOT_VISIBLE)) return FOG_STATES.DISCOVERED_NOT_VISIBLE;
  if (states.includes(FOG_STATES.AUDIBLE_ONLY)) return FOG_STATES.AUDIBLE_ONLY;
  return FOG_STATES.UNKNOWN;
}

function drawFogCell(map, coordinates, fogState) {
  const polygon = cellPolygon(map, coordinates);
  context.save();
  context.fillStyle = fogState === FOG_STATES.AUDIBLE_ONLY ? "rgba(34, 28, 44, 0.96)" : "rgba(6, 8, 10, 0.98)";
  fillPolygon(polygon);
  if (fogState === FOG_STATES.AUDIBLE_ONLY) {
    context.strokeStyle = "rgba(169, 145, 97, 0.24)";
    context.lineWidth = 1;
    strokePolygon(polygon);
  }
  context.restore();
}

function drawPerceptionPresentation(map, playerPerception = null) {
  if (playerPerception) drawSoundPulses(map, playerPerception);
  if (state.role === "gm" && state.editor.perceptionDebug?.enabled && state.scene === SCENES.MAP_VIEW) {
    const perception = computePlayerPerception(state, map, state.actorPlayerId, { updateKnowledge: false });
    drawPerceptionDebug(map, perception);
  }
}

function drawSoundPulses(map, perception) {
  const phase = ((lastFrame || 0) % 1800) / 1800;
  (perception.perceivedSounds || []).forEach((sound) => {
    const marker = sound.perceivedSound?.markerPosition;
    if (!marker) return;
    const center = cellCenter(map, marker);
    const radius = Math.max(5, (sound.perceivedSound.directionUncertaintyDeg || 10) / 2 + phase * 16);
    context.save();
    context.globalAlpha = Math.max(0.08, (1 - phase) * 0.55);
    context.strokeStyle = sound.category === "combat" ? "#d96a57" : "#d8c890";
    context.lineWidth = 1.5;
    context.beginPath();
    context.arc(center.x, center.y, radius, 0, Math.PI * 2);
    context.stroke();
    context.globalAlpha *= 0.35;
    context.beginPath();
    context.arc(center.x, center.y, radius + 4, 0, Math.PI * 2);
    context.stroke();
    context.restore();
  });
}

function drawPerceptionDebug(map, perception) {
  if (!perception?.origin) return;
  const origin = cellCenter(map, perception.origin);
  context.save();
  if (state.editor.perceptionDebug.vision) {
    context.strokeStyle = "rgba(109, 187, 122, 0.5)";
    context.lineWidth = 1;
    context.beginPath();
    context.arc(origin.x, origin.y, perception.visionRangeCells * map.tileSize, 0, Math.PI * 2);
    context.stroke();
    context.fillStyle = "rgba(109, 187, 122, 0.08)";
    perception.visibleCellKeys.forEach((key) => {
      const coords = cellIdToCoordinates(key);
      if (coords) fillPolygon(cellPolygon(map, coords));
    });
  }
  if (state.editor.perceptionDebug.hearing) {
    context.strokeStyle = "rgba(216, 200, 144, 0.5)";
    context.lineWidth = 1;
    context.beginPath();
    context.arc(origin.x, origin.y, perception.hearingRangeCells * map.tileSize, 0, Math.PI * 2);
    context.stroke();
  }
  if (state.editor.perceptionDebug.acousticPaths) {
    (perception.perceivedSounds || []).forEach((sound) => {
      const marker = sound.perceivedSound?.markerPosition;
      if (!marker) return;
      const target = cellCenter(map, marker);
      context.strokeStyle = "rgba(216, 200, 144, 0.45)";
      context.setLineDash([3, 3]);
      context.beginPath();
      context.moveTo(origin.x, origin.y);
      context.lineTo(target.x, target.y);
      context.stroke();
      context.setLineDash([]);
    });
  }
  context.restore();
}

function cellIdToCoordinates(key) {
  const parts = String(key).split(":");
  const type = parts.at(-3);
  if (type === "hex") return { q: Number(parts.at(-2)), r: Number(parts.at(-1)) };
  if (type === "square") return { x: Number(parts.at(-2)), y: Number(parts.at(-1)) };
  return null;
}

function drawEncounter(encounter) {
  if (!encounter) return;
  const map = state.maps[encounter.battleMapId];
  encounter.combatants.forEach((entity) => {
    if (entity.defeated && state.role === "player") return;
    drawEntitySprite(entity, entity.x, entity.y, map, entity.id === encounter.activeEntityId);
    drawHealth(entity, map);
  });
  const selected = encounter.combatants.find((entity) => entity.id === state.selectedEntityId);
  if (selected) drawCellSelection(map, coordinateFromCell(map, selected.x, selected.y), "#fff8c7");
}

function drawGrid(map, perception = null) {
  normalizeMapGeometry(map);
  context.save();
  context.strokeStyle = "rgba(20, 24, 28, 0.45)";
  context.lineWidth = 1;
  if (perception) {
    for (let y = 0; y < map.height; y += 1) {
      for (let x = 0; x < map.width; x += 1) {
        const coordinates = coordinateFromCell(map, x, y);
        const fogState = fogStateFor(perception, map, coordinates);
        if (fogState === FOG_STATES.UNKNOWN) continue;
        strokePolygon(cellPolygon(map, coordinates));
      }
    }
    context.restore();
    return;
  }
  if (map.gridType === GRID_TYPES.HEX) {
    for (let r = 0; r < map.height; r += 1) {
      for (let q = 0; q < map.width; q += 1) {
        strokePolygon(cellPolygon(map, { q, r }));
      }
    }
  } else {
    for (let x = 0; x <= map.width; x += 1) {
      context.beginPath();
      context.moveTo(x * map.tileSize + 0.5, 0);
      context.lineTo(x * map.tileSize + 0.5, map.height * map.tileSize);
      context.stroke();
    }
    for (let y = 0; y <= map.height; y += 1) {
      context.beginPath();
      context.moveTo(0, y * map.tileSize + 0.5);
      context.lineTo(map.width * map.tileSize, y * map.tileSize + 0.5);
      context.stroke();
    }
  }
  context.restore();
}

function drawTileDefinition(definitionId, coordinates, map, scale = 1, imageRef = null) {
  normalizeMapGeometry(map);
  const indexed = coordinateToIndex(map, coordinates);
  const polygon = cellPolygon(map, coordinates);
  const definition = state.tileDefinitions[definitionId];
  const effectiveImageRef = imageRef || definition?.image || null;
  context.save();
  clipPolygon(polygon);
  if (effectiveImageRef?.imageAssetId) {
    if (drawTileImage(effectiveImageRef, polygon, map, scale)) {
      drawWoodcutAnimation(definitionId, polygon);
      context.restore();
      return;
    }
    drawMissingImageFallback(polygon);
    context.restore();
    return;
  }
  const sprite = spriteCache.get(definitionId);
  if (sprite) {
    if (map.gridType === GRID_TYPES.HEX) {
      const bounds = polygonBounds(polygon);
      context.drawImage(sprite, bounds.x, bounds.y, bounds.width * scale, bounds.height * scale);
    } else {
      context.drawImage(sprite, indexed.x * map.tileSize, indexed.y * map.tileSize, map.tileSize * scale, map.tileSize * scale);
    }
    context.restore();
    return;
  }
  context.fillStyle = "#555";
  fillPolygon(polygon);
  context.restore();
}

function drawWoodcutAnimation(definitionId, polygon) {
  if (!["water", "trigger-marker", "fireplace", "torch", "portal", "magical-terrain"].includes(definitionId)) return;
  const bounds = polygonBounds(polygon);
  const phase = Math.floor((lastFrame || 0) / 420) % 4;
  context.save();
  context.globalAlpha = 0.18;
  context.strokeStyle = definitionId === "water" ? "#d8c890" : "#f1c96b";
  context.lineWidth = 1;
  if (definitionId === "water") {
    for (let y = bounds.y + 6 + phase; y < bounds.y + bounds.height; y += 8) {
      context.beginPath();
      context.moveTo(bounds.x + 3, y);
      context.lineTo(bounds.x + bounds.width - 3, y - 2);
      context.stroke();
    }
  } else {
    const cx = bounds.x + bounds.width / 2;
    const cy = bounds.y + bounds.height / 2;
    context.beginPath();
    context.arc(cx, cy, Math.max(4, Math.min(bounds.width, bounds.height) / 4 + phase), 0, Math.PI * 2);
    context.stroke();
  }
  context.restore();
}

function drawPlacedTile(tile, map) {
  for (let y = 0; y < tile.height; y += 1) {
    for (let x = 0; x < tile.width; x += 1) {
      drawTileDefinition(tile.definitionId, coordinateFromCell(map, tile.x + x, tile.y + y), map, 1, tile.image);
    }
  }
  if (tile.hiddenFromPlayers && state.role === "gm") {
    context.fillStyle = "rgba(226, 94, 163, 0.38)";
    drawTileOverlay(map, tile);
  }
}

function drawAtlasMapInstances(map, perception = null) {
  sortedAtlasInstances(map, state.atlasRegistry).forEach(({ instance, asset }) => {
    if (state.role === "player" && instance.hiddenFromPlayers) return;
    if (perception) {
      const cell = worldToCell(map, { x: instance.x, y: instance.y });
      const fogState = cell ? fogStateFor(perception, map, cell.coordinates) : FOG_STATES.UNKNOWN;
      if (fogState === FOG_STATES.UNKNOWN || fogState === FOG_STATES.AUDIBLE_ONLY) return;
      context.save();
      if (fogState === FOG_STATES.DISCOVERED_NOT_VISIBLE) context.globalAlpha = 0.35;
      drawAtlasInstance(instance, asset);
      context.restore();
      return;
    }
    drawAtlasInstance(instance, asset);
  });
}

function drawAtlasInstance(instance, asset) {
  const image = asset ? assetImageCache.get(asset.assetId) : null;
  context.save();
  context.translate(instance.x, instance.y);
  context.rotate(((instance.rotationDeg || 0) * Math.PI) / 180);
  const width = instance.width * (instance.scale || 1);
  const height = instance.height * (instance.scale || 1);
  if (image && image.complete && image.naturalWidth > 0) {
    context.drawImage(image, -width / 2, -height / 2, width, height);
  } else {
    context.fillStyle = "#3f2034";
    context.fillRect(-width / 2, -height / 2, width, height);
    context.strokeStyle = "#f4c75e";
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(-width / 2, -height / 2);
    context.lineTo(width / 2, height / 2);
    context.moveTo(width / 2, -height / 2);
    context.lineTo(-width / 2, height / 2);
    context.stroke();
  }
  context.restore();
}

function drawAtlasSelection(instance, color) {
  context.save();
  context.translate(instance.x, instance.y);
  context.rotate(((instance.rotationDeg || 0) * Math.PI) / 180);
  context.strokeStyle = color;
  context.lineWidth = 2;
  context.strokeRect(-instance.width / 2, -instance.height / 2, instance.width, instance.height);
  context.restore();
}

function hitTestAtlasInstanceAtPoint(map, worldPoint, role = "gm") {
  const rows = sortedAtlasInstances(map, state.atlasRegistry).filter((row) => role !== "player" || row.instance.hiddenFromPlayers !== true);
  for (let index = rows.length - 1; index >= 0; index -= 1) {
    const { instance, asset } = rows[index];
    if (atlasAlphaHitTest(instance, asset, worldPoint)) return instance;
  }
  return null;
}

function atlasAlphaHitTest(instance, asset, worldPoint) {
  const local = atlasLocalPoint(instance, worldPoint);
  if (local.x < 0 || local.y < 0 || local.x > 1 || local.y > 1) return false;
  if (!asset) return true;
  const image = assetImageCache.get(asset.assetId);
  if (!image || image.dataset.failed === "true" || !image.complete || image.naturalWidth <= 0 || image.naturalHeight <= 0) return true;
  const sample = atlasAlphaSample(asset.assetId, image, local);
  return sample == null ? true : sample > 12;
}

function atlasLocalPoint(instance, worldPoint) {
  const width = instance.width * (instance.scale || 1);
  const height = instance.height * (instance.scale || 1);
  const angle = -((instance.rotationDeg || 0) * Math.PI) / 180;
  const dx = worldPoint.x - instance.x;
  const dy = worldPoint.y - instance.y;
  const localX = dx * Math.cos(angle) - dy * Math.sin(angle);
  const localY = dx * Math.sin(angle) + dy * Math.cos(angle);
  return {
    x: (localX + width / 2) / width,
    y: (localY + height / 2) / height
  };
}

function atlasAlphaSample(assetId, image, local) {
  let cached = atlasAlphaHitCache.get(assetId);
  if (!cached) {
    const canvasNode = document.createElement("canvas");
    canvasNode.width = image.naturalWidth;
    canvasNode.height = image.naturalHeight;
    const ctx = canvasNode.getContext("2d", { willReadFrequently: true });
    if (!ctx) return null;
    ctx.drawImage(image, 0, 0);
    cached = { canvas: canvasNode, ctx };
    atlasAlphaHitCache.set(assetId, cached);
  }
  const x = clamp(Math.floor(local.x * cached.canvas.width), 0, cached.canvas.width - 1);
  const y = clamp(Math.floor(local.y * cached.canvas.height), 0, cached.canvas.height - 1);
  return cached.ctx.getImageData(x, y, 1, 1).data[3];
}

function drawEntitySprite(entity, x, y, map, selected) {
  context.save();
  const base = entity.faction === "monsters" || entity.controller === "gm" ? "#813c3a" : entity.assignedPlayerId === "player-b" ? "#4e6f40" : "#2f5d8a";
  const accent = entity.role === "commander" ? "#f4c75e" : entity.faction === "monsters" ? "#d96a57" : "#8fd3ff";
  const center = cellCenter(map, coordinateFromCell(map, x, y));
  const size = map.gridType === GRID_TYPES.HEX ? hexPixelRadius(map) * 1.2 : map.tileSize;
  const px = center.x - size / 2;
  const py = center.y - size / 2;
  context.fillStyle = "rgba(0,0,0,0.34)";
  context.fillRect(px + size * 0.2, py + size * 0.76, size * 0.62, Math.max(2, size * 0.12));
  context.fillStyle = base;
  context.fillRect(px + size * 0.25, py + size * 0.28, size * 0.5, size * 0.56);
  context.fillStyle = accent;
  context.fillRect(px + size * 0.31, py + size * 0.13, size * 0.38, size * 0.25);
  context.fillStyle = "#fff8c7";
  context.fillRect(px + size * 0.38, py + size * 0.34, 1, 1);
  context.fillRect(px + size * 0.58, py + size * 0.34, 1, 1);
  if (entity.defeated) {
    context.fillStyle = "rgba(0,0,0,0.55)";
    context.fillRect(px + 2, py + 2, size - 4, size - 4);
  }
  if (selected) drawCellSelection(map, coordinateFromCell(map, x, y), "#f4c75e");
  context.restore();
}

function drawHealth(entity, map) {
  const center = cellCenter(map, coordinateFromCell(map, entity.x, entity.y));
  const barWidth = map.gridType === GRID_TYPES.HEX ? hexPixelRadius(map) * 1.4 : 12;
  const px = center.x - barWidth / 2;
  const py = center.y + (map.gridType === GRID_TYPES.HEX ? hexPixelRadius(map) * 0.55 : map.tileSize * 0.38);
  context.fillStyle = "#1c1b18";
  context.fillRect(px, py, barWidth, 2);
  context.fillStyle = entity.faction === "players" ? "#6dbb7a" : "#d96a57";
  context.fillRect(px, py, Math.max(0, Math.ceil((entity.hp / entity.maxHp) * barWidth)), 2);
}

function drawTileSelection(map, tile, color) {
  for (let y = 0; y < tile.height; y += 1) {
    for (let x = 0; x < tile.width; x += 1) {
      drawCellSelection(map, coordinateFromCell(map, tile.x + x, tile.y + y), color);
    }
  }
}

function drawCellSelection(map, coordinates, color) {
  context.save();
  context.strokeStyle = color;
  context.lineWidth = 2;
  if (map.gridType === GRID_TYPES.HEX) {
    strokePolygon(cellPolygon(map, coordinates), true);
  } else {
    const index = coordinateToIndex(map, coordinates);
    context.strokeRect(index.x * map.tileSize + 1, index.y * map.tileSize + 1, map.tileSize - 2, map.tileSize - 2);
  }
  context.restore();
}

function clipPolygon(polygon) {
  context.beginPath();
  polygon.forEach((point, index) => {
    if (index === 0) context.moveTo(point.x, point.y);
    else context.lineTo(point.x, point.y);
  });
  context.closePath();
  context.clip();
}

function fillPolygon(polygon) {
  context.beginPath();
  polygon.forEach((point, index) => {
    if (index === 0) context.moveTo(point.x, point.y);
    else context.lineTo(point.x, point.y);
  });
  context.closePath();
  context.fill();
}

function strokePolygon(polygon, selected = false) {
  context.beginPath();
  polygon.forEach((point, index) => {
    if (index === 0) context.moveTo(point.x, point.y);
    else context.lineTo(point.x, point.y);
  });
  context.closePath();
  if (selected) context.lineWidth = 2;
  context.stroke();
}

function polygonBounds(polygon) {
  const xs = polygon.map((point) => point.x);
  const ys = polygon.map((point) => point.y);
  const x = Math.min(...xs);
  const y = Math.min(...ys);
  return { x, y, width: Math.max(...xs) - x, height: Math.max(...ys) - y };
}

function drawTileImage(imageRef, polygon) {
  const image = assetImageCache.get(imageRef.imageAssetId);
  if (!image || !image.complete || image.naturalWidth === 0) return false;
  const bounds = polygonBounds(polygon);
  context.save();
  context.globalAlpha = typeof imageRef.opacity === "number" ? clamp(imageRef.opacity, 0, 1) : 1;
  context.translate(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2);
  context.rotate(((imageRef.rotationDeg || 0) * Math.PI) / 180);
  context.scale(imageRef.flipX ? -1 : 1, imageRef.flipY ? -1 : 1);
  const fit = imageRef.fitMode || "cover";
  let drawWidth = bounds.width;
  let drawHeight = bounds.height;
  if (fit === "contain") {
    const ratio = Math.min(bounds.width / image.naturalWidth, bounds.height / image.naturalHeight);
    drawWidth = image.naturalWidth * ratio;
    drawHeight = image.naturalHeight * ratio;
  } else if (fit === "cover") {
    const ratio = Math.max(bounds.width / image.naturalWidth, bounds.height / image.naturalHeight);
    drawWidth = image.naturalWidth * ratio;
    drawHeight = image.naturalHeight * ratio;
  }
  if (fit === "tile") {
    context.translate(-bounds.width / 2, -bounds.height / 2);
    const pattern = context.createPattern(image, "repeat");
    context.fillStyle = pattern;
    context.fillRect(0, 0, bounds.width, bounds.height);
  } else {
    context.drawImage(image, -drawWidth / 2, -drawHeight / 2, drawWidth, drawHeight);
  }
  context.restore();
  return true;
}

function drawMissingImageFallback(polygon) {
  const bounds = polygonBounds(polygon);
  context.fillStyle = "#3f2034";
  context.fillRect(bounds.x, bounds.y, bounds.width, bounds.height);
  context.strokeStyle = "#f4c75e";
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(bounds.x, bounds.y);
  context.lineTo(bounds.x + bounds.width, bounds.y + bounds.height);
  context.moveTo(bounds.x + bounds.width, bounds.y);
  context.lineTo(bounds.x, bounds.y + bounds.height);
  context.stroke();
}

function drawTileOverlay(map, tile) {
  for (let y = 0; y < tile.height; y += 1) {
    for (let x = 0; x < tile.width; x += 1) {
      const polygon = cellPolygon(map, coordinateFromCell(map, tile.x + x, tile.y + y));
      fillPolygon(polygon);
    }
  }
}

function buildSpriteCache() {
  spriteCache = new Map();
  state.tileManifest.definitions.forEach((definition) => {
    const offscreen = document.createElement("canvas");
    offscreen.width = state.tileManifest.tileSize;
    offscreen.height = state.tileManifest.tileSize;
    const ctx = offscreen.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    ctx.fillStyle = definition.sprite.base;
    ctx.fillRect(0, 0, offscreen.width, offscreen.height);
    definition.sprite.rects.forEach((rect) => {
      ctx.fillStyle = rect.color;
      ctx.fillRect(rect.x, rect.y, rect.w, rect.h);
    });
    spriteCache.set(definition.id, offscreen);
  });
}

function buildAssetImageCache() {
  assetImageCache = new Map();
  atlasAlphaHitCache = new Map();
  [...tileAssets(state.tileAssetRegistry), ...atlasAssets(state.tileAssetRegistry)].forEach((asset) => {
    const image = new Image();
    image.decoding = "async";
    image.onload = () => renderAll();
    image.onerror = () => {
      image.dataset.failed = "true";
      renderAll();
    };
    image.src = asset.sourcePath;
    assetImageCache.set(asset.assetId, image);
  });
  atlasRenderableAssets(state.atlasRegistry).forEach((asset) => {
    const image = new Image();
    image.decoding = "async";
    image.onload = () => renderAll();
    image.onerror = () => {
      image.dataset.failed = "true";
      renderAll();
    };
    image.src = asset.derivedPath;
    assetImageCache.set(asset.assetId, image);
  });
}

function currentReplay() {
  return state.replays.find((replay) => replay.replayId === state.replay.selectedReplayId) || state.replays.at(-1) || null;
}

function initializeReplayDisplay() {
  const replay = currentReplay();
  if (!replay) return;
  state.replay.cursor = Math.max(0, Math.min(state.replay.cursor, replay.orderedEvents.length));
  state.replay.displayState = rebuildEncounterState(replay, state.replay.cursor);
}

function stepReplay(delta, rerender = true) {
  const replay = currentReplay();
  if (!replay) return;
  state.replay.cursor = Math.max(0, Math.min(replay.orderedEvents.length, state.replay.cursor + delta));
  state.replay.displayState = rebuildEncounterState(replay, state.replay.cursor);
  if (state.replay.cursor >= replay.orderedEvents.length) state.replay.playing = false;
  if (rerender) renderAll();
}

function stepReplayRound(delta) {
  const replay = currentReplay();
  if (!replay) return;
  const rounds = replayRounds(replay);
  const current = rounds.reduce((chosen, item) => (item.index <= state.replay.cursor ? item : chosen), rounds[0]);
  const index = Math.max(0, Math.min(rounds.length - 1, rounds.indexOf(current) + delta));
  state.replay.cursor = rounds[index].index;
  state.replay.displayState = rebuildEncounterState(replay, state.replay.cursor);
  renderAll();
}

function verifyCurrentReplay() {
  const replay = currentReplay();
  if (!replay) return { ok: false, message: "No replay." };
  const live = state.activeEncounter ? comparableEncounterState(state.activeEncounter) : replay.finalState;
  return verifyReplayRecord(replay, live);
}

function showMapForVerification(mapId) {
  if (!state.maps[mapId]) return { ok: false, message: "Map not found." };
  state.currentMapId = mapId;
  state.lastValidMapId = mapId;
  state.scene = SCENES.MAP_EDIT;
  state.role = "gm";
  fitCurrentMap();
  renderAll();
  return { ok: true, mapId, gridType: state.maps[mapId].gridType };
}

async function runAcceptanceScript() {
  await resetApplication();
  const checks = [];
  const pass = (name, condition, data = {}) => {
    const ok = Boolean(condition);
    checks.push({ name, status: ok ? "PASS" : "FAIL", ...data });
    if (!ok) throw new Error(`Acceptance failed: ${name}`);
  };
  const openTile = (tileId) => {
    const map = getCurrentMap(state);
    const tile = findTile(map, tileId);
    state.selectedTileId = tileId;
    const result = openChildMapFromTile(state, tile, { role: "gm" });
    pass(`open ${tileId}`, result.ok && state.currentMapId === tile.childMapId);
  };

  setRole("gm");
  pass("gm view", state.role === "gm" && state.scene === SCENES.MAP_VIEW);
  pass("open world", state.currentMapId === "map-world");

  const parentState = createGameState(bundleCache);
  parentState.scene = SCENES.MAP_VIEW;
  const parentTile = findTile(getCurrentMap(parentState), "tile-world-city");
  openChildMapFromTile(parentState, parentTile, { role: "gm" });
  const parentReturn = returnToParentMap(parentState, { role: "gm" });
  pass("parent return works", parentReturn.ok && parentState.currentMapId === "map-world" && parentState.selectedTileId === "tile-world-city");

  const editorState = createGameState(bundleCache);
  editorState.scene = SCENES.MAP_EDIT;
  const placed = placeTile(editorState, "chair", 1, 1);
  pass("tile placement works", placed.ok && getCurrentMap(editorState).placedTiles.some((tile) => tile.id === placed.tile.id));

  const manualState = createGameState(bundleCache);
  manualState.scene = SCENES.MAP_VIEW;
  ["tile-world-city", "tile-city-block", "tile-block-tavern"].forEach((tileId) => {
    const tile = findTile(getCurrentMap(manualState), tileId);
    openChildMapFromTile(manualState, tile, { role: "gm" });
  });
  manualState.selectedTileId = "tile-tavern-ambush-trigger";
  const manual = manualTriggerSelectedTile(manualState);
  pass("manual gm trigger works", manual.ok && manualState.scene === SCENES.ENCOUNTER);

  openTile("tile-world-city");
  openTile("tile-city-block");
  openTile("tile-block-tavern");
  pass("breadcrumb tavern", getMapPath(state).map((item) => item.name).join(" > ") === "World > City > Block > Tavern Main Floor");

  setRole("player");
  const publicMap = playerVisibleSnapshot(state);
  pass("hidden trigger invisible to player", !publicMap.placedTiles.some((tile) => tile.id === "tile-tavern-ambush-trigger"));
  state.selectedEntityId = "pc-lyra";
  ["right", "right", "right"].forEach((direction) => {
    const vector = directionVector(direction);
    const result = moveExplorationEntity(state, "pc-lyra", vector.dx, vector.dy, { role: "player", playerId: "player-a" });
    if (result.ok) processMapEvent(state, "player_enters_tile", { entityId: "pc-lyra", from: result.from, to: result.to, actorRole: "player" });
  });
  pass("encounter launched", state.scene === SCENES.ENCOUNTER && state.activeEncounter?.encounterId === "enc-tavern-ambush");
  pass("territory background correct", state.activeEncounter.territoryId === "map-tavern-main-floor" && getCurrentMap(state).placedTiles.some((tile) => tile.definitionId === "bar"));

  setRole("gm");
  const orderResult = issueCommanderOrder(state, { role: "gm" }, "attack_nearest", { targetId: "pc-lyra" });
  pass("commander order issued", orderResult.ok);
  pass("ordinary monsters queued", orderResult.queued.length === 3);
  const overrideTarget = orderResult.queued[0].entityId;
  const overrideResult = directMonsterOverride(state, { role: "gm" }, overrideTarget, "defend");
  pass("direct override", overrideResult.ok && state.activeEncounter.pendingCommanderActions.some((item) => item.entityId === overrideTarget && item.source === "direct_gm"));

  setRole("player");
  const lyra = activeCombatant(state);
  pass("player active authorized", lyra.id === "pc-lyra" && lyra.assignedPlayerId === "player-a");
  const moveA = executeEncounterAction(state, { role: "player", playerId: "player-a" }, { type: "move", direction: "right" });
  pass("player move cost", moveA.ok && activeCombatant(state).timeSpent === 1);
  const invalid = executeEncounterAction(state, { role: "player", playerId: "player-b" }, { type: "defend" });
  pass("invalid action no time", !invalid.ok && activeCombatant(state).timeSpent === 1);
  executeEncounterAction(state, { role: "player", playerId: "player-a" }, { type: "move", direction: "right" });
  executeEncounterAction(state, { role: "player", playerId: "player-a" }, { type: "defend" });
  pass("time chain", activeCombatant(state).timeSpent === 4);
  executeEncounterAction(state, { role: "player", playerId: "player-a" }, { type: "wait" });
  pass("time wait advances", state.activeEncounter.activeEntityId !== "pc-lyra");

  const finishResult = autoResolveEncounterToEnd(state);
  pass("encounter completed", finishResult.ok && state.activeEncounter.status === "completed");
  pass("replay saved", state.replays.length === 1 && state.replays[0].finalStateHash);
  setScene(SCENES.REPLAY);
  while (state.replay.cursor < currentReplay().orderedEvents.length) stepReplay(1, false);
  const verification = verifyCurrentReplay();
  pass("replay hash matches", verification.finalStateHashMatches && verification.repeatHashMatches && verification.replayDoesNotMutateLiveState, verification);
  exitEncounterToMap(state);
  pass("returned to tavern main floor", state.scene === SCENES.MAP_VIEW && state.currentMapId === "map-tavern-main-floor");
  saveState(state);
  const restored = createGameState(bundleCache, JSON.parse(localStorage.getItem("shaelvien.recursive.tabletop.v0")));
  pass("refresh restores valid map", restored.scene === SCENES.MAP_VIEW && restored.maps[restored.currentMapId]);
  persistAndRender();
  return {
    checks,
    finalStateHash: currentReplay()?.finalStateHash || null,
    integrityHash: currentReplay()?.integrityHash || null,
    eventCount: state.eventLog.length
  };
}

async function runEditorAcceptanceScript() {
  await resetApplication();
  const checks = [];
  const pass = (name, condition, data = {}) => {
    const ok = Boolean(condition);
    checks.push({ name, status: ok ? "PASS" : "FAIL", ...data });
    if (!ok) throw new Error(`Editor acceptance failed: ${name}`);
  };

  setRole("gm");
  setScene(SCENES.MAP_EDIT);
  const world = getCurrentMap(state);
  pass("existing square maps default square", world.gridType === "square");
  pass("world dimensions preserved", world.width === 16 && world.height === 10);
  const tavern = state.maps["map-tavern-main-floor"];
  pass("tavern ambush remains square", tavern.gridType === "square" && tavern.width === 12 && tavern.height === 8);

  const cityTile = findTile(world, "tile-world-city");
  const cityCell = selectionForCell(world, coordinateFromCell(world, cityTile.x, cityTile.y));
  const selected = selectCell(state, world, cityCell);
  pass("direct tile selection works", selected.ok && state.selectedTileId === cityTile.id);
  pass("selected tile identity stable", state.selection.cellId === cellId(world, { x: cityTile.x, y: cityTile.y }));

  state.selectedTileImageAssetId = "woodcut-symbol-city-001";
  const imageSet = setSelectedTileImage(state, state.selectedTileImageAssetId);
  pass("image-backed square tile assignment", imageSet.ok && selectedTile(state).image.imageAssetId === "woodcut-symbol-city-001");
  saveState(state);
  const restored = await createInitialState();
  pass("image assignment save restore", findTile(restored.maps["map-world"], cityTile.id).image?.imageAssetId === "woodcut-symbol-city-001");

  const publicMap = playerVisibleSnapshot(state, state.maps["map-tavern-main-floor"]);
  pass("player hidden trigger remains filtered", !publicMap.placedTiles.some((tile) => tile.id === "tile-tavern-ambush-trigger"));
  pass("player snapshot has no gm notes", publicMap.placedTiles.every((tile) => !tile.metadata?.gmNotes));

  const beforeUndoCount = state.editor.undoStack.length;
  const paint = paintTerrainAtCell(state, world, cityCell, "road");
  const undo = undoEditorEdit(state);
  const redo = redoEditorEdit(state);
  pass("undo redo separate edit stream", paint.ok && undo.ok && redo.ok && state.editor.undoStack.length >= beforeUndoCount);
  pass("gameplay replay stream isolated", state.replays.length === 0);

  state.maps["map-editor-hex-pointy"] = normalizeMapGeometry({
    schemaVersion: "shaelvien.map.v2",
    id: "map-editor-hex-pointy",
    name: "Editor Hex Pointy Test",
    category: "interior",
    parentMapId: null,
    parentTileId: null,
    width: 4,
    height: 4,
    tileSize: 24,
    gridType: "hex",
    gridSettings: { hex: { orientation: "pointy", radius: 5, radiusMeaning: "center_to_corner", unitSystem: "imperial", distanceUnit: "ft", layoutBounds: { columns: 4, rows: 4 } } },
    terrain: { default: "floor", overrides: [] },
    placedTiles: [],
    entities: [],
    entryPoints: [],
    exitPoints: [],
    triggers: [],
    permissions: { gm: { canView: true, canEdit: true }, player: { canView: true } },
    atmosphere: { light: "test", sound: "silent", gmNotes: "" },
    encounterReferences: []
  });
  state.currentMapId = "map-editor-hex-pointy";
  const pointyMap = getCurrentMap(state);
  const pointyCenter = cellCenter(pointyMap, { q: 1, r: 1 });
  const pointyHit = worldToCell(pointyMap, pointyCenter);
  pass("pointy hex hit exact center", pointyHit?.coordinates.q === 1 && pointyHit?.coordinates.r === 1);
  pass("pointy hex polygon contains center", pointInPolygon(pointyCenter, cellPolygon(pointyMap, { q: 1, r: 1 })));
  const placedHex = placeTile(state, "floor", 1, 1);
  selectedTile(state).image = { imageAssetId: "woodcut-object-table-001", fitMode: "cover", rotationDeg: 0, flipX: false, flipY: false, opacity: 1, tint: null };
  pass("image-backed hex tile reference", placedHex.ok && selectedTile(state).image.imageAssetId === "woodcut-object-table-001");

  state.maps["map-editor-hex-flat"] = normalizeMapGeometry({
    ...deepClone(pointyMap),
    id: "map-editor-hex-flat",
    name: "Editor Hex Flat Test",
    placedTiles: [],
    gridSettings: { hex: { orientation: "flat", radius: 5, radiusMeaning: "center_to_corner", unitSystem: "metric", distanceUnit: "m", layoutBounds: { columns: 4, rows: 4 } } }
  });
  state.currentMapId = "map-editor-hex-flat";
  const flatMap = getCurrentMap(state);
  const flatCenter = cellCenter(flatMap, { q: 2, r: 1 });
  const flatHit = worldToCell(flatMap, flatCenter);
  pass("flat hex hit exact center", flatHit?.coordinates.q === 2 && flatHit?.coordinates.r === 1);
  pass("hex radius meaning recorded", flatMap.gridSettings.hex.radiusMeaning === "center_to_corner" && hexPhysicalRadius(flatMap) === 5);

  const squarePhysical = deriveMapSettings({ gridType: "square", sizeMode: "physical", width: 80, height: 50, cellWidth: 5, cellHeight: 5, unitSystem: "imperial", distanceUnit: "ft" });
  pass("physical square sizing derives whole cells", squarePhysical.ok && squarePhysical.columns === 16 && squarePhysical.rows === 10);
  const badPhysical = deriveMapSettings({ gridType: "square", sizeMode: "physical", width: 81, height: 50, cellWidth: 5, cellHeight: 5, unitSystem: "imperial", distanceUnit: "ft" });
  pass("non whole square physical sizing rejected", badPhysical.ok === false);
  const hexCoverage = deriveMapSettings({ gridType: "hex", sizeMode: "physical", mapWidth: 80, mapHeight: 50, hexRadius: 5, orientation: "pointy", unitSystem: "metric", distanceUnit: "m" });
  pass("physical hex sizing reports coverage", hexCoverage.ok && hexCoverage.actualWidth > 0 && hexCoverage.deltaWidth !== undefined);

  state.currentMapId = "map-tavern-main-floor";
  const shrink = applyMapSettings(state, {
    name: tavern.name,
    gridType: "square",
    sizeMode: "tile-count",
    columns: 4,
    rows: 4,
    tileSize: tavern.tileSize,
    defaultTerrain: "floor",
    unitSystem: "imperial",
    distanceUnit: "ft",
    cellWidth: 5,
    cellHeight: 5,
    playerVisibilityDefault: "visible"
  }, { confirmShrink: false });
  pass("map resize protects attached content", shrink.ok === false && shrink.impact?.protectedContentCount > 0);
  pass("first preset dimensions unchanged after blocked shrink", state.maps["map-tavern-main-floor"].width === 12 && state.maps["map-tavern-main-floor"].height === 8);

  state.currentMapId = "map-world";
  state.lastValidMapId = "map-world";
  state.scene = SCENES.MAP_EDIT;
  selectCell(state, state.maps["map-world"], cityCell);
  fitCurrentMap();
  saveState(state);
  const restoredAfterViewport = await createInitialState();
  pass("refresh restores selected map and selection", restoredAfterViewport.maps[restoredAfterViewport.currentMapId] && restoredAfterViewport.selection?.cellId);
  persistAndRender();
  return { checks, selectedCell: state.selection, undoDepth: state.editor.undoStack.length };
}

async function runWorkspaceAcceptanceScript() {
  await runEditorAcceptanceScript();
  const checks = [];
  const pass = (name, condition, data = {}) => {
    const ok = Boolean(condition);
    checks.push({ name, status: ok ? "PASS" : "FAIL", ...data });
    if (!ok) throw new Error(`Workspace acceptance failed: ${name}`);
  };

  setRole("gm");
  setScene(SCENES.MAP_EDIT);
  state.currentMapId = "map-world";
  const shellRect = document.querySelector(".app-shell").getBoundingClientRect();
  const appRect = document.querySelector(".app-bar").getBoundingClientRect();
  const toolbarRect = document.querySelector(".main-toolbar").getBoundingClientRect();
  const viewportRect = elements.mapViewport.getBoundingClientRect();
  pass("full viewport application shell", Math.round(shellRect.height) <= window.innerHeight && Math.round(shellRect.width) <= window.innerWidth);
  pass("normal editing no page vertical scroll", document.documentElement.scrollHeight <= window.innerHeight + 1 && document.body.scrollHeight <= window.innerHeight + 1);
  pass("normal editing no page horizontal overflow", document.documentElement.scrollWidth <= window.innerWidth + 1);
  pass("toolbars do not overlap", appRect.bottom <= toolbarRect.top + 1 && toolbarRect.bottom <= viewportRect.top + 20);
  pass("map visible immediately", viewportRect.height > window.innerHeight * (window.innerWidth < 600 ? 0.62 : 0.55));

  fitMapMode("fit-map", { persist: false });
  pass("Fit Map works", currentViewport().fitMode === "fit-map" && currentViewport().zoom > 0);
  fitMapMode("fit-width", { persist: false });
  pass("Fit Width works", currentViewport().fitMode === "fit-width" && currentViewport().zoom > 0);
  fitMapMode("fit-height", { persist: false });
  pass("Fit Height works", currentViewport().fitMode === "fit-height" && currentViewport().zoom > 0);
  setActualSize({ persist: false });
  pass("Actual Size works", currentViewport().fitMode === "actual-size" && Math.abs(currentViewport().zoom - 1) < 0.001);
  const world = state.maps["map-world"];
  selectCell(state, world, selectionForCell(world, { x: 7, y: 4 }));
  fitSelection({ persist: false });
  pass("Fit Selection works", currentViewport().fitMode === "fit-selection" && currentViewport().zoom >= 2);
  resetRotation();
  pass("Compass reset returns North-up", currentViewport().rotationDeg === 0);

  const squareMap = normalizeMapGeometry({
    schemaVersion: "shaelvien.map.v2",
    id: "map-workspace-square-verify",
    name: "Workspace Square Verify",
    category: "interior",
    parentMapId: null,
    parentTileId: null,
    width: 5,
    height: 5,
    tileSize: 24,
    gridType: "square",
    terrain: { default: "floor", overrides: [] },
    placedTiles: [],
    entities: [],
    entryPoints: [],
    exitPoints: [],
    triggers: [],
    permissions: { gm: { canView: true, canEdit: true }, player: { canView: true } },
    atmosphere: { light: "verify", sound: "silent", gmNotes: "" },
    encounterReferences: []
  });
  const pointyMap = state.maps["map-editor-hex-pointy"];
  const flatMap = state.maps["map-editor-hex-flat"];
  state.maps[squareMap.id] = squareMap;
  const rotationResults = [
    verifyRotatedCellTarget(squareMap.id, { x: 2, y: 3 }),
    verifyRotatedCellTarget(pointyMap.id, { q: 1, r: 1 }),
    verifyRotatedCellTarget(flatMap.id, { q: 2, r: 1 })
  ];
  rotationResults.forEach((result) => {
    pass(`${result.gridType} rotated hit testing`, result.ok, result);
  });

  state.currentMapId = "map-workspace-square-verify";
  const map = getCurrentMap(state);
  const paintCell = selectionForCell(map, { x: 3, y: 2 });
  state.selectedPaletteId = "road";
  setActiveTool(state, "paint");
  const paintResult = paintTerrainAtCell(state, map, paintCell, "road");
  const painted = paintResult.ok && map.terrain.overrides.some((item) => item.x === 3 && item.y === 2 && item.definitionId === "road");
  pass("paint applies expected logical cell", painted);

  state.currentMapId = "map-world";
  const viewport = currentViewport();
  viewport.rotationDeg = 270;
  viewport.gridVisible = false;
  viewport.compassVisible = true;
  saveState(state);
  const restored = await createInitialState();
  const restoredViewport = restored.editor.viewportByMap["map-world"];
  pass("viewport state restores independently", restoredViewport?.rotationDeg === 270 && restoredViewport?.gridVisible === false);
  pass("Tavern Ambush remains square", restored.maps["map-tavern-main-floor"].gridType === "square");
  pass("view operations do not create replay records", restored.replays.length === 0);
  state = restored;
  state.scene = SCENES.MAP_EDIT;
  state.role = "gm";
  persistAndRender();
  return { checks, viewport: currentViewport(), shell: { width: shellRect.width, height: shellRect.height } };
}

function verifyRotatedCellTarget(mapId, coordinates) {
  state.currentMapId = mapId;
  state.lastValidMapId = mapId;
  state.scene = SCENES.MAP_EDIT;
  state.role = "gm";
  const map = getCurrentMap(state);
  const expected = selectionForCell(map, coordinates);
  const viewport = currentViewport();
  const results = [0, 90, 180, 270].map((angle) => {
    viewport.rotationDeg = angle;
    viewport.initialized = true;
    fitMapMode("fit-map", { persist: false });
    const point = worldToScreen(cellCenter(map, expected.coordinates));
    const hit = worldToCell(map, screenToWorld(point));
    return {
      angle,
      hit: hit?.cellId || null,
      ok: hit?.cellId === expected.cellId
    };
  });
  return {
    mapId,
    gridType: map.gridType === "hex" ? `${map.gridSettings.hex?.orientation || "pointy"} hex` : "square",
    expected: expected.cellId,
    results,
    ok: results.every((result) => result.ok)
  };
}

async function runTabletopAcceptanceScript() {
  await resetApplication();
  const checks = [];
  const pass = (name, condition, data = {}) => {
    const ok = Boolean(condition);
    checks.push({ name, status: ok ? "PASS" : "FAIL", ...data });
    if (!ok) throw new Error(`Tabletop acceptance failed: ${name}`);
  };

  setRole("gm");
  setScene(SCENES.MAP_VIEW);
  fitCurrentMap({ persist: false });
  const shellRect = document.querySelector(".app-shell").getBoundingClientRect();
  pass("fixed single-screen shell", Math.round(shellRect.height) <= window.innerHeight && document.documentElement.scrollHeight <= window.innerHeight + 1);
  pass("tabletop map central", elements.mapViewport.getBoundingClientRect().height > window.innerHeight * 0.45);

  const world = getCurrentMap(state);
  const cityTile = findTile(world, "tile-world-city");
  const cityCell = selectionForCell(world, coordinateFromCell(world, cityTile.x, cityTile.y));
  const cityPoint = worldToScreen(cellCenter(world, cityCell.coordinates));
  handleCanvasTap(cityCell, cityPoint);
  handleCanvasTap(cityCell, cityPoint);
  pass("double-tap child entry works", state.currentMapId === "map-city");

  const viewport = currentViewport();
  viewport.zoom = 1.5;
  viewport.fitMode = "custom";
  viewport.initialized = true;
  const beforePanX = viewport.offsetX;
  handlePointerDown({ x: 120, y: 120, clientX: 120, clientY: 120 }, { pointerId: 101, pointerType: "touch", button: 0 });
  handlePointerMove({ x: 154, y: 132, clientX: 154, clientY: 132 }, { pointerId: 101, pointerType: "touch", buttons: 1 });
  handlePointerRelease({ x: 154, y: 132, clientX: 154, clientY: 132 }, { pointerId: 101, pointerType: "touch", target: canvas });
  pass("swipe pans map", currentViewport().offsetX !== beforePanX);

  handlePointerDown({ x: 120, y: 120, clientX: 120, clientY: 120 }, { pointerId: 201, pointerType: "touch", button: 0 });
  handlePointerDown({ x: 180, y: 120, clientX: 180, clientY: 120 }, { pointerId: 202, pointerType: "touch", button: 0 });
  const pinchBefore = { zoom: currentViewport().zoom, rotation: currentViewport().rotationDeg };
  handlePointerMove({ x: 110, y: 125, clientX: 110, clientY: 125 }, { pointerId: 201, pointerType: "touch", buttons: 1 });
  handlePointerMove({ x: 198, y: 175, clientX: 198, clientY: 175 }, { pointerId: 202, pointerType: "touch", buttons: 1 });
  handlePointerRelease({ x: 198, y: 175, clientX: 198, clientY: 175 }, { pointerId: 202, pointerType: "touch", target: canvas });
  pass("pinch zoom works", currentViewport().zoom !== pinchBefore.zoom);
  pass("pinch rotate snaps viewport", [0, 90, 180, 270].includes(currentViewport().rotationDeg));

  openOverlay(state.tabletop, "scene");
  renderAll();
  pass("menus open over center", !elements.tabletopOverlay.hidden && !elements.tabletopOverlayBackdrop.hidden);
  closeOverlay(state.tabletop);
  renderAll();
  pass("closed overlays do not intercept input", elements.tabletopOverlay.hidden && elements.tabletopOverlayBackdrop.hidden);

  const gmProjection = tabletopProjection(state.tabletop, "gm", "player-a");
  const playerProjection = tabletopProjection(state.tabletop, "player", "player-a");
  pass("gm scene layout exists", gmProjection.decks.some((deck) => deck.deckId === "deck-orcs-001"));
  pass("player scene privacy filters monster deck", !playerProjection.decks.some((deck) => deck.deckId === "deck-orcs-001"));
  pass("dice row has all dice", gmProjection.dice.length === 9);

  const weaponResult = resolveDiceBagAction(state.tabletop, "card-weapon-sword-001", "attack", { baseAttack: 3 });
  pass("dice bag card action works", weaponResult.ok && weaponResult.result.totalAttack === 17);
  pass("modifier chips visible in result", weaponResult.result.modifiers.length === 2);

  const lore = shareLoreCard(state.tabletop);
  const playerAfterShare = tabletopProjection(state.tabletop, "player", "player-a");
  pass("lore card sharing respects audience", lore.ok && playerAfterShare.cards.some((card) => card.cardId === "card-lore-tavern-warning"));
  const advanced = advanceInitiative(state.tabletop);
  const paused = pauseClock(state.tabletop);
  const resumed = resumeClock(state.tabletop);
  pass("initiative and chess clock work", advanced.ok && paused.ok && resumed.ok);
  pass("viewport state outside tabletop replay", !state.tabletop.replayBoundary.authoritativeEvents.some((event) => event.type.startsWith("viewport_")));
  persistAndRender();
  return {
    checks,
    tabletopEvents: state.tabletop.replayBoundary.authoritativeEvents.length,
    latestDiceBag: weaponResult.result,
    currentMapId: state.currentMapId
  };
}

async function runAtlasAcceptanceScript() {
  await resetApplication();
  const checks = [];
  const pass = (name, condition, data = {}) => {
    const ok = Boolean(condition);
    checks.push({ name, status: ok ? "PASS" : "FAIL", ...data });
    if (!ok) throw new Error(`Atlas acceptance failed: ${name}`);
  };

  setRole("gm");
  setScene(SCENES.MAP_EDIT);
  state.currentMapId = "map-atlas-demo";
  state.lastValidMapId = state.currentMapId;
  state.editor.inspectorOpen = true;
  fitCurrentMap({ persist: false });
  renderAll();

  pass("atlas registry loaded", state.atlasRegistry.sources.length === 3 && state.atlasRegistry.assets.length === 11);
  pass("asset browser generated from registry", elements.atlasBrowser?.querySelectorAll("[data-atlas-asset-id]").length >= 1);
  pass("source provenance retained", state.atlasRegistry.sources.every((source) => source.driveFileId && source.driveParentId && source.chatgptShareId && source.localSourcePath));
  const collections = atlasCollections(state.atlasRegistry);
  pass("collections are data driven", collections.some((collection) => collection.id === "waterfall") && collections.some((collection) => collection.id === "streams_and_small_watercourses"));

  const map = getCurrentMap(state);
  const existingRefs = map.atlasInstances.filter((instance) => instance.assetId === "atlas.wonder.waterfall.001").length;
  pass("multiple instances reference one asset", existingRefs === 2);
  pass("layer ordering deterministic", sortedAtlasInstances(map, state.atlasRegistry)[0].instance.instanceId === "atlas-demo-plains-001");

  const cell = selectionForCell(map, { x: 10, y: 6 });
  selectCell(state, map, cell);
  state.selectedAtlasAssetId = "atlas.wonder.waterfall.002";
  const placed = createAtlasInstance(state, map, state.selectedAtlasAssetId, cell.coordinates);
  pass("atlas asset placement works", placed.ok && map.atlasInstances.some((instance) => instance.instanceId === placed.instance.instanceId));
  const beforeMove = { x: placed.instance.x, y: placed.instance.y };
  const moved = moveSelectedAtlasInstance(state, map, 8, -8);
  pass("atlas move works", moved.ok && moved.instance.x === beforeMove.x + 8 && moved.instance.y === beforeMove.y - 8);
  const rotated = rotateSelectedAtlasInstance(state, map, 90);
  pass("atlas rotation works", rotated.ok && rotated.instance.rotationDeg === 90);
  const child = setAtlasInstanceChildMap(state, map, "map-atlas-demo-waterfall-interior");
  pass("atlas child map attachment works", child.ok && child.instance.childMapId === "map-atlas-demo-waterfall-interior");

  openSelectedAtlasChild();
  pass("atlas child map entry works", state.currentMapId === "map-atlas-demo-waterfall-interior");
  commandResult(returnToParentMap(state, actor()));
  await new Promise((resolve) => window.setTimeout(resolve, 0));
  pass("atlas child map return works", state.currentMapId === "map-atlas-demo" && state.selectedAtlasInstanceId === "atlas-demo-waterfall-001");

  state.currentMapId = "map-atlas-demo";
  state.selectedAtlasInstanceId = placed.instance.instanceId;
  saveState(state);
  const restored = await createInitialState();
  const restoredMap = restored.maps["map-atlas-demo"];
  const restoredInstance = restoredMap.atlasInstances.find((instance) => instance.instanceId === placed.instance.instanceId);
  pass("atlas save reload restores instance", restoredInstance?.assetId === "atlas.wonder.waterfall.002");
  pass("atlas rotation survives reload", restoredInstance?.rotationDeg === 90);
  pass("atlas child relation survives reload", restoredInstance?.childMapId === "map-atlas-demo-waterfall-interior");

  const missingRows = sortedAtlasInstances({ atlasInstances: [{ instanceId: "missing", assetId: "atlas.nope", x: 0, y: 0, width: 1, height: 1, visible: true }] }, state.atlasRegistry);
  pass("unknown asset does not substitute image", missingRows.length === 1 && missingRows[0].asset === null);

  state.currentMapId = "map-atlas-region-stream-demo";
  state.lastValidMapId = state.currentMapId;
  state.selectedAtlasCollection = "streams_and_small_watercourses";
  renderAtlasBrowser();
  const streamMap = getCurrentMap(state);
  const streamAssets = state.atlasRegistry.assets.filter((asset) => asset.collection === "streams_and_small_watercourses");
  const streamRefs = streamMap.atlasInstances.filter((instance) => instance.assetId === "atlas.region.water.stream.straight.001").length;
  pass("production stream collection registered", streamAssets.length === 5);
  pass("production stream collection appears in browser", elements.atlasBrowser?.querySelectorAll("[data-atlas-asset-id]").length >= 5);
  pass("production stream map reuses registered asset", streamRefs === 2);
  pass("production stream map rotation survives load", streamMap.atlasInstances.some((instance) => instance.rotationDeg === 270));
  const streamChild = streamMap.atlasInstances.find((instance) => instance.childMapId === "map-atlas-region-stream-source");
  pass("production stream child map link exists", Boolean(streamChild));
  state.selectedAtlasInstanceId = streamChild.instanceId;
  openSelectedAtlasChild();
  pass("production stream child map entry works", state.currentMapId === "map-atlas-region-stream-source");
  commandResult(returnToParentMap(state, actor()));
  await new Promise((resolve) => window.setTimeout(resolve, 0));
  pass("production stream child map return works", state.currentMapId === "map-atlas-region-stream-demo" && state.selectedAtlasInstanceId === "atlas-region-stream-pool-001");

  state = restored;
  state.currentMapId = "map-atlas-region-stream-demo";
  state.lastValidMapId = state.currentMapId;
  state.scene = SCENES.MAP_EDIT;
  state.role = "gm";
  state.selectedAtlasCollection = "streams_and_small_watercourses";
  buildAssetImageCache();
  persistAndRender();
  return { checks, placedInstanceId: placed.instance.instanceId, restoredRotation: restoredInstance?.rotationDeg, productionMapId: "map-atlas-region-stream-demo" };
}

async function runPerceptionAcceptanceScript() {
  await resetApplication();
  const checks = [];
  const pass = (name, condition, data = {}) => {
    const ok = Boolean(condition);
    checks.push({ name, status: ok ? "PASS" : "FAIL", ...data });
    if (!ok) throw new Error(`Perception acceptance failed: ${name}`);
  };

  state.currentMapId = "map-tavern-main-floor";
  state.lastValidMapId = state.currentMapId;
  state.scene = SCENES.MAP_VIEW;
  setRole("player");
  state.selectedEntityId = "pc-lyra";
  const tavern = getCurrentMap(state);
  const allTilesHaveCollision = Object.values(state.maps).every((map) => map.placedTiles.every((tile) => tile.collision && tile.collisionShape));
  const allEntitiesHaveCollision = Object.values(state.maps).every((map) => map.entities.every((entity) => entity.collision && entity.collisionShape));
  pass("all object instances support collision", allTilesHaveCollision);
  pass("all entity instances support collision", allEntitiesHaveCollision);
  const starts = legalStartCellsForPlayer(state, tavern, "player-a");
  pass("authorized player starts visible", starts.length >= 1);
  const placement = placeOwnedPlayerCharacter(state, tavern, "pc-lyra", starts[0], { role: "player", playerId: "player-a" });
  pass("player can place owned PC", placement.ok);
  const unauthorized = placeOwnedPlayerCharacter(state, tavern, "pc-lyra", starts[0], { role: "player", playerId: "player-b" });
  pass("player cannot place unauthorized entity", !unauthorized.ok);
  const publicMap = playerVisibleSnapshot(state, tavern);
  pass("player data filtered by perception", publicMap.dataFilteredByPerception === true && !publicMap.placedTiles.some((tile) => tile.id === "tile-tavern-ambush-trigger"));
  const perception = computePlayerPerception(state, tavern, "player-a", { updateKnowledge: true });
  pass("player reveal centered on controlled PC", perception.entityId === "pc-lyra" && perception.visibleCellKeys.includes(cellKey(tavern, coordinateFromCell(tavern, placement.entity.x, placement.entity.y))));
  const viewport = currentViewport();
  viewport.zoom = 0.25;
  pass("player zoom-out clamp derives from perception", currentViewport().zoom >= minimumAllowedZoomForPlayer(tavern));

  const openField = createPerceptionScenarioMap("map-perception-open-field", { openField: true });
  state.maps[openField.id] = openField;
  state.currentMapId = openField.id;
  state.lastValidMapId = openField.id;
  emitSoundEvent(state, {
    soundEventId: "sound-open-field-bush",
    mapId: openField.id,
    sourcePosition: { x: 28, y: 2 },
    intensity: 0.8,
    category: "creature",
    description: "distant movement behind brush"
  }, { record: false });
  const openFieldPublic = playerVisibleSnapshot(state, openField);
  pass("open field heard without terrain reveal", openFieldPublic.perceivedSounds.length === 1 && !openFieldPublic.placedTiles.some((tile) => tile.id === "open-field-bush"));

  const doorway = createPerceptionScenarioMap("map-perception-doorway", { doorway: true });
  state.maps[doorway.id] = doorway;
  state.currentMapId = doorway.id;
  state.soundEvents = [];
  emitSoundEvent(state, {
    soundEventId: "sound-kitchen-door",
    mapId: doorway.id,
    sourcePosition: { x: 8, y: 3 },
    intensity: 0.9,
    category: "object impact",
    description: "heavy clambering"
  }, { record: false });
  const doorwayPerception = computePlayerPerception(state, doorway, "player-a", { updateKnowledge: true });
  const doorMarker = doorwayPerception.perceivedSounds[0]?.perceivedSound?.markerPosition;
  pass("kitchen sound redirects to doorway", doorMarker?.x === 5 && doorMarker?.y === 3, { marker: doorMarker });
  pass("wall blocks hidden room vision", !doorwayPerception.visibleCellKeys.includes(cellKey(doorway, { x: 8, y: 1 })));
  pass("open door permits line of sight", doorwayPerception.visibleCellKeys.includes(cellKey(doorway, { x: 8, y: 3 })));

  const closedDoor = createPerceptionScenarioMap("map-perception-closed-door", { closedDoor: true });
  state.maps[closedDoor.id] = closedDoor;
  state.currentMapId = closedDoor.id;
  state.soundEvents = [];
  const closedDoorPerception = computePlayerPerception(state, closedDoor, "player-a", { updateKnowledge: true });
  pass("closed door blocks vision", !closedDoorPerception.visibleCellKeys.includes(cellKey(closedDoor, { x: 8, y: 3 })));

  const sealed = createPerceptionScenarioMap("map-perception-sealed", { doorway: false });
  state.maps[sealed.id] = sealed;
  state.currentMapId = sealed.id;
  state.soundEvents = [];
  emitSoundEvent(state, {
    soundEventId: "sound-sealed-room",
    mapId: sealed.id,
    sourcePosition: { x: 8, y: 3 },
    intensity: 0.7,
    category: "machinery",
    description: "muffled grinding"
  }, { record: false });
  const sealedPerception = computePlayerPerception(state, sealed, "player-a", { updateKnowledge: true });
  pass("sealed room sound strongly attenuated or missed", sealedPerception.perceivedSounds.length === 0);

  state.role = "gm";
  state.currentMapId = doorway.id;
  state.editor.perceptionDebug.enabled = true;
  const gmDebug = computePlayerPerception(state, doorway, "player-a", { updateKnowledge: false });
  pass("gm debug overlay has perception data", gmDebug.visibleCellKeys.length > 0 && gmDebug.perceivedSounds.length >= 0);
  persistAndRender();
  return { checks, openFieldSounds: openFieldPublic.perceivedSounds.length, doorwayMarker: doorMarker };
}

function createPerceptionScenarioMap(id, options = {}) {
  const width = options.openField ? 32 : 10;
  const height = options.openField ? 5 : 7;
  const overrides = [];
  const placedTiles = [];
  if (options.openField) {
    placedTiles.push({
      schemaVersion: "shaelvien.tile.v2",
      id: "open-field-bush",
      definitionId: "bush",
      x: 28,
      y: 2,
      width: 1,
      height: 1,
      rotation: 0,
      visible: true,
      hiddenFromPlayers: false,
      blocked: false,
      childMapId: null,
      entryPointId: null,
      actions: [],
      triggers: [],
      encounterId: null,
      image: null,
      metadata: { label: "Distant Bush", gmNotes: "Beyond vision range." }
    });
  } else {
    for (let y = 0; y < height; y += 1) overrides.push({ x: 5, y, definitionId: "wall" });
    if (options.doorway) overrides.splice(overrides.findIndex((item) => item.x === 5 && item.y === 3), 1, { x: 5, y: 3, definitionId: "door" });
    if (options.closedDoor) {
      overrides.splice(overrides.findIndex((item) => item.x === 5 && item.y === 3), 1, { x: 5, y: 3, definitionId: "floor" });
      placedTiles.push({
        schemaVersion: "shaelvien.tile.v2",
        id: "closed-door-test",
        definitionId: "door",
        x: 5,
        y: 3,
        width: 1,
        height: 1,
        rotation: 0,
        visible: true,
        hiddenFromPlayers: false,
        blocked: true,
        childMapId: null,
        entryPointId: null,
        actions: [],
        triggers: [],
        encounterId: null,
        image: null,
        metadata: { label: "Closed Door", state: "closed", gmNotes: "test" }
      });
    }
  }
  const map = normalizeMapGeometry({
    schemaVersion: "shaelvien.map.v2",
    id,
    name: id,
    category: "interior",
    parentMapId: null,
    parentTileId: null,
    width,
    height,
    tileSize: 16,
    gridType: "square",
    gridSettings: { square: { columns: width, rows: height, cellWidth: 5, cellHeight: 5, unitSystem: "imperial", distanceUnit: "ft" } },
    terrain: { default: "floor", overrides },
    placedTiles,
    entities: [{ id: "pc-lyra", definitionId: "char-lyra", name: "Lyra", controller: "player", assignedPlayerId: "player-a", x: options.openField ? 0 : 2, y: options.openField ? 2 : 3, visible: true }],
    entryPoints: [],
    exitPoints: [],
    triggers: [],
    permissions: { gm: { canView: true, canEdit: true }, player: { canView: true } },
    atmosphere: { light: "test", sound: "test", gmNotes: "" },
    encounterReferences: []
  });
  return normalizeMapCollision(map, state);
}

function workspacePointForCell(mapId, coordinates) {
  if (!state.maps[mapId]) return null;
  state.currentMapId = mapId;
  const map = getCurrentMap(state);
  const screen = worldToScreen(cellCenter(map, coordinates));
  const rect = canvas.getBoundingClientRect();
  return {
    x: Math.round(rect.left + screen.x),
    y: Math.round(rect.top + screen.y),
    screen,
    rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
    viewport: deepClone(currentViewport())
  };
}

function setText(id, text) {
  if (elements[id]) elements[id].textContent = text;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
