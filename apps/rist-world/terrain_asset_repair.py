from __future__ import annotations

import io
import json
import math
import shutil
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

from repair_plains_tiles import (
    CURRENT_CATALOG,
    DRIVE_FILE_IDS as PLAINS_DRIVE_FILE_IDS,
    historical_message_id,
    source_rows as plains_source_rows,
)


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "build" / "terrain-repair"
SOURCE_CACHE = ROOT / "build" / "terrain-source-cache"

OCEAN_DRIVE_FILE_IDS = {
    67: "1IOsZjw3CM5Es0jrJbpiRlfjOk6VAf6RY",
    68: "1OT_wceQsZCPeu3ycZuLlsrw7jhRDYgV_",
    69: "1S2A_1AkPxKImCXPMns3cND8H_joSpS7c",
    70: "1LAC_7T9DRwD-CYnIM6nP7bua18KMkjJP",
    71: "114QASi-hXViwU7KDXPobMv_ZoeAiAi_3",
}
ICE_DRIVE_FILE_IDS = {
    21: "1TjEeQZh67r32wPd_UwmGQ2RgIjLmWF8F",
}

MIN_DIMENSION = 28
MIN_OUTPUT_BYTES = 1_000
REGULAR_GRID_SIZE = 6
REGULAR_INSET_FRACTION = 0.12
ICE_COLUMNS = 6
ICE_ROWS = 5
ICE_INSET_FRACTION = 0.08


def download_drive_image(file_id: str) -> bytes:
    """Download the canonical Drive image without accepting HTML fallbacks."""
    cached = SOURCE_CACHE / f"{file_id}.img"
    if cached.exists():
        payload = cached.read_bytes()
        with Image.open(io.BytesIO(payload)) as probe:
            probe.verify()
        return payload

    fid = urllib.parse.quote(file_id, safe="")
    urls = (
        f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",
        f"https://drive.google.com/uc?export=download&id={fid}&confirm=t",
        f"https://lh3.googleusercontent.com/d/{fid}=s0",
    )
    failures: list[str] = []
    for url in urls:
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 RIST-Asset-Repair/3.0",
                    "Accept": "image/*,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = response.read()
                content_type = response.headers.get("Content-Type", "")
            if len(payload) < 1024 or "text/html" in content_type.casefold():
                raise RuntimeError(f"unexpected response {content_type} ({len(payload)} bytes)")
            with Image.open(io.BytesIO(payload)) as probe:
                probe.verify()
            SOURCE_CACHE.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(payload)
            return payload
        except Exception as exc:  # pragma: no cover - endpoint fallback reporting
            failures.append(f"{type(exc).__name__}: {exc}")
    raise RuntimeError("Canonical Drive image unavailable: " + " | ".join(failures))


def _bands(values: np.ndarray, minimum_score: float) -> list[tuple[int, int, float]]:
    hits = np.flatnonzero(values >= minimum_score)
    if not len(hits):
        return []
    runs: list[tuple[int, int, float]] = []
    start = last = int(hits[0])
    best = float(values[last])
    for raw in hits[1:]:
        position = int(raw)
        if position <= last + 2:
            last = position
            best = max(best, float(values[position]))
        else:
            runs.append((start, last + 1, best))
            start = last = position
            best = float(values[position])
    runs.append((start, last + 1, best))
    return runs


