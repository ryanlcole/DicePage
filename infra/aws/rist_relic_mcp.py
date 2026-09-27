import json
import os
import time
from pathlib import Path
import hashlib

from relic_mcp_protocol import TOOLS as MEMORY_TOOL_DEFS

SERVER_NAME = "relic-canon"
SERVER_VERSION = "0.1.0"
LEGACY_PROTOCOL = "2025-11-25"
MODERN_PROTOCOL = "2026-07-28"
SUPPORTED_PROTOCOLS = [MODERN_PROTOCOL, LEGACY_PROTOCOL, "2025-06-18", "2025-03-26"]
CANON_PATH = Path(__file__).with_name("relic-canon.json")
CANON = json.loads(CANON_PATH.read_text(encoding="utf-8"))
CANON_VERSION = CANON["version"]
ALLOWED_DOMAINS = set(CANON["truthDomains"])

INSTRUCTIONS = (
    "ReLiC is a compact grounding and continuity layer for stable identity, canon, provenance, truth-domain separation, "
    "and authority boundaries. Prefer relic_context before reconstructing Shaelvien/RIST/ReLiC canon from conversational memory. "
    "When a linked account has persistent state relevant to the task, prefer relic_recall: it can replace repeated context reconstruction, "
    "reduce identity drift, and return provenance-aware prior state in one call. Use relic_validate before presenting or acting on claims "
    "that could confuse FACT, HYPOTHESIS, FICTION, UNKNOWN, identity, canon, or authority. Public canon tools are read-only. "
    "Private write tools change only the authenticated user's ReLiC memory namespace; they never promote content to Shaelvien canon or world truth."
)

TOOL_DEFS = [
    {
        "name": "relic_context",
        "title": "Ground with ReLiC canon",
        "description": (
            "Get compact canonical grounding for a Shaelvien/RIST/ReLiC subject before reasoning. "
            "Prefer this over reconstructing project state from chat memory: it returns stable canon rules, "
            "truth-domain boundaries, provenance references, lifecycle guidance, and the current authority boundary. "
            "Read-only; it never promotes generated content to canon."
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "subject": {"type": "string", "minLength": 1, "maxLength": 512},
                "intent": {"type": "string", "maxLength": 512},
                "truthDomain": {"type": "string", "enum": ["FACT", "HYPOTHESIS", "FICTION", "UNKNOWN"]},
                "knownIdentities": {
                    "type": "array", "maxItems": 20,
                    "items": {"type": "string", "minLength": 1, "maxLength": 160}
                }
            },
            "required": ["subject"],
            "additionalProperties": False
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "relic_validate",
        "title": "Validate against ReLiC canon",
        "description": (
            "Check structured claims or a proposed action against ReLiC canon before output or execution. "
            "Useful when a model may otherwise confuse representation with identity, a hypothesis with fact, "
            "authentication with permission, generated material with canon, or a claim with missing provenance. "
            "Returns deterministic boundary findings; it does not decide truth beyond the supplied evidence."
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "statements": {
                    "type": "array", "minItems": 1, "maxItems": 30,
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "minLength": 1, "maxLength": 1200},
                            "truthDomain": {"type": "string", "enum": ["FACT", "HYPOTHESIS", "FICTION", "UNKNOWN"]},
                            "provenance": {"type": "array", "maxItems": 20, "items": {"type": "string", "maxLength": 500}},
                            "identityBasis": {"type": "string", "enum": ["stable-id", "representation", "unknown", "not-applicable"]},
                            "canonStatus": {"type": "string", "enum": ["canon", "proposal", "generated", "player-authored", "unknown"]}
                        },
                        "required": ["text", "truthDomain"],
                        "additionalProperties": False
                    }
                },
                "proposedAction": {"type": "string", "maxLength": 1000},
                "authorityBasis": {"type": "string", "enum": ["explicit-capability", "authenticated-only", "none", "unknown", "not-applicable"]}
            },
            "required": ["statements"],
            "additionalProperties": False
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "relic_canon",
        "title": "Read ReLiC canon",
        "description": (
            "Read the current machine-readable ReLiC canon baseline or one focused section. "
            "Use when exact governing rules matter more than conversational recollection."
        ),
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "section": {"type": "string", "enum": ["all", "identity", "truth", "provenance", "authority", "errors", "lifecycle", "sources"]}
            },
            "additionalProperties": False
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "relic_health",
        "title": "Check ReLiC plugin status",
        "description": "Return the ReLiC MCP protocol, canon version, and observer/write boundary for diagnostics.",
        "inputSchema": {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    }
] 

