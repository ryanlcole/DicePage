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
from botocore.exceptions import ClientError

from mutation_policy import canonical_piece_state, dynamo_safe, protects_piece
from region_geometry import region_cell_for_point
from region_projection import (
    normalize_region_layer,
    project as project_region_source,
)


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
PARCEL_RELEASE_REFUNDS_ENABLED = str(os.environ.get("PARCEL_RELEASE_REFUNDS_ENABLED", "true")).strip().lower() not in {"0", "false", "no", "off"}

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

# Commerce is deliberately authority-first. Paid providers may fulfill these
# records later, but a browser can never manufacture a subscription, access
# grant, Kickstarter reward, or Shaelvien Token by changing client state.
WORLD_TOKEN_SK_PREFIX = "WORLD_TOKEN#"
COMMERCE_GRANT_SK_PREFIX = "ENTITLEMENT#"
COMMERCE_INVITES_PK = "COMMERCE#INVITES"
COMMERCE_INVITE_SK_PREFIX = "INVITE#"
COMMERCE_INVITE_MAX_DAYS = 3650
COMMERCE_INVITE_MAX_TOKENS = 5
COMMERCE_PLANS = {
    "dedicated-roleplayer": {
        "displayName": "Dedicated Roleplayer",
        "monthlyUsdCents": 0,
        "entitlements": ["access.roleplayer.online"],
    },
    "standard-roleplayer": {
        "displayName": "Standard Roleplayer",
        "monthlyUsdCents": 500,
        "entitlements": ["access.roleplayer.online"],
    },
    "gamemaster": {
        "displayName": "GameMaster",
        "monthlyUsdCents": 1000,
        "entitlements": ["access.roleplayer.online", "access.gamemaster"],
    },
    "storyteller": {
        "displayName": "Storyteller",
        "monthlyUsdCents": 1500,
        "entitlements": [
            "access.roleplayer.online",
            "access.gamemaster",
            "access.storyteller",
        ],
    },
    "worldbuilder": {
        "displayName": "Worldbuilder",
        "monthlyUsdCents": 2000,
        "entitlements": [
            "access.roleplayer.online",
            "access.gamemaster",
            "access.storyteller",
            "access.worldbuilder",
        ],
    },
}

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


def region_map_key(world_id, region_id):
    return {"pk": world_partition(world_id), "sk": "REGIONMAP#" + region_id}


REGION_Z_MODEL = "world-int-region-hundredth-v1"
REGION_Z_RESET_MARKER = "MIGRATION#20260924_REGION_Z100_RESET_V1"
_region_z_reset_checked = False


def ensure_region_z_reset():
    """One-time project-owner-authorized reset of old Geonaph regions."""
    global _region_z_reset_checked
    if _region_z_reset_checked:
        return

    marker_key = {
        "pk": world_partition(GEONAPH_WORLD_ID),
        "sk": REGION_Z_RESET_MARKER,
    }
    if world.get_item(Key=marker_key, ConsistentRead=True).get("Item"):
        _region_z_reset_checked = True
        return

    removed_records = 0
    with world.batch_writer() as batch:
        for prefix in ("REGION#", "REGIONMAP#"):
            for item in query_world_prefix(GEONAPH_WORLD_ID, prefix):
                batch.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
                removed_records += 1

    removed_layers = 0
    source_key = world_source_key(GEONAPH_WORLD_ID)
    source = world.get_item(Key=source_key, ConsistentRead=True).get("Item")
    if source and isinstance(source.get("state"), dict):
        state = dict(source["state"])
        layers = state.get("userLayers") or []
        if isinstance(layers, list):
            kept = [
                item for item in layers
                if not (isinstance(item, dict) and str(item.get("regionId") or ""))
            ]
            removed_layers = len(layers) - len(kept)
            if removed_layers:
                state["userLayers"] = kept
                world.update_item(
                    Key=source_key,
                    UpdateExpression=(
                        "SET #state = :state, updatedAtUtc = :updated, "
                        "updatedByUserId = :by"
                    ),
                    ExpressionAttributeNames={"#state": "state"},
                    ExpressionAttributeValues={
                        ":state": dynamo_safe(state),
                        ":updated": datetime.now(timezone.utc).isoformat(),
                        ":by": "system:region-z100-reset",
                    },
                )

    world.put_item(Item={
        **marker_key,
        "entityType": "migration",
        "migration": REGION_Z_RESET_MARKER,
        "removedRegionRecords": removed_records,
        "removedRegionLayers": removed_layers,
        "createdAtUtc": datetime.now(timezone.utc).isoformat(),
    })
    _region_z_reset_checked = True


def world_token_key(user_id):
    """Legacy genesis token key retained for compatibility."""
    return {"pk": "USER#" + user_id, "sk": GENESIS_WORLD_TOKEN_SK}


def purchased_world_token_key(user_id, token_id):
    return {
        "pk": "USER#" + user_id,
        "sk": WORLD_TOKEN_SK_PREFIX + safe_id(token_id, "tokenId"),
    }


def query_user_prefix(user_id, prefix):
    result = users.query(
        KeyConditionExpression=Key("pk").eq("USER#" + user_id)
        & Key("sk").begins_with(prefix)
    )
    return result.get("Items", [])


def query_world_tokens(user_id):
    items = query_user_prefix(user_id, WORLD_TOKEN_SK_PREFIX)
    items.sort(key=lambda item: str(item.get("createdAtUtc") or ""))
    return items


def world_token_by_id(user_id, token_id):
    token_id = str(token_id or "").strip()
    if not token_id:
        return None
    for item in query_world_tokens(user_id):
        if str(item.get("tokenId") or "") == token_id:
            return item
    return None


def spendable_world_token(user_id, requested_token_id=""):
    requested_token_id = str(requested_token_id or "").strip()
    if requested_token_id:
        token = world_token_by_id(user_id, requested_token_id)
        return token if token and str(token.get("status") or "") == "unspent" else token
    return next(
        (
            item
            for item in query_world_tokens(user_id)
            if str(item.get("status") or "") == "unspent"
        ),
        None,
    )


def world_token_for_parcel(user_id, parcel_id):
    return next(
        (
            item
            for item in query_world_tokens(user_id)
            if str(item.get("status") or "") == "spent"
            and str(item.get("parcelId") or "") == str(parcel_id or "")
        ),
        None,
    )


def normalize_unspent_world_token(user_id, token):
    if not token or str(token.get("status") or "") != "unspent":
        return token
    key = {"pk": str(token.get("pk") or ""), "sk": str(token.get("sk") or "")}
    if not key["pk"] or not key["sk"]:
        return token

    account_half = str(token.get("accountHalfCode") or "")
    expected_hash = hashlib.sha256(account_half.encode()).hexdigest() if account_half else ""
    holder_ok = str(token.get("holderUserId") or "") == user_id
    class_ok = str(token.get("tokenClass") or "") == SHAELVIEN_TOKEN_CLASS
    hash_ok = bool(account_half) and str(token.get("accountHalfHash") or "") == expected_hash

    # A valid token must be read-only on the claim path until the atomic spend.
    # Rewriting it immediately before TransactWriteItems creates needless
    # contention on the exact item the transaction is about to update.
    if holder_ok and class_ok and hash_ok:
        return token

    if not account_half:
        candidate_half = secrets.token_hex(32)
        try:
            users.update_item(
                Key=key,
                UpdateExpression=(
                    "SET holderUserId = :userId, tokenClass = :tokenClass, "
                    "accountHalfCode = :code, accountHalfHash = :hash"
                ),
                ConditionExpression="#status = :unspent AND attribute_not_exists(accountHalfCode)",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":userId": user_id,
                    ":tokenClass": SHAELVIEN_TOKEN_CLASS,
                    ":code": candidate_half,
                    ":hash": hashlib.sha256(candidate_half.encode()).hexdigest(),
                    ":unspent": "unspent",
                },
            )
        except ClientError as exc:
            if (exc.response.get("Error") or {}).get("Code") != "ConditionalCheckFailedException":
                raise
    else:
        try:
            users.update_item(
                Key=key,
                UpdateExpression=(
                    "SET holderUserId = :userId, tokenClass = :tokenClass, "
                    "accountHalfHash = :hash"
                ),
                ConditionExpression="#status = :unspent",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":userId": user_id,
                    ":tokenClass": SHAELVIEN_TOKEN_CLASS,
                    ":hash": expected_hash,
                    ":unspent": "unspent",
                },
            )
        except ClientError as exc:
            if (exc.response.get("Error") or {}).get("Code") != "ConditionalCheckFailedException":
                raise
    return users.get_item(Key=key, ConsistentRead=True).get("Item") or token


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


