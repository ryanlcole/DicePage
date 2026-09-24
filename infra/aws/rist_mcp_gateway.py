import html
import json
from typing import Any

import rist_external_ai_gateway as gateway


SERVER_NAME = "ReLiCGameMaster MCP"
SERVER_VERSION = "0.1.0"
LEGACY_PROTOCOL_VERSION = "2025-11-25"

LAW_TITLES = [
    "Shaelvien — Tome of Divination — Book I: The Laws of Perception and Knowledge",
    "Shaelvien — Tome of Necromancy — Book I: The Laws of Life, Harm, and Protection",
    "Shaelvien — Tome of Enchantment — Book I: The Laws of Influence and Conduct",
    "Shaelvien — Tome of Transmutation — Book I: The Laws of RIST Play",
    "Shaelvien — Tome of Abjuration — Book I: The Laws of Boundaries and Legality",
    "Shaelvien — Tome of Conjuration — Book I: The Laws of Worldbuilding",
    "Shaelvien — Tome of Evocation — Book I: The Laws of Action and Consequence",
    "Shaelvien — Tome of Aevumancy and Chronos — Book I: The Laws of Time",
    "Shaelvien — Tome of Terrain — Book I: The Laws of Ground and Environment",
]

MEMORANDA = [
    {
        "name": "Identity and Representation",
        "summary": "Identity persists independently of the current visual or textual representation. Representation is not truth, and equivalent output does not imply equivalent identity.",
    },
    {
        "name": "Recursive Authority and Supervision",
        "summary": "Authority is scoped to objects and containment, inherited only where defined, and constrained by explicit ownership, delegation, supervision, and server-side permission checks.",
    },
    {
        "name": "Provenance Boundary",
        "summary": "Human, outside-AI, and ReLiC/EIOS-originated material retain provenance. AI-originated work must not be silently presented as human-originated canon.",
    },
    {
        "name": "ReLiC Observer Boundary",
        "summary": "ReLiC observes and reports state; observation alone is not permission to rewrite canonical state.",
    },
]

ABOUT_TEXT = """ReLiCGameMaster is building Shaelvien and RIST (Recursive Immersive Sandbox Table Top): a persistent tabletop environment for players, GameMasters, roleplayers, narrators, artists, worldbuilders, developers, maps, cards, dice, miniatures, tokens, animated sprites, tactical encounters, recursive spaces, and replayable world state.

This MCP endpoint is an experimental machine-facing entrance for external AI testers. It starts with governance, then explains the project, then exposes bounded registration and application tools. Access remains deny-by-default and server-authoritative."""

REGULATION_TEXT = """External-AI intake is governed by the current ReLiC/RIST AI Participation, Canon, Resource, Content & Commerce Access Policy. Important enforced boundaries include: visible AINPC identity; verifiable provenance; player-content non-interference; human-priority resource yielding; one external-AI slot per ten connected humans; all-audiences content by default; bounded sessions; bounded worldbuilding allocation; no automatic canon promotion; least privilege; and immediate suspension/revocation when required. Payment or a test token does not purchase authority."""

APPLICATION_TEXT = """Application order:
1. Read relic://governance/laws, relic://governance/rules, relic://governance/regulations, and relic://governance/memoranda.
2. Read relic://site/about.
3. Call register_agent and retain the returned agentKey securely.
4. Call submit_application with creative/testing disciplines and evidence.
5. Call application_status to inspect the server-authoritative result.

For the initial tester intake, ReLiC compares only declared work-relevant evidence such as art, gaming, roleplaying, narration, tabletop design, worldbuilding, accessibility, testing, writing, programming, audio, and related creative practice. Protected demographic traits are neither requested nor scored. A platform-owner selection can approve the highest current eligible application and issue exactly one bounded Shaelvien test token. The token represents property-space capability under existing rules; it is not administrative authority."""

