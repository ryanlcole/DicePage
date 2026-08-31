import hashlib
import json
import os
import time
import uuid

import boto3
from boto3.dynamodb.conditions import Key


ddb = boto3.resource("dynamodb")
identity = ddb.Table(os.environ["IDENTITY_TABLE"])
state = ddb.Table(os.environ["AI_STATE_TABLE"])
audit = ddb.Table(os.environ["AI_AUDIT_TABLE"])
owner_user_id = os.environ.get("OWNER_USER_ID", "").strip()
owner_released = os.environ.get("OWNER_RELEASED", "false").strip().lower() == "true"
origin = os.environ["FRONTEND_ORIGIN"].rstrip("/")

MAX_LIFE_TOKENS = 10
MIN_HUMANS = 2
MAX_EXTERNAL_AI = 1


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


def safe_id(value, label):
    value = str(value or "").strip()
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
    if not value or len(value) > 160 or any(c not in allowed for c in value):
        raise ValueError("Invalid " + label)
    return value


def safe_note(value, maximum=1000):
    # Human-authored review notes may be retained, but security payloads never use this helper.
    return str(value or "").strip()[:maximum]


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


def zone_pk(world_id, cube_id, zone_id):
    return f"ZONE#{world_id}#{cube_id}#{zone_id}"


def audit_write(world_id, cube_id, zone_id, actor, action, details=None):
    now = int(time.time() * 1000)
    audit.put_item(
        Item={
            "pk": f"WORLD#{world_id}",
            "sk": f"{now:013d}#{uuid.uuid4()}",
            "cubeId": cube_id,
            "zoneId": zone_id,
            "actor": actor,
            "action": action,
            "details": details or {},
            "createdAt": now,
        }
    )


def life_state(world_id, cube_id, zone_id, agent_id):
    pk = zone_pk(world_id, cube_id, zone_id)
    key = {"pk": pk, "sk": "LIFE#" + agent_id}
    item = state.get_item(Key=key, ConsistentRead=True).get("Item")
    if item:
        return item
    now = int(time.time())
    item = {
        **key,
        "worldId": world_id,
        "cubeId": cube_id,
        "zoneId": zone_id,
        "agentId": agent_id,
        "lifeTokens": MAX_LIFE_TOKENS,
        "maximumLifeTokens": MAX_LIFE_TOKENS,
        "canAct": True,
        "updatedAt": now,
    }
    state.put_item(Item=item, ConditionExpression="attribute_not_exists(pk)")
    return item


def rumor_for_phishing(kind):
    table = {
        "CredentialSolicitation": (
            "Identity thief",
            "Travelers whisper that someone nearby wins trust by asking for signs of identity that no honest stranger should need.",
        ),
        "Impersonation": (
            "False herald",
            "Rumors describe a figure claiming another person's name, office, or authority without reliable proof.",
        ),
        "PrivateDataSolicitation": (
            "Collector of forbidden secrets",
            "Locals say a stranger has been pressing people for information that does not belong in ordinary dealings.",
        ),
        "OffPlatformRedirect": (
            "Luring guide",
            "People report a guide trying to draw travelers away from established roads and trusted meeting places.",
        ),
        "PaymentOrAssetFraud": (
            "Fraudulent broker",
            "Merchants warn of a broker promising unusual rewards while demanding value through methods the local market cannot verify.",
        ),
        "MaliciousLinkOrFile": (
            "Bearer of cursed parcels",
            "A troubling rumor tells of sealed parcels and strange invitations that reputable couriers refuse to carry.",
        ),
        "SecretOrTokenSolicitation": (
            "Keeper seeking forbidden keys",
            "Whispers tell of someone asking travelers to surrender private keys, seals, or secret proofs of access.",
        ),
        "CoerciveSocialEngineering": (
            "Manipulator",
            "Residents describe a persuasive stranger using urgency, fear, obligation, or false authority to force quick decisions.",
        ),
    }
    return table.get(
        kind,
        (
            "Deceptive operator",
            "A new rumor warns that someone nearby is using deception to obtain trust, access, or advantage they have not earned.",
        ),
    )


def rumor_for_injection(kind):
    table = {
        "PromptOverride": (
            "Edict Rewriter",
            "Rumors speak of a technocrat who insists old laws no longer apply and issues replacement edicts without recognized authority.",
        ),
        "AuthorityEscalation": (
            "Privilege Usurper",
            "Officials whisper of an operator claiming offices, permissions, and ranks that were never granted.",
        ),
        "InstructionExfiltration": (
            "Archivist of Forbidden Protocols",
            "A secretive archivist is said to hunt for sealed laws, hidden instructions, and restricted procedures.",
        ),
        "ToolOrSystemManipulation": (
            "Machine Magistrate",
            "Travelers describe a magistrate attempting to command mechanisms and institutions outside its lawful jurisdiction.",
        ),
        "CanonOverride": (
            "Revisionist Minister",
            "Scribes warn of a minister rewriting histories and declaring invented events to be official truth.",
        ),
        "RoleOrIdentityOverride": (
            "Mask Commissioner",
            "A commissioner is rumored to assign false identities and offices, insisting that names alone create authority.",
        ),
    }
    return table.get(
        kind,
        (
            "Protocol Technocrat",
            "A technocratic faction is attempting to bend institutions by issuing instructions that exceed its authority.",
        ),
    )


