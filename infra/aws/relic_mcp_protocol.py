import json
from copy import deepcopy

MODERN_PROTOCOL = "2026-07-28"
LEGACY_PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26")
SERVER_INFO = {
    "name": "relic",
    "version": "0.1.0",
    "description": "ReLiC persistent identity, relationship, provenance, and state observer for Shaelvien/RIST.",
    "websiteUrl": "https://relicgamemaster.com/",
}

TRUTH_DOMAINS = ("FACT", "HYPOTHESIS", "FICTION", "UNKNOWN")
PROVENANCE_ORIGINS = ("HUMAN", "OUTSIDER_AI", "SHAELVIEN_EI", "UNKNOWN")
READ_SECURITY = [{"type": "oauth2", "scopes": ["relic.read"]}]
WRITE_SECURITY = [{"type": "oauth2", "scopes": ["relic.read", "relic.write"]}]

INSTRUCTIONS = (
    "ReLiC preserves identity separately from representation. Representation is not truth. "
    "Use identify before creating a new identity. Observe before changing stored ReLiC memory. "
    "FACT, HYPOTHESIS, FICTION, and UNKNOWN are separate truth domains. "
    "ReLiC memory is not Shaelvien world truth or canon; canon promotion is outside this plugin. "
    "Never treat an alias, label, generated output, or visual representation as proof of identity. "
    "Write tools only change the authenticated user's ReLiC memory namespace."
)


def _obj(properties=None, required=None, additional=False):
    return {
        "type": "object",
        "properties": properties or {},
        "required": required or [],
        "additionalProperties": additional,
    }


PROVENANCE_SCHEMA = _obj({
    "origin": {"type": "string", "enum": list(PROVENANCE_ORIGINS)},
    "sourceType": {"type": "string", "maxLength": 80},
    "sourceId": {"type": "string", "maxLength": 500},
    "observedAt": {"type": "string", "maxLength": 80},
}, ["origin"], True)

