import base64
import hashlib
import html
import json
import os
import secrets
import time
import urllib.parse
import uuid

import boto3

ddb = boto3.resource("dynamodb")
oauth = ddb.Table(os.environ["MCP_AUTH_TABLE"])
identity = ddb.Table(os.environ["IDENTITY_TABLE"])

PUBLIC_ORIGIN = os.environ.get("PUBLIC_ORIGIN", "https://relicgamemaster.com").rstrip("/")
RESOURCE_ID = PUBLIC_ORIGIN + "/mcp"
AUTH_ISSUER = PUBLIC_ORIGIN
DISCORD_AUTH_API = os.environ["DISCORD_AUTH_API"].rstrip("/")
ACCESS_SECONDS = 8 * 3600
REFRESH_SECONDS = 30 * 24 * 3600
SCOPES = ("relic.read", "relic.write")


def now():
    return int(time.time())


def json_response(status, body, headers=None):
    base = {
        "cache-control": "no-store",
        "content-type": "application/json; charset=utf-8",
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET,POST,OPTIONS",
        "access-control-allow-headers": "authorization,content-type,mcp-protocol-version,mcp-method,mcp-name",
    }
    if headers:
        base.update(headers)
    return {"statusCode": status, "headers": base, "body": json.dumps(body, separators=(",", ":"))}


def html_response(status, body):
    return {
        "statusCode": status,
        "headers": {"cache-control": "no-store", "content-type": "text/html; charset=utf-8"},
        "body": body,
    }


def redirect(location):
    return {
        "statusCode": 302,
        "headers": {"cache-control": "no-store", "location": location, "content-type": "text/plain; charset=utf-8"},
        "body": "",
    }


def parse_json(event):
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw)


def parse_form(event):
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    parsed = urllib.parse.parse_qs(raw, keep_blank_values=True)
    return {k: v[-1] if v else "" for k, v in parsed.items()}


def safe_https_url(value, label):
    value = str(value or "").strip()
    try:
        parsed = urllib.parse.urlsplit(value)
    except Exception as exc:
        raise ValueError(f"Invalid {label}") from exc
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError(f"Invalid {label}")
    return value


def normalize_scopes(raw):
    if isinstance(raw, list):
        requested = [str(x) for x in raw]
    else:
        requested = [x for x in str(raw or "").split() if x]
    unknown = [x for x in requested if x not in SCOPES]
    if unknown:
        raise ValueError("Unsupported scope: " + ",".join(unknown))
    return sorted(set(requested))


def client_key(client_id):
    return {"pk": "CLIENT#" + client_id, "sk": "PROFILE"}


def get_client(client_id):
    return oauth.get_item(Key=client_key(str(client_id or "")), ConsistentRead=True).get("Item")


def metadata():
    return {
        "issuer": AUTH_ISSUER,
        "authorization_endpoint": PUBLIC_ORIGIN + "/oauth/authorize",
        "token_endpoint": PUBLIC_ORIGIN + "/oauth/token",
        "registration_endpoint": PUBLIC_ORIGIN + "/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": list(SCOPES),
        "resource_parameter_supported": True,
        "authorization_response_iss_parameter_supported": True,
    }


def protected_resource():
    return {
        "resource": RESOURCE_ID,
        "authorization_servers": [AUTH_ISSUER],
        "scopes_supported": list(SCOPES),
        "resource_documentation": PUBLIC_ORIGIN + "/.well-known/relic-mcp.json",
    }