def _recursive_separator_boxes(
    dark: np.ndarray,
    separator_score: float,
) -> list[tuple[int, int, int, int]]:
    """Split an irregular atlas only at full-width/full-height dark gutters."""
    height, width = dark.shape

    def recurse(box: tuple[int, int, int, int], depth: int = 0) -> list[tuple[int, int, int, int]]:
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        if w < MIN_DIMENSION or h < MIN_DIMENSION or depth >= 96:
            return [box]
        region = dark[y0:y1, x0:x1]
        columns = _bands(region.mean(axis=0), separator_score)
        rows = _bands(region.mean(axis=1), separator_score)

        left, right, top, bottom = 0, w, 0, h
        for a, b, _ in columns:
            if a <= 4:
                left = max(left, b)
            if b >= w - 4:
                right = min(right, a)
        for a, b, _ in rows:
            if a <= 4:
                top = max(top, b)
            if b >= h - 4:
                bottom = min(bottom, a)
        if (
            (left or right < w or top or bottom < h)
            and right - left >= MIN_DIMENSION
            and bottom - top >= MIN_DIMENSION
        ):
            return recurse((x0 + left, y0 + top, x0 + right, y0 + bottom), depth + 1)

        choices: list[tuple[str, int, int, float, int]] = []
        for a, b, score in columns:
            if a >= MIN_DIMENSION and w - b >= MIN_DIMENSION:
                choices.append(("vertical", a, b, score, w))
        for a, b, score in rows:
            if a >= MIN_DIMENSION and h - b >= MIN_DIMENSION:
                choices.append(("horizontal", a, b, score, h))
        if not choices:
            return [box]
        choices.sort(
            key=lambda item: (
                item[3],
                item[2] - item[1],
                min(item[1], item[4] - item[2]) / item[4],
            ),
            reverse=True,
        )
        axis, a, b, _, _ = choices[0]
        if axis == "vertical":
            return recurse((x0, y0, x0 + a, y1), depth + 1) + recurse(
                (x0 + b, y0, x1, y1), depth + 1
            )
        return recurse((x0, y0, x1, y0 + a), depth + 1) + recurse(
            (x0, y0 + b, x1, y1), depth + 1
        )

    return recurse((0, 0, width, height))


def _regular_grid_boxes(width: int, height: int) -> list[tuple[int, int, int, int]]:
    """Cut known 6x6 sheets on their cells, excluding their engraved frames."""
    boxes: list[tuple[int, int, int, int]] = []
    for row in range(REGULAR_GRID_SIZE):
        y0 = round(row * height / REGULAR_GRID_SIZE)
        y1 = round((row + 1) * height / REGULAR_GRID_SIZE)
        for column in range(REGULAR_GRID_SIZE):
            x0 = round(column * width / REGULAR_GRID_SIZE)
            x1 = round((column + 1) * width / REGULAR_GRID_SIZE)
            inset = max(8, round(min(x1 - x0, y1 - y0) * REGULAR_INSET_FRACTION))
            boxes.append((x0 + inset, y0 + inset, x1 - inset, y1 - inset))
    return boxes


def _separator_grid_boxes(
    image: Image.Image,
    expected_columns: int,
    expected_rows: int,
    inset_fraction: float,
) -> list[tuple[int, int, int, int]]:
    """Extract a uniform grid whose row count cannot be inferred from aspect ratio."""
    luminance = np.asarray(image.convert("RGB"), dtype=np.uint16).mean(axis=2)
    dark = luminance < 55.0
    column_bands = _bands(dark.mean(axis=0), 0.90)
    row_bands = _bands(dark.mean(axis=1), 0.90)
    height, width = dark.shape

    def intervals(
        length: int,
        bands: list[tuple[int, int, float]],
        expected: int,
        axis: str,
    ) -> list[tuple[int, int]]:
        if len(bands) != expected + 1:
            raise RuntimeError(f"Expected {expected + 1} {axis} separator bands, found {len(bands)}")
        if bands[0][0] > 8 or bands[-1][1] < length - 8:
            raise RuntimeError(f"{axis.capitalize()} grid boundary is incomplete")
        gaps = [(bands[index][1], bands[index + 1][0]) for index in range(expected)]
        if any(end - start < MIN_DIMENSION for start, end in gaps):
            raise RuntimeError(f"{axis.capitalize()} grid contains a tiny panel")
        return gaps

    columns = intervals(width, column_bands, expected_columns, "column")
    rows = intervals(height, row_bands, expected_rows, "row")
    boxes: list[tuple[int, int, int, int]] = []
    for y0, y1 in rows:
        for x0, x1 in columns:
            inset = max(8, round(min(x1 - x0, y1 - y0) * inset_fraction))
            box = (x0 + inset, y0 + inset, x1 - inset, y1 - inset)
            if box[2] - box[0] < MIN_DIMENSION or box[3] - box[1] < MIN_DIMENSION:
                raise RuntimeError("Frame removal produced a tiny panel")
            boxes.append(box)
    return boxes


