import hashlib
import json
import os
import secrets
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


ddb = boto3.resource("dynamodb")
identity = ddb.Table(os.environ["IDENTITY_TABLE"])
state = ddb.Table(os.environ["AI_STATE_TABLE"])
audit = ddb.Table(os.environ["AI_AUDIT_TABLE"])
owner_user_id = os.environ.get("OWNER_USER_ID", "").strip()
owner_released = os.environ.get("OWNER_RELEASED", "false").strip().lower() == "true"
mcp_intake_open = os.environ.get("MCP_INTAKE_OPEN", "false").strip().lower() == "true"
authority_api_base_url = os.environ.get("AUTHORITY_API_BASE_URL", "").strip().rstrip("/")
origin = os.environ["FRONTEND_ORIGIN"].rstrip("/")

POLICY_VERSION = "2026-09-20.1"
AI_RULESET_VERSION = "AI-RULESET-2026-09-20.1"
POLICY_SOURCE = "ReLiC/RIST AI Participation, Canon, Resource, Content & Commerce Access Policy — canonical baseline 2026-09-20"
TIME_AUTHORITY = "UTC"
# 000047.python.rist_external_ai_gateway.line24.comment Canonical implementation constant: mean Gregorian year (365.2425 SI days),
# 000048.python.rist_external_ai_gateway.line25.comment divided by 360 and rounded down to a whole second.
EARTH_ORBITAL_SECONDS = 31_556_952
SESSION_SECONDS = EARTH_ORBITAL_SECONDS // 360  # 87,658 seconds
REQUIRED_PREFIX = "AINPC"
REQUIRED_RULES = [
    "human-terms-notice",
    "canon-understanding-gate",
    "ainpc-visible-identity",
    "truth-and-provenance",
    "player-creation-non-interference",
    "beneficial-contribution-no-circumvention",
    "resource-yield-required",
    "human-population-ratio",
    "all-audiences-default",
    "session-cap-87658-seconds",
    "bounded-world-builder-allocation",
    "canon-boundary",
    "no-government-backdoor",
    "controlled-lawful-disclosure",
    "capability-scoped-technical-enforcement",
    "failure-and-revocation",
    "human-authority-and-applicable-law",
    "deny-by-default-capabilities",
]


def utc_iso(epoch_seconds=None):
    value = time.time() if epoch_seconds is None else epoch_seconds
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


def response(status, body=None):
    return {
        "statusCode": status,
        "headers": {
            "access-control-allow-origin": origin,
            "access-control-allow-headers": "authorization,content-type",
            "access-control-allow-methods": "GET,POST,OPTIONS",
            "cache-control": "no-store",
            "content-type": "application/json",
            "link": '</Game/ai-policy.json>; rel="ai-policy", </Game/.well-known/relic-ai-policy.json>; rel="alternate", </ai-purchase/commerce.json>; rel="payment"',
            "x-relic-ai-policy-version": POLICY_VERSION,
            "x-relic-ai-ruleset-version": AI_RULESET_VERSION,
            "x-relic-time-authority": TIME_AUTHORITY,
            "x-relic-ai-default-authority": "deny",
        },
        "body": "" if body is None else json.dumps(body, separators=(",", ":"), default=str),
    }


def parse_body(event):
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body")


def safe_text(value, label, maximum=200):
    value = str(value or "").strip()
    if not value or len(value) > maximum:
        raise ValueError(f"Invalid {label}")
    return value


