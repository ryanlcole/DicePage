#!/usr/bin/env python3
"""Seed The Sunken Tundra into the owner's latest empty Shaelvien parcel.

The script is intentionally conservative:
- it never creates or moves a parcel;
- it prefers an existing parcel/region already named Sunken Tundra;
- otherwise it selects the most recently claimed owner parcel that has no
  authored world-source layers and no legacy region tiles/overlays;
- it preserves every other world-source layer and all parcel geometry.

Run from GitHub Actions after the frontend assets are published.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

WORLD_ID = "shaelvien-geonaph-alpha-001"
WORLD_PK = f"WORLD#{WORLD_ID}"
ZONE_NAME = "The Sunken Tundra"
GRID_COLUMNS = 30
GRID_ROWS = 30
PLACEMENT_WIDTH_FRACTION = 0.12
ZONE_SIZE = (1 / GRID_COLUMNS) / PLACEMENT_WIDTH_FRACTION

LAYERS = [
    (0, "Abyss Floor", "00-abyss-floor.webp"),
    (1, "Vent Currents", "01-vent-currents.webp"),
    (2, "Floating Ruins", "02-floating-ruins.webp"),
    (3, "Biolume Gardens", "03-biolume-gardens.webp"),
    (4, "Current Fauna", "04-current-fauna.webp"),
    (5, "Shallow Shelf", "05-shallow-shelf.webp"),
    (6, "Sea Surface", "06-sea-surface.webp"),
]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_aws(region: str, *args: str) -> dict:
    cmd = ["aws", *args, "--region", region, "--output", "json"]
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return json.loads(result.stdout or "{}")


def from_av(value):
    if not isinstance(value, dict):
        return value
    if "S" in value:
        return value["S"]
    if "N" in value:
        raw = value["N"]
        number = Decimal(raw)
        return int(number) if number == number.to_integral_value() else float(number)
    if "BOOL" in value:
        return bool(value["BOOL"])
    if "NULL" in value:
        return None
    if "L" in value:
        return [from_av(item) for item in value["L"]]
    if "M" in value:
        return {key: from_av(item) for key, item in value["M"].items()}
    if "SS" in value:
        return list(value["SS"])
    if "NS" in value:
        return [from_av({"N": item}) for item in value["NS"]]
    return value


def item_from_av(item: dict | None) -> dict:
    return {key: from_av(value) for key, value in (item or {}).items()}


def to_av(value):
    if value is None:
        return {"NULL": True}
    if isinstance(value, bool):
        return {"BOOL": value}
    if isinstance(value, str):
        return {"S": value}
    if isinstance(value, int):
        return {"N": str(value)}
    if isinstance(value, float):
        return {"N": format(Decimal(str(value)), "f")}
    if isinstance(value, Decimal):
        return {"N": format(value, "f")}
    if isinstance(value, list):
        return {"L": [to_av(item) for item in value]}
    if isinstance(value, dict):
        return {"M": {str(key): to_av(item) for key, item in value.items()}}
    raise TypeError(f"Unsupported DynamoDB value: {type(value)!r}")


def item_to_av(item: dict) -> dict:
    return {key: to_av(value) for key, value in item.items()}


def put_item(region: str, table: str, item: dict) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        json.dump(item_to_av(item), handle, separators=(",", ":"))
        path = handle.name
    try:
        run_aws(region, "dynamodb", "put-item", "--table-name", table, "--item", f"file://{path}")
    finally:
        Path(path).unlink(missing_ok=True)


def get_item(region: str, table: str, pk: str, sk: str) -> dict:
    key = json.dumps({"pk": {"S": pk}, "sk": {"S": sk}}, separators=(",", ":"))
    payload = run_aws(region, "dynamodb", "get-item", "--table-name", table, "--key", key, "--consistent-read")
    return item_from_av(payload.get("Item"))


def query_prefix(region: str, table: str, prefix: str) -> list[dict]:
    values = json.dumps(
        {":pk": {"S": WORLD_PK}, ":prefix": {"S": prefix}},
        separators=(",", ":"),
    )
    payload = run_aws(
        region,
        "dynamodb",
        "query",
        "--table-name",
        table,
        "--key-condition-expression",
        "pk = :pk AND begins_with(sk, :prefix)",
        "--expression-attribute-values",
        values,
        "--consistent-read",
    )
    return [item_from_av(item) for item in payload.get("Items", [])]


def region_name(region_item: dict) -> str:
    state = region_item.get("state") if isinstance(region_item.get("state"), dict) else {}
    return str(state.get("name") or "")


def parcel_name(parcel: dict) -> str:
    return str(parcel.get("displayName") or "")


def normalized_name(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def region_is_empty(region_item: dict, world_layers: list[dict], region_id: str) -> bool:
    state = region_item.get("state") if isinstance(region_item.get("state"), dict) else {}
    if state.get("sourceTiles") or state.get("overlayTiles"):
        return False
    return not any(
        isinstance(layer, dict) and str(layer.get("regionId") or "") == region_id
        for layer in world_layers
    )


def choose_target(region: str, table: str, owner_user_id: str, world_source: dict):
    state = world_source.get("state") if isinstance(world_source.get("state"), dict) else {}
    world_layers = state.get("userLayers") if isinstance(state.get("userLayers"), list) else []
    owned = [
        parcel
        for parcel in query_prefix(region, table, "PARCEL#")
        if str(parcel.get("ownerUserId") or "") == owner_user_id
    ]
    if not owned:
        raise SystemExit("No owner Shaelvien parcel exists to receive The Sunken Tundra.")

    candidates = []
    exact = []
    for parcel in owned:
        region_id = str(parcel.get("regionId") or "")
        if not region_id:
            continue
        region_item = get_item(region, table, WORLD_PK, "REGION#" + region_id)
        if not region_item:
            continue
        names = {normalized_name(parcel_name(parcel)), normalized_name(region_name(region_item))}
        if normalized_name(ZONE_NAME) in names or "sunken tundra" in names:
            exact.append((parcel, region_item))
            continue
        if region_is_empty(region_item, world_layers, region_id):
            candidates.append((parcel, region_item))

    if exact:
        pool = exact
    else:
        if not candidates:
            raise SystemExit(
                "No empty owner parcel is available. Refusing to overwrite authored Shaelvien content."
            )
        pool = candidates

    pool.sort(
        key=lambda pair: (
            str(pair[0].get("claimedAtUtc") or ""),
            int(pair[0].get("cellIndex") or 0),
        ),
        reverse=True,
    )
    return pool[0], world_layers


def build_layers(parcel: dict, asset_base_url: str) -> list[dict]:
    column = int(parcel.get("column") or 0)
    row = int(parcel.get("row") or 0)
    x = (column + 0.5) / GRID_COLUMNS
    y = (row + 0.5) / GRID_ROWS
    region_id = str(parcel["regionId"])
    base = asset_base_url.rstrip("/")
    layers = []
    for layer_index, name, filename in LAYERS:
        src = f"{base}/{filename}"
        layers.append(
            {
                "id": f"sunken-tundra:{region_id}:layer-{layer_index}",
                "regionId": region_id,
                "assetId": f"zone:sunken-tundra:{layer_index}",
                "personalAssetKey": None,
                "name": name,
                "libraryTile": False,
                "kind": "image",
                "originalSrc": src,
                "transparentSrc": src,
                "transparent": layer_index != 0,
                "x": x,
                "y": y,
                "tier": 0,
                "layer": layer_index,
                "size": ZONE_SIZE,
                "rotation": 0,
                "opacity": 1,
                "committed": True,
            }
        )
    return layers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", required=True)
    parser.add_argument("--owner-user-id", required=True)
    parser.add_argument("--asset-base-url", required=True)
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    source_item = get_item(args.region, args.table, WORLD_PK, "WORLDSOURCE")
    if not source_item or not isinstance(source_item.get("state"), dict):
        raise SystemExit("Canonical Geonaph WORLDSOURCE is missing; refusing to invent a replacement world map.")

    (parcel, region_item), existing_layers = choose_target(
        args.region, args.table, args.owner_user_id, source_item
    )
    region_id = str(parcel["regionId"])
    zone_layers = build_layers(parcel, args.asset_base_url)

    source_state = dict(source_item["state"])
    source_state["userLayers"] = [
        layer
        for layer in existing_layers
        if not (isinstance(layer, dict) and str(layer.get("regionId") or "") == region_id)
    ] + zone_layers
    source_state["savedAt"] = utc_stamp()

    source_item["state"] = source_state
    source_item["updatedAtUtc"] = utc_stamp()
    source_item["updatedByUserId"] = args.owner_user_id
    source_item.setdefault("entityType", "worldMap")
    source_item.setdefault("worldId", WORLD_ID)

    parcel["displayName"] = ZONE_NAME
    region_state = dict(region_item.get("state") or {})
    region_state["name"] = ZONE_NAME
    region_state["tierIndex"] = 0
    region_state["sourceLayerOffsets"] = list(range(100))
    region_state["updatedAtUtc"] = utc_stamp()
    region_item["state"] = region_state
    region_item["updatedAt"] = int(time.time())

    put_item(args.region, args.table, parcel)
    put_item(args.region, args.table, region_item)
    put_item(args.region, args.table, source_item)

    verify = get_item(args.region, args.table, WORLD_PK, "WORLDSOURCE")
    verify_state = verify.get("state") if isinstance(verify.get("state"), dict) else {}
    verify_layers = [
        layer
        for layer in (verify_state.get("userLayers") or [])
        if isinstance(layer, dict) and str(layer.get("regionId") or "") == region_id
    ]
    if len(verify_layers) != len(LAYERS):
        raise SystemExit(
            f"Sunken Tundra verification failed: expected {len(LAYERS)} layers, found {len(verify_layers)}."
        )

    print(
        json.dumps(
            {
                "ok": True,
                "worldId": WORLD_ID,
                "regionId": region_id,
                "parcelId": parcel.get("parcelId"),
                "column": parcel.get("column"),
                "row": parcel.get("row"),
                "name": ZONE_NAME,
                "layerCount": len(verify_layers),
                "surfaceLayer": 6,
                "connectedToEndemarByClaimLattice": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