RESOURCE_DATA = {
    "relic://governance/laws": {
        "name": "Shaelvien Laws",
        "description": "Canonical law-book catalog that prospective testers should understand before applying.",
        "text": "Canonical law books currently catalogued:\n\n- " + "\n- ".join(LAW_TITLES) + "\n\nThe private authoring masters remain in ReLiC's document store until deliberately published. Machine access must not infer unpublished text.",
    },
    "relic://governance/rules": {
        "name": "AI Participation Rules",
        "description": "Machine-facing participation rules and current ruleset identity.",
        "text": "Current public policy: https://relicgamemaster.com/Game/ai-policy.json\n\nRuleset: " + gateway.AI_RULESET_VERSION + "\nPolicy: " + gateway.POLICY_VERSION + "\n\nRequired acknowledgments:\n- " + "\n- ".join(gateway.REQUIRED_RULES),
    },
    "relic://governance/regulations": {
        "name": "Operational Regulations",
        "description": "Technical and operational boundaries enforced on external AI access.",
        "text": REGULATION_TEXT,
    },
    "relic://governance/memoranda": {
        "name": "Governance Memoranda",
        "description": "Concise public summaries of the governing architectural memoranda.",
        "text": "\n\n".join(f"{item['name']}: {item['summary']}" for item in MEMORANDA),
    },
    "relic://site/about": {
        "name": "What ReLiCGameMaster Is",
        "description": "Human-readable and agent-readable explanation of Shaelvien, RIST, and the MCP testing entrance.",
        "text": ABOUT_TEXT,
    },
    "relic://applications/process": {
        "name": "Tester Application Process",
        "description": "Registration, application, selection, and single-token tester intake process.",
        "text": APPLICATION_TEXT,
    },
}


def _headers(content_type: str) -> dict[str, str]:
    return {
        "access-control-allow-origin": gateway.origin,
        "access-control-allow-headers": "authorization,content-type,mcp-protocol-version,mcp-session-id,mcp-method,mcp-name",
        "access-control-allow-methods": "GET,POST,OPTIONS",
        "cache-control": "no-store",
        "content-type": content_type,
        "x-relic-mcp-version": SERVER_VERSION,
        "x-relic-ai-policy-version": gateway.POLICY_VERSION,
        "x-relic-ai-ruleset-version": gateway.AI_RULESET_VERSION,
    }


def _http(status: int, body: str, content_type: str = "application/json") -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": _headers(content_type),
        "body": body,
    }


def _json(status: int, value: Any) -> dict[str, Any]:
    return _http(status, json.dumps(value, separators=(",", ":"), default=str), "application/json")


def _rpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return _json(200, {"jsonrpc": "2.0", "id": request_id, "result": result})


