from __future__ import annotations

import base64
import io
import json
import re
import subprocess
import urllib.parse
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
MESSAGE_ID = re.compile(r"m_[0-9a-f]+", re.IGNORECASE)

DRIVE_FILE_IDS = {
    "m_6a730f972aa4819181d970a49b2f703a": "1F2sumHWgnB72leECCIaSPjCbQNbMfiti",
    "m_6a7329921bb8819185c10151199733ce": "1k3iRpL0vpA0yIqfWZQv4eetq0MmETVX0",
    "m_6a73408f3704819197ceb7efa243dbd1": "1BbzddzEAUjVYr-neEwcD9VdVsHQx9h4B",
    "m_6a733ef362148191a93398fa0088b325": "19b_pM1K16OS52hsw-eNUWGVVP2MdrO29",
    "m_6a733fe6ecd88191927a2a3dd86b55b6": "15hPtHJ-elzs9TF3FuqdKeU3uRpanESZz",
    "m_6a7342f9a4b881918fcf1245ad925f47": "1kDx3jKhFvkjuWpL3BBRiGk12ys6jc7GH",
    "m_6a73424896ac8191b75d8ed17e0e7a84": "1odZHuqsYVOd6w21WYepT46Baa71-IuGL",
    "m_6a734175ce4c81918f68acf2c3389ec4": "1rgSz7MvikjGkKhH7uJLHMLYXbgWJZkob",
    "m_6a7343e2099c8191845ada585e998b23": "1XSN5deJuTfX9XP5K61SJwTECauCyuICa",
    "m_6a7345cae2d08191ac5178e71c347bea": "14eUjrCH0f4rnDXsx5aMlqdv1F6z7z1-2",
    "m_6a73471c05248191b09bdeb47a5b161b": "1jEUwWMvHsp_L94PzFNcqUpsiv8rF2miY",
    "m_6a73465dabdc819195323acd2d0fbb59": "1Xe5mNHOAfjEI9EFuRY0AqxUh1Ah32EK2",
    "m_6a7347d178488191aa2e996739e68336": "1nJJ8slhqNaMK56bP7Inz6rMw_MmypFrO",
    "m_6a734beb63388191bf39874f1531cc85": "1JxYL9KXnOK54lipH57cbUPA6NmVVyjET",
    "m_6a73488645b4819180c5cd90f2a2affd": "10Ud2eMjVowEIOFsfFjPpAFPBAE32sjJE",
    "m_6a7349f84ecc8191a135f2a462af489c": "1mrES0JBByMDlADMOPmqRc-eDPmiutI5c",
    "m_6a734967e638819180b1522ce516bdd3": "1I5xfFrSM9xVmZxJWJWr8ZAGXrZ-7Tl9a",
    "m_6a734ca2529c8191aea0189dfe655384": "1pENPMJE3pDIWKrS2z4o8SpGNUQbBMzTD",
    "m_6a734d604b408191ad6a8cf6768450e0": "1Dp-ZbgcXjCM32bcFdYMGNcGOQgmCC19S",
    "m_6a734f2fc7088191aa341e335d3f4d3e": "1mrfiuXuV00vrvLjD9svdFqv5Fg7vY7iJ",
    "m_6a734eabe4308191a81af6a41a8d4729": "1dSRlczShzDXB_dw8g0WG8S9r4MELwPql",
    "m_6a7350abc0a4819184daf1e563353f10": "1rDb_ZnGHjk8gZtTEl0kYjATskPKXcamj",
    "m_6a734fe59adc81918795c7fe56d01b64": "1xr40w4JMItyK0i-8znn15dYFOzQRKvHz",
    "m_6a736959ab648191b35e320a8e34faa7": "1kfjE2OojKTSNwBPo4JQD9pUeyyKQqNLK",
    "m_6a73770d56788191aa2dfdbdb6044941": "1hDDm-0eoEkDYKOksaT9gmlhZxn20R1SK",
    "m_6a7377de439c8191ae612a0d41ce16e8": "1ihRl9Gz-WRou-XTKv_c9IEi7Q4CbDtQZ",
    "m_6a737991105481919442afaf83fc47b9": "17qSH0oZ5jYE_o3ma9GRlmoi65LZlo7zJ",
    "m_6a737a3001d481919ea3dfe8ba15f89b": "1OAY23V-ANg0XcwemLA1igRlEqP9TVq_3",
    "m_6a73789e2ffc819185b6bd9f1776d202": "1qiJ7UyE_h7QWA9TjKHz9n7CG5gLAl33E",
    "m_6a739928000c8191ac514e2a1f8c9d23": "1EsoVMCBpRnWgS9_8aVNIaA8Wozzws9zx",
    "m_6a739a197b848191b77eaac2010be9fe": "17iD8EALrwEQkEU-6dytfFOCAF9q37fwZ",
    "m_6a73999ef81081919dcf8feed13ee85e": "14pHLJXYoHCO8xzBX5gERdShvCpux1bg3",
}


def historical_catalog() -> list[dict]:
    raw = subprocess.check_output(["git", "show", f"{HISTORICAL_REF}:{HISTORICAL_CATALOG}"], cwd=ROOT, text=True)
    return json.loads(raw)


