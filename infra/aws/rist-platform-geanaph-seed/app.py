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
ZONE_NAME = "Geonaph"
ZONE_MARKER = "geonaph-east-v4-history-policy"
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
FRAME_WIDTH = 1672
FRAME_HEIGHT = 941
SURFACE_FILE = "fantasy_archipelago_terrain_atlas.png"
HISTORY_REGION_NODE_ID = "region-west-turkana"
HISTORY_LOCAL_NODE_ID = "local-lomekwi-3"
HISTORY_INSTANCE_NODE_ID = "instance-lom3-toolmaking-locality"

# Display representations only. The independent truth manifest remains the
# evidence/provenance authority; these generated layers never become semantic
# truth merely because they share a locked canvas.
VISUAL_LAYERS = (
    ("cavern", "Cavern Network", "luminous_underground_cavern_network.png", 0, 0, -40, False),
    ("subterranean", "Subterranean Realm", "enchanted_subterranean_realm_map.png", 0, 1, -30, False),
    ("aquifer", "Aquifer", "luminous_underground_aquifer_world_map.png", 0, 2, -20, False),
    ("deep-geology", "Deep Geology", "glowing_volcanic_world_map_layer.png", 0, 3, -10, False),
    ("terrain", "Terrain Surface", SURFACE_FILE, 0, 4, 0, True),
    ("surface-overlay", "Surface Overlay", "luminous_fantasy_archipelago_map_overlay.png", 1, 0, 10, False),
    ("water", "Waterways", "glowing_fantasy_waterway_map.png", 1, 1, 20, False),
    ("ruins", "Ruined Surface", "fantastical_ruined_archipelago_layer.png", 1, 2, 30, False),
    ("celestial", "Celestial Overlay", "celestial_nebula_archipelago_map.png", 2, 0, 40, False),
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalized_name(value) -> str:
    return " ".join(str(value or "").strip().lower().split())


def is_geonaph_name(value) -> bool:
    # Accept the legacy display spelling while migrating one persistent identity.
    return normalized_name(value) in {"geonaph", "geanaph"}


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
            "frameWidth": FRAME_WIDTH,
            "frameHeight": FRAME_HEIGHT,
            "frameLock": True,
            "visualLayerCount": len(VISUAL_LAYERS),
            "representationPolicy": "Representation != Semantic Truth",
            "historyContentPolicy": {
                "matureContent": "ALLOWED",
                "presentation": "historical-context",
                "provenanceIndependent": True,
                "preserveDifficultFacts": True,
            },
            "description": (
                "Canonical Shaelvien-owned Geonaph historical corridor. "
                "Facts, reconstruction, and fiction remain separately labeled."
            ),
            "spatialNodes": [
                {
                    "nodeId": HISTORY_REGION_NODE_ID,
                    "kind": "REGION",
                    "name": "West Turkana",
                    "parentNodeId": CANONICAL_REGION_ID,
                    "provenance": "FACT",
                    "createdAtUtc": str(state.get("createdAtUtc") or stamp),
                    "updatedAtUtc": stamp,
                    "description": (
                        "FACT: West Turkana, Kenya. Contains the Lomekwi 3 archaeological "
                        "site used as Geonaph's oldest installed playable history node."
                    ),
                },
                {
                    "nodeId": HISTORY_LOCAL_NODE_ID,
                    "kind": "LOCAL",
                    "name": "Lomekwi 3",
                    "parentNodeId": HISTORY_REGION_NODE_ID,
                    "provenance": "FACT",
                    "createdAtUtc": str(state.get("createdAtUtc") or stamp),
                    "updatedAtUtc": stamp,
                    "description": (
                        "FACT: approximately 3.3 Ma; in situ stone artefacts, core reduction "
                        "and battering in a wooded palaeoenvironment. Toolmaker taxonomic "
                        "identity remains unresolved."
                    ),
                },
                {
                    "nodeId": HISTORY_INSTANCE_NODE_ID,
                    "kind": "INSTANCE",
                    "name": "LOM3 Tool-Making Locality",
                    "parentNodeId": HISTORY_LOCAL_NODE_ID,
                    "provenance": "FACT",
                    "createdAtUtc": str(state.get("createdAtUtc") or stamp),
                    "updatedAtUtc": stamp,
                    "description": (
                        "PLAYABLE FACT ANCHOR: reproduce only evidence-grounded classes of "
                        "stone-working action. Successful gameplay never becomes new history."
                    ),
                },
            ],
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


def build_visual_layers(asset_base_url: str, truth_manifest_url: str) -> list[dict]:
    base = asset_base_url.rstrip("/")
    layers = []
    for semantic_role, name, filename, tier, layer, display_z, mmo_surface in VISUAL_LAYERS:
        url = f"{base}/{filename}"
        layers.append(
            {
                "id": f"geanaph:{CANONICAL_REGION_ID}:{semantic_role}",
                "regionId": CANONICAL_REGION_ID,
                "assetId": f"zone:geanaph:{semantic_role}",
                "name": name,
                "libraryTile": False,
                "kind": "image",
                "placementRole": "deed-frame",
                "fullWorld": False,
                "fullDeedFrame": True,
                "originalSrc": url,
                "transparentSrc": url,
                "transparent": True,
                "x": Decimal("0.5"),
                "y": Decimal("0.5"),
                "tier": tier,
                "layer": layer,
                "displayZ": display_z,
                "semanticRole": semantic_role,
                "size": 1,
                "rotation": 0,
                "opacity": 1,
                "committed": True,
                "mmoSurface": mmo_surface,
                "representationOnly": True,
                "provenance": "OUTSIDER_AI",
                "truthManifestUrl": truth_manifest_url,
                "frameLock": True,
                "frameWidth": FRAME_WIDTH,
                "frameHeight": FRAME_HEIGHT,
            }
        )
    return layers


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

    if not is_geonaph_name(exact_cell.get("displayName")):
        raise RuntimeError(
            "The canonical Geonaph cell east of Endemar is already occupied by "
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
            is_geonaph_name(parcel.get("displayName"))
            and int(parcel.get("cellIndex") or -1) != CANONICAL_CELL
        ):
            raise RuntimeError(
                "A Geonaph parcel already exists outside the canonical east-of-Endemar cell; "
                "refusing to create a second identity."
            )

    existing_region = region_item(table, CANONICAL_REGION_ID)
    if existing_region:
        existing_name = normalized_name(region_name(existing_region))
        if existing_name and not is_geonaph_name(existing_name):
            raise RuntimeError(
                "The canonical Geonaph region identity conflicts with an existing region; "
                "refusing to overwrite existing world truth."
            )

    parcel = canonical_parcel(owner_user_id, existing_parcel)
    region = canonical_region(
        owner_user_id,
        surface_url,
        truth_manifest_url,
        existing_region,
    )
    visual_layers = build_visual_layers(asset_base_url, truth_manifest_url)

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
    ] + visual_layers

    markers[ZONE_MARKER] = {
        "regionId": CANONICAL_REGION_ID,
        "seededAtUtc": utc_stamp(),
        "relativeTo": "Endemar",
        "relativeOffsetX": 1,
        "relativeOffsetY": 0,
        "ownerUserId": owner_user_id,
        "truthManifestUrl": truth_manifest_url,
        "surfaceRepresentationUrl": surface_url,
        "visualLayerCount": len(visual_layers),
        "frameWidth": FRAME_WIDTH,
        "frameHeight": FRAME_HEIGHT,
        "frameLock": True,
        "entryView": "all-parallax",
        "representationOnly": True,
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
            "Geonaph verification failed: parcel owner does not match the configured platform owner."
        )
    if int(verify_parcel.get("column") or -1) != CANONICAL_COLUMN or int(
        verify_parcel.get("row") or -1
    ) != CANONICAL_ROW:
        raise RuntimeError(
            "Geonaph verification failed: parcel is not exactly east of Endemar."
        )
    if len(verify_layers) != len(VISUAL_LAYERS):
        raise RuntimeError(
            f"Geonaph verification failed: expected {len(VISUAL_LAYERS)} visual layers, "
            f"found {len(verify_layers)}."
        )
    if sum(1 for item in verify_layers if bool(item.get("mmoSurface"))) != 1:
        raise RuntimeError(
            "Geonaph verification failed: exactly one deed-map surface representation is required."
        )
    if not all(bool(item.get("fullDeedFrame")) for item in verify_layers):
        raise RuntimeError(
            "Geonaph verification failed: every visual layer must fill the locked deed frame."
        )

    verify_region = region_item(table, CANONICAL_REGION_ID)
    verify_region_state = (
        verify_region.get("state")
        if isinstance(verify_region.get("state"), dict)
        else {}
    )
    verify_nodes = {
        str(node.get("nodeId") or ""): node
        for node in (verify_region_state.get("spatialNodes") or [])
        if isinstance(node, dict)
    }
    required_history_nodes = {
        HISTORY_REGION_NODE_ID: ("REGION", CANONICAL_REGION_ID, "FACT"),
        HISTORY_LOCAL_NODE_ID: ("LOCAL", HISTORY_REGION_NODE_ID, "FACT"),
        HISTORY_INSTANCE_NODE_ID: ("INSTANCE", HISTORY_LOCAL_NODE_ID, "FACT"),
    }
    for node_id, (kind, parent_id, provenance) in required_history_nodes.items():
        node = verify_nodes.get(node_id)
        if not node:
            raise RuntimeError(
                f"Geonaph history verification failed: missing spatial node {node_id}."
            )
        if str(node.get("kind") or "").upper() != kind:
            raise RuntimeError(
                f"Geonaph history verification failed: {node_id} has the wrong kind."
            )
        if str(node.get("parentNodeId") or "") != parent_id:
            raise RuntimeError(
                f"Geonaph history verification failed: {node_id} has the wrong parent."
            )
        if str(node.get("provenance") or "").upper() != provenance:
            raise RuntimeError(
                f"Geonaph history verification failed: {node_id} has invalid provenance."
            )

    history_policy = (
        verify_region_state.get("historyContentPolicy")
        if isinstance(verify_region_state.get("historyContentPolicy"), dict)
        else {}
    )
    if str(history_policy.get("matureContent") or "").upper() != "ALLOWED":
        raise RuntimeError(
            "Geonaph history verification failed: Shaelvien Mature content policy was not preserved."
        )
    if not bool(history_policy.get("provenanceIndependent")):
        raise RuntimeError(
            "Geonaph history verification failed: content rating must remain independent of provenance."
        )

    return {
        "seeded": True,
        "alreadySeeded": existing_parcel is not None,
        "parcelId": CANONICAL_PARCEL_ID,
        "regionId": CANONICAL_REGION_ID,
        "column": CANONICAL_COLUMN,
        "row": CANONICAL_ROW,
        "canonicalEastOfEndemar": True,
        "ownerBoundToPlatformAccount": True,
        "ownerUserId": owner_user_id,
        "visibility": "Public",
        "visualLayerCount": len(verify_layers),
        "historyRegionNodeId": HISTORY_REGION_NODE_ID,
        "historyLocalNodeId": HISTORY_LOCAL_NODE_ID,
        "historyInstanceNodeId": HISTORY_INSTANCE_NODE_ID,
        "historyHierarchyVerified": True,
        "historyProvenanceVerified": True,
        "historyContentPolicyVerified": True,
        "matureContentAllowed": True,
        "provenanceIndependentOfRating": True,
        "canonicalDisplayName": ZONE_NAME,
        "frameWidth": FRAME_WIDTH,
        "frameHeight": FRAME_HEIGHT,
        "frameLock": True,
        "entryView": "all-parallax",
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
                "OWNER_USER_ID is required so Geonaph uses the same platform-owner account as Endemar."
            )
        if not asset_base_url.startswith("https://"):
            raise RuntimeError("ASSET_BASE_URL must be an HTTPS URL.")

        result = seed_zone(table, owner_user_id, asset_base_url)
        print(json.dumps(result, sort_keys=True))
        send_cloudformation_response(event, context, "SUCCESS", result)
    except Exception as exc:
        print(f"Geonaph seed failed: {exc}")
        send_cloudformation_response(
            event,
            context,
            "FAILED",
            {"error": str(exc)},
            reason=str(exc)[:900],
        )
