# Art Asset Registry

Milestone: `SHAELVIEN-WOODCUT-TILESET-1`

The authoritative browser asset registry is:

`data/assets/tile_asset_registry.json`

The production Atlas registry is:

`data/atlas/atlas_asset_registry.json`

The current default visual language is:

`shaelvien_woodcut_v1`

## Asset Locations

- Generated 32x32 frames: `assets/tiles/woodcut/`
- Sprite atlas/contact sheet: `assets/tiles/woodcut_atlas_001.png`
- Manifest defaults: `data/tile_manifest.json`
- Atlas source cache: `assets/atlas/source/`
- Atlas derived runtime assets: `assets/atlas/derived/`
- Atlas thumbnails: `assets/atlas/thumbnails/`

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

## Atlas Source Authority

Approved Atlas artwork is managed in Google Drive. The local source cache is a verified runtime copy, not the human authority.

Atlas source records preserve:

- Drive file ID
- Drive parent ID
- Drive path
- Drive modified time
- ChatGPT share/generation IDs when the Drive file is a ChatGPT image wrapper
- local source hash
- derived asset provenance

Map data stores Atlas instances by `assetId`; it does not duplicate image bytes or flatten terrain and landmarks into one image.

Transparent Atlas assets use a rectangular file envelope with alpha transparency. The envelope is not the gameplay shape and is not limited by the active square or hex grid. Runtime selection and placement treat the derived PNG alpha as the irregular asset shape, while square/hex geometry remains available for recursive maps, token movement, and measurement.