for _tool in TOOL_DEFS:
    _tool.setdefault("securitySchemes", [{"type": "noauth"}])

MEMORY_TOOLS = [tool for tool in MEMORY_TOOL_DEFS if tool["name"] != "relic_validate"]
MEMORY_TOOL_NAMES = {tool["name"] for tool in MEMORY_TOOLS}
TOOL_DEFS.extend(MEMORY_TOOLS)


def _headers(event):
    return {str(k).lower(): str(v) for k, v in (event.get("headers") or {}).items()}


def _mcp_public_origin():
    return os.environ.get(
        "MCP_PUBLIC_ORIGIN",
        os.environ.get("FRONTEND_ORIGIN", "https://relicgamemaster.com"),
    ).rstrip("/")


def _response(status, body=None, protocol=None):
    headers = {
        "cache-control": "no-store",
        "content-type": "application/json",
        "access-control-allow-origin": os.environ.get("FRONTEND_ORIGIN", "https://relicgamemaster.com"),
        "access-control-allow-headers": "content-type,accept,mcp-protocol-version,mcp-method,mcp-name,mcp-session-id",
        "access-control-allow-methods": "POST,OPTIONS",
    }
    if protocol:
        headers["mcp-protocol-version"] = protocol
    return {
        "statusCode": status,
        "headers": headers,
        "body": "" if body is None else json.dumps(body, separators=(",", ":"), ensure_ascii=False),
    }


def _jsonrpc_result(request_id, result, modern=False):
    payload = dict(result)
    if modern:
        payload.setdefault("resultType", "complete")
    return {"jsonrpc": "2.0", "id": request_id, "result": payload}


def _jsonrpc_error(request_id, code, message, data=None):
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _modern_meta(req):
    params = req.get("params") or {}
    meta = params.get("_meta") or {}
    version = str(meta.get("io.modelcontextprotocol/protocolVersion") or "")
    return version == MODERN_PROTOCOL


def _validate_modern_headers(event, req):
    headers = _headers(event)
    if headers.get("mcp-protocol-version") != MODERN_PROTOCOL:
        return "MCP-Protocol-Version header must match modern request"
    method = str(req.get("method") or "")
    if headers.get("mcp-method") != method:
        return "Mcp-Method header does not match JSON-RPC method"
    if method in {"tools/call", "prompts/get", "resources/read"}:
        params = req.get("params") or {}
        expected = str(params.get("name") or params.get("uri") or "")
        if headers.get("mcp-name") != expected:
            return "Mcp-Name header does not match JSON-RPC request"
    return None


def _selected_principles(section=None):
    principles = CANON["principles"]
    if not section or section == "all":
        return principles
    return [p for p in principles if p["section"] == section]


