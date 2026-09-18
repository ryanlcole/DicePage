import hashlib
import json
import os
import secrets
import time
import urllib.parse
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError

from mutation_policy import canonical_piece_state, dynamo_safe, protects_piece


ddb = boto3.resource("dynamodb")
identity = ddb.Table(os.environ["IDENTITY_TABLE"])
users = ddb.Table(os.environ["USERS_TABLE"])
world = ddb.Table(os.environ["WORLD_TABLE"])
memberships = ddb.Table(os.environ["MEMBERSHIPS_TABLE"])
audit = ddb.Table(os.environ["AUDIT_TABLE"])
realtime = ddb.Table(os.environ["REALTIME_TABLE"])
s3 = boto3.client("s3")
bucket = os.environ["USER_DATA_BUCKET"]
kms_key = os.environ["USER_DATA_KEY_ARN"]
owner_user_id = os.environ.get("OWNER_USER_ID", "").strip()
origin = os.environ["FRONTEND_ORIGIN"].rstrip("/")
GEONAPH_WORLD_ID = "shaelvien-geonaph-alpha-001"
DEFAULT_WORLD_SLOTS = 1
DEFAULT_SURFACE_WORLD_PIXELS = 2048
CLAIM_REQUEST_PERMISSIONS = {"Restricted", "Limited", "Cooperative"}
CLAIM_DECISION_PERMISSIONS = CLAIM_REQUEST_PERMISSIONS | {"Blocked", "ReleaseOwnership"}

# Shaelvien MMO land is an exclusive 30x30 claim lattice centered on Endemar.
# A completed RIST profile receives one genesis Shaelvien Token. Spending it
# atomically binds one account-held code half to one Shaelvien property-space code half.
MMO_PARCEL_GRID_COLUMNS = 30
MMO_PARCEL_GRID_ROWS = 30
SHAELVIEN_TOKEN_CLASS = "shaelvien.property-space"
SHAELVIEN_PROPERTY_SPACE_PIXELS = 2048
SHAELVIEN_PROPERTY_SPACE_LAYERS = 100
MMO_PARCEL_PIXELS = SHAELVIEN_PROPERTY_SPACE_PIXELS
MMO_PARCEL_MAX_HEIGHT = SHAELVIEN_PROPERTY_SPACE_LAYERS
ENDEMAR_ORIGIN_COLUMN = 15
ENDEMAR_ORIGIN_ROW = 15
GENESIS_WORLD_TOKEN_SK = "WORLD_TOKEN#GENESIS"
PARCEL_DELEGATION_PERMISSIONS = {"View", "Edit", "Manage", "None"}
_serializer = TypeSerializer()


