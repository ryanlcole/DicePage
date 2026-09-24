from pathlib import Path
import unittest


APP = Path(__file__).resolve().parents[1] / "app.py"


class CollaborationAuthorityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP.read_text(encoding="utf-8")

    def test_connection_codes_are_one_use_hash_only_and_authenticated(self):
        self.assertIn('COLLAB_INVITES_PK = "COLLAB#INVITES"', self.source)
        self.assertIn('code = f"rcc_{invite_id}_{secrets.token_hex(18)}"', self.source)
        self.assertIn('"codeHash": hashlib.sha256(code.encode()).hexdigest()', self.source)
        self.assertIn('path == "/authority/connections/redeem"', self.source)
        self.assertIn("You cannot connect an account to itself", self.source)
        self.assertIn("This connection code has already been used", self.source)
        self.assertNotIn('"code": code,\n            "createdByUserId"', self.source)

    def test_redeeming_connection_creates_reciprocal_directory_entries(self):
        self.assertIn("def collaboration_connection_key(user_id, linked_user_id):", self.source)
        self.assertIn('COLLAB_CONNECTION_SK_PREFIX = "CONNECTION#"', self.source)
        self.assertIn('"linkedUserId": user_id', self.source)
        self.assertIn('"linkedUserId": creator', self.source)
        self.assertIn('path == "/authority/connections"', self.source)
        self.assertIn('"defaultAssetPermission": "Waiting for GM"', self.source)

    def test_linking_identity_does_not_grant_world_or_asset_permission(self):
        block = self.source[
            self.source.index('if method == "POST" and path == "/authority/connections/redeem"'):
            self.source.index('if method == "POST" and path == "/authority/connections/revoke"')
        ]
        self.assertNotIn("membership.grant", block)
        self.assertNotIn("claimPermission", block)
        self.assertNotIn("PermissionGrant.View", block)
        self.assertNotIn("permission", block.lower().replace("defaultassetpermission", ""))

    def test_unlink_revokes_both_sides(self):
        self.assertIn('path == "/authority/connections/revoke"', self.source)
        self.assertIn("peer_key = collaboration_connection_key(linked_user_id, user_id)", self.source)
        self.assertIn("revokedAtUtc = :stamp", self.source)


if __name__ == "__main__":
    unittest.main()
