from __future__ import annotations

import io
import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CURRENT_CATALOG = ROOT / "apps" / "rist-world" / "wwwroot" / "assets" / "drive-tiles" / "catalog.json"
STAGE = ROOT / "build" / "plains-repair"
HISTORICAL_REF = "a816797c826fb622bdf82306d5a887db79668e68"
HISTORICAL_CATALOG = "apps/rist-world/wwwroot/assets/drive-tiles/catalog.json"
PLAIN_NAME = re.compile(r"^Plains\s+(\d+)$", re.IGNORECASE)
CURRENT_SET = re.compile(r"/plains/plains-(\d+)/tile-\d+-\d+\.(?:png|jpe?g|webp)$", re.IGNORECASE)


def historical_catalog() -> list[dict]:
    raw = subprocess.check_output(
        ["git", "show", f"{HISTORICAL_REF}:{HISTORICAL_CATALOG}"],
        cwd=ROOT,
        text=True,
    )
    return json.loads(raw)


def source_rows() -> dict[int, dict]:
    found: dict[int, dict] = {}
    for item in historical_catalog():
        if str(item.get("folder", "")).casefold() != "plains":
            continue
        match = PLAIN_NAME.match(str(item.get("name", "")).strip())
        if not match:
            raise RuntimeError(f"Unrecognized historical Plains name: {item.get('name')!r}")
        number = int(match.group(1))
        if number in found:
            raise RuntimeError(f"Duplicate historical Plains set: {number:03d}")
        if not item.get("image"):
            raise RuntimeError(f"Historical Plains {number:03d} has no source image URL")
        found[number] = item
    if not found:
        raise RuntimeError("No historical Plains source sheets found")
    return found


def current_set_numbers() -> set[int]:
    rows = json.loads(CURRENT_CATALOG.read_text(encoding="utf-8"))
    result: set[int] = set()
    for item in rows:
        if str(item.get("folder", "")).casefold() != "plains":
            continue
        match = CURRENT_SET.search(str(item.get("image", "")))
        if match:
            result.add(int(match.group(1)))
    return result


def download(url: str, attempts: int = 4) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 RIST-Asset-Repair/1.0",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
            if len(data) < 1024:
                raise RuntimeError(f"Downloaded source is unexpectedly small ({len(data)} bytes)")
            return data
        except Exception as exc:  # network failures are retried, never partially published
            last = exc
            if attempt < attempts:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Unable to download source after {attempts} attempts: {last}") from last


def cut_sheet(number: int, payload: bytes) -> int:
    with Image.open(io.BytesIO(payload)) as opened:
        image = opened.convert("RGB")
    width, height = image.size
    if min(width, height) < 192:
        raise RuntimeError(f"Plains {number:03d} source is too small: {width}x{height}")
    if abs(width - height) > max(width, height) * 0.08:
        raise RuntimeError(f"Plains {number:03d} source is not a standard square atlas: {width}x{height}")

    target = STAGE / f"plains-{number:03d}"
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    for row in range(6):
        y0 = round(row * height / 6)
        y1 = round((row + 1) * height / 6)
        for col in range(6):
            x0 = round(col * width / 6)
            x1 = round((col + 1) * width / 6)
            tile = image.crop((x0, y0, x1, y1))
            output = target / f"tile-{row + 1:02d}-{col + 1:02d}.jpg"
            tile.save(output, "JPEG", quality=95, subsampling=0, optimize=True)
            if output.stat().st_size < 1000:
                raise RuntimeError(f"Plains {number:03d} generated an unexpectedly small cut: {output.name}")
            count += 1
    return count


def validate_stage(expected_sets: set[int]) -> None:
    actual_dirs = {int(path.name.rsplit("-", 1)[1]) for path in STAGE.glob("plains-*") if path.is_dir()}
    if actual_dirs != expected_sets:
        raise RuntimeError(f"Staged Plains set mismatch. Expected {sorted(expected_sets)}, got {sorted(actual_dirs)}")
    for number in sorted(expected_sets):
        files = sorted((STAGE / f"plains-{number:03d}").glob("tile-??-??.jpg"))
        if len(files) != 36:
            raise RuntimeError(f"Plains {number:03d} staged {len(files)} cuts instead of 36")
        with Image.open(files[0]) as test:
            if abs(test.width - test.height) > max(test.width, test.height) * 0.08:
                raise RuntimeError(f"Plains {number:03d} first cut is not square-ish: {test.size}")


def main() -> None:
    sources = source_rows()
    current = current_set_numbers()
    historical = set(sources)
    if current != historical:
        missing_from_history = sorted(current - historical)
        missing_from_current = sorted(historical - current)
        raise RuntimeError(
            "Refusing partial Plains repair: current/historical set inventories differ. "
            f"Only current={missing_from_history}; only historical={missing_from_current}"
        )

    if STAGE.exists():
        import shutil
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    total = 0
    for index, number in enumerate(sorted(sources), 1):
        print(f"[{index}/{len(sources)}] Recovering Plains {number:03d}", flush=True)
        payload = download(str(sources[number]["image"]))
        cuts = cut_sheet(number, payload)
        if cuts != 36:
            raise RuntimeError(f"Plains {number:03d} generated {cuts} cuts instead of 36")
        total += cuts

    validate_stage(historical)
    print(f"Validated complete Plains repair: {len(historical)} sets, {total} cuts", flush=True)


if __name__ == "__main__":
    main()
