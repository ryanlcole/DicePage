import { createGameState, serializableState } from "./state.js";
import { normalizeAssetRegistry } from "./assets.js";

export const STORAGE_KEY = "shaelvien.recursive.tabletop.v0";

const DATA_PATHS = Object.freeze({
  tileManifest: "data/tile_manifest.json",
  maps: [
    "data/maps/world.json",
    "data/maps/city.json",
    "data/maps/block.json",
    "data/maps/tavern_exterior.json",
    "data/maps/tavern_main_floor.json",
    "data/maps/tavern_encounter.json"
  ],
  encounters: ["data/encounters/tavern_ambush.json"],
  characters: ["data/characters/players.json"],
  creatures: ["data/creatures/monsters.json"],
  tileAssetRegistry: "data/assets/tile_asset_registry.json",
  collisionPresets: "data/collision_presets.json",
  perceptionProfiles: "data/perception_profiles.json",
  acousticMaterials: "data/acoustic_materials.json"
});

export async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

export async function loadGameBundle() {
  const [tileManifest, maps, encounters, characterGroups, creatureGroups, tileAssetRegistry, collisionPresets, perceptionProfiles, acousticMaterials] = await Promise.all([
    loadJson(DATA_PATHS.tileManifest),
    Promise.all(DATA_PATHS.maps.map(loadJson)),
    Promise.all(DATA_PATHS.encounters.map(loadJson)),
    Promise.all(DATA_PATHS.characters.map(loadJson)),
    Promise.all(DATA_PATHS.creatures.map(loadJson)),
    loadJson(DATA_PATHS.tileAssetRegistry).catch(() => ({ schemaVersion: "shaelvien.tile_asset_registry.v1", assets: [] })),
    loadJson(DATA_PATHS.collisionPresets).catch(() => ({ schemaVersion: "shaelvien.collision_presets.v1", presets: [] })),
    loadJson(DATA_PATHS.perceptionProfiles).catch(() => ({ schemaVersion: "shaelvien.perception_profiles.v1", profiles: [] })),
    loadJson(DATA_PATHS.acousticMaterials).catch(() => ({ schemaVersion: "shaelvien.acoustic_materials.v1", materials: [] }))
  ]);
  return {
    tileManifest,
    maps,
    encounters,
    characters: characterGroups.flatMap((group) => group.characters),
    creatures: creatureGroups.flatMap((group) => group.creatures),
    tileAssetRegistry: normalizeAssetRegistry(tileAssetRegistry),
    collisionPresets,
    perceptionProfiles,
    acousticMaterials
  };
}

export function loadPersistedState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

export function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(serializableState(state)));
}

export function clearSavedState() {
  localStorage.removeItem(STORAGE_KEY);
}

export async function createInitialState() {
  const bundle = await loadGameBundle();
  return createGameState(bundle, loadPersistedState());
}
