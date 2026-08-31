from __future__ import annotations

import io
import json
import shutil
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

from repair_plains_tiles import (
    CURRENT_CATALOG,
    DRIVE_FILE_IDS,
    STAGE,
    current_set_numbers,
    historical_message_id,
    source_rows,
)

DARK_LEVEL = 50.0
SEPARATOR_SCORE = 0.965
MIN_DIM = 32
MAX_DEPTH = 64


def download_original(file_id: str) -> bytes:
    fid = urllib.parse.quote(file_id, safe="")
    urls = (
        f"https://drive.google.com/uc?export=download&id={fid}&confirm=t",
        f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",
        f"https://lh3.googleusercontent.com/d/{fid}=s0",
    )
    errors: list[str] = []
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 RIST-Asset-Repair/2.0", "Accept": "image/*,*/*;q=0.8"})
            with urllib.request.urlopen(req, timeout=90) as response:
                data = response.read()
                content_type = response.headers.get("Content-Type", "")
            if len(data) < 1024 or "text/html" in content_type.casefold():
                raise RuntimeError(f"unexpected response {content_type} {len(data)} bytes")
            with Image.open(io.BytesIO(data)) as probe:
                print(f"  source {probe.width}x{probe.height} {probe.format} {len(data)} bytes", flush=True)
            return data
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
    raise RuntimeError("Unable to recover canonical Drive source: " + " | ".join(errors))


def _bands(values: np.ndarray) -> list[tuple[int, int, float]]:
    hits = np.flatnonzero(values >= SEPARATOR_SCORE)
    if not len(hits):
        return []
    runs: list[tuple[int, int, float]] = []
    start = last = int(hits[0])
    best = float(values[last])
    for raw in hits[1:]:
        pos = int(raw)
        if pos <= last + 2:
            last = pos
            best = max(best, float(values[pos]))
        else:
            runs.append((start, last + 1, best))
            start = last = pos
            best = float(values[pos])
    runs.append((start, last + 1, best))
    return runs


def segment_boxes(image: Image.Image) -> list[tuple[int, int, int, int]]:
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint16)
    dark = rgb.mean(axis=2) < DARK_LEVEL
    height, width = dark.shape

    def recurse(box: tuple[int, int, int, int], depth: int = 0) -> list[tuple[int, int, int, int]]:
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        if w < MIN_DIM or h < MIN_DIM or depth >= MAX_DEPTH:
            return [box]
        region = dark[y0:y1, x0:x1]
        cols = _bands(region.mean(axis=0))
        rows = _bands(region.mean(axis=1))

        left, right, top, bottom = 0, w, 0, h
        for a, b, _ in cols:
            if a <= 3:
                left = max(left, b)
            if b >= w - 3:
                right = min(right, a)
        for a, b, _ in rows:
            if a <= 3:
                top = max(top, b)
            if b >= h - 3:
                bottom = min(bottom, a)
        if (left or right < w or top or bottom < h) and right - left >= MIN_DIM and bottom - top >= MIN_DIM:
            return recurse((x0 + left, y0 + top, x0 + right, y0 + bottom), depth + 1)

        choices: list[tuple[str, int, int, float, int]] = []
        for a, b, score in cols:
            if a >= MIN_DIM and w - b >= MIN_DIM:
                choices.append(("v", a, b, score, w))
        for a, b, score in rows:
            if a >= MIN_DIM and h - b >= MIN_DIM:
                choices.append(("h", a, b, score, h))
        if not choices:
            return [box]
        choices.sort(key=lambda c: (c[3], c[2] - c[1], min(c[1], c[4] - c[2]) / c[4]), reverse=True)
        axis, a, b, _, _ = choices[0]
        if axis == "v":
            return recurse((x0, y0, x0 + a, y1), depth + 1) + recurse((x0 + b, y0, x1, y1), depth + 1)
        return recurse((x0, y0, x1, y0 + a), depth + 1) + recurse((x0, y0 + b, x1, y1), depth + 1)

    boxes = [b for b in recurse((0, 0, width, height)) if b[2] - b[0] >= MIN_DIM and b[3] - b[1] >= MIN_DIM]
    boxes.sort(key=lambda b: (b[1], b[0]))
    if not 2 <= len(boxes) <= 120:
        raise RuntimeError(f"Separator analysis produced implausible cut count {len(boxes)}")
    coverage = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in boxes) / (width * height)
    if coverage < 0.70:
        raise RuntimeError(f"Separator analysis retained only {coverage:.1%} of source area")
    return boxes


