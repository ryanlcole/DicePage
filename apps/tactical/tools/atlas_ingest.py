from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from collections import deque

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "atlas" / "atlas_source_manifest.json"
REGISTRY_PATH = ROOT / "data" / "atlas" / "atlas_asset_registry.json"
DERIVED_ROOT = ROOT / "assets" / "atlas" / "derived"
THUMB_ROOT = ROOT / "assets" / "atlas" / "thumbnails"

LAYER_ORDER = {
    "base": 0,
    "terrain": 1,
    "terrain_transition": 2,
    "water_system": 3,
    "natural_landmark": 4,
    "road": 5,
    "civilization_landmark": 6,
    "structure": 7,
    "object": 8,
    "gameplay_entity": 9,
    "gm_overlay": 10,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def transparent_background(crop: Image.Image, threshold: int) -> Image.Image:
    rgba = crop.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    samples = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    bg = tuple(sum(sample[channel] for sample in samples) // len(samples) for channel in range(3))
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            distance = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            if distance <= threshold:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def transparent_background_edge_flood(crop: Image.Image, threshold: int) -> Image.Image:
    rgba = crop.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    samples = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    bg = tuple(sum(sample[channel] for sample in samples) // len(samples) for channel in range(3))
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))
    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height or (x, y) in visited:
            continue
        visited.add((x, y))
        r, g, b, a = pixels[x, y]
        distance = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
        if distance > threshold:
            continue
        pixels[x, y] = (r, g, b, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return rgba


def build_registry(manifest: dict, *, dry_run: bool = False) -> dict:
    source_by_id = {source["sourceId"]: source for source in manifest["sources"]}
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    sources = []
    assets = []

    for source in manifest["sources"]:
        source_path = ROOT / source["localSourcePath"]
        if not source_path.exists():
            raise FileNotFoundError(f"missing local source: {source['localSourcePath']}")
        source_hash = sha256_file(source_path)
        if source_hash != source["contentHash"]:
            raise ValueError(f"source hash mismatch for {source['sourceId']}: {source_hash}")
        with Image.open(source_path) as image:
            width, height = image.size
        if width != source["widthPx"] or height != source["heightPx"]:
            raise ValueError(f"source dimensions mismatch for {source['sourceId']}: {width}x{height}")
        sources.append({
            "sourceId": source["sourceId"],
            "name": source["name"],
            "category": source["category"],
            "collection": source["collection"],
            "driveFileId": source["driveFileId"],
            "driveParentId": source["driveParentId"],
            "drivePath": source["drivePath"],
            "driveMimeType": source["driveMimeType"],
            "driveModifiedTime": source["driveModifiedTime"],
            "chatgptShareId": source["chatgptShareId"],
            "chatgptShareUrl": source["chatgptShareUrl"],
            "chatgptGenerationId": source["chatgptGenerationId"],
            "chatgptConversationId": source["chatgptConversationId"],
            "chatgptMessageId": source["chatgptMessageId"],
            "chatgptAssetPointer": source["chatgptAssetPointer"],
            "localSourcePath": source["localSourcePath"],
            "mimeType": source["mimeType"],
            "widthPx": width,
            "heightPx": height,
            "contentHash": source_hash,
            "syncStatus": source["syncStatus"],
            "approvedStatus": source["approvedStatus"],
            "lastVerified": now,
        })

    for definition in manifest["assetDefinitions"]:
        source = source_by_id[definition["sourceId"]]
        source_path = ROOT / source["localSourcePath"]
        x, y, width, height = definition["sourceRect"]
        derived_path = DERIVED_ROOT / f"{definition['assetId'].replace('.', '-')}.png"
        thumb_path = THUMB_ROOT / f"{definition['assetId'].replace('.', '-')}.png"
        if not dry_run:
            derived_path.parent.mkdir(parents=True, exist_ok=True)
            thumb_path.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(source_path) as image:
                crop = image.crop((x, y, x + width, y + height))
                alpha = definition.get("alphaExtraction") or {}
                if definition.get("transparentBackground") and alpha.get("mode") == "background_key":
                    crop = transparent_background(crop, int(alpha.get("threshold", 30)))
                elif definition.get("transparentBackground") and alpha.get("mode") == "edge_flood":
                    crop = transparent_background_edge_flood(crop, int(alpha.get("threshold", 30)))
                else:
                    crop = crop.convert("RGBA")
                crop.save(derived_path)
                thumb = crop.copy()
                thumb.thumbnail((160, 120), Image.Resampling.LANCZOS)
                thumb.save(thumb_path)

        with Image.open(derived_path) as derived:
            native_width, native_height = derived.size
        transparent_background_enabled = bool(definition.get("transparentBackground"))
        shape_model = definition.get("shapeModel") or ("irregular_alpha_mask" if transparent_background_enabled else "rectangular_image")
        assets.append({
            "assetId": definition["assetId"],
            "name": definition["name"],
            "category": definition["category"],
            "collection": definition["collection"],
            "sourceImage": source["localSourcePath"],
            "sourceId": source["sourceId"],
            "sourceRect": {"x": x, "y": y, "width": width, "height": height},
            "derivedPath": rel(derived_path),
            "thumbnailPath": rel(thumb_path),
            "mimeType": "image/png",
            "nativeWidth": native_width,
            "nativeHeight": native_height,
            "contentHash": sha256_file(derived_path),
            "thumbnailHash": sha256_file(thumb_path),
            "anchor": definition.get("anchor", "center"),
            "allowedRotations": definition.get("allowedRotations", [0]),
            "layer": definition["layer"],
            "layerOrder": LAYER_ORDER.get(definition["layer"], 50),
            "tags": definition.get("tags", []),
            "connectors": definition.get("connectors", []),
            "transparentBackground": transparent_background_enabled,
            "shapeModel": shape_model,
            "rectIsStorageEnvelope": bool(definition.get("rectIsStorageEnvelope", transparent_background_enabled)),
            "alphaMaskSource": definition.get("alphaMaskSource", "derived_png_alpha" if transparent_background_enabled else "none"),
            "createdFrom": {
                "sourceId": source["sourceId"],
                "driveFileId": source["driveFileId"],
                "chatgptShareId": source["chatgptShareId"],
                "chatgptGenerationId": source["chatgptGenerationId"],
            },
            "defaultPlacement": definition.get("defaultPlacement", {}),
            "version": 1,
            "enabled": True,
        })

    return {
        "schemaVersion": "shaelvien.atlas_asset_registry.v1",
        "generatedAt": now,
        "sourceAuthority": manifest["sourceAuthority"],
        "syncPolicy": manifest["syncPolicy"],
        "layerOrder": LAYER_ORDER,
        "sources": sorted(sources, key=lambda item: item["sourceId"]),
        "assets": sorted(assets, key=lambda item: (item["layerOrder"], item["collection"], item["assetId"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Shaelvien Atlas derived assets and runtime registry.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = load_json(Path(args.manifest))
    registry = build_registry(manifest, dry_run=args.dry_run)
    if not args.dry_run:
        write_json(Path(args.registry), registry)
    print(json.dumps({
        "ok": True,
        "dryRun": args.dry_run,
        "sources": len(registry["sources"]),
        "assets": len(registry["assets"]),
        "registry": str(Path(args.registry)),
        "derivedRoot": str(DERIVED_ROOT),
        "thumbnailRoot": str(THUMB_ROOT),
    }, indent=2))


if __name__ == "__main__":
    main()
