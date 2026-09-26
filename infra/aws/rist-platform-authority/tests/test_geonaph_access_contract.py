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

    def test_completed_profile_mints_one_server_owned_world_token_pair(self):
        self.assertIn('path == "/authority/profile-complete"', self.source)
        self.assertIn('GENESIS_WORLD_TOKEN_SK = "WORLD_TOKEN#GENESIS"', self.source)
        self.assertIn('"accountHalfCode": account_half', self.source)
        self.assertIn('"worldHalfCode": world_half', self.source)
        self.assertIn("binding_hash = hashlib.sha256(", self.source)
        self.assertIn('ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)"', self.source)

    def test_mmo_parcel_is_2048_square_height_one_hundred_and_expands_from_endemar(self):
        self.assertIn("SHAELVIEN_PROPERTY_SPACE_PIXELS = 2048", self.source)
        self.assertIn("MMO_PARCEL_PIXELS = SHAELVIEN_PROPERTY_SPACE_PIXELS", self.source)
        self.assertIn("SHAELVIEN_PROPERTY_SPACE_LAYERS = 100", self.source)
        self.assertIn("MMO_PARCEL_MAX_HEIGHT = SHAELVIEN_PROPERTY_SPACE_LAYERS", self.source)
        self.assertIn("ENDEMAR_ORIGIN_COLUMN = 15", self.source)
        self.assertIn("ENDEMAR_ORIGIN_ROW = 15", self.source)
        self.assertIn("def mmo_parcel_claimable(cell_index, parcels):", self.source)
        self.assertIn(
            "frontier = occupied | {(ENDEMAR_ORIGIN_COLUMN, ENDEMAR_ORIGIN_ROW)}",
            self.source,
        )
        self.assertIn('path == "/world/parcels/claim"', self.source)
        self.assertIn("transact_write_items(", self.source)

    def test_mmo_parcel_is_exclusive_while_owned_and_owner_can_release_to_ghost(self):
        self.assertIn('path == "/world/parcels/delegate"', self.source)
        self.assertIn('PARCEL_DELEGATION_PERMISSIONS = {"View", "Edit", "Manage", "None"}', self.source)
        self.assertIn('parcel_permission(world_id, parcel_id, user_id) == "Manage"', self.source)
        self.assertIn('region["parcelPixelWidth"] = MMO_PARCEL_PIXELS', self.source)
        self.assertIn('region["parcelPixelHeight"] = MMO_PARCEL_PIXELS', self.source)
        self.assertIn('region["maxHeight"] = MMO_PARCEL_MAX_HEIGHT', self.source)
        self.assertIn('region["parentNodeId"] = "world:" + world_id', self.source)
        self.assertIn('region["coordinateSpace"] = "world-normalized-v1"', self.source)
        self.assertIn('region["canonicalMinX"] = column / MMO_PARCEL_GRID_COLUMNS', self.source)
        self.assertIn('region["canonicalZMax"] = MMO_PARCEL_MAX_HEIGHT', self.source)
        self.assertIn('region["ownerUserId"] = owner', self.source)
        self.assertIn('path == "/world/parcels/release"', self.source)
        self.assertIn('Only the property owner may release this Shaelvien property space', self.source)
        self.assertIn('"entityType": "ghostZone"', self.source)
        self.assertIn('"contentUsePolicy": "preserve-only"', self.source)
        self.assertIn('"published": False', self.source)
        self.assertIn('"status": "released"', self.source)
        self.assertIn('"release-refund"', self.source)

if __name__ == "__main__":
    unittest.main()