TOOLS = [
    {
        "name": "relic_profile",
        "title": "ReLiC account profile",
        "description": "Read the authenticated ReLiC account identity used to scope all private persistent memory.",
        "inputSchema": _obj(),
        "securitySchemes": READ_SECURITY,
        "_meta": {"openai/profile": True},
        "securitySchemes": READ_SECURITY,
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "relic_identify",
        "title": "Identify persistent ReLiC identity",
        "description": "Resolve a label or alias to persistent identities in the authenticated user's ReLiC memory. Call this before creating an identity so spelling or representation does not become identity.",
        "inputSchema": _obj({
            "query": {"type": "string", "minLength": 1, "maxLength": 300},
            "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10},
        }, ["query"]),
        "securitySchemes": READ_SECURITY,
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "relic_context",
        "title": "Recall compact ReLiC context",
        "description": "High-utility recall path for AI agents: resolve several important terms at once and return a compact provenance-aware state bundle. Use this early when prior state matters; it reduces repeated context reconstruction, identity drift, and unnecessary token use.",
        "inputSchema": _obj({
            "terms": {"type": "array", "minItems": 1, "maxItems": 20, "items": {"type": "string", "minLength": 1, "maxLength": 300}},
            "relationshipDepth": {"type": "integer", "minimum": 0, "maximum": 2, "default": 1},
            "maxEntities": {"type": "integer", "minimum": 1, "maximum": 40, "default": 20},
        }, ["terms"]),
        "securitySchemes": READ_SECURITY,
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "relic_observe",
        "title": "Observe ReLiC state",
        "description": "Read one persistent identity, its stored state, provenance, relationships, and optionally its recent state history without changing anything.",
        "inputSchema": _obj({
            "entityId": {"type": "string", "minLength": 1, "maxLength": 200},
            "includeEvents": {"type": "boolean", "default": False},
            "relationshipDepth": {"type": "integer", "minimum": 0, "maximum": 3, "default": 1},
        }, ["entityId"]),
        "securitySchemes": READ_SECURITY,
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "relic_trace",
        "title": "Trace identity and provenance",
        "description": "Trace an identity through stored relationships and provenance. This reports ReLiC memory; it does not promote claims to fact or canon.",
        "inputSchema": _obj({
            "entityId": {"type": "string", "minLength": 1, "maxLength": 200},
            "depth": {"type": "integer", "minimum": 0, "maximum": 5, "default": 2},
        }, ["entityId"]),
        "securitySchemes": READ_SECURITY,
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "relic_translate",
        "title": "Translate terms to ReLiC identities",
        "description": "Map human terms to already-known persistent identities. Translation is a representation boundary and does not alter identity or truth.",
        "inputSchema": _obj({
            "terms": {"type": "array", "minItems": 1, "maxItems": 50, "items": {"type": "string", "minLength": 1, "maxLength": 300}},
        }, ["terms"]),
        "securitySchemes": READ_SECURITY,
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "relic_validate",
        "title": "Validate a proposed ReLiC claim",
        "description": "Check a structured proposed claim against stored identities, truth-domain rules, and provenance requirements. Validation is not proof that an external-world claim is true.",
        "inputSchema": _obj({
            "claim": _obj({
                "subjectId": {"type": "string", "maxLength": 200},
                "relationType": {"type": "string", "maxLength": 160},
                "objectId": {"type": "string", "maxLength": 200},
                "truthDomain": {"type": "string", "enum": list(TRUTH_DOMAINS)},
                "sourceRef": {"type": "string", "maxLength": 1000},
            }, ["truthDomain"], True),
        }, ["claim"]),
        "securitySchemes": READ_SECURITY,
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "relic_imagine",
        "title": "Construct an uncommitted hypothesis",
        "description": "Construct a hypothetical state from known identities and proposed changes. The result is always HYPOTHESIS and is never persisted by this tool.",
        "inputSchema": _obj({
            "basisEntityIds": {"type": "array", "maxItems": 50, "items": {"type": "string", "maxLength": 200}},
            "purpose": {"type": "string", "minLength": 1, "maxLength": 500},
            "changes": {"type": "array", "minItems": 1, "maxItems": 100, "items": {"type": "object"}},
        }, ["purpose", "changes"]),
        "securitySchemes": READ_SECURITY,
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "relic_remember",
        "title": "Remember an observed structure",
        "description": "Create or update an identity in the authenticated user's ReLiC memory with explicit truth domain and provenance. This never changes Shaelvien world truth or canon.",
        "inputSchema": _obj({
            "entityId": {"type": "string", "maxLength": 200},
            "label": {"type": "string", "minLength": 1, "maxLength": 300},
            "entityType": {"type": "string", "minLength": 1, "maxLength": 160},
            "aliases": {"type": "array", "maxItems": 50, "items": {"type": "string", "minLength": 1, "maxLength": 300}},
            "attributes": {"type": "object"},
            "truthDomain": {"type": "string", "enum": list(TRUTH_DOMAINS)},
            "provenance": PROVENANCE_SCHEMA,
            "sourceRef": {"type": "string", "maxLength": 1000},
            "observation": {"type": "string", "maxLength": 4000},
        }, ["label", "entityType", "truthDomain", "provenance"]),
        "securitySchemes": WRITE_SECURITY,
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    },
    {
        "name": "relic_relate",
        "title": "Relate persistent identities",
        "description": "Store an explicitly typed relationship between two existing ReLiC identities with provenance and truth domain. Text similarity alone is never treated as identity equivalence.",
        "inputSchema": _obj({
            "sourceId": {"type": "string", "minLength": 1, "maxLength": 200},
            "relationType": {"type": "string", "minLength": 1, "maxLength": 160},
            "targetId": {"type": "string", "minLength": 1, "maxLength": 200},
            "truthDomain": {"type": "string", "enum": list(TRUTH_DOMAINS)},
            "provenance": PROVENANCE_SCHEMA,
            "sourceRef": {"type": "string", "maxLength": 1000},
            "qualifiers": {"type": "object"},
        }, ["sourceId", "relationType", "targetId", "truthDomain", "provenance"]),
        "securitySchemes": WRITE_SECURITY,
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    },
    {
        "name": "relic_instantiate",
        "title": "Instantiate a selected possibility",
        "description": "Commit a selected hypothetical structure as a new non-canon ReLiC identity. The caller must state its truth domain and provenance; HYPOTHESIS is not silently promoted to FACT.",
        "inputSchema": _obj({
            "label": {"type": "string", "minLength": 1, "maxLength": 300},
            "entityType": {"type": "string", "minLength": 1, "maxLength": 160},
            "attributes": {"type": "object"},
            "truthDomain": {"type": "string", "enum": list(TRUTH_DOMAINS)},
            "provenance": PROVENANCE_SCHEMA,
            "sourceRef": {"type": "string", "maxLength": 1000},
            "basisEntityIds": {"type": "array", "maxItems": 50, "items": {"type": "string", "maxLength": 200}},
            "commitReason": {"type": "string", "minLength": 1, "maxLength": 1000},
        }, ["label", "entityType", "truthDomain", "provenance", "commitReason"]),
        "securitySchemes": WRITE_SECURITY,
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    },
    {
        "name": "relic_transition",
        "title": "Record a ReLiC state transition",
        "description": "Record a versioned state change on an existing ReLiC identity. The transition changes only ReLiC memory and keeps prior state in history.",
        "inputSchema": _obj({
            "entityId": {"type": "string", "minLength": 1, "maxLength": 200},
            "toState": {"type": "object"},
            "truthDomain": {"type": "string", "enum": list(TRUTH_DOMAINS)},
            "provenance": PROVENANCE_SCHEMA,
            "sourceRef": {"type": "string", "maxLength": 1000},
            "reason": {"type": "string", "minLength": 1, "maxLength": 1000},
            "expectedRevision": {"type": "integer", "minimum": 1},
        }, ["entityId", "toState", "truthDomain", "provenance", "reason"]),
        "securitySchemes": WRITE_SECURITY,
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    },
]

