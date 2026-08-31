from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TACTICAL = ROOT / "apps" / "tactical"
STAGE = ROOT / "build" / "aws-assets"


def main() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    (STAGE / "atlas").mkdir(parents=True)
    (STAGE / "cards").mkdir(parents=True)

    registry = json.loads(
        (TACTICAL / "data" / "atlas" / "atlas_asset_registry.json").read_text(
            encoding="utf-8"
        )
    )
    assets = []
    for item in registry.get("assets", []):
        if not item.get("enabled", True):
            continue
        source_path = TACTICAL / item.get("derivedPath", "")
        if not source_path.is_file():
            continue
        target = STAGE / "atlas" / source_path.name
        shutil.copy2(source_path, target)
        assets.append(
            {
                "id": item["assetId"],
                "name": item.get("name", item["assetId"]),
                "path": f"atlas/{target.name}",
            }
        )

    cards = json.loads(
        (TACTICAL / "data" / "tabletop" / "card_definitions.json").read_text(
            encoding="utf-8"
        )
    ).get("cards", [])
    (STAGE / "cards" / "cards.json").write_text(
        json.dumps(cards, indent=2), encoding="utf-8"
    )
    (STAGE / "atlas-manifest.json").write_text(
        json.dumps(assets, indent=2), encoding="utf-8"
    )
    print(f"Staged {len(assets)} Atlas assets + {len(cards)} cards; Naeja excluded")


if __name__ == "__main__":
    main()
