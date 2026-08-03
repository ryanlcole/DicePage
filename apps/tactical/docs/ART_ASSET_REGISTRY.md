# Art Asset Registry

Milestone: `SHAELVIEN-WOODCUT-TILESET-1`

The authoritative browser asset registry is:

`data/assets/tile_asset_registry.json`

The current default visual language is:

`shaelvien_woodcut_v1`

## Asset Locations

- Generated 32x32 frames: `assets/tiles/woodcut/`
- Sprite atlas/contact sheet: `assets/tiles/woodcut_atlas_001.png`
- Manifest defaults: `data/tile_manifest.json`

## Registry Rules

Every production art record must include:

- stable `assetId`
- `sourcePath`
- `mimeType`
- `widthPx`
- `heightPx`
- `contentHash`
- `licenseStatus`
- `author`
- `tags`
- timestamps

No passwords, tokens, personal information, or license keys belong in the registry.

## Originality Policy

Woodcut assets in this milestone were generated locally by deterministic drawing code in `tools/generate_woodcut_tiles.py`. They do not reference, download, copy, or trace commercial assets.

Imported custom images remain supported as optional GM content, but Shaelvien woodcut assets are the default mapping experience.
