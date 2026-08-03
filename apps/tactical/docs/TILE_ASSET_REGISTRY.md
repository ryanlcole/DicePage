# Tile Asset Registry

Tile images are registered by ID and referenced from map tiles. Large image blobs are not stored in map JSON.

Registry:

```text
data/assets/tile_asset_registry.json
```

Asset directory:

```text
assets/tiles/
```

## Record Shape

```json
{
  "assetId": "tile-asset-stone-floor-001",
  "name": "Stone Floor",
  "type": "tile_image",
  "sourcePath": "assets/tiles/stone_floor_001.png",
  "mimeType": "image/png",
  "widthPx": 64,
  "heightPx": 64,
  "contentHash": "sha256",
  "licenseStatus": "original",
  "author": "Shaelvien local placeholder",
  "tags": [],
  "createdAt": "2026-08-03T09:45:00-04:00",
  "updatedAt": "2026-08-03T09:45:00-04:00"
}
```

## Tile Reference

```json
{
  "imageAssetId": "tile-asset-stone-floor-001",
  "fitMode": "cover",
  "rotationDeg": 0,
  "flipX": false,
  "flipY": false,
  "opacity": 1,
  "tint": null
}
```

## Static Upload Boundary

The current frontend is static and has no safe upload endpoint. Browser-selected files are validated and hashed, but not written into the project asset directory by the client.

Required upload endpoint for a later server-backed pass:

- accept only PNG, JPEG, and WebP
- reject executables and malformed files
- compute SHA-256 server-side
- reuse an existing registry record on hash match
- write only under `assets/tiles/`
- never overwrite an existing asset with different bytes
- update `data/assets/tile_asset_registry.json` through the existing authoritative save boundary

This pass implements registered asset selection, assignment, removal, fallback rendering, square rendering, and hex clipping.
