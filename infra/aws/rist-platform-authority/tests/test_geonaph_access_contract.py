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
        self.assertIn(
            'return response(200, {"worldId": world_id, "role": "viewer", "effectiveAuthority": "publicViewer"})',
            self.source,
        )

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
