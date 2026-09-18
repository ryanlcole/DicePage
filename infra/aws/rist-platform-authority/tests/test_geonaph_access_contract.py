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
            'return response(403, {"error": "Geonaph GM authority cannot be delegated"})',
            self.source,
        )


if __name__ == "__main__":
    unittest.main()