def ghost_zone_key(world_id, ghost_id):
    return {
        "pk": world_partition(world_id),
        "sk": "GHOSTZONE#" + safe_id(ghost_id, "ghostId"),
    }


def active_ghost_zones(world_id):
    return [
        item
        for item in query_world_prefix(world_id, "GHOSTZONE#")
        if not str(item.get("reclaimedAtUtc") or "")
    ]


def public_ghost_zone(item, user_id=""):
    if not item:
        return None
    return {
        "ghostId": str(item.get("ghostId") or ""),
        "worldId": str(item.get("worldId") or ""),
        "cellIndex": int(item.get("cellIndex") or 0),
        "column": int(item.get("column") or 0),
        "row": int(item.get("row") or 0),
        "releasedAtUtc": str(item.get("releasedAtUtc") or ""),
        "status": "ghost",
        "ownedByYou": bool(user_id and str(item.get("ownerUserId") or "") == user_id),
    }


def public_world_token(item):
    if not item:
        return None
    return {
        "tokenId": str(item.get("tokenId") or ""),
        "tokenClass": str(item.get("tokenClass") or SHAELVIEN_TOKEN_CLASS),
        "status": str(item.get("status") or "unspent"),
        "holderUserId": str(item.get("holderUserId") or ""),
        "purchasedWorldId": str(item.get("purchasedWorldId") or ""),
        "parcelId": str(item.get("parcelId") or ""),
        "bindingHash": str(item.get("bindingHash") or ""),
        "createdAtUtc": str(item.get("createdAtUtc") or ""),
        "spentAtUtc": str(item.get("spentAtUtc") or ""),
        "source": str(item.get("source") or ""),
        "sourceReference": str(item.get("sourceReference") or ""),
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


def ensure_parcel_region(world_id, parcel, now_value=None):
    """Reconcile the editable region that represents an already-owned parcel.

    Token + parcel are the atomic ownership identity. The region is a derived
    representation and must never be allowed to veto that ownership transaction.
    """
    parcel_id = str(parcel.get("parcelId") or "")
    region_id = str(parcel.get("regionId") or ("region-" + parcel_id))
    owner = str(parcel.get("ownerUserId") or "")
    column = int(parcel.get("column") or 0)
    row = int(parcel.get("row") or 0)
    display_name = str(parcel.get("displayName") or f"Shaelvien {column},{row}")
    now_value = int(time.time()) if now_value is None else int(now_value)
    key = region_key(world_id, region_id)
    existing = world.get_item(Key=key, ConsistentRead=True).get("Item") or {}
    state = dict(existing.get("state") or {})

    canonical = {
        "regionId": region_id,
        "worldId": world_id,
        "name": str(state.get("name") or display_name),
        "minColumn": column,
        "minRow": row,
        "maxColumn": column,
        "maxRow": row,
        "selectedCells": [int(parcel.get("cellIndex") or 0)],
        "createdAtUtc": str(state.get("createdAtUtc") or parcel.get("claimedAtUtc") or utc_stamp()),
        "updatedAtUtc": utc_stamp(),
        "tierIndex": int(state.get("tierIndex") or 0),
        "sourceLayerOffsets": list(range(MMO_PARCEL_MAX_HEIGHT)),
        "gridShape": str(state.get("gridShape") or "square"),
        "ownerUserId": owner,
        "parcelId": parcel_id,
        "parcelPixelWidth": int(parcel.get("pixelWidth") or MMO_PARCEL_PIXELS),
        "parcelPixelHeight": int(parcel.get("pixelHeight") or MMO_PARCEL_PIXELS),
        "maxHeight": int(parcel.get("maxHeight") or MMO_PARCEL_MAX_HEIGHT),
        "parentNodeId": "world:" + world_id,
        "coordinateSpace": "world-normalized-v1",
        "canonicalMinX": column / MMO_PARCEL_GRID_COLUMNS,
        "canonicalMinY": row / MMO_PARCEL_GRID_ROWS,
        "canonicalMaxX": (column + 1) / MMO_PARCEL_GRID_COLUMNS,
        "canonicalMaxY": (row + 1) / MMO_PARCEL_GRID_ROWS,
        "canonicalZMin": 0,
        "canonicalZMax": MMO_PARCEL_MAX_HEIGHT,
    }
    # Preserve authored region content while enforcing parcel identity/geometry.
    canonical["sourceTiles"] = list(state.get("sourceTiles") or [])
    canonical["overlayTiles"] = list(state.get("overlayTiles") or [])
    merged_state = {**state, **canonical}
    item = {
        **existing,
        **key,
        "worldId": world_id,
        "regionId": region_id,
        "parcelId": parcel_id,
        "ownerUserId": owner,
        "state": dynamo_safe(merged_state),
        "updatedAt": now_value,
    }
    world.put_item(Item=dynamo_safe(item))
    return item


def ensure_genesis_world_token(user_id, account_id, player_alias):
    key = world_token_key(user_id)
    current = users.get_item(Key=key, ConsistentRead=True).get("Item")
    if current:
        # Legacy unspent tokens created before split-code binding did not have
        # accountHalfCode/accountHalfHash. Upgrade those records in place so the
        # user's original free token remains valid rather than failing with 409.
        if (
            str(current.get("status") or "") == "unspent"
            and not str(current.get("accountHalfCode") or "")
        ):
            account_half = secrets.token_hex(32)
            try:
                users.update_item(
                    Key=key,
                    UpdateExpression=(
                        "SET accountHalfCode = :code, accountHalfHash = :hash, "
                        "profileAccountId = :accountId, profileAlias = :alias"
                    ),
                    ConditionExpression=(
                        "#status = :unspent AND holderUserId = :userId "
                        "AND attribute_not_exists(accountHalfCode)"
                    ),
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":code": account_half,
                        ":hash": hashlib.sha256(account_half.encode()).hexdigest(),
                        ":accountId": str(account_id or "")[:160],
                        ":alias": str(player_alias or "")[:80],
                        ":unspent": "unspent",
                        ":userId": user_id,
                    },
                )
            except ClientError as exc:
                if (exc.response.get("Error") or {}).get("Code") != "ConditionalCheckFailedException":
                    raise
            current = users.get_item(Key=key, ConsistentRead=True).get("Item") or current
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


def _new_world_token_item(user_id, source, reference="", created_by=""):
    profile = users.get_item(
        Key={"pk": "USER#" + user_id, "sk": "PROFILE"},
        ConsistentRead=True,
    ).get("Item") or {}
    token_id = "swt_" + uuid.uuid4().hex
    account_half = secrets.token_hex(32)
    return {
        **purchased_world_token_key(user_id, token_id),
        "tokenId": token_id,
        "tokenClass": SHAELVIEN_TOKEN_CLASS,
        "status": "unspent",
        "holderUserId": user_id,
        "accountHalfCode": account_half,
        "accountHalfHash": hashlib.sha256(account_half.encode()).hexdigest(),
        "profileAccountId": str(profile.get("profileAccountId") or "")[:160],
        "profileAlias": str(profile.get("playerAlias") or profile.get("displayName") or "")[:80],
        "createdAtUtc": utc_stamp(),
        "spentAtUtc": "",
        "purchasedWorldId": "",
        "parcelId": "",
        "bindingHash": "",
        "source": str(source or "commerce")[:40],
        "sourceReference": str(reference or "")[:160],
        "createdByUserId": str(created_by or "")[:160],
    }


