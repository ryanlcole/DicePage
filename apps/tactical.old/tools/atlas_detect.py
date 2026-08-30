from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "atlas" / "atlas_source_manifest.json"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "atlas" / "detections"
DEFAULT_REPORT_DIR = Path(r"C:\Shaelvien\verify_reports\shaelvien_atlas_asset_pipeline_2")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def median(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def sample_background(image: Image.Image, step: int) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    samples: list[tuple[int, int, int]] = []
    for x in range(0, width, step):
        samples.append(pixels[x, 0])
        samples.append(pixels[x, height - 1])
    for y in range(0, height, step):
        samples.append(pixels[0, y])
        samples.append(pixels[width - 1, y])
    return (
        median([sample[0] for sample in samples]),
        median([sample[1] for sample in samples]),
        median([sample[2] for sample in samples]),
    )


def foreground_mask(image: Image.Image, background: tuple[int, int, int], threshold: int) -> bytearray:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    mask = bytearray(width * height)
    for y in range(height):
        offset = y * width
        for x in range(width):
            r, g, b = pixels[x, y]
            distance = abs(r - background[0]) + abs(g - background[1]) + abs(b - background[2])
            if distance >= threshold:
                mask[offset + x] = 1
    return mask


def edge_flood_foreground_mask(image: Image.Image, background: tuple[int, int, int], threshold: int) -> bytearray:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    background_mask = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))
    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        index = y * width + x
        if background_mask[index]:
            continue
        r, g, b = pixels[x, y]
        distance = abs(r - background[0]) + abs(g - background[1]) + abs(b - background[2])
        if distance > threshold:
            continue
        background_mask[index] = 1
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    mask = bytearray(width * height)
    for index, value in enumerate(background_mask):
        mask[index] = 0 if value else 1
    return mask


def connected_components(mask: bytearray, width: int, height: int, min_area: int) -> list[dict]:
    visited = bytearray(width * height)
    components: list[dict] = []
    neighbors = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    for y in range(height):
        for x in range(width):
            index = y * width + x
            if not mask[index] or visited[index]:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited[index] = 1
            min_x = max_x = x
            min_y = max_y = y
            area = 0
            while queue:
                cx, cy = queue.popleft()
                area += 1
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                for dx, dy in neighbors:
                    nx = cx + dx
                    ny = cy + dy
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    ni = ny * width + nx
                    if mask[ni] and not visited[ni]:
                        visited[ni] = 1
                        queue.append((nx, ny))
            if area >= min_area:
                components.append({"x": min_x, "y": min_y, "w": max_x - min_x + 1, "h": max_y - min_y + 1, "area": area})
    return components


def gap_between(a: dict, b: dict) -> float:
    ax2 = a["x"] + a["w"]
    ay2 = a["y"] + a["h"]
    bx2 = b["x"] + b["w"]
    by2 = b["y"] + b["h"]
    dx = max(b["x"] - ax2, a["x"] - bx2, 0)
    dy = max(b["y"] - ay2, a["y"] - by2, 0)
    return math.hypot(dx, dy)


def merge_boxes(boxes: list[dict], max_gap: int, max_width: int = 0, max_height: int = 0) -> list[dict]:
    groups = [{**box, "members": 1, "area": box["area"]} for box in boxes]
    changed = True
    while changed:
        changed = False
        merged: list[dict] = []
        used = [False] * len(groups)
        for i, current in enumerate(groups):
            if used[i]:
                continue
            used[i] = True
            acc = dict(current)
            absorbed = True
            while absorbed:
                absorbed = False
                for j, candidate in enumerate(groups):
                    if used[j]:
                        continue
                    if gap_between(acc, candidate) <= max_gap:
                        x1 = min(acc["x"], candidate["x"])
                        y1 = min(acc["y"], candidate["y"])
                        x2 = max(acc["x"] + acc["w"], candidate["x"] + candidate["w"])
                        y2 = max(acc["y"] + acc["h"], candidate["y"] + candidate["h"])
                        if max_width and x2 - x1 > max_width:
                            continue
                        if max_height and y2 - y1 > max_height:
                            continue
                        acc = {
                            "x": x1,
                            "y": y1,
                            "w": x2 - x1,
                            "h": y2 - y1,
                            "area": acc["area"] + candidate["area"],
                            "members": acc["members"] + candidate.get("members", 1),
                        }
                        used[j] = True
                        absorbed = True
                        changed = True
            merged.append(acc)
        groups = merged
    return groups


