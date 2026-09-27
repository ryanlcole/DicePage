import importlib.util
import json
import os
import pathlib
import sys
import types
import unittest
import urllib.parse


ROOT = pathlib.Path(__file__).parent


class _FakeTable:
    def __init__(self):
        self.items = {}

    def get_item(self, Key, ConsistentRead=False):
        value = self.items.get((Key.get("pk"), Key.get("sk")))
        return {"Item": value} if value is not None else {}

    def put_item(self, Item, **kwargs):
        self.items[(Item.get("pk"), Item.get("sk"))] = dict(Item)
        return {}

    def delete_item(self, Key):
        self.items.pop((Key.get("pk"), Key.get("sk")), None)
        return {}


class _FakeDdb:
    def __init__(self):
        self.tables = {}

    def Table(self, name):
        return self.tables.setdefault(name, _FakeTable())


fake_ddb = _FakeDdb()
fake_boto3 = types.ModuleType("boto3")
fake_boto3.resource = lambda name: fake_ddb
sys.modules["boto3"] = fake_boto3

os.environ.setdefault("MCP_AUTH_TABLE", "auth-test")
os.environ.setdefault("IDENTITY_TABLE", "identity-test")
os.environ.setdefault("DISCORD_AUTH_API", "https://auth.example.test")
os.environ.setdefault("PUBLIC_ORIGIN", "https://relicgamemaster.com")

spec = importlib.util.spec_from_file_location("relic_mcp_auth", ROOT / "relic_mcp_auth.py")
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def form_event(data):
    return {
        "body": urllib.parse.urlencode(data),
        "isBase64Encoded": False,
        "requestContext": {"http": {"method": "POST"}},
        "rawPath": "/oauth/token",
    }


def response_body(response):
    return json.loads(response["body"]) if response.get("body") else None


class ReLiCMcpAuthTests(unittest.TestCase):
    def setUp(self):
        fake_ddb.tables.clear()
        m.oauth = fake_ddb.Table("auth-test")
        m.identity = fake_ddb.Table("identity-test")

    def test_metadata_is_pkce_oauth_for_canonical_resource(self):
        metadata = m.metadata()
        resource = m.protected_resource()
        self.assertEqual(metadata["issuer"], "https://relicgamemaster.com")
        self.assertEqual(metadata["code_challenge_methods_supported"], ["S256"])
        self.assertIn("authorization_code", metadata["grant_types_supported"])
        self.assertIn("refresh_token", metadata["grant_types_supported"])
        self.assertEqual(metadata["token_endpoint_auth_methods_supported"], ["none"])
        self.assertTrue(metadata["authorization_response_iss_parameter_supported"])
        self.assertEqual(resource["resource"], "https://relicgamemaster.com/mcp")
        self.assertEqual(resource["authorization_servers"], ["https://relicgamemaster.com"])

    def test_refresh_token_rejects_wrong_resource(self):
        client_id = "relic-client-test"
        m.oauth.put_item(Item={
            "pk": "CLIENT#" + client_id,
            "sk": "PROFILE",
            "clientId": client_id,
        })
        refresh = "refresh-test-token"
        digest = __import__("hashlib").sha256(refresh.encode("utf-8")).hexdigest()
        m.oauth.put_item(Item={
            "pk": "REFRESH#" + digest,
            "sk": "TOKEN",
            "userId": "user-test",
            "username": "Test User",
            "clientId": client_id,
            "scopes": ["relic.read"],
            "resource": m.RESOURCE_ID,
            "expiresAt": m.now() + 3600,
        })
        response = m.token(form_event({
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh,
            "resource": "https://evil.example/mcp",
        }))
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response_body(response)["error"], "invalid_target")

    def test_refresh_token_is_bound_to_original_resource(self):
        client_id = "relic-client-test"
        m.oauth.put_item(Item={
            "pk": "CLIENT#" + client_id,
            "sk": "PROFILE",
            "clientId": client_id,
        })
        refresh = "refresh-test-token"
        digest = __import__("hashlib").sha256(refresh.encode("utf-8")).hexdigest()
        m.oauth.put_item(Item={
            "pk": "REFRESH#" + digest,
            "sk": "TOKEN",
            "userId": "user-test",
            "username": "Test User",
            "clientId": client_id,
            "scopes": ["relic.read"],
            "resource": "https://stale.example/mcp",
            "expiresAt": m.now() + 3600,
        })
        response = m.token(form_event({
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh,
            "resource": m.RESOURCE_ID,
        }))
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response_body(response)["error"], "invalid_grant")


if __name__ == "__main__":
    unittest.main()
