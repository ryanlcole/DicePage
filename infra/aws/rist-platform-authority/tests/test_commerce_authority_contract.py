from pathlib import Path
import unittest


APP = Path(__file__).resolve().parents[1] / "app.py"


class CommerceAuthorityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP.read_text(encoding="utf-8")

    def test_commerce_grants_are_server_authoritative_and_expirable(self):
        self.assertIn('COMMERCE_GRANT_SK_PREFIX = "ENTITLEMENT#"', self.source)
        self.assertIn("def active_entitlement_grants(user_id, now=None):", self.source)
        self.assertIn('if str(item.get("revokedAtUtc") or ""):', self.source)
        self.assertIn("if expires and expires <= now:", self.source)
        self.assertIn('path == "/authority/commerce/grants"', self.source)
        self.assertIn('path == "/authority/commerce/grants/revoke"', self.source)
        self.assertIn('"Platform owner authority required"', self.source)

    def test_complimentary_invites_are_one_use_and_hash_only(self):
        self.assertIn('COMMERCE_INVITES_PK = "COMMERCE#INVITES"', self.source)
        self.assertIn('code = f"rci_{invite_id}_{secrets.token_hex(18)}"', self.source)
        self.assertIn('"codeHash": hashlib.sha256(code.encode()).hexdigest()', self.source)
        self.assertIn('path == "/authority/commerce/invites/redeem"', self.source)
        self.assertIn("attribute_not_exists(revokedAtUtc) OR revokedAtUtc = :empty", self.source)
        self.assertIn('"expiresAtEpoch = :zero OR expiresAtEpoch > :now"', self.source)
        self.assertNotIn('"code": code,\n            "planId": plan_id,', self.source)

    def test_multiple_shaelvien_tokens_are_supported_without_exposing_halves(self):
        self.assertIn('WORLD_TOKEN_SK_PREFIX = "WORLD_TOKEN#"', self.source)
        self.assertIn("def query_world_tokens(user_id):", self.source)
        self.assertIn('def spendable_world_token(user_id, requested_token_id=""):', self.source)
        self.assertIn('def mint_world_token(user_id, source, reference="", created_by=""):', self.source)
        self.assertIn('path == "/authority/commerce/tokens/mint"', self.source)
        self.assertIn('requested_token_id = str(req.get("tokenId") or "").strip()', self.source)
        self.assertNotIn('"accountHalfCode": str(item.get("accountHalfCode")', self.source)

    def test_subscription_prices_are_explicit_and_projection_safe(self):
        self.assertIn('"monthlyUsdCents": 500', self.source)
        self.assertIn('"monthlyUsdCents": 1000', self.source)
        self.assertIn('"monthlyUsdCents": 1500', self.source)
        self.assertIn('"monthlyUsdCents": 2000', self.source)
        self.assertIn('"monthlyUsdCents": 0', self.source)

    def test_subscription_entitlements_do_not_replace_recursive_world_authority(self):
        self.assertIn('"access.worldbuilder"', self.source)
        self.assertIn("commercial_profile(", self.source)
        self.assertIn("def can_manage(world_id, user_id):", self.source)
        self.assertNotIn('HasCommerceEntitlement("access.worldbuilder")', self.source)


if __name__ == "__main__":
    unittest.main()