def utc_stamp():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_default(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return str(value)


def response(status, body=None):
    return {
        "statusCode": status,
        "headers": {
            "access-control-allow-origin": origin,
            "access-control-allow-headers": "authorization,content-type",
            "access-control-allow-methods": "GET,POST,OPTIONS",
            "cache-control": "no-store",
            "content-type": "application/json",
        },
        "body": "" if body is None else json.dumps(body, separators=(",", ":"), default=_json_default),
    }


def auth(event):
    header = (event.get("headers") or {}).get("authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    raw = header.split(" ", 1)[1].strip()
    digest = hashlib.sha256(raw.encode()).hexdigest()
    item = identity.get_item(Key={"pk": "session#" + digest}).get("Item")
    if not item or int(item.get("expiresAt", 0)) <= int(time.time()):
        return None
    return {"userId": str(item["userId"]), "displayName": item.get("username", "RIST user")}


def body(event):
    return json.loads(event.get("body") or "{}")


def membership(world_id, user_id):
    return memberships.get_item(Key={"pk": "WORLD#" + world_id, "sk": "USER#" + user_id}).get("Item")


def is_geonaph(world_id):
    return world_id == GEONAPH_WORLD_ID


def can_view(world_id, user_id):
    if is_geonaph(world_id):
        return True
    if owner_user_id and user_id == owner_user_id:
        return True
    return membership(world_id, user_id) is not None


def can_manage(world_id, user_id):
    # Geonaph is the public MMO world, but its world-management authority is
    # permanently reserved to the configured platform owner.
    if is_geonaph(world_id):
        return bool(owner_user_id and user_id == owner_user_id)
    if owner_user_id and user_id == owner_user_id:
        return True
    item = membership(world_id, user_id)
    return bool(item and item.get("role") in ("owner", "GM"))


def claim_permission(world_id, user_id):
    item = membership(world_id, user_id) or {}
    value = str(item.get("claimPermission") or "Blocked").strip()
    return value if value in CLAIM_DECISION_PERMISSIONS else "Blocked"


def world_partition(world_id):
    return "WORLD#" + world_id


def claim_key(world_id, request_id):
    return {"pk": world_partition(world_id), "sk": "CLAIM#" + request_id}


def region_key(world_id, region_id):
    return {"pk": world_partition(world_id), "sk": "REGION#" + region_id}


def world_source_key(world_id):
    return {"pk": world_partition(world_id), "sk": "WORLDSOURCE"}


def world_token_key(user_id):
    return {"pk": "USER#" + user_id, "sk": GENESIS_WORLD_TOKEN_SK}


def parcel_id_from_cell(cell_index):
    column = int(cell_index) % MMO_PARCEL_GRID_COLUMNS
    row = int(cell_index) // MMO_PARCEL_GRID_COLUMNS
    return f"parcel-{column}-{row}"


def parcel_key(world_id, parcel_id):
    return {"pk": world_partition(world_id), "sk": "PARCEL#" + parcel_id}


def parcel_acl_key(world_id, parcel_id, user_id):
    return {
        "pk": world_partition(world_id),
        "sk": f"PARCELACL#{parcel_id}#USER#{user_id}",
    }


def _ddb_map(value):
    return {key: _serializer.serialize(item) for key, item in value.items()}


def public_world_token(item):
    if not item:
        return None
    return {
        "tokenId": str(item.get("tokenId") or ""),
        "tokenClass": SHAELVIEN_TOKEN_CLASS,
        "status": str(item.get("status") or "unspent"),
        "holderUserId": str(item.get("holderUserId") or ""),
        "purchasedWorldId": str(item.get("purchasedWorldId") or ""),
        "parcelId": str(item.get("parcelId") or ""),
        "bindingHash": str(item.get("bindingHash") or ""),
        "createdAtUtc": str(item.get("createdAtUtc") or ""),
        "spentAtUtc": str(item.get("spentAtUtc") or ""),
    }


def public_parcel(item):
    if not item:
        return None
    return {
        "parcelId": str(item.get("parcelId") or ""),
        "worldId": str(item.get("worldId") or ""),
        "regionId": str(item.get("regionId") or ""),
        "displayName": str(item.get("displayName") or ""),
        "ownerUserId": str(item.get("ownerUserId") or ""),
        "cellIndex": int(item.get("cellIndex") or 0),
        "column": int(item.get("column") or 0),
        "row": int(item.get("row") or 0),
        "pixelWidth": int(item.get("pixelWidth") or MMO_PARCEL_PIXELS),
        "pixelHeight": int(item.get("pixelHeight") or MMO_PARCEL_PIXELS),
        "maxHeight": int(item.get("maxHeight") or MMO_PARCEL_MAX_HEIGHT),
        "bindingHash": str(item.get("bindingHash") or ""),
        "claimedAtUtc": str(item.get("claimedAtUtc") or ""),
    }


def ensure_genesis_world_token(user_id, account_id, player_alias):
    key = world_token_key(user_id)
    current = users.get_item(Key=key, ConsistentRead=True).get("Item")
    if current:
        return current

    stamp = utc_stamp()
    account_half = secrets.token_hex(32)
    item = {
        **key,
        "tokenId": "swt_" + uuid.uuid4().hex,
        "tokenClass": SHAELVIEN_TOKEN_CLASS,
        "status": "unspent",
        "holderUserId": user_id,
        # The account half is intentionally never returned by the API. The Users
        # table owns this half; a claimed world parcel owns the matching other half.
        "accountHalfCode": account_half,
        "accountHalfHash": hashlib.sha256(account_half.encode()).hexdigest(),
        "profileAccountId": str(account_id or "")[:160],
        "profileAlias": str(player_alias or "")[:80],
        "createdAtUtc": stamp,
        "spentAtUtc": "",
        "purchasedWorldId": "",
        "parcelId": "",
        "bindingHash": "",
    }
    try:
        users.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )
        return item
    except ClientError as exc:
        if (exc.response.get("Error") or {}).get("Code") != "ConditionalCheckFailedException":
            raise
        return users.get_item(Key=key, ConsistentRead=True).get("Item") or item


def parcel_permission(world_id, parcel_id, user_id):
    item = world.get_item(
        Key=parcel_acl_key(world_id, parcel_id, user_id),
        ConsistentRead=True,
    ).get("Item") or {}
    value = str(item.get("permission") or "None")
    return value if value in PARCEL_DELEGATION_PERMISSIONS else "None"


def can_edit_parcel(world_id, parcel_id, user_id):
    item = world.get_item(
        Key=parcel_key(world_id, parcel_id),
        ConsistentRead=True,
    ).get("Item")
    if not item:
        return False
    if str(item.get("ownerUserId") or "") == user_id:
        return True
    if can_manage(world_id, user_id):
        return True
    return parcel_permission(world_id, parcel_id, user_id) in ("Edit", "Manage")


def mmo_parcel_claimable(cell_index, parcels):
    cell_index = int(cell_index)
    if cell_index < 0 or cell_index >= MMO_PARCEL_GRID_COLUMNS * MMO_PARCEL_GRID_ROWS:
        return False
    column = cell_index % MMO_PARCEL_GRID_COLUMNS
    row = cell_index // MMO_PARCEL_GRID_COLUMNS
    if column == ENDEMAR_ORIGIN_COLUMN and row == ENDEMAR_ORIGIN_ROW:
        return False

    occupied = {
        (int(item.get("column") or 0), int(item.get("row") or 0))
        for item in parcels
        if item.get("parcelId")
    }
    if (column, row) in occupied:
        return False

    frontier = occupied | {(ENDEMAR_ORIGIN_COLUMN, ENDEMAR_ORIGIN_ROW)}
    return any(
        (column + dx, row + dy) in frontier
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if dx or dy
    )


def query_world_prefix(world_id, prefix):
    result = world.query(
        KeyConditionExpression=Key("pk").eq(world_partition(world_id))
        & Key("sk").begins_with(prefix)
    )
    return result.get("Items", [])


def manager_user_ids(world_id):
    ids = set()
    if owner_user_id:
        ids.add(owner_user_id)
    try:
        result = memberships.query(
            KeyConditionExpression=Key("pk").eq(world_partition(world_id))
        )
        for item in result.get("Items", []):
            if item.get("role") in ("owner", "GM") and item.get("userId"):
                ids.add(str(item["userId"]))
    except Exception:
        pass
    return ids


def notify_user(user_id, notification_type, world_id, payload):
    if not user_id:
        return
    now_ms = int(time.time() * 1000)
    users.put_item(
        Item={
            "pk": "USER#" + user_id,
            "sk": f"NOTIFICATION#{now_ms:013d}#{uuid.uuid4()}",
            "type": notification_type,
            "worldId": world_id,
            "payload": dynamo_safe(payload or {}),
            "unread": True,
            "createdAt": now_ms,
        }
    )


def audit_write(world_id, user_id, action, entity_id="", details=None):
    now = int(time.time() * 1000)
    audit.put_item(
        Item={
            "pk": "WORLD#" + world_id,
            "sk": f"{now:013d}#{uuid.uuid4()}",
            "userId": user_id,
            "action": action,
            "entityId": entity_id,
            "details": details or {},
            "createdAt": now,
        }
    )


def safe_id(value, label):
    value = str(value or "").strip()
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
    if not value or len(value) > 160 or any(c not in allowed for c in value):
        raise ValueError("Invalid " + label)
    return value


def _mutation_owner(req, current, manager, user_id):
    if current and current.get("ownerUserId"):
        return str(current["ownerUserId"])
    requested = str(req.get("ownerUserId") or "").strip()
    if manager:
        return safe_id(requested, "ownerUserId") if requested else user_id
    if requested == user_id:
        return user_id
    return ""


def _mutate_world_entity(req, world_id, entity_id, user_id, now):
    try:
        expected = int(req.get("expectedVersion", 0))
    except (TypeError, ValueError):
        return response(400, {"error": "Invalid expectedVersion"})
    if expected < 0:
        return response(400, {"error": "Invalid expectedVersion"})

    payload = req.get("payload") or {}
    if not isinstance(payload, dict):
        return response(400, {"error": "Mutation payload must be an object"})
    action = str(req.get("action") or "update")[:80]
    key = {"pk": "WORLD#" + world_id, "sk": "ENTITY#" + entity_id}
    current = world.get_item(Key=key, ConsistentRead=True).get("Item")
    manager = can_manage(world_id, user_id)
    own_entity = bool(current and current.get("ownerUserId") == user_id)
    if not (manager or own_entity):
        return response(403, {"error": "Server authority denied mutation"})

    actual = int(current.get("version", 0)) if current else 0
    if actual != expected:
        return response(409, {"error": "Version conflict", "actualVersion": actual, "entity": current})

    current_state = current.get("state") if current else None
    if protects_piece(action, entity_id, current_state):
        try:
            next_state = canonical_piece_state(action, entity_id, payload, current_state, manager=manager)
        except PermissionError as exc:
            return response(403, {"error": str(exc)})
        except ValueError as exc:
            return response(400, {"error": str(exc)})
    else:
        next_state = payload

    next_state = dynamo_safe(next_state)
    new_version = actual + 1
    item = {
        **key,
        "worldId": world_id,
        "entityId": entity_id,
        "version": new_version,
        "updatedAt": now,
        "updatedBy": user_id,
        "state": next_state,
    }
    owner = _mutation_owner(req, current, manager, user_id)
    if owner:
        item["ownerUserId"] = owner

    world.put_item(
        Item=item,
        ConditionExpression="attribute_not_exists(#v) OR #v = :expected",
        ExpressionAttributeNames={"#v": "version"},
        ExpressionAttributeValues={":expected": Decimal(expected)},
    )
    audit_write(world_id, user_id, action, entity_id, {"version": new_version})
    return response(200, item)


def commercial_profile(existing, platform_owner):
    existing = existing or {}
    raw_entitlements = existing.get("entitlements") or []
    entitlements = sorted({str(value).strip() for value in raw_entitlements if str(value).strip()})
    try:
        world_slots = max(DEFAULT_WORLD_SLOTS, int(existing.get("worldSlots", DEFAULT_WORLD_SLOTS)))
    except (TypeError, ValueError):
        world_slots = DEFAULT_WORLD_SLOTS
    try:
        surface_pixels = max(
            DEFAULT_SURFACE_WORLD_PIXELS,
            int(existing.get("surfaceWorldPixels", DEFAULT_SURFACE_WORLD_PIXELS)),
        )
    except (TypeError, ValueError):
        surface_pixels = DEFAULT_SURFACE_WORLD_PIXELS

    if platform_owner:
        entitlements = sorted(set(entitlements) | {"worlds.unlimited", "surface.unlimited"})

    return {
        "entitlements": entitlements,
        "worldSlots": world_slots,
        "surfaceWorldPixels": surface_pixels,
    }


def user_world_id_from_key(raw):
    parts = str(raw or "").replace("\\", "/").strip("/").split("/")
    if len(parts) < 3 or parts[0] != "worlds":
        return ""
    try:
        return safe_id(parts[1], "worldId")
    except ValueError:
        return ""


def can_claim_world_slot(user_id, world_id):
    if not world_id or is_geonaph(world_id):
        return True

    platform_owner = bool(owner_user_id and user_id == owner_user_id)
    if platform_owner:
        return True

    profile = users.get_item(
        Key={"pk": "USER#" + user_id, "sk": "PROFILE"},
        ConsistentRead=True,
    ).get("Item") or {}
    commercial = commercial_profile(profile, False)
    if "worlds.unlimited" in commercial["entitlements"]:
        return True

    exact_prefix = f"users/{user_id}/worlds/{world_id}/"
    existing = s3.list_objects_v2(Bucket=bucket, Prefix=exact_prefix, MaxKeys=1)
    if existing.get("KeyCount", 0):
        return True

    root = f"users/{user_id}/worlds/"
    listed = s3.list_objects_v2(Bucket=bucket, Prefix=root, Delimiter="/")
    owned_worlds = {
        prefix["Prefix"][len(root):].strip("/")
        for prefix in listed.get("CommonPrefixes", [])
        if prefix.get("Prefix")
    }
    owned_worlds.discard(GEONAPH_WORLD_ID)
    return len(owned_worlds) < int(commercial["worldSlots"])


def handler(event, context):
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]
    if method == "OPTIONS":
        return response(204)

    session = auth(event)
    if not session:
        return response(401, {"error": "Authentication required"})
    user_id = session["userId"]
    q = event.get("queryStringParameters") or {}
    now = int(time.time())

    if method == "POST" and path == "/authority/profile-complete":
        req = body(event)
        account_id = str(req.get("accountId") or "").strip()
        player_alias = str(req.get("playerAlias") or "").strip()
        if not account_id or not player_alias:
            return response(400, {"error": "Completed profile identity is required"})
        profile_key = {"pk": "USER#" + user_id, "sk": "PROFILE"}
        users.update_item(
            Key=profile_key,
            UpdateExpression=(
                "SET displayName = :displayName, playerAlias = :alias, "
                "profileAccountId = :accountId, profileCompletedAt = if_not_exists(profileCompletedAt, :completedAt)"
            ),
            ExpressionAttributeValues={
                ":displayName": session["displayName"],
                ":alias": player_alias[:80],
                ":accountId": account_id[:160],
                ":completedAt": now,
            },
        )
        token = ensure_genesis_world_token(user_id, account_id, player_alias)
        return response(200, public_world_token(token))

    if method == "GET" and path == "/authority/world-tokens":
        token = users.get_item(
            Key=world_token_key(user_id),
            ConsistentRead=True,
        ).get("Item")
        return response(200, [] if token is None else [public_world_token(token)])

    if method == "GET" and path == "/authority/me":
        profile_key = {"pk": "USER#" + user_id, "sk": "PROFILE"}
        existing_profile = users.get_item(Key=profile_key, ConsistentRead=True).get("Item") or {}
        users.update_item(
            Key=profile_key,
            UpdateExpression="SET displayName = :displayName, lastSeenAt = :lastSeenAt",
            ExpressionAttributeValues={
                ":displayName": session["displayName"],
                ":lastSeenAt": now,
            },
        )
        platform_owner = bool(owner_user_id and user_id == owner_user_id)
        commercial = commercial_profile(existing_profile, platform_owner)
        return response(
            200,
            {
                "userId": user_id,
                "displayName": session["displayName"],
                "platformOwner": platform_owner,
                **commercial,
            },
        )

    if method == "GET" and path == "/world/membership":
        world_id = safe_id(q.get("worldId"), "worldId")
        if is_geonaph(world_id):
            if owner_user_id and user_id == owner_user_id:
                return response(
                    200,
                    {
                        "worldId": world_id,
                        "role": "owner",
                        "effectiveAuthority": "platformOwner",
                        "claimPermission": "Blocked",
                    },
                )
            # Geonaph remains public-view, but a database membership row may
            # independently enable scoped claim requests without elevating the role.
            return response(
                200,
                {
                    "worldId": world_id,
                    "role": "viewer",
                    "effectiveAuthority": "publicViewer",
                    "claimPermission": claim_permission(world_id, user_id),
                },
            )
        item = membership(world_id, user_id)
        if item:
            item.setdefault("claimPermission", "Blocked")
            return response(200, item)
        if owner_user_id and user_id == owner_user_id:
            return response(
                200,
                {
                    "worldId": world_id,
                    "role": "owner",
                    "effectiveAuthority": "platformOwner",
                    "claimPermission": "Blocked",
                },
            )
        return response(200, {"worldId": world_id, "role": "none", "claimPermission": "Blocked"})

    if method == "POST" and path == "/world/membership/grant":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        target = safe_id(req.get("userId"), "userId")
        role = req.get("role")
        claim_permission_value = str(req.get("claimPermission") or "Blocked").strip()
        if role not in ("viewer", "player", "GM", "owner"):
            return response(400, {"error": "Invalid role"})
        if claim_permission_value not in CLAIM_DECISION_PERMISSIONS - {"ReleaseOwnership"}:
            return response(400, {"error": "Invalid claimPermission"})
        if is_geonaph(world_id):
            if not (owner_user_id and user_id == owner_user_id):
                return response(403, {"error": "Endemar authority is reserved to the platform owner"})
            if role in ("GM", "owner") and target != owner_user_id:
                return response(403, {"error": "Endemar GM authority cannot be delegated"})
        else:
            existing = membership(world_id, user_id)
            if not ((owner_user_id and user_id == owner_user_id) or (existing and existing.get("role") == "owner")):
                return response(403, {"error": "Owner authority required"})
        memberships.put_item(
            Item={
                "pk": "WORLD#" + world_id,
                "sk": "USER#" + target,
                "worldId": world_id,
                "userId": target,
                "role": role,
                "claimPermission": claim_permission_value,
                "updatedAt": now,
            }
        )
        audit_write(
            world_id,
            user_id,
            "membership.grant",
            details={"target": target, "role": role, "claimPermission": claim_permission_value},
        )
        return response(200, {"ok": True, "claimPermission": claim_permission_value})

    if method == "POST" and path == "/world/membership/claim-permission":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        target = safe_id(req.get("userId"), "userId")
        value = str(req.get("claimPermission") or "Blocked").strip()
        if value not in CLAIM_DECISION_PERMISSIONS - {"ReleaseOwnership"}:
            return response(400, {"error": "Invalid claimPermission"})
        if not can_manage(world_id, user_id):
            return response(403, {"error": "GM/owner authority required"})
        current = membership(world_id, target) or {
            "pk": world_partition(world_id),
            "sk": "USER#" + target,
            "worldId": world_id,
            "userId": target,
            "role": "viewer",
        }
        if is_geonaph(world_id) and target != owner_user_id:
            current["role"] = "viewer"
        current["claimPermission"] = value
        current["updatedAt"] = now
        memberships.put_item(Item=current)
        audit_write(
            world_id,
            user_id,
            "membership.claim-permission",
            details={"target": target, "claimPermission": value},
        )
        return response(200, {"ok": True, "claimPermission": value})

    if method == "POST" and path == "/world/claims/request":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        if can_manage(world_id, user_id):
            return response(400, {"error": "World managers do not need claim requests"})
        permission = claim_permission(world_id, user_id)
        if permission not in CLAIM_REQUEST_PERMISSIONS:
            return response(403, {"error": "Claim requests are not enabled for this membership"})

        try:
            cells = sorted(
                {
                    int(value)
                    for value in (req.get("selectedCells") or [])
                    if 0 <= int(value) < 900
                }
            )
            layers = sorted(
                {
                    int(value)
                    for value in (req.get("sourceLayerOffsets") or [])
                    if 0 <= int(value) < 10
                }
            )
        except (TypeError, ValueError):
            return response(400, {"error": "Invalid claim cells or layers"})
        if not cells or not layers:
            return response(400, {"error": "A claim requires selected cells and source layers"})

        request_id = uuid.uuid4().hex
        stamp = utc_stamp()
        requested_name = str(req.get("requestedName") or "").strip()[:80]
        item = {
            **claim_key(world_id, request_id),
            "requestId": request_id,
            "worldId": world_id,
            "requesterUserId": user_id,
            "requesterDisplayName": str(
                req.get("requesterDisplayName") or session["displayName"]
            )[:120],
            "workspace": str(req.get("workspace") or "regiondefiner")[:40],
            "tierIndex": max(0, min(2, int(req.get("tierIndex") or 0))),
            "selectedCells": cells,
            "sourceLayerOffsets": layers,
            "gridShape": "hex"
            if str(req.get("gridShape") or "").lower() == "hex"
            else "square",
            "status": "pending",
            "permission": permission,
            "requestedResourceId": str(req.get("requestedResourceId") or "")[:160],
            "requestedName": requested_name,
            "createdAtUtc": stamp,
            "updatedAtUtc": stamp,
            "approvedResourceId": "",
            "note": "",
        }
        world.put_item(Item=dynamo_safe(item))
        for manager_id in manager_user_ids(world_id):
            notify_user(
                manager_id,
                "world.claim.request",
                world_id,
                {
                    "requestId": request_id,
                    "requesterUserId": user_id,
                    "requesterDisplayName": item["requesterDisplayName"],
                    "requestedName": requested_name,
                    "tierIndex": item["tierIndex"],
                    "selectedCellCount": len(cells),
                },
            )
        audit_write(
            world_id,
            user_id,
            "claim.request",
            request_id,
            {"cells": len(cells), "tierIndex": item["tierIndex"]},
        )
        return response(200, item)

    if method == "GET" and path == "/world/claims":
        world_id = safe_id(q.get("worldId"), "worldId")
        status = str(q.get("status") or "pending").lower()
        items = query_world_prefix(world_id, "CLAIM#")
        if not can_manage(world_id, user_id):
            items = [
                item
                for item in items
                if str(item.get("requesterUserId") or "") == user_id
            ]
        if status not in ("", "all"):
            items = [
                item
                for item in items
                if str(item.get("status") or "").lower() == status
            ]
        items.sort(key=lambda item: str(item.get("createdAtUtc") or ""))
        return response(200, items)

    if method == "POST" and path == "/world/claims/decision":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        if not can_manage(world_id, user_id):
            return response(403, {"error": "GM/owner authority required"})
        request_id = safe_id(req.get("requestId"), "requestId")
        key = claim_key(world_id, request_id)
        item = world.get_item(Key=key, ConsistentRead=True).get("Item")
        if not item:
            return response(404, {"error": "Claim request not found"})

        permission = str(req.get("permission") or "Blocked").strip()
        if permission not in CLAIM_DECISION_PERMISSIONS:
            return response(400, {"error": "Invalid claim decision"})
        approved = permission != "Blocked"

        try:
            cells = (
                sorted(
                    {
                        int(value)
                        for value in (
                            req.get("approvedCells")
                            or item.get("selectedCells")
                            or []
                        )
                        if 0 <= int(value) < 900
                    }
                )
                if approved
                else []
            )
            layers = (
                sorted(
                    {
                        int(value)
                        for value in (
                            req.get("approvedLayerOffsets")
                            or item.get("sourceLayerOffsets")
                            or []
                        )
                        if 0 <= int(value) < 10
                    }
                )
                if approved
                else []
            )
        except (TypeError, ValueError):
            return response(400, {"error": "Invalid approved claim scope"})

        if approved and permission in CLAIM_REQUEST_PERMISSIONS and (
            not cells or not layers
        ):
            return response(
                400, {"error": "Approved claims require explicit cells and layers"}
            )

        resource_id = str(
            req.get("approvedResourceId")
            or ("region-" + request_id if approved else "")
        )[:160]
        stamp = utc_stamp()
        item["status"] = "approved" if approved else "denied"
        item["permission"] = permission
        item["approvedResourceId"] = resource_id
        item["note"] = str(req.get("note") or "")[:500]
        item["updatedAtUtc"] = stamp
        world.put_item(Item=dynamo_safe(item))

        if approved:
            requested_name = (
                str(item.get("requestedName") or "Claimed Region").strip()[:80]
                or "Claimed Region"
            )
            columns = [cell % 30 for cell in cells]
            rows = [cell // 30 for cell in cells]
            region_state = {
                "regionId": resource_id,
                "worldId": world_id,
                "name": requested_name,
                "minColumn": min(columns),
                "minRow": min(rows),
                "maxColumn": max(columns),
                "maxRow": max(rows),
                "selectedCells": cells,
                "sourceTiles": [],
                "overlayTiles": [],
                "createdAtUtc": stamp,
                "updatedAtUtc": stamp,
                "tierIndex": max(0, min(2, int(item.get("tierIndex") or 0))),
                "sourceLayerOffsets": layers,
                "gridShape": "hex"
                if str(item.get("gridShape") or "").lower() == "hex"
                else "square",
                "ownerUserId": str(item.get("requesterUserId") or ""),
            }
            world.put_item(
                Item={
                    **region_key(world_id, resource_id),
                    "worldId": world_id,
                    "regionId": resource_id,
                    "ownerUserId": region_state["ownerUserId"],
                    "state": dynamo_safe(region_state),
                    "updatedAt": now,
                }
            )

        requester_id = str(item.get("requesterUserId") or "")
        notify_user(
            requester_id,
            "world.claim.decision",
            world_id,
            {
                "requestId": request_id,
                "status": item["status"],
                "approvedResourceId": resource_id,
                "requestedName": item.get("requestedName", ""),
            },
        )
        audit_write(
            world_id,
            user_id,
            "claim.decision",
            request_id,
            {"status": item["status"], "permission": permission},
        )
        return response(200, item)

    if method == "GET" and path == "/world/parcels":
        world_id = safe_id(q.get("worldId"), "worldId")
        if not is_geonaph(world_id):
            return response(400, {"error": "MMO parcel claims belong to Shaelvien"})
        parcels = [public_parcel(item) for item in query_world_prefix(world_id, "PARCEL#")]
        parcels = [item for item in parcels if item is not None]
        for parcel in parcels:
            if parcel["ownerUserId"] == user_id:
                parcel["effectivePermission"] = "Owner"
            else:
                parcel["effectivePermission"] = parcel_permission(
                    world_id, parcel["parcelId"], user_id
                )
        parcels.sort(key=lambda item: (item["row"], item["column"]))
        return response(200, parcels)

    if method == "POST" and path == "/world/parcels/claim":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        if not is_geonaph(world_id):
            return response(400, {"error": "Shaelvien Tokens may only purchase Shaelvien property space"})

        try:
            cell_index = int(req.get("cellIndex"))
        except (TypeError, ValueError):
            return response(400, {"error": "A valid parcel cell is required"})
        if cell_index < 0 or cell_index >= MMO_PARCEL_GRID_COLUMNS * MMO_PARCEL_GRID_ROWS:
            return response(400, {"error": "Parcel cell is outside the Shaelvien claim lattice"})

        parcels = query_world_prefix(world_id, "PARCEL#")
        if not mmo_parcel_claimable(cell_index, parcels):
            return response(409, {"error": "That parcel is occupied or is not yet connected to Endemar"})

        token_key = world_token_key(user_id)
        token = users.get_item(Key=token_key, ConsistentRead=True).get("Item")
        if not token or str(token.get("status") or "") != "unspent":
            return response(409, {"error": "An unspent Shaelvien Token is required"})

        column = cell_index % MMO_PARCEL_GRID_COLUMNS
        row = cell_index // MMO_PARCEL_GRID_COLUMNS
        parcel_id = parcel_id_from_cell(cell_index)
        region_id = "region-" + parcel_id
        display_name = str(req.get("displayName") or "").strip()[:80] or f"Shaelvien {column},{row}"
        stamp = utc_stamp()
        world_half = secrets.token_hex(32)
        account_half = str(token.get("accountHalfCode") or "")
        if not account_half:
            return response(409, {"error": "Shaelvien Token account half is unavailable"})
        binding_hash = hashlib.sha256(
            f"{account_half}:{world_half}:{world_id}:{parcel_id}".encode()
        ).hexdigest()

        parcel_item = {
            **parcel_key(world_id, parcel_id),
            "parcelId": parcel_id,
            "regionId": region_id,
            "worldId": world_id,
            "displayName": display_name,
            "ownerUserId": user_id,
            "cellIndex": cell_index,
            "column": column,
            "row": row,
            "pixelWidth": MMO_PARCEL_PIXELS,
            "pixelHeight": MMO_PARCEL_PIXELS,
            "maxHeight": MMO_PARCEL_MAX_HEIGHT,
            # The world half never leaves the server. Its binding digest is safe
            # to expose and proves which account token was irreversibly paired.
            "worldHalfCode": world_half,
            "worldHalfHash": hashlib.sha256(world_half.encode()).hexdigest(),
            "bindingHash": binding_hash,
            "claimedAtUtc": stamp,
        }
        region_state = {
            "regionId": region_id,
            "worldId": world_id,
            "name": display_name,
            "minColumn": column,
            "minRow": row,
            "maxColumn": column,
            "maxRow": row,
            "selectedCells": [cell_index],
            "sourceTiles": [],
            "overlayTiles": [],
            "createdAtUtc": stamp,
            "updatedAtUtc": stamp,
            "tierIndex": 0,
            "sourceLayerOffsets": list(range(MMO_PARCEL_MAX_HEIGHT)),
            "gridShape": "square",
            "ownerUserId": user_id,
            "parcelId": parcel_id,
            "parcelPixelWidth": MMO_PARCEL_PIXELS,
            "parcelPixelHeight": MMO_PARCEL_PIXELS,
            "maxHeight": MMO_PARCEL_MAX_HEIGHT,
        }
        region_item = {
            **region_key(world_id, region_id),
            "worldId": world_id,
            "regionId": region_id,
            "parcelId": parcel_id,
            "ownerUserId": user_id,
            "state": dynamo_safe(region_state),
            "updatedAt": now,
        }

        try:
            ddb.meta.client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": users.name,
                            "Key": _ddb_map(token_key),
                            "UpdateExpression": (
                                "SET #status = :spent, purchasedWorldId = :worldId, "
                                "parcelId = :parcelId, bindingHash = :binding, spentAtUtc = :spentAt"
                            ),
                            "ConditionExpression": "#status = :unspent AND holderUserId = :userId",
                            "ExpressionAttributeNames": {"#status": "status"},
                            "ExpressionAttributeValues": _ddb_map(
                                {
                                    ":spent": "spent",
                                    ":worldId": world_id,
                                    ":parcelId": parcel_id,
                                    ":binding": binding_hash,
                                    ":spentAt": stamp,
                                    ":unspent": "unspent",
                                    ":userId": user_id,
                                }
                            ),
                        }
                    },
                    {
                        "Put": {
                            "TableName": world.name,
                            "Item": _ddb_map(dynamo_safe(parcel_item)),
                            "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                        }
                    },
                    {
                        "Put": {
                            "TableName": world.name,
                            "Item": _ddb_map(dynamo_safe(region_item)),
                            "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                        }
                    },
                ]
            )
        except ClientError as exc:
            code = (exc.response.get("Error") or {}).get("Code")
            if code in ("TransactionCanceledException", "ConditionalCheckFailedException"):
                occupied = world.get_item(
                    Key=parcel_key(world_id, parcel_id),
                    ConsistentRead=True,
                ).get("Item")
                return response(
                    409,
                    {
                        "error": (
                            "That Shaelvien parcel has already been claimed"
                            if occupied
                            else "The Shaelvien Token was already spent or changed"
                        )
                    },
                )
            raise

        audit_write(
            world_id,
            user_id,
            "parcel.claim",
            parcel_id,
            {
                "cellIndex": cell_index,
                "regionId": region_id,
                "pixelWidth": MMO_PARCEL_PIXELS,
                "pixelHeight": MMO_PARCEL_PIXELS,
                "maxHeight": MMO_PARCEL_MAX_HEIGHT,
                "bindingHash": binding_hash,
            },
        )
        return response(200, public_parcel(parcel_item))

    if method == "POST" and path == "/world/parcels/delegate":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        parcel_id = safe_id(req.get("parcelId"), "parcelId")
        target = safe_id(req.get("userId"), "userId")
        permission = str(req.get("permission") or "None").strip().title()
        if permission not in PARCEL_DELEGATION_PERMISSIONS:
            return response(400, {"error": "Invalid parcel permission"})
        parcel = world.get_item(
            Key=parcel_key(world_id, parcel_id),
            ConsistentRead=True,
        ).get("Item")
        if not parcel:
            return response(404, {"error": "Shaelvien parcel not found"})
        parcel_owner = str(parcel.get("ownerUserId") or "")
        parcel_manage = parcel_permission(world_id, parcel_id, user_id) == "Manage"
        if parcel_owner != user_id and not can_manage(world_id, user_id) and not parcel_manage:
            return response(403, {"error": "Parcel owner or Manage permission is required"})

        acl_key = parcel_acl_key(world_id, parcel_id, target)
        if permission == "None":
            world.delete_item(Key=acl_key)
        else:
            world.put_item(
                Item={
                    **acl_key,
                    "worldId": world_id,
                    "parcelId": parcel_id,
                    "userId": target,
                    "permission": permission,
                    "grantedByUserId": user_id,
                    "updatedAtUtc": utc_stamp(),
                }
            )
        audit_write(
            world_id,
            user_id,
            "parcel.delegate",
            parcel_id,
            {"target": target, "permission": permission},
        )
        return response(200, {"ok": True, "parcelId": parcel_id, "userId": target, "permission": permission})

    if method == "GET" and path == "/world/parcels/delegations":
        world_id = safe_id(q.get("worldId"), "worldId")
        parcel_id = safe_id(q.get("parcelId"), "parcelId")
        parcel = world.get_item(
            Key=parcel_key(world_id, parcel_id),
            ConsistentRead=True,
        ).get("Item")
        if not parcel:
            return response(404, {"error": "Shaelvien parcel not found"})
        if str(parcel.get("ownerUserId") or "") != user_id and not can_manage(world_id, user_id):
            return response(403, {"error": "Parcel owner authority required"})
        items = query_world_prefix(world_id, "PARCELACL#" + parcel_id + "#USER#")
        items.sort(key=lambda item: str(item.get("userId") or ""))
        return response(
            200,
            [
                {
                    "parcelId": str(item.get("parcelId") or ""),
                    "userId": str(item.get("userId") or ""),
                    "permission": str(item.get("permission") or "None"),
                    "updatedAtUtc": str(item.get("updatedAtUtc") or ""),
                }
                for item in items
            ],
        )

    if method == "GET" and path == "/world/source":
        world_id = safe_id(q.get("worldId"), "worldId")
        if not can_view(world_id, user_id):
            return response(403, {"error": "World access required"})
        item = world.get_item(
            Key=world_source_key(world_id), ConsistentRead=True
        ).get("Item")
        if not item:
            return response(
                200,
                {
                    "worldId": world_id,
                    "state": None,
                    "updatedAtUtc": "",
                },
            )
        return response(
            200,
            {
                "worldId": world_id,
                "state": item.get("state"),
                "updatedAtUtc": str(item.get("updatedAtUtc") or ""),
            },
        )

    if method == "POST" and path == "/world/source":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        if not can_manage(world_id, user_id):
            return response(403, {"error": "World Builder authority required"})
        state = req.get("state")
        if not isinstance(state, dict):
            return response(400, {"error": "World source state must be an object"})
        state_world_id = str(state.get("worldId") or "").strip()
        if state_world_id and state_world_id != world_id:
            return response(400, {"error": "World source identity mismatch"})
        # DynamoDB items are capped at 400 KB. Keep the shared WorldBuilder source
        # comfortably below that ceiling; image bytes belong in asset storage and
        # the database stores only authored map metadata and asset references.
        encoded_size = len(
            json.dumps(state, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        )
        if encoded_size > 320000:
            return response(
                413,
                {
                    "error": (
                        "World source metadata is too large for the database. "
                        "Publish uploaded image bytes to asset storage and save again."
                    )
                },
            )
        updated_at = datetime.now(timezone.utc).isoformat()
        safe_state = dynamo_safe(state)
        world.put_item(
            Item={
                **world_source_key(world_id),
                "entityType": "worldSource",
                "worldId": world_id,
                "state": safe_state,
                "updatedAtUtc": updated_at,
                "updatedByUserId": user_id,
            }
        )
        audit_write(
            world_id,
            user_id,
            "world.source.save",
            "WORLDSOURCE",
            {"bytes": encoded_size},
        )
        return response(
            200,
            {
                "worldId": world_id,
                "state": safe_state,
                "updatedAtUtc": updated_at,
            },
        )

    if method == "GET" and path == "/world/regions":
        world_id = safe_id(q.get("worldId"), "worldId")
        if not can_view(world_id, user_id):
            return response(403, {"error": "World access required"})
        regions = []
        for item in query_world_prefix(world_id, "REGION#"):
            state = dict(item.get("state") or {})
            state["ownerUserId"] = str(
                item.get("ownerUserId") or state.get("ownerUserId") or ""
            )
            regions.append(state)
        regions.sort(key=lambda region: str(region.get("name") or "").lower())
        return response(200, regions)

    if method == "POST" and path == "/world/regions":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        region = req.get("region") or {}
        if not isinstance(region, dict):
            return response(400, {"error": "Region payload must be an object"})
        region_id = safe_id(region.get("regionId"), "regionId")
        key = region_key(world_id, region_id)
        current = world.get_item(Key=key, ConsistentRead=True).get("Item")
        manager = can_manage(world_id, user_id)
        owner = str(
            (current or {}).get("ownerUserId") or region.get("ownerUserId") or ""
        )
        if current:
            state = current.get("state") or {}
            parcel_id = str(current.get("parcelId") or state.get("parcelId") or "")
            delegated = bool(parcel_id and can_edit_parcel(world_id, parcel_id, user_id))
            if not (manager or owner == user_id or delegated):
                return response(403, {"error": "Region edit authority required"})
        elif not manager:
            return response(
                403, {"error": "Only a GM/owner may create a region directly"}
            )
        if not owner:
            owner = user_id

        # A token-purchased MMO parcel is permanent world truth. Region editors may
        # change its contents, but may not enlarge its square, raise its height,
        # rewrite its token binding, or transfer ownership through a region save.
        current_state = dict((current or {}).get("state") or {})
        current_parcel_id = str(
            (current or {}).get("parcelId")
            or current_state.get("parcelId")
            or region.get("parcelId")
            or ""
        )
        if current_parcel_id:
            parcel = world.get_item(
                Key=parcel_key(world_id, current_parcel_id),
                ConsistentRead=True,
            ).get("Item")
            if not parcel:
                return response(409, {"error": "Parcel authority record is missing"})
            owner = str(parcel.get("ownerUserId") or owner)
            column = int(parcel.get("column") or 0)
            row = int(parcel.get("row") or 0)
            cell_index = int(parcel.get("cellIndex") or (row * MMO_PARCEL_GRID_COLUMNS + column))
            region["parcelId"] = current_parcel_id
            region["minColumn"] = column
            region["minRow"] = row
            region["maxColumn"] = column
            region["maxRow"] = row
            region["selectedCells"] = [cell_index]
            region["tierIndex"] = 0
            region["sourceLayerOffsets"] = list(range(MMO_PARCEL_MAX_HEIGHT))
            region["gridShape"] = "square"
            region["parcelPixelWidth"] = MMO_PARCEL_PIXELS
            region["parcelPixelHeight"] = MMO_PARCEL_PIXELS
            region["maxHeight"] = MMO_PARCEL_MAX_HEIGHT

        region["worldId"] = world_id
        region["regionId"] = region_id
        region["ownerUserId"] = owner
        region["updatedAtUtc"] = utc_stamp()
        world.put_item(
            Item={
                **key,
                "worldId": world_id,
                "regionId": region_id,
                "ownerUserId": owner,
                "state": dynamo_safe(region),
                "updatedAt": now,
            }
        )
        audit_write(
            world_id,
            user_id,
            "region.save",
            region_id,
            {"ownerUserId": owner},
        )
        return response(200, region)

    if method == "GET" and path == "/world/entity":
        world_id = safe_id(q.get("worldId"), "worldId")
        entity_id = safe_id(q.get("entityId"), "entityId")
        if not can_view(world_id, user_id):
            return response(403, {"error": "World access required"})
        item = world.get_item(
            Key={"pk": "WORLD#" + world_id, "sk": "ENTITY#" + entity_id},
            ConsistentRead=True,
        ).get("Item")
        return response(200, item or {"worldId": world_id, "entityId": entity_id, "missing": True})

    if method == "POST" and path == "/world/mutate":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        entity_id = safe_id(req.get("entityId"), "entityId")
        return _mutate_world_entity(req, world_id, entity_id, user_id, now)

    if method == "POST" and path == "/realtime/ticket":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        if not can_view(world_id, user_id):
            return response(403, {"error": "World access required"})
        ticket = secrets.token_urlsafe(32)
        expires = now + 120
        realtime.put_item(Item={"pk": "TICKET#" + ticket, "userId": user_id, "worldId": world_id, "expiresAt": expires})
        return response(200, {"ticket": ticket, "expiresAt": expires})

    if method == "POST" and path == "/userdata/upload":
        req = body(event)
        raw = str(req.get("key") or "").replace("\\", "/").strip("/")
        if not raw or ".." in raw.split("/") or len(raw) > 512:
            return response(400, {"error": "Invalid key"})
        requested_world_id = user_world_id_from_key(raw)
        if requested_world_id and not can_claim_world_slot(user_id, requested_world_id):
            return response(403, {"error": "Additional world-slot entitlement required"})
        key = "users/" + user_id + "/" + raw
        content_type = req.get("contentType") or "application/octet-stream"
        post = s3.generate_presigned_post(
            Bucket=bucket,
            Key=key,
            Fields={
                "Content-Type": content_type,
                "x-amz-server-side-encryption": "aws:kms",
                "x-amz-server-side-encryption-aws-kms-key-id": kms_key,
            },
            Conditions=[
                {"Content-Type": content_type},
                {"x-amz-server-side-encryption": "aws:kms"},
                {"x-amz-server-side-encryption-aws-kms-key-id": kms_key},
                ["content-length-range", 1, 52428800],
            ],
            ExpiresIn=300,
        )
        return response(200, post)

    if method == "GET" and path == "/userdata/download":
        raw = urllib.parse.unquote(q.get("key") or "").replace("\\", "/").strip("/")
        if not raw or ".." in raw.split("/") or len(raw) > 512:
            return response(400, {"error": "Invalid key"})
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": "users/" + user_id + "/" + raw},
            ExpiresIn=300,
        )
        return response(200, {"url": url})

    return response(404, {"error": "Not found"})
