# Shaelvien Atlas Asset Pipeline

Status: first vertical slice.

Google Drive is the authoritative human-managed source library for approved Atlas artwork. The tactical app keeps a local runtime cache so maps do not require a live Drive or ChatGPT connection during play.

Pipeline:

1. Google Drive source record
2. Local immutable source cache
3. Derived runtime PNGs
4. Thumbnails
5. Atlas asset registry
6. Map `atlasInstances`
7. Canvas renderer

The current slice uses:

- `Shaelvien/07_Media/Tiles/World_Map/Terrain/Plains`
- `Shaelvien/07_Media/Tiles/World_Map/Landmarks/Wonders/Hydrological`
- `Shaelvien/07_Media/Tiles/Region_Map/Water/Streams_and_Small_Watercourses`

The Drive files currently copied as `text/html` ChatGPT shared-image pages. The ingest records the Drive file IDs and ChatGPT share metadata, then uses the recovered PNG as the local source cache. The original Drive files are not modified.

## Files

- Source manifest: `data/atlas/atlas_source_manifest.json`
- Runtime registry: `data/atlas/atlas_asset_registry.json`
- Source cache: `assets/atlas/source/`
- Derived assets: `assets/atlas/derived/`
- Thumbnails: `assets/atlas/thumbnails/`
- Ingest tool: `tools/atlas_ingest.py`

## Non-Destructive Rules

- Never edit approved Drive artwork in place.
- Never upload derived images over source images.
- Preserve previous local source until a new source validates.
- Regenerate derived files only from a verified source hash.
- Treat filenames as labels, not identity.

Identity comes from:

- `driveFileId`
- `driveParentId`
- `drivePath`
- Drive modified time
- ChatGPT share and generation IDs when the Drive file is a ChatGPT wrapper
- Local source content hash

## Asset Records

Each reusable asset records:

- `assetId`
- `category`
- `collection`
- `sourceId`
- `sourceRect`
- `shapeModel`
- `rectIsStorageEnvelope`
- `alphaMaskSource`
- `derivedPath`
- `thumbnailPath`
- `layer`
- `allowedRotations`
- `connectors`
- `createdFrom`

Artwork owns appearance. Data owns semantic properties.

## Irregular Asset Shapes

Atlas artwork is not constrained to square or hex cells. Square and hex geometry are map tools for recursion, movement, range, and token placement. They are not art-crop rules.

For transparent Atlas assets, `sourceRect` is only the storage envelope used to crop a derived PNG from the approved source sheet. The rest of that rectangle may be transparent. The actual visible and selectable shape is the derived PNG alpha mask:

```json
{
  "shapeModel": "irregular_alpha_mask",
  "rectIsStorageEnvelope": true,
  "alphaMaskSource": "derived_png_alpha"
}
```

The source-sheet detector scans candidates in stable top-down, left-to-right order. Candidate rectangles remain unapproved review envelopes until a human accepts or corrects them. Manual correction belongs in manifest data, not in destructive source-image edits.

Layering resolves overlap between irregular pieces. The renderer sorts by deterministic Atlas layer and z-order before drawing and hit testing.

## Map Instances

Maps store reusable instance data:

```json
{
  "instanceId": "atlas-demo-waterfall-001",
  "assetId": "atlas.wonder.waterfall.001",
  "x": 276,
  "y": 148,
  "rotationDeg": 90,
  "scale": 1,
  "layer": "natural_landmark",
  "childMapId": "map-atlas-demo-waterfall-interior"
}
```

Multiple instances may reference the same asset. The renderer composites them in deterministic layer order.

## Current Limits

The first production stream collection uses detection to create review candidates, then manual manifest entries for accepted assets. Automatic irregular-boundary detection is not authoritative yet. Transparency extraction is conservative and may require manual correction for production-quality cutouts.
