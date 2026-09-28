from pathlib import Path
import unittest

APP = Path(__file__).resolve().parents[1] / "app.py"

class OwnerDashboardContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP.read_text(encoding="utf-8")

    def test_visit_endpoint_is_write_only_and_never_stores_raw_ip(self):
        self.assertIn('path == "/telemetry/visit"', self.source)
        self.assertIn("def _visitor_hash(source_ip):", self.source)
        self.assertIn("hmac.new(_telemetry_secret()", self.source)
        self.assertNotIn('"sourceIp": source_ip', self.source)
        self.assertNotIn('"ip": source_ip', self.source)

    def test_owner_dashboard_requires_server_side_owner_identity(self):
        self.assertIn('path == "/authority/owner/dashboard"', self.source)
        self.assertIn('return owner_dashboard(session)', self.source)
        self.assertIn('Platform owner authority required', self.source)
        self.assertIn('owner_user_id and user_id == owner_user_id', self.source)

    def test_dashboard_counts_game_and_external_ai_accounts(self):
        self.assertIn('Attr("sk").eq("PROFILE")', self.source)
        self.assertIn('Attr("pk").begins_with("AI-REGISTRATION#")', self.source)
        self.assertIn('"accountStatus": ai_status', self.source)

    def test_privacy_contract_is_explicit(self):
        self.assertIn('"rawIpStored": False', self.source)
        self.assertIn('"rawQuestionStored": False', self.source)
        self.assertIn('"visitorIdentity": "server-keyed-hmac"', self.source)

if __name__ == "__main__":
    unittest.main()