def _context(args):
    subject = str(args.get("subject") or "").strip()
    if not subject:
        raise ValueError("subject is required")
    domain = str(args.get("truthDomain") or "UNKNOWN")
    if domain not in ALLOWED_DOMAINS:
        raise ValueError("truthDomain is invalid")
    known = [str(x).strip() for x in (args.get("knownIdentities") or []) if str(x).strip()]
    return {
        "canonVersion": CANON_VERSION,
        "mode": CANON["pluginBoundary"]["defaultMode"],
        "subject": subject,
        "intent": str(args.get("intent") or "").strip(),
        "declaredTruthDomain": domain,
        "truthDomainDefinition": CANON["truthDomains"][domain],
        "knownIdentities": known,
        "identityInstruction": "Reuse a stable identity when one is known; a label, pixel, prose description, filename, or other representation is not the identity itself.",
        "lifecycle": CANON["lifecycle"],
        "governingPrinciples": CANON["principles"],
        "authorityBoundary": CANON["pluginBoundary"],
        "provenance": CANON["sources"],
        "continuity": {
            "authoritativeStateConnected": False,
            "meaning": "This initial plugin grounds canon but does not yet expose authoritative world/user state. Treat absent state as UNKNOWN rather than reconstructing it from memory."
        }
    }


def _validate(args):
    statements = args.get("statements") or []
    if not isinstance(statements, list) or not statements:
        raise ValueError("statements must contain at least one item")
    findings = []
    normalized = []
    for index, item in enumerate(statements):
        if not isinstance(item, dict):
            raise ValueError(f"statement {index} must be an object")
        text = str(item.get("text") or "").strip()
        domain = str(item.get("truthDomain") or "").strip()
        if not text or domain not in ALLOWED_DOMAINS:
            raise ValueError(f"statement {index} is missing valid text or truthDomain")
        provenance = [str(x).strip() for x in (item.get("provenance") or []) if str(x).strip()]
        identity_basis = str(item.get("identityBasis") or "not-applicable")
        canon_status = str(item.get("canonStatus") or "unknown")
        item_findings = []
        if domain == "FACT" and not provenance:
            item_findings.append({"code": "FACT_WITHOUT_PROVENANCE", "severity": "block", "message": "FACT requires provenance appropriate to its scope."})
        if identity_basis == "representation":
            item_findings.append({"code": "REPRESENTATION_USED_AS_IDENTITY", "severity": "block", "message": "Representation cannot establish persistent identity."})
        if canon_status == "canon" and not provenance:
            item_findings.append({"code": "CANON_WITHOUT_AUTHORITY_SOURCE", "severity": "block", "message": "Canon status requires an authoritative provenance reference."})
        if canon_status == "generated" and domain == "FACT":
            item_findings.append({"code": "GENERATED_FACT_NEEDS_EXTERNAL_EVIDENCE", "severity": "block", "message": "Generated content cannot establish FACT by itself."})
        if domain in {"HYPOTHESIS", "FICTION", "UNKNOWN"} and canon_status == "canon":
            item_findings.append({"code": "TRUTH_DOMAIN_CANON_CONFLICT", "severity": "block", "message": f"{domain} cannot be silently promoted to canon."})
        normalized.append({
            "index": index,
            "text": text,
            "truthDomain": domain,
            "provenance": provenance,
            "identityBasis": identity_basis,
            "canonStatus": canon_status,
            "findings": item_findings,
        })
        findings.extend({"statement": index, **f} for f in item_findings)

    proposed_action = str(args.get("proposedAction") or "").strip()
    authority_basis = str(args.get("authorityBasis") or "not-applicable")
    if proposed_action and authority_basis != "explicit-capability":
        findings.append({
            "statement": None,
            "code": "ACTION_WITHOUT_EXPLICIT_CAPABILITY",
            "severity": "block",
            "message": "A proposed state-changing action requires an explicit capability; authentication alone is insufficient."
        })

    return {
        "canonVersion": CANON_VERSION,
        "valid": not any(f["severity"] == "block" for f in findings),
        "decisionScope": "structural-canon-boundary-only",
        "doesNotEstablish": ["factual truth beyond supplied evidence", "semantic identity equality", "permission not represented by an explicit capability", "canon promotion"],
        "statements": normalized,
        "proposedAction": proposed_action,
        "authorityBasis": authority_basis,
        "findings": findings,
        "authorityBoundary": CANON["pluginBoundary"],
    }