def separator_boxes(image: Image.Image) -> list[tuple[int, int, int, int]]:
    """Return actual panel interiors, following the sheet's dark separators.

    Square source sheets use a regular six-by-six layout whose engraved frame
    is inset from every tile. Landscape sheets are irregular atlases; those are
    recursively divided only where a separator crosses the current region.
    Their threshold adapts to each source so dark grass is not mistaken for a
    gutter and bright parchment still separates cleanly.
    """
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint16)
    height, width = rgb.shape[:2]
    regular = abs(width - height) <= 2
    if regular:
        return _regular_grid_boxes(width, height)

    luminance = rgb.mean(axis=2)
    dark_tenth_percentile = float(np.percentile(luminance, 10))
    dark_level = min(60.0, 40.0 + dark_tenth_percentile)
    separator_score = 0.93 if dark_tenth_percentile >= 25.0 else 0.965
    dark = luminance < dark_level
    boxes = [
        box
        for box in _recursive_separator_boxes(dark, separator_score)
        if box[2] - box[0] >= MIN_DIMENSION and box[3] - box[1] >= MIN_DIMENSION
    ]
    boxes.sort(key=lambda box: (box[1], box[0]))
    if not 24 <= len(boxes) <= 80:
        raise RuntimeError(f"Irregular sheet produced implausible panel count {len(boxes)}")
    coverage = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in boxes) / (width * height)
    if coverage < 0.68:
        raise RuntimeError(f"Separator analysis retained only {coverage:.1%} of source area")
    return boxes


def _square_crop(image: Image.Image) -> Image.Image:
    """Center-crop an extracted panel without reintroducing its separator."""
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    return image.crop((left, top, left + side, top + side))


