from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "Components" / "PowerCardWorkspace.razor"
MODELS = ROOT / "CardEffectModels.cs"
CONTRACT = ROOT / "CARD_EFFECT_ENGINE_CONTRACT.md"


class PowerCardWorkspaceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = WORKSPACE.read_text(encoding="utf-8")
        cls.models = MODELS.read_text(encoding="utf-8")
        cls.contract = CONTRACT.read_text(encoding="utf-8")

    def test_power_is_system_neutral_and_gm_named(self):
        self.assertIn("RistPowerDefinition", self.models)
        self.assertIn('"Magic" is a family', self.models)
        self.assertIn("SYSTEM NAMES", self.workspace)
        self.assertIn("SectionName", self.workspace)
        self.assertIn("FamilyLabel", self.workspace)
        self.assertIn("ResourceLabel", self.workspace)

    def test_power_cards_carry_targeting_effect_resolution_and_duration(self):
        for marker in (
            "TARGETING / INSTANCE GEOMETRY",
            "JOINED EFFECTS",
            "TARGET JOIN",
            "OPERATION",
            "RESOLUTION",
            "DIFFICULTY JOIN",
            "DURATION",
            "STACKING",
        ):
            self.assertIn(marker, self.workspace)
        for geometry in (
            "LINE", "CONE", "SPHERE", "CYLINDER", "BOX",
            "WALL", "CHAIN", "POLYGON", "PATH", "VOLUME",
        ):
            self.assertIn(f"<option>{geometry}</option>", self.workspace)

    def test_power_representation_and_spawn_follow_locked_contract(self):
        for mode in ("SPRITE", "IMAGE", "DRAW", "NONE"):
            self.assertIn(f"<option>{mode}</option>", self.workspace)
        self.assertIn("FLASH AFFECTED GRID BORDERS", self.workspace)
        self.assertIn("SPRITE CHAIN", self.workspace)
        self.assertIn("CHARACTER/NPC CARD", self.workspace)
        self.assertIn("RistEffectRepresentation", self.models)
        self.assertIn("RistSpawnDefinition", self.models)
        self.assertIn("same spawned entity identity", self.contract.lower())

    def test_runtime_effect_identity_is_separate_from_card_definition(self):
        self.assertIn("RistEffectInstance", self.models)
        self.assertIn("EffectId", self.models)
        self.assertIn("CardInstanceId", self.models)
        self.assertIn("RistSpatialEffectGeometry", self.models)
        self.assertIn("RistSpawnedEntityReference", self.models)


if __name__ == "__main__":
    unittest.main()