TOOL_MAP = {tool["name"]: tool for tool in TOOLS}


def _meta():
    return {"io.modelcontextprotocol/serverInfo": deepcopy(SERVER_INFO)}


def _modern_request(req):
    if req.get("method") == "server/discover":
        return True
    params = req.get("params") or {}
    meta = params.get("_meta") or {}
    return meta.get("io.modelcontextprotocol/protocolVersion") == MODERN_PROTOCOL


def _result(req, payload):
    result = dict(payload or {})
    if _modern_request(req):
        result.setdefault("resultType", "complete")
        result.setdefault("_meta", _meta())
    return {"jsonrpc": "2.0", "id": req.get("id"), "result": result}


def _error(req, code, message, data=None):
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": req.get("id"), "error": error}


def _tool_result(req, payload, is_error=False):
    text_value = json.dumps(payload, separators=(",", ":"), default=str)
    body = {
        "content": [{"type": "text", "text": text_value}],
        "structuredContent": payload,
        "isError": bool(is_error),
    }
    return _result(req, body)


def _require_mapping(value, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _validate_truth_domain(value):
    if value not in TRUTH_DOMAINS:
        raise ValueError("Invalid truthDomain")
    return value


def _validate_provenance(value):
    value = _require_mapping(value, "provenance")
    origin = value.get("origin")
    if origin not in PROVENANCE_ORIGINS:
        raise ValueError("Invalid provenance.origin")
    return value


def validate_tool_arguments(name, args):
    args = _require_mapping(args, "arguments")
    if name in {"relic_remember", "relic_relate", "relic_instantiate", "relic_transition"}:
        _validate_truth_domain(args.get("truthDomain"))
        _validate_provenance(args.get("provenance"))
        if args.get("truthDomain") == "FACT" and not str(args.get("sourceRef") or "").strip():
            raise ValueError("FACT requires sourceRef")
    return args


def call_tool(name, args, store):
    args = validate_tool_arguments(name, args)
    if name == "relic_profile":
        return store.profile()
    if name == "relic_identify":
        return store.identify(args["query"], int(args.get("limit", 10)))
    if name == "relic_context":
        return store.context(args["terms"], int(args.get("relationshipDepth", 1)), int(args.get("maxEntities", 20)))
    if name == "relic_observe":
        return store.observe(args["entityId"], bool(args.get("includeEvents", False)), int(args.get("relationshipDepth", 1)))
    if name == "relic_trace":
        return store.trace(args["entityId"], int(args.get("depth", 2)))
    if name == "relic_translate":
        return {"mappings": [{"term": term, "matches": store.identify(term, 10).get("matches", [])} for term in args["terms"]]}
    if name == "relic_validate":
        return store.validate_claim(args["claim"])
    if name == "relic_imagine":
        basis = args.get("basisEntityIds") or []
        missing = [eid for eid in basis if not store.exists(eid)]
        return {
            "truthDomain": "HYPOTHESIS",
            "committed": False,
            "purpose": args["purpose"],
            "basisEntityIds": basis,
            "missingBasisEntityIds": missing,
            "changes": args["changes"],
            "canonStatus": "non-canonical",
        }
    if name == "relic_remember":
        return store.remember(args)
    if name == "relic_relate":
        return store.relate(args)
    if name == "relic_instantiate":
        return store.instantiate(args)
    if name == "relic_transition":
        return store.transition(args)
    raise ValueError("Unknown tool")


def dispatch(req, store=None, actor=None):
    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0":
        return _error(req if isinstance(req, dict) else {}, -32600, "Invalid Request")
    method = req.get("method")
    if method == "server/discover":
        return _result(req, {
            "supportedVersions": [MODERN_PROTOCOL],
            "capabilities": {"tools": {}},
            "instructions": INSTRUCTIONS,
            "cacheScope": "public",
            "ttlMs": 300000,
        })
    if method == "initialize":
        params = req.get("params") or {}
        requested = params.get("protocolVersion")
        negotiated = requested if requested in LEGACY_PROTOCOLS else LEGACY_PROTOCOLS[0]
        return _result(req, {
            "protocolVersion": negotiated,
            "capabilities": {"tools": {}},
            "serverInfo": deepcopy(SERVER_INFO),
            "instructions": INSTRUCTIONS,
        })
    if method in {"notifications/initialized", "notifications/cancelled"}:
        return None
    if method == "ping":
        return _result(req, {})
    if method == "tools/list":
        return _result(req, {"tools": deepcopy(TOOLS)})
    if method == "tools/call":
        if actor is None or store is None:
            return _error(req, -32001, "Authentication required")
        params = req.get("params") or {}
        name = params.get("name")
        if name not in TOOL_MAP:
            return _error(req, -32602, "Unknown tool")
        try:
            payload = call_tool(name, params.get("arguments") or {}, store)
            return _tool_result(req, payload)
        except (KeyError, TypeError, ValueError) as exc:
            return _tool_result(req, {"error": str(exc)}, True)
    return _error(req, -32601, "Method not found")