def _seamless_texture(image: Image.Image, blend_fraction: float = 0.16) -> Image.Image:
    """Move central texture to the perimeter with a smooth periodic blend."""
    source = np.asarray(image.convert("RGB"), dtype=np.float32)
    height, width = source.shape[:2]
    x_weight = np.sin(np.linspace(0, np.pi, width, dtype=np.float32)) ** 2
    y_weight = np.sin(np.linspace(0, np.pi, height, dtype=np.float32)) ** 2
    center_weight = (y_weight[:, None] * x_weight[None, :])[..., None]
    shifted = np.roll(source, (height // 2, width // 2), axis=(0, 1))
    pixels = source * center_weight + shifted * (1 - center_weight)

    # Make paired edge pixels converge over a shallow feather. This preserves
    # the water detail while guaranteeing that a repeated tile has no hard box.
    feather = max(6, round(min(width, height) * blend_fraction / 2))
    for distance in range(feather):
        weight = ((feather - distance) / feather) ** 2
        opposite = (pixels[:, distance] + pixels[:, -(distance + 1)]) / 2
        pixels[:, distance] = pixels[:, distance] * (1 - weight) + opposite * weight
        pixels[:, -(distance + 1)] = pixels[:, -(distance + 1)] * (1 - weight) + opposite * weight
    for distance in range(feather):
        weight = ((feather - distance) / feather) ** 2
        opposite = (pixels[distance, :] + pixels[-(distance + 1), :]) / 2
        pixels[distance, :] = pixels[distance, :] * (1 - weight) + opposite * weight
        pixels[-(distance + 1), :] = pixels[-(distance + 1), :] * (1 - weight) + opposite * weight
    return Image.fromarray(np.uint8(np.clip(pixels, 0, 255)))


def _edge_error(image: Image.Image) -> float:
    pixels = np.asarray(image.convert("RGB"), dtype=np.float32)
    horizontal = np.mean(np.abs(pixels[:, 0] - pixels[:, -1]))
    vertical = np.mean(np.abs(pixels[0] - pixels[-1]))
    return float((horizontal + vertical) / 2)


def _seam_band_error(image: Image.Image) -> float:
    """Detect a broad dark/light frame even when the outer pixels happen to match."""
    pixels = np.asarray(image.convert("L"), dtype=np.float32)
    height, width = pixels.shape
    band = max(2, round(min(width, height) * 0.10))
    outer = np.concatenate(
        (
            pixels[:band].ravel(),
            pixels[-band:].ravel(),
            pixels[band:-band, :band].ravel(),
            pixels[band:-band, -band:].ravel(),
        )
    )
    inner = np.concatenate(
        (
            pixels[band : 2 * band, band:-band].ravel(),
            pixels[-2 * band : -band, band:-band].ravel(),
            pixels[2 * band : -2 * band, band : 2 * band].ravel(),
            pixels[2 * band : -2 * band, -2 * band : -band].ravel(),
        )
    )
    return float(abs(outer.mean() - inner.mean()))


def save_jpeg(image: Image.Image, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, "JPEG", quality=95, subsampling=0, optimize=True)
    if target.stat().st_size < MIN_OUTPUT_BYTES:
        raise RuntimeError(f"Generated tiny or empty cut: {target}")


def rebuild_plains() -> dict[int, int]:
    counts: dict[int, int] = {}
    rows = plains_source_rows()
    for index, number in enumerate(sorted(rows), 1):
        message_id = historical_message_id(str(rows[number]["image"]))
        file_id = PLAINS_DRIVE_FILE_IDS[message_id]
        print(f"Plains [{index}/{len(rows)}] {number:03d}", flush=True)
        with Image.open(io.BytesIO(download_drive_image(file_id))) as opened:
            source = opened.convert("RGB")
        boxes = separator_boxes(source)
        print(f"  -> {len(boxes)} whole panels", flush=True)
        target = STAGE / "tilesets" / "world" / "terrain" / "plains" / f"plains-{number:03d}"
        for sequence, box in enumerate(boxes, 1):
            save_jpeg(_square_crop(source.crop(box)), target / f"tile-{sequence:02d}-01.jpg")
        counts[number] = len(boxes)
    return counts


def rebuild_ocean() -> tuple[dict[int, int], dict[int, float], dict[int, float]]:
    counts: dict[int, int] = {}
    edge_errors: dict[int, float] = {}
    seam_band_errors: dict[int, float] = {}
    for index, (number, file_id) in enumerate(sorted(OCEAN_DRIVE_FILE_IDS.items()), 1):
        print(f"Ocean [{index}/{len(OCEAN_DRIVE_FILE_IDS)}] {number:03d}", flush=True)
        with Image.open(io.BytesIO(download_drive_image(file_id))) as opened:
            source = opened.convert("RGB")
        boxes = separator_boxes(source)
        target = STAGE / "tilesets" / "world" / "terrain" / "ocean" / f"ocean-{number:03d}"
        worst = 0.0
        worst_band = 0.0
        base_band = 0.0
        for sequence, box in enumerate(boxes, 1):
            clean = _square_crop(source.crop(box))
            seamless = _seamless_texture(clean)
            row = math.ceil(sequence / 6)
            column = ((sequence - 1) % 6) + 1
            output = target / f"tile-{row:02d}-{column:02d}.jpg"
            save_jpeg(seamless, output)
            with Image.open(output) as encoded:
                edge_error = _edge_error(encoded)
                band_error = _seam_band_error(encoded)
            worst = max(worst, edge_error)
            worst_band = max(worst_band, band_error)
            if number == 71 and sequence == 1:
                base_band = band_error
        if worst > 4.0:
            raise RuntimeError(f"Ocean {number:03d} failed edge continuity check: {worst:.2f}")
        if worst_band > 18.0:
            raise RuntimeError(f"Ocean {number:03d} retained a visible seam band: {worst_band:.2f}")
        if number == 71 and base_band > 2.0:
            raise RuntimeError(f"Base ocean tile retained a grid-forming vignette: {base_band:.2f}")
        counts[number] = len(boxes)
        edge_errors[number] = worst
        seam_band_errors[number] = worst_band
    return counts, edge_errors, seam_band_errors


def rebuild_ice() -> dict[int, int]:
    counts: dict[int, int] = {}
    for index, (number, file_id) in enumerate(sorted(ICE_DRIVE_FILE_IDS.items()), 1):
        print(f"Ice [{index}/{len(ICE_DRIVE_FILE_IDS)}] {number:03d}", flush=True)
        with Image.open(io.BytesIO(download_drive_image(file_id))) as opened:
            source = opened.convert("RGB")
        boxes = _separator_grid_boxes(source, ICE_COLUMNS, ICE_ROWS, ICE_INSET_FRACTION)
        expected = ICE_COLUMNS * ICE_ROWS
        if len(boxes) != expected:
            raise RuntimeError(f"Ice {number:03d} produced {len(boxes)} panels instead of {expected}")
        target = STAGE / "tilesets" / "world" / "terrain" / "ice" / f"ice-{number:03d}"
        for sequence, box in enumerate(boxes, 1):
            row = math.ceil(sequence / ICE_COLUMNS)
            column = ((sequence - 1) % ICE_COLUMNS) + 1
            clean = _square_crop(source.crop(box))
            output = target / f"tile-{row:02d}-{column:02d}.jpg"
            save_jpeg(clean, output)
            with Image.open(output) as encoded:
                if min(encoded.size) < 140:
                    raise RuntimeError(f"Ice {number:03d} generated an undersized panel: {encoded.size}")
        print(f"  -> {len(boxes)} whole panels ({ICE_COLUMNS}x{ICE_ROWS})", flush=True)
        counts[number] = len(boxes)
    return counts


def rewrite_catalog(
    plains_counts: dict[int, int],
    ocean_counts: dict[int, int],
    ice_counts: dict[int, int],
) -> None:
    rows = json.loads(CURRENT_CATALOG.read_text(encoding="utf-8"))
    repair_folders = {"plains", "ocean", "ice"}
    old = [row for row in rows if str(row.get("folder", "")).casefold() in repair_folders]
    keep = [row for row in rows if str(row.get("folder", "")).casefold() not in repair_folders]
    rebuilt: list[dict] = []

    for folder, counts in (("Plains", plains_counts), ("Ocean", ocean_counts), ("Ice", ice_counts)):
        slug = folder.casefold()
        for number, count in sorted(counts.items()):
            needle = f"/{slug}-{number:03d}/"
            source = next((row for row in old if needle in str(row.get("image", ""))), None)
            if source is None:
                raise RuntimeError(f"Catalog metadata unavailable for {folder} {number:03d}")
            base = str(source["image"]).rsplit("/", 1)[0]
            for sequence in range(1, count + 1):
                if folder in {"Ocean", "Ice"}:
                    columns = 6 if folder == "Ocean" else ICE_COLUMNS
                    row_number = math.ceil(sequence / columns)
                    column = ((sequence - 1) % columns) + 1
                else:
                    row_number = sequence
                    column = 1
                rebuilt.append(
                    {
                        "id": f"aws-{slug}-{number:03d}-{row_number:02d}-{column:02d}",
                        "name": f"{folder} {number:03d} · {row_number},{column}",
                        "image": f"{base}/tile-{row_number:02d}-{column:02d}.jpg",
                        "layer": source.get("layer", "WORLD"),
                        "directory": source.get("directory", "Terrain"),
                        "folder": source.get("folder", folder),
                        "author": source.get("author", "Ryan L. Cole / Shaelvien Drive"),
                    }
                )
    CURRENT_CATALOG.write_text(json.dumps(keep + rebuilt, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    plains_counts = rebuild_plains()
    ocean_counts, edge_errors, seam_band_errors = rebuild_ocean()
    ice_counts = rebuild_ice()
    rewrite_catalog(plains_counts, ocean_counts, ice_counts)
    print(
        f"Validated terrain repair: Plains {sum(plains_counts.values())} pieces; "
        f"Ocean {sum(ocean_counts.values())} seamless pieces; "
        f"Ice {sum(ice_counts.values())} whole pieces; "
        + ", ".join(
            f"Ocean {number:03d} edge={edge_errors[number]:.2f} band={seam_band_errors[number]:.2f}"
            for number in edge_errors
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