def source_rows() -> dict[int, dict]:
    found: dict[int, dict] = {}
    for item in historical_catalog():
        if str(item.get("folder", "")).casefold() != "plains":
            continue
        match = PLAIN_NAME.match(str(item.get("name", "")).strip())
        if not match:
            raise RuntimeError(f"Unrecognized historical Plains name: {item.get('name')!r}")
        found[int(match.group(1))] = item
    if not found:
        raise RuntimeError("No historical Plains source sheets found")
    return found


def current_set_numbers() -> set[int]:
    rows = json.loads(CURRENT_CATALOG.read_text(encoding="utf-8"))
    result: set[int] = set()
    for item in rows:
        if str(item.get("folder", "")).casefold() == "plains":
            match = CURRENT_SET.search(str(item.get("image", "")))
            if match:
                result.add(int(match.group(1)))
    return result


def historical_message_id(url: str) -> str:
    marker = "/enc/"
    if marker not in url:
        raise RuntimeError("Historical source has no encoded identity")
    token = url.split(marker, 1)[1].split("?", 1)[0].split("/", 1)[0]
    token += "=" * (-len(token) % 4)
    payload = json.loads(base64.urlsafe_b64decode(token).decode("utf-8"))
    match = MESSAGE_ID.search(str(payload.get("id", "")))
    if not match:
        raise RuntimeError("Historical source identity contains no message ID")
    return match.group(0).lower()


def candidate_urls(file_id: str) -> list[str]:
    fid = urllib.parse.quote(file_id, safe="")
    return [
        f"https://drive.google.com/uc?export=download&id={fid}&confirm=t",
        f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",
        f"https://lh3.googleusercontent.com/d/{fid}=s0",
        f"https://drive.google.com/thumbnail?id={fid}&sz=w4096",
    ]


def fetch_candidate(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 RIST-Asset-Repair/1.0", "Accept": "image/*,*/*;q=0.8"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read(), response.headers.get("Content-Type", "")


def download_original(file_id: str) -> bytes:
    failures: list[str] = []
    for url in candidate_urls(file_id):
        try:
            data, content_type = fetch_candidate(url)
            if len(data) < 1024 or "text/html" in content_type.casefold():
                failures.append(f"{url}: {content_type} {len(data)} bytes")
                continue
            with Image.open(io.BytesIO(data)) as probe:
                width, height, fmt = probe.width, probe.height, probe.format
            print(f"  candidate {url.split('?')[0]} -> {width}x{height} {fmt} {len(data)} bytes", flush=True)
            if width == height and width >= 600:
                return data
            failures.append(f"{url}: alternate representation {width}x{height}")
        except Exception as exc:
            failures.append(f"{url}: {type(exc).__name__}: {exc}")
    raise RuntimeError("No endpoint returned the original square atlas. " + " | ".join(failures))


def cut_sheet(number: int, payload: bytes) -> int:
    with Image.open(io.BytesIO(payload)) as opened:
        image = opened.convert("RGB")
    width, height = image.size
    if width != height or width < 600:
        raise RuntimeError(f"Plains {number:03d} is not the canonical square atlas: {width}x{height}")
    target = STAGE / f"plains-{number:03d}"
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    for row in range(6):
        y0, y1 = round(row * height / 6), round((row + 1) * height / 6)
        for col in range(6):
            x0, x1 = round(col * width / 6), round((col + 1) * width / 6)
            output = target / f"tile-{row + 1:02d}-{col + 1:02d}.jpg"
            image.crop((x0, y0, x1, y1)).save(output, "JPEG", quality=95, subsampling=0, optimize=True)
            if output.stat().st_size < 1000:
                raise RuntimeError(f"Plains {number:03d} generated a tiny cut: {output.name}")
            count += 1
    return count


def validate_stage(expected_sets: set[int]) -> None:
    actual = {int(p.name.rsplit("-", 1)[1]) for p in STAGE.glob("plains-*") if p.is_dir()}
    if actual != expected_sets:
        raise RuntimeError(f"Staged Plains mismatch. Expected {sorted(expected_sets)}, got {sorted(actual)}")
    for number in sorted(expected_sets):
        if len(list((STAGE / f"plains-{number:03d}").glob("tile-??-??.jpg"))) != 36:
            raise RuntimeError(f"Plains {number:03d} did not stage exactly 36 cuts")


def main() -> None:
    sources = source_rows()
    historical = set(sources)
    current = current_set_numbers()
    if current != historical:
        raise RuntimeError(f"Refusing partial repair; current={sorted(current)}, historical={sorted(historical)}")
    source_ids = {historical_message_id(str(item["image"])) for item in sources.values()}
    if source_ids != set(DRIVE_FILE_IDS):
        raise RuntimeError("Canonical Drive source inventory does not exactly match historical Plains inventory")

    if STAGE.exists():
        import shutil
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    total = 0
    for index, number in enumerate(sorted(sources), 1):
        message_id = historical_message_id(str(sources[number]["image"]))
        print(f"[{index}/{len(sources)}] Plains {number:03d} / {message_id}", flush=True)
        total += cut_sheet(number, download_original(DRIVE_FILE_IDS[message_id]))

    validate_stage(historical)
    print(f"Validated complete Plains repair: {len(historical)} sets, {total} cuts", flush=True)


if __name__ == "__main__":
    main()
