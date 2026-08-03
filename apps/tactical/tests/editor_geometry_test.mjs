import fs from "node:fs/promises";
import { createGameState, deepClone } from "../js/state.js";
import { findTile, getCurrentMap, placeTile, playerVisibleSnapshot } from "../js/maps.js";
import {
  applyMapSettings,
  deriveMapSettings,
  paintTerrainAtCell,
  previewResizeImpact,
  selectCell,
  selectedTile,
  setSelectedTileImage,
  undoEditorEdit
} from "../js/editor.js";
import {
  cellCenter,
  cellId,
  cellPolygon,
  coordinateFromCell,
  normalizeMapGeometry,
  pointInPolygon,
  selectionForCell,
  worldToCell
} from "../js/grid.js";

const root = new URL("../", import.meta.url);

async function readJson(relativePath) {
  return JSON.parse(await fs.readFile(new URL(relativePath, root), "utf8"));
}

async function bundle() {
  const tileManifest = await readJson("data/tile_manifest.json");
  const tileAssetRegistry = await readJson("data/assets/tile_asset_registry.json");
  const maps = await Promise.all([
    "data/maps/world.json",
    "data/maps/city.json",
    "data/maps/block.json",
    "data/maps/tavern_exterior.json",
    "data/maps/tavern_main_floor.json",
    "data/maps/tavern_encounter.json"
  ].map(readJson));
  const encounters = [await readJson("data/encounters/tavern_ambush.json")];
  const characters = (await readJson("data/characters/players.json")).characters;
  const creatures = (await readJson("data/creatures/monsters.json")).creatures;
  return { tileManifest, tileAssetRegistry, maps, encounters, characters, creatures };
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const state = createGameState(await bundle());
const world = getCurrentMap(state);
assert(world.gridType === "square", "legacy world did not normalize to square");
assert(world.width === 16 && world.height === 10, "world dimensions changed");
assert(state.maps["map-tavern-main-floor"].gridType === "square", "tavern map was converted away from square");

const cityTile = findTile(world, "tile-world-city");
const cityCell = selectionForCell(world, coordinateFromCell(world, cityTile.x, cityTile.y));
selectCell(state, world, cityCell);
assert(state.selectedTileId === "tile-world-city", "direct square tile selection failed");
assert(state.selection.cellId === cellId(world, { x: cityTile.x, y: cityTile.y }), "selection cell id unstable");

const imageResult = setSelectedTileImage(state, "woodcut-symbol-city-001");
assert(imageResult.ok, "registered tile image rejected");
assert(selectedTile(state).image.imageAssetId === "woodcut-symbol-city-001", "tile image was not assigned");
assert(!setSelectedTileImage(state, "missing-asset").ok, "missing asset was accepted through validator");

const publicTavern = playerVisibleSnapshot(state, state.maps["map-tavern-main-floor"]);
assert(!publicTavern.placedTiles.some((tile) => tile.id === "tile-tavern-ambush-trigger"), "hidden trigger leaked to player snapshot");
assert(publicTavern.placedTiles.every((tile) => !tile.metadata.gmNotes), "GM notes leaked to player snapshot");

const beforeReplayCount = state.replays.length;
const paintResult = paintTerrainAtCell(state, world, cityCell, "road");
assert(paintResult.ok, "terrain paint failed");
const undoResult = undoEditorEdit(state);
assert(undoResult.ok, "editor undo failed");
assert(state.replays.length === beforeReplayCount, "edit undo mutated encounter replay records");

state.maps["map-editor-hex-pointy-node"] = normalizeMapGeometry({
  schemaVersion: "shaelvien.map.v2",
  id: "map-editor-hex-pointy-node",
  name: "Node Pointy Hex",
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
  atmosphere: { light: "test", sound: "none", gmNotes: "" },
  encounterReferences: []
});
state.currentMapId = "map-editor-hex-pointy-node";
const pointy = getCurrentMap(state);
const center = cellCenter(pointy, { q: 1, r: 1 });
const hit = worldToCell(pointy, center);
assert(hit.coordinates.q === 1 && hit.coordinates.r === 1, "pointy hex center hit failed");
assert(pointInPolygon(center, cellPolygon(pointy, { q: 1, r: 1 })), "pointy hex polygon rejected center");
placeTile(state, "floor", 1, 1);
selectedTile(state).image = { imageAssetId: "woodcut-object-table-001", fitMode: "cover", rotationDeg: 0, flipX: false, flipY: false, opacity: 1, tint: null };
assert(selectedTile(state).q === 1 && selectedTile(state).r === 1, "hex tile did not store axial aliases");

state.maps["map-editor-hex-flat-node"] = normalizeMapGeometry({
  ...deepClone(pointy),
  id: "map-editor-hex-flat-node",
  placedTiles: [],
  gridSettings: { hex: { orientation: "flat", radius: 5, radiusMeaning: "center_to_corner", unitSystem: "metric", distanceUnit: "m", layoutBounds: { columns: 4, rows: 4 } } }
});
state.currentMapId = "map-editor-hex-flat-node";
const flat = getCurrentMap(state);
const flatCenter = cellCenter(flat, { q: 2, r: 1 });
const flatHit = worldToCell(flat, flatCenter);
assert(flatHit.coordinates.q === 2 && flatHit.coordinates.r === 1, "flat hex center hit failed");
assert(flat.gridSettings.hex.radiusMeaning === "center_to_corner", "hex radius meaning was not retained");

const goodSquarePhysical = deriveMapSettings({ gridType: "square", sizeMode: "physical", width: 80, height: 50, cellWidth: 5, cellHeight: 5, unitSystem: "imperial", distanceUnit: "ft" });
assert(goodSquarePhysical.ok && goodSquarePhysical.columns === 16 && goodSquarePhysical.rows === 10, "square physical sizing failed");
const badSquarePhysical = deriveMapSettings({ gridType: "square", sizeMode: "physical", width: 81, height: 50, cellWidth: 5, cellHeight: 5, unitSystem: "imperial", distanceUnit: "ft" });
assert(!badSquarePhysical.ok, "non-whole square physical sizing was accepted");
const hexPhysical = deriveMapSettings({ gridType: "hex", sizeMode: "physical", mapWidth: 80, mapHeight: 50, hexRadius: 5, orientation: "pointy", unitSystem: "metric", distanceUnit: "m" });
assert(hexPhysical.ok && hexPhysical.actualWidth > 0 && hexPhysical.actualHeight > 0, "hex physical coverage failed");

state.currentMapId = "map-tavern-main-floor";
const shrinkImpact = previewResizeImpact(getCurrentMap(state), 4, 4);
assert(shrinkImpact.protectedContentCount > 0, "shrink impact did not detect protected content");
const shrink = applyMapSettings(state, {
  name: "Tavern Main Floor",
  gridType: "square",
  sizeMode: "tile-count",
  columns: 4,
  rows: 4,
  tileSize: 16,
  defaultTerrain: "floor",
  unitSystem: "imperial",
  distanceUnit: "ft",
  cellWidth: 5,
  cellHeight: 5,
  playerVisibilityDefault: "visible"
}, { confirmShrink: false });
assert(!shrink.ok, "protected shrink was allowed without confirmation");
assert(state.maps["map-tavern-main-floor"].width === 12 && state.maps["map-tavern-main-floor"].height === 8, "blocked shrink changed first preset map");

console.log(JSON.stringify({
  ok: true,
  initialSquareSelection: cellId(world, { x: cityTile.x, y: cityTile.y }),
  finalSelection: state.selection?.cellId || null,
  hex: { pointyHit: hit.coordinates, flatHit: flatHit.coordinates },
  imageAssets: Object.keys(state.tileAssets).length,
  shrinkProtectedContent: shrinkImpact.protectedContentCount,
  replayCount: state.replays.length
}, null, 2));
