from __future__ import annotations

import json
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TACTICAL = ROOT / "apps" / "tactical"
STAGE = ROOT / "build" / "aws-assets"
NAEJA_URL = "https://drive.usercontent.google.com/download?id=1tESehBzxAPrugiE4gNL9Vsfc5Mmh0tCT&export=download&confirm=t"


def fetch_naeja() -> bytes:
    request = urllib.request.Request(NAEJA_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        image = response.read()
    if len(image) < 300_000:
        raise SystemExit(f"Naeja download unexpectedly small: {len(image)} bytes")
    if not image.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit("Naeja Drive download is not a PNG")
    return image


def main() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    (STAGE / "worlds" / "naeja").mkdir(parents=True)
    (STAGE / "atlas").mkdir(parents=True)
    (STAGE / "cards").mkdir(parents=True)

    image = fetch_naeja()
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
    print(f"Staged Naeja {len(image)} bytes + {len(assets)} Atlas assets + {len(cards)} cards")


if __name__ == "__main__":
    main()
