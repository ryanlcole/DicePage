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
ZONE_NAME = "Geanaph"
ZONE_MARKER = "geanaph-east-v2"
GRID_COLUMNS = 30
GRID_ROWS = 30
PARCEL_PIXELS = 2048
PARCEL_MAX_HEIGHT = 100
ENDEMAR_COLUMN = 15
ENDEMAR_ROW = 15
CANONICAL_COLUMN = ENDEMAR_COLUMN + 1
CANONICAL_ROW = ENDEMAR_ROW
CANONICAL_CELL = CANONICAL_ROW * GRID_COLUMNS + CANONICAL_COLUMN
CANONICAL_PARCEL_ID = f"parcel-{CANONICAL_COLUMN}-{CANONICAL_ROW}"
CANONICAL_REGION_ID = "region-" + CANONICAL_PARCEL_ID
PLACEMENT_WIDTH_FRACTION = Decimal("0.12")
ZONE_SIZE = (Decimal(1) / Decimal(GRID_COLUMNS)) / PLACEMENT_WIDTH_FRACTION
SURFACE_FILE = "fantasy_archipelago_terrain_atlas.png"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalized_name(value) -> str:
    return " ".join(str(value or "").strip().lower().split())


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


def region_item(table, region_id: str) -> dict:
    if not region_id:
        return {}
    return table.get_item(
        Key={"pk": WORLD_PK, "sk": "REGION#" + region_id},
        ConsistentRead=True,
    ).get("Item") or {}


def region_name(item: dict) -> str:
    state = item.get("state") if isinstance(item.get("state"), dict) else {}
    return str(state.get("name") or "")


def geanaph_urls(asset_base_url: str) -> tuple[str, str]:
    base = asset_base_url.rstrip("/")
    return (
        f"{base}/{SURFACE_FILE}",
        f"{base}/truth/geanaph_truth_manifest.json",
    )


def canonical_parcel(owner_user_id: str, existing: dict | None = None) -> dict:
    stamp = utc_stamp()
    parcel = dict(existing or {})
    parcel.update(
        {
            "pk": WORLD_PK,
            "sk": "PARCEL#" + CANONICAL_PARCEL_ID,
            "parcelId": CANONICAL_PARCEL_ID,
            "regionId": CANONICAL_REGION_ID,
            "worldId": WORLD_ID,
            "displayName": ZONE_NAME,
            "ownerUserId": owner_user_id,
            "cellIndex": CANONICAL_CELL,
            "column": CANONICAL_COLUMN,
            "row": CANONICAL_ROW,
            "pixelWidth": PARCEL_PIXELS,
            "pixelHeight": PARCEL_PIXELS,
            "maxHeight": PARCEL_MAX_HEIGHT,
            "bindingHash": "",
            "claimedAtUtc": str(parcel.get("claimedAtUtc") or stamp),
            "visibility": "Public",
            "status": "Canonical",
            "canonicalZone": True,
            "platformOwned": True,
        }
    )
    return parcel


def canonical_region(
    owner_user_id: str,
    surface_url: str,
    truth_manifest_url: str,
    existing: dict | None = None,
) -> dict:
    stamp = utc_stamp()
    item = dict(existing or {})
    state = dict(item.get("state") or {})
    state.update(
        {
            "regionId": CANONICAL_REGION_ID,
            "worldId": WORLD_ID,
            "name": ZONE_NAME,
            "minColumn": CANONICAL_COLUMN,
            "minRow": CANONICAL_ROW,
            "maxColumn": CANONICAL_COLUMN,
            "maxRow": CANONICAL_ROW,
            "selectedCells": [CANONICAL_CELL],
            "sourceTiles": list(state.get("sourceTiles") or []),
            "overlayTiles": list(state.get("overlayTiles") or []),
            "createdAtUtc": str(state.get("createdAtUtc") or stamp),
            "updatedAtUtc": stamp,
            "tierIndex": 0,
            "sourceLayerOffsets": list(range(PARCEL_MAX_HEIGHT)),
            "gridShape": "square",
            "ownerUserId": owner_user_id,
            "parcelId": CANONICAL_PARCEL_ID,
            "parcelPixelWidth": PARCEL_PIXELS,
            "parcelPixelHeight": PARCEL_PIXELS,
            "maxHeight": PARCEL_MAX_HEIGHT,
            "parentNodeId": "world:" + WORLD_ID,
            "coordinateSpace": "world-normalized-v1",
            "canonicalMinX": Decimal(CANONICAL_COLUMN) / Decimal(GRID_COLUMNS),
            "canonicalMinY": Decimal(CANONICAL_ROW) / Decimal(GRID_ROWS),
            "canonicalMaxX": Decimal(CANONICAL_COLUMN + 1) / Decimal(GRID_COLUMNS),
            "canonicalMaxY": Decimal(CANONICAL_ROW + 1) / Decimal(GRID_ROWS),
            "canonicalZMin": 0,
            "canonicalZMax": PARCEL_MAX_HEIGHT,
            "relativeTo": "Endemar",
            "relativeOffsetX": 1,
            "relativeOffsetY": 0,
            "truthManifestUrl": truth_manifest_url,
            "surfaceRepresentationUrl": surface_url,
            "representationPolicy": "Representation != Semantic Truth",
        }
    )
    return {
        **item,
        "pk": WORLD_PK,
        "sk": "REGION#" + CANONICAL_REGION_ID,
        "worldId": WORLD_ID,
        "regionId": CANONICAL_REGION_ID,
        "parcelId": CANONICAL_PARCEL_ID,
        "ownerUserId": owner_user_id,
        "state": state,
        "updatedAt": int(time.time()),
    }


