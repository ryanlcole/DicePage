from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "Components" / "CampaignWorkspace.razor"
ROUTER = ROOT / "Components" / "TaskWorkspaceRouter.razor"
AUTHORITY = ROOT / "RecursiveAuthority.cs"


class CampaignConnectionsContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CAMPAIGN.read_text(encoding="utf-8")
        cls.router = ROUTER.read_text(encoding="utf-8")
        cls.authority = AUTHORITY.read_text(encoding="utf-8")

    def test_victims_and_co_conspirators_is_campaign_section(self):
        self.assertIn("VICTIMS &amp; CO‑CONSPIRATORS", self.source)
        self.assertIn("PERMISSIONS DIRECTORY", self.source)
        self.assertIn('Mode == "campaign"', self.router)
        self.assertIn("<CampaignWorkspace />", self.router)

    def test_codes_create_connections_not_permissions(self):
        self.assertIn("CreateConnectionInviteAsync", self.source)
        self.assertIn("RedeemConnectionInviteAsync", self.source)
        self.assertIn("Connecting an account does not grant access by itself", self.source)

    def test_default_asset_permission_waits_for_gm(self):
        self.assertIn('public const string WaitingForGameMaster = "Waiting for GM"', self.authority)
        self.assertIn("PermissionGrant.None", self.authority)
        self.assertIn("WaitingForGameMaster", self.source)

    def test_directory_supports_unlink_without_credential_sharing(self):
        self.assertIn("RevokeConnectionAsync", self.source)
        self.assertIn("UNLINK", self.source)
        self.assertNotIn("password", self.source.lower())
        self.assertNotIn("token", self.source.lower())


if __name__ == "__main__":
    unittest.main()