def register_client(event):
    body = parse_json(event)
    uris = body.get("redirect_uris") or []
    if not isinstance(uris, list) or not uris or len(uris) > 10:
        raise ValueError("redirect_uris must be a non-empty array")
    redirect_uris = [safe_https_url(uri, "redirect_uri") for uri in uris]
    auth_method = str(body.get("token_endpoint_auth_method") or "none")
    if auth_method != "none":
        raise ValueError("Only token_endpoint_auth_method=none is supported")
    grant_types = body.get("grant_types") or ["authorization_code", "refresh_token"]
    if any(x not in ("authorization_code", "refresh_token") for x in grant_types):
        raise ValueError("Unsupported grant type")
    response_types = body.get("response_types") or ["code"]
    if response_types != ["code"] and "code" not in response_types:
        raise ValueError("Only response_type=code is supported")
    client_id = "relic-client-" + str(uuid.uuid4())
    created = now()
    item = {
        **client_key(client_id),
        "clientId": client_id,
        "clientName": str(body.get("client_name") or "MCP client").strip()[:160],
        "redirectUris": redirect_uris,
        "tokenEndpointAuthMethod": "none",
        "grantTypes": ["authorization_code", "refresh_token"],
        "responseTypes": ["code"],
        "createdAt": created,
    }
    oauth.put_item(Item=item, ConditionExpression="attribute_not_exists(pk)")
    return json_response(201, {
        "client_id": client_id,
        "client_id_issued_at": created,
        "client_name": item["clientName"],
        "redirect_uris": redirect_uris,
        "token_endpoint_auth_method": "none",
        "grant_types": item["grantTypes"],
        "response_types": item["responseTypes"],
    })


def authorize(event):
    q = event.get("queryStringParameters") or {}
    if q.get("response_type") != "code":
        raise ValueError("response_type=code required")
    client_id = str(q.get("client_id") or "")
    client = get_client(client_id)
    if not client:
        raise ValueError("Unknown client_id")
    redirect_uri = safe_https_url(q.get("redirect_uri"), "redirect_uri")
    if redirect_uri not in client.get("redirectUris", []):
        raise ValueError("redirect_uri is not registered")
    if q.get("code_challenge_method") != "S256":
        raise ValueError("PKCE S256 required")
    challenge = str(q.get("code_challenge") or "").strip()
    if len(challenge) < 43 or len(challenge) > 128:
        raise ValueError("Invalid code_challenge")
    resource = str(q.get("resource") or RESOURCE_ID).rstrip("/")
    if resource != RESOURCE_ID:
        raise ValueError("Invalid resource")
    scopes = normalize_scopes(q.get("scope") or "relic.read")
    if not scopes:
        scopes = ["relic.read"]
    request_token = secrets.token_urlsafe(32)
    created = now()
    oauth.put_item(Item={
        "pk": "AUTHREQ#" + request_token,
        "sk": "REQUEST",
        "requestToken": request_token,
        "clientId": client_id,
        "clientName": client.get("clientName", "MCP client"),
        "redirectUri": redirect_uri,
        "clientState": str(q.get("state") or ""),
        "codeChallenge": challenge,
        "resource": RESOURCE_ID,
        "scopes": scopes,
        "createdAt": created,
        "expiresAt": created + 600,
        "ttl": created + 600,
    }, ConditionExpression="attribute_not_exists(pk)")
    return redirect(DISCORD_AUTH_API + "/auth/login?" + urllib.parse.urlencode({"mcp_request": request_token}))


def _load_handoff(ticket, request_token):
    handoff_key = {"pk": "mcphandoff#" + str(ticket or "")}
    handoff = identity.get_item(Key=handoff_key, ConsistentRead=True).get("Item")
    req_key = {"pk": "AUTHREQ#" + str(request_token or ""), "sk": "REQUEST"}
    request = oauth.get_item(Key=req_key, ConsistentRead=True).get("Item")
    if not handoff or not request:
        raise ValueError("Login handoff is invalid or expired")
    current = now()
    if int(handoff.get("expiresAt", 0)) <= current or int(request.get("expiresAt", 0)) <= current:
        raise ValueError("Login handoff is invalid or expired")
    if str(handoff.get("mcpRequestToken") or "") != str(request_token or ""):
        raise ValueError("Login handoff does not match authorization request")
    return handoff_key, handoff, req_key, request