def cut_sheet(number: int, payload: bytes) -> int:
    with Image.open(io.BytesIO(payload)) as opened:
        image = opened.convert("RGB")
    boxes = segment_boxes(image)
    target = STAGE / f"plains-{number:03d}"
    target.mkdir(parents=True, exist_ok=True)
    for seq, (x0, y0, x1, y1) in enumerate(boxes, 1):
        output = target / f"tile-{seq:02d}-01.jpg"
        image.crop((x0, y0, x1, y1)).save(output, "JPEG", quality=95, subsampling=0, optimize=True)
        if output.stat().st_size < 1000:
            raise RuntimeError(f"Plains {number:03d} generated tiny cut {output.name}")
    print(f"  -> {len(boxes)} actual pieces", flush=True)
    return len(boxes)


def rewrite_catalog(counts: dict[int, int]) -> None:
    rows = json.loads(CURRENT_CATALOG.read_text(encoding="utf-8"))
    old_plains = [row for row in rows if str(row.get("folder", "")).casefold() == "plains"]
    keep = [row for row in rows if str(row.get("folder", "")).casefold() != "plains"]
    rebuilt: list[dict] = []
    for number, count in sorted(counts.items()):
        needle = f"/plains-{number:03d}/"
        source = next((row for row in old_plains if needle in str(row.get("image", ""))), None)
        if not source:
            raise RuntimeError(f"No current catalog metadata for Plains {number:03d}")
        base = str(source["image"]).rsplit("/", 1)[0]
        for seq in range(1, count + 1):
            rebuilt.append({
                "id": f"aws-plains-{number:03d}-{seq:02d}-01",
                "name": f"Plains {number:03d} · {seq},1",
                "image": f"{base}/tile-{seq:02d}-01.jpg",
                "layer": source.get("layer", "WORLD"),
                "directory": source.get("directory", "Terrain"),
                "folder": source.get("folder", "Plains"),
                "author": source.get("author", "Ryan L. Cole / Shaelvien Drive"),
            })
    CURRENT_CATALOG.write_text(json.dumps(keep + rebuilt, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    sources = source_rows()
    expected = set(sources)
    if current_set_numbers() != expected:
        raise RuntimeError("Refusing repair because current and historical Plains inventories differ")
    source_ids = {historical_message_id(str(item["image"])) for item in sources.values()}
    if source_ids != set(DRIVE_FILE_IDS):
        raise RuntimeError("Canonical Drive source inventory does not exactly match historical Plains inventory")
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    counts: dict[int, int] = {}
    for index, number in enumerate(sorted(sources), 1):
        message_id = historical_message_id(str(sources[number]["image"]))
        print(f"[{index}/{len(sources)}] Plains {number:03d} / {message_id}", flush=True)
        counts[number] = cut_sheet(number, download_original(DRIVE_FILE_IDS[message_id]))

    if set(counts) != expected:
        raise RuntimeError("Incomplete Plains staging")
    rewrite_catalog(counts)
    total = sum(counts.values())
    print("Counts: " + ", ".join(f"{n:03d}={counts[n]}" for n in sorted(counts)), flush=True)
    print(f"Validated complete geometry repair: {len(counts)} sets, {total} actual pieces", flush=True)


if __name__ == "__main__":
    main()