def surface_layer(surface_url: str, truth_manifest_url: str) -> dict:
    x = (Decimal(CANONICAL_COLUMN) + Decimal("0.5")) / Decimal(GRID_COLUMNS)
    y = (Decimal(CANONICAL_ROW) + Decimal("0.5")) / Decimal(GRID_ROWS)
    return {
        "id": f"geanaph:{CANONICAL_REGION_ID}:surface",
        "regionId": CANONICAL_REGION_ID,
        "assetId": "zone:geanaph:surface-representation",
        "name": "Geanaph Surface Representation",
        "libraryTile": False,
        "kind": "image",
        "originalSrc": surface_url,
        "transparentSrc": surface_url,
        "transparent": True,
        "x": x,
        "y": y,
        "tier": 0,
        "layer": 0,
        "size": ZONE_SIZE,
        "rotation": 0,
        "opacity": 1,
        "committed": True,
        "mmoSurface": True,
        "deedZoneLayer": True,
        "deedLocalFull": True,
        "representationOnly": True,
        "provenance": "OUTSIDER_AI",
        "truthManifestUrl": truth_manifest_url,
    }


def verify_existing_target(parcels: list[dict]) -> dict | None:
    exact_cell = next(
        (
            parcel
            for parcel in parcels
            if int(parcel.get("cellIndex") or -1) == CANONICAL_CELL
        ),
        None,
    )
    if exact_cell is None:
        return None

    if normalized_name(exact_cell.get("displayName")) != normalized_name(ZONE_NAME):
        raise RuntimeError(
            "The canonical Geanaph cell east of Endemar is already occupied by "
            + str(exact_cell.get("displayName") or exact_cell.get("parcelId") or "another deed")
            + "; refusing to overwrite existing world truth."
        )
    return exact_cell


