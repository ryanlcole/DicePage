# SHAEP v2 — Spatial Hot Preservation Object

`SHAEP` is Shaelvien/RIST's converted hot audiovisual archive format. The canonical archive extension is `.shaep`; its media type is `application/vnd.shaelvien.shaep`. Metadata is stored beside the archive as `manifest.json` with media type `application/vnd.shaelvien.shaep+json`.

SHAEP v2 corrects the v1 definition. **A `.shaep` is not merely a manifest around PNG/JPEG/video/audio. It is the target hot archive representation produced by converting supported A/V source media.** The native upload is still preserved as source truth and provenance, but once conversion succeeds the `.shaep` archive becomes the canonical runtime/preservation representation.

SHAEP is best described as a media archive/container format with a conversion profile. Source decoders may vary by input type; the SHAEP archive profile defines the common hot representation and indexing contract. The binary packing/encoder implementation can evolve behind that contract without changing `ShaepId`.

## Core rule

**The server stores truth; the viewer produces perception.**

The server preserves the source, the SHAEP identity, world placement truth, and—when ready—the converted hot archive. The viewer does not own world truth. It reads only the portion of that truth needed for its current camera window, depth, animation time, and controls, then produces the temporary screen representation.

A world is not saved as one giant pre-rendered bitmap. A viewer positions its bounded camera over world coordinates, resolves intersecting SHAEP identities, requests only the needed archive planes/chunks, stacks them by depth, and rasterizes only what the current screen can perceive.

## Identity is not the checksum

`ShaepId` is an opaque persistent identity (`shaep-<guid>`). `Sha256` is optional integrity evidence for a particular source or archive payload. Two distinct SHAEP objects may contain byte-identical payloads and therefore share a checksum without becoming the same object.

Conversion, re-indexing, moving objects, rebuilding caches, or changing the archive encoder does not change `ShaepId`.

## v2 object layout

```text
uploads/shaep/<ShaepId>/
  manifest.json          metadata, provenance, spatial/temporal contract
  archive.shaep          converted hot A/V archive
  archive.index.json     optional external hot-access index
```

The manifest describes three deliberately separate things:

```text
Source       preserved native upload truth
Canonical    best currently usable representation
Archive      .shaep conversion target/status/profile/index
```

During `pending-conversion`, `converting`, or `failed`, `Canonical` may remain the native `Source` so the existing library/viewer never points at a nonexistent archive. When conversion becomes `ready`, `Canonical` must point to `archive.shaep` and use the SHAEP archive media type.

That fallback is compatibility, not the definition of SHAEP. The intended completed state is a converted `.shaep` hot archive.

## Hot archive contract

SHAEP v2 currently names the archive profile `shaep-hot-archive-v1` and layout `indexed-planes`. These are format contracts rather than an accidental dependency on one transcoder.

The archive must support hot/random access. A consumer should be able to obtain the subset needed for the current perception—such as an image plane, temporal frame range, audio range, sprite sequence, or other indexed media region—without treating an entire long A/V source as one indivisible cold blob.

The manifest can carry `ChunkCount`, archive byte length, archive hash, conversion time, and an optional external index object. The encoder is responsible for materializing the binary archive and index. Until that service exists for a given source type, the conversion remains explicitly pending; the system must never label the native source itself as a completed `.shaep` conversion.

## Conversion lifecycle

```text
native source upload
      ↓
SHAEP identity + v2 manifest
      ↓
pending-conversion
      ↓
converting
      ↓
archive.shaep + index
      ↓
ready
      ↓
Canonical = archive.shaep
```

A failed conversion retains the native source and its provenance, records `failed`, and may retry later under the same `ShaepId`.

## Spatial contract

SHAEP carries intrinsic/default spatial fields:

- `X`, `Y`
- `CubeX`, `CubeY`, `CubeZ`
- `PlaneIndex`
- `ZTier`, `ZLayer`
- `WidthCells`, `HeightCells`

These are reusable asset defaults, not a substitute for concrete world placement. A `TileItem`/world placement keeps its own coordinates and depth while linking to `ShaepId`; the same SHAEP may therefore appear in more than one place without duplicating identity.

The viewer's grid and camera are perception mechanisms. Button controls and gestures operate the same viewer authority; they do not rewrite the SHAEP's world truth.

## Temporal contract

Animated/A/V media may additionally provide:

- `FrameCount`
- `FramesPerSecond`
- `DurationSeconds`
- `Loop`

Time changes the representation selected from the archive, not spatial identity.

## Provenance

Provenance is persistent. Direct authenticated human uploads begin with origin `HUMAN`. AI-derived material retains its ancestry and must not silently become Human Made. Unknown provenance remains distinguishable from authenticated human provenance.

The native source remains available as provenance/source truth even after the canonical hot archive exists.

## v2 example while conversion is pending

```json
{
  "Format": "SHAEP",
  "Version": 2,
  "ShaepId": "shaep-8f3951a777ca48c9ad23d38f6e19c324",
  "Name": "Coast Shore 1",
  "Source": {
    "ObjectKey": "uploads/tiles/coast/abc-coast.png",
    "MediaType": "image/png"
  },
  "Canonical": {
    "ObjectKey": "uploads/tiles/coast/abc-coast.png",
    "MediaType": "image/png"
  },
  "Archive": {
    "ObjectKey": "uploads/shaep/shaep-8f3951a777ca48c9ad23d38f6e19c324/archive.shaep",
    "MediaType": "application/vnd.shaelvien.shaep",
    "Profile": "shaep-hot-archive-v1",
    "Layout": "indexed-planes",
    "ConversionStatus": "pending-conversion",
    "SourceMediaType": "image/png",
    "IndexObjectKey": "uploads/shaep/shaep-8f3951a777ca48c9ad23d38f6e19c324/archive.index.json"
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
  "IngestStatus": "pending-conversion"
}
```

When conversion succeeds, `Archive.ConversionStatus` and `IngestStatus` become `ready`, archive integrity/size/index fields are populated, and `Canonical` switches to `archive.shaep`.

## v1 compatibility

SHAEP v1 was implemented as a JSON manifest whose source and canonical payload could be the same native object. That implementation is now treated as a legacy metadata contract, not the final meaning of `.shaep`.

The v2 reader accepts v1 manifests and upgrades them without changing `ShaepId`, native source bytes, provenance, or world placements. The upgrade creates the v2 archive target and marks conversion pending. Existing v1 manifests may remain at `manifest.shaep`; new v2 metadata lives at `manifest.json`, reserving `.shaep` for the actual converted hot archive.

Runtime thumbnails, resized previews, decoded GPU textures, viewer composites and similar screen caches remain disposable representations. Source truth and completed SHAEP archive truth are persistent according to storage policy. A storage-class transition does not change SHAEP identity.
