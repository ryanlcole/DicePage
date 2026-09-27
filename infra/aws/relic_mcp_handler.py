import base64
import hashlib
import json
import os
import time

import boto3

from relic_mcp_protocol import MODERN_PROTOCOL, TOOL_MAP, dispatch
from relic_mcp_store import DynamoRelicStore

ddb = boto3.resource("dynamodb")
memory = ddb.Table(os.environ["MCP_MEMORY_TABLE"])
auth = ddb.Table(os.environ["MCP_AUTH_TABLE"])

PUBLIC_ORIGIN = os.environ.get("PUBLIC_ORIGIN", "https://relicgamemaster.com").rstrip("/")
RESOURCE_ID = PUBLIC_ORIGIN + "/mcp"
RESOURCE_METADATA = PUBLIC_ORIGIN + "/.well-known/oauth-protected-resource"

READ_TOOLS = {
    "relic_profile", "relic_identify", "relic_context", "relic_observe",
    "relic_trace", "relic_translate", "relic_validate", "relic_imagine",
}
WRITE_TOOLS = {"relic_remember", "relic_relate", "relic_instantiate", "relic_transition"}


def _headers(event):
    return {str(k).lower(): str(v) for k, v in (event.get("headers") or {}).items()}


def _json_response(status, body=None, extra_headers=None):
    headers = {
        "cache-control": "no-store",
        "content-type": "application/json; charset=utf-8",
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET,POST,OPTIONS",
        "access-control-allow-headers": (
            "authorization,content-type,accept,mcp-session-id,mcp-protocol-version,"
            "mcp-method,mcp-name"
        ),
        "access-control-expose-headers": "Mcp-Session-Id",
    }
    if extra_headers:
        headers.update(extra_headers)
    return {
        "statusCode": status,
        "headers": headers,
        "body": "" if body is None else json.dumps(body, separators=(",", ":"), default=str),
    }


def _parse_body(event):
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw or "{}")


def _auth_context(event):
    headers = _headers(event)
    value = headers.get("authorization", "")
    if not value.lower().startswith("bearer "):
        return None
    token = value.split(" ", 1)[1].strip()
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    item = auth.get_item(
        Key={"pk": "ACCESS#" + digest, "sk": "TOKEN"},
        ConsistentRead=True,
    ).get("Item")
    if not item or int(item.get("expiresAt", 0)) <= int(time.time()):
        return None
    if str(item.get("resource") or "").rstrip("/") != RESOURCE_ID:
        return None
    return {
        "userId": str(item["userId"]),
        "username": str(item.get("username") or "ReLiC user"),
        "scopes": set(str(x) for x in (item.get("scopes") or [])),
    }


def _required_scopes(tool_name):
    if tool_name in WRITE_TOOLS:
        return {"relic.read", "relic.write"}
    if tool_name in READ_TOOLS:
        return {"relic.read"}
    return set()


def _challenge(req, required):
    scope = " ".join(sorted(required or {"relic.read"}))
    challenge = (
        f'Bearer resource_metadata="{RESOURCE_METADATA}",'
        f' error="insufficient_scope",'
        f' error_description="Connect your ReLiC account to continue",'
        f' scope="{scope}"'
    )
    modern = req.get("method") == "server/discover" or (
        ((req.get("params") or {}).get("_meta") or {}).get(
            "io.modelcontextprotocol/protocolVersion"
        ) == MODERN_PROTOCOL
    )
    result = {
        "content": [{
            "type": "text",
            "text": "Authentication required. Connect your ReLiC account to use private persistent memory.",
        }],
        "_meta": {"mcp/www_authenticate": [challenge]},
        "isError": True,
    }
    if modern:
        result["resultType"] = "complete"
        result.setdefault("_meta", {})["io.modelcontextprotocol/serverInfo"] = {
            "name": "relic", "version": "0.1.0"
        }
    return {"jsonrpc": "2.0", "id": req.get("id"), "result": result}


def _validate_modern_headers(event, req):
    params = req.get("params") or {}
    meta = params.get("_meta") or {}
    modern = meta.get("io.modelcontextprotocol/protocolVersion") == MODERN_PROTOCOL
    if not modern and req.get("method") != "server/discover":
        return None
    headers = _headers(event)
    version = headers.get("mcp-protocol-version")
    method = headers.get("mcp-method")
    if version and version != MODERN_PROTOCOL:
        return {"code": -32022, "message": "Unsupported protocol version"}
    if method and method != req.get("method"):
        return {"code": -32020, "message": "Mcp-Method header does not match JSON-RPC method"}
    if req.get("method") in {"tools/call", "resources/read", "prompts/get"}:
        expected = str(params.get("name") or params.get("uri") or "")
        header_name = headers.get("mcp-name")
        if header_name and expected and header_name != expected:
            return {"code": -32020, "message": "Mcp-Name header does not match request"}
    return None


def handler(event, context):
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]

    if method == "OPTIONS":
        return _json_response(204)

    if path != "/mcp":
        return _json_response(404, {"error": "not_found"})

    if method == "GET":
        return _json_response(200, {
            "name": "ReLiC MCP",
            "endpoint": RESOURCE_ID,
            "protocols": [MODERN_PROTOCOL, "2025-11-25"],
            "authentication": "OAuth 2.1",
        })

    if method != "POST":
        return _json_response(405, {"error": "method_not_allowed"}, {"allow": "GET,POST,OPTIONS"})

    try:
        req = _parse_body(event)
    except Exception:
        return _json_response(400, {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Parse error"},
        })

    mismatch = _validate_modern_headers(event, req)
    if mismatch:
        return _json_response(400, {
            "jsonrpc": "2.0",
            "id": req.get("id"),
            "error": mismatch,
        })

    if req.get("method") == "tools/call":
        params = req.get("params") or {}
        tool_name = str(params.get("name") or "")
        if tool_name not in TOOL_MAP:
            result = dispatch(req, None, None)
            return _json_response(200, result)
        required = _required_scopes(tool_name)
        actor = _auth_context(event)
        if not actor or not required.issubset(actor["scopes"]):
            return _json_response(200, _challenge(req, required))
        store = DynamoRelicStore(memory, actor["userId"], actor["username"])
        result = dispatch(req, store, actor["userId"])
        return _json_response(200 if result is not None else 202, result)

    result = dispatch(req, None, None)
    if result is None:
        return _json_response(202)
    return _json_response(200, result)