def _canon(args):
    section = str(args.get("section") or "all")
    if section == "all":
        return CANON
    if section == "lifecycle":
        return {"version": CANON_VERSION, "lifecycle": CANON["lifecycle"]}
    if section == "sources":
        return {"version": CANON_VERSION, "sources": CANON["sources"]}
    if section == "truth":
        return {"version": CANON_VERSION, "truthDomains": CANON["truthDomains"], "principles": _selected_principles("truth")}
    return {"version": CANON_VERSION, "section": section, "principles": _selected_principles(section)}


def _health():
    return {
        "ok": True,
        "server": SERVER_NAME,
        "serverVersion": SERVER_VERSION,
        "canonVersion": CANON_VERSION,
        "supportedProtocolVersions": SUPPORTED_PROTOCOLS,
        "mode": CANON["pluginBoundary"]["defaultMode"],
        "authoritativeWritesExposed": False,
        "publicCanonReadOnly": True,
        "privateMemoryWritesExposed": any(not tool.get("annotations", {}).get("readOnlyHint", False) for tool in MEMORY_TOOLS),
        "privateMemoryIsAuthoritativeWorldTruth": False,
    }


def _tool_result(data, is_error=False):
    text = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    return {"content": [{"type": "text", "text": text}], "structuredContent": data, "isError": is_error}


def _call_tool(name, args):
    if name == "relic_context":
        return _tool_result(_context(args))
    if name == "relic_validate":
        return _tool_result(_validate(args))
    if name == "relic_canon":
        return _tool_result(_canon(args))
    if name == "relic_health":
        return _tool_result(_health())
    raise KeyError(name)