def seed_zone(table, owner_user_id: str, asset_base_url: str) -> dict:
    source_key = {"pk": WORLD_PK, "sk": "WORLDSOURCE"}
    source_item = table.get_item(Key=source_key, ConsistentRead=True).get("Item")
    if not source_item or not isinstance(source_item.get("state"), dict):
        raise RuntimeError(
            "Canonical Shaelvien WORLDSOURCE is missing; refusing to invent a replacement world map."
        )

    surface_url, truth_manifest_url = geanaph_urls(asset_base_url)
    source_state = dict(source_item["state"])
    markers = dict(source_state.get("migrationMarkers") or {})
    existing_layers = (
        list(source_state.get("userLayers") or [])
        if isinstance(source_state.get("userLayers"), list)
        else []
    )

    parcels = query_world_prefix(table, "PARCEL#")
    existing_parcel = verify_existing_target(parcels)

    for parcel in parcels:
        if (
            normalized_name(parcel.get("displayName")) == normalized_name(ZONE_NAME)
            and int(parcel.get("cellIndex") or -1) != CANONICAL_CELL
        ):
            raise RuntimeError(
                "A Geanaph parcel already exists outside the canonical east-of-Endemar cell; "
                "refusing to create a second identity."
            )

    existing_region = region_item(table, CANONICAL_REGION_ID)
    if existing_region:
        existing_name = normalized_name(region_name(existing_region))
        if existing_name and existing_name != normalized_name(ZONE_NAME):
            raise RuntimeError(
                "The canonical Geanaph region identity conflicts with an existing region; "
                "refusing to overwrite existing world truth."
            )

    parcel = canonical_parcel(owner_user_id, existing_parcel)
    region = canonical_region(
        owner_user_id,
        surface_url,
        truth_manifest_url,
        existing_region,
    )
    layer = surface_layer(surface_url, truth_manifest_url)

    source_state["userLayers"] = [
        item
        for item in existing_layers
        if not (
            isinstance(item, dict)
            and (
                str(item.get("regionId") or "") == CANONICAL_REGION_ID
                or str(item.get("id") or "").startswith("geanaph:")
            )
        )
    ] + [layer]

    markers[ZONE_MARKER] = {
        "regionId": CANONICAL_REGION_ID,
        "seededAtUtc": utc_stamp(),
        "relativeTo": "Endemar",
        "relativeOffsetX": 1,
        "relativeOffsetY": 0,
        "ownerUserId": owner_user_id,
        "truthManifestUrl": truth_manifest_url,
        "surfaceRepresentationUrl": surface_url,
        "representationOnly": True,
        "deedLocalFull": True,
    }
    source_state["migrationMarkers"] = markers
    source_state["savedAt"] = utc_stamp()

    source_item["state"] = source_state
    source_item["entityType"] = str(source_item.get("entityType") or "worldMap")
    source_item["worldId"] = WORLD_ID
    source_item["updatedAtUtc"] = utc_stamp()
    source_item["updatedByUserId"] = owner_user_id

    if existing_parcel is None:
        table.put_item(
            Item=parcel,
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )
    else:
        table.put_item(Item=parcel)
    table.put_item(Item=region)
    table.put_item(Item=source_item)

    verify_parcel = table.get_item(
        Key={"pk": WORLD_PK, "sk": "PARCEL#" + CANONICAL_PARCEL_ID},
        ConsistentRead=True,
    ).get("Item") or {}
    verify_source = table.get_item(Key=source_key, ConsistentRead=True).get("Item") or {}
    verify_state = (
        verify_source.get("state") if isinstance(verify_source.get("state"), dict) else {}
    )
    verify_layers = [
        item
        for item in (verify_state.get("userLayers") or [])
        if isinstance(item, dict)
        and str(item.get("regionId") or "") == CANONICAL_REGION_ID
    ]

    if str(verify_parcel.get("ownerUserId") or "") != owner_user_id:
        raise RuntimeError(
            "Geanaph verification failed: parcel owner does not match the configured platform owner."
        )
    if int(verify_parcel.get("column") or -1) != CANONICAL_COLUMN or int(
        verify_parcel.get("row") or -1
    ) != CANONICAL_ROW:
        raise RuntimeError(
            "Geanaph verification failed: parcel is not exactly east of Endemar."
        )
    if len(verify_layers) != 1 or not bool(verify_layers[0].get("mmoSurface")):
        raise RuntimeError(
            "Geanaph verification failed: canonical MMO surface representation is missing."
        )

    return {
        "seeded": True,
        "alreadySeeded": bool(markers.get(ZONE_MARKER) and existing_parcel is not None),
        "parcelId": CANONICAL_PARCEL_ID,
        "regionId": CANONICAL_REGION_ID,
        "column": CANONICAL_COLUMN,
        "row": CANONICAL_ROW,
        "canonicalEastOfEndemar": True,
        "ownerBoundToPlatformAccount": True,
        "ownerUserId": owner_user_id,
        "visibility": "Public",
        "truthManifestUrl": truth_manifest_url,
        "surfaceRepresentationUrl": surface_url,
        "representationOnly": True,
    }


def send_cloudformation_response(event, context, status: str, data: dict, reason: str = ""):
    body = {
        "Status": status,
        "Reason": reason or f"See CloudWatch Log Stream: {context.log_stream_name}",
        "PhysicalResourceId": str(
            event.get("PhysicalResourceId") or "geanaph-east-zone-seed-v2"
        ),
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
            raise RuntimeError(
                "OWNER_USER_ID is required so Geanaph uses the same platform-owner account as Endemar."
            )
        if not asset_base_url.startswith("https://"):
            raise RuntimeError("ASSET_BASE_URL must be an HTTPS URL.")

        result = seed_zone(table, owner_user_id, asset_base_url)
        print(json.dumps(result, sort_keys=True))
        send_cloudformation_response(event, context, "SUCCESS", result)
    except Exception as exc:
        print(f"Geanaph seed failed: {exc}")
        send_cloudformation_response(
            event,
            context,
            "FAILED",
            {"error": str(exc)},
            reason=str(exc)[:900],
        )
