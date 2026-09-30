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
ZONE_MARKER = "geanaph-east-v1"

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

# These are representation layers backed by the verified Geanaph truth package.
# Their z values are display-order semantics only; they are not physical depth.
TRUTH_LAYERS = (
    (0, "groundwater", "Groundwater Basin Boundaries", "built_live/T_truth_groundwater_boundaries.png", -50, False),
    (1, "active-faults", "Active Faults", "built_live/T_truth_active_faults.png", -40, False),
    (2, "plate-boundaries", "Plate Boundaries", "built_live/T_truth_plate_boundaries.png", -30, False),
    (3, "submerged-archaeology", "Submerged Archaeology", "T_truth_submerged.png", -20, False),
    (4, "subterranean", "Subterranean Engineering", "T_truth_subterranean.png", -10, False),
    (5, "current-coastline", "Current Coastline", "T_truth_current_coastline.png", 0, True),
    (6, "current-rivers", "Current Rivers", "T_truth_current_rivers.png", 10, False),
    (7, "early-engineering", "Early Engineering Anchors", "T_truth_early_engineering.png", 20, False),
    (8, "surface-archaeology", "Surface Archaeology", "T_truth_archaeology_surface.png", 30, False),
    (9, "chronology", "Chronology", "T_truth_chronology_stars.png", 40, False),
)


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


def _region_item(table, region_id: str) -> dict:
    if not region_id:
        return {}
    return table.get_item(
        Key={"pk": WORLD_PK, "sk": "REGION#" + region_id},
        ConsistentRead=True,
    ).get("Item") or {}


def _region_is_empty(region_item: dict, world_layers: list, region_id: str) -> bool:
    state = region_item.get("state") if isinstance(region_item.get("state"), dict) else {}
    if state.get("sourceTiles") or state.get("overlayTiles"):
        return False
    return not any(
        isinstance(layer, dict) and str(layer.get("regionId") or "") == region_id
        for layer in world_layers
    )


def _canonical_parcel(owner_user_id: str) -> dict:
    stamp = utc_stamp()
    return {
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
        "claimedAtUtc": stamp,
        "visibility": "Public",
        "status": "Canonical",
        "canonicalZone": True,
        "canonicalOwner": "platformOwner",
        "tokenSpent": False,
    }


def _canonical_region(owner_user_id: str, existing: dict | None = None) -> dict:
    existing = dict(existing or {})
    state = dict(existing.get("state") or {})
    stamp = utc_stamp()

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
            "sourceLayerOffsets": list(range(10)),
            "gridShape": str(state.get("gridShape") or "square"),
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
            "truthLayerCount": len(TRUTH_LAYERS),
            "truthPackageStatus": "verified",
        }
    )

    return {
        **existing,
        "pk": WORLD_PK,
        "sk": "REGION#" + CANONICAL_REGION_ID,
        "worldId": WORLD_ID,
        "regionId": CANONICAL_REGION_ID,
        "parcelId": CANONICAL_PARCEL_ID,
        "ownerUserId": owner_user_id,
        "state": state,
        "updatedAt": int(time.time()),
    }


