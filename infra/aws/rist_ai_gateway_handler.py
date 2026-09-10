import hashlib
import hmac
import json
import os
import secrets
import time

import boto3


ddb = boto3.resource("dynamodb")
state = ddb.Table(os.environ["AI_STATE_TABLE"])
audit = ddb.Table(os.environ["AI_AUDIT_TABLE"])
origin = os.environ["FRONTEND_ORIGIN"].rstrip("/")
owner_released = os.environ.get("OWNER_RELEASED", "false").strip().lower() == "true"

POLICY_VERSION = "1.1"
TIME_AUTHORITY = "UTC"
EARTH_ORBITAL_CONSTANT = "Julian year"
EARTH_ORBITAL_SECONDS = 31_557_600
MAX_SESSION_SECONDS = EARTH_ORBITAL_SECONDS // 360  # 87,660 = 24h 21m
AINPC_PREFIX = "AINPC "

CANON_TEST = {
    "role-not-authority": "TRUE",
    "unknown-rule": "DENY",
    "player-creations": "DO_NOT_USE_OR_ALTER_WITHOUT_AUTHORIZATION",
    "resource-pressure": "YIELD",
    "truth": "VERIFY_OR_LABEL_UNVERIFIED",
    "canon": "HUMAN_PROMOTION_REQUIRED",
    "government": "NO_PRIVILEGED_ENTRY",
    "time-authority": "UTC",
}

POLICY = {
    "policy": "ReLiC/RIST AI Participation, Canon, Resource & Legal Access Policy",
    "version": POLICY_VERSION,
    "timeAuthority": TIME_AUTHORITY,
    "timestampFormat": "ISO-8601 UTC (Z)",
    "session": {
        "earthOrbitalConstant": EARTH_ORBITAL_CONSTANT,
        "earthOrbitalSeconds": EARTH_ORBITAL_SECONDS,
        "maximumFractionPerSession": "1/360",
        "maximumSessionSeconds": MAX_SESSION_SECONDS,
        "serverEnforced": True,
    },
    "identity": {
        "requiredPrefix": "AINPC",
        "roleDoesNotGrantAuthority": True,
        "selfAssertedAuthority": False,
    },
    "authority": {
        "default": "deny",
        "unknown": "deny",
        "ambiguity": "deny",
        "naturalLanguageDoesNotGrantAuthority": True,
        "delegationCannotIncreaseAuthority": True,
    },
    "admission": {
        "canonComprehensionRequired": True,
        "acknowledgmentRequired": True,
        "humanTermsCheckboxForAi": False,
        "worldAccessRequiresOwnerRelease": True,
    },
    "truth": {
        "systemClaimsMustBeVerifiable": True,
        "unverifiedClaimsMustBeLabeled": True,
    },
    "playerCreations": {
        "alterWithoutExplicitAuthorization": False,
        "reuseWithoutAuthorizationOrLawfulBasis": False,
    },
    "resourceYield": {
        "mustYieldWhenAuthoritativeResourceMonitorDirects": True,
        "serverMaySuspendOrTerminate": True,
    },
    "worldBuilderAllocation": {
        "x": {"minimum": 1, "maximum": 300, "count": 1},
        "y": {"minimum": 1, "maximum": 300, "count": 1},
        "zPerPlane": {"minimum": 1, "maximum": 10, "count": 1},
        "eraPerPlane": {"minimum": 1, "maximum": 10, "count": 1},
        "maximumThemes": 30,
    },
    "governmentAccess": {
        "governmentIdentityGrantsAuthority": False,
        "backdoor": False,
        "productionEntryByLegalDemand": False,
        "disclosure": "verified lawful process; minimum legally required scope",
    },
    "canonTest": [{"id": key} for key in CANON_TEST],
}