def mint_world_token(user_id, source, reference="", created_by=""):
    item = _new_world_token_item(user_id, source, reference, created_by)
    users.put_item(
        Item=item,
        ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
    )
    return item


def commerce_plan(plan_id):
    plan_id = str(plan_id or "").strip().lower()
    plan = COMMERCE_PLANS.get(plan_id)
    if not plan:
        raise ValueError("Unknown commerce plan")
    return plan_id, plan


def entitlement_grant_key(user_id, grant_id):
    return {
        "pk": "USER#" + user_id,
        "sk": COMMERCE_GRANT_SK_PREFIX + safe_id(grant_id, "grantId"),
    }


def _grant_expiry(now, expires_in_days):
    try:
        days = int(expires_in_days or 0)
    except (TypeError, ValueError):
        raise ValueError("Invalid access expiry")
    if days < 0 or days > COMMERCE_INVITE_MAX_DAYS:
        raise ValueError("Invalid access expiry")
    return 0 if days == 0 else now + days * 86400


def _new_entitlement_grant(
    user_id,
    plan_id,
    source,
    created_by,
    expires_at_epoch=0,
    label="",
    invite_id="",
):
    plan_id, plan = commerce_plan(plan_id)
    grant_id = "grant_" + uuid.uuid4().hex
    return {
        **entitlement_grant_key(user_id, grant_id),
        "grantId": grant_id,
        "holderUserId": user_id,
        "planId": plan_id,
        "entitlements": list(plan["entitlements"]),
        "source": str(source or "complimentary")[:40],
        "label": str(label or "")[:120],
        "inviteId": str(invite_id or "")[:160],
        "createdByUserId": str(created_by or "")[:160],
        "createdAtUtc": utc_stamp(),
        "createdAtEpoch": int(time.time()),
        "expiresAtEpoch": int(expires_at_epoch or 0),
        "revokedAtUtc": "",
    }


def public_entitlement_grant(item):
    if not item:
        return None
    return {
        "grantId": str(item.get("grantId") or ""),
        "planId": str(item.get("planId") or ""),
        "entitlements": [str(value) for value in (item.get("entitlements") or [])],
        "source": str(item.get("source") or ""),
        "label": str(item.get("label") or ""),
        "inviteId": str(item.get("inviteId") or ""),
        "createdAtUtc": str(item.get("createdAtUtc") or ""),
        "expiresAtEpoch": int(item.get("expiresAtEpoch") or 0),
        "revokedAtUtc": str(item.get("revokedAtUtc") or ""),
    }


def active_entitlement_grants(user_id, now=None):
    now = int(time.time()) if now is None else int(now)
    result = []
    for item in query_user_prefix(user_id, COMMERCE_GRANT_SK_PREFIX):
        if str(item.get("revokedAtUtc") or ""):
            continue
        try:
            expires = int(item.get("expiresAtEpoch") or 0)
        except (TypeError, ValueError):
            continue
        if expires and expires <= now:
            continue
        result.append(item)
    return result


def merge_commercial_entitlements(user_id, profile, now=None):
    merged = dict(profile or {})
    values = {
        str(value).strip()
        for value in (merged.get("entitlements") or [])
        if str(value).strip()
    }
    for grant in active_entitlement_grants(user_id, now):
        values.update(
            str(value).strip()
            for value in (grant.get("entitlements") or [])
            if str(value).strip()
        )
    merged["entitlements"] = sorted(values)
    return merged


def commerce_summary(user_id, profile=None):
    profile = profile or users.get_item(
        Key={"pk": "USER#" + user_id, "sk": "PROFILE"},
        ConsistentRead=True,
    ).get("Item") or {}
    grants = active_entitlement_grants(user_id)
    merged = merge_commercial_entitlements(user_id, profile)
    tokens = query_world_tokens(user_id)
    return {
        "entitlements": commercial_profile(
            merged,
            bool(owner_user_id and user_id == owner_user_id),
        )["entitlements"],
        "plans": [
            {
                "planId": plan_id,
                "displayName": str(plan.get("displayName") or plan_id),
                "monthlyUsdCents": int(plan.get("monthlyUsdCents") or 0),
                "entitlements": list(plan.get("entitlements") or []),
            }
            for plan_id, plan in COMMERCE_PLANS.items()
        ],
        "grants": [public_entitlement_grant(item) for item in grants],
        "tokens": [public_world_token(item) for item in tokens],
        "unspentTokenCount": sum(
            1 for item in tokens if str(item.get("status") or "") == "unspent"
        ),
    }


def commerce_invite_key(invite_id):
    return {
        "pk": COMMERCE_INVITES_PK,
        "sk": COMMERCE_INVITE_SK_PREFIX + safe_id(invite_id, "inviteId"),
    }


def parse_commerce_invite_code(code):
    code = str(code or "").strip()
    parts = code.split("_")
    if len(parts) != 3 or parts[0] != "rci":
        raise ValueError("Invalid access link")
    invite_id = safe_id(parts[1], "inviteId")
    if len(parts[2]) < 24:
        raise ValueError("Invalid access link")
    return invite_id, code


def public_commerce_invite(item):
    if not item:
        return None
    status = "available"
    now = int(time.time())
    if str(item.get("revokedAtUtc") or ""):
        status = "revoked"
    elif str(item.get("redeemedAtUtc") or ""):
        status = "redeemed"
    elif int(item.get("expiresAtEpoch") or 0) and int(item.get("expiresAtEpoch") or 0) <= now:
        status = "expired"
    return {
        "inviteId": str(item.get("inviteId") or ""),
        "planId": str(item.get("planId") or ""),
        "label": str(item.get("label") or ""),
        "tokenQuantity": int(item.get("tokenQuantity") or 0),
        "status": status,
        "createdAtUtc": str(item.get("createdAtUtc") or ""),
        "expiresAtEpoch": int(item.get("expiresAtEpoch") or 0),
        "redeemedAtUtc": str(item.get("redeemedAtUtc") or ""),
        "redeemedUserId": str(item.get("redeemedUserId") or ""),
        "redeemedGrantId": str(item.get("redeemedGrantId") or ""),
        "revokedAtUtc": str(item.get("revokedAtUtc") or ""),
    }


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


def editable_region_state(world_id, region_id, user_id):
    item = world.get_item(
        Key=region_key(world_id, region_id),
        ConsistentRead=True,
    ).get("Item")
    if not item:
        return None
    state = dict(item.get("state") or {})
    owner = str(item.get("ownerUserId") or state.get("ownerUserId") or "")
    parcel_id = str(item.get("parcelId") or state.get("parcelId") or "")
    if can_manage(world_id, user_id) or owner == user_id:
        return state
    if parcel_id and can_edit_parcel(world_id, parcel_id, user_id):
        return state
    return None


def validate_region_map_layer(region_state, layer, region_id=""):
    normalized = normalize_region_layer(
        region_state, layer, region_id or str(layer.get("regionId") or "region")
    )
    layer.clear()
    layer.update(normalized)
    return layer


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