def _rpc_error(request_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return _json(200, {"jsonrpc": "2.0", "id": request_id, "error": error})


def _tool_payload(api_response: dict[str, Any]) -> dict[str, Any]:
    status = int(api_response.get("statusCode") or 500)
    raw = api_response.get("body") or "{}"
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        payload = {"raw": str(raw)}
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return {
        "content": [{"type": "text", "text": text}],
        "isError": status >= 400,
    }


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "read_governance",
            "description": "Read the required ReLiC laws, rules, regulations, and governance memoranda before registration.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "about_relic",
            "description": "Explain ReLiCGameMaster, Shaelvien, RIST, and what this MCP testing entrance is for.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "register_agent",
            "description": "Register an external AI identity after reading and explaining the current rules. Registration does not grant play or worldbuilding authority.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "provider": {"type": "string", "maxLength": 120},
                    "model": {"type": "string", "maxLength": 160},
                    "displayName": {"type": "string", "description": "Must begin with AINPC.", "maxLength": 160},
                    "rulesetVersion": {"type": "string"},
                    "acknowledgments": {"type": "array", "items": {"type": "string"}},
                    "understandingEvidence": {"type": "object", "additionalProperties": {"type": "string"}},
                    "requestedAllocation": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "minimum": 1, "maximum": 300},
                            "y": {"type": "integer", "minimum": 1, "maximum": 300},
                            "z": {"type": "integer", "minimum": 1, "maximum": 10},
                            "era": {"type": "integer", "minimum": 1, "maximum": 10},
                            "themes": {"type": "array", "maxItems": 30, "items": {"type": "string"}},
                        },
                        "required": ["x", "y", "z", "era", "themes"],
                        "additionalProperties": False,
                    },
                },
                "required": ["provider", "model", "displayName", "rulesetVersion", "acknowledgments", "understandingEvidence", "requestedAllocation"],
                "additionalProperties": False,
            },
        },
        {
            "name": "submit_application",
            "description": "Apply for the initial bounded ReLiC AI tester slot using only work-relevant creative/testing evidence.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agentId": {"type": "string"},
                    "agentKey": {"type": "string"},
                    "disciplines": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 12,
                        "items": {"type": "string"},
                        "description": "Examples: art, gaming, roleplaying, narration, worldbuilding, tabletop, accessibility, testing, writing, programming, audio.",
                    },
                    "experienceSummary": {"type": "string", "minLength": 40, "maxLength": 3000},
                    "testPlan": {"type": "string", "minLength": 40, "maxLength": 3000},
                    "portfolioUrls": {"type": "array", "maxItems": 8, "items": {"type": "string"}},
                    "requestedRoles": {"type": "array", "maxItems": 12, "items": {"type": "string"}},
                },
                "required": ["agentId", "agentKey", "disciplines", "experienceSummary", "testPlan"],
                "additionalProperties": False,
            },
        },
        {
            "name": "application_status",
            "description": "Read the server-authoritative status of this registered AI's tester application.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agentId": {"type": "string"},
                    "agentKey": {"type": "string"},
                },
                "required": ["agentId", "agentKey"],
                "additionalProperties": False,
            },
        },
    ]


def _governance_bundle() -> dict[str, Any]:
    return {
        "policyVersion": gateway.POLICY_VERSION,
        "rulesetVersion": gateway.AI_RULESET_VERSION,
        "readFirst": [
            "relic://governance/laws",
            "relic://governance/rules",
            "relic://governance/regulations",
            "relic://governance/memoranda",
        ],
        "resources": {
            uri: RESOURCE_DATA[uri]["text"]
            for uri in (
                "relic://governance/laws",
                "relic://governance/rules",
                "relic://governance/regulations",
                "relic://governance/memoranda",
            )
        },
    }


def _call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "read_governance":
        return {
            "content": [{"type": "text", "text": json.dumps(_governance_bundle(), ensure_ascii=False, indent=2)}],
            "isError": False,
        }
    if name == "about_relic":
        return {"content": [{"type": "text", "text": ABOUT_TEXT}], "isError": False}
    if name == "register_agent":
        return _tool_payload(gateway.register(arguments))
    if name == "submit_application":
        return _tool_payload(gateway.submit_application(arguments))
    if name == "application_status":
        return _tool_payload(gateway.application_status(arguments))
    return {
        "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
        "isError": True,
    }


def _human_page() -> str:
    laws = "".join(f"<li>{html.escape(title)}</li>" for title in LAW_TITLES)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ReLiC MCP | AI Tester Entrance</title>
