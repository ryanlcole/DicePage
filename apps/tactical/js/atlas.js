import { cellCenter } from "./grid.js";

function deepClone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function recordAtlasEvent(state, type, payload = {}) {
  const event = {
    sequence: state.nextEventSeq++,
    type,
    scene: state.scene,
    mapId: state.currentMapId,
    encounterId: state.activeEncounter?.encounterId || null,
    round: state.activeEncounter?.round || null,
    rejected: false,
    stateChanging: true,
    payload: deepClone(payload)
  };
  state.eventLog.push(event);
  return event;
}

export const ATLAS_LAYER_ORDER = Object.freeze({
  base: 0,
  terrain: 1,
  terrain_transition: 2,
  water_system: 3,
  natural_landmark: 4,
  road: 5,
  civilization_landmark: 6,
  structure: 7,
  object: 8,
  gameplay_entity: 9,
  gm_overlay: 10
});

export function normalizeAtlasRegistry(registry) {
  const safe = registry && typeof registry === "object" ? registry : {};
  const layerOrder = safe.layerOrder && typeof safe.layerOrder === "object" ? safe.layerOrder : ATLAS_LAYER_ORDER;
  return {
    schemaVersion: safe.schemaVersion || "shaelvien.atlas_asset_registry.v0",
    generatedAt: safe.generatedAt || "",
    sourceAuthority: safe.sourceAuthority || "unknown",
    syncPolicy: safe.syncPolicy || null,
    layerOrder,
    publicRuntimeRegistry: safe.publicRuntimeRegistry === true,
    sourceCacheIncluded: safe.sourceCacheIncluded === true,
    sources: Array.isArray(safe.sources) ? safe.sources.map(normalizeAtlasSource).filter(Boolean) : [],
    assets: Array.isArray(safe.assets) ? safe.assets.map((asset) => normalizeAtlasAsset(asset, layerOrder)).filter(Boolean) : []
  };
}

export function normalizeAtlasSource(source) {
  if (!source?.sourceId || !source.localSourcePath) return null;
  return {
    ...deepClone(source),
    sourceId: String(source.sourceId),
    localSourcePath: String(source.localSourcePath),
    contentHash: String(source.contentHash || "")
  };
}

export function normalizeAtlasAsset(asset, layerOrder = ATLAS_LAYER_ORDER) {
  if (!asset?.assetId || !asset.derivedPath) return null;
  const layer = asset.layer || "object";
  const normalized = {
    assetId: String(asset.assetId),
    name: String(asset.name || asset.assetId),
    category: String(asset.category || "unknown"),
    collection: String(asset.collection || "uncategorized"),
    sourceId: String(asset.sourceId || ""),
    sourceRect: asset.sourceRect && typeof asset.sourceRect === "object"
      ? {
        x: Number(asset.sourceRect.x) || 0,
        y: Number(asset.sourceRect.y) || 0,
        width: Number(asset.sourceRect.width) || 0,
        height: Number(asset.sourceRect.height) || 0
      }
      : null,
    derivedPath: String(asset.derivedPath),
    thumbnailPath: String(asset.thumbnailPath || asset.derivedPath),
    mimeType: asset.mimeType || "image/png",
    nativeWidth: Number(asset.nativeWidth) || 1,
    nativeHeight: Number(asset.nativeHeight) || 1,
    contentHash: String(asset.contentHash || ""),
    thumbnailHash: String(asset.thumbnailHash || ""),
    anchor: asset.anchor || "center",
    allowedRotations: Array.isArray(asset.allowedRotations) ? asset.allowedRotations.map(Number) : [0],
    layer,
    layerOrder: Number.isFinite(Number(asset.layerOrder)) ? Number(asset.layerOrder) : Number(layerOrder[layer] ?? 50),
    tags: Array.isArray(asset.tags) ? asset.tags.map(String) : [],
    connectors: Array.isArray(asset.connectors) ? deepClone(asset.connectors) : [],
    transparentBackground: asset.transparentBackground === true,
    shapeModel: String(asset.shapeModel || (asset.transparentBackground === true ? "irregular_alpha_mask" : "rectangular_image")),
    rectIsStorageEnvelope: asset.rectIsStorageEnvelope === true,
    alphaMaskSource: String(asset.alphaMaskSource || (asset.transparentBackground === true ? "derived_png_alpha" : "none")),
    createdFrom: asset.createdFrom && typeof asset.createdFrom === "object" ? deepClone(asset.createdFrom) : {},
    defaultPlacement: asset.defaultPlacement && typeof asset.defaultPlacement === "object" ? deepClone(asset.defaultPlacement) : {},
    version: Number(asset.version) || 1,
    enabled: asset.enabled !== false
  };
  if (Object.prototype.hasOwnProperty.call(asset, "sourceImage")) {
    normalized.sourceImage = String(asset.sourceImage || "");
  }
  return normalized;
}