def _choose_target(table, owner_user_id: str, world_layers: list) -> tuple[dict, dict, bool]:
    parcels = query_world_prefix(table, "PARCEL#")

    same_name = [
        parcel
        for parcel in parcels
        if normalized_name(parcel.get("displayName")) == normalized_name(ZONE_NAME)
    ]
    for parcel in same_name:
        if int(parcel.get("cellIndex") or -1) != CANONICAL_CELL:
            raise RuntimeError(
                "A Geanaph parcel already exists outside the canonical east-of-Endemar cell; "
                "refusing to move or duplicate existing world truth."
            )

    occupied = next(
        (parcel for parcel in parcels if int(parcel.get("cellIndex") or -1) == CANONICAL_CELL),
        None,
    )
    if occupied is not None:
        if normalized_name(occupied.get("displayName")) != normalized_name(ZONE_NAME):
            raise RuntimeError(
                "The canonical Geanaph cell east of Endemar is occupied by "
                + str(occupied.get("displayName") or occupied.get("parcelId") or "another deed")
                + "; refusing to overwrite existing world truth."
            )
        existing_owner = str(occupied.get("ownerUserId") or "")
        if existing_owner and existing_owner != owner_user_id:
            raise RuntimeError(
                "Geanaph already has a different owner; refusing to transfer ownership silently."
            )
        if not bool(occupied.get("canonicalZone")) and existing_owner != owner_user_id:
            raise RuntimeError(
                "The east-of-Endemar parcel is not marked canonical; refusing to promote it automatically."
            )

        occupied = {
            **occupied,
            "ownerUserId": owner_user_id,
            "displayName": ZONE_NAME,
            "visibility": "Public",
            "status": "Canonical",
            "canonicalZone": True,
            "canonicalOwner": "platformOwner",
            "tokenSpent": False,
        }
        region_id = str(occupied.get("regionId") or CANONICAL_REGION_ID)
        if region_id != CANONICAL_REGION_ID:
            raise RuntimeError(
                "Geanaph parcel has a non-canonical region identity; refusing to rewrite identity silently."
            )
        region_item = _region_item(table, CANONICAL_REGION_ID)
        return occupied, _canonical_region(owner_user_id, region_item), False

    legacy_region = _region_item(table, CANONICAL_REGION_ID)
    if legacy_region:
        legacy_name = normalized_name(
            (legacy_region.get("state") or {}).get("name")
            if isinstance(legacy_region.get("state"), dict)
            else ""
        )
        if legacy_name and legacy_name != normalized_name(ZONE_NAME):
            raise RuntimeError(
                "The canonical Geanaph region identity conflicts with an existing region; "
                "refusing to overwrite existing world truth."
            )
        if not _region_is_empty(legacy_region, world_layers, CANONICAL_REGION_ID):
            raise RuntimeError(
                "The canonical Geanaph region already contains unrelated authored content; "
                "refusing to overwrite it."
            )

    parcel = _canonical_parcel(owner_user_id)
    region = _canonical_region(owner_user_id, legacy_region)
    return parcel, region, True


def _build_layers(asset_base_url: str) -> list[dict]:
    x = (Decimal(CANONICAL_COLUMN) + Decimal("0.5")) / Decimal(GRID_COLUMNS)
    y = (Decimal(CANONICAL_ROW) + Decimal("0.5")) / Decimal(GRID_ROWS)
    base = asset_base_url.rstrip("/")
    manifest_url = f"{base}/geanaph_truth_manifest.json"

    return [
        {
            "id": f"geanaph:{CANONICAL_REGION_ID}:{truth_id}",
            "regionId": CANONICAL_REGION_ID,
            "assetId": f"zone:geanaph:{truth_id}",
            "name": name,
            "libraryTile": False,
            "kind": "image",
            "originalSrc": f"{base}/{filename}",
            "transparentSrc": f"{base}/{filename}",
            "transparent": True,
            "x": x,
            "y": y,
            "tier": 0,
            "layer": layer_index,
            "size": ZONE_SIZE,
            "rotation": 0,
            "opacity": 1,
            "committed": True,
            "mmoSurface": mmo_surface,
            "truthLayerId": truth_id,
            "truthDisplayZ": truth_z,
            "truthManifestUrl": manifest_url,
            "provenance": "published-source-registry",
            "relationshipLinesSynthetic": 0,
        }
        for layer_index, truth_id, name, filename, truth_z, mmo_surface in TRUTH_LAYERS
    ]


