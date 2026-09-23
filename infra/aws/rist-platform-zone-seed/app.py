from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key


WORLD_ID = "shaelvien-geonaph-alpha-001"
WORLD_PK = f"WORLD#{WORLD_ID}"
ZONE_NAME = "The Sunken Tundra"
ZONE_MARKER = "sunken-tundra-v1"
GRID_COLUMNS = 30
GRID_ROWS = 30
PLACEMENT_WIDTH_FRACTION = Decimal("0.12")
ZONE_SIZE = (Decimal(1) / Decimal(GRID_COLUMNS)) / PLACEMENT_WIDTH_FRACTION

LAYERS = (
    (0, "Abyss Floor", "00-abyss-floor.webp"),
    (1, "Vent Currents", "01-vent-currents.webp"),
    (2, "Floating Ruins", "02-floating-ruins.webp"),
    (3, "Biolume Gardens", "03-biolume-gardens.webp"),
    (4, "Current Fauna", "04-current-fauna.webp"),
    (5, "Shallow Shelf", "05-shallow-shelf.webp"),
    (6, "Sea Surface", "06-sea-surface.webp"),
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalized_name(value) -> str:
    return " ".join(str(value or "").strip().lower().split())


def region_name(region_item: dict) -> str:
    state = region_item.get("state") if isinstance(region_item.get("state"), dict) else {}
    return str(state.get("name") or "")


def region_is_empty(region_item: dict, world_layers: list, region_id: str) -> bool:
    state = region_item.get("state") if isinstance(region_item.get("state"), dict) else {}
    if state.get("sourceTiles") or state.get("overlayTiles"):
        return False
    return not any(
        isinstance(layer, dict) and str(layer.get("regionId") or "") == region_id
        for layer in world_layers
    )


def query_world_prefix(table, prefix: str) -> list[dict]:
    result = table.query(
        KeyConditionExpression=Key("pk").eq(WORLD_PK) & Key("sk").begins_with(prefix),
        ConsistentRead=True,
    )
    items = list(result.get("Items") or [])
    while result.get("LastEvaluatedKey"):
        result = table.query(
            KeyConditionExpression=Key("pk").eq(WORLD_PK) & Key("sk").begins_with(prefix),
            ExclusiveStartKey=result["LastEvaluatedKey"],
            ConsistentRead=True,
        )
        items.extend(result.get("Items") or [])
    return items


class SeedPrerequisiteUnavailable(RuntimeError):
    """Optional artwork seed waits for an explicitly owned empty parcel."""


def choose_target(table, owner_user_id: str, world_layers: list):
    parcels = [
        item
        for item in query_world_prefix(table, "PARCEL#")
        if str(item.get("ownerUserId") or "") == owner_user_id
    ]
    if not parcels:
        raise SeedPrerequisiteUnavailable("No owner Shaelvien parcel exists to receive The Sunken Tundra.")

    exact = []
    empty = []
    for parcel in parcels:
        region_id = str(parcel.get("regionId") or "")
        if not region_id:
            continue
        region_item = table.get_item(
            Key={"pk": WORLD_PK, "sk": "REGION#" + region_id},
            ConsistentRead=True,
        ).get("Item")
        if not region_item:
            continue

        names = {
            normalized_name(parcel.get("displayName")),
            normalized_name(region_name(region_item)),
        }
        if normalized_name(ZONE_NAME) in names or "sunken tundra" in names:
            exact.append((parcel, region_item))
        elif region_is_empty(region_item, world_layers, region_id):
            empty.append((parcel, region_item))

    pool = exact or empty
    if not pool:
        raise SeedPrerequisiteUnavailable(
            "No empty owner parcel is available. Refusing to overwrite authored Shaelvien content."
        )

    pool.sort(
        key=lambda pair: (
            str(pair[0].get("claimedAtUtc") or ""),
            int(pair[0].get("cellIndex") or 0),
        ),
        reverse=True,
    )
    return pool[0]


def build_layers(parcel: dict, asset_base_url: str) -> list[dict]:
    column = int(parcel.get("column") or 0)
    row = int(parcel.get("row") or 0)
    x = (Decimal(column) + Decimal("0.5")) / Decimal(GRID_COLUMNS)
    y = (Decimal(row) + Decimal("0.5")) / Decimal(GRID_ROWS)
    region_id = str(parcel["regionId"])
    base = asset_base_url.rstrip("/")

    return [
        {
            "id": f"sunken-tundra:{region_id}:layer-{layer_index}",
            "regionId": region_id,
            "assetId": f"zone:sunken-tundra:{layer_index}",
            "name": name,
            "libraryTile": False,
            "kind": "image",
            "originalSrc": f"{base}/{filename}",
            "transparentSrc": f"{base}/{filename}",
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
        for layer_index, name, filename in LAYERS
    ]


def seed_zone(table, owner_user_id: str, asset_base_url: str) -> dict:
    source_key = {"pk": WORLD_PK, "sk": "WORLDSOURCE"}
    source_item = table.get_item(Key=source_key, ConsistentRead=True).get("Item")
    if not source_item or not isinstance(source_item.get("state"), dict):
        raise SeedPrerequisiteUnavailable(
            "Canonical Geonaph WORLDSOURCE is missing; refusing to invent a replacement world map."
        )

    source_state = dict(source_item["state"])
    markers = dict(source_state.get("migrationMarkers") or {})
    existing_layers = (
        list(source_state.get("userLayers") or [])
        if isinstance(source_state.get("userLayers"), list)
        else []
    )

    if markers.get(ZONE_MARKER):
        seeded = [
            layer
            for layer in existing_layers
            if isinstance(layer, dict)
            and str(layer.get("id") or "").startswith("sunken-tundra:")
        ]
        if len(seeded) == len(LAYERS):
            region_id = str(seeded[0].get("regionId") or "")
            return {
                "seeded": False,
                "alreadySeeded": True,
                "regionId": region_id,
                "layerCount": len(seeded),
            }

    parcel, region_item = choose_target(table, owner_user_id, existing_layers)
    region_id = str(parcel["regionId"])
    zone_layers = build_layers(parcel, asset_base_url)

    source_state["userLayers"] = [
        layer
        for layer in existing_layers
        if not (
            isinstance(layer, dict)
            and (
                str(layer.get("regionId") or "") == region_id
                or str(layer.get("id") or "").startswith("sunken-tundra:")
            )
        )
    ] + zone_layers
    markers[ZONE_MARKER] = {
        "regionId": region_id,
        "seededAtUtc": utc_stamp(),
        "surfaceTier": 0,
        "surfaceLayer": 6,
    }
    source_state["migrationMarkers"] = markers
    source_state["savedAt"] = utc_stamp()

    parcel["displayName"] = ZONE_NAME

    region_state = dict(region_item.get("state") or {})
    region_state["name"] = ZONE_NAME
    region_state["tierIndex"] = 0
    region_state["updatedAtUtc"] = utc_stamp()
    region_item["state"] = region_state
    region_item["updatedAt"] = int(time.time())

    source_item["state"] = source_state
    source_item["entityType"] = str(source_item.get("entityType") or "worldMap")
    source_item["worldId"] = WORLD_ID
    source_item["updatedAtUtc"] = utc_stamp()
    source_item["updatedByUserId"] = owner_user_id

    # Preserve the existing claim geometry and all unrelated world data. Only the
    # selected empty owner parcel, its derived region name, and its canonical
    # world-source layers are changed.
    table.put_item(Item=parcel)
    table.put_item(Item=region_item)
    table.put_item(Item=source_item)

    verify = table.get_item(Key=source_key, ConsistentRead=True).get("Item") or {}
    verify_state = verify.get("state") if isinstance(verify.get("state"), dict) else {}
    verify_layers = [
        layer
        for layer in (verify_state.get("userLayers") or [])
        if isinstance(layer, dict) and str(layer.get("regionId") or "") == region_id
    ]
    if len(verify_layers) != len(LAYERS):
        raise RuntimeError(
            f"Sunken Tundra verification failed: expected {len(LAYERS)} layers, "
            f"found {len(verify_layers)}."
        )

    return {
        "seeded": True,
        "alreadySeeded": False,
        "regionId": region_id,
        "parcelId": str(parcel.get("parcelId") or ""),
        "column": int(parcel.get("column") or 0),
        "row": int(parcel.get("row") or 0),
        "layerCount": len(verify_layers),
        "surfaceTier": 0,
        "surfaceLayer": 6,
        "connectedToEndemarByClaimLattice": True,
    }


def send_cloudformation_response(event, context, status: str, data: dict, reason: str = ""):
    body = {
        "Status": status,
        "Reason": reason or f"See CloudWatch Log Stream: {context.log_stream_name}",
        "PhysicalResourceId": str(event.get("PhysicalResourceId") or "sunken-tundra-zone-seed-v1"),
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "NoEcho": False,
        "Data": data,
    }
    encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        event["ResponseURL"],
        data=encoded,
        method="PUT",
        headers={"content-type": "", "content-length": str(len(encoded))},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()


def handler(event, context):
    if event.get("RequestType") == "Delete":
        send_cloudformation_response(event, context, "SUCCESS", {"deleted": False})
        return

    try:
        table = boto3.resource("dynamodb").Table(os.environ["WORLD_TABLE"])
        owner_user_id = str(os.environ.get("OWNER_USER_ID") or "").strip()
        asset_base_url = str(os.environ.get("ASSET_BASE_URL") or "").strip()
        if not owner_user_id:
            raise RuntimeError("OWNER_USER_ID is required for the Sunken Tundra seed.")
        if not asset_base_url.startswith("https://"):
            raise RuntimeError("ASSET_BASE_URL must be an HTTPS URL.")

        result = seed_zone(table, owner_user_id, asset_base_url)
        print(json.dumps(result, sort_keys=True))
        send_cloudformation_response(event, context, "SUCCESS", result)
    except SeedPrerequisiteUnavailable as exc:
        # Optional artwork must never block deploying map permission fixes or
        # fabricate an owner parcel. This is explicitly deferred, not seeded;
        # a future deliberate Revision change can retry after prerequisites exist.
        result = {"seeded": False, "deferred": True, "reason": str(exc)}
        print(f"Sunken Tundra seed deferred: {exc}")
        send_cloudformation_response(event, context, "SUCCESS", result)
    except Exception as exc:
        print(f"Sunken Tundra seed failed: {exc}")
        send_cloudformation_response(
            event,
            context,
            "FAILED",
            {"error": str(exc)},
            reason=str(exc)[:900],
        )