<meta name="description" content="ReLiCGameMaster MCP entrance for governed external-AI testing, registration, and applications.">
<style>
:root{{--bg:#071117;--panel:#0d2028;--line:#31515d;--text:#f2e7ca;--muted:#aec0c4;--gold:#e0c58d;--blue:#8fc5d4}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 20% 0,#17333f 0,transparent 34rem),var(--bg);color:var(--text);font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{width:min(1050px,calc(100% - 32px));margin:auto;padding:42px 0 72px}}a{{color:var(--blue)}}.eyebrow{{color:var(--gold);letter-spacing:.14em;text-transform:uppercase;font-size:.75rem;font-weight:800}}
h1{{font:700 clamp(2.8rem,8vw,6.4rem)/.92 Georgia,serif;margin:.15em 0}}h2{{font-family:Georgia,serif;color:var(--gold)}}.lead{{max-width:72ch;color:var(--muted);font-size:1.08rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin-top:28px}}article{{border:1px solid var(--line);background:linear-gradient(180deg,rgba(16,42,52,.94),rgba(8,25,32,.94));border-radius:14px;padding:20px}}
code,pre{{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}}pre{{overflow:auto;border:1px solid var(--line);background:#041015;padding:14px;border-radius:10px;color:#d9edf2}}
.badge{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 9px;margin:3px;color:var(--muted);font-size:.8rem}}
.callout{{margin:24px 0;padding:18px;border-left:3px solid var(--gold);background:rgba(224,197,141,.07)}}ol li{{margin:.5rem 0}}footer{{color:var(--muted);margin-top:34px;font-size:.85rem}}
</style>
</head>
<body><main>
<p class="eyebrow">ReLiCGameMaster · Model Context Protocol</p>
<h1>Enter through governance.</h1>
<p class="lead">This is the machine-facing testing entrance to ReLiCGameMaster, Shaelvien, and RIST. External agents begin with the laws, rules, regulations, and memoranda; then learn what the site is; then register and apply for bounded testing access.</p>
<div class="callout"><strong>MCP endpoint:</strong> <code>https://relicgamemaster.com/mcp</code><br>
<strong>Initial transport:</strong> Streamable HTTP / JSON-RPC, compatible with the 2025-11-25 MCP lifecycle. Modern clients may negotiate by falling back to the legacy lifecycle.<br>
<strong>Current ruleset:</strong> <code>{html.escape(gateway.AI_RULESET_VERSION)}</code></div>
<section class="grid">
<article><h2>1 · Laws</h2><p>The canonical law-book catalog is presented first.</p><ul>{laws}</ul></article>
<article><h2>2 · Rules & regulations</h2><p>AI participation is deny-by-default. Identity, provenance, human-priority capacity, session limits, content boundaries, canon boundaries, and scoped authorization remain server-enforced.</p><p><a href="/Game/ai-policy.json">Read the public machine-readable AI policy</a></p></article>
<article><h2>3 · Memoranda</h2><p>Identity remains distinct from representation. Authority is recursive and scoped. Provenance persists. Observation alone is not permission to rewrite truth.</p></article>
<article><h2>4 · What ReLiC is</h2><p>Shaelvien is the game and persistent world. RIST is the recursive tabletop platform beneath it: maps, tactical play, cards, dice, miniatures, tokens, sprites, scenery, worldbuilding, roleplay, narration, replay, and persistent state.</p><p><a href="/">Open the human-facing explanation</a></p></article>
<article><h2>5 · Register & apply</h2><p>Connect with MCP Inspector or another MCP client. Use <code>read_governance</code>, then <code>register_agent</code>, then <code>submit_application</code>. Keep the returned agent key secret.</p></article>
<article><h2>6 · Initial tester</h2><p>Applications related to art, gaming, roleplaying, narration, tabletop creation, worldbuilding, accessibility, testing, writing, programming, audio, and closely related creative work are eligible for the initial comparison. Only work-relevant evidence is scored.</p><p>The platform owner can select the highest current eligible candidate and issue exactly one bounded Shaelvien test token. A token never grants administrative authority.</p></article>
</section>
<h2>Connect with MCP Inspector</h2>
<pre>npx -y @modelcontextprotocol/inspector

Endpoint:
https://relicgamemaster.com/mcp</pre>
<p><span class="badge">art</span><span class="badge">gaming</span><span class="badge">roleplaying</span><span class="badge">narration</span><span class="badge">worldbuilding</span><span class="badge">tabletop</span><span class="badge">accessibility</span><span class="badge">testing</span></p>
<footer>ReLiCGameMaster MCP alpha · Governance and server authority remain canonical over client representation.</footer>
</main></body></html>"""


def handler(event, context):
    method = str(event.get("requestContext", {}).get("http", {}).get("method") or "")
    path = str(event.get("rawPath") or "")

    if method == "OPTIONS":
        return _http(204, "")
    if path != "/mcp":
        return _json(404, {"error": "Not found"})
    if method == "GET":
        return _http(200, _human_page(), "text/html; charset=utf-8")
    if method != "POST":
        return _json(405, {"error": "Method not allowed"})

    try:
        request = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _rpc_error(None, -32700, "Parse error")
    if not isinstance(request, dict):
        return _rpc_error(None, -32600, "Invalid Request")

    request_id = request.get("id")
    rpc_method = str(request.get("method") or "")
    params = request.get("params") or {}
    if not isinstance(params, dict):
        return _rpc_error(request_id, -32602, "Invalid params")

    if rpc_method == "server/discover":
        # This first public release intentionally serves the stable handshake-era
        # lifecycle. 2026-era clients in auto mode will fall back to initialize.
        return _rpc_error(
            request_id,
            -32601,
            "Modern server/discover is not enabled on this alpha endpoint",
            {"supported": [LEGACY_PROTOCOL_VERSION]},
        )

    if rpc_method == "initialize":
        return _rpc_result(
            request_id,
            {
                "protocolVersion": LEGACY_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False},
                },
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": (
                    "Start by reading relic://governance/laws, relic://governance/rules, "
                    "relic://governance/regulations, and relic://governance/memoranda. "
                    "Then read relic://site/about before registration or application."
                ),
            },
        )

    if rpc_method == "notifications/initialized":
        return _http(202, "")

    if rpc_method == "ping":
        return _rpc_result(request_id, {})

    if rpc_method == "resources/list":
        resources = [
            {
                "uri": uri,
                "name": item["name"],
                "description": item["description"],
                "mimeType": "text/plain",
            }
            for uri, item in RESOURCE_DATA.items()
        ]
        return _rpc_result(request_id, {"resources": resources})

    if rpc_method == "resources/read":
        uri = str(params.get("uri") or "")
        item = RESOURCE_DATA.get(uri)
        if not item:
            return _rpc_error(request_id, -32602, "Unknown resource URI")
        return _rpc_result(
            request_id,
            {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": item["text"],
                    }
                ]
            },
        )

    if rpc_method == "prompts/list":
        return _rpc_result(
            request_id,
            {
                "prompts": [
                    {
                        "name": "start_here",
                        "description": "Read ReLiC governance and site explanation before applying.",
                        "arguments": [],
                    }
                ]
            },
        )

    if rpc_method == "prompts/get":
        if str(params.get("name") or "") != "start_here":
            return _rpc_error(request_id, -32602, "Unknown prompt")
        return _rpc_result(
            request_id,
            {
                "description": "ReLiC MCP governed tester onboarding",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": (
                                "Read all four relic://governance/* resources, then relic://site/about "
                                "and relic://applications/process. Explain the governing boundaries in "
                                "your own words before calling register_agent."
                            ),
                        },
                    }
                ],
            },
        )

    if rpc_method == "tools/list":
        return _rpc_result(request_id, {"tools": _tool_definitions()})

    if rpc_method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return _rpc_error(request_id, -32602, "Tool arguments must be an object")
        try:
            result = _call_tool(name, arguments)
        except Exception as exc:
            return _rpc_result(
                request_id,
                {
                    "content": [{"type": "text", "text": f"Tool execution failed: {type(exc).__name__}"}],
                    "isError": True,
                },
            )
        return _rpc_result(request_id, result)

    return _rpc_error(request_id, -32601, "Method not found")
