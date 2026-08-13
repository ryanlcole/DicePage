from __future__ import annotations

import base64
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TACTICAL = ROOT / "apps" / "tactical"
STAGE = ROOT / "build" / "aws-assets"


def main() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    (STAGE / "worlds" / "naeja").mkdir(parents=True)
    (STAGE / "atlas").mkdir(parents=True)
    (STAGE / "cards").mkdir(parents=True)

    source = (TACTICAL / "js" / "naeja_world_asset.js").read_text(encoding="utf-8")
    match = re.search(r"base64,(.*?)\";\s*$", source, flags=re.S)
    if not match:
        raise SystemExit("Naeja embedded source not found")
    image = base64.b64decode(re.sub(r"\s+", "", match.group(1)))
    if len(image) < 100_000:
        raise SystemExit(f"Naeja image unexpectedly small: {len(image)} bytes")
    (STAGE / "worlds" / "naeja" / "world.jpg").write_bytes(image)

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
    print(f"Staged Naeja + {len(assets)} Atlas assets + {len(cards)} cards")


if __name__ == "__main__":
    main()