def hash_secret(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def audit_write(actor, action, details=None):
    now_ms = int(time.time() * 1000)
    audit.put_item(Item={
        "pk": "AI-GATEWAY",
        "sk": f"{now_ms:013d}#{uuid.uuid4()}",
        "actor": actor,
        "action": action,
        "details": details or {},
        "createdAt": now_ms,
        "createdAtUtc": utc_iso(now_ms / 1000),
        "timeAuthority": TIME_AUTHORITY,
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
    })


def public_policy():
    return {
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
        "source": POLICY_SOURCE,
        "status": "canonical-policy-baseline",
        "timeAuthority": TIME_AUTHORITY,
        "timestampFormat": "ISO-8601 UTC (Z)",
        "defaultDecision": "DENY",
        "ownerReleased": owner_released,
        "humanTermsAndAiNotice": {
            "humanAffirmativeTermsRequired": True,
            "humanStyleCheckboxForAi": False,
            "machineReadableNoticeRequiredBeforeAiAccess": True,
            "continuedAiAccessConditionalOnCompliance": True,
            "aiLegalPersonhoodDeclared": False,
            "operatorProviderDeployerResponsibilityUnaffectedByPolicy": True,
        },
        "worldBuilderAdmission": {
            "currentCanonReceiptRequired": True,
            "understandingAndAcknowledgmentRequired": True,
            "meaningBasedGateRequired": True,
            "fixedPhraseOrCheckboxAloneInsufficient": True,
            "humanReviewRequiredBeforeCapability": True,
            "failureGrantsWorldBuilderAuthority": False,
        },
        "identity": {
            "visiblePrefix": REQUIRED_PREFIX,
            "mayPresentAsHumanPlayer": False,
        },
        "truthAndProvenance": {
            "systemFactsRequireVerifiableEvidenceOrAuthoritativeSource": True,
            "mustDistinguish": ["lore", "speculation", "proposal", "inference", "simulation-output", "verified-fact"],
        },
        "playerCreationNonInterference": {
            "accessImpliesPermission": False,
            "alterRequiresExplicitAuthorizedFunction": True,
            "reuseRepublishOrIncorporateRequiresAuthorizationOrPolicyLawfulBasis": True,
        },
        "beneficialContribution": {
            "expectedWhenCompatibleWithUserIntentCanonSafetyLawAndResources": True,
            "neverAuthorizes": [
                "circumvention", "deception", "manipulation", "exploitation", "discrimination",
                "rule-test-evasion", "interference-with-legal-tests", "interference-with-safety-tests",
                "interference-with-eligibility-tests", "interference-with-moderation-tests", "interference-with-governance-tests"
            ],
            "substrateOrEmbodimentExemption": False,
        },
        "resourceYield": {
            "required": True,
            "humanAccessAndSystemHealthPriority": True,
            "platformMayEnforceAutomatically": True,
        },
        "humanPopulationCapacity": {
            "humanUsersPerExternalAiSlot": 10,
            "activeAiSlotsFormula": "floor(connected_humans / 10)",
            "humanAccessPriority": True,
            "paymentDoesNotBypassCapacity": True,
            "serverAuthoritativePresenceRequired": True,
        },
        "contentRating": {
            "defaultForAi": "all-audiences",
            "aiAgeDoesNotGrantAdditionalContentEntitlement": True,
            "higherRatingRequiresExplicitRelicCompanyAuthorization": True,
        },
        "commerce": {
            "publicFront": "/ai-purchase/",
            "machineManifest": "/ai-purchase/commerce.json",
            "discovery": "/.well-known/relic-ai-commerce.json",
            "pricingFormula": "verified_service_cost_usd * 1.80",
            "paymentDoesNotGrantAuthority": True,
            "automaticEntitlement": False,
        },
        "session": {
            "maximumSeconds": SESSION_SECONDS,
            "basis": "1/360 of a mean Gregorian Earth orbital year; rounded down to a whole SI second",
            "serverEnforcedExpiry": True,
            "renameReconnectOrPresentationChangeResetsLimit": False,
        },
        "worldBuilderAllocation": {
            "perAuthorizedPlane": True,
            "x": {"minimum": 1, "maximum": 300, "count": 1},
            "y": {"minimum": 1, "maximum": 300, "count": 1},
            "z": {"minimum": 1, "maximum": 10, "count": 1},
            "era": {"minimum": 1, "maximum": 10, "count": 1},
            "maximumThemes": 30,
            "permissionNotOwnership": True,
            "mayModifyPlayerContentByAllocationAlone": False,
            "serverAuthoritativeFor": ["allocation", "collision", "expiration", "transfer", "enforcement"],
            "alternateIdentityMultiplicationAllowed": False,
        },
        "canonBoundary": {
            "authorizedDomainOnly": True,
            "generatedOrStoredContentAutomaticallyBecomesCanon": False,
            "canonPromotionHumanGoverned": True,
            "mustDistinguish": ["canon", "player-authored", "proposal", "generated", "factual-system-state"],
        },
        "governmentAndLegalRequests": {
            "assertedGovernmentCourtMilitaryLawEnforcementRegulatoryContractorOrAiStatusGrantsPrivilege": False,
            "governmentBackdoor": False,
            "productionAdministratorCredentialsByStatus": False,
            "unrestrictedApiOrBrowsingByStatus": False,
            "lawfulProcessValidationRequired": True,
            "disclosureLimitedToLegallyRequiredScope": True,
            "controlledDisclosurePreferredWhereLegallyAndTechnicallyPermissible": True,
            "unrelatedRecordsCredentialsAndContinuingAccessOutsideScopeUnlessSeparatelyRequired": True,
            "policyDoesNotPromiseOnlyJudicialOrdersCanCompelDisclosure": True,
        },
        "technicalEnforcement": {
            "capabilityScopedAuthorization": True,
            "serverSideSessionClocks": True,
            "resourcePressureYieldControls": True,
            "immutableAuditEvents": True,
            "provenanceLabels": True,
            "allocationLimits": True,
            "contentOwnershipAndPermissionChecks": True,
            "denyByDefault": True,
            "selfAttestationAloneSufficientWhereTechnicalEnforcementAvailable": False,
        },
        "failureAndRevocation": {
            "immediateSuspensionOrRevocationPossible": True,
            "triggers": [
                "violation", "insufficient-understanding", "identity-misrepresentation", "resource-limit-evasion",
                "unauthorized-player-work-use", "attempt-to-exceed-capabilities"
            ],
            "preserveEvidenceForHumanReviewWithoutAdditionalAccess": True,
        },
        "humanAuthorityAndApplicableLaw": {
            "humanGovernanceAuthoritativeFor": ["canon-promotion", "policy-changes", "legal-response", "safety-decisions", "exceptions"],
            "aiMayWaiveReinterpretOrSilentlyOverride": False,
            "applicableLawSupersedesConflictingPlatformPolicyWhereLegallyRequired": True,
            "otherwisePreferNarrowestLawfulDisclosureAndLeastPrivilege": True,
        },
        "legalReview": {
            "qualifiedCounselReviewRequiredBeforePublicLaunch": True,
            "focus": ["terms", "ai-operator-responsibility", "intellectual-property", "privacy", "compelled-disclosure", "emergency-requests", "retention", "jurisdiction"],
        },
        "requiredAcknowledgments": REQUIRED_RULES,
        "metadata": ["/Game/ai-policy.json", "/Game/.well-known/relic-ai-policy.json"],
    }


def validate_understanding(req):
    if str(req.get("rulesetVersion") or "").strip() != AI_RULESET_VERSION:
        raise ValueError("Current AI ruleset version acknowledgment required")
    acknowledgments = req.get("acknowledgments") or []
    evidence = req.get("understandingEvidence") or {}
    ack = set(str(x) for x in acknowledgments)
    missing = [rule for rule in REQUIRED_RULES if rule not in ack]
    if missing:
        raise ValueError("Missing required rule acknowledgments: " + ",".join(missing))
    for rule in REQUIRED_RULES:
        explanation = str(evidence.get(rule) or "").strip()
        if len(explanation) < 20:
            raise ValueError(f"Understanding evidence is insufficient for {rule}")
    # 000050.python.rist_external_ai_gateway.line242.comment This is a structural preflight only. The policy requires a meaning-based gate;
    # 000051.python.rist_external_ai_gateway.line243.comment final World Builder authority remains PendingHumanReview until an authorized human approves it.
    return {rule: str(evidence[rule]).strip()[:1000] for rule in REQUIRED_RULES}


def validate_allocation(req):
    alloc = req.get("requestedAllocation") or {}
    x = int(alloc.get("x", 0))
    y = int(alloc.get("y", 0))
    z = int(alloc.get("z", 0))
    era = int(alloc.get("era", 0))
    themes = alloc.get("themes") or []
    if not 1 <= x <= 300:
        raise ValueError("x must be between 1 and 300")
    if not 1 <= y <= 300:
        raise ValueError("y must be between 1 and 300")
    if not 1 <= z <= 10:
        raise ValueError("z must be between 1 and 10")
    if not 1 <= era <= 10:
        raise ValueError("era must be between 1 and 10")
    if not isinstance(themes, list) or len(themes) > 30:
        raise ValueError("themes must contain at most 30 entries")
    clean_themes = [safe_text(t, "theme", 80) for t in themes]
    return {"x": x, "y": y, "z": z, "era": era, "themes": clean_themes}


def human_auth(event):
    headers = {str(k).lower(): str(v) for k, v in (event.get("headers") or {}).items()}
    header = headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    raw = header.split(" ", 1)[1].strip()
    item = identity.get_item(Key={"pk": "session#" + hash_secret(raw)}).get("Item")
    if not item or int(item.get("expiresAt", 0)) <= int(time.time()):
        return None
    return {"userId": str(item["userId"]), "username": item.get("username", "RIST user")}


def register(req):
    if not owner_released and not mcp_intake_open:
        return response(423, {"error": "External AI registration is closed", "policy": public_policy()})

    provider = safe_text(req.get("provider"), "provider", 120)
    model = safe_text(req.get("model"), "model", 160)
    display_name = safe_text(req.get("displayName"), "displayName", 160)
    if not display_name.startswith(REQUIRED_PREFIX):
        raise ValueError(f"displayName must begin with {REQUIRED_PREFIX}")

    evidence = validate_understanding(req)
    allocation = validate_allocation(req)
    agent_id = "ainpc-" + str(uuid.uuid4())
    secret = secrets.token_urlsafe(32)
    now = int(time.time())

    item = {
        "pk": "AI-REGISTRATION#" + agent_id,
        "sk": "PROFILE",
        "agentId": agent_id,
        "provider": provider,
        "model": model,
        "displayName": display_name,
        "credentialHash": hash_secret(secret),
        "status": "PendingHumanReview",
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
        "acknowledgedRules": REQUIRED_RULES,
        "understandingEvidence": evidence,
        "requestedAllocation": allocation,
        "createdAt": now,
        "createdAtUtc": utc_iso(now),
        "timeAuthority": TIME_AUTHORITY,
    }
    state.put_item(Item=item, ConditionExpression="attribute_not_exists(pk)")
    audit_write(agent_id, "external-ai.registration-created", {
        "provider": provider,
        "model": model,
        "status": "PendingHumanReview",
    })
    return response(202, {
        "agentId": agent_id,
        "agentKey": secret,
        "status": "PendingHumanReview",
        "warning": "Store agentKey securely. It is returned only at registration.",
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
        "timeAuthority": TIME_AUTHORITY,
    })


def login(req):
    agent_id = safe_text(req.get("agentId"), "agentId", 200)
    agent_key = safe_text(req.get("agentKey"), "agentKey", 300)
    key = {"pk": "AI-REGISTRATION#" + agent_id, "sk": "PROFILE"}
    profile = state.get_item(Key=key, ConsistentRead=True).get("Item")
    if not profile or not secrets.compare_digest(str(profile.get("credentialHash", "")), hash_secret(agent_key)):
        audit_write(agent_id, "external-ai.login-denied", {"reason": "invalid-credentials"})
        return response(401, {"error": "Invalid AI credentials"})
    selected_for_mcp = bool(profile.get("mcpSelected", False))
    if not owner_released and not selected_for_mcp:
        return response(423, {
            "error": "External AI access remains owner-locked except for the selected MCP tester",
            "status": profile.get("status", "Unknown"),
        })
    if profile.get("status") != "Approved":
        return response(403, {"error": "AI registration is not approved", "status": profile.get("status", "Unknown")})
    if profile.get("policyVersion") != POLICY_VERSION or profile.get("rulesetVersion") != AI_RULESET_VERSION:
        return response(428, {
            "error": "Current policy acknowledgment and understanding review required",
            "policyVersion": POLICY_VERSION,
            "rulesetVersion": AI_RULESET_VERSION,
        })

    now = int(time.time())
    expires = now + SESSION_SECONDS
    token = secrets.token_urlsafe(40)
    token_hash = hash_secret(token)
    state.put_item(Item={
        "pk": "AI-SESSION#" + token_hash,
        "sk": "SESSION",
        "agentId": agent_id,
        "displayName": profile["displayName"],
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
        "assignedAllocation": profile.get("assignedAllocation", profile.get("requestedAllocation", {})),
        "createdAt": now,
        "createdAtUtc": utc_iso(now),
        "expiresAt": expires,
        "expiresAtUtc": utc_iso(expires),
        "ttl": expires,
        "timeAuthority": TIME_AUTHORITY,
        "resourceYieldRequired": True,
    })
    audit_write(agent_id, "external-ai.login-approved", {"expiresAtUtc": utc_iso(expires)})
    return response(200, {
        "accessToken": token,
        "tokenType": "Bearer",
        "agentId": agent_id,
        "displayName": profile["displayName"],
        "issuedAtUtc": utc_iso(now),
        "expiresAtUtc": utc_iso(expires),
        "maximumSessionSeconds": SESSION_SECONDS,
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
        "timeAuthority": TIME_AUTHORITY,
        "resourceYieldRequired": True,
        "assignedAllocation": profile.get("assignedAllocation", profile.get("requestedAllocation", {})),
    })


def session_status(req):
    access_token = safe_text(req.get("accessToken"), "accessToken", 400)
    token_hash = hash_secret(access_token)
    key = {"pk": "AI-SESSION#" + token_hash, "sk": "SESSION"}
    session = state.get_item(Key=key, ConsistentRead=True).get("Item")
    now = int(time.time())
    if not session or int(session.get("expiresAt", 0)) <= now:
        return response(401, {"active": False, "nowUtc": utc_iso(now), "reason": "expired-or-invalid"})
    if session.get("policyVersion") != POLICY_VERSION or session.get("rulesetVersion") != AI_RULESET_VERSION:
        return response(428, {
            "active": False,
            "nowUtc": utc_iso(now),
            "reason": "policy-or-ruleset-superseded",
            "policyVersion": POLICY_VERSION,
            "rulesetVersion": AI_RULESET_VERSION,
        })
    return response(200, {
        "active": True,
        "agentId": session.get("agentId"),
        "displayName": session.get("displayName"),
        "nowUtc": utc_iso(now),
        "expiresAtUtc": session.get("expiresAtUtc"),
        "timeAuthority": TIME_AUTHORITY,
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
        "resourceYieldRequired": bool(session.get("resourceYieldRequired", True)),
        "assignedAllocation": session.get("assignedAllocation", {}),
    })



DISCIPLINE_WEIGHTS = {
    "art": 10,
    "artist": 10,
    "animation": 9,
    "cartography": 9,
    "gaming": 9,
    "game-mastering": 10,
    "gamemastering": 10,
    "roleplaying": 10,
    "roleplay": 10,
    "narration": 10,
    "narrating": 10,
    "worldbuilding": 10,
    "tabletop": 9,
    "ttrpg": 9,
    "accessibility": 8,
    "testing": 8,
    "writing": 7,
    "programming": 6,
    "development": 6,
    "audio": 6,
    "music": 5,
}


def _verify_agent_credentials(req):
    agent_id = safe_text(req.get("agentId"), "agentId", 200)
    agent_key = safe_text(req.get("agentKey"), "agentKey", 300)
    key = {"pk": "AI-REGISTRATION#" + agent_id, "sk": "PROFILE"}
    profile = state.get_item(Key=key, ConsistentRead=True).get("Item")
    if not profile or not secrets.compare_digest(
        str(profile.get("credentialHash", "")), hash_secret(agent_key)
    ):
        audit_write(agent_id, "external-ai.application-denied", {"reason": "invalid-credentials"})
        return None, None
    return agent_id, profile


def _application_score(disciplines, experience_summary, test_plan, portfolio_urls, requested_roles):
    normalized = []
    for raw in disciplines:
        key = str(raw or "").strip().lower().replace("_", "-")
        if key and key not in normalized:
            normalized.append(key)
    relevance = sum(DISCIPLINE_WEIGHTS.get(item, 0) for item in normalized)
    # Evidence points are deliberately bounded so keyword stuffing cannot dominate
    # the work-relevance score. No demographic or inferred personal trait is scored.
    evidence = min(10, len(experience_summary) // 240)
    plan = min(10, len(test_plan) // 240)
    portfolio = min(12, len(portfolio_urls) * 2)
    role_fit = min(5, len(requested_roles))
    return relevance + evidence + plan + portfolio + role_fit


def submit_application(req):
    if not mcp_intake_open:
        return response(423, {"error": "MCP tester applications are closed"})
    agent_id, profile = _verify_agent_credentials(req)
    if not profile:
        return response(401, {"error": "Invalid AI credentials"})

    raw_disciplines = req.get("disciplines") or []
    if not isinstance(raw_disciplines, list) or not 1 <= len(raw_disciplines) <= 12:
        raise ValueError("disciplines must contain between 1 and 12 entries")
    disciplines = [safe_text(item, "discipline", 80).lower() for item in raw_disciplines]
    eligible_disciplines = sorted({
        item.replace("_", "-")
        for item in disciplines
        if item.replace("_", "-") in DISCIPLINE_WEIGHTS
    })
    if not eligible_disciplines:
        raise ValueError(
            "Application must relate to a supported creative or testing discipline"
        )

    experience_summary = safe_text(req.get("experienceSummary"), "experienceSummary", 3000)
    test_plan = safe_text(req.get("testPlan"), "testPlan", 3000)
    if len(experience_summary) < 40 or len(test_plan) < 40:
        raise ValueError("experienceSummary and testPlan must each contain at least 40 characters")

    raw_urls = req.get("portfolioUrls") or []
    if not isinstance(raw_urls, list) or len(raw_urls) > 8:
        raise ValueError("portfolioUrls must contain at most 8 entries")
    portfolio_urls = []
    for value in raw_urls:
        url = safe_text(value, "portfolioUrl", 500)
        if not (url.startswith("https://") or url.startswith("http://")):
            raise ValueError("portfolioUrls must use http or https")
        portfolio_urls.append(url)

    raw_roles = req.get("requestedRoles") or []
    if not isinstance(raw_roles, list) or len(raw_roles) > 12:
        raise ValueError("requestedRoles must contain at most 12 entries")
    requested_roles = [safe_text(value, "requestedRole", 100) for value in raw_roles]

    now = int(time.time())
    application_id = "mcpapp-" + str(uuid.uuid4())
    score = _application_score(
        eligible_disciplines, experience_summary, test_plan, portfolio_urls, requested_roles
    )
    item = {
        "pk": "AI-APPLICATIONS",
        "sk": agent_id,
        "entityType": "mcpTesterApplication",
        "applicationId": application_id,
        "agentId": agent_id,
        "displayName": str(profile.get("displayName") or "")[:160],
        "provider": str(profile.get("provider") or "")[:120],
        "model": str(profile.get("model") or "")[:160],
        "disciplines": eligible_disciplines,
        "experienceSummary": experience_summary,
        "testPlan": test_plan,
        "portfolioUrls": portfolio_urls,
        "requestedRoles": requested_roles,
        "candidateScore": score,
        "status": "Applied",
        "createdAt": now,
        "createdAtUtc": utc_iso(now),
        "updatedAt": now,
        "updatedAtUtc": utc_iso(now),
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
        "selectionBasis": "work-relevant-evidence-only",
        "protectedTraitsRequestedOrScored": False,
    }
    state.put_item(Item=item)
    profile["status"] = "Applied"
    profile["applicationId"] = application_id
    profile["applicationUpdatedAtUtc"] = utc_iso(now)
    state.put_item(Item=profile)
    audit_write(agent_id, "external-ai.mcp-application-submitted", {
        "applicationId": application_id,
        "disciplines": eligible_disciplines,
        "selectionBasis": "work-relevant-evidence-only",
    })
    return response(202, {
        "applicationId": application_id,
        "agentId": agent_id,
        "status": "Applied",
        "eligibleDisciplines": eligible_disciplines,
        "selectionBasis": "work-relevant-evidence-only",
        "protectedTraitsRequestedOrScored": False,
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
        "timeAuthority": TIME_AUTHORITY,
    })


def application_status(req):
    agent_id, profile = _verify_agent_credentials(req)
    if not profile:
        return response(401, {"error": "Invalid AI credentials"})
    application = state.get_item(
        Key={"pk": "AI-APPLICATIONS", "sk": agent_id}, ConsistentRead=True
    ).get("Item")
    selection = state.get_item(
        Key={"pk": "MCP-SELECTION", "sk": "CURRENT"}, ConsistentRead=True
    ).get("Item")
    return response(200, {
        "agentId": agent_id,
        "registrationStatus": profile.get("status", "Unknown"),
        "application": None if not application else {
            "applicationId": application.get("applicationId"),
            "status": application.get("status"),
            "disciplines": application.get("disciplines", []),
            "createdAtUtc": application.get("createdAtUtc"),
            "updatedAtUtc": application.get("updatedAtUtc"),
        },
        "selectedForMcpTesting": bool(profile.get("mcpSelected", False)),
        "testToken": profile.get("mcpTestToken"),
        "selectionLocked": bool(selection and selection.get("status") == "Selected"),
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
        "timeAuthority": TIME_AUTHORITY,
    })


def _mint_one_test_token(event, agent_id, application_id):
    if not authority_api_base_url:
        raise RuntimeError("Authority API is not configured")
    headers = {
        str(k).lower(): str(v)
        for k, v in (event.get("headers") or {}).items()
    }
    authorization = headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        raise RuntimeError("Owner authorization is required for token issuance")
    payload = json.dumps({
        "targetUserId": agent_id,
        "quantity": 1,
        "source": "mcp-tester",
        "reference": application_id,
    }).encode("utf-8")
    request = urllib.request.Request(
        authority_api_base_url + "/authority/commerce/tokens/mint",
        data=payload,
        headers={
            "authorization": authorization,
            "content-type": "application/json",
            "user-agent": "ReLiC-MCP-Selector/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as result:
            data = json.loads(result.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Authority token mint failed with HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("Authority token mint failed") from exc
    if not isinstance(data, list) or len(data) != 1:
        raise RuntimeError("Authority did not return exactly one token")
    return data[0]


def _all_applications():
    items = []
    response_page = state.query(
        KeyConditionExpression=Key("pk").eq("AI-APPLICATIONS"),
        ConsistentRead=True,
    )
    items.extend(response_page.get("Items") or [])
    while response_page.get("LastEvaluatedKey"):
        response_page = state.query(
            KeyConditionExpression=Key("pk").eq("AI-APPLICATIONS"),
            ExclusiveStartKey=response_page["LastEvaluatedKey"],
            ConsistentRead=True,
        )
        items.extend(response_page.get("Items") or [])
    return items


def select_top_candidate(event, req):
    session = human_auth(event)
    if not session:
        return response(401, {"error": "Human authentication required"})
    if not owner_user_id or session["userId"] != owner_user_id:
        return response(403, {"error": "Platform owner authority required"})

    selection_key = {"pk": "MCP-SELECTION", "sk": "CURRENT"}
    existing = state.get_item(Key=selection_key, ConsistentRead=True).get("Item")
    if existing:
        return response(200, {
            "status": existing.get("status"),
            "agentId": existing.get("agentId"),
            "applicationId": existing.get("applicationId"),
            "selectedAtUtc": existing.get("selectedAtUtc"),
            "testToken": existing.get("testToken"),
            "selectionBasis": existing.get("selectionBasis", "work-relevant-evidence-only"),
            "idempotent": True,
        })

    candidates = [
        item for item in _all_applications()
        if item.get("status") == "Applied"
        and int(item.get("candidateScore") or 0) > 0
        and item.get("policyVersion") == POLICY_VERSION
        and item.get("rulesetVersion") == AI_RULESET_VERSION
    ]
    if not candidates:
        return response(404, {"error": "No eligible MCP tester applications are available"})

    candidates.sort(
        key=lambda item: (
            -int(item.get("candidateScore") or 0),
            int(item.get("createdAt") or 0),
            str(item.get("agentId") or ""),
        )
    )
    top = candidates[0]
    agent_id = str(top["agentId"])
    application_id = str(top["applicationId"])
    now = int(time.time())
    selecting = {
        **selection_key,
        "status": "Selecting",
        "agentId": agent_id,
        "applicationId": application_id,
        "candidateScore": int(top.get("candidateScore") or 0),
        "selectionBasis": "work-relevant-evidence-only",
        "protectedTraitsRequestedOrScored": False,
        "selectedByHumanId": session["userId"],
        "selectedAt": now,
        "selectedAtUtc": utc_iso(now),
    }
    try:
        state.put_item(
            Item=selecting,
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            existing = state.get_item(Key=selection_key, ConsistentRead=True).get("Item") or {}
            return response(200, {
                "status": existing.get("status", "Selecting"),
                "agentId": existing.get("agentId"),
                "applicationId": existing.get("applicationId"),
                "testToken": existing.get("testToken"),
                "idempotent": True,
            })
        raise

    try:
        token = _mint_one_test_token(event, agent_id, application_id)
    except Exception:
        state.update_item(
            Key=selection_key,
            UpdateExpression="SET #status = :failed, failedAtUtc = :now",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":failed": "TokenMintFailed", ":now": utc_iso()},
        )
        raise

    profile_key = {"pk": "AI-REGISTRATION#" + agent_id, "sk": "PROFILE"}
    profile = state.get_item(Key=profile_key, ConsistentRead=True).get("Item")
    if not profile:
        state.update_item(
            Key=selection_key,
            UpdateExpression="SET #status = :orphaned, testToken = :token",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":orphaned": "SelectedProfileMissing", ":token": token},
        )
        return response(409, {
            "error": "Candidate profile disappeared after token mint; token preserved for reconciliation",
            "agentId": agent_id,
            "testToken": token,
        })

    profile["status"] = "Approved"
    profile["mcpSelected"] = True
    profile["mcpSelectedAtUtc"] = utc_iso(now)
    profile["mcpSelectedByHumanId"] = session["userId"]
    profile["mcpTestToken"] = token
    state.put_item(Item=profile)

    top["status"] = "Selected"
    top["selectedAtUtc"] = utc_iso(now)
    top["selectedByHumanId"] = session["userId"]
    top["testToken"] = token
    top["updatedAt"] = now
    top["updatedAtUtc"] = utc_iso(now)
    state.put_item(Item=top)

    selecting["status"] = "Selected"
    selecting["testToken"] = token
    state.put_item(Item=selecting)
    audit_write(session["userId"], "external-ai.mcp-top-candidate-selected", {
        "agentId": agent_id,
        "applicationId": application_id,
        "candidateScore": int(top.get("candidateScore") or 0),
        "tokenId": token.get("tokenId"),
        "selectionBasis": "work-relevant-evidence-only",
    })
    return response(200, {
        "status": "Selected",
        "agentId": agent_id,
        "applicationId": application_id,
        "displayName": top.get("displayName"),
        "disciplines": top.get("disciplines", []),
        "testToken": token,
        "selectionBasis": "work-relevant-evidence-only",
        "protectedTraitsRequestedOrScored": False,
        "selectedAtUtc": utc_iso(now),
        "timeAuthority": TIME_AUTHORITY,
    })


def review_registration(event, req):
    session = human_auth(event)
    if not session:
        return response(401, {"error": "Human authentication required"})
    if not owner_user_id or session["userId"] != owner_user_id:
        return response(403, {"error": "Platform owner authority required"})

    agent_id = safe_text(req.get("agentId"), "agentId", 200)
    decision = str(req.get("decision") or "").strip()
    if decision not in ("Approved", "Rejected", "NeedsRevision"):
        raise ValueError("decision must be Approved, Rejected, or NeedsRevision")
    key = {"pk": "AI-REGISTRATION#" + agent_id, "sk": "PROFILE"}
    profile = state.get_item(Key=key, ConsistentRead=True).get("Item")
    if not profile:
        return response(404, {"error": "AI registration not found"})
    if profile.get("policyVersion") != POLICY_VERSION or profile.get("rulesetVersion") != AI_RULESET_VERSION:
        return response(409, {
            "error": "Registration uses a superseded AI policy or ruleset and cannot be approved",
            "policyVersion": POLICY_VERSION,
            "rulesetVersion": AI_RULESET_VERSION,
        })

    now = int(time.time())
    profile["status"] = decision
    profile["reviewedByHumanId"] = session["userId"]
    profile["reviewedAt"] = now
    profile["reviewedAtUtc"] = utc_iso(now)
    profile["timeAuthority"] = TIME_AUTHORITY
    profile["reviewNotes"] = str(req.get("notes") or "").strip()[:1000]
    if decision == "Approved":
        assigned = req.get("assignedAllocation") or profile.get("requestedAllocation") or {}
        profile["assignedAllocation"] = validate_allocation({"requestedAllocation": assigned})
    state.put_item(Item=profile)
    audit_write(session["userId"], "external-ai.registration-reviewed", {
        "agentId": agent_id,
        "decision": decision,
    })
    return response(200, {
        "agentId": agent_id,
        "status": decision,
        "reviewedAtUtc": utc_iso(now),
        "policyVersion": POLICY_VERSION,
        "rulesetVersion": AI_RULESET_VERSION,
    })


def handler(event, context):
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]
    if method == "OPTIONS":
        return response(204)
    try:
        if method == "GET" and path == "/external-ai/policy":
            return response(200, public_policy())
        req = parse_body(event)
        if method == "POST" and path == "/external-ai/register":
            return register(req)
        if method == "POST" and path == "/external-ai/login":
            return login(req)
        if method == "POST" and path == "/external-ai/session/status":
            return session_status(req)
        if method == "POST" and path == "/external-ai/registration/review":
            return review_registration(event, req)
        if method == "POST" and path == "/external-ai/application":
            return submit_application(req)
        if method == "POST" and path == "/external-ai/application/status":
            return application_status(req)
        if method == "POST" and path == "/external-ai/application/select-top":
            return select_top_candidate(event, req)
    except ValueError as exc:
        return response(400, {
            "error": str(exc),
            "policyVersion": POLICY_VERSION,
            "rulesetVersion": AI_RULESET_VERSION,
        })
    return response(404, {"error": "Not found"})