export function atlasAssetsById(registry) {
  return Object.fromEntries(normalizeAtlasRegistry(registry).assets.map((asset) => [asset.assetId, asset]));
}

export function atlasCollections(registry) {
  const collections = new Map();
  normalizeAtlasRegistry(registry).assets.filter((asset) => asset.enabled).forEach((asset) => {
    if (!collections.has(asset.collection)) {
      collections.set(asset.collection, {
        id: asset.collection,
        category: asset.category,
        name: titleCase(asset.collection),
        count: 0
      });
    }
    collections.get(asset.collection).count += 1;
  });
  return [...collections.values()].sort((a, b) => `${a.category}:${a.name}`.localeCompare(`${b.category}:${b.name}`));
}

export function atlasRenderableAssets(registry) {
  return normalizeAtlasRegistry(registry).assets.filter((asset) => asset.enabled);
}

export function normalizeMapAtlasInstances(map) {
  if (!map || typeof map !== "object") return map;
  map.atlasInstances = Array.isArray(map.atlasInstances) ? map.atlasInstances.map(normalizeAtlasInstance).filter(Boolean) : [];
  return map;
}

export function normalizeAtlasInstance(instance) {
  if (!instance?.instanceId || !instance.assetId) return null;
  return {
    instanceId: String(instance.instanceId),
    assetId: String(instance.assetId),
    x: Number(instance.x) || 0,
    y: Number(instance.y) || 0,
    width: Number(instance.width) || 1,
    height: Number(instance.height) || 1,
    rotationDeg: Number(instance.rotationDeg) || 0,
    scale: Number(instance.scale) || 1,
    layer: instance.layer || null,
    z: Number.isFinite(Number(instance.z)) ? Number(instance.z) : 0,
    visible: instance.visible !== false,
    hiddenFromPlayers: instance.hiddenFromPlayers === true,
    childMapId: instance.childMapId || null,
    interactionId: instance.interactionId || null,
    triggerId: instance.triggerId || null,
    encounterId: instance.encounterId || null,
    metadata: instance.metadata && typeof instance.metadata === "object" ? deepClone(instance.metadata) : {}
  };
}

export function sortedAtlasInstances(map, registry) {
  const assets = atlasAssetsById(registry);
  return (map.atlasInstances || [])
    .map((instance) => ({ instance, asset: assets[instance.assetId] || null }))
    .filter((row) => row.instance.visible !== false)
    .sort((a, b) => {
      const layerA = layerOrder(a.instance, a.asset);
      const layerB = layerOrder(b.instance, b.asset);
      if (layerA !== layerB) return layerA - layerB;
      if (a.instance.z !== b.instance.z) return a.instance.z - b.instance.z;
      return a.instance.instanceId.localeCompare(b.instance.instanceId);
    });
}

export function createAtlasInstance(state, map, assetId, coordinates = null) {
  const asset = atlasAssetsById(state.atlasRegistry)[assetId];
  if (!asset) return { ok: false, message: "Atlas asset is not registered." };
  normalizeMapAtlasInstances(map);
  const point = coordinates ? cellCenter(map, coordinates) : { x: (map.width * map.tileSize) / 2, y: (map.height * map.tileSize) / 2 };
  const placement = asset.defaultPlacement || {};
  const width = Math.max(1, Number(placement.widthCells || 2) * map.tileSize);
  const height = Math.max(1, Number(placement.heightCells || Math.max(1, width / Math.max(1, asset.nativeWidth / asset.nativeHeight))) * map.tileSize);
  const instance = normalizeAtlasInstance({
    instanceId: `atlas-instance-${asset.assetId.replaceAll(".", "-")}-${state.nextEventSeq}`,
    assetId,
    x: point.x,
    y: point.y,
    width,
    height,
    rotationDeg: 0,
    scale: 1,
    layer: asset.layer,
    z: map.atlasInstances.length,
    visible: true,
    hiddenFromPlayers: false,
    childMapId: null,
    metadata: {
      label: asset.name,
      sourceId: asset.sourceId,
      collection: asset.collection
    }
  });
  map.atlasInstances.push(instance);
  state.selectedAtlasInstanceId = instance.instanceId;
  recordAtlasEvent(state, "atlas_instance_placed", { mapId: map.id, instance: deepClone(instance) });
  return { ok: true, instance };
}

