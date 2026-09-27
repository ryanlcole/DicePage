import importlib.util
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).parent
mod_path = ROOT / "rist_relic_mcp.py"
spec = importlib.util.spec_from_file_location("rist_relic_mcp", mod_path)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def event(body, headers=None, method="POST"):
    return {
        "body": json.dumps(body),
        "headers": headers or {},
        "requestContext": {"requestId": "test", "http": {"method": method}},
        "rawPath": "/mcp",
    }


def body(resp):
    return json.loads(resp["body"]) if resp["body"] else None


class ReLiCMcpTests(unittest.TestCase):
    def test_initialize_and_tools(self):
        r = m.handler(event({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}, {"mcp-protocol-version":"2025-11-25"}), None)
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(body(r)["result"]["protocolVersion"], "2025-11-25")
        r = m.handler(event({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}, {"mcp-protocol-version":"2025-11-25"}), None)
        tools = body(r)["result"]["tools"]
        self.assertEqual({t["name"] for t in tools}, {"relic_context","relic_validate","relic_canon","relic_health"})

    def test_context_is_observer_only(self):
        r = m.handler(event({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"relic_context","arguments":{"subject":"ReLiC plugin","truthDomain":"FACT"}}}, {"mcp-protocol-version":"2025-11-25"}), None)
        data = body(r)["result"]["structuredContent"]
        self.assertEqual(data["mode"], "read-only-observer")
        self.assertFalse(data["continuity"]["authoritativeStateConnected"])
        self.assertTrue(any(p["id"] == "RELIC.REPRESENTATION.NOT_TRUTH" for p in data["governingPrinciples"]))

    def test_validation_blocks_promotion_and_bad_identity(self):
        r = m.handler(event({"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"relic_validate","arguments":{"statements":[{"text":"Rendered token equals identity","truthDomain":"FACT","identityBasis":"representation","canonStatus":"generated"}],"proposedAction":"commit state","authorityBasis":"authenticated-only"}}}, {"mcp-protocol-version":"2025-11-25"}), None)
        data = body(r)["result"]["structuredContent"]
        self.assertFalse(data["valid"])
        codes = {f["code"] for f in data["findings"]}
        self.assertTrue({"FACT_WITHOUT_PROVENANCE","REPRESENTATION_USED_AS_IDENTITY","GENERATED_FACT_NEEDS_EXTERNAL_EVIDENCE","ACTION_WITHOUT_EXPLICIT_CAPABILITY"}.issubset(codes))

    def test_modern_discovery(self):
        req = {"jsonrpc":"2.0","id":5,"method":"server/discover","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}
        headers = {"mcp-protocol-version":"2026-07-28","mcp-method":"server/discover"}
        r = m.handler(event(req, headers), None)
        data = body(r)["result"]
        self.assertEqual(data["resultType"], "complete")
        self.assertIn("2026-07-28", data["supportedVersions"])


if __name__ == "__main__":
    unittest.main()
