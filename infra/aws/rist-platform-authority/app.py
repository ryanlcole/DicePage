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


def utc_stamp():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
        "body": "" if body is None else json.dumps(body, separators=(",", ":"), default=str),
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
            if not (manager or owner == user_id):
                return response(403, {"error": "Region edit authority required"})
        elif not manager:
            return response(
                403, {"error": "Only a GM/owner may create a region directly"}
            )
        if not owner:
            owner = user_id

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
