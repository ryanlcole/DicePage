from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "WorldSession.CardCanon.cs"
MODELS = ROOT / "CardEffectModels.cs"
INDEX = ROOT / "Components" / "CardIndexWorkspace.razor"
CONTRACT = ROOT / "CARD_EFFECT_ENGINE_CONTRACT.md"


class CardEffectEngineContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canon = CANON.read_text(encoding="utf-8")
        cls.models = MODELS.read_text(encoding="utf-8")
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.contract = CONTRACT.read_text(encoding="utf-8")

    def test_canonical_card_envelope_carries_behavior(self):
        self.assertIn("public int Version { get; set; } = 4;", self.canon)
        self.assertIn("RistCardType.Power", self.index)
        self.assertIn("public RistCardBehavior Behavior", self.canon)
        self.assertIn("card.Behavior", self.canon)

    def test_effect_runtime_identities_are_distinct(self):
        for marker in (
            "class RistCardBehavior",
            "class RistEffectInstance",
            "class RistSpawnedEntityReference",
            "EffectId",
            "CardInstanceId",
        ):
            self.assertIn(marker, self.models)
        self.assertIn("Card Definition", self.contract)
        self.assertIn("Effect Instance", self.contract)
        self.assertIn("Spawned Entity", self.contract)

    def test_card_creator_authors_targeting_representation_and_spawn(self):
        for marker in (
            "CARD BEHAVIOR",
            "Activation",
            "Target",
            "Geometry",
            "Resolution",
            "Representation",
            "SPRITE",
            "IMAGE",
            "DRAW",
            "Unbounded range",
            "SPAWN / SUMMON",
            "Token Asset ID",
            "Character/NPC Card ID",
        ):
            self.assertIn(marker, self.index)
        self.assertIn("SaveDraftAsync", self.index)
        self.assertIn("Behavior=behavior", self.index)

    def test_power_is_system_neutral(self):
        self.assertIn("Power,", self.canon)
        self.assertIn("class RistPowerDefinition", self.models)
        self.assertIn('Family { get; set; } = "Magic"', self.models)
        self.assertIn("internal mechanic is **POWER**", self.contract)

    def test_spatial_targeting_supports_xyz_and_common_geometries(self):
        for marker in (
            "RistSpatialEffectGeometry",
            "double X",
            "double Y",
            "double Z",
            "LINE",
            "CONE",
            "SPHERE",
            "PATH",
            "VOLUME",
        ):
            self.assertIn(marker, self.models + self.index)


if __name__ == "__main__":
    unittest.main()
