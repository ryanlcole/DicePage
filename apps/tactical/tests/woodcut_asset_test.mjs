import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

function hash(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function pngSize(bytes) {
  assert(bytes.subarray(0, 8).toString("hex") === "89504e470d0a1a0a", "not a PNG");
  return {
    width: bytes.readUInt32BE(16),
    height: bytes.readUInt32BE(20)
  };
}

const registry = await readJson("data/assets/tile_asset_registry.json");
const manifest = await readJson("data/tile_manifest.json");
const css = await readFile("styles.css", "utf8");
const woodcutAssets = registry.assets.filter((asset) => String(asset.assetId).startsWith("woodcut-"));
const tileImages = woodcutAssets.filter((asset) => asset.type === "tile_image");
const autotiles = woodcutAssets.filter((asset) => asset.type === "autotile_image");
const atlas = registry.assets.find((asset) => asset.assetId === "woodcut-atlas-001");

assert(registry.schemaVersion === "shaelvien.tile_asset_registry.v2", "registry schema was not upgraded");
assert(registry.defaultVisualLanguage === "shaelvien_woodcut_v1", "woodcut visual language is not default");
assert(manifest.schemaVersion === "shaelvien.tile_manifest.v2", "manifest schema was not upgraded");
assert(manifest.tileSize === 32, "authoritative tile size is not 32");
assert(manifest.visualLanguage === "shaelvien_woodcut_v1", "manifest does not use woodcut visual language");
assert(manifest.autotileVisualOnly === true, "autotiling must be visual-only");
assert(woodcutAssets.length >= 80, "expected at least 80 woodcut assets");
assert(tileImages.length >= 45, "expected starter terrain and object image set");
assert(autotiles.length === 32, "expected 8 terrain autotile groups with 4 edge variants each");
assert(manifest.autotileSets.length === 8, "expected 8 visual autotile sets");
assert(atlas && atlas.type === "tile_atlas", "woodcut atlas missing");
assert(atlas.tileSizePx === 32 && atlas.frameCount === 82, "atlas frame metadata is incorrect");
assert(woodcutAssets.every((asset) => asset.licenseStatus === "original"), "non-original license status found");
assert(woodcutAssets.every((asset) => !/commercial|ripped|copied/i.test([asset.name, asset.author, ...(asset.tags || [])].join(" "))), "commercial/copy marker found in woodcut metadata");
assert(manifest.definitions.filter((definition) => definition.image?.imageAssetId?.startsWith("woodcut-")).length >= 45, "manifest definitions do not default to woodcut images");
assert(css.includes("image-rendering: pixelated"), "nearest-neighbor CSS rendering is not preserved");

const atlasBytes = await readFile(atlas.sourcePath);
const atlasHash = hash(atlasBytes);
const atlasSize = pngSize(atlasBytes);
assert(atlasHash === atlas.contentHash, "atlas content hash mismatch");
assert(atlasSize.width === atlas.widthPx && atlasSize.height === atlas.heightPx, "atlas dimensions do not match registry");

for (const asset of woodcutAssets.filter((item) => item.type !== "tile_atlas")) {
  const bytes = await readFile(asset.sourcePath);
  const size = pngSize(bytes);
  assert(size.width === 32 && size.height === 32, `${asset.assetId} is not 32x32`);
  assert(hash(bytes) === asset.contentHash, `${asset.assetId} content hash mismatch`);
}

console.log(JSON.stringify({
  ok: true,
  visualLanguage: registry.defaultVisualLanguage,
  manifestTileSize: manifest.tileSize,
  woodcutAssets: woodcutAssets.length,
  tileImages: tileImages.length,
  autotiles: autotiles.length,
  atlas: {
    assetId: atlas.assetId,
    width: atlasSize.width,
    height: atlasSize.height,
    hash: atlasHash
  },
  nearestNeighbor: true,
  originalMetadataOnly: true
}, null, 2));