def scale_box(box: dict, scale: int, width: int, height: int, padding: int) -> dict:
    x = max(0, box["x"] * scale - padding)
    y = max(0, box["y"] * scale - padding)
    x2 = min(width, (box["x"] + box["w"]) * scale + padding)
    y2 = min(height, (box["y"] + box["h"]) * scale + padding)
    return {
        "x": int(x),
        "y": int(y),
        "width": int(x2 - x),
        "height": int(y2 - y),
        "componentArea": int(box["area"] * scale * scale),
        "mergedComponents": int(box.get("members", 1)),
    }


def candidate_id(source_id: str, index: int) -> str:
    safe = source_id.replace(".", "-").replace("_", "-")
    return f"{safe}-candidate-{index:03d}"


def draw_contact_sheet(image: Image.Image, candidates: list[dict], output_path: Path) -> None:
    annotated = image.convert("RGBA")
    draw = ImageDraw.Draw(annotated)
    for index, candidate in enumerate(candidates, start=1):
        rect = candidate["sourceRect"]
        x, y, width, height = rect["x"], rect["y"], rect["width"], rect["height"]
        draw.rectangle((x, y, x + width, y + height), outline=(230, 185, 70, 255), width=3)
        draw.text((x + 4, y + 4), str(index), fill=(255, 240, 180, 255))
    annotated.thumbnail((1200, 800), Image.Resampling.LANCZOS)

    crop_w = 190
    crop_h = 160
    cols = 5
    rows = math.ceil(len(candidates) / cols)
    sheet = Image.new("RGBA", (max(annotated.width, cols * crop_w), annotated.height + rows * crop_h + 24), (18, 16, 12, 255))
    sheet.alpha_composite(annotated, ((sheet.width - annotated.width) // 2, 0))
    draw = ImageDraw.Draw(sheet)
    y_offset = annotated.height + 20
    for idx, candidate in enumerate(candidates):
        rect = candidate["sourceRect"]
        crop = image.crop((rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"])).convert("RGBA")
        crop.thumbnail((crop_w - 24, crop_h - 40), Image.Resampling.LANCZOS)
        x0 = (idx % cols) * crop_w
        y0 = y_offset + (idx // cols) * crop_h
        sheet.alpha_composite(crop, (x0 + (crop_w - crop.width) // 2, y0 + 8))
        draw.text((x0 + 8, y0 + crop_h - 28), f"{idx + 1}: {rect['width']}x{rect['height']}", fill=(240, 230, 206, 255))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def find_source(manifest: dict, source_id: str) -> dict:
    for source in manifest["sources"]:
        if source["sourceId"] == source_id:
            return source
    raise KeyError(f"source id not found: {source_id}")


def detect(args: argparse.Namespace) -> dict:
    manifest = load_json(Path(args.manifest))
    source = find_source(manifest, args.source_id)
    source_path = ROOT / source["localSourcePath"]
    source_hash = sha256_file(source_path)
    if source_hash != source["contentHash"]:
        raise ValueError(f"source hash mismatch for {source['sourceId']}: {source_hash}")

    with Image.open(source_path) as original:
        image = original.convert("RGB")
    full_width, full_height = image.size
    work = image.resize((full_width // args.scale, full_height // args.scale), Image.Resampling.BILINEAR) if args.scale > 1 else image
    background = sample_background(work, args.sample_step)
    if args.background_mode == "edge_flood":
        mask = edge_flood_foreground_mask(work, background, args.threshold)
    else:
        mask = foreground_mask(work, background, args.threshold)
    components = connected_components(mask, work.width, work.height, args.min_area)
    max_group_width = args.max_group_width // args.scale if args.max_group_width else 0
    max_group_height = args.max_group_height // args.scale if args.max_group_height else 0
    merged = merge_boxes(components, args.merge_gap, max_group_width, max_group_height)
    boxes = [
        scale_box(box, args.scale, full_width, full_height, args.padding)
        for box in merged
    ]
    boxes = [
        box for box in boxes
        if box["width"] >= args.min_width and box["height"] >= args.min_height
    ]
    boxes.sort(key=lambda box: (box["y"], box["x"], box["width"] * box["height"]))
    candidates = []
    for index, box in enumerate(boxes, start=1):
        candidates.append({
            "candidateId": candidate_id(source["sourceId"], index),
            "scanOrder": index,
            "sourceId": source["sourceId"],
            "sourceRect": box,
            "shapeModel": "irregular_alpha_mask",
            "rectIsStorageEnvelope": True,
            "alphaMaskSource": "derived_png_alpha",
            "detection": {
                "method": "left_to_right_top_down_edge_background_component_distance",
                "backgroundMode": args.background_mode,
                "backgroundRgb": list(background),
                "threshold": args.threshold,
                "scale": args.scale,
                "mergeGapPx": args.merge_gap * args.scale,
                "paddingPx": args.padding,
                "reviewStatus": "candidate_unapproved",
                "notes": [
                    "Candidates are sorted from top to bottom, then left to right.",
                    "sourceRect is the non-authoritative storage envelope for the transparent derived asset.",
                    "The playable/art shape is the derived PNG alpha mask; square and hex grids are not used as art-crop constraints."
                ]
            }
        })
    payload = {
        "schemaVersion": "shaelvien.atlas_detection_candidates.v1",
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "sourceId": source["sourceId"],
        "sourcePath": source["localSourcePath"],
        "sourceHash": source_hash,
        "driveFileId": source["driveFileId"],
        "drivePath": source["drivePath"],
        "parameters": {
            "threshold": args.threshold,
            "backgroundMode": args.background_mode,
            "scale": args.scale,
            "mergeGap": args.merge_gap,
            "padding": args.padding,
            "minArea": args.min_area,
            "minWidth": args.min_width,
            "minHeight": args.min_height,
            "maxGroupWidth": args.max_group_width,
            "maxGroupHeight": args.max_group_height
        },
        "componentCount": len(components),
        "candidateCount": len(candidates),
        "candidates": candidates
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect separated Atlas source-sheet objects by foreground distance.")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--threshold", type=int, default=44)
    parser.add_argument("--background-mode", choices=["edge_flood", "threshold"], default="edge_flood")
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--merge-gap", type=int, default=12, help="Gap in working-image pixels before scaling.")
    parser.add_argument("--padding", type=int, default=8)
    parser.add_argument("--min-area", type=int, default=80, help="Minimum component area in working-image pixels.")
    parser.add_argument("--min-width", type=int, default=28)
    parser.add_argument("--min-height", type=int, default=28)
    parser.add_argument("--max-group-width", type=int, default=0)
    parser.add_argument("--max-group-height", type=int, default=0)
    parser.add_argument("--out", default="")
    parser.add_argument("--contact-sheet", default="")
    parser.add_argument("--sample-step", type=int, default=12)
    args = parser.parse_args()

    payload = detect(args)
    out_path = Path(args.out) if args.out else DEFAULT_OUTPUT_DIR / f"{args.source_id.replace('.', '_')}.json"
    write_json(out_path, payload)
    if args.contact_sheet:
        manifest = load_json(Path(args.manifest))
        source = find_source(manifest, args.source_id)
        with Image.open(ROOT / source["localSourcePath"]) as image:
            draw_contact_sheet(image.convert("RGBA"), payload["candidates"], Path(args.contact_sheet))
    print(json.dumps({
        "ok": True,
        "sourceId": payload["sourceId"],
        "componentCount": payload["componentCount"],
        "candidateCount": payload["candidateCount"],
        "output": str(out_path),
        "contactSheet": args.contact_sheet or None
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
