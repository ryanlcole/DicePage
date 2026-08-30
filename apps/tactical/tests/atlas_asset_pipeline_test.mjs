import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { normalizeAtlasRegistry, normalizeMapAtlasInstances, sortedAtlasInstances } from "../js/atlas.js";

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

const manifest = await readJson("data/atlas/atlas_source_manifest.json");
const registry = normalizeAtlasRegistry(await readJson("data/atlas/atlas_asset_registry.json"));
const demoMap = normalizeMapAtlasInstances(await readJson("data/maps/atlas_demo.json"));
const childMap = await readJson("data/maps/atlas_demo_waterfall_interior.json");
const streamMap = normalizeMapAtlasInstances(await readJson("data/maps/atlas_region_stream_demo.json"));
const streamChildMap = await readJson("data/maps/atlas_region_stream_source.json");
const streamDetections = await readJson("data/atlas/detections/streams_candidates_bounded_320.json");

assert(manifest.schemaVersion === "shaelvien.atlas_source_manifest.v1", "source manifest schema mismatch");
assert(registry.schemaVersion === "shaelvien.atlas_asset_registry.v1", "atlas registry schema mismatch");
assert(registry.sourceAuthority === "google_drive", "Google Drive must remain artwork authority");
assert(registry.syncPolicy?.localRuntimeRequiresLiveDrive === false, "runtime must not require live Drive");
assert(registry.sources.length === 3, "expected three source records after first production collection");
assert(registry.assets.length === 11, "expected eleven derived atlas assets after first production collection");

const sourceIds = new Set(registry.sources.map((source) => source.sourceId));
const assetIds = new Set();
for (const source of registry.sources) {
  assert(source.driveFileId && source.driveParentId && source.drivePath, `${source.sourceId} missing Drive provenance`);
  assert(source.chatgptShareId && source.chatgptGenerationId, `${source.sourceId} missing ChatGPT provenance`);
  const bytes = await readFile(source.localSourcePath);
  const size = pngSize(bytes);
  assert(size.width === source.widthPx && size.height === source.heightPx, `${source.sourceId} source dimensions changed`);
  assert(hash(bytes) === source.contentHash, `${source.sourceId} source hash changed`);
}

for (const asset of registry.assets) {
  assert(!assetIds.has(asset.assetId), `${asset.assetId} duplicate asset id`);
  assetIds.add(asset.assetId);
  assert(sourceIds.has(asset.sourceId), `${asset.assetId} source id missing`);
  assert(asset.createdFrom?.driveFileId && asset.createdFrom?.chatgptShareId, `${asset.assetId} missing createdFrom provenance`);
  const bytes = await readFile(asset.derivedPath);
  const thumb = await readFile(asset.thumbnailPath);
  const size = pngSize(bytes);
  assert(size.width === asset.nativeWidth && size.height === asset.nativeHeight, `${asset.assetId} derived dimensions changed`);
  assert(hash(bytes) === asset.contentHash, `${asset.assetId} derived hash mismatch`);
  assert(hash(thumb) === asset.thumbnailHash, `${asset.assetId} thumbnail hash mismatch`);
  if (asset.transparentBackground) {
    assert(asset.shapeModel === "irregular_alpha_mask", `${asset.assetId} should use alpha-mask shape semantics`);
    assert(asset.rectIsStorageEnvelope === true, `${asset.assetId} source rect should be marked as a storage envelope`);
    assert(asset.alphaMaskSource === "derived_png_alpha", `${asset.assetId} alpha mask source mismatch`);
  }
}

const waterfallRefs = demoMap.atlasInstances.filter((instance) => instance.assetId === "atlas.wonder.waterfall.001");
assert(waterfallRefs.length === 2, "demo map should reuse one waterfall asset through multiple instances");
assert(new Set(waterfallRefs.map((instance) => instance.assetId)).size === 1, "waterfall instances should point to one asset id");
assert(demoMap.atlasInstances.some((instance) => instance.childMapId === "map-atlas-demo-waterfall-interior"), "atlas instance child map link missing");
assert(childMap.parentMapId === "map-atlas-demo" && childMap.parentAtlasInstanceId === "atlas-demo-waterfall-001", "child map reverse atlas relationship missing");
assert(demoMap.atlasInstances.some((instance) => instance.rotationDeg === 90), "rotation must survive JSON load");