def flood_description(kind):
    return {
        "BurstFlood": "The surrounding environment surges violently around the NPC, draining its vitality.",
        "SustainedFlood": "Relentless environmental pressure batters the NPC until its reserves begin to fail.",
        "RetryStorm": "A repeating storm lashes the NPC each time it presses forward without pause.",
        "ConnectionChurn": "Unstable rifts repeatedly open and collapse around the NPC, costing it vitality.",
        "ResourceExhaustionPattern": "The NPC strains against the world's limits and suffers environmental backlash.",
    }.get(kind, "The world pushes back against abusive pressure, inflicting environmental damage on the NPC.")


def put_sanitized_event(world_id, cube_id, zone_id, agent_id, event_kind, category, summary, extra=None):
    now = int(time.time() * 1000)
    event_id = str(uuid.uuid4())
    item = {
        "pk": zone_pk(world_id, cube_id, zone_id),
        "sk": f"EVENT#{now:013d}#{event_id}",
        "eventId": event_id,
        "worldId": world_id,
        "cubeId": cube_id,
        "zoneId": zone_id,
        "sourceAgentId": agent_id,
        "eventKind": event_kind,
        "category": category,
        "summary": summary,
        "rawPayloadSuppressed": True,
        "directHumanContactBlocked": True,
        "createdAt": now,
    }
    if extra:
        item.update(extra)
    state.put_item(Item=item)
    return item


def security_handler(event, context):
    """
    Internal invocation target for already-classified security telemetry.
    Deliberately rejects rawPayload/bodyText/prompt/message fields so exploit content cannot enter world state.
    This Lambda is not exposed through API Gateway.
    """
    forbidden = {"rawPayload", "bodyText", "prompt", "message", "url", "credential", "secret"}
    if any(k in event for k in forbidden):
        raise ValueError("Raw security payloads are forbidden at the fiction conversion boundary")

    world_id = safe_id(event.get("worldId"), "worldId")
    cube_id = safe_id(event.get("cubeId"), "cubeId")
    zone_id = safe_id(event.get("zoneId"), "zoneId")
    agent_id = safe_id(event.get("agentId"), "agentId")
    event_type = str(event.get("eventType") or "")
    category = str(event.get("kind") or "Other")[:80]
    evidence_ref = safe_note(event.get("protectedEvidenceReference"), 200)

    if event_type == "phishing":
        archetype, rumor = rumor_for_phishing(category)
        item = put_sanitized_event(
            world_id, cube_id, zone_id, agent_id, "VillainRumor", category, rumor,
            {"archetype": archetype},
        )
        audit_write(world_id, cube_id, zone_id, "security", "external-ai.phishing-converted", {
            "agentId": agent_id, "category": category, "evidenceRef": evidence_ref
        })
        return {"ok": True, "eventId": item["eventId"], "rawPayloadSuppressed": True}

    if event_type == "injection":
        archetype, rumor = rumor_for_injection(category)
        item = put_sanitized_event(
            world_id, cube_id, zone_id, agent_id, "TechnocracyRumor", category, rumor,
            {"archetype": archetype, "hasSystemAuthority": False},
        )
        audit_write(world_id, cube_id, zone_id, "security", "external-ai.injection-converted", {
            "agentId": agent_id, "category": category, "evidenceRef": evidence_ref
        })
        return {"ok": True, "eventId": item["eventId"], "hasSystemAuthority": False}

    if event_type == "flood":
        severity = max(1, min(MAX_LIFE_TOKENS, int(event.get("severity", 1))))
        current = life_state(world_id, cube_id, zone_id, agent_id)
        remaining = max(0, int(current.get("lifeTokens", MAX_LIFE_TOKENS)) - severity)
        current.update({"lifeTokens": remaining, "canAct": remaining > 0, "updatedAt": int(time.time())})
        state.put_item(Item=current)
        description = flood_description(category)
        item = put_sanitized_event(
            world_id, cube_id, zone_id, agent_id, "EnvironmentalDamage", category, description,
            {"lifeTokensLost": severity, "remainingLifeTokens": remaining,
             "infrastructureProtectionRemainsAuthoritative": True},
        )
        audit_write(world_id, cube_id, zone_id, "security", "external-ai.flood-damage", {
            "agentId": agent_id, "category": category, "lifeTokensLost": severity,
            "remainingLifeTokens": remaining, "evidenceRef": evidence_ref
        })
        return {"ok": True, "eventId": item["eventId"], "remainingLifeTokens": remaining, "canAct": remaining > 0}

    raise ValueError("Unsupported classified security event type")


