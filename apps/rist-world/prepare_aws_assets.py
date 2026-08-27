from __future__ import annotations

import json
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TACTICAL = ROOT / "apps" / "tactical"
STAGE = ROOT / "build" / "aws-assets"
NAEJA_URL = "https://drive.usercontent.google.com/download?id=1tESehBzxAPrugiE4gNL9Vsfc5Mmh0tCT&export=download&confirm=t"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def try_fetch_naeja() -> bytes | None:
    """Best-effort legacy import only. Google Drive must never block AWS staging."""
    try:
        request = urllib.request.Request(NAEJA_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            image = response.read()
        if len(image) < 300_000 or not image.startswith(PNG_MAGIC):
            print("Naeja legacy Drive source unavailable or not a PNG; skipping it without blocking AWS migration")
            return None
        return image
    except Exception as exc:
        print(f"Naeja legacy Drive source skipped: {type(exc).__name__}")
        return None


def main() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    (STAGE / "worlds" / "naeja").mkdir(parents=True)
    (STAGE / "atlas").mkdir(parents=True)
    (STAGE / "cards").mkdir(parents=True)

    image = try_fetch_naeja()
    if image is not None:
        (STAGE / "worlds" / "naeja" / "world.png").write_bytes(image)

    registry = json.loads((TACTICAL / "data" / "atlas" / "atlas_asset_registry.json").read_text(encoding="utf-8"))
    assets = []
    for item in registry.get("assets", []):
        if not item.get("enabled", True):
            continue
        source_path = TACTICAL / item.get("derivedPath", "")
        if not source_path.is_file():
            continue
        target = STAGE / "atlas" / source_path.name
        shutil.copy2(source_path, target)
        assets.append({"id": item["assetId"], "name": item.get("name", item["assetId"]), "path": f"atlas/{target.name}"})

    cards = json.loads((TACTICAL / "data" / "tabletop" / "card_definitions.json").read_text(encoding="utf-8")).get("cards", [])
    (STAGE / "cards" / "cards.json").write_text(json.dumps(cards, indent=2), encoding="utf-8")
    (STAGE / "atlas-manifest.json").write_text(json.dumps(assets, indent=2), encoding="utf-8")
    naeja_status = f"Naeja {len(image)} bytes" if image is not None else "Naeja deferred"
    print(f"Staged {naeja_status} + {len(assets)} Atlas assets + {len(cards)} cards")


if __name__ == "__main__":
    main()
