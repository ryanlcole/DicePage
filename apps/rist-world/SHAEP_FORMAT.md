# SHAEP v1 — Spatial Hot Preservation Object

`SHAEP` is the Shaelvien/RIST spatial asset format. The file extension is `.shaep` and the manifest media type is `application/vnd.shaelvien.shaep+json`.

SHAEP is **not a codec**. PNG, JPEG, TIFF, WebP, GIF, video, audio, sprites and future media remain established payload formats. SHAEP is the persistent identity and spatial/preservation manifest that points at those bytes.

## Core rule

**The server stores truth; the viewer owns the grid and produces perception.**

A world is not saved as a giant pre-rendered image. A viewer positions its temporary grid over world coordinates, reads only placements intersecting that window, resolves their SHAEP payloads, stacks them by depth, and rasterizes only the pixels the current screen can perceive. Moving the viewer changes the address being read; it does not move or reload a giant world bitmap.

## Identity is not the checksum

`ShaepId` is an opaque persistent identity (`shaep-<guid>`). `Sha256` is optional integrity evidence for a payload. Two distinct SHAEP objects may legally contain byte-identical media and therefore have the same checksum without becoming the same object.

## Storage model

A SHAEP manifest contains references, not embedded media bytes.

```text
asset.shaep
  identity
  source payload reference
  canonical payload reference
  spatial defaults
  temporal metadata
  provenance
  storage state
  ingest state
```

The source and canonical payload may initially reference the exact same S3 object. This is how current uploads enter the system: the object is **hot**, immediately readable, and marked `pending-normalization`. A preservation normalizer may later replace the canonical reference without changing `ShaepId`.

Only canonical preservation truth must be permanent. Runtime thumbnails, resized images, decoded frames, texture atlases and viewer composites are representations/cache and may be regenerated or discarded.

The canonical object remains hot while immediate world access requires it. A future S3 lifecycle transition may move that same canonical payload to an archival storage class after policy/time says it no longer needs immediate access. A storage-class transition does not change SHAEP identity or world coordinates.

## Spatial contract

SHAEP v1 carries these intrinsic/default spatial fields:

- `X`, `Y`
- `CubeX`, `CubeY`, `CubeZ`
- `PlaneIndex`
- `ZTier`, `ZLayer`
- `WidthCells`, `HeightCells`

The viewer's grid is the compositor. Cell dimensions determine rendered size; screen pixels are temporary output. A reusable SHAEP may be placed in more than one world location, so a world placement can bind/override the SHAEP's spatial defaults while preserving the same asset identity.

In the current WorldBuilder, `TileItem` stores the concrete placement coordinates/depth and its `ShaepId` links that placement back to the persistent asset.

## Temporal contract

Animated media may additionally provide:

- `FrameCount`
- `FramesPerSecond`
- `DurationSeconds`
- `Loop`

Time changes representation, not spatial identity.

## Provenance

Provenance is persistent. Direct authenticated human uploads begin with origin `HUMAN`. AI-derived material must retain its ancestry and must not silently become Human Made. Unknown provenance remains distinguishable from authenticated human provenance.

## v1 example

```json
{
  "Format": "SHAEP",
  "Version": 1,
  "ShaepId": "shaep-8f3951a777ca48c9ad23d38f6e19c324",
  "Name": "Coast Shore 1",
  "Source": {
    "ObjectKey": "uploads/tiles/coast/abc-coast.png",
    "MediaType": "image/png",
    "Sha256": ""
  },
  "Canonical": {
    "ObjectKey": "uploads/tiles/coast/abc-coast.png",
    "MediaType": "image/png",
    "Sha256": ""
  },
  "Spatial": {
    "X": 0,
    "Y": 0,
    "CubeX": 0,
    "CubeY": 0,
    "CubeZ": 0,
    "PlaneIndex": 0,
    "ZTier": 0,
    "ZLayer": 0,
    "WidthCells": 1,
    "HeightCells": 1
  },
  "Temporal": null,
  "Provenance": {
    "Origin": "HUMAN"
  },
  "StorageState": "hot",
  "IngestStatus": "pending-normalization"
}
```

## Current ingestion boundary

The current browser uploader still accepts the image formats it can safely preview today. Saving the user asset catalog automatically creates a `.shaep` manifest for every new upload and lazily migrates older private uploads without duplicating their media bytes.

Format normalization is deliberately a separate service boundary. AWS MediaConvert can participate for supported video/audio workloads; static raster/vector preservation requires an image-capable normalizer. Whatever service is used, it updates the canonical payload reference rather than changing SHAEP identity.