def seed_zone(table, owner_user_id: str, asset_base_url: str) -> dict:
    source_key = {"pk": WORLD_PK, "sk": "WORLDSOURCE"}
    source_item = table.get_item(Key=source_key, ConsistentRead=True).get("Item")
    if not source_item or not isinstance(source_item.get("state"), dict):
        raise RuntimeError(
            "Canonical Shaelvien WORLDSOURCE is missing; refusing to invent a replacement world map."
        )

    source_state = dict(source_item["state"])
    markers = dict(source_state.get("migrationMarkers") or {})
    existing_layers = (
        list(source_state.get("userLayers") or [])
        if isinstance(source_state.get("userLayers"), list)
        else []
    )

    parcel, region_item, created_parcel = _choose_target(
        table, owner_user_id, existing_layers
    )
    zone_layers = _build_layers(asset_base_url)

    source_state["userLayers"] = [
        layer
        for layer in existing_layers
        if not (
            isinstance(layer, dict)
            and (
                str(layer.get("regionId") or "") == CANONICAL_REGION_ID
                or str(layer.get("id") or "").startswith("geanaph:")
            )
        )
    ] + zone_layers

    markers[ZONE_MARKER] = {
        "regionId": CANONICAL_REGION_ID,
        "parcelId": CANONICAL_PARCEL_ID,
        "seededAtUtc": utc_stamp(),
        "coordinate": {"x": 1, "y": 0},
        "surfaceTier": 0,
        "surfaceLayer": 5,
        "truthManifestUrl": asset_base_url.rstrip("/") + "/geanaph_truth_manifest.json",
        "ownerAuthority": "platformOwner",
    }
    source_state["migrationMarkers"] = markers
    source_state["savedAt"] = utc_stamp()

    source_item["state"] = source_state
    source_item["entityType"] = str(source_item.get("entityType") or "worldMap")
    source_item["worldId"] = WORLD_ID
    source_item["updatedAtUtc"] = utc_stamp()
    source_item["updatedByUserId"] = owner_user_id

    if created_parcel:
        table.put_item(
            Item=parcel,
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )
    else:
        table.put_item(Item=parcel)
    table.put_item(Item=region_item)
    table.put_item(Item=source_item)

    verify_parcel = table.get_item(
        Key={"pk": WORLD_PK, "sk": "PARCEL#" + CANONICAL_PARCEL_ID},
        ConsistentRead=True,
    ).get("Item") or {}
    verify_source = table.get_item(Key=source_key, ConsistentRead=True).get("Item") or {}
    verify_state = verify_source.get("state") if isinstance(verify_source.get("state"), dict) else {}
    verify_layers = [
        layer
        for layer in (verify_state.get("userLayers") or [])
        if isinstance(layer, dict)
        and str(layer.get("regionId") or "") == CANONICAL_REGION_ID
    ]

    if str(verify_parcel.get("ownerUserId") or "") != owner_user_id:
        raise RuntimeError("Geanaph verification failed: owner does not match the platform owner.")
    if len(verify_layers) != len(TRUTH_LAYERS):
        raise RuntimeError(
            f"Geanaph verification failed: expected {len(TRUTH_LAYERS)} layers, "
            f"found {len(verify_layers)}."
        )
    if sum(1 for layer in verify_layers if bool(layer.get("mmoSurface"))) != 1:
        raise RuntimeError("Geanaph verification failed: exactly one MMO surface layer is required.")

    return {
        "seeded": True,
        "alreadySeeded": False,
        "zoneName": ZONE_NAME,
        "parcelId": CANONICAL_PARCEL_ID,
        "regionId": CANONICAL_REGION_ID,
        "column": CANONICAL_COLUMN,
        "row": CANONICAL_ROW,
        "relativeX": 1,
        "relativeY": 0,
        "eastOfEndemar": True,
        "ownerMatchesPlatformOwner": True,
        "tokenSpent": False,
        "layerCount": len(verify_layers),
        "surfaceTier": 0,
        "surfaceLayer": 5,
        "truthManifestUrl": asset_base_url.rstrip("/") + "/geanaph_truth_manifest.json",
    }


def send_cloudformation_response(event, context, status: str, data: dict, reason: str = ""):
    body = {
        "Status": status,
        "Reason": reason or f"See CloudWatch Log Stream: {context.log_stream_name}",
        "PhysicalResourceId": str(event.get("PhysicalResourceId") or "geanaph-east-zone-seed-v1"),
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
            raise RuntimeError("OWNER_USER_ID is required for the Geanaph canonical seed.")
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