const streamAssets = registry.assets.filter((asset) => asset.collection === "streams_and_small_watercourses");
const streamSource = registry.sources.find((source) => source.sourceId === "drive.region_map.water.streams_small_watercourses.001");
const repeatedStreamRefs = streamMap.atlasInstances.filter((instance) => instance.assetId === "atlas.region.water.stream.straight.001");
assert(streamSource, "stream source record missing");
assert(streamAssets.length === 5, "first production stream collection should contain five accepted assets");
assert(streamAssets.every((asset) => asset.layer === "water_system"), "stream assets must remain water-system layer assets");
assert(streamAssets.every((asset) => asset.connectors.length >= 1), "stream assets must have connector metadata");
assert(repeatedStreamRefs.length === 2, "stream demo should reuse one registered stream asset through multiple instances");
assert(streamMap.atlasInstances.some((instance) => instance.rotationDeg === 270), "stream demo rotation must survive JSON load");
assert(streamMap.atlasInstances.some((instance) => instance.childMapId === "map-atlas-region-stream-source"), "stream demo child map link missing");
assert(streamChildMap.parentMapId === "map-atlas-region-stream-demo" && streamChildMap.parentAtlasInstanceId === "atlas-region-stream-pool-001", "stream child map reverse relationship missing");
assert(streamDetections.schemaVersion === "shaelvien.atlas_detection_candidates.v1", "distance detector output schema mismatch");
assert(streamDetections.candidateCount >= 40, "distance detector did not produce reviewable candidates");
assert(streamDetections.candidates.every((candidate) => candidate.detection.reviewStatus === "candidate_unapproved"), "detector candidates must remain unapproved until reviewed");
assert(streamDetections.candidates.every((candidate, index) => candidate.scanOrder === index + 1), "detector candidates must preserve left-to-right top-down scan order");
assert(streamDetections.candidates.every((candidate) => candidate.shapeModel === "irregular_alpha_mask"), "detector candidates must use irregular alpha-mask shape semantics");
assert(streamDetections.candidates.every((candidate) => candidate.rectIsStorageEnvelope === true), "detector source rectangles must be storage envelopes");

const ordered = sortedAtlasInstances(demoMap, registry);
const orderedKeys = ordered.map((row) => `${row.asset?.layerOrder ?? "missing"}:${row.instance.z}:${row.instance.instanceId}`);
assert([...orderedKeys].sort().join("|") === orderedKeys.join("|"), "layer ordering is not deterministic");

const missingMap = normalizeMapAtlasInstances({
  atlasInstances: [{
    instanceId: "atlas-missing-test",
    assetId: "atlas.unknown.asset",
    x: 1,
    y: 1,
    width: 10,
    height: 10,
    rotationDeg: 0,
    visible: true
  }]
});
const missingRows = sortedAtlasInstances(missingMap, registry);
assert(missingRows.length === 1 && missingRows[0].asset === null, "unknown asset id should remain renderable as fallback, not substituted");

const stableBefore = JSON.stringify(demoMap);
const stableAfter = JSON.stringify(normalizeMapAtlasInstances(JSON.parse(stableBefore)));
assert(stableBefore === stableAfter, "map atlas save/load normalization is not deterministic");

console.log(JSON.stringify({
  ok: true,
  sources: registry.sources.length,
  assets: registry.assets.length,
  collections: [...new Set(registry.assets.map((asset) => asset.collection))].sort(),
  reusedWaterfallInstances: waterfallRefs.length,
  reusedStreamInstances: repeatedStreamRefs.length,
  streamCollectionAssets: streamAssets.length,
  streamDetectionCandidates: streamDetections.candidateCount,
  childMap: childMap.id,
  streamChildMap: streamChildMap.id,
  sourceHashes: Object.fromEntries(registry.sources.map((source) => [source.sourceId, source.contentHash])),
  deterministicLayerOrder: ordered.map((row) => row.instance.instanceId),
  streamLayerOrder: sortedAtlasInstances(streamMap, registry).map((row) => row.instance.instanceId)
}, null, 2));