export function findAtlasInstance(map, instanceId) {
  normalizeMapAtlasInstances(map);
  return map.atlasInstances.find((instance) => instance.instanceId === instanceId) || null;
}

export function moveSelectedAtlasInstance(state, map, dx, dy) {
  const instance = findAtlasInstance(map, state.selectedAtlasInstanceId);
  if (!instance) return { ok: false, message: "No atlas instance selected." };
  const from = { x: instance.x, y: instance.y };
  instance.x += dx;
  instance.y += dy;
  recordAtlasEvent(state, "atlas_instance_changed", { mapId: map.id, instanceId: instance.instanceId, from, to: { x: instance.x, y: instance.y } });
  return { ok: true, instance };
}

export function rotateSelectedAtlasInstance(state, map, deltaDeg) {
  const instance = findAtlasInstance(map, state.selectedAtlasInstanceId);
  if (!instance) return { ok: false, message: "No atlas instance selected." };
  const asset = atlasAssetsById(state.atlasRegistry)[instance.assetId];
  const allowed = asset?.allowedRotations?.length ? asset.allowedRotations : [0, 90, 180, 270];
  const normalized = ((instance.rotationDeg + deltaDeg) % 360 + 360) % 360;
  instance.rotationDeg = nearestRotation(normalized, allowed);
  recordAtlasEvent(state, "atlas_instance_changed", { mapId: map.id, instanceId: instance.instanceId, rotationDeg: instance.rotationDeg });
  return { ok: true, instance };
}

export function setAtlasInstanceChildMap(state, map, childMapId) {
  const instance = findAtlasInstance(map, state.selectedAtlasInstanceId);
  if (!instance) return { ok: false, message: "No atlas instance selected." };
  instance.childMapId = childMapId || null;
  recordAtlasEvent(state, "atlas_instance_changed", { mapId: map.id, instanceId: instance.instanceId, childMapId: instance.childMapId });
  return { ok: true, instance };
}

export function removeSelectedAtlasInstance(state, map) {
  normalizeMapAtlasInstances(map);
  const index = map.atlasInstances.findIndex((instance) => instance.instanceId === state.selectedAtlasInstanceId);
  if (index < 0) return { ok: false, message: "No atlas instance selected." };
  const [removed] = map.atlasInstances.splice(index, 1);
  state.selectedAtlasInstanceId = null;
  recordAtlasEvent(state, "atlas_instance_changed", { mapId: map.id, instanceId: removed.instanceId, removed: true });
  return { ok: true, removed };
}

export function hitTestAtlasInstance(map, registry, worldPoint, role = "gm") {
  const rows = sortedAtlasInstances(map, registry).filter((row) => role !== "player" || row.instance.hiddenFromPlayers !== true);
  for (let index = rows.length - 1; index >= 0; index -= 1) {
    const { instance } = rows[index];
    if (pointInRotatedRect(worldPoint, instance)) return instance;
  }
  return null;
}

function pointInRotatedRect(point, instance) {
  const angle = -((instance.rotationDeg || 0) * Math.PI) / 180;
  const dx = point.x - instance.x;
  const dy = point.y - instance.y;
  const localX = dx * Math.cos(angle) - dy * Math.sin(angle);
  const localY = dx * Math.sin(angle) + dy * Math.cos(angle);
  return Math.abs(localX) <= instance.width / 2 && Math.abs(localY) <= instance.height / 2;
}

function layerOrder(instance, asset) {
  if (Number.isFinite(Number(ATLAS_LAYER_ORDER[instance.layer]))) return ATLAS_LAYER_ORDER[instance.layer];
  return asset ? asset.layerOrder : 50;
}

function nearestRotation(value, allowed) {
  return allowed.reduce((best, item) => {
    const current = angularDistance(value, item);
    return current < angularDistance(value, best) ? item : best;
  }, allowed[0]);
}

function angularDistance(a, b) {
  const diff = Math.abs((((a - b) % 360) + 540) % 360 - 180);
  return diff;
}

function titleCase(value) {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