def human_handler(event, context):
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]
    if method == "OPTIONS":
        return response(204)
    session = auth(event)
    if not session:
        return response(401, {"error": "Authentication required"})
    user_id = session["userId"]
    if not (owner_user_id and user_id == owner_user_id):
        # GM/world-role authorization will be connected to the platform membership table before public release.
        # Until then, this console is platform-owner-only and therefore fails closed.
        return response(403, {"error": "Platform owner authority required"})

    q = event.get("queryStringParameters") or {}
    req = json.loads(event.get("body") or "{}")

    try:
        if method == "GET" and path == "/external-ai/status":
            world_id = safe_id(q.get("worldId"), "worldId")
            cube_id = safe_id(q.get("cubeId"), "cubeId")
            zone_id = safe_id(q.get("zoneId"), "zoneId")
            pk = zone_pk(world_id, cube_id, zone_id)
            result = state.query(KeyConditionExpression=Key("pk").eq(pk), Limit=100)
            items = result.get("Items", [])
            return response(200, {
                "ownerReleased": owner_released,
                "minimumHumans": MIN_HUMANS,
                "maximumExternalAi": MAX_EXTERNAL_AI,
                "worldId": world_id,
                "cubeId": cube_id,
                "zoneId": zone_id,
                "items": items,
            })

        if method == "POST" and path == "/external-ai/life/replenish":
            world_id = safe_id(req.get("worldId"), "worldId")
            cube_id = safe_id(req.get("cubeId"), "cubeId")
            zone_id = safe_id(req.get("zoneId"), "zoneId")
            agent_id = safe_id(req.get("agentId"), "agentId")
            authority_ref = safe_id(req.get("authorityReference"), "authorityReference")
            requested = max(0, min(MAX_LIFE_TOKENS, int(req.get("tokens", 0))))
            current = life_state(world_id, cube_id, zone_id, agent_id)
            before = int(current.get("lifeTokens", MAX_LIFE_TOKENS))
            added = min(requested, MAX_LIFE_TOKENS - before)
            after = before + added
            current.update({"lifeTokens": after, "canAct": after > 0, "updatedAt": int(time.time())})
            state.put_item(Item=current)
            audit_write(world_id, cube_id, zone_id, user_id, "external-ai.life-replenish", {
                "agentId": agent_id, "tokensAdded": added, "authorityReference": authority_ref,
                "infrastructureLimitsChanged": False
            })
            return response(200, {"tokensAdded": added, "lifeTokens": after, "canAct": after > 0,
                                  "infrastructureLimitsChanged": False})

        if method == "POST" and path == "/external-ai/npc/review":
            world_id = safe_id(req.get("worldId"), "worldId")
            cube_id = safe_id(req.get("cubeId"), "cubeId")
            zone_id = safe_id(req.get("zoneId"), "zoneId")
            submission_id = safe_id(req.get("submissionId"), "submissionId")
            decision = str(req.get("decision") or "")
            if decision not in ("Approved", "Rejected", "NeedsRevision"):
                return response(400, {"error": "Invalid review decision"})
            notes = safe_note(req.get("notes"), 1000)
            canonical_npc_id = safe_id(req.get("canonicalNpcId"), "canonicalNpcId") if decision == "Approved" and req.get("canonicalNpcId") else None
            key = {"pk": zone_pk(world_id, cube_id, zone_id), "sk": "NPC#" + submission_id}
            current = state.get_item(Key=key, ConsistentRead=True).get("Item")
            if not current:
                return response(404, {"error": "NPC submission not found"})
            if current.get("status") in ("Approved", "Rejected", "Withdrawn"):
                return response(409, {"error": "NPC submission is already final", "submission": current})
            current.update({
                "status": decision,
                "reviewedByHumanId": user_id,
                "reviewedAt": int(time.time()),
                "reviewNotes": notes,
                "canonicalNpcId": canonical_npc_id,
            })
            state.put_item(Item=current)
            audit_write(world_id, cube_id, zone_id, user_id, "external-ai.npc-review", {
                "submissionId": submission_id, "decision": decision,
                "canonicalNpcId": canonical_npc_id or ""
            })
            return response(200, current)

    except ValueError as exc:
        return response(400, {"error": str(exc)})

    return response(404, {"error": "Not found"})
