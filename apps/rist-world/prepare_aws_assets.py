from __future__ import annotations

import base64
import json
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
    marker = "base64,"
    start = source.find(marker)
    if start < 0:
        raise SystemExit("Naeja embedded source not found: base64 marker missing")
    start += len(marker)
    end = source.find('"', start)
    if end < 0:
        raise SystemExit("Naeja embedded source not found: closing quote missing")
    payload = "".join(source[start:end].split())
    try:
        image = base64.b64decode(payload, validate=True)
    except Exception as exc:
        raise SystemExit(f"Naeja base64 decode failed: {exc}") from exc
    if len(image) < 100_000:
        raise SystemExit(f"Naeja image unexpectedly small: {len(image)} bytes")
    if not image.startswith(b"\xff\xd8\xff"):
        raise SystemExit("Naeja decoded payload is not a JPEG")
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
