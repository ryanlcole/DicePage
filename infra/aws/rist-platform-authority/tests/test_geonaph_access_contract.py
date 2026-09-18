from pathlib import Path
import unittest


APP = Path(__file__).resolve().parents[1] / "app.py"


class GeonaphAccessContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP.read_text(encoding="utf-8")

    def test_geonaph_is_public_view_for_authenticated_users(self):
        self.assertIn('GEONAPH_WORLD_ID = "shaelvien-geonaph-alpha-001"', self.source)
        self.assertIn("def can_view(world_id, user_id):", self.source)
        self.assertIn("if is_geonaph(world_id):\n        return True", self.source)
        self.assertIn('"effectiveAuthority": "publicViewer"', self.source)
        self.assertIn('"claimPermission": claim_permission(world_id, user_id)', self.source)

    def test_geonaph_management_stays_platform_owner_only(self):
        self.assertIn(
            "if is_geonaph(world_id):\n        return bool(owner_user_id and user_id == owner_user_id)",
            self.source,
        )
        self.assertIn('if role in ("GM", "owner") and target != owner_user_id:', self.source)
        self.assertIn(
            'return response(403, {"error": "Endemar GM authority cannot be delegated"})',
            self.source,
        )


    def test_region_claims_use_database_authority_and_notify_gm(self):
        self.assertIn('path == "/world/claims/request"', self.source)
        self.assertIn('path == "/world/claims/decision"', self.source)
        self.assertIn('path == "/world/regions"', self.source)
        self.assertIn('query_world_prefix(world_id, "REGION#")', self.source)
        self.assertIn('notify_user(', self.source)
        self.assertIn('"world.claim.request"', self.source)
        self.assertIn('"world.claim.decision"', self.source)

    def test_gm_can_enable_claim_permission_without_granting_world_management(self):
        self.assertIn('path == "/world/membership/claim-permission"', self.source)
        self.assertIn('if not can_manage(world_id, user_id):', self.source)
        self.assertIn('current["claimPermission"] = value', self.source)
        self.assertIn('current["role"] = "viewer"', self.source)

    def test_world_slot_is_enforced_before_presigned_private_world_upload(self):
        self.assertIn("def can_claim_world_slot(user_id, world_id):", self.source)
        self.assertIn('if "worlds.unlimited" in commercial["entitlements"]:', self.source)
        self.assertIn('Delimiter="/"', self.source)
        self.assertIn('"Additional world-slot entitlement required"', self.source)

    def test_authority_profile_exposes_commercial_defaults_without_overwriting_entitlements(self):
        self.assertIn("DEFAULT_WORLD_SLOTS = 1", self.source)
        self.assertIn("DEFAULT_SURFACE_WORLD_PIXELS = 2048", self.source)
        self.assertIn("def commercial_profile(existing, platform_owner):", self.source)
        self.assertIn("users.update_item(", self.source)
        self.assertIn('"worldSlots": world_slots', self.source)
        self.assertIn('"surfaceWorldPixels": surface_pixels', self.source)
        self.assertIn('"worlds.unlimited", "surface.unlimited"', self.source)

if __name__ == "__main__":
    unittest.main()