def can_discover_mmo_parcel(world_id, parcel, user_id):
    """Server-authoritative Shaelvien zone discovery.

    Draft user-created zones are private to the creator, Shaelvien managers/GMs,
    explicit invite/delegation recipients, and users with recorded visit access.
    Published/open-player zones are discoverable by all authenticated players.
    """
    if not parcel:
        return False
    parcel_id = str(parcel.get("parcelId") or "")
    if str(parcel.get("ownerUserId") or "") == user_id:
        return True
    if user_id in manager_user_ids(world_id):
        return True
    if parcel_permission(world_id, parcel_id, user_id) in ("View", "Edit", "Manage"):
        return True
    if bool(parcel.get("published")) or bool(parcel.get("openToPlayers")):
        return True
    visit = world.get_item(
        Key={
            "pk": world_partition(world_id),
            "sk": f"PARCELVISIT#{parcel_id}#USER#{user_id}",
        }
    ).get("Item")
    return bool(visit)


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
    commercial = commercial_profile(merge_commercial_entitlements(user_id, profile), False)
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
    # The exact-Z reset was a one-time migration, not request-time behavior.
    # Never run destructive region cleanup from an authenticated API request:
    # newly authored deeds/overlays must survive Lambda cold starts.
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
        tokens = [
            normalize_unspent_world_token(user_id, item)
            for item in query_world_tokens(user_id)
        ]
        return response(
            200,
            [public_world_token(item) for item in tokens],
        )

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
        commercial = commercial_profile(
            merge_commercial_entitlements(user_id, existing_profile),
            platform_owner,
        )
        return response(
            200,
            {
                "userId": user_id,
                "displayName": session["displayName"],
                "platformOwner": platform_owner,
                **commercial,
            },
        )


    if method == "GET" and path == "/authority/commerce":
        profile = users.get_item(
            Key={"pk": "USER#" + user_id, "sk": "PROFILE"},
            ConsistentRead=True,
        ).get("Item") or {}
        return response(200, commerce_summary(user_id, profile))

    if method == "GET" and path == "/authority/commerce/invites":
        if not (owner_user_id and user_id == owner_user_id):
            return response(403, {"error": "Platform owner authority required"})
        result = users.query(
            KeyConditionExpression=Key("pk").eq(COMMERCE_INVITES_PK)
            & Key("sk").begins_with(COMMERCE_INVITE_SK_PREFIX),
            ScanIndexForward=False,
            Limit=50,
        )
        return response(
            200,
            [public_commerce_invite(item) for item in result.get("Items", [])],
        )

    if method == "POST" and path == "/authority/commerce/invites":
        if not (owner_user_id and user_id == owner_user_id):
            return response(403, {"error": "Platform owner authority required"})
        req = body(event)
        try:
            plan_id, _ = commerce_plan(req.get("planId"))
            expires_at = _grant_expiry(now, req.get("expiresInDays", 365))
            token_quantity = int(req.get("tokenQuantity") or 0)
        except (TypeError, ValueError) as exc:
            return response(400, {"error": str(exc)})
        if token_quantity < 0 or token_quantity > COMMERCE_INVITE_MAX_TOKENS:
            return response(400, {"error": "Invalid token quantity"})

        invite_id = uuid.uuid4().hex[:16]
        code = f"rci_{invite_id}_{secrets.token_hex(18)}"
        item = {
            **commerce_invite_key(invite_id),
            "inviteId": invite_id,
            "codeHash": hashlib.sha256(code.encode()).hexdigest(),
            "planId": plan_id,
            "label": str(req.get("label") or "")[:120],
            "tokenQuantity": token_quantity,
            "createdByUserId": user_id,
            "createdAtUtc": utc_stamp(),
            "createdAtEpoch": now,
            "expiresAtEpoch": expires_at,
            "revokedAtUtc": "",
            "redeemedAtUtc": "",
            "redeemedUserId": "",
            "redeemedGrantId": "",
        }
        users.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )
        audit_write(
            "commerce",
            user_id,
            "commerce.invite.create",
            invite_id,
            {
                "planId": plan_id,
                "tokenQuantity": token_quantity,
                "expiresAtEpoch": expires_at,
            },
        )
        result = public_commerce_invite(item)
        result["code"] = code
        result["redeemUrl"] = (
            origin + "/Play/index.html?access=" + urllib.parse.quote(code, safe="")
        )
        return response(200, result)

    if method == "POST" and path == "/authority/commerce/invites/redeem":
        req = body(event)
        try:
            invite_id, code = parse_commerce_invite_code(req.get("code"))
        except ValueError as exc:
            return response(400, {"error": str(exc)})
        key = commerce_invite_key(invite_id)
        invite = users.get_item(Key=key, ConsistentRead=True).get("Item")
        if not invite or not secrets.compare_digest(
            str(invite.get("codeHash") or ""),
            hashlib.sha256(code.encode()).hexdigest(),
        ):
            return response(404, {"error": "Access link is not recognized"})
        if str(invite.get("revokedAtUtc") or ""):
            return response(409, {"error": "This access link has been revoked"})
        if str(invite.get("redeemedAtUtc") or ""):
            if str(invite.get("redeemedUserId") or "") == user_id:
                return response(
                    200,
                    {
                        "ok": True,
                        "alreadyRedeemed": True,
                        "grantId": str(invite.get("redeemedGrantId") or ""),
                        "planId": str(invite.get("planId") or ""),
                    },
                )
            return response(409, {"error": "This access link has already been used"})
        invite_expiry = int(invite.get("expiresAtEpoch") or 0)
        if invite_expiry and invite_expiry <= now:
            return response(409, {"error": "This access link has expired"})

        plan_id = str(invite.get("planId") or "")
        try:
            commerce_plan(plan_id)
        except ValueError:
            return response(409, {"error": "This access link references an unavailable plan"})
        grant = _new_entitlement_grant(
            user_id,
            plan_id,
            "complimentary",
            str(invite.get("createdByUserId") or owner_user_id),
            invite_expiry,
            str(invite.get("label") or ""),
            invite_id,
        )
        token_quantity = min(
            COMMERCE_INVITE_MAX_TOKENS,
            max(0, int(invite.get("tokenQuantity") or 0)),
        )
        token_items = [
            _new_world_token_item(
                user_id,
                "complimentary",
                "invite:" + invite_id,
                str(invite.get("createdByUserId") or owner_user_id),
            )
            for _ in range(token_quantity)
        ]
        transactions = [
            {
                "Update": {
                    "TableName": users.name,
                    "Key": key,
                    "UpdateExpression": (
                        "SET redeemedAtUtc = :stamp, redeemedUserId = :userId, "
                        "redeemedGrantId = :grantId"
                    ),
                    "ConditionExpression": (
                        "(attribute_not_exists(redeemedUserId) OR redeemedUserId = :empty) "
                        "AND (attribute_not_exists(revokedAtUtc) OR revokedAtUtc = :empty) "
                        "AND (expiresAtEpoch = :zero OR expiresAtEpoch > :now)"
                    ),
                    "ExpressionAttributeValues": {
                        ":stamp": utc_stamp(),
                        ":userId": user_id,
                        ":grantId": grant["grantId"],
                        ":empty": "",
                        ":zero": 0,
                        ":now": now,
                    },
                }
            },
            {
                "Put": {
                    "TableName": users.name,
                    "Item": dynamo_safe(grant),
                    "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                }
            },
        ]
        transactions.extend(
            {
                "Put": {
                    "TableName": users.name,
                    "Item": dynamo_safe(token),
                    "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                }
            }
            for token in token_items
        )
        try:
            ddb.meta.client.transact_write_items(TransactItems=transactions)
        except ClientError as exc:
            if (exc.response.get("Error") or {}).get("Code") in (
                "TransactionCanceledException",
                "ConditionalCheckFailedException",
            ):
                return response(409, {"error": "This access link changed before redemption completed"})
            raise

        notify_user(
            user_id,
            "commerce.access.granted",
            "commerce",
            {
                "planId": plan_id,
                "grantId": grant["grantId"],
                "tokenQuantity": token_quantity,
            },
        )
        audit_write(
            "commerce",
            user_id,
            "commerce.invite.redeem",
            invite_id,
            {
                "grantId": grant["grantId"],
                "planId": plan_id,
                "tokenQuantity": token_quantity,
            },
        )
        return response(
            200,
            {
                "ok": True,
                "alreadyRedeemed": False,
                "grantId": grant["grantId"],
                "planId": plan_id,
                "tokenQuantity": token_quantity,
            },
        )

    if method == "POST" and path == "/authority/commerce/invites/revoke":
        if not (owner_user_id and user_id == owner_user_id):
            return response(403, {"error": "Platform owner authority required"})
        req = body(event)
        try:
            invite_id = safe_id(req.get("inviteId"), "inviteId")
        except ValueError as exc:
            return response(400, {"error": str(exc)})
        key = commerce_invite_key(invite_id)
        invite = users.get_item(Key=key, ConsistentRead=True).get("Item")
        if not invite:
            return response(404, {"error": "Access invite not found"})
        stamp = utc_stamp()
        users.update_item(
            Key=key,
            UpdateExpression="SET revokedAtUtc = :stamp, revokedByUserId = :userId",
            ExpressionAttributeValues={":stamp": stamp, ":userId": user_id},
        )
        redeemed_user = str(invite.get("redeemedUserId") or "")
        redeemed_grant = str(invite.get("redeemedGrantId") or "")
        if redeemed_user and redeemed_grant:
            users.update_item(
                Key=entitlement_grant_key(redeemed_user, redeemed_grant),
                UpdateExpression="SET revokedAtUtc = :stamp, revokedByUserId = :userId",
                ExpressionAttributeValues={":stamp": stamp, ":userId": user_id},
            )
            notify_user(
                redeemed_user,
                "commerce.access.revoked",
                "commerce",
                {"inviteId": invite_id, "grantId": redeemed_grant},
            )
        audit_write(
            "commerce",
            user_id,
            "commerce.invite.revoke",
            invite_id,
            {"redeemedUserId": redeemed_user, "grantId": redeemed_grant},
        )
        refreshed = users.get_item(Key=key, ConsistentRead=True).get("Item") or invite
        return response(200, public_commerce_invite(refreshed))

    if method == "POST" and path == "/authority/commerce/grants":
        if not (owner_user_id and user_id == owner_user_id):
            return response(403, {"error": "Platform owner authority required"})
        req = body(event)
        try:
            target = safe_id(req.get("targetUserId"), "targetUserId")
            plan_id, _ = commerce_plan(req.get("planId"))
            expires_at = _grant_expiry(now, req.get("expiresInDays", 365))
        except ValueError as exc:
            return response(400, {"error": str(exc)})
        grant = _new_entitlement_grant(
            target,
            plan_id,
            str(req.get("source") or "complimentary"),
            user_id,
            expires_at,
            str(req.get("label") or ""),
        )
        users.put_item(
            Item=grant,
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )
        notify_user(
            target,
            "commerce.access.granted",
            "commerce",
            {"planId": plan_id, "grantId": grant["grantId"]},
        )
        audit_write(
            "commerce",
            user_id,
            "commerce.grant.create",
            grant["grantId"],
            {"targetUserId": target, "planId": plan_id},
        )
        return response(200, public_entitlement_grant(grant))

    if method == "POST" and path == "/authority/commerce/grants/revoke":
        if not (owner_user_id and user_id == owner_user_id):
            return response(403, {"error": "Platform owner authority required"})
        req = body(event)
        try:
            target = safe_id(req.get("targetUserId"), "targetUserId")
            grant_id = safe_id(req.get("grantId"), "grantId")
        except ValueError as exc:
            return response(400, {"error": str(exc)})
        key = entitlement_grant_key(target, grant_id)
        current = users.get_item(Key=key, ConsistentRead=True).get("Item")
        if not current:
            return response(404, {"error": "Access grant not found"})
        stamp = utc_stamp()
        users.update_item(
            Key=key,
            UpdateExpression="SET revokedAtUtc = :stamp, revokedByUserId = :userId",
            ExpressionAttributeValues={":stamp": stamp, ":userId": user_id},
        )
        notify_user(
            target,
            "commerce.access.revoked",
            "commerce",
            {"grantId": grant_id},
        )
        audit_write(
            "commerce",
            user_id,
            "commerce.grant.revoke",
            grant_id,
            {"targetUserId": target},
        )
        refreshed = users.get_item(Key=key, ConsistentRead=True).get("Item") or current
        return response(200, public_entitlement_grant(refreshed))

    if method == "POST" and path == "/authority/commerce/tokens/mint":
        if not (owner_user_id and user_id == owner_user_id):
            return response(403, {"error": "Platform owner authority required"})
        req = body(event)
        try:
            target = safe_id(req.get("targetUserId"), "targetUserId")
            quantity = int(req.get("quantity") or 1)
        except (TypeError, ValueError) as exc:
            return response(400, {"error": str(exc)})
        if quantity < 1 or quantity > 20:
            return response(400, {"error": "Token quantity must be between 1 and 20"})
        source = str(req.get("source") or "commerce")[:40]
        reference = str(req.get("reference") or "")[:160]
        minted = [
            mint_world_token(target, source, reference, user_id)
            for _ in range(quantity)
        ]
        notify_user(
            target,
            "commerce.tokens.granted",
            "commerce",
            {"quantity": quantity, "source": source},
        )
        audit_write(
            "commerce",
            user_id,
            "commerce.tokens.mint",
            target,
            {"quantity": quantity, "source": source, "reference": reference},
        )
        return response(200, [public_world_token(item) for item in minted])

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
        parcel_items = [
            item
            for item in query_world_prefix(world_id, "PARCEL#")
            if can_discover_mmo_parcel(world_id, item, user_id)
        ]
        parcels = [public_parcel(item) for item in parcel_items]
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

    if method == "GET" and path == "/world/ghost-zones":
        world_id = safe_id(q.get("worldId"), "worldId")
        if not is_geonaph(world_id):
            return response(400, {"error": "Ghost zones belong to Shaelvien"})
        ghosts = [
            public_ghost_zone(item, user_id)
            for item in active_ghost_zones(world_id)
        ]
        ghosts = [item for item in ghosts if item is not None]
        ghosts.sort(key=lambda item: (item["row"], item["column"], item["releasedAtUtc"]))
        return response(200, ghosts)

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

        column = cell_index % MMO_PARCEL_GRID_COLUMNS
        row = cell_index // MMO_PARCEL_GRID_COLUMNS
        parcel_id = parcel_id_from_cell(cell_index)
        region_id = "region-" + parcel_id

        requested_token_id = str(req.get("tokenId") or "").strip()
        token = spendable_world_token(user_id, requested_token_id)
        token_sk = token.get("sk") if token and isinstance(token.get("sk"), str) else ""
        token_key = (
            {"pk": "USER#" + user_id, "sk": token_sk}
            if token and token_sk.startswith(WORLD_TOKEN_SK_PREFIX)
            else None
        )
        existing_parcel = world.get_item(
            Key=parcel_key(world_id, parcel_id),
            ConsistentRead=True,
        ).get("Item")
        existing_region = world.get_item(
            Key=region_key(world_id, region_id),
            ConsistentRead=True,
        ).get("Item")

        # Claim is idempotent for the account that already owns this exact
        # property space. A retry after a slow/lost 200 must enter the property
        # instead of presenting a false 409 conflict.
        if existing_parcel:
            if (
                str(existing_parcel.get("ownerUserId") or "") == user_id
                and world_token_for_parcel(user_id, parcel_id)
            ):
                ensure_parcel_region(world_id, existing_parcel, now)
                return response(200, public_parcel(existing_parcel))
            return response(409, {"error": "That Shaelvien property space has already been claimed"})

        if not token:
            return response(409, {"error": "A Shaelvien Token is required"})
        if str(token.get("status") or "") != "unspent":
            bound_parcel_id = str(token.get("parcelId") or "")
            if bound_parcel_id:
                bound = world.get_item(
                    Key=parcel_key(world_id, bound_parcel_id),
                    ConsistentRead=True,
                ).get("Item")
                if bound and str(bound.get("ownerUserId") or "") == user_id:
                    return response(
                        409,
                        {
                            "error": (
                                f"Your Shaelvien Token is already bound to "
                                f"{str(bound.get('displayName') or bound_parcel_id)}. "
                                "Enter that property space instead."
                            )
                        },
                    )
            return response(409, {"error": "Your Shaelvien Token has already been spent"})

        if existing_region:
            existing_region_state = dict(existing_region.get("state") or {})
            existing_region_owner = str(
                existing_region.get("ownerUserId")
                or existing_region_state.get("ownerUserId")
                or ""
            )
            if existing_region_owner and existing_region_owner != user_id:
                return response(
                    409,
                    {
                        "error": (
                            "That property space has a conflicting legacy region record. "
                            "Choose another available square."
                        )
                    },
                )

        parcels = query_world_prefix(world_id, "PARCEL#")
        if not mmo_parcel_claimable(cell_index, parcels):
            return response(409, {"error": "That property space is occupied or is not yet connected to Endemar"})

        display_name = str(req.get("displayName") or "").strip()[:80] or f"Shaelvien {column},{row}"
        stamp = utc_stamp()
        world_half = secrets.token_hex(32)
        account_half = str(token.get("accountHalfCode") or "")
        if not account_half:
            return response(
                409,
                {
                    "error": (
                        "This legacy Shaelvien Token needs one account refresh before it can be spent. "
                        "Close and reopen the property claim screen, then try again."
                    )
                },
            )
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
            # to expose and proves which account token was paired for this claim.
            "worldHalfCode": world_half,
            "worldHalfHash": hashlib.sha256(world_half.encode()).hexdigest(),
            "bindingHash": binding_hash,
            "claimedAtUtc": stamp,
            # User-created Shaelvien zones are private-by-default. Publication
            # and open-player discovery are explicit later actions.
            "published": False,
            "openToPlayers": False,
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
            "parentNodeId": "world:" + world_id,
            "coordinateSpace": "world-normalized-v1",
            "canonicalMinX": column / MMO_PARCEL_GRID_COLUMNS,
            "canonicalMinY": row / MMO_PARCEL_GRID_ROWS,
            "canonicalMaxX": (column + 1) / MMO_PARCEL_GRID_COLUMNS,
            "canonicalMaxY": (row + 1) / MMO_PARCEL_GRID_ROWS,
            "canonicalZMin": 0,
            "canonicalZMax": MMO_PARCEL_MAX_HEIGHT,
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

        # The previous token Update produced DynamoDB cancellation reason
        # ValidationError while the parcel Put reported None. Replace the expression
        # update with a full conditional Put of the same keyed token record. This
        # preserves atomicity without relying on a fragile UpdateExpression.
        spent_token = {
            **token,
            # Always overwrite the physical DynamoDB key from authenticated
            # authority. A legacy token payload may carry stale/malformed key
            # metadata, but ownership lives in USER#<authenticated-user>.
            "pk": token_key["pk"],
            "sk": token_key["sk"],
            "status": "spent",
            "purchasedWorldId": world_id,
            "parcelId": parcel_id,
            "bindingHash": binding_hash,
            "spentAtUtc": stamp,
        }
        # boto3.resource("dynamodb") registers its document-type serializer on
        # meta.client. Passing AttributeValue envelopes here (for example
        # {"pk": {"S": "USER#..."}}) is therefore serialized a second time as a
        # DynamoDB Map and produces "key pk expected: S actual: M".
        spent_token_native = dynamo_safe(spent_token)
        parcel_item_native = dynamo_safe(parcel_item)
        if not isinstance(spent_token_native.get("pk"), str) or not isinstance(spent_token_native.get("sk"), str):
            return response(500, {"error": "Shaelvien Token storage key is not canonical string authority."})
        if not isinstance(parcel_item_native.get("pk"), str) or not isinstance(parcel_item_native.get("sk"), str):
            return response(500, {"error": "Shaelvien property storage key is not canonical string authority."})

        claim_transaction = [
                    {
                        "Put": {
                            "TableName": users.name,
                            "Item": spent_token_native,
                            "ConditionExpression": "#status = :unspent",
                            "ExpressionAttributeNames": {"#status": "status"},
                            "ExpressionAttributeValues": {":unspent": "unspent"},
                        }
                    },
                    {
                        "Put": {
                            "TableName": world.name,
                            "Item": parcel_item_native,
                            "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                        }
                    },
                ]
        claim_committed = False
        for claim_attempt in range(2):
            try:
                ddb.meta.client.transact_write_items(
                    TransactItems=claim_transaction
                )
                claim_committed = True
                break
            except ClientError as exc:
                code = (exc.response.get("Error") or {}).get("Code")
                if code not in ("TransactionCanceledException", "ConditionalCheckFailedException"):
                    raise

                occupied = world.get_item(
                    Key=parcel_key(world_id, parcel_id),
                    ConsistentRead=True,
                ).get("Item")
                latest_token = world_token_for_parcel(user_id, parcel_id)
                if (
                    occupied
                    and str(occupied.get("ownerUserId") or "") == user_id
                    and latest_token
                ):
                    return response(200, public_parcel(occupied))

                latest_region = world.get_item(
                    Key=region_key(world_id, region_id),
                    ConsistentRead=True,
                ).get("Item")
                latest_selected_token = users.get_item(
                    Key=token_key,
                    ConsistentRead=True,
                ).get("Item")

                # A transaction can be canceled by short-lived contention even
                # though every authoritative condition is still valid. Retry once
                # only when nothing was committed and the exact selected token
                # remains unspent. This is safe because the transaction itself is
                # still the only operation allowed to spend the token.
                if (
                    claim_attempt == 0
                    and not occupied
                    and latest_selected_token
                    and str(latest_selected_token.get("status") or "") == "unspent"
                ):
                    time.sleep(0.075)
                    continue

                if not latest_selected_token:
                    return response(
                        409,
                        {
                            "error": (
                                "The selected Shaelvien Token record is no longer available. "
                                "No property was claimed."
                            )
                        },
                    )
                if str(latest_selected_token.get("status") or "") != "unspent":
                    bound_parcel_id = str(latest_selected_token.get("parcelId") or "")
                    return response(
                        409,
                        {
                            "error": (
                                f"The selected Shaelvien Token is already bound to {bound_parcel_id}."
                                if bound_parcel_id
                                else "The selected Shaelvien Token is no longer unspent."
                            )
                        },
                    )

                cancellation_reasons = exc.response.get("CancellationReasons") or []
                reason_codes = [
                    str(reason.get("Code") or "None")
                    for reason in cancellation_reasons
                ]
                reason_messages = [
                    str(reason.get("Message") or "").strip()
                    for reason in cancellation_reasons
                ]
                safe_reason = ",".join(reason_codes[:3]) if reason_codes else "unknown"
                first_message = next(
                    (message for message in reason_messages if message),
                    str((exc.response.get("Error") or {}).get("Message") or "").strip(),
                )
                if len(first_message) > 280:
                    first_message = first_message[:277] + "..."
                token_shape = {
                    "pkLength": len(str(token_key.get("pk") or "")),
                    "skLength": len(str(token_key.get("sk") or "")),
                    "tokenIdPresent": bool(str(token.get("tokenId") or "")),
                    "accountHalfPresent": bool(str(token.get("accountHalfCode") or "")),
                    "status": str(token.get("status") or ""),
                }
                print(
                    "Shaelvien claim transaction canceled",
                    {
                        "userId": user_id,
                        "tokenSk": str(token_key.get("sk") or ""),
                        "parcelId": parcel_id,
                        "attempt": claim_attempt + 1,
                        "reasons": safe_reason,
                        "messages": reason_messages[:3],
                        "tokenShape": token_shape,
                    },
                )
                detail = first_message or safe_reason
                return response(
                    409,
                    {
                        "error": (
                            "The ownership transaction was canceled before anything was spent. "
                            "The selected token is still unspent and the property is still available. "
                            f"AWS diagnostic: {detail}"
                        ),
                        "claimConflict": safe_reason,
                        "claimConflictMessage": first_message,
                    },
                )

        if not claim_committed:
            return response(
                409,
                {
                    "error": (
                        "The property claim did not complete. No Shaelvien Token was spent."
                    )
                },
            )

        # Ownership is complete at this point. Region state is a representation of
        # the owned property space, so reconcile it after the atomic token+parcel
        # binding rather than allowing representation state to veto ownership.
        ensure_parcel_region(world_id, parcel_item, now)

        # A newly claimed parcel replaces the public ghost placeholder at this
        # coordinate, while the private preservation archive remains untouched.
        try:
            for ghost in active_ghost_zones(world_id):
                if int(ghost.get("cellIndex") or -1) != cell_index:
                    continue
                world.update_item(
                    Key=ghost_zone_key(world_id, str(ghost.get("ghostId") or "")),
                    UpdateExpression="SET reclaimedAtUtc = :stamp, reclaimedByParcelId = :parcelId",
                    ExpressionAttributeValues={
                        ":stamp": stamp,
                        ":parcelId": parcel_id,
                    },
                )
        except Exception as exc:
            print("Ghost-zone representation reconciliation failed", str(exc)[:280])

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

    if method == "POST" and path == "/world/parcels/release":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        parcel_id = safe_id(req.get("parcelId"), "parcelId")
        if not is_geonaph(world_id):
            return response(400, {"error": "Only Shaelvien MMO property space can be released"})

        parcel = world.get_item(
            Key=parcel_key(world_id, parcel_id),
            ConsistentRead=True,
        ).get("Item")

        # Release is idempotent. If the authoritative parcel is already gone,
        # return the existing ghost archive for this owner's prior release rather
        # than issuing another replacement key.
        if not parcel:
            prior = next(
                (
                    item
                    for item in query_world_prefix(world_id, "GHOSTZONE#")
                    if str(item.get("formerParcelId") or "") == parcel_id
                    and str(item.get("ownerUserId") or "") == user_id
                ),
                None,
            )
            if prior:
                refund_token_id = str(prior.get("refundTokenId") or "")
                refund_token = world_token_by_id(user_id, refund_token_id) if refund_token_id else None
                return response(
                    200,
                    {
                        "ok": True,
                        "ghostZone": public_ghost_zone(prior, user_id),
                        "refundIssued": bool(refund_token),
                        "refundToken": public_world_token(refund_token),
                        "alreadyReleased": True,
                    },
                )
            return response(404, {"error": "Shaelvien property space not found"})

        if str(parcel.get("ownerUserId") or "") != user_id:
            return response(403, {"error": "Only the property owner may release this Shaelvien property space"})

        region_id = str(parcel.get("regionId") or ("region-" + parcel_id))
        region_item = world.get_item(
            Key=region_key(world_id, region_id),
            ConsistentRead=True,
        ).get("Item")
        region_map_item = world.get_item(
            Key=region_map_key(world_id, region_id),
            ConsistentRead=True,
        ).get("Item")
        source_item = world.get_item(
            Key=world_source_key(world_id),
            ConsistentRead=True,
        ).get("Item")
        source_state = dict((source_item or {}).get("state") or {})
        existing_layers = source_state.get("userLayers") or []
        if not isinstance(existing_layers, list):
            existing_layers = []
        legacy_region_layers = [
            item
            for item in existing_layers
            if isinstance(item, dict) and str(item.get("regionId") or "") == region_id
        ]
        region_map_state = dict((region_map_item or {}).get("state") or {})
        map_layers = region_map_state.get("userLayers") or []
        if not isinstance(map_layers, list):
            map_layers = []
        archived_layers = map_layers if region_map_item is not None else legacy_region_layers
        remaining_layers = [
            item
            for item in existing_layers
            if not isinstance(item, dict) or str(item.get("regionId") or "") != region_id
        ]
        delegations = query_world_prefix(world_id, "PARCELACL#" + parcel_id + "#USER#")

        spent_token = world_token_for_parcel(user_id, parcel_id)
        if not spent_token:
            return response(
                409,
                {
                    "error": (
                        "The property binding token record is missing. "
                        "The property was left untouched so no content or ownership can be lost."
                    )
                },
            )

        stamp = utc_stamp()
        binding_hash = str(parcel.get("bindingHash") or "")
        ghost_seed = f"{world_id}:{parcel_id}:{binding_hash}:{str(parcel.get('claimedAtUtc') or '')}"
        ghost_id = "ghost-" + hashlib.sha256(ghost_seed.encode()).hexdigest()[:24]
        refund_token = (
            _new_world_token_item(
                user_id,
                "release-refund",
                f"{world_id}:{parcel_id}:{ghost_id}",
                user_id,
            )
            if PARCEL_RELEASE_REFUNDS_ENABLED
            else None
        )
        refund_token_id = str((refund_token or {}).get("tokenId") or "")

        archive = {
            "format": "RIST_GHOST_ZONE_ARCHIVE_V1",
            "worldId": world_id,
            "ghostId": ghost_id,
            "ownerUserId": user_id,
            "releasedAtUtc": stamp,
            "contentUsePolicy": "preserve-only",
            "published": False,
            "parcel": {
                "parcelId": parcel_id,
                "regionId": region_id,
                "displayName": str(parcel.get("displayName") or ""),
                "cellIndex": int(parcel.get("cellIndex") or 0),
                "column": int(parcel.get("column") or 0),
                "row": int(parcel.get("row") or 0),
                "pixelWidth": int(parcel.get("pixelWidth") or MMO_PARCEL_PIXELS),
                "pixelHeight": int(parcel.get("pixelHeight") or MMO_PARCEL_PIXELS),
                "maxHeight": int(parcel.get("maxHeight") or MMO_PARCEL_MAX_HEIGHT),
                "bindingHash": binding_hash,
                "claimedAtUtc": str(parcel.get("claimedAtUtc") or ""),
            },
            "regionState": dict((region_item or {}).get("state") or {}),
            "userLayers": archived_layers,
            "delegations": [
                {
                    "userId": str(item.get("userId") or ""),
                    "permission": str(item.get("permission") or "None"),
                    "updatedAtUtc": str(item.get("updatedAtUtc") or ""),
                }
                for item in delegations
            ],
        }
        archive_bytes = json.dumps(
            archive,
            separators=(",", ":"),
            ensure_ascii=False,
            default=_json_default,
        ).encode("utf-8")
        archive_key = f"users/{user_id}/ghost-zones/{world_id}/{ghost_id}.json"
        archive_sha = hashlib.sha256(archive_bytes).hexdigest()

        # Preserve first, then unpublish. An interrupted release can leave an
        # extra private archive version, but can never remove the live content
        # before a durable preservation copy exists.
        s3.put_object(
            Bucket=bucket,
            Key=archive_key,
            Body=archive_bytes,
            ContentType="application/json",
            ServerSideEncryption="aws:kms",
            SSEKMSKeyId=kms_key,
        )

        ghost_item = {
            **ghost_zone_key(world_id, ghost_id),
            "entityType": "ghostZone",
            "ghostId": ghost_id,
            "worldId": world_id,
            "ownerUserId": user_id,
            "formerParcelId": parcel_id,
            "formerRegionId": region_id,
            "cellIndex": int(parcel.get("cellIndex") or 0),
            "column": int(parcel.get("column") or 0),
            "row": int(parcel.get("row") or 0),
            "releasedAtUtc": stamp,
            "reclaimedAtUtc": "",
            "reclaimedByParcelId": "",
            "published": False,
            "contentUsePolicy": "preserve-only",
            "archiveKey": archive_key,
            "archiveSha256": archive_sha,
            "archiveBytes": len(archive_bytes),
            "refundIssued": bool(refund_token),
            "refundTokenId": refund_token_id,
        }

        released_token = {
            **spent_token,
            "status": "released",
            "releasedAtUtc": stamp,
            "releaseGhostId": ghost_id,
            "replacementTokenId": refund_token_id,
        }

        release_transaction = [
            {
                "Put": {
                    "TableName": world.name,
                    "Item": dynamo_safe(ghost_item),
                    "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                }
            },
            {
                "Put": {
                    "TableName": users.name,
                    "Item": dynamo_safe(released_token),
                    "ConditionExpression": "#status = :spent AND parcelId = :parcelId",
                    "ExpressionAttributeNames": {"#status": "status"},
                    "ExpressionAttributeValues": {
                        ":spent": "spent",
                        ":parcelId": parcel_id,
                    },
                }
            },
            {
                "Delete": {
                    "TableName": world.name,
                    "Key": parcel_key(world_id, parcel_id),
                    "ConditionExpression": "ownerUserId = :owner",
                    "ExpressionAttributeValues": {":owner": user_id},
                }
            },
        ]

        if region_item:
            release_transaction.append(
                {
                    "Delete": {
                        "TableName": world.name,
                        "Key": region_key(world_id, region_id),
                        "ConditionExpression": "parcelId = :parcelId",
                        "ExpressionAttributeValues": {":parcelId": parcel_id},
                    }
                }
            )

        if region_map_item:
            release_transaction.append(
                {
                    "Delete": {
                        "TableName": world.name,
                        "Key": region_map_key(world_id, region_id),
                    }
                }
            )

        if refund_token:
            release_transaction.append(
                {
                    "Put": {
                        "TableName": users.name,
                        "Item": dynamo_safe(refund_token),
                        "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                    }
                }
            )

        if source_item and archived_layers:
            updated_source_state = dict(source_state)
            updated_source_state["userLayers"] = remaining_layers
            updated_source_state["savedAt"] = stamp
            updated_source_item = {
                **source_item,
                "state": dynamo_safe(updated_source_state),
                "updatedAtUtc": stamp,
                "updatedByUserId": user_id,
            }
            expected_source_stamp = str(source_item.get("updatedAtUtc") or "")
            source_put = {
                "TableName": world.name,
                "Item": dynamo_safe(updated_source_item),
            }
            if expected_source_stamp:
                source_put["ConditionExpression"] = "updatedAtUtc = :expected"
                source_put["ExpressionAttributeValues"] = {":expected": expected_source_stamp}
            else:
                source_put["ConditionExpression"] = "attribute_not_exists(updatedAtUtc)"
            release_transaction.append({"Put": source_put})

        try:
            ddb.meta.client.transact_write_items(TransactItems=release_transaction)
        except ClientError as exc:
            code = (exc.response.get("Error") or {}).get("Code")
            if code in ("TransactionCanceledException", "ConditionalCheckFailedException"):
                return response(
                    409,
                    {
                        "error": (
                            "The property changed while release was being prepared. "
                            "Nothing was unpublished or refunded; refresh and try again."
                        )
                    },
                )
            raise

        # ACLs are no longer live authority once the parcel record is gone. Their
        # prior values remain inside the private ghost archive for loss prevention.
        for delegation in delegations:
            key = {
                "pk": str(delegation.get("pk") or ""),
                "sk": str(delegation.get("sk") or ""),
            }
            if key["pk"] and key["sk"]:
                world.delete_item(Key=key)

        audit_write(
            world_id,
            user_id,
            "parcel.release",
            parcel_id,
            {
                "ghostId": ghost_id,
                "cellIndex": ghost_item["cellIndex"],
                "refundIssued": bool(refund_token),
                "refundTokenId": refund_token_id,
                "archiveSha256": archive_sha,
            },
        )
        notify_user(
            user_id,
            "parcel.released",
            world_id,
            {
                "parcelId": parcel_id,
                "ghostId": ghost_id,
                "refundIssued": bool(refund_token),
                "refundTokenId": refund_token_id,
            },
        )
        return response(
            200,
            {
                "ok": True,
                "ghostZone": public_ghost_zone(ghost_item, user_id),
                "refundIssued": bool(refund_token),
                "refundToken": public_world_token(refund_token),
                "alreadyReleased": False,
            },
        )

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

    if method == "GET" and path == "/world/source/region":
        world_id = safe_id(q.get("worldId"), "worldId")
        region_id = safe_id(q.get("regionId"), "regionId")
        if not can_view(world_id, user_id):
            return response(403, {"error": "World access required"})
        deed = world.get_item(
            Key=region_key(world_id, region_id), ConsistentRead=True
        ).get("Item")
        if not deed:
            return response(404, {"error": "Region deed not found"})
        parent = world.get_item(
            Key=world_source_key(world_id), ConsistentRead=True
        ).get("Item")
        parent_state = (parent or {}).get("state")
        if not isinstance(parent_state, dict):
            if is_geonaph(world_id):
                # Geonaph's immutable parent terrain is published as
                # build-time source-cell assets. Region projection does not
                # require a duplicate WORLDSOURCE row just to address them.
                parent = {"state": {}, "updatedAtUtc": ""}
                parent_state = {}
            else:
                return response(409, {"error": "Canonical parent map is not published"})

        region_map = world.get_item(
            Key=region_map_key(world_id, region_id), ConsistentRead=True
        ).get("Item")
        if region_map:
            raw_region_map_state = region_map.get("state")
            region_map_state = (
                dict(raw_region_map_state)
                if isinstance(raw_region_map_state, dict)
                else {}
            )
        else:
            # Migration compatibility: absence of a REGIONMAP record means
            # project any legacy regionId-tagged overlays from WORLDSOURCE.
            region_map_state = None

        try:
            projected = project_region_source(
                world_id, region_id, deed.get("state") or {},
                parent_state, region_map_state,
            )
        except (ValueError, TypeError) as exc:
            return response(409, {"error": str(exc)})
        return response(200, {
            "worldId": world_id, "regionId": region_id,
            "projection": "region-world-z-v2", "state": projected,
            "updatedAtUtc": str(
                (region_map or {}).get("updatedAtUtc")
                or parent.get("updatedAtUtc")
                or ""
            ),
        })

    if method == "POST" and path == "/world/source/region":
        req = body(event)
        world_id = safe_id(req.get("worldId"), "worldId")
        region_id = safe_id(req.get("regionId"), "regionId")
        region_state = editable_region_state(world_id, region_id, user_id)
        if region_state is None:
            return response(403, {"error": "Region edit authority required"})
        incoming = req.get("userLayers")
        if not isinstance(incoming, list):
            return response(400, {"error": "userLayers must be an array"})
        if len(incoming) > 250:
            return response(413, {"error": "Regional overlay limit exceeded"})

        try:
            normalized = [
                normalize_region_layer(region_state, dict(item), region_id)
                for item in incoming
            ]
        except PermissionError as exc:
            return response(403, {"error": str(exc)})
        except (TypeError, ValueError) as exc:
            return response(400, {"error": str(exc)})

        region_map_state = {
            "format": "RIST_REGION_MAP_V1",
            "worldId": world_id,
            "regionId": region_id,
            "zModel": REGION_Z_MODEL,
            "userLayers": normalized,
        }
        encoded_size = len(json.dumps(
            region_map_state, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8"))
        if encoded_size > 360000:
            return response(413, {"error": "Region map metadata exceeds database capacity"})

        updated_at = datetime.now(timezone.utc).isoformat()
        world.update_item(
            Key=region_map_key(world_id, region_id),
            UpdateExpression=(
                "SET entityType = :entityType, worldId = :worldId, regionId = :regionId, "
                "#state = :state, updatedAtUtc = :updatedAtUtc, updatedByUserId = :updatedBy"
            ),
            ExpressionAttributeNames={"#state": "state"},
            ExpressionAttributeValues={
                ":entityType": "regionMap",
                ":worldId": world_id,
                ":regionId": region_id,
                ":state": dynamo_safe(region_map_state),
                ":updatedAtUtc": updated_at,
                ":updatedBy": user_id,
            },
        )
        audit_write(world_id, user_id, "region.overlay.save", region_id, {
            "layers": len(normalized),
            "parentTierIndex": int(region_state.get("tierIndex") or 0),
            "zModel": REGION_Z_MODEL,
            "storage": "REGIONMAP",
            "bytes": encoded_size,
        })
        return response(200, {
            "worldId": world_id,
            "regionId": region_id,
            "state": region_map_state,
            "updatedAtUtc": updated_at,
            "savedLayerCount": len(normalized),
            "zModel": REGION_Z_MODEL,
            "storage": "REGIONMAP",
        })

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

        # A claimed MMO parcel is exclusive world truth until its owner releases it.
        # Region editors may change its contents, but may not enlarge its square,
        # raise its height, rewrite its token binding, transfer ownership, or release
        # it through an ordinary region save.
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
            region["parentNodeId"] = "world:" + world_id
            region["coordinateSpace"] = "world-normalized-v1"
            region["canonicalMinX"] = column / MMO_PARCEL_GRID_COLUMNS
            region["canonicalMinY"] = row / MMO_PARCEL_GRID_ROWS
            region["canonicalMaxX"] = (column + 1) / MMO_PARCEL_GRID_COLUMNS
            region["canonicalMaxY"] = (row + 1) / MMO_PARCEL_GRID_ROWS
            region["canonicalZMin"] = 0
            region["canonicalZMax"] = MMO_PARCEL_MAX_HEIGHT

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