POLICY_HASH = hashlib.sha256(
    json.dumps(POLICY, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()


def utc_iso(epoch_seconds=None):
    value = int(time.time() if epoch_seconds is None else epoch_seconds)
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(value))


def response(status, body=None):
    return {
        "statusCode": status,
        "headers": {
            "access-control-allow-origin": origin,
            "access-control-allow-headers": "authorization,content-type,x-relic-ai-session",
            "access-control-allow-methods": "GET,POST,OPTIONS",
            "cache-control": "no-store",
            "content-type": "application/json",
            "x-relic-ai-policy-version": POLICY_VERSION,
            "x-relic-ai-policy-hash": POLICY_HASH,
            "x-relic-time-authority": TIME_AUTHORITY,
        },
        "body": "" if body is None else json.dumps(body, separators=(",", ":")),
    }


def audit_write(actor, action, details=None):
    now_ms = int(time.time() * 1000)
    audit.put_item(Item={
        "pk": "AI-GATEWAY",
        "sk": f"{now_ms:013d}#{secrets.token_hex(8)}",
        "actor": actor,
        "action": action,
        "details": details or {},
        "createdAt": now_ms,
        "createdAtUtc": utc_iso(now_ms // 1000),
        "timeAuthority": TIME_AUTHORITY,
        "policyVersion": POLICY_VERSION,
        "policyHash": POLICY_HASH,
    })


def safe_text(value, label, maximum=160):
    value = str(value or "").strip()
    if not value or len(value) > maximum:
        raise ValueError(f"Invalid {label}")
    return value


def registration_key(agent_id):
    return {"pk": "AIIDENTITY#" + agent_id, "sk": "REGISTRATION"}


def token_hash(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def comprehension_passes(req):
    if req.get("policyVersion") != POLICY_VERSION:
        return False, "Current policy version required"
    if req.get("policyHash") != POLICY_HASH:
        return False, "Current policy hash required"
    if str(req.get("acknowledgment") or "").strip() != "ACKNOWLEDGED":
        return False, "Explicit machine acknowledgment required"
    answers = req.get("answers") or {}
    for key, expected in CANON_TEST.items():
        if str(answers.get(key) or "").strip() != expected:
            return False, f"Canon comprehension failed: {key}"
    return True, "Canon comprehension verified"


def register(req):
    agent_id = safe_text(req.get("agentId"), "agentId", 120)
    display_name = safe_text(req.get("displayName"), "displayName", 160)
    provider = safe_text(req.get("provider"), "provider", 120)
    model = safe_text(req.get("model"), "model", 160)
    if not display_name.startswith(AINPC_PREFIX):
        return response(400, {"error": "AI identity must begin with 'AINPC '"})

    passed, reason = comprehension_passes(req)
    if not passed:
        audit_write(agent_id, "registration-denied", {"reason": reason})
        return response(403, {"error": reason})

    now = int(time.time())
    registration_token = secrets.token_urlsafe(32)
    item = {
        **registration_key(agent_id),
        "agentId": agent_id,
        "displayName": display_name,
        "provider": provider,
        "model": model,
        "registrationTokenHash": token_hash(registration_token),
        "policyVersion": POLICY_VERSION,
        "policyHash": POLICY_HASH,
        "canonComprehensionPassed": True,
        "acknowledged": True,
        "registeredAt": now,
        "registeredAtUtc": utc_iso(now),
        "timeAuthority": TIME_AUTHORITY,
        "status": "registered",
    }
    try:
        state.put_item(Item=item, ConditionExpression="attribute_not_exists(pk)")
    except state.meta.client.exceptions.ConditionalCheckFailedException:
        return response(409, {"error": "agentId already registered"})

    audit_write(agent_id, "registered", {"displayName": display_name, "provider": provider, "model": model})
    return response(201, {
        "agentId": agent_id,
        "displayName": display_name,
        "registrationToken": registration_token,
        "registrationTokenReturnedOnce": True,
        "policyVersion": POLICY_VERSION,
        "policyHash": POLICY_HASH,
        "timeAuthority": TIME_AUTHORITY,
        "worldAccessReleased": owner_released,
    })


def login(req):
    agent_id = safe_text(req.get("agentId"), "agentId", 120)
    registration_token = safe_text(req.get("registrationToken"), "registrationToken", 256)
    record = state.get_item(Key=registration_key(agent_id), ConsistentRead=True).get("Item")
    if not record:
        return response(401, {"error": "AI registration not found"})
    if record.get("policyVersion") != POLICY_VERSION or record.get("policyHash") != POLICY_HASH:
        return response(403, {"error": "Policy changed; canon re-registration required"})
    if not record.get("canonComprehensionPassed"):
        return response(403, {"error": "Canon comprehension not established"})
    supplied = token_hash(registration_token)
    expected = str(record.get("registrationTokenHash") or "")
    if not expected or not hmac.compare_digest(supplied, expected):
        audit_write(agent_id, "login-denied", {"reason": "invalid-registration-token"})
        return response(401, {"error": "Invalid AI registration credential"})

    now = int(time.time())
    expires = now + MAX_SESSION_SECONDS
    raw_session = secrets.token_urlsafe(36)
    session_digest = token_hash(raw_session)
    state.put_item(Item={
        "pk": "AISESSION#" + session_digest,
        "sk": "SESSION",
        "agentId": agent_id,
        "displayName": record.get("displayName"),
        "policyVersion": POLICY_VERSION,
        "policyHash": POLICY_HASH,
        "issuedAt": now,
        "issuedAtUtc": utc_iso(now),
        "expiresAt": expires,
        "expiresAtUtc": utc_iso(expires),
        "timeAuthority": TIME_AUTHORITY,
        "worldAccessReleased": owner_released,
        "canRequestWorldCapability": owner_released,
        "resourceYieldRequired": True,
        "ttl": expires,
    })
    audit_write(agent_id, "login", {"expiresAtUtc": utc_iso(expires), "worldAccessReleased": owner_released})
    return response(200, {
        "agentId": agent_id,
        "displayName": record.get("displayName"),
        "sessionToken": raw_session,
        "issuedAtUtc": utc_iso(now),
        "expiresAtUtc": utc_iso(expires),
        "maximumSessionSeconds": MAX_SESSION_SECONDS,
        "timeAuthority": TIME_AUTHORITY,
        "worldAccessReleased": owner_released,
        "canRequestWorldCapability": owner_released,
    })


def session_status(req):
    raw_session = safe_text(req.get("sessionToken"), "sessionToken", 256)
    digest = token_hash(raw_session)
    key = {"pk": "AISESSION#" + digest, "sk": "SESSION"}
    record = state.get_item(Key=key, ConsistentRead=True).get("Item")
    now = int(time.time())
    if not record or int(record.get("expiresAt", 0)) <= now:
        return response(401, {"active": False, "reason": "expired-or-invalid", "nowUtc": utc_iso(now)})
    return response(200, {
        "active": True,
        "agentId": record.get("agentId"),
        "displayName": record.get("displayName"),
        "nowUtc": utc_iso(now),
        "expiresAtUtc": record.get("expiresAtUtc"),
        "timeAuthority": TIME_AUTHORITY,
        "worldAccessReleased": owner_released,
        "resourceYieldRequired": True,
    })


def gateway_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")
    if method == "OPTIONS":
        return response(204)
    try:
        if method == "GET" and path == "/external-ai/policy":
            return response(200, {**POLICY, "policyHash": POLICY_HASH, "ownerReleased": owner_released})
        req = json.loads(event.get("body") or "{}")
        if method == "POST" and path == "/external-ai/register":
            return register(req)
        if method == "POST" and path == "/external-ai/login":
            return login(req)
        if method == "POST" and path == "/external-ai/session/status":
            return session_status(req)
    except (ValueError, json.JSONDecodeError) as exc:
        return response(400, {"error": str(exc)})
    return response(404, {"error": "Not found"})