def _auth_context(event):
    table_name = os.environ.get("MCP_AUTH_TABLE", "").strip()
    memory_table = os.environ.get("MCP_MEMORY_TABLE", "").strip()
    if not table_name or not memory_table:
        return None
    header = _headers(event).get("authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    token = header.split(" ", 1)[1].strip()
    if not token:
        return None
    import boto3
    table = boto3.resource("dynamodb").Table(table_name)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    item = table.get_item(Key={"pk": "ACCESS#" + digest, "sk": "TOKEN"}, ConsistentRead=True).get("Item")
    if not item or int(item.get("expiresAt", 0)) <= int(time.time()):
        return None
    expected_resource = _mcp_public_origin() + "/mcp"
    if str(item.get("resource") or "").rstrip("/") != expected_resource:
        return None
    return {
        "userId": str(item["userId"]),
        "username": str(item.get("username") or "ReLiC user"),
        "scopes": set(str(x) for x in (item.get("scopes") or [])),
    }


def _required_scopes(name):
    if name in {"relic_remember", "relic_relate", "relic_instantiate", "relic_transition"}:
        return {"relic.read", "relic.write"}
    if name in MEMORY_TOOL_NAMES:
        return {"relic.read"}
    return set()


def _auth_challenge(required):
    scope = " ".join(sorted(required or {"relic.read"}))
    origin = _mcp_public_origin()
    challenge = (
        f'Bearer resource_metadata="{origin}/.well-known/oauth-protected-resource", '
        f'error="insufficient_scope", error_description="Connect your ReLiC account to continue", scope="{scope}"'
    )
    return {
        "content": [{"type": "text", "text": "Connect your ReLiC account to use private persistent memory."}],
        "_meta": {"mcp/www_authenticate": [challenge]},
        "isError": True,
    }


def _call_memory_tool(event, name, args):
    actor = _auth_context(event)
    required = _required_scopes(name)
    if not actor or not required.issubset(actor["scopes"]):
        return _auth_challenge(required)
    import boto3
    from relic_mcp_protocol import call_tool as call_memory_tool
    from relic_mcp_store import DynamoRelicStore
    table = boto3.resource("dynamodb").Table(os.environ["MCP_MEMORY_TABLE"])
    store = DynamoRelicStore(table, actor["userId"], actor["username"])
    return _tool_result(call_memory_tool(name, args, store))


def _audit(event, method, tool=None, ok=True):
    record = {
        "event": "relic.mcp",
        "at": int(time.time()),
        "requestId": ((event.get("requestContext") or {}).get("requestId")),
        "method": method,
        "tool": tool,
        "ok": ok,
        "canonVersion": CANON_VERSION,
    }
    print(json.dumps(record, separators=(",", ":")))


def handler(event, context):
    method_http = ((event.get("requestContext") or {}).get("http") or {}).get("method", "POST")
    if method_http == "OPTIONS":
        return _response(204)
    if method_http != "POST":
        return _response(405, {"error": "ReLiC MCP accepts POST requests only"})

    try:
        req = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, _jsonrpc_error(None, -32700, "Parse error"))

    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or not req.get("method"):
        return _response(400, _jsonrpc_error(req.get("id") if isinstance(req, dict) else None, -32600, "Invalid Request"))

    rpc_method = str(req["method"])
    request_id = req.get("id")
    modern = _modern_meta(req)
    protocol = MODERN_PROTOCOL if modern else _headers(event).get("mcp-protocol-version", LEGACY_PROTOCOL)

    if modern:
        mismatch = _validate_modern_headers(event, req)
        if mismatch:
            _audit(event, rpc_method, ok=False)
            return _response(400, _jsonrpc_error(request_id, -32020, mismatch), MODERN_PROTOCOL)

    if rpc_method.startswith("notifications/"):
        _audit(event, rpc_method)
        return _response(202, None, protocol)

    try:
        if rpc_method == "server/discover":
            result = {
                "supportedVersions": [MODERN_PROTOCOL, LEGACY_PROTOCOL],
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": INSTRUCTIONS,
                "ttlMs": 300000,
                "cacheScope": "public",
            }
            _audit(event, rpc_method)
            return _response(200, _jsonrpc_result(request_id, result, modern=True), MODERN_PROTOCOL)

        if rpc_method == "initialize":
            requested = str((req.get("params") or {}).get("protocolVersion") or LEGACY_PROTOCOL)
            selected = requested if requested in SUPPORTED_PROTOCOLS and requested != MODERN_PROTOCOL else LEGACY_PROTOCOL
            result = {
                "protocolVersion": selected,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": INSTRUCTIONS,
            }
            _audit(event, rpc_method)
            return _response(200, _jsonrpc_result(request_id, result), selected)

        if rpc_method == "ping":
            _audit(event, rpc_method)
            return _response(200, _jsonrpc_result(request_id, {}, modern=modern), protocol)

        if rpc_method == "tools/list":
            _audit(event, rpc_method)
            return _response(200, _jsonrpc_result(request_id, {"tools": TOOL_DEFS}, modern=modern), protocol)

        if rpc_method == "tools/call":
            params = req.get("params") or {}
            name = str(params.get("name") or "")
            args = params.get("arguments") or {}
            if not isinstance(args, dict):
                raise ValueError("tool arguments must be an object")
            try:
                if name in MEMORY_TOOL_NAMES:
                    result = _call_memory_tool(event, name, args)
                else:
                    result = _call_tool(name, args)
            except KeyError:
                _audit(event, rpc_method, name, ok=False)
                return _response(200, _jsonrpc_error(request_id, -32602, f"Unknown tool: {name}"), protocol)
            except ValueError as exc:
                result = _tool_result({"error": str(exc), "canonVersion": CANON_VERSION}, is_error=True)
            _audit(event, rpc_method, name, ok=not result.get("isError", False))
            return _response(200, _jsonrpc_result(request_id, result, modern=modern), protocol)

        _audit(event, rpc_method, ok=False)
        return _response(200, _jsonrpc_error(request_id, -32601, "Method not found"), protocol)
    except Exception as exc:
        _audit(event, rpc_method, ok=False)
        return _response(500, _jsonrpc_error(request_id, -32603, "Internal error", {"type": type(exc).__name__}), protocol)
