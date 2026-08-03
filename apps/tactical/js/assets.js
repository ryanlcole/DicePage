export const TILE_IMAGE_FORMATS = Object.freeze(["image/png", "image/jpeg", "image/webp"]);

export function defaultTileImageRef(assetId) {
  return {
    imageAssetId: assetId,
    fitMode: "cover",
    rotationDeg: 0,
    flipX: false,
    flipY: false,
    opacity: 1,
    tint: null
  };
}

export function normalizeAssetRegistry(registry) {
  const safe = registry && typeof registry === "object" ? registry : {};
  return {
    schemaVersion: safe.schemaVersion || "shaelvien.tile_asset_registry.v1",
    defaultVisualLanguage: safe.defaultVisualLanguage || "",
    uploadEndpointStatus: safe.uploadEndpointStatus || "",
    uploadPolicy: safe.uploadPolicy || null,
    woodcutPolicy: safe.woodcutPolicy || null,
    assets: Array.isArray(safe.assets) ? safe.assets.map(normalizeAsset).filter(Boolean) : []
  };
}

export function normalizeAsset(asset) {
  if (!asset || !asset.assetId || !asset.sourcePath) return null;
  const allowedType = ["tile_image", "autotile_image", "tile_atlas"].includes(asset.type) ? asset.type : "tile_image";
  return {
    assetId: String(asset.assetId),
    name: String(asset.name || asset.assetId),
    type: allowedType,
    sourcePath: String(asset.sourcePath),
    mimeType: TILE_IMAGE_FORMATS.includes(asset.mimeType) ? asset.mimeType : "image/png",
    widthPx: Number.isInteger(asset.widthPx) ? asset.widthPx : null,
    heightPx: Number.isInteger(asset.heightPx) ? asset.heightPx : null,
    contentHash: String(asset.contentHash || ""),
    licenseStatus: asset.licenseStatus || "unknown",
    author: asset.author || "",
    tags: Array.isArray(asset.tags) ? asset.tags.map(String) : [],
    createdAt: asset.createdAt || "",
    updatedAt: asset.updatedAt || "",
    atlasId: asset.atlasId || "",
    atlasSourcePath: asset.atlasSourcePath || "",
    sourceRect: asset.sourceRect && typeof asset.sourceRect === "object"
      ? {
        x: Number(asset.sourceRect.x) || 0,
        y: Number(asset.sourceRect.y) || 0,
        width: Number(asset.sourceRect.width) || asset.widthPx || null,
        height: Number(asset.sourceRect.height) || asset.heightPx || null
      }
      : null,
    tileSizePx: Number.isInteger(asset.tileSizePx) ? asset.tileSizePx : null,
    columns: Number.isInteger(asset.columns) ? asset.columns : null,
    frameCount: Number.isInteger(asset.frameCount) ? asset.frameCount : null
  };
}

export function assetsById(registry) {
  return Object.fromEntries(normalizeAssetRegistry(registry).assets.map((asset) => [asset.assetId, asset]));
}

export function tileAssets(registry) {
  return normalizeAssetRegistry(registry).assets.filter((asset) => asset.type === "tile_image");
}

export function atlasAssets(registry) {
  return normalizeAssetRegistry(registry).assets.filter((asset) => asset.type === "tile_atlas");
}

export function imageRefIsValid(ref, registry) {
  if (!ref?.imageAssetId) return false;
  return Boolean(assetsById(registry)[ref.imageAssetId]);
}

export async function hashBrowserFile(file) {
  if (!file || !TILE_IMAGE_FORMATS.includes(file.type)) {
    return { ok: false, message: "Only PNG, JPEG, and WebP tile images are accepted." };
  }
  const bytes = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest("SHA-256", bytes);
  const hash = Array.from(new Uint8Array(hashBuffer)).map((byte) => byte.toString(16).padStart(2, "0")).join("");
  return {
    ok: true,
    name: file.name,
    mimeType: file.type,
    size: file.size,
    contentHash: hash
  };
}

export function duplicateAssetByHash(registry, contentHash) {
  return tileAssets(registry).find((asset) => asset.contentHash && asset.contentHash.toLowerCase() === String(contentHash).toLowerCase()) || null;
}
