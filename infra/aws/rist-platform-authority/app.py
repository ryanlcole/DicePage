import hashlib
import json
import os
import secrets
import time
import urllib.parse
import uuid
from decimal import Decimal

import boto3

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
        users.put_item(
            Item={
                "pk": "USER#" + user_id,
                "sk": "PROFILE",
                "displayName": session["displayName"],
                "lastSeenAt": now,
            }
        )
        return response(
            200,
            {
                "userId": user_id,
                "displayName": session["displayName"],
                "platformOwner": bool(owner_user_id and user_id == owner_user_id),
            },
        )

    if method == "GET" and path == "/world/membership":
        world_id = safe_id(q.get("worldId"), "worldId")
        if is_geonaph(world_id):
            if owner_user_id and user_id == owner_user_id:
                return response(200, {"worldId": world_id, "role": "owner", "effectiveAuthority": "platformOwner"})
            # Geonaph is readable/explorable by every authenticated RIST user.
            # Stale or accidental GM membership rows must never elevate Geonaph.
            return response(200, {"worldId": world_id, "role": "viewer", "effectiveAuthority": "publicViewer"})
        item = membership(world_id, user_id)
        if item:
            return response(200, item)
        if owner_user_id and user_id == owner_user_id:
            return response(200, {"worldId": world_id, "role": "owner", "effectiveAuthority": "platformOwner"})
        return response(200, {"worldId": world_id, "role": "none"})

    if method == "POST" and path == "/world/membership/grant":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        target = safe_id(req.get("userId"), "userId")
        role = req.get("role")
        if role not in ("viewer", "player", "GM", "owner"):
            return response(400, {"error": "Invalid role"})
        if is_geonaph(world_id):
            if not (owner_user_id and user_id == owner_user_id):
                return response(403, {"error": "Geonaph authority is reserved to the platform owner"})
            if role in ("GM", "owner") and target != owner_user_id:
                return response(403, {"error": "Geonaph GM authority cannot be delegated"})
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
                "updatedAt": now,
            }
        )
        audit_write(world_id, user_id, "membership.grant", details={"target": target, "role": role})
        return response(200, {"ok": True})

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