def identity_consent_get(event):
    q = event.get("queryStringParameters") or {}
    ticket = str(q.get("ticket") or "")
    request_token = str(q.get("request") or "")
    _, handoff, _, request = _load_handoff(ticket, request_token)
    client_name = html.escape(str(request.get("clientName") or "MCP client"))
    username = html.escape(str(handoff.get("username") or "ReLiC user"))
    scopes = ", ".join(html.escape(x) for x in request.get("scopes", []))
    action = PUBLIC_ORIGIN + "/oauth/identity"
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Connect ReLiC</title><style>
body{{font-family:system-ui,sans-serif;background:#0e1014;color:#f4f6fa;margin:0;padding:32px}}
main{{max-width:620px;margin:auto;background:#171b22;border:1px solid #303743;border-radius:18px;padding:26px}}
button{{font:inherit;padding:12px 18px;margin-right:10px;border-radius:10px;border:0;cursor:pointer}}
.allow{{font-weight:700}} .deny{{background:#303743;color:#fff}} code{{word-break:break-word}}
</style></head><body><main><h1>Connect ReLiC</h1>
<p><strong>{client_name}</strong> is requesting access as <strong>{username}</strong>.</p>
<p>Scopes: <code>{scopes}</code></p>
<p>ReLiC keeps persistent identities, relationships, provenance and state. It does not automatically change Shaelvien world truth or canon.</p>
<form method="post" action="{html.escape(action)}">
<input type="hidden" name="ticket" value="{html.escape(ticket)}">
<input type="hidden" name="request" value="{html.escape(request_token)}">
<button class="allow" type="submit" name="decision" value="allow">Allow</button>
<button class="deny" type="submit" name="decision" value="deny">Deny</button>
</form></main></body></html>"""
    return html_response(200, page)


def identity_consent_post(event):
    form = parse_form(event)
    ticket = str(form.get("ticket") or "")
    request_token = str(form.get("request") or "")
    handoff_key, handoff, req_key, request = _load_handoff(ticket, request_token)
    identity.delete_item(Key=handoff_key)
    oauth.delete_item(Key=req_key)
    params = {"iss": AUTH_ISSUER}
    if str(form.get("decision") or "") != "allow":
        params["error"] = "access_denied"
        params["error_description"] = "The user denied ReLiC access."
    else:
        code = secrets.token_urlsafe(40)
        code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
        created = now()
        oauth.put_item(Item={
            "pk": "CODE#" + code_hash,
            "sk": "CODE",
            "userId": str(handoff["userId"]),
            "username": str(handoff.get("username") or "ReLiC user"),
            "clientId": request["clientId"],
            "redirectUri": request["redirectUri"],
            "codeChallenge": request["codeChallenge"],
            "resource": request["resource"],
            "scopes": request.get("scopes", ["relic.read"]),
            "createdAt": created,
            "expiresAt": created + 300,
            "ttl": created + 300,
        }, ConditionExpression="attribute_not_exists(pk)")
        params["code"] = code
    if request.get("clientState"):
        params["state"] = request["clientState"]
    separator = "&" if "?" in request["redirectUri"] else "?"
    return redirect(request["redirectUri"] + separator + urllib.parse.urlencode(params))


def _pkce_s256(verifier):
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _issue_tokens(user_id, username, client_id, scopes, resource):
    current = now()
    access = secrets.token_urlsafe(48)
    refresh = secrets.token_urlsafe(56)
    access_hash = hashlib.sha256(access.encode("utf-8")).hexdigest()
    refresh_hash = hashlib.sha256(refresh.encode("utf-8")).hexdigest()
    oauth.put_item(Item={
        "pk": "ACCESS#" + access_hash,
        "sk": "TOKEN",
        "userId": user_id,
        "username": username,
        "clientId": client_id,
        "scopes": scopes,
        "resource": resource,
        "issuedAt": current,
        "expiresAt": current + ACCESS_SECONDS,
        "ttl": current + ACCESS_SECONDS,
    })
    oauth.put_item(Item={
        "pk": "REFRESH#" + refresh_hash,
        "sk": "TOKEN",
        "userId": user_id,
        "username": username,
        "clientId": client_id,
        "scopes": scopes,
        "resource": resource,
        "issuedAt": current,
        "expiresAt": current + REFRESH_SECONDS,
        "ttl": current + REFRESH_SECONDS,
    })
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": ACCESS_SECONDS,
        "refresh_token": refresh,
        "scope": " ".join(scopes),
    }


def token(event):
    form = parse_form(event)
    grant_type = form.get("grant_type")
    client_id = str(form.get("client_id") or "")
    if not get_client(client_id):
        return json_response(400, {"error": "invalid_client"})
    if grant_type == "authorization_code":
        code = str(form.get("code") or "")
        key = {"pk": "CODE#" + hashlib.sha256(code.encode("utf-8")).hexdigest(), "sk": "CODE"}
        item = oauth.get_item(Key=key, ConsistentRead=True).get("Item")
        if not item or int(item.get("expiresAt", 0)) <= now():
            return json_response(400, {"error": "invalid_grant"})
        if item.get("clientId") != client_id or item.get("redirectUri") != form.get("redirect_uri"):
            return json_response(400, {"error": "invalid_grant"})
        if str(form.get("resource") or RESOURCE_ID).rstrip("/") != RESOURCE_ID:
            return json_response(400, {"error": "invalid_target"})
        verifier = str(form.get("code_verifier") or "")
        if not verifier or not secrets.compare_digest(_pkce_s256(verifier), str(item.get("codeChallenge") or "")):
            return json_response(400, {"error": "invalid_grant"})
        oauth.delete_item(Key=key)
        return json_response(200, _issue_tokens(
            str(item["userId"]), str(item.get("username") or "ReLiC user"),
            client_id, list(item.get("scopes") or ["relic.read"]), RESOURCE_ID
        ))
    if grant_type == "refresh_token":
        refresh = str(form.get("refresh_token") or "")
        key = {"pk": "REFRESH#" + hashlib.sha256(refresh.encode("utf-8")).hexdigest(), "sk": "TOKEN"}
        item = oauth.get_item(Key=key, ConsistentRead=True).get("Item")
        if not item or int(item.get("expiresAt", 0)) <= now() or item.get("clientId") != client_id:
            return json_response(400, {"error": "invalid_grant"})
        requested = normalize_scopes(form.get("scope") or item.get("scopes") or [])
        original = set(item.get("scopes") or [])
        if not set(requested).issubset(original):
            return json_response(400, {"error": "invalid_scope"})
        oauth.delete_item(Key=key)
        return json_response(200, _issue_tokens(
            str(item["userId"]), str(item.get("username") or "ReLiC user"),
            client_id, requested, RESOURCE_ID
        ))
    return json_response(400, {"error": "unsupported_grant_type"})


def handler(event, context):
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]
    if method == "OPTIONS":
        return json_response(204, {})
    try:
        if method == "GET" and path in (
            "/.well-known/oauth-authorization-server",
            "/.well-known/openid-configuration",
        ):
            return json_response(200, metadata())
        if method == "GET" and path in (
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp",
        ):
            return json_response(200, protected_resource())
        if method == "POST" and path == "/oauth/register":
            return register_client(event)
        if method == "GET" and path == "/oauth/authorize":
            return authorize(event)
        if path == "/oauth/identity" and method == "GET":
            return identity_consent_get(event)
        if path == "/oauth/identity" and method == "POST":
            return identity_consent_post(event)
        if method == "POST" and path == "/oauth/token":
            return token(event)
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        return json_response(400, {"error": "invalid_request", "error_description": str(exc)})
    return json_response(404, {"error": "not_found"})
